from __future__ import absolute_import
from celery import shared_task
from django.core.cache import cache
from channels.layers import get_channel_layer
from .handle_test import DOTEST

channel_layer = get_channel_layer()


@shared_task
def dotest(conf):
    try:
        chl_name = cache.get('channel_name')
        print('channel_name={}'.format(chl_name))
        tst = DOTEST(chl_name, channel_layer)
        ret = tst.init_all(conf)
        return ret
    except Exception as e:
        print('task error:{}'.format(e))


@shared_task
def initchannel(channel_name):
    cache.set('channel_name', channel_name, 60 * 60)

    # rptlogger.start(channel_name, channel_layer)
