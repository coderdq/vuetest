import logging
from django.shortcuts import render, HttpResponse
from django.core import  serializers
from django.http import JsonResponse,StreamingHttpResponse
import os
import json
from shutil import copyfile
from django.views.decorators.csrf import csrf_exempt
from celery.app.control import Control

from config.celery import app
from config.settings import UPLOAD_DIR, TEST_TEMPLATE_DIR

from .models import CalibModel, UpgradeModel
from .tasks import do_calibrate,do_upgrade
from commoninterface.utils import make_zip

upgrade_process=None
calibrate_process=None
logger = logging.getLogger('ghost')

def stop_upgrade():
    try:
        global upgrade_process
        if upgrade_process:
            print('终止任务')
            ctrl = Control(app=app)
            ctrl.revoke(str(upgrade_process.id), terminate=True)
            upgrade_process = None
    except Exception as e:
        logger.error(e)

def stop_calibrate():
    try:
        global calibrate_process
        print(calibrate_process)
        if calibrate_process:
            print('终止任务')
            ctrl = Control(app=app)
            ctrl.revoke(str(calibrate_process.id), terminate=True)
            calibrate_process = None
    except Exception as e:
        logger.error(e)

# Create your views here.
@csrf_exempt
def big_file_download(request):
    def file_iterator(file_name, chunk_size=512):
        with open(file_name,'rb') as f:
            while True:
                c = f.read(chunk_size)
                if c:
                    yield c
                else:
                    break

    postbody = request.body
    data = json.loads(postbody)
    # the_file_name = "E:\\testresult\\ID_滤波_E\\1.0\\ID_滤波_E_1.0.xlsx"
    the_file_name=data.get('filepath','')

    if the_file_name:
        the_path = os.path.dirname(os.path.dirname(the_file_name))  # 上两级目录
        zip_file = os.path.join(os.path.dirname(the_path), 'export.zip')
        make_zip(the_path, zip_file)
        response = StreamingHttpResponse(file_iterator(zip_file))
        # response['content-type'] = 'application/octet-stream'
        response['content-type'] = 'application/zip'
        response['Content-Disposition'] = "attachment; filename = {}".format('export.zip')
        # response['file-name']="{}".format(name)
        return response
@csrf_exempt
def upgrade_upload(request):
    try:
        if request.method == 'POST':
            ip = request.POST.get('ip')
            bbpath = None
            armpath = None
            bbfile = request.FILES.get('bbfile', None)

            if bbfile:
                bbpath = write_file(bbfile)

            armfile = request.FILES.get('armfile', None)
            if armfile:
                armpath = write_file(armfile)
            if bbpath is None and armpath is None:
                return JsonResponse({'result': False,'message':'升级文件缺失'})
            bdconf = {'IP': ip, 'BB_PATH': bbpath, 'ARM_PATH': armpath}
            print(bdconf)
            up_params = UpgradeModel()
            up_params.ip = ip
            if bbpath is not None:
                up_params.bbfile_path = bbpath
            if armpath is not None:
                up_params.armfile_path = armpath
            up_params.save()
            global upgrade_process
            upgrade_process = do_upgrade.delay(bdconf)
            ret=upgrade_process.get(timeout=60*60)
            message = '升级成功' if ret else '升级失败'
            return JsonResponse({'result': ret,'message':message})
            # for test
            # return json_response(200, 'OK', {'result': True})
    except Exception as e:
        print('upgrade_upload error:',e)
        return JsonResponse({'result': False,'message':'升级失败'})

@csrf_exempt
def calibrate_upload(request):
    '''
    定标下发当前设置
    :param request:
    :return:
    '''
    try:
        if request.method == 'POST':
            calib_params = CalibModel()
            ip = request.POST.get('ip', None)
            fsvip = request.POST.get('fsvip', None)
            file = request.FILES.get('file', None)  # 测试模板
            port = request.POST.get('port', '')

            if file is not None:
                filepath = write_file(file)
                filename = os.path.basename(filepath)
                new_path = os.path.join(TEST_TEMPLATE_DIR, filename)  # 将测试模板放到测试目录
                copyfile(filepath, new_path)
                calib_params.ip = ip
                calib_params.fsvip = fsvip
                calib_params.template_path = new_path
                fsvconf = {'IP': fsvip, 'DIR': new_path}
                bdconf = {'IP': ip}
                thconf = {}
                if port:
                    # port = port.strip().strip('\n\r\t')
                    lowtemp = request.POST.get('lowtemp', None)
                    normtemp = request.POST.get('normtemp', None)
                    hightemp = request.POST.get('hightemp', None)
                    period = request.POST.get('period', None)
                    calib_params.lowtemp = int(lowtemp)
                    calib_params.normtemp = int(normtemp)
                    calib_params.hightemp = int(hightemp)
                    calib_params.port = int(port)
                    calib_params.period = int(period)
                    thconf = {"PORT": port, "LOW_TEMP": lowtemp, "NORM_TEMP": normtemp, "HIGH_TEMP": hightemp,
                              "PERIOD": period}
                calib_params.save()
                print(fsvconf)
                global calibrate_process
                # 开始测试
                calibrate_process= do_calibrate.delay(fsvconf, bdconf, thconf)
                ret=calibrate_process.get(timeout=60*60)
                calibrate_process = None
                message = '测试失败'
                endpath = ''
                if not isinstance(ret, tuple):
                    message = '测试成功' if ret else '测试失败'
                else:
                    message = '测试成功' if ret[0] else '测试失败'
                    endpath = ret[1]
                # message = '定标成功' if ret else '定标失败'
                return JsonResponse({'result': ret,'message':message,'filepath':endpath})
            else:
                return JsonResponse({'result': False,'message':'测试模板缺失'})
    except Exception as e:
        print('calibrate_upload error:',e)
        return JsonResponse({'result': False,'message':'定标失败'})


def write_file(fp):
    if fp is None:
        return None
    dir = UPLOAD_DIR
    if not os.path.exists(dir):
        os.mkdir(dir)
    filepath = os.path.join(dir, fp.name)
    destination = open(filepath, 'wb+')
    try:
        for chunk in fp.chunks():
            destination.write(chunk)
        return filepath
    except Exception:
        return None
    finally:
        destination.close()

@csrf_exempt
def show_upgrade_history(request):

    response = {}
    try:
        params = UpgradeModel.objects.all()
        response['params'] = json.loads(serializers.serialize("json", params))
        response['msg'] = 'success'
        response['error_num'] = 0
    except Exception as e:
        response['msg'] = str(e)
        response['error_num'] = 1
    return JsonResponse(response)

@csrf_exempt
def show_calib_history(request):
    response = {}
    try:
        params = CalibModel.objects.all()
        response['params'] = json.loads(serializers.serialize("json", params))
        response['msg'] = 'success'
        response['error_num'] = 0
    except Exception as e:
        response['msg'] = str(e)
        response['error_num'] = 1
    return JsonResponse(response)

@csrf_exempt
def clear_upgrade_history(request):

    response = {}
    try:
        UpgradeModel.objects.all().delete()
        response['msg'] = 'success'
        response['error_num'] = 0
    except Exception as e:
        response['msg'] = str(e)
        response['error_num'] = 1
    return JsonResponse(response)

@csrf_exempt
def clear_calib_history(request):
    '''
    清空定标历史记录
    :param request:
    :return:
    '''
    response = {}
    try:
        CalibModel.objects.all().delete()
        response['msg'] = 'success'
        response['error_num'] = 0
    except Exception as e:
        response['msg'] = str(e)
        response['error_num'] = 1
    return JsonResponse(response)


@csrf_exempt
def set_calib_history(request):
    '''
    下发定标历史配置
    :param request:
    :return:
    '''
    try:
        if request.method == 'POST':
            postbody = request.body
            data = json.loads(postbody)
            port = data.get('port', '')
            thconf = {}
            if port:
                # port = port.strip().strip('\n\r\t')
                thconf = {
                    "PORT": port,
                    "LOW_TEMP": data.get('lowtemp',None),
                    "NORM_TEMP": data.get('normtemp',None),
                    "HIGH_TEMP": data.get('hightemp',None),
                    "PERIOD": data.get('period',None)
                }
            fsvconf = {'IP': data.get('fsvip'), 'DIR': data.get('template_path')}
            bdconf = {'IP': data.get('ip')}
            # 开始测试
            global calibrate_process
            calibrate_process = do_calibrate.delay(fsvconf, bdconf, thconf)
            ret=calibrate_process.get(timeout=60*60)
            calibrate_process = None
            message = '测试失败'
            endpath = ''
            if not isinstance(ret, tuple):
                message = '测试成功' if ret else '测试失败'
            else:
                message = '测试成功' if ret[0] else '测试失败'
                endpath = ret[1]
            # message = '定标成功' if ret else '定标失败'
            return JsonResponse({'result': ret,'message':message,'filepath':endpath})
    except Exception as e:
        print('set_calib_history error:', e)
        return JsonResponse({'result': False, 'message': '定标失败'})


@csrf_exempt
def set_upgrade_history(request):
    '''
    下发升级历史配置
    :param request:
    :return:
    '''
    if request.method == 'POST':
        postbody = request.body
        data = json.loads(postbody)
        ip = data.get('ip', '').strip().strip('\n\r\t')
        bbpath=data.get('bbfile','')
        armpath=data.get('armfile','')
        if not bbpath and not armpath:
            return JsonResponse({'result': False,'message':'升级文件缺失'})
        bdconf = {'IP': ip, 'BB_PATH': bbpath, 'ARM_PATH': armpath}
        # 开始测试
        print(bdconf)
        global upgrade_process
        upgrade_process = do_upgrade.delay(bdconf)
        ret = upgrade_process.get(timeout=60 * 60)
        message = '升级成功' if ret else '升级失败'
        return JsonResponse({'result': ret,'message':message})

def register(request):
    return render(request, 't2k-product/4.html')
