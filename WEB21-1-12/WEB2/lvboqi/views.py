#! python
# -*- coding: utf-8 -*-
import logging
import os
import json
from shutil import copyfile
from celery.app.control import Control
from config.celery import app
from django.views.decorators.csrf import csrf_exempt
from django.core import  serializers
from django.http import JsonResponse,StreamingHttpResponse

from lvboqi.models import LVBOQI

#
# from .zvl_ctrl import *
# from .init_inst import VisaInstrument
from .tasks import dotest
from config.settings import UPLOAD_DIR, TEST_TEMPLATE_DIR
from commoninterface.utils import make_zip

logger = logging.getLogger('ghost')

do_process = None


def stop_process():
    try:
        global do_process
        if do_process:
            print('终止任务')
            ctrl = Control(app=app)
            ctrl.revoke(str(do_process.id), terminate=True)
            do_process = None
    except Exception as e:
        logger.error(e)


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
def lvboqi_upload(request):
    try:
        if request.method == 'POST':
            lvboqi_params = LVBOQI()
            data = request.POST
            max = data.get('max', None)  # 获取MAX
            ip = data.get('ip', None)
            band = data.get('band', None)
            file = request.FILES.get('file', None)
            port = request.POST.get('port', '')

            if file is not None:
                filepath = write_file(file)
                filename = os.path.basename(filepath)
                new_path = os.path.join(TEST_TEMPLATE_DIR, filename)  # 将测试模板放到测试目录
                copyfile(filepath, new_path)
                lvboqi_params.ip = ip
                lvboqi_params.max = max
                lvboqi_params.band = band
                lvboqi_params.dir = new_path
                zvlconf = {'IP': ip, 'MAX': max, 'BAND': band, 'DIR': new_path}
                thconf = {}
                if port:
                    # port = port.strip().strip('\n\r\t')
                    lowtemp = request.POST.get('lowtemp', None)
                    normtemp = request.POST.get('normtemp', None)
                    hightemp = request.POST.get('hightemp', None)
                    period = request.POST.get('period', None)
                    lvboqi_params.lowtemp = int(lowtemp)
                    lvboqi_params.normtemp = int(normtemp)
                    lvboqi_params.hightemp = int(hightemp)
                    lvboqi_params.port = int(port)
                    lvboqi_params.period = int(period)
                    thconf = {"PORT": port, "LOW_TEMP": lowtemp, "NORM_TEMP": normtemp, "HIGH_TEMP": hightemp,
                              "PERIOD": period}
                lvboqi_params.save()
                # 开始测试
                # instr = VisaInstrument()
                config = {'ZVL': zvlconf, 'THDEV': thconf}
                logger.debug(config)
                # ret = init_zvl(instr, config)
                global do_process
                do_process = dotest.delay(config)
                ret = do_process.get(timeout=60 * 60)
                message='测试失败'
                endpath=''
                if not isinstance(ret,tuple):
                    message = '测试成功' if ret else '测试失败'
                else:
                    message='测试成功' if ret[0] else '测试失败'
                    endpath=ret[1]
                do_process=None
                return JsonResponse({'result': ret,'message':message,'filepath':endpath})
            else:
                return JsonResponse({'result': False,'message': '测试模板缺失'})
    except Exception as e:
        logger.error('lvboqi_upload error:{}'.format(e))
        return JsonResponse({'result': False,'message':'测试失败'})

@csrf_exempt
def show_lvboqi_history(request):
    response = {}
    try:
        params =LVBOQI.objects.all()
        response['params'] = json.loads(serializers.serialize("json", params))
        response['msg'] = 'success'
        response['error_num'] = 0
    except Exception as e:
        response['msg'] = str(e)
        response['error_num'] = 1
    return JsonResponse(response)
    # return render(request, 'homepage.html')

@csrf_exempt
def clear_lvboqi_history(request):
    # 清空数据库历史记录
    response = {}
    try:
        LVBOQI.objects.all().delete()
        response['msg'] = 'success'
        response['error_num'] = 0
    except Exception as e:
        response['msg'] = str(e)
        response['error_num'] = 1
    return JsonResponse(response)


@csrf_exempt
def set_lvboqi_history(request):
    try:
        if request.method == 'POST':
            postbody = request.body
            data = json.loads(postbody)
            port = data.get('port', '')
            print(data)
            thconf = {}
            if port:
                # port = port.strip().strip('\n\r\t')
                thconf = {
                    "PORT": port,
                    "LOW_TEMP": data.get('lowtemp'),
                    "NORM_TEMP": data.get('normtemp'),
                    "HIGH_TEMP": data.get('hightemp'),
                    "PERIOD": data.get('period')
                }
            zvlconf = {
                'IP': data.get('ip'),
                'MAX': data.get('max'),
                'BAND': data.get('band'),
                'DIR': data.get('dir')
            }
            # 开始测试
            # instr = VisaInstrument()
            config = {'ZVL': zvlconf, 'THDEV': thconf}
            logger.debug(config)
            # ret = init_zvl(instr, config)
            global do_process
            do_process = dotest.delay(config)
            print('do_process={}'.format(do_process))
            ret = do_process.get(timeout=60 * 60)
            message = '测试失败'
            endpath = ''
            if not isinstance(ret, tuple):
                message = '测试成功' if ret else '测试失败'
            else:
                message = '测试成功' if ret[0] else '测试失败'
                endpath = ret[1]
            do_process = None
            # message = '测试完毕'
            return JsonResponse({'result': ret, 'message': message,'filepath':endpath})
    except Exception as e:
        logger.error('set_lvboqi_history error:{}'.format(e))
        return JsonResponse({'result': False, 'message': '测试失败'})


@csrf_exempt
def fortest(request):
    import time
    response={'he':'world'}
    time.sleep(180)
    return JsonResponse(response)
