(window["webpackJsonp"]=window["webpackJsonp"]||[]).push([["chunk-c983dcc8"],{"02f4":function(t,e,o){var n=o("4588"),i=o("be13");t.exports=function(t){return function(e,o){var r,s,l=String(i(e)),a=n(o),c=l.length;return a<0||a>=c?t?"":void 0:(r=l.charCodeAt(a),r<55296||r>56319||a+1===c||(s=l.charCodeAt(a+1))<56320||s>57343?t?l.charAt(a):r:t?l.slice(a,a+2):s-56320+(r-55296<<10)+65536)}}},"0390":function(t,e,o){"use strict";var n=o("02f4")(!0);t.exports=function(t,e,o){return e+(o?n(t,e).length:1)}},"0bfb":function(t,e,o){"use strict";var n=o("cb7c");t.exports=function(){var t=n(this),e="";return t.global&&(e+="g"),t.ignoreCase&&(e+="i"),t.multiline&&(e+="m"),t.unicode&&(e+="u"),t.sticky&&(e+="y"),e}},"0f4d":function(t,e,o){},"1bab":function(t,e,o){"use strict";o.d(e,"a",(function(){return s}));o("28a5");var n=o("bc3a"),i=o.n(n),r=o("5c96");function s(t){var e=i.a.create({headers:{"Content-Type":"application/x-www-form-urlencoded;charset=UTF-8"}});return e.interceptors.request.use((function(t){return t.method,(t.url.indexOf("export")>-1||t.url.indexOf("Export")>-1)&&(t.responseType="blob"),t}),(function(t){Promise.reject(t)})),e.interceptors.response.use((function(t){var e=t.data;return 200!==t.status?(console.log(t.status),Promise.reject(e.msg)):t}),(function(t){var e="";return""==t.message?(e="请求数据不存在",e=404===t.response.status?"请求数据不存在":"系统出现错误信息"):e="ECONNABORTED"===t.code?"连接超时":t.message,Object(r["Message"])({message:e,type:"error",duration:5e3}),Promise.reject(t)})),e(t)}i.a.defaults.timeout=18e5},"214f":function(t,e,o){"use strict";o("b0c5");var n=o("2aba"),i=o("32e9"),r=o("79e5"),s=o("be13"),l=o("2b4c"),a=o("520a"),c=l("species"),u=!r((function(){var t=/./;return t.exec=function(){var t=[];return t.groups={a:"7"},t},"7"!=="".replace(t,"$<a>")})),f=function(){var t=/(?:)/,e=t.exec;t.exec=function(){return e.apply(this,arguments)};var o="ab".split(t);return 2===o.length&&"a"===o[0]&&"b"===o[1]}();t.exports=function(t,e,o){var p=l(t),d=!r((function(){var e={};return e[p]=function(){return 7},7!=""[t](e)})),h=d?!r((function(){var e=!1,o=/a/;return o.exec=function(){return e=!0,null},"split"===t&&(o.constructor={},o.constructor[c]=function(){return o}),o[p](""),!e})):void 0;if(!d||!h||"replace"===t&&!u||"split"===t&&!f){var m=/./[p],g=o(s,p,""[t],(function(t,e,o,n,i){return e.exec===a?d&&!i?{done:!0,value:m.call(e,o,n)}:{done:!0,value:t.call(o,e,n)}:{done:!1}})),v=g[0],b=g[1];n(String.prototype,t,v),i(RegExp.prototype,p,2==e?function(t,e){return b.call(t,this,e)}:function(t){return b.call(t,this)})}}},"28a5":function(t,e,o){"use strict";var n=o("aae3"),i=o("cb7c"),r=o("ebd6"),s=o("0390"),l=o("9def"),a=o("5f1b"),c=o("520a"),u=o("79e5"),f=Math.min,p=[].push,d="split",h="length",m="lastIndex",g=4294967295,v=!u((function(){RegExp(g,"y")}));o("214f")("split",2,(function(t,e,o,u){var b;return b="c"=="abbc"[d](/(b)*/)[1]||4!="test"[d](/(?:)/,-1)[h]||2!="ab"[d](/(?:ab)*/)[h]||4!="."[d](/(.?)(.?)/)[h]||"."[d](/()()/)[h]>1||""[d](/.?/)[h]?function(t,e){var i=String(this);if(void 0===t&&0===e)return[];if(!n(t))return o.call(i,t,e);var r,s,l,a=[],u=(t.ignoreCase?"i":"")+(t.multiline?"m":"")+(t.unicode?"u":"")+(t.sticky?"y":""),f=0,d=void 0===e?g:e>>>0,v=new RegExp(t.source,u+"g");while(r=c.call(v,i)){if(s=v[m],s>f&&(a.push(i.slice(f,r.index)),r[h]>1&&r.index<i[h]&&p.apply(a,r.slice(1)),l=r[0][h],f=s,a[h]>=d))break;v[m]===r.index&&v[m]++}return f===i[h]?!l&&v.test("")||a.push(""):a.push(i.slice(f)),a[h]>d?a.slice(0,d):a}:"0"[d](void 0,0)[h]?function(t,e){return void 0===t&&0===e?[]:o.call(this,t,e)}:o,[function(o,n){var i=t(this),r=void 0==o?void 0:o[e];return void 0!==r?r.call(o,i,n):b.call(String(i),o,n)},function(t,e){var n=u(b,t,this,e,b!==o);if(n.done)return n.value;var c=i(t),p=String(this),d=r(c,RegExp),h=c.unicode,m=(c.ignoreCase?"i":"")+(c.multiline?"m":"")+(c.unicode?"u":"")+(v?"y":"g"),y=new d(v?c:"^(?:"+c.source+")",m),x=void 0===e?g:e>>>0;if(0===x)return[];if(0===p.length)return null===a(y,p)?[p]:[];var S=0,w=0,k=[];while(w<p.length){y.lastIndex=v?w:0;var _,C=a(y,v?p:p.slice(w));if(null===C||(_=f(l(y.lastIndex+(v?0:w)),p.length))===S)w=s(p,w,h);else{if(k.push(p.slice(S,w)),k.length===x)return k;for(var E=1;E<=C.length-1;E++)if(k.push(C[E]),k.length===x)return k;w=S=_}}return k.push(p.slice(S)),k}]}))},"520a":function(t,e,o){"use strict";var n=o("0bfb"),i=RegExp.prototype.exec,r=String.prototype.replace,s=i,l="lastIndex",a=function(){var t=/a/,e=/b*/g;return i.call(t,"a"),i.call(e,"a"),0!==t[l]||0!==e[l]}(),c=void 0!==/()??/.exec("")[1],u=a||c;u&&(s=function(t){var e,o,s,u,f=this;return c&&(o=new RegExp("^"+f.source+"$(?!\\s)",n.call(f))),a&&(e=f[l]),s=i.call(f,t),a&&s&&(f[l]=f.global?s.index+s[0].length:e),c&&s&&s.length>1&&r.call(s[0],o,(function(){for(u=1;u<arguments.length-2;u++)void 0===arguments[u]&&(s[u]=void 0)})),s}),t.exports=s},"5f1b":function(t,e,o){"use strict";var n=o("23c6"),i=RegExp.prototype.exec;t.exports=function(t,e){var o=t.exec;if("function"===typeof o){var r=o.call(t,e);if("object"!==typeof r)throw new TypeError("RegExp exec method returned something other than an Object or null");return r}if("RegExp"!==n(t))throw new TypeError("RegExp#exec called on incompatible receiver");return i.call(t,e)}},"65d5":function(t,e,o){"use strict";var n=o("7d4b"),i=o.n(n);i.a},"6bdf":function(t,e,o){},"7d4b":function(t,e,o){},8021:function(t,e,o){"use strict";var n=function(){var t=this,e=t.$createElement,o=t._self._c||e;return o("div",[o("el-dialog",{attrs:{title:"日志",visible:t.showModal},on:{"update:visible":function(e){t.showModal=e}}},[o("textarea",{staticStyle:{overflow:"scroll"},attrs:{id:"logContent","vertical-align":"middle",readonly:"readonly",cols:"80",rows:"20"}}),o("span",{staticClass:"dialog-footer",attrs:{slot:"footer"},slot:"footer"},[o("el-button",{attrs:{type:"primary"},on:{click:t.closeModal}},[t._v("关闭")])],1)])],1)},i=[],r={name:"Log",data:function(){return{showModal:!1,socket:null}},props:{title:{type:String,default:""}},mounted:function(){this.initWebSocket()},methods:{closeModal:function(){document.querySelector("#logContent").value="",this.showModal=!1},openModal:function(){this.showModal=!0,this.initWebSocket()},receive:function(t){document.querySelector("#logContent").value+=t.message},initWebSocket:function(){var t="ws://".concat(window.location.host,"/ws/")+this.title+"/log/";this.socket=new WebSocket(t),this.socket.onmessage=function(t){var e=JSON.parse(t.data);document.querySelector("#logContent").value+=e.message},this.socket.onclose=function(){console.log("websocket关闭"),this.socket=null},this.socket.onopen=function(){console.log("websocket打开")},this.socket.onerror=function(){console.log("websocket连接错误")}},closeWebSocket:function(){null!=this.socket&&this.socket.close()}}},s=r,l=(o("efff"),o("2877")),a=Object(l["a"])(s,n,i,!1,null,"017ec3ad",null);e["a"]=a.exports},"9cae":function(t,e,o){"use strict";var n=o("6bdf"),i=o.n(n);i.a},"9d5e":function(t,e,o){"use strict";function n(t,e){console.log("export");var o=new Blob([t],{type:"application/zip"}),n=e,i=document.createElement("a");i.download=n,i.style.display="none",i.href=window.URL.createObjectURL(o),document.body.appendChild(i),i.click(),window.URL.revokeObjectURL(i.href),document.body.removeChild(i)}function i(){var t=new Date,e=t.getFullYear(),o=t.getMonth()+1,n=t.getDate(),i=t.getHours(),r=t.getMinutes(),s=t.getSeconds();return o=o>9?o:"0"+o,n=n>9?n:"0"+n,i=i>9?i:"0"+i,r=r>9?r:"0"+r,s=s>9?s:"0"+s,""+e+o+n+i+r+s}o.d(e,"a",(function(){return n})),o.d(e,"b",(function(){return i}))},b0c5:function(t,e,o){"use strict";var n=o("520a");o("5ca1")({target:"RegExp",proto:!0,forced:n!==/./.exec},{exec:n})},b5a1:function(t,e,o){"use strict";o.r(e);var n=function(){var t=this,e=t.$createElement,o=t._self._c||e;return o("div",{staticClass:"main",staticStyle:{width:"100%",height:"100%"}},[o("child",{ref:"mychild",attrs:{title:t.logTitle}}),o("div",{staticClass:"main-inner"},[o("div",{staticClass:"title"},[t._v("\n            温度补偿测试配置\n        ")]),o("div",{staticClass:"content"},[o("div",{staticStyle:{padding:"0 20px 25px",width:"100%",height:"calc(100% - 18px)"}},[o("div",{ref:"scrollDiv",attrs:{id:"scrollOuterDiv"},on:{scroll:t.scrollEvent}},[o("div",{staticClass:"scrollDiv",staticStyle:{height:"100%"}},[o("div",{staticClass:"red"},[o("el-row",{staticStyle:{height:"100%"},attrs:{gutter:24}},[o("el-col",{staticStyle:{height:"calc(100%-30px)"},attrs:{span:24}},[o("el-form",{ref:"Lform",staticStyle:{"margin-top":"20px",border:"1px solid #EBEEF5",padding:"10px",height:"calc(100% - 1px)"},attrs:{model:t.form.Info,size:"mini","label-width":"180px",inline:!0,rules:t.Rules}},[o("el-form-item",{staticStyle:{"margin-top":"1px"},attrs:{label:"频谱仪IP地址：",prop:"fsvip"}},[o("el-input",{model:{value:t.form.Info.fsvip,callback:function(e){t.$set(t.form.Info,"fsvip",e)},expression:"form.Info.fsvip"}})],1),o("br"),o("el-form-item",{attrs:{label:"测试模板的目录："}},[o("el-upload",{ref:"upload",staticClass:"upload-demo",attrs:{limit:1,accept:".xlsx",action:"action","on-change":t.handleChange,"http-request":t.fileUpload,"file-list":t.fileList,"auto-upload":!1}},[o("el-button",{attrs:{slot:"trigger",size:"mini",type:"primary"},slot:"trigger"},[t._v("选取文件")])],1)],1),o("br"),o("el-form-item",{staticStyle:{"margin-top":"1px"},attrs:{label:"设备IP地址：",prop:"boardip"}},[o("el-input",{model:{value:t.form.Info.boardip,callback:function(e){t.$set(t.form.Info,"boardip",e)},expression:"form.Info.boardip"}})],1),o("br"),o("el-form-item",{attrs:{label:"温箱串口号：",prop:"port"}},[o("el-input",{attrs:{type:"number"},model:{value:t.form.Info.port,callback:function(e){t.$set(t.form.Info,"port",e)},expression:"form.Info.port"}})],1),o("br"),o("br")],1)],1),o("el-col",{staticStyle:{"text-align":"center"},attrs:{span:24}},[o("el-button",{staticStyle:{"margin-top":"30px"},attrs:{size:"mini",type:"primary"},on:{click:function(e){return t.set("Lform")}}},[t._v("设置")]),o("el-button",{staticStyle:{"margin-top":"30px"},attrs:{size:"mini",type:"primary"},on:{click:t.stopProcess}},[t._v("停止")]),o("el-button",{attrs:{size:"mini",type:"primary"},on:{click:t.exportResult}},[t._v("下载")])],1)],1)],1),o("div",{staticClass:"red"},[o("h3",{staticClass:"equipmentTitle",staticStyle:{"line-height":"20px",position:"relative"}},[t._v("\n                                历史信息\n                                "),o("el-form",{staticStyle:{"text-align":"right",position:"absolute",right:"0",top:"0","margin-top":"10px"},attrs:{size:"mini"}},[o("el-button",{attrs:{size:"mini",type:"primary"},on:{click:t.query}},[t._v("查询")]),o("el-button",{attrs:{size:"mini",type:"primary"},on:{click:t.clearHistory}},[t._v("清空")]),o("el-button",{attrs:{size:"mini",type:"primary"},on:{click:t.stopProcess}},[t._v("停止")])],1)],1),o("el-table",{staticStyle:{width:"100%","margin-top":"30px"},attrs:{data:t.infos,border:""}},[o("el-table-column",{attrs:{fiexed:"left",align:"center",prop:"idx",label:"编号"},scopedSlots:t._u([{key:"default",fn:function(e){return[t._v(t._s(e.row.pk))]}}])}),o("el-table-column",{attrs:{align:"center",prop:"fsvip",label:"频谱仪IP"},scopedSlots:t._u([{key:"default",fn:function(e){return[t._v(t._s(e.row.fields.fsvip))]}}])}),o("el-table-column",{attrs:{align:"center",prop:"dir",label:"测试模板路径"},scopedSlots:t._u([{key:"default",fn:function(e){return[t._v(t._s(e.row.fields.dir))]}}])}),o("el-table-column",{attrs:{align:"center",prop:"boardip",label:"设备IP"},scopedSlots:t._u([{key:"default",fn:function(e){return[t._v(t._s(e.row.fields.boardip))]}}])}),o("el-table-column",{attrs:{align:"center",prop:"port",label:"串口号"},scopedSlots:t._u([{key:"default",fn:function(e){return[t._v(t._s(e.row.fields.port))]}}])}),o("el-table-column",{attrs:{fixed:"right",label:"操作"},scopedSlots:t._u([{key:"default",fn:function(e){return[o("el-button",{attrs:{size:"mini",type:"primary"},on:{click:function(o){return t.handleClick(e.row)}}},[t._v("设置")])]}}])})],1)],1)])]),o("div",{staticClass:"indexs",staticStyle:{"margin-top":"20px"}},[o("el-button-group",t._l(t.titleList,(function(e,n){return o("el-button",{style:e.style,attrs:{size:"mini",type:"primary",plain:""},on:{click:function(o){return t.titleClick(e,n)}}},[t._v(t._s(e.info))])})),1)],1)])])])],1)},i=[],r=(o("ac6a"),o("1bab")),s=o("9d5e"),l=o("8021"),a={name:"",components:{child:l["a"]},data:function(){return{filepath:"",logTitle:"tempcomp",runningState:!1,n:0,finished:!0,currentScrollTop:0,preScrollTop:0,action:"/us-base/tempcomp/",form:{Info:{fsvip:"",boardip:"",port:""}},infos:[],Rules:{fsvip:[{required:!0,message:"请输入频谱仪IP",trigger:"blur"}],boardip:[{required:!0,message:"请输入设备IP",trigger:"blur"}],port:[{required:!0,message:"请输入串口号",trigger:"blur"}]},formdata:"",fileContent:"",fileList:[],titleList:[{info:"基本信息",style:"background:#409EFF;color:#fff;border-color:#409EFF"},{info:"历史信息",style:""}]}},created:function(){},mounted:function(){this.query()},beforeDestroy:function(){this.$refs.mychild.closeWebSocket()},computed:{},watch:{},methods:{stopProcess:function(){console.log("stopprocess"),this.$refs.mychild.closeWebSocket(),this.runningState=!1,this.$message.success("已停止测试")},scrollEvent:function(){if(this.finished){var t=this;this.finished=!1;var e=document.getElementsByClassName("red")[0].clientHeight;this.currentScrollTop=this.$refs.scrollDiv.scrollTop,this.preScrollTop<this.currentScrollTop?this.n++:this.preScrollTop>this.currentScrollTop&&this.n>=1&&this.n--,this.$refs.scrollDiv.scrollTop=e*this.n,this.titleList.forEach((function(t,e){t.style=""})),this.titleList[this.n].style="background:#409EFF;color:#fff;border-color:#409EFF",this.preScrollTop=this.$refs.scrollDiv.scrollTop,t.finished=!0}},titleClick:function(t,e){this.n=e;var o=this;this.finished=!1;var n=document.getElementsByClassName("red")[0].clientHeight;this.$refs.scrollDiv.scrollTop=n*this.n,this.titleList.forEach((function(t,e){t.style=""})),this.titleList[this.n].style="background:#409EFF;color:#fff;border-color:#409EFF",this.preScrollTop=this.$refs.scrollDiv.scrollTop,setTimeout((function(){o.finished=!0}),0)},query:function(){var t=this;Object(r["a"])({method:"post",url:"/tempcomp/show_history/"}).then((function(e){var o=e.data;0===o["error_num"]?(t.infos=o["params"],t.$message.success(o["msg"])):t.$message.error(o["msg"])}))},clearHistory:function(){var t=this;Object(r["a"])({method:"post",url:"/tempcomp/clear_history/"}).then((function(e){console.log(e);var o=e.data;0===o["error_num"]?(t.infos=[],t.$message.success(o["msg"])):t.$message.error(o["msg"])}))},handleClick:function(t){var e=this;if(this.runningState)this.$message.warning("正在运行中，请稍后");else{this.runningState=!0,this.$refs.mychild.openModal();var o={fsvip:t.fields.fsvip,dir:t.fields.dir,boardip:t.fields.boardip,port:t.fields.port};Object(r["a"])({method:"post",url:"/tempcomp/set_history/",data:o}).then((function(t){if(console.log(t),e.runningState=!1,200===t.status){var o=t.data,n=o.message;o.result?(e.filepath=o.filepath,e.$message.success(n)):e.$message.error(n)}}))}},handleChange:function(t,e){this.fileList=e.slice(-1)},fileUpload:function(t){this.fileContent=t.file},set:function(t){var e=this,o=this;this.$refs[t].validate((function(t){if(t){if(o.runningState)return void e.$message.warning("正在运行中，请稍后");e.runningState=!0,e.$refs.mychild.openModal(),e.$refs.upload.submit(),e.formdata=new FormData,e.formdata.append("file",e.fileContent),e.formdata.append("fsvip",o.form.Info.fsvip),e.formdata.append("boardip",o.form.Info.boardip),e.formdata.append("port",o.form.Info.port),Object(r["a"])({method:"post",url:"/tempcomp/upload/",data:e.formdata}).then((function(t){if(console.log(t),e.runningState=!1,200===t.status){var o=t.data,n=o.message;o.result?(e.$message.success(n),e.filepath=o.filepath,console.log(e.filepath)):e.$message.error(n)}}))}}))},exportResult:function(){this.filepath?Object(r["a"])({method:"post",url:"/tempcomp/export/",data:{filepath:this.filepath}}).then((function(t){var e=Object(s["b"])()+".zip";console.log(e),Object(s["a"])(t.data,e)})).catch((function(t){console.log(t)})):this.$message.error("没有结果可下载")},wdTableScrollEvent:function(t){return console.log(t),t.stopPropagation(),t.preventDefault(),!1}}},c=a,u=(o("9cae"),o("65d5"),o("2877")),f=Object(u["a"])(c,n,i,!1,null,"2dccdedc",null);e["default"]=f.exports},efff:function(t,e,o){"use strict";var n=o("0f4d"),i=o.n(n);i.a}}]);