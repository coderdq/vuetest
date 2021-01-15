from django.urls import path, re_path

from . import views

urlpatterns = [
    re_path('^fortest/$', views.register, ),

    re_path('^upgrade_upload/$', views.upgrade_upload, ),
    re_path('^set_upgrade_history/$',views.set_upgrade_history,),
    re_path('^show_calib_history/$',views.show_calib_history),
    re_path('^clear_upgrade_history/$',views.clear_upgrade_history,),
    re_path('^calibrate_upload/$', views.calibrate_upload, ),
    re_path('^set_calib_history/$', views.set_calib_history, ),
    re_path('^clear_calib_history/$', views.clear_calib_history, ),
    re_path('^show_upgrade_history/$',views.show_upgrade_history),
    re_path('^export/$',views.big_file_download,)
]
