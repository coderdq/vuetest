from django.shortcuts import render
import logging
import os
import json
from shutil import copyfile
from celery.app.control import Control
from config.celery import app
from django.views.decorators.csrf import csrf_exempt
from django.core import serializers
from django.http import JsonResponse, StreamingHttpResponse

from .models import TCompModel
from .tasks import dotest
from config.settings import UPLOAD_DIR, TEST_TEMPLATE_DIR
from commoninterface.utils import make_zip

logger = logging.getLogger('ghost')

do_process = None


# Create your views here.

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
        with open(file_name, 'rb') as f:
            while True:
                c = f.read(chunk_size)
                if c:
                    yield c
                else:
                    break

    postbody = request.body
    data = json.loads(postbody)
    the_file_name = data.get('filepath', '')

    if the_file_name:
        the_path = os.path.dirname(os.path.dirname(the_file_name))  # 上两级目录
        zip_file = os.path.join(os.path.dirname(the_path), 'export.zip')
        make_zip(the_path, zip_file)
        response = StreamingHttpResponse(file_iterator(zip_file))
        # response['content-type'] = 'application/octet-stream'
        response['content-type'] = 'application/zip'
        response['Content-Disposition'] = "attachment; filename = {}".format('export.zip')
        return response


@csrf_exempt
def show_tempcomp_history(request):
    response = {}
    try:
        params = TCompModel.objects.all()
        response['params'] = json.loads(serializers.serialize("json", params))
        response['msg'] = 'success'
        response['error_num'] = 0
    except Exception as e:
        response['msg'] = str(e)
        response['error_num'] = 1
    return JsonResponse(response)


@csrf_exempt
def clear_tempcomp_history(request):
    # 清空数据库历史记录
    response = {}
    try:
        TCompModel.objects.all().delete()
        response['msg'] = 'success'
        response['error_num'] = 0
    except Exception as e:
        response['msg'] = str(e)
        response['error_num'] = 1
    return JsonResponse(response)


@csrf_exempt
def tempcomp_upload(request):
    try:
        if request.method == 'POST':
            tcomp_params = TCompModel()
            data = request.POST
            fsvip = data.get('fsvip', None)
            boardip = data.get('boardip', None)

            file = request.FILES.get('file', None)
            port = data.get('port', '')

            if file is not None:
                filepath = write_file(file)
                filename = os.path.basename(filepath)
                new_path = os.path.join(TEST_TEMPLATE_DIR, filename)  # 将测试模板放到测试目录
                copyfile(filepath, new_path)
                tcomp_params.boardip = boardip
                tcomp_params.fsvip = fsvip
                tcomp_params.dir = new_path
                fsvconf = {'IP': fsvip, 'DIR': new_path}
                bdconf = {'IP': boardip}
                thconf = {}
                if port:
                    tcomp_params.port = int(port)
                    thconf = {"PORT": port}
                tcomp_params.save()
                # 开始测试

                global do_process
                do_process = dotest.delay(fsvconf, bdconf, thconf)
                ret = do_process.get(timeout=60 * 60)
                message = '测试失败'
                endpath = ''
                if not isinstance(ret, tuple):
                    message = '测试成功' if ret else '测试失败'
                else:
                    message = '测试成功' if ret[0] else '测试失败'
                    endpath = ret[1]
                do_process = None
                return JsonResponse({'result': ret, 'message': message, 'filepath': endpath})
            else:
                return JsonResponse({'result': False, 'message': '测试模板缺失'})
    except Exception as e:
        logger.error('lvboqi_upload error:{}'.format(e))
        return JsonResponse({'result': False, 'message': '测试失败'})


@csrf_exempt
def set_tempcomp_history(request):
    """
    记录温度补偿历史记录
    :param request:
    :return:
    """
    try:
        if request.method == 'POST':
            postbody = request.body
            data = json.loads(postbody)
            # 记录提交的高低温箱的串口数据
            port = data.get('port', '')
            print(data)
            thconf = {}
            if port:
                thconf = {
                    "PORT": port
                }
            # 记录提交的频谱仪的IP地址以及测试模板的路径
            fsvconf = {
                'IP': data.get('fsvip'),
                'DIR': data.get('dir')
            }
            bdconf = {'IP': data.get('boardip')}
            # 开始测试
            

            global do_process
            do_process = dotest.delay(fsvconf, bdconf, thconf)
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
            return JsonResponse({'result': ret, 'message': message, 'filepath': endpath})
    except Exception as e:
        logger.error('set_lvboqi_history error:{}'.format(e))
        return JsonResponse({'result': False, 'message': '测试失败'})
