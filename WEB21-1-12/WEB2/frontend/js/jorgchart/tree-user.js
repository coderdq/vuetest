/**
 * @author xuxinyue
 */
"use strict";

$(function() {
    /**
     * 用户权限
     */
    var ioptype = 0; //用户类型
    var opcode = 0;
    var opname = "";
    var index = 0;

    //初始化界面
    $(document).ready(function() {
        var Url = document.URL;
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


    var promise = new Promise(function(resolve, reject) {
        //获取后台数据
        $.ajax({
            url: "../getUserListTreeInfo.action",
            type: 'get',
            dataType: 'json',
            success: function(data) {
                if (data.total < 15) {
                    $("#tree").height(900);
                } else {
                    var multiple = Math.floor((data.total - 15) / 5);
                    var H = multiple * 300 + 900;
                    $("#tree").height(H);
                }
                resolve(data);
            },
            error: function() {
                layer.msg("加载数据失败", { time: 1500, icon: 2 });
            }
        })
    }).then(function(data) {

        //获取数据渲染页面
        var margin = { top: 20, right: 120, bottom: 20, left: 120 },
            width = document.getElementById("tree").offsetWidth,
            height = document.getElementById("tree").offsetHeight;

        var i = 0,
            duration = 750, //过渡延迟时间
            root,
            fontSize = 12, //字体大小
            nodeWidth = 120, //节点宽度
            nodeHeight = 30; //节点高度

        var tree = d3.layout.tree() //创建一个树布局
            .size([height, width]);

        //生成曲线
        var diagonal = d3.svg.diagonal()
            .projection(function(d) { return [d.y, d.x]; }); //创建新的斜线生成器

        //生成折线
        var funLine = function(obj) { //折线
            var s = obj.source;
            var t = obj.target;
            return "M" + s.y + "," + s.x + "L" + (s.y + (t.y - s.y) / 2) + "," + s.x + "L" + (s.y + (t.y - s.y) / 2) + "," + t.x + "L" + t.y + "," + t.x;

        }

        //声明与定义画布属性
        var svg = d3.select("body").select("#tree").append("svg")
            .attr("width", width)
            .attr("height", height)
            .append("g")
            .attr("transform", "translate(" + margin.left * 2 + "," + margin.top + ")");

        root = data; //treeData为上边定义的节点属性
        root.x0 = height / 2;
        root.y0 = 0;

        update(root);


        function update(source) {

            //计算新树图的布局
            var nodes = tree.nodes(root).reverse(),
                links = tree.links(nodes);

            //设置y坐标点，每层占200px
            nodes.forEach(function(d) { d.y = d.depth * 200; });

            // 每个node对应一个group
            var node = svg.selectAll("g.node")
                .data(nodes, function(d) { return d.id || (d.id = ++i); });
            //data()：绑定一个数组到选择集上，数组的各项值分别与选择集的各元素绑定

            //新增节点数据集，设置位置
            var nodeEnter = node.enter().append("g")
                //在 svg 中添加一个g，g是 svg 中的一个属性，是group的意思，它表示一组lines ， rects ，circles 其实坐标轴就是由这些东西构成的。
                .attr("class", "node")
                //attr设置html属性，style设置css属性
                //d 代表数据，也就是与某元素绑定的数据。
                .attr("transform", function(d) {
                    return "translate(" + source.y0 + "," + source.x0 + ")";
                })
                .on("mouseenter", hover)
                .on("mouseleave", hover);

            //添加连接点---此处设置的是圆圈过渡时候的效果（颜色）
            nodeEnter.append("rect")
                .attr("x", -nodeWidth / 2)
                .attr("y", -nodeHeight / 2)
                .attr("width", nodeWidth)
                .attr("height", nodeHeight)
                .style("fill", "#1ab394")
                .on("mouseenter", hover)
                .on("mouseleave", hover);

            nodeEnter.append("circle")
                .attr("r", function(d) {
                    //判断是否有子集，无子集不显示
                    return d.children || d._children ? 8 : 0;
                })
                .attr("class", function(d) {
                    return d.children || d._children ? "circle" : '';
                })
                .attr("cx", nodeWidth - 20)
                .style("fill", "#fff");

            //添加标签
            nodeEnter.append("text")
                .attr("dy", fontSize / 2 - 2)
                .text(function(d) { return d.name + "(" + d.title + ")"; })
                .style("fill", "white")
                .attr("text-anchor", "middle")
                .style("fill-opacity", 1e-6);

            //添加悬浮效果
            nodeEnter.append("rect")
                .attr("x", -nodeWidth / 2)
                .attr("y", nodeHeight / 2 + 5)
                .attr("width", nodeWidth)
                .attr("height", nodeHeight)
                .style("fill", "#1ab394")
                .attr("class", "hoverBox");

            //增加按钮
            nodeEnter.append("image")
                .attr("xlink:href", "../img/add.png")
                .attr("class", "addNode")
                .attr("x", -37)
                .attr("y", nodeHeight - 4)
                .on("click", addNode);

            //编辑按钮
            nodeEnter.append("image")
                .attr("xlink:href", "../img/edit.png")
                .attr("class", "editNode")
                .attr("x", -8)
                .attr("y", nodeHeight - 4)
                .on("click", editNode);

            //删除按钮
            nodeEnter.append("image")
                .attr("xlink:href", "../img/remove.png")
                .attr("class", "removeNode")
                .attr("x", 21)
                .attr("y", nodeHeight - 4)
                .on("click", removeNode);

            //收放按钮image
            nodeEnter.append("image")
                .attr("xlink:href", function(d) {
                    if (d.children) {
                        return "../img/in.png";
                    }
                    if (d._children) {
                        return '../img/out.png'
                    }
                })
                .attr("class", function(d) {
                    return d.children || d._children ? "imageNode" : 'none';
                })
                .attr("x", nodeWidth - 28)
                .attr("y", -8)
                .on("mouseenter", toggle)
                .on("mouseleave", toggle)
                .on("click", click)



            //将节点过渡到一个新的位置---主要是针对节点过渡过程中的过渡效果
            //node就是保留的数据集，为原来数据的图形添加过渡动画。首先是整个组的位置
            var nodeUpdate = node.transition() //开始一个动画过渡
                .duration(duration) //过渡延迟时间,此处主要设置的是圆圈节点随斜线的过渡延迟
                .attr("transform", function(d) {
                    return "translate(" + d.y + "," + d.x + ")";
                });

            //添加矩形
            nodeUpdate.select("rect")
                .attr("x", -nodeWidth / 2)
                .attr("y", -nodeHeight / 2)
                .attr("width", nodeWidth)
                .attr("height", nodeHeight)
                .style("fill", "#1ab394");

            nodeUpdate.select(".circle")
                .attr("r", function(d) {
                    return d.children || d._children ? 8 : 0;
                })
                .style("fill", "#fff");

            nodeUpdate.select("text")
                .attr("text-anchor", "middle")
                .style("fill-opacity", 1);

            nodeUpdate.select(".imageNode")
                .attr("xlink:href", function(d) {
                    if (d.children) {
                        return "../img/in.png";
                    }
                    if (d._children) {
                        return '../img/out.png'
                    }
                })

            //过渡现有的节点到父母的新位置,最后处理消失的数据，添加消失动画
            var nodeExit = node.exit().transition()
                .duration(duration)
                .attr("transform", function(d) {
                    return "translate(" + source.y + "," + source.x + ")";
                })
                .remove();

            nodeExit.select("rect")
                .attr("x", -nodeWidth / 2)
                .attr("y", -nodeHeight / 2)
                .attr("width", nodeWidth)
                .attr("height", nodeHeight)
                .attr("rx", 10)
                .style("fill", "#1ab394");

            nodeExit.select("circle")
                .attr("r", 0);

            nodeExit.select("text")
                .attr("text-anchor", "middle")
                .style("fill-opacity", 1e-6);

            //线操作相关,再处理连线集合
            var link = svg.selectAll("path.link")
                .data(links, function(d) {
                    return d.target.id;
                });

            //添加新的连线
            link.enter().insert("path", "g")
                .attr("class", "link")
                .attr("d", function(d) {
                    var o = { x: source.x0, y: source.y0 };
                    //diagonal - 生成一个二维贝塞尔连接器, 用于节点连接图.
                    // return diagonal({ source: o, target: p });
                    return funLine({ source: o, target: o }); //生成折线

                })
                .attr('marker-end', 'url(#arrow)');

            //将斜线过渡到新的位置
            //保留的连线添加过渡动画
            link.transition()
                .duration(duration)
                .attr("d", funLine);

            //过渡现有的斜线到父母的新位置,消失的连线添加过渡动画
            link.exit().transition()
                .duration(duration)
                .attr("d", function(d) {
                    var o = {
                        x: source.x,
                        y: source.y
                    };
                    return funLine({
                        source: o,
                        target: o
                    });
                })
                .remove();

            //将旧的斜线过渡效果隐藏
            nodes.forEach(function(d) {
                d.x0 = d.x;
                d.y0 = d.y;
            });
        }

        //定义一个将某节点折叠的函数,切换子节点事件
        function click(d) {
            if (d.children) {
                d._children = d.children;
                d.children = null;
            } else {
                d.children = d._children;
                d._children = null;
            }
            update(d);
        }

        //悬浮时间
        function hover() {
            var e = window.event || window.ev;
            if (e.type == "mouseenter") {
                $(this).find(".hoverBox").show();
                $(this).find(".addNode").css("opacity", "1");
                $(this).find(".editNode").css("opacity", "1");
                $(this).find(".removeNode").css("opacity", "1");
            } else if (e.type == "mouseleave") {
                $(this).find(".hoverBox").hide();
                $(this).find(".addNode").css("opacity", "0");
                $(this).find(".editNode").css("opacity", "0");
                $(this).find(".removeNode").css("opacity", "0");
            }
        }

        //
        function toggle() {
            var e = window.event || window.ev;
            if (e.type == "mouseenter") {
                $(this).parent().find(".hoverBox").hide();
                $(this).find(".addNode").css("opacity", "0");
                $(this).find(".editNode").css("opacity", "0");
                $(this).find(".removeNode").css("opacity", "0");
            } else if (e.type == "mouseleave") {
                $(this).parent().find(".hoverBox").show();
                $(this).find(".addNode").css("opacity", "1");
                $(this).find(".editNode").css("opacity", "1");
                $(this).find(".removeNode").css("opacity", "1");
            }
        }

        //添加
        function addNode(d) {
            var type = d.optype;
            if (type == 2) {
                swal({
                    title: "提示信息",
                    text: "用户无添加权限"
                });
                return;
            } else {
                layer.open({
                    type: 2,
                    title: '用户添加',
                    shadeClose: true,
                    shade: 0.4,
                    maxmin: true,
                    area: ['80%', '90%'],
                    content: ['sywdata_userinfo.html?ioptype=' + ioptype + '-' + opcode + '-' + opname + '']
                });
            }
        }

        //修改
        function editNode(d) {
            var optype = d.optype;
            var code = d.id;
            var name = d.name;
            layer.open({
                type: 2,
                title: '用户[' + name + ']修改',
                shadeClose: true,
                shade: 0.4,
                maxmin: true,
                area: ['80%', '90%'],
                content: ['sywdata_userinfo.html?ioptype=' + ioptype + '&op_type=' + optype + '&op_code=' + code + '&modify=1']
            });
        }

        //删除
        function removeNode(d) {
            var code = d.id + "";
            var name = d.name;
            if (name == 'admin') {
                swal({
                    title: "提示信息",
                    text: "超级管理员 001 不能被删除"
                });
                return;
            }
            swal({
                    title: "用户删除",
                    text: "你确定删除用户 [" + name + "] 吗?",
                    type: "warning",
                    showCancelButton: true,
                    confirmButtonColor: "#DD6B55",
                    confirmButtonText: "删除",
                    closeOnConfirm: false
                },
                function() {
                    showWaitDialog();
                    var param = {
                        Op_Code: code,
                    };
                    $.ajaxPost("../deleteUserInfo.action", param, function(data) {
                        closeWaitDialog();
                        if (data.isSuccess == true) {
                            swal({
                                title: "提示信息",
                                text: "删除用户[" + name + "]成功"
                            });
                            location.reload();
                        } else {
                            swal({
                                title: "提示信息",
                                text: "删除用户[" + name + "]失败"
                            });
                        }

                    });
                }
            )
        }

        //显示等待提示框
        function showWaitDialog() {
            index = parent.layer.open({
                type: 1,
                shade: false,
                title: false, //不显示标题
                closeBtn: false, //不显示关闭按钮
                area: ['220px', '120px'], //宽高
                content: "<div style='padding-top:50px'><div class='sk-spinner sk-spinner-three-bounce'>\
	            <div class='sk-bounce1'></div>\
	            <div class='sk-bounce2'></div>\
	            <div class='sk-bounce3'></div>\
	         	</div></div>", //捕获的元素
            });
        }

        //关闭等待提示框
        function closeWaitDialog() {
            parent.layer.close(index);
        }
    })

    // 刷新按钮
    $(".fixedRightBox").on("click", ".refresh", function() {
        location.reload();
    })

    //向上
    $(".fixedRightBox").on("click", ".toTop", function() {
        document.scrollTop = 0;
    })
});