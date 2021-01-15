from django.urls import path, re_path

from . import views

urlpatterns = [

    re_path('^power_upload/$', views.power_set, name='power_set'),
    re_path('^show_power_history/$',views.show_power_history,name='show_power_history'),
    re_path('^set_power_history/$',views.set_power_history,name='set_power_history'),
    re_path('^clear_power_history/$',views.clear_power_history,name='clear_power_history'),
    re_path('^export/$',views.big_file_download,)
]
