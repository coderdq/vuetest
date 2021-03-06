from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync


class RptLogger(object):
    channel_name = ''

    def __init__(self):
        self.channel_layer = None
        try:
            channel_layer = get_channel_layer()
            self.channel_layer = channel_layer
        except Exception as e:
            print('errOR:{}'.format(e))

    def rpt_message(self, msg):
        if self.channel_layer and self.channel_name:
            async_to_sync(self.channel_layer.send)(
                RptLogger.channel_name,
                {
                    "type": "send.message",
                    "message": msg
                }
            )
