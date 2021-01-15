import json
import time
from channels.generic.websocket import WebsocketConsumer

from .tasks import initchannel
from .t2kmoduleviews import stop_dl,stop_ul


class LogConsumer(WebsocketConsumer):
    def connect(self):
        self.accept()
        print('accept')
        chl = self.channel_name
        print(chl)
        initchannel.delay(chl)

    def disconnect(self, code):
        print('disconnect websocket')
        stop_dl()
        stop_ul()

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



