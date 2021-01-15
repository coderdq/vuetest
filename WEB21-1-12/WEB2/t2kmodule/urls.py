from django.urls import path, re_path

from . import t2kmoduleviews

urlpatterns = [
        # t2k裸板下行
    # re_path(r'^t2kmoduledlsethtml/$', t2kmoduleviews.t2kmoduledlsethtml, name='t2kmoduledlsethtml'),
    re_path(r'^dl_newset/$', t2kmoduleviews.t2kmoduledl_newset, ),
    re_path(r'^dl_set/$', t2kmoduleviews.t2kmoduledl_set, ),
    re_path(r'^show_dl_history/$', t2kmoduleviews.show_t2kmoduledl_history, ),
    re_path(r'^clear_dl_history/$', t2kmoduleviews.clear_t2kmoduledl_history,),

    # t2k裸板上行
    re_path(r'^ul_newset/$', t2kmoduleviews.t2kmoduleul_newset, ),
    re_path(r'^ul_set/$', t2kmoduleviews.t2kmoduleul_set, ),
    re_path(r'^show_ul_history/$', t2kmoduleviews.show_t2kmoduleul_history, ),
    re_path(r'^clear_ul_history/$', t2kmoduleviews.clear_t2kmoduleul_history,),

    #for test
    re_path(r'^fortest/$',t2kmoduleviews.fortest,),
    re_path('^export/$',t2kmoduleviews.big_file_download,)
]
