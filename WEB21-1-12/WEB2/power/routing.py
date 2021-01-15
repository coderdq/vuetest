from django.urls import re_path
from . import consumers

websocket_urlpatterns=[
    re_path(r'ws/power/log/$', consumers.LogConsumer),
]