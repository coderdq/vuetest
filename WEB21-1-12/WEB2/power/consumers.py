import json
import time
from channels.generic.websocket import WebsocketConsumer

from .tasks import initchannel
from .views import stop_process


class LogConsumer(WebsocketConsumer):
    def connect(self):
        try:
            print('连接websocket')
            self.accept()
            chl = self.channel_name
            initchannel.delay(chl)
        except Exception as e:
            print('connect error:{}'.format(e))

    def disconnect(self, code):
        stop_process()


    def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']
        if message:
            self.send(text_data=json.dumps({
                'message': message+'\n'
            }))

    def send_message(self, event):
        self.send(text_data=json.dumps({
            'message': '['
                +time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))
                       +'] '+event['message'] + '\n'
        }))

