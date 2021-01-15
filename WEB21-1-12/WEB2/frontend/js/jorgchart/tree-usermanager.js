/**
 * @author xuxinyue
 */

'use strict';

$(function() {
    /**
     * 用户权限
     */
    var ioptype = 0; //用户类型
    var opcode = 0;
    var opname = "";

    //初始化界面
    $(document).ready(function() {
        var Url = document.URL;
        console.log()
        var param = Url.split("?")[1];

        if (param != null) {
            var paramdata = param.split("&");
            var param1 = paramdata[0];
            var param2 = paramdata[1];
            var param3 = paramdata[2];
            ioptype = param1.split("=")[1];
            opcode = param2.split("=")[1];
            opname = param3.split("=")[1];
        }
    });

    var pro = new Promise(function(resolve, reject) {
        //获取后台数据
        $.ajax({
            url: "../getUserListTreeInfo.action",
            type: 'get',
            dataType: 'json',
            success: function(data) {
                resolve(data);
            },
            error: function() {
                layer.msg("加载数据失败", { time: 1500, icon: 2 });
            }
        })
    }).then(function(data) {
    	console.log(data)
        $('#chart-container').orgchart({
            'data': data,
            'depth': 3,
            'nodeTitle': 'name',
            'nodeContent': 'title',
            'nodeID': 'id',
            'createNode': function($node, data) {
                // var nodePrompt = $('<i>', {
                //     'class': 'fa fa-info-circle second-menu-icon',
                //     click: function() {
                //         $(this).siblings('.second-menu').toggle();
                //     }
                // });
                // var secondMenu = '<div class="second-menu"><img class="avatar" src="img/avatar/' + data.id + '.jpg"></div>';
                // $node.append(nodePrompt);
            }
        });

    })

});