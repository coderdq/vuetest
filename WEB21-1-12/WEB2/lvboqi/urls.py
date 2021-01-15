from django.urls import path, re_path

from . import views

urlpatterns = [

    re_path('^lvboqi_upload/$', views.lvboqi_upload, ),
    re_path('^show_lvboqi_history/$', views.show_lvboqi_history, ),
    re_path('^set_lvboqi_history/$', views.set_lvboqi_history, ),
    re_path('^clear_lvboqi_history/$', views.clear_lvboqi_history,),
    re_path('^fortest/$',views.fortest,),
    re_path('^export/$',views.big_file_download,)
]
