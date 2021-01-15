
from __future__ import absolute_import
import logging
from celery import shared_task
from celery.utils.log import get_task_logger
from django.core.cache import cache
from channels.layers import get_channel_layer
from .handle_test import TcompTEST

channel_layer = get_channel_layer()
logger = get_task_logger('ghost')

@shared_task
def dotest(fsvconf, bdconf, thconf):
    try:
        chl_name = cache.get('channel_name')
        print('channel_name={}'.format(chl_name))
        tst = TcompTEST(chl_name, channel_layer,logger)
        ret = tst.init_all(fsvconf, bdconf, thconf)
        return ret
    except Exception as e:
        print('task error:{}'.format(e))


@shared_task
def initchannel(channel_name):
    cache.set('channel_name', channel_name, 60 * 60)

    # rptlogger.start(channel_name, channel_layer)
