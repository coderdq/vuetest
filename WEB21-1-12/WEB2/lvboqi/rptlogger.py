from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync


class RptLogger(object):
    channel_name = ''

    def __init__(self):
        self.channel_layer = None
        try:
            channel_layer = get_channel_layer()
            print('channel_layer=', channel_layer)
            self.channel_layer = channel_layer
        except Exception as e:
            print('errOR:{}'.format(e))

    def rpt_message(self, msg):
        try:
            print('channel_name=', self.channel_name)
            if self.channel_layer and self.channel_name:
                print('rpt_message')
                async_to_sync(self.channel_layer.send)(
                    RptLogger.channel_name,
                    {
                        "type": "send.message",
                        "message": msg
                    }
                )
        except Exception as e:
            print('rpt_msg error:{}'.format(e))
