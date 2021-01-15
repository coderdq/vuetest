import logging
import os
import json
from shutil import copyfile
from django.core import  serializers
from django.views.decorators.csrf import csrf_exempt
from celery.app.control import Control
from config.celery import app
from django.http import JsonResponse,StreamingHttpResponse
from t2kmodule.models import T2KDLModel, T2KULModel


from config.settings import UPLOAD_DIR, TEST_TEMPLATE_DIR, LingmdDIR
from .tasks import do_dltest,do_ultest
from commoninterface.utils import make_zip

logger = logging.getLogger('ghost')
dl_process=None
ul_process=None

def stop_ul():
    try:
        global ul_process
        if ul_process:
            print('终止任务')
            ctrl = Control(app=app)
            ctrl.revoke(str(ul_process.id), terminate=True)
            ul_process = None
    except Exception as e:
        logger.error(e)

def stop_dl():
    try:
        global dl_process
        if dl_process:
            print('***终止任务')
            ctrl = Control(app=app)
            ctrl.revoke(str(dl_process.id), terminate=True)
            dl_process = None
            print('******')
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
    the_file_name=data.get('filepath','')

    if the_file_name:
        the_path = os.path.dirname(os.path.dirname(the_file_name))  # 上两级目录
        zip_file = os.path.join(os.path.dirname(the_path), 'export.zip')
        make_zip(the_path, zip_file)
        response = StreamingHttpResponse(file_iterator(zip_file))
        response['content-type'] = 'application/zip'
        response['Content-Disposition'] = "attachment; filename = {}".format('export.zip')
        return response

@csrf_exempt
def t2kmoduledl_newset(request):
    try:
        if request.method == 'POST':
            t2kmoduledl_params = T2KDLModel()
            data = request.POST
            port = data.get('port', '')
            deviceconf = {}
            if port:
                # port = port.strip().strip('\n\r\t')
                deviceconf = {
                    "PORT": port,
                    "LOW_TEMP": data.get('lowtemp',None),
                    "NORM_TEMP": data.get('normtemp',None),
                    "HIGH_TEMP": data.get('hightemp',None),
                    "PERIOD": data.get('period',None)
                }
            file = request.FILES.get('file', None)  # 测试模板
            if file:
                filepath = write_file(file)
                filename = os.path.basename(filepath)
                new_path = os.path.join(TEST_TEMPLATE_DIR, filename)  # 将测试模板放到测试目录
                copyfile(filepath, new_path)
                t2kdir = new_path
            else:
                return JsonResponse({'result': False,'message':'测试模板缺失'})
            fsvconf = {'IP': data.get('fsvip'), 'DIR': t2kdir, 'OFFSET': data.get('fsvoffset')}
            bdconf = {'IP': data.get('board_ip'), 'CELL': data.get('cellid')}
            logger.debug(fsvconf)
            t2kmoduledl_params.fsvip = data.get('fsvip')
            t2kmoduledl_params.fsvoffset = data.get('fsvoffset')
            t2kmoduledl_params.t2kdir = t2kdir
            t2kmoduledl_params.board_ip = data.get('board_ip')
            t2kmoduledl_params.cellid = data.get('cellid')
            if port:
                t2kmoduledl_params.port = data.get('port')
                t2kmoduledl_params.lowtemp = data.get('lowtemp')
                t2kmoduledl_params.normtemp = data.get('normtemp')
                t2kmoduledl_params.hightemp = data.get('hightemp')
                t2kmoduledl_params.period = data.get('period')
            t2kmoduledl_params.save()  # 保存到数据库

            global  dl_process
            dl_process=do_dltest.delay(fsvconf, bdconf, deviceconf)
            ret=dl_process.get(timeout=60*60)
            dl_process = None
            message = '测试失败'
            endpath = ''
            if not isinstance(ret, tuple):
                message = '测试成功' if ret else '测试失败'
            else:
                message = '测试成功' if ret[0] else '测试失败'
                endpath = ret[1]

            return JsonResponse({'result': ret,'message':message,'filepath':endpath})
    except Exception as e:
        logger.error(e)
        return JsonResponse({'result': False,'message':'测试失败'})

@csrf_exempt
def t2kmoduledl_set(request):
    try:
        if request.method == 'POST':
            # data = request.POST
            postbody=request.body
            data=json.loads(postbody)
            port = data.get('port', '')
            deviceconf = {}
            if port:
                # port = port.strip().strip('\n\r\t')
                deviceconf = {
                    "PORT": port,
                    "LOW_TEMP": data.get('lowtemp',None),
                    "NORM_TEMP": data.get('normtemp',None),
                    "HIGH_TEMP": data.get('hightemp',None),
                    "PERIOD": data.get('period',None)
                }
            t2kdir = data.get('t2kdir')
            fsvconf = {'IP': data.get('fsvip'), 'DIR': t2kdir, 'OFFSET': data.get('fsvoffset')}
            bdconf = {'IP': data.get('board_ip'), 'CELL': data.get('cellid')}
            logger.debug(fsvconf)

            global  dl_process
            dl_process=do_dltest.delay(fsvconf, bdconf, deviceconf)
            ret=dl_process.get(timeout=60*60)
            dl_process = None
            message = '测试失败'
            endpath = ''
            if not isinstance(ret, tuple):
                message = '测试成功' if ret else '测试失败'
            else:
                message = '测试成功' if ret[0] else '测试失败'
                endpath = ret[1]
            return JsonResponse( {'result': ret,'message':message,'filepath':endpath})
    except Exception as e:
        logger.error(e)
        return JsonResponse({'result': False, 'message': '测试失败'})


@csrf_exempt
def t2kmoduleul_newset(request):
    '''
    点击设置
    :param request:
    :return:
    '''
    try:
        if request.method == 'POST':
            t2kmoduleul_params = T2KULModel()
            data = request.POST
            port = data.get('port', '')
            deviceconf = {}
            if port:
                # port = port.strip().strip('\n\r\t')
                deviceconf = {"PORT": port, "LOW_TEMP": data.get('lowtemp',None),
                              "NORM_TEMP": data.get('normtemp',None), "HIGH_TEMP": data.get('hightemp',None),
                              "PERIOD": data.get('period',None)}

            file = request.FILES.get('file', None)  # 测试模板
            if file is not None:
                filepath = write_file(file)
                filename = os.path.basename(filepath)
                new_path = os.path.join(TEST_TEMPLATE_DIR, filename)  # 将测试模板放到测试目录
                copyfile(filepath, new_path)
                template_path = new_path
            else:
                return JsonResponse({'result': False,'message':'测试模板缺失'})

            t2kmoduleul_params.smbv_ip = data.get('smbv_ip')
            t2kmoduleul_params.smbv_offset = data.get('smbv_offset')
            t2kmoduleul_params.exe_path = LingmdDIR,
            t2kmoduleul_params.template_path = template_path
            t2kmoduleul_params.board_ip = data.get('board_ip')
            t2kmoduleul_params.cellid = data.get('cellid')
            if port:
                t2kmoduleul_params.port = port
                t2kmoduleul_params.lowtemp = data.get('lowtemp')
                t2kmoduleul_params.normtemp = data.get('normtemp')
                t2kmoduleul_params.hightemp = data.get('hightemp')
                t2kmoduleul_params.period = data.get('period')
            t2kmoduleul_params.save()  # 保存到数据库
            smbvconf = {'IP': data.get('smbv_ip'),
                        'PATH': LingmdDIR,
                        'OFFSET': data.get('smbv_offset')}
            bdconf = {'DIR': template_path, 'IP': data.get('board_ip'), 'CELL': data.get('cellid')}

            global ul_process
            ul_process = do_ultest.delay(smbvconf, bdconf, deviceconf)
            ret = ul_process.get(timeout=60 * 60)
            # ret = dt.init_all(smbvconf, bdconf, deviceconf)
            ul_process = None
            message = '测试失败'
            endpath = ''
            if not isinstance(ret, tuple):
                message = '测试成功' if ret else '测试失败'
            else:
                message = '测试成功' if ret[0] else '测试失败'
                endpath = ret[1]
            return JsonResponse({'result': ret,'message':message,'filepath':endpath})
    except Exception as e:
        logger.error(e)
        return JsonResponse({'result': False, 'message': '测试失败'})


@csrf_exempt
def t2kmoduleul_set(request):
    '''
    点击设置
    :param request:
    :return:
    '''
    if request.method == 'POST':
        postbody = request.body
        data = json.loads(postbody)
        print(data)
        port = data.get('port', '')

        deviceconf = {}
        if port:
            # port = port.strip().strip('\n\r\t')
            deviceconf = {"PORT": port, "LOW_TEMP": data.get('lowtemp',None),
                          "NORM_TEMP": data.get('normtemp',None), "HIGH_TEMP": data.get('hightemp',None),
                          "PERIOD": data.get('period',None)}
        template_path = data.get('template_path')
        smbvconf = {'IP': data.get('smbv_ip'),
                    'PATH': LingmdDIR,
                    'OFFSET': data.get('smbv_offset')}
        bdconf = {'DIR': template_path, 'IP': data.get('board_ip'), 'CELL': data.get('cellid')}

        global ul_process
        ul_process = do_ultest.delay(smbvconf, bdconf, deviceconf)
        ret = ul_process.get(timeout=60 * 60)
        # ret = dt.init_all(smbvconf, bdconf, deviceconf)
        ul_process = None
        message = '测试失败'
        endpath = ''
        if not isinstance(ret, tuple):
            message = '测试成功' if ret else '测试失败'
        else:
            message = '测试成功' if ret[0] else '测试失败'
            endpath = ret[1]
        return JsonResponse({'result': ret,'message':message,'filepath':endpath})


@csrf_exempt
def show_t2kmoduleul_history(request):
    response = {}
    try:
        params = T2KULModel.objects.all()
        response['params'] = json.loads(serializers.serialize("json", params))
        response['msg'] = 'success'
        response['error_num'] = 0
    except Exception as e:
        response['msg'] = str(e)
        response['error_num'] = 1
    return JsonResponse(response)


@csrf_exempt
def show_t2kmoduledl_history(request):
    response={}
    try:
        params = T2KDLModel.objects.all()
        response['params']=json.loads(serializers.serialize("json", params))
        response['msg']='success'
        response['error_num']=0
    except Exception as e:
        response['msg']=str(e)
        response['error_num']=1
    return JsonResponse(response)


@csrf_exempt
def clear_t2kmoduleul_history(request):
    response={}
    try:
        T2KULModel.objects.all().delete()
        response['msg'] = 'success'
        response['error_num'] = 0
    except Exception as e:
        response['msg'] = str(e)
        response['error_num'] = 1
    return JsonResponse(response)


@csrf_exempt
def clear_t2kmoduledl_history(request):
    response = {}
    try:
        T2KDLModel.objects.all().delete()
        response['msg'] = 'success'
        response['error_num'] = 0
    except Exception as e:
        response['msg'] = str(e)
        response['error_num'] = 1
    return JsonResponse(response)



@csrf_exempt
def fortest(request):
    import time
    response={'he':'world'}
    time.sleep(60*5)
    return JsonResponse(response)
    # from commoninterface import winauto
    # exeauto = winauto.T2KEXEOperate()
    # exeauto.start_exe('192.254.1.86', LingmdDIR)
    # exeauto.site_manage()
    # if not exeauto.enter_test_mode(0, 'TDD'):
    #     logger.error('操作灵敏度软件错误')
    #
    # if not exeauto.create_ue():
    #     logger.error('操作灵敏度软件错误')
    #
    # coord = exeauto.ready_for_check()
    #
    # exeauto.check_result(coord)
    # return render(request, 't2k-module/1.html')
