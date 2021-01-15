# -*- coding: utf-8 -*-

from django.urls import path, re_path,include
from django.views.generic.base import TemplateView


urlpatterns = [
    path('', TemplateView.as_view(template_name='index.html'), ),
    # 滤波器
    re_path('^lvboqi/',include('lvboqi.urls')),
    # 功放
    re_path('^power/',include('power.urls')),
    re_path('^t2kmodule/',include('t2kmodule.urls')),
    re_path('^t2kmachine/', include('t2kmachine.urls')),
    re_path('^tempcomp/',include('tempcomp.urls'))
    # re_path('^api/',include('tst.urls')),
    # re_path('^dq/',include('dqt.urls'))
]
