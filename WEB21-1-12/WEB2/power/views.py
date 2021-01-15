#! python
# -*- coding: utf-8 -*-

import os
import json
import logging
from shutil import copyfile
from celery.app.control import Control
from config.celery import app
from django.views.decorators.csrf import csrf_exempt
from django.core import  serializers
from django.http import JsonResponse,StreamingHttpResponse
from power.models import *

from config.settings import UPLOAD_DIR, TEST_TEMPLATE_DIR
from .tasks import dotest
from commoninterface.utils import make_zip

logger = logging.getLogger('ghost')

do_process=None

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
def clear_power_history(request):
    # 清空数据库历史记录
    response = {}
    try:
        POWER.objects.all().delete()
        response['msg'] = 'success'
        response['error_num'] = 0
    except Exception as e:
        response['msg'] = str(e)
        response['error_num'] = 1
    return JsonResponse(response)


@csrf_exempt
def set_power_history(request):
    try:
        if request.method == 'POST':
            logger.debug('set_power_history')
            postbody = request.body
            data = json.loads(postbody)
            print(data)
            port = data.get('port', '')
            config = {
                'FSV': {
                    'IP': data.get('fsvip'),
                    'OFFSET': data.get('fsvoffset')
                },
                'ZVL': {
                    'IP': data.get('zvlip'),
                    'OFFSET': data.get('zvloffset')
                },
                'SMBV': {
                    'IP': data.get('smbvip')
                },
                'POWER': {
                    'DIR': data.get('powerdir'),
                    'BAND': data.get('band'),
                    'ZVLSTATE': data.get('zvlused'),
                    'DL': data.get('dl'),
                },
            }
            thconf = {}
            if port:
                # port = port.strip().strip('\n\r\t')
                lowtemp = data.get('lowtemp', None)
                normtemp = data.get('normtemp', None)
                hightemp = data.get('hightemp', None)
                period = data.get('period', None)

                thconf = {"PORT": port, "LOW_TEMP": lowtemp, "NORM_TEMP": normtemp, "HIGH_TEMP": hightemp,
                          "PERIOD": period}
                config['THDEVICE'] = thconf
            logger.debug(config)
            global do_process
            # dotest = DOTEST()
            # ret = dotest.init_all(config)
            do_process=dotest.delay(config)
            ret=do_process.get(timeout=60*60)
            do_process = None

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
        return JsonResponse({'result': False,'message': '测试失败'})


@csrf_exempt
def power_set(request):
    try:
        if request.method == 'POST':
            power_params = POWER()
            data = request.POST
            print(data)
            file = request.FILES.get('file', None)  # 测试模板
            port = request.POST.get('port', '')

            if file is not None:
                filepath = write_file(file)
                filename = os.path.basename(filepath)
                new_path = os.path.join(TEST_TEMPLATE_DIR, filename)  # 将测试模板放到测试目录
                copyfile(filepath, new_path)
                config = {
                    'FSV': {
                        'IP': data.get('fsvip'),
                        'OFFSET': data.get('fsvoffset')
                    },
                    'ZVL': {
                        'IP': data.get('zvlip'),
                        'OFFSET': data.get('zvloffset')
                    },
                    'SMBV': {
                        'IP': data.get('smbvip')
                    },
                    'POWER': {
                        'DIR': new_path,
                        'BAND': data.get('band'),
                        'ZVLSTATE': data.get('zvlused'),
                        'DL': data.get('dl'),
                    },
                }
                power_params.fsvip = data.get('fsvip')
                power_params.fsvoffset = data.get('fsvoffset')
                power_params.zvlip = data.get('zvlip')
                power_params.zvloffset = data.get('zvloffset')
                power_params.smbvip = data.get('smbvip')
                power_params.powerdir = new_path
                power_params.band = data.get('band')
                power_params.zvlused = data.get('zvlused')
                power_params.dl = data.get('dl')
                thconf = {}
                if port:
                    # port = port.strip().strip('\n\r\t')
                    lowtemp = data.get('lowtemp', None)
                    normtemp = data.get('normtemp', None)
                    hightemp = data.get('hightemp', None)
                    period = data.get('period', None)
                    power_params.lowtemp = int(lowtemp)
                    power_params.normtemp = int(normtemp)
                    power_params.hightemp = int(hightemp)
                    power_params.port = int(port)
                    power_params.period = int(period)
                    thconf = {"PORT": port, "LOW_TEMP": lowtemp, "NORM_TEMP": normtemp, "HIGH_TEMP": hightemp,
                              "PERIOD": period}
                    config['THDEVICE'] = thconf
                power_params.save()  # 保存到数据库
                print(config)
                global do_process
                # dotest = DOTEST()
                # ret = dotest.init_all(config)
                do_process = dotest.delay(config)
                ret = do_process.get(timeout=60 * 60)
                message = '测试失败'
                endpath = ''
                if not isinstance(ret, tuple):
                    message = '测试成功' if ret else '测试失败'
                else:
                    message = '测试成功' if ret[0] else '测试失败'
                    endpath = ret[1]
                do_process = None
                return JsonResponse({'result': ret,'message':message,'filepath':endpath})
            else:
                return JsonResponse({'result': False,'message':'测试模板缺失'})
    except Exception as e:
        logger.error(e)
        return JsonResponse({'result': False,'message': '测试失败'})

@csrf_exempt
def show_power_history(request):
    response = {}
    try:
        params = POWER.objects.all()
        response['params'] = json.loads(serializers.serialize("json", params))
        response['msg'] = 'success'
        response['error_num'] = 0
    except Exception as e:
        response['msg'] = str(e)
        response['error_num'] = 1
    return JsonResponse(response)
