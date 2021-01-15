from django.urls import path, re_path

from . import views

urlpatterns = [
    re_path(r'^show_history/$',views.show_tempcomp_history,),
    re_path(r'^clear_history/$',views.clear_tempcomp_history,),
    re_path(r'^set_history/$',views.set_tempcomp_history,),
    re_path(r'^upload/$',views.tempcomp_upload,),
    re_path('^export/$',views.big_file_download,)

]
