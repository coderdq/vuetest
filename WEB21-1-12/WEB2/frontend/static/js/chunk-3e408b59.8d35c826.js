(window["webpackJsonp"]=window["webpackJsonp"]||[]).push([["chunk-3e408b59"],{"02f4":function(t,e,o){var n=o("4588"),r=o("be13");t.exports=function(t){return function(e,o){var i,l,s=String(r(e)),a=n(o),c=s.length;return a<0||a>=c?t?"":void 0:(i=s.charCodeAt(a),i<55296||i>56319||a+1===c||(l=s.charCodeAt(a+1))<56320||l>57343?t?s.charAt(a):i:t?s.slice(a,a+2):l-56320+(i-55296<<10)+65536)}}},"0390":function(t,e,o){"use strict";var n=o("02f4")(!0);t.exports=function(t,e,o){return e+(o?n(t,e).length:1)}},"0bfb":function(t,e,o){"use strict";var n=o("cb7c");t.exports=function(){var t=n(this),e="";return t.global&&(e+="g"),t.ignoreCase&&(e+="i"),t.multiline&&(e+="m"),t.unicode&&(e+="u"),t.sticky&&(e+="y"),e}},"0f4d":function(t,e,o){},"1bab":function(t,e,o){"use strict";o.d(e,"a",(function(){return l}));o("28a5");var n=o("bc3a"),r=o.n(n),i=o("5c96");function l(t){var e=r.a.create({headers:{"Content-Type":"application/x-www-form-urlencoded;charset=UTF-8"}});return e.interceptors.request.use((function(t){return t.method,(t.url.indexOf("export")>-1||t.url.indexOf("Export")>-1)&&(t.responseType="blob"),t}),(function(t){Promise.reject(t)})),e.interceptors.response.use((function(t){var e=t.data;return 200!==t.status?(console.log(t.status),Promise.reject(e.msg)):t}),(function(t){var e="";return""==t.message?(e="请求数据不存在",e=404===t.response.status?"请求数据不存在":"系统出现错误信息"):e="ECONNABORTED"===t.code?"连接超时":t.message,Object(i["Message"])({message:e,type:"error",duration:5e3}),Promise.reject(t)})),e(t)}r.a.defaults.timeout=18e5},"214f":function(t,e,o){"use strict";o("b0c5");var n=o("2aba"),r=o("32e9"),i=o("79e5"),l=o("be13"),s=o("2b4c"),a=o("520a"),c=s("species"),f=!i((function(){var t=/./;return t.exec=function(){var t=[];return t.groups={a:"7"},t},"7"!=="".replace(t,"$<a>")})),u=function(){var t=/(?:)/,e=t.exec;t.exec=function(){return e.apply(this,arguments)};var o="ab".split(t);return 2===o.length&&"a"===o[0]&&"b"===o[1]}();t.exports=function(t,e,o){var p=s(t),d=!i((function(){var e={};return e[p]=function(){return 7},7!=""[t](e)})),m=d?!i((function(){var e=!1,o=/a/;return o.exec=function(){return e=!0,null},"split"===t&&(o.constructor={},o.constructor[c]=function(){return o}),o[p](""),!e})):void 0;if(!d||!m||"replace"===t&&!f||"split"===t&&!u){var h=/./[p],g=o(l,p,""[t],(function(t,e,o,n,r){return e.exec===a?d&&!r?{done:!0,value:h.call(e,o,n)}:{done:!0,value:t.call(o,e,n)}:{done:!1}})),b=g[0],v=g[1];n(String.prototype,t,b),r(RegExp.prototype,p,2==e?function(t,e){return v.call(t,this,e)}:function(t){return v.call(t,this)})}}},"28a5":function(t,e,o){"use strict";var n=o("aae3"),r=o("cb7c"),i=o("ebd6"),l=o("0390"),s=o("9def"),a=o("5f1b"),c=o("520a"),f=o("79e5"),u=Math.min,p=[].push,d="split",m="length",h="lastIndex",g=4294967295,b=!f((function(){RegExp(g,"y")}));o("214f")("split",2,(function(t,e,o,f){var v;return v="c"=="abbc"[d](/(b)*/)[1]||4!="test"[d](/(?:)/,-1)[m]||2!="ab"[d](/(?:ab)*/)[m]||4!="."[d](/(.?)(.?)/)[m]||"."[d](/()()/)[m]>1||""[d](/.?/)[m]?function(t,e){var r=String(this);if(void 0===t&&0===e)return[];if(!n(t))return o.call(r,t,e);var i,l,s,a=[],f=(t.ignoreCase?"i":"")+(t.multiline?"m":"")+(t.unicode?"u":"")+(t.sticky?"y":""),u=0,d=void 0===e?g:e>>>0,b=new RegExp(t.source,f+"g");while(i=c.call(b,r)){if(l=b[h],l>u&&(a.push(r.slice(u,i.index)),i[m]>1&&i.index<r[m]&&p.apply(a,i.slice(1)),s=i[0][m],u=l,a[m]>=d))break;b[h]===i.index&&b[h]++}return u===r[m]?!s&&b.test("")||a.push(""):a.push(r.slice(u)),a[m]>d?a.slice(0,d):a}:"0"[d](void 0,0)[m]?function(t,e){return void 0===t&&0===e?[]:o.call(this,t,e)}:o,[function(o,n){var r=t(this),i=void 0==o?void 0:o[e];return void 0!==i?i.call(o,r,n):v.call(String(r),o,n)},function(t,e){var n=f(v,t,this,e,v!==o);if(n.done)return n.value;var c=r(t),p=String(this),d=i(c,RegExp),m=c.unicode,h=(c.ignoreCase?"i":"")+(c.multiline?"m":"")+(c.unicode?"u":"")+(b?"y":"g"),y=new d(b?c:"^(?:"+c.source+")",h),x=void 0===e?g:e>>>0;if(0===x)return[];if(0===p.length)return null===a(y,p)?[p]:[];var w=0,k=0,S=[];while(k<p.length){y.lastIndex=b?k:0;var I,_=a(y,b?p:p.slice(k));if(null===_||(I=u(s(y.lastIndex+(b?0:k)),p.length))===w)k=l(p,k,m);else{if(S.push(p.slice(w,k)),S.length===x)return S;for(var T=1;T<=_.length-1;T++)if(S.push(_[T]),S.length===x)return S;k=w=I}}return S.push(p.slice(w)),S}]}))},"3b41":function(t,e,o){},"40d5":function(t,e,o){"use strict";var n=o("3b41"),r=o.n(n);r.a},"520a":function(t,e,o){"use strict";var n=o("0bfb"),r=RegExp.prototype.exec,i=String.prototype.replace,l=r,s="lastIndex",a=function(){var t=/a/,e=/b*/g;return r.call(t,"a"),r.call(e,"a"),0!==t[s]||0!==e[s]}(),c=void 0!==/()??/.exec("")[1],f=a||c;f&&(l=function(t){var e,o,l,f,u=this;return c&&(o=new RegExp("^"+u.source+"$(?!\\s)",n.call(u))),a&&(e=u[s]),l=r.call(u,t),a&&l&&(u[s]=u.global?l.index+l[0].length:e),c&&l&&l.length>1&&i.call(l[0],o,(function(){for(f=1;f<arguments.length-2;f++)void 0===arguments[f]&&(l[f]=void 0)})),l}),t.exports=l},"5f1b":function(t,e,o){"use strict";var n=o("23c6"),r=RegExp.prototype.exec;t.exports=function(t,e){var o=t.exec;if("function"===typeof o){var i=o.call(t,e);if("object"!==typeof i)throw new TypeError("RegExp exec method returned something other than an Object or null");return i}if("RegExp"!==n(t))throw new TypeError("RegExp#exec called on incompatible receiver");return r.call(t,e)}},8021:function(t,e,o){"use strict";var n=function(){var t=this,e=t.$createElement,o=t._self._c||e;return o("div",[o("el-dialog",{attrs:{title:"日志",visible:t.showModal},on:{"update:visible":function(e){t.showModal=e}}},[o("textarea",{staticStyle:{overflow:"scroll"},attrs:{id:"logContent","vertical-align":"middle",readonly:"readonly",cols:"80",rows:"20"}}),o("span",{staticClass:"dialog-footer",attrs:{slot:"footer"},slot:"footer"},[o("el-button",{attrs:{type:"primary"},on:{click:t.closeModal}},[t._v("关闭")])],1)])],1)},r=[],i={name:"Log",data:function(){return{showModal:!1,socket:null}},props:{title:{type:String,default:""}},mounted:function(){this.initWebSocket()},methods:{closeModal:function(){document.querySelector("#logContent").value="",this.showModal=!1},openModal:function(){this.showModal=!0,this.initWebSocket()},receive:function(t){document.querySelector("#logContent").value+=t.message},initWebSocket:function(){var t="ws://".concat(window.location.host,"/ws/")+this.title+"/log/";this.socket=new WebSocket(t),this.socket.onmessage=function(t){var e=JSON.parse(t.data);document.querySelector("#logContent").value+=e.message},this.socket.onclose=function(){console.log("websocket关闭"),this.socket=null},this.socket.onopen=function(){console.log("websocket打开")},this.socket.onerror=function(){console.log("websocket连接错误")}},closeWebSocket:function(){null!=this.socket&&this.socket.close()}}},l=i,s=(o("efff"),o("2877")),a=Object(s["a"])(l,n,r,!1,null,"017ec3ad",null);e["a"]=a.exports},"858e":function(t,e,o){},"9d5e":function(t,e,o){"use strict";function n(t,e){console.log("export");var o=new Blob([t],{type:"application/zip"}),n=e,r=document.createElement("a");r.download=n,r.style.display="none",r.href=window.URL.createObjectURL(o),document.body.appendChild(r),r.click(),window.URL.revokeObjectURL(r.href),document.body.removeChild(r)}function r(){var t=new Date,e=t.getFullYear(),o=t.getMonth()+1,n=t.getDate(),r=t.getHours(),i=t.getMinutes(),l=t.getSeconds();return o=o>9?o:"0"+o,n=n>9?n:"0"+n,r=r>9?r:"0"+r,i=i>9?i:"0"+i,l=l>9?l:"0"+l,""+e+o+n+r+i+l}o.d(e,"a",(function(){return n})),o.d(e,"b",(function(){return r}))},a889:function(t,e,o){"use strict";o.r(e);var n=function(){var t=this,e=t.$createElement,o=t._self._c||e;return o("div",{staticClass:"main",staticStyle:{width:"100%",height:"100%"}},[o("child",{ref:"mychild",attrs:{title:t.logTitle}}),o("div",{staticClass:"main-inner"},[o("div",{staticClass:"title"},[t._v("\n                T2K整机定标\n            ")]),o("div",{staticClass:"content"},[o("div",{staticStyle:{padding:"0 20px 25px",width:"100%",height:"calc(100% - 18px)"}},[o("div",{ref:"scrollDiv",attrs:{id:"scrollOuterDiv"},on:{scroll:t.scrollEvent}},[o("div",{staticClass:"scrollDiv",staticStyle:{height:"100%"}},[o("div",{staticClass:"red"},[o("el-row",{staticStyle:{height:"100%"},attrs:{gutter:24}},[o("el-col",{staticStyle:{height:"calc(100%-30px)"},attrs:{span:12}},[o("el-form",{ref:"Cform",staticStyle:{"margin-top":"20px",border:"1px solid #EBEEF5",padding:"10px",height:"calc(100% - 1px)"},attrs:{model:t.form.Info,size:"mini","label-width":"180px",inline:!0,rules:t.Rules}},[o("el-form-item",{staticStyle:{"margin-top":"1px"},attrs:{label:"频谱仪IP地址：",prop:"fsvip"}},[o("el-input",{model:{value:t.form.Info.fsvip,callback:function(e){t.$set(t.form.Info,"fsvip",e)},expression:"form.Info.fsvip"}})],1),o("br"),o("el-form-item",{attrs:{label:"测试模板的目录："}},[o("el-upload",{ref:"upload",staticClass:"upload-demo",attrs:{limit:1,accept:".xlsx",action:"action","on-change":t.handleChange,"http-request":t.fileUpload,"file-list":t.fileList,"auto-upload":!1}},[o("el-button",{attrs:{slot:"trigger",size:"mini",type:"primary"},slot:"trigger"},[t._v("选取文件")])],1)],1),o("br"),o("el-form-item",{attrs:{label:"设备IP：",prop:"ip"}},[o("el-input",{model:{value:t.form.Info.ip,callback:function(e){t.$set(t.form.Info,"ip",e)},expression:"form.Info.ip"}})],1),o("br")],1)],1),o("el-col",{staticStyle:{height:"calc(100%-30px)"},attrs:{span:12}},[o("el-form",{staticStyle:{"margin-top":"20px",border:"1px solid #EBEEF5",padding:"10px",height:"calc(100% - 1px)"},attrs:{model:t.form.Info,size:"mini","label-width":"120px",inline:!0}},[o("el-form-item",{attrs:{label:"端口号：",prop:"port"}},[o("el-input",{attrs:{type:"number"},model:{value:t.form.Info.THInfo.port,callback:function(e){t.$set(t.form.Info.THInfo,"port",e)},expression:"form.Info.THInfo.port"}})],1),o("br"),o("el-form-item",{attrs:{label:"低温：",prop:"lowtemp"}},[o("el-input",{attrs:{type:"number"},model:{value:t.form.Info.THInfo.lowtemp,callback:function(e){t.$set(t.form.Info.THInfo,"lowtemp",e)},expression:"form.Info.THInfo.lowtemp"}})],1),o("br"),o("el-form-item",{attrs:{label:"常温：",prop:"normtemp"}},[o("el-input",{attrs:{type:"number"},model:{value:t.form.Info.THInfo.normtemp,callback:function(e){t.$set(t.form.Info.THInfo,"normtemp",e)},expression:"form.Info.THInfo.normtemp"}})],1),o("br"),o("el-form-item",{attrs:{label:"高温：",prop:"hightemp"}},[o("el-input",{attrs:{type:"number"},model:{value:t.form.Info.THInfo.hightemp,callback:function(e){t.$set(t.form.Info.THInfo,"hightemp",e)},expression:"form.Info.THInfo.hightemp"}})],1),o("br"),o("el-form-item",{attrs:{label:"持续时间(分钟)：",prop:"period"}},[o("el-input",{attrs:{type:"number"},model:{value:t.form.Info.THInfo.period,callback:function(e){t.$set(t.form.Info.THInfo,"period",e)},expression:"form.Info.THInfo.period"}})],1),o("br")],1)],1),o("el-col",{staticStyle:{"text-align":"center"},attrs:{span:24}},[o("el-button",{staticStyle:{"margin-top":"30px"},attrs:{size:"mini",type:"primary"},on:{click:function(e){return t.set("Cform")}}},[t._v("设置")]),o("el-button",{staticStyle:{"margin-top":"30px"},attrs:{size:"mini",type:"primary"},on:{click:t.stopProcess}},[t._v("停止")]),o("el-button",{attrs:{size:"mini",type:"primary"},on:{click:t.exportResult}},[t._v("下载")])],1)],1)],1),o("div",{staticClass:"red"},[o("h3",{staticClass:"equipmentTitle",staticStyle:{"line-height":"20px",position:"relative"}},[t._v("\n                                    历史信息\n                                    "),o("el-form",{staticStyle:{"text-align":"right",position:"absolute",right:"0",top:"0","margin-top":"10px"},attrs:{size:"mini"}},[o("el-button",{attrs:{size:"mini",type:"primary"},on:{click:t.query}},[t._v("查询")]),o("el-button",{attrs:{size:"mini",type:"primary"},on:{click:t.clearHistory}},[t._v("清空")]),o("el-button",{attrs:{size:"mini",type:"primary"},on:{click:t.stopProcess}},[t._v("停止")])],1)],1),o("el-table",{staticStyle:{width:"100%","margin-top":"30px"},attrs:{data:t.infos,border:""}},[o("el-table-column",{attrs:{fiexed:"left",align:"center",prop:"idx",label:"编号"},scopedSlots:t._u([{key:"default",fn:function(e){return[t._v(t._s(e.row.pk))]}}])}),o("el-table-column",{attrs:{align:"center",prop:"fsvip",label:"频谱仪IP"},scopedSlots:t._u([{key:"default",fn:function(e){return[t._v(t._s(e.row.fields.fsvip))]}}])}),o("el-table-column",{attrs:{align:"center",prop:"template_path",label:"测试模板路径"},scopedSlots:t._u([{key:"default",fn:function(e){return[t._v(t._s(e.row.fields.template_path))]}}])}),o("el-table-column",{attrs:{align:"center",prop:"ip",label:"设备IP"},scopedSlots:t._u([{key:"default",fn:function(e){return[t._v(t._s(e.row.fields.ip))]}}])}),o("el-table-column",{attrs:{align:"center",prop:"port",label:"串口端口号"},scopedSlots:t._u([{key:"default",fn:function(e){return[t._v(t._s(e.row.fields.port))]}}])}),o("el-table-column",{attrs:{align:"center",prop:"lowtemp",label:"低温温度"},scopedSlots:t._u([{key:"default",fn:function(e){return[t._v(t._s(e.row.fields.lowtemp))]}}])}),o("el-table-column",{attrs:{align:"center",prop:"normtemp",label:"常温温度"},scopedSlots:t._u([{key:"default",fn:function(e){return[t._v(t._s(e.row.fields.normtemp))]}}])}),o("el-table-column",{attrs:{align:"center",prop:"hightemp",label:"高温温度"},scopedSlots:t._u([{key:"default",fn:function(e){return[t._v(t._s(e.row.fields.hightemp))]}}])}),o("el-table-column",{attrs:{align:"center",prop:"period",label:"持续时间"},scopedSlots:t._u([{key:"default",fn:function(e){return[t._v(t._s(e.row.fields.period))]}}])}),o("el-table-column",{attrs:{fixed:"right",label:"操作"},scopedSlots:t._u([{key:"default",fn:function(e){return[o("el-button",{on:{click:function(o){return t.handleClick(e.row)}}},[t._v("设置")])]}}])})],1)],1)])]),o("div",{staticClass:"indexs",staticStyle:{"margin-top":"20px"}},[o("el-button-group",t._l(t.titleList,(function(e,n){return o("el-button",{style:e.style,attrs:{size:"mini",type:"primary",plain:""},on:{click:function(o){return t.titleClick(e,n)}}},[t._v(t._s(e.info))])})),1)],1)])])])],1)},r=[],i=(o("ac6a"),o("1bab")),l=o("9d5e"),s=o("8021"),a={name:"",components:{child:s["a"]},data:function(){return{filepath:"",logTitle:"t2kmachine",runningState:!1,n:0,finished:!0,currentScrollTop:0,preScrollTop:0,action:"/us-base/t2machine/",form:{Info:{fsvip:"",ip:"",THInfo:{port:"",lowtemp:"",normtemp:"",hightemp:"",period:""}}},infos:[],Rules:{fsvip:[{required:!0,message:"请输入频谱仪IP",trigger:"blur"}],ip:[{required:!0,message:"请输入板子IP",trigger:"blur"}]},formdata:"",fileContent:"",fileList:[],titleList:[{info:"基本信息",style:"background:#409EFF;color:#fff;border-color:#409EFF"},{info:"历史信息",style:""}]}},created:function(){},mounted:function(){this.query()},beforeDestroy:function(){this.$refs.mychild.closeWebSocket()},watch:{},methods:{stopProcess:function(){console.log("stopprocess"),this.$refs.mychild.closeWebSocket(),this.runningState=!1},scrollEvent:function(){if(this.finished){var t=this;this.finished=!1;var e=document.getElementsByClassName("red")[0].clientHeight;this.currentScrollTop=this.$refs.scrollDiv.scrollTop,this.preScrollTop<this.currentScrollTop?this.n++:this.preScrollTop>this.currentScrollTop&&this.n>=1&&this.n--,this.$refs.scrollDiv.scrollTop=e*this.n,this.titleList.forEach((function(t,e){t.style=""})),this.titleList[this.n].style="background:#409EFF;color:#fff;border-color:#409EFF",this.preScrollTop=this.$refs.scrollDiv.scrollTop,t.finished=!0}},titleClick:function(t,e){this.n=e;var o=this;this.finished=!1;var n=document.getElementsByClassName("red")[0].clientHeight;this.$refs.scrollDiv.scrollTop=n*this.n,this.titleList.forEach((function(t,e){t.style=""})),this.titleList[this.n].style="background:#409EFF;color:#fff;border-color:#409EFF",this.preScrollTop=this.$refs.scrollDiv.scrollTop,setTimeout((function(){o.finished=!0}),0)},query:function(){var t=this;Object(i["a"])({method:"post",url:"/t2kmachine/show_calib_history/"}).then((function(e){var o=e.data;0===o["error_num"]?(t.infos=o["params"],t.$message.success(o["msg"])):t.$message.error(o["msg"])}))},clearHistory:function(){var t=this;Object(i["a"])({method:"post",url:"/t2kmachine/clear_calib_history/"}).then((function(e){console.log(e);var o=e.data;0===o["error_num"]?(t.infos=[],t.$message.success(o["msg"])):t.$message.error(o["msg"])}))},handleClick:function(t){var e=this;if(this.runningState)this.$message.warning("正在运行中，请稍后");else{this.runningState=!0,this.$refs.mychild.openModal();var o={fsvip:t.fields.fsvip,template_path:t.fields.template_path,ip:t.fields.ip,port:t.fields.port,lowtemp:t.fields.lowtemp,normtemp:t.fields.normtemp,hightemp:t.fields.hightemp,period:t.fields.period};Object(i["a"])({method:"post",url:"/t2kmachine/set_calib_history/",data:o}).then((function(t){if(console.log(t),e.runningState=!1,200===t.status){var o=t.data,n=o.message;o.result?(e.filepath=o.filepath,e.$message.success(n)):e.$message.error(n)}}))}},handleChange:function(t,e){this.fileList=e.slice(-1)},fileUpload:function(t){this.fileContent=t.file},set:function(t){var e=this,o=this;this.$refs[t].validate((function(t){if(t){if(o.runningState)return void e.$message.warning("正在运行中，请稍后");e.runningState=!0,e.$refs.upload.submit(),e.$refs.mychild.openModal(),e.formdata=new FormData,e.formdata.append("file",e.fileContent),e.formdata.append("fsvip",o.form.Info.fsvip),e.formdata.append("ip",o.form.Info.ip),e.formdata.append("port",o.form.Info.THInfo.port),e.formdata.append("lowtemp",o.form.Info.THInfo.lowtemp),e.formdata.append("normtemp",o.form.Info.THInfo.normtemp),e.formdata.append("hightemp",o.form.Info.THInfo.hightemp),e.formdata.append("period",o.form.Info.THInfo.period),Object(i["a"])({method:"post",url:"/t2kmachine/calibrate_upload/",data:e.formdata}).then((function(t){if(console.log(t),e.runningState=!1,200===t.status){var o=t.data,n=o.message;o.result?(e.filepath=o.filepath,e.$message.success(n)):e.$message.error(n)}}))}}))},exportResult:function(){this.filepath?Object(i["a"])({method:"post",url:"/t2kmachine/export/",data:{filepath:this.filepath}}).then((function(t){var e=Object(l["b"])()+".zip";console.log(e),Object(l["a"])(t.data,e)})).catch((function(t){console.log(t)})):this.$message.error("没有结果可下载")},wdTableScrollEvent:function(t){return console.log(t),t.stopPropagation(),t.preventDefault(),!1}}},c=a,f=(o("c193"),o("40d5"),o("2877")),u=Object(f["a"])(c,n,r,!1,null,"db2ad162",null);e["default"]=u.exports},b0c5:function(t,e,o){"use strict";var n=o("520a");o("5ca1")({target:"RegExp",proto:!0,forced:n!==/./.exec},{exec:n})},c193:function(t,e,o){"use strict";var n=o("858e"),r=o.n(n);r.a},efff:function(t,e,o){"use strict";var n=o("0f4d"),r=o.n(n);r.a}}]);