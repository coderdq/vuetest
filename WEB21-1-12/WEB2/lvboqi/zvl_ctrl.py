# coding:utf-8
import os

import copy
import time
import modbus_tk
from shutil import copyfile
from asgiref.sync import async_to_sync
from .api.comm_excel import ZVLExcel
from .api.zvl import ZVLCtrl
from commoninterface.master import THDevice

'''
    读取测试项，得到测试结果后写入excel
'''


# logger = logging.getLogger('ghost')


# END_EDGE=3000 #矢网分析的最大freq 3GHz=3000MHz

class LVBOQITest(object):
    def __init__(self, chl_name, chl_layer, log):

        self.zvlexl = ZVLExcel()
        self.th_dev = THDevice()
        self.zvl = ZVLCtrl()
        self.channel_name = chl_name
        self.channel_layer = chl_layer
        self.logger = log

    def rpt_message(self, msg):
        try:
            if self.channel_layer and self.channel_name:
                print('rpt_msg')
                async_to_sync(self.channel_layer.send)(
                    self.channel_name,
                    {
                        "type": "send.message",
                        "message": msg
                    }
                )
        except Exception as e:
            print('rpt_msg error:{}'.format(e))

    def init_zvl(self, cfg):
        try:
            config = copy.deepcopy(cfg)
            if config:
                if 'ZVL' not in config.keys():
                    self.logger.debug('no ZVL in config')
                    return False
                zvlcfg = config['ZVL']
                if 'IP' not in zvlcfg.keys() or 'DIR' not in zvlcfg.keys() or 'BAND' not in zvlcfg.keys():
                    self.logger.error('no IP/DIR/BAND in zvl config')
                    return False
                ip = zvlcfg['IP']
                dir = zvlcfg['DIR']
                band = zvlcfg['BAND']
                maxfreq = float(zvlcfg['MAX'])
                self.logger.debug('load config={}'.format(config))
                self.rpt_message('load config={}'.format(config))
                if not ip:
                    self.logger.debug('ip is empty in zvl config')
                    return False
                # for test
                self.zvl.init_inst(ip)
                self.zvl.reset_zvl()  # 初始化zvl

                th_flag = False
                # 高低温配置
                thconf = config.get('THDEV', {})
                port = thconf.get('PORT', '')

                if not port:
                    th_flag = False
                else:
                    th_flag = True
                end_path = self.handle_path(dir, band)
                if not end_path:
                    self.logger.error('no excel path')
                    self.rpt_message('ERROR:no excel path')
                    return False

                # 初始化连接zvl
                if not th_flag:
                    self.logger.debug('常温测试')

                    # 读取excel配置文件
                    ret = self.handle_content(end_path, band, maxfreq)
                    self.logger.debug('******test  finished****')
                    self.rpt_message('INFO:******test  finished****')
                    return ret, end_path
                else:
                    self.logger.debug('高低温测试')

                    params = [end_path, band, maxfreq]
                    ret = self.gd_test(*params, **thconf)
                    return ret, end_path
                    # loop = asyncio.get_event_loop()
                    # params=[instr, end_path, band,maxfreq]
                    # loop.run_until_complete(gd_test(*params,**thconf))
                    # loop.close()

        except Exception as e:
            self.logger.error('init_zvl error:{}'.format(e))
            self.rpt_message('ERROR:init_zvl error:{}'.format(e))
            return False

    def check_temp(self, target_temp):
        i = 0
        j = 0
        self.logger.debug('check temp {}'.format(target_temp))
        while True:
            pv = self.th_dev.get_temp_pv()
            if not pv:
                time.sleep(60)
                j = j + 1
                if j >= 3:
                    raise StopIteration('dev not online**')
                continue
            if pv >= target_temp - 10 and pv <= target_temp + 10:
                # 上下1度
                self.logger.info('i={},hit target {}'.format(i, target_temp))
                if i >= 3:
                    break
                i = i + 1
            else:
                i = 0
            time.sleep(30)

    def handle_test(self, target_temp, period):
        '''

        :param target_temp:
        :param period: 以分钟为单位
        :return:
        '''
        self.check_temp(target_temp)
        self.logger.info('到达温度后开始等待{}分钟'.format(period))
        time.sleep(60 * float(period))
        # 使用矢网测试
        self.logger.info('start zvl test....')

    def gd_test(self, *args, **kwargs):
        '''
        高低温测试
        :return:
        '''
        try:
            # th_dev = THDevice()
            ret = False
            end_path, band, maxfreq = args
            thconf = kwargs
            port = thconf.get('PORT')
            low_temp = thconf.get('LOW_TEMP', None)  # 高低温箱的低温
            high_temp = thconf.get('HIGH_TEMP', None)  # 高低温箱的高温
            norm_temp = thconf.get('NORM_TEMP', None)
            period = thconf.get('PERIOD', 20)

            if self.th_dev.connect_th(PORT='COM{}'.format(port)):
                self.logger.info('th connected**')
                self.th_dev.set_fixed_mode()
                if norm_temp is not None:
                    self.logger.info('start 常温测试')
                    self.th_dev.set_temp_sv(int(norm_temp) * 10)
                self.th_dev.start_dev()
                if norm_temp is not None:
                    self.handle_test(int(norm_temp) * 10, period)
                    ret = self.handle_content(end_path, band, maxfreq, 0)
                    self.logger.debug('******常温测试  finished****')
                if low_temp is not None:
                    self.logger.info('start 低温测试')
                    self.th_dev.set_temp_sv(int(low_temp) * 10)
                    self.handle_test(int(low_temp) * 10, period)
                    ret = self.handle_content(end_path, band, maxfreq, 1)
                    self.logger.debug('******低温测试  finished****')
                if high_temp is not None:
                    self.logger.info('start 高温测试')
                    self.th_dev.set_temp_sv(int(high_temp) * 10)
                    self.handle_test(int(high_temp) * 10, period)
                    ret = self.handle_content(end_path, band, maxfreq, 2)
                    self.logger.debug('******高温测试  finished****')
                self.logger.debug('高低温箱停止运行')
                self.th_dev.stop_dev()
                return ret
        except modbus_tk.modbus.ModbusError as e:
            self.logger.exception('{}'.format(e))
            raise StopIteration('th_dev')

    def handle_path(self, path, band):
        '''
        根据config目录下的test_conf.json文件中测试模板的路径path，生成对应器件id和序列号的文件夹及文件
        :param path:
        :return:新生成的测试模板路径
        '''
        try:
            end_path = ''
            device_id_path = ''
            if self.zvlexl.open_excel(path):
                device_type, device_id = self.zvlexl.get_id(band)  # 获取模板中待测试器件的类型及序列号
                dirname = os.path.dirname(path)
                if device_type is not None:
                    device_type_path = os.path.join(dirname, str(device_type))
                    if device_id is not None:
                        device_id_path = os.path.join(device_type_path, str(device_id))
                    else:
                        device_id_path = device_type_path
                else:
                    device_type_path = dirname
                    device_id_path = dirname
                if not os.path.exists(device_type_path):
                    os.makedirs(device_type_path)
                if not os.path.exists(device_id_path):
                    os.makedirs(device_id_path)
                excelname = os.path.basename(path)  # 获取excel文件名
                newexcelname = str(device_type) + '_' + str(device_id) + '.xlsx'  # 新的excel表名
                end_path = os.path.join(device_id_path, newexcelname)
                if os.path.exists(end_path):
                    pass
                else:
                    copyfile(path, end_path)
            else:
                return None
            self.logger.debug('end_path={}'.format(end_path))
        except Exception as e:
            self.logger.error('{}'.format(e))
            return None
        return end_path

    def handle_content(self, end_path, band, END_EDGE, temp=0):
        '''
        将图片保存到器件类型文件夹下序列号所在文件夹，根据器件类型创建文件夹，再创建序列号子文件夹

        :param path:
        :param band:
        :param END_EDGE:
        :return:
        '''
        try:
            temp_dict = {0: '常温', 1: '低温', 2: '高温'}

            if end_path:
                device_id_path = os.path.dirname(end_path)
                if self.zvlexl.open_excel(end_path):
                    self.zvl.remove_allmarker(1)
                    dfcontent = self.zvlexl.read_testitems(band)  # 读取到Band区域所有行列的内容
                    if dfcontent is None:
                        self.logger.error('zvl excel is empty')
                        self.rpt_message('ERROR:zvl excel is empty')
                        return False
                    results = []  # 实测值及测试结果

                    # 先设置带内freq span
                    low_edge, up_edge, leftlow_edge, rightup_edge = self.zvlexl.get_bandx_edge(band)
                    self.logger.debug(
                        'low/up_edge,left/right={},{},{},{}'.format(low_edge, up_edge, leftlow_edge, rightup_edge))
                    self.set_edge(low_edge, up_edge)
                    indicators = self.zvlexl.get_inband_indicator(dfcontent)
                    self.logger.debug('indicators={}'.format(indicators))
                    tracen = 1
                    markern = 1

                    # 最大平均损耗S21
                    if self.set_trace(tracen, 'MLOG', 'S21'):
                        results.append(self.get_max_avg_s21(tracen, markern, low_edge, up_edge, indicators[1]))
                    else:
                        results.append(None)
                    # 最大插入损耗S21
                    results.insert(0, self.get_min_loss(tracen, markern, indicators[0]))
                    self.logger.debug('results={}'.format(results))
                    # S11
                    tracen += 1
                    if self.add_new_trace(tracen, 'MLOG', 'S11'):
                        results.append(self.get_max_loss(tracen, 1, indicators[2]))
                    else:
                        results.append(None)
                    self.logger.debug('results={}'.format(results))
                    # S22
                    tracen += 1
                    if self.add_new_trace(tracen, 'MLOG', 'S22'):
                        results.append(self.get_max_loss(tracen, 1, indicators[3]))
                    else:
                        results.append(None)
                    # 带内波动
                    results.append(self.get_ripple_in_bw(1, 1, indicators[4]))
                    self.logger.debug('device_id_path={}'.format(device_id_path))
                    # auto scale
                    # zvl.auto_scale(instr.zvlHandle,tracen)
                    # 保存带内测试图片
                    inbandpngpath = os.path.join(device_id_path, '{}zvl_inband{}.PNG'.format(temp_dict[temp], band))
                    self.zvl.save_screenshot(r'c:\\Temp\\1.PNG', r'{}'.format(inbandpngpath))
                    # 删除trace s11,s22
                    self.zvl.delete_trace(2)
                    self.zvl.delete_trace(3)
                    self.zvl.remove_allmarker(1)
                    time.sleep(1)
                    # 带外抑制
                    outbanddf = self.zvlexl.get_outband_items(dfcontent)  # dataframe
                    markerxlist = []  # 带外的marker x,float，单位MHz

                    for _, rows in outbanddf.iterrows():
                        # low_edge,up_edge,indicator_operator,indicator
                        up_edge = rows[1]
                        if rows[0] >= END_EDGE:
                            break
                        if rows[1] > END_EDGE:
                            up_edge = END_EDGE

                        markerxlist.extend([rows[0], up_edge])
                        self.set_edge(rows[0], up_edge)
                        minabsy, minx = self.set_fixed_marker(rows[0], up_edge)
                        self.logger.debug('absys={}'.format(minabsy))
                        results.append(self.get_outband_rejection(minabsy, minx, rows[2], rows[3]))
                    filtered_markerxlist = []  # 去重后的markerx列表
                    for item in markerxlist:
                        if item not in filtered_markerxlist:
                            filtered_markerxlist.append(item)

                    #     self.set_edge(rows[0], up_edge)
                    #     time.sleep(0.3)
                    #     markerxy = self.get_min_rejection_marker(1, 1)
                    #     # zvl.auto_scale(instr.zvlHandle,1)
                    #     if markerxy:
                    #         # 保存图片
                    #         outpngpath = os.path.join(device_id_path,
                    #                                   '{}band{}_out_{}.PNG'.format(temp_dict[temp], band, rows[0]))
                    #         outpngs.append(outpngpath)
                    #         zvl.save_screenshot(self.instr.zvlHandle, r'c:\\Temp\\1.PNG', r'{}'.format(outpngpath))
                    #
                    #         markerx, absy = markerxy
                    #         markerxlist.append(markerx)  # 换算成MHz单位
                    #         results.append(self.get_min_rejection(absy, rows[2], rows[3]))  # 's21'
                    #     else:
                    #         results.append(None)
                    # self.logger.debug('results={}'.format(results))

                    # 生成带外测试图
                    # outband_lowedge = outbanddf.iloc[0, 0]  # 第一个带外点
                    # outband_upedge=outbanddf.iloc[-1,1]  #最后一个带外点
                    # 截图
                    outband_lowedge = filtered_markerxlist[0]
                    outband_upedge = filtered_markerxlist[-1]
                    self.set_edge(outband_lowedge, outband_upedge)
                    self.logger.debug('markerxlist={}'.format(filtered_markerxlist))
                    length = len(filtered_markerxlist)
                    divided_marker = [filtered_markerxlist[i:i + 10] for i in
                                      range(0, length, 10)]  # 10个marker为一组，分成多个子列表
                    idx = 0
                    outbandpngpaths = []
                    for part in divided_marker:
                        self.logger.debug('part={}'.format(part))
                        self.set_outband_trace_marker(1, 1, part)
                        outbandpngpath = os.path.join(device_id_path,
                                                      '{}zvl_outband{}_{}.PNG'.format(temp_dict[temp], band, idx))
                        self.zvl.save_screenshot(r'c:\\Temp\\2.PNG', r'{}'.format(outbandpngpath))
                        time.sleep(.3)
                        self.zvl.remove_allmarker(1)
                        outbandpngpaths.append(outbandpngpath)
                        idx += 1
                    self.set_edge(leftlow_edge, rightup_edge)
                    filteredmarkerlist = [item for item in filtered_markerxlist if leftlow_edge <= item <= rightup_edge]
                    self.logger.debug('filtered markerxlist={}'.format(filteredmarkerlist))
                    length = len(filteredmarkerlist)
                    divided_marker = [filteredmarkerlist[i:i + 10] for i in
                                      range(0, length, 10)]  # 10个marker为一组，分成多个子列表

                    for part in divided_marker:
                        self.logger.debug('part={}'.format(part))
                        self.set_outband_trace_marker(1, 1, part)
                        outbandpngpath = os.path.join(device_id_path,
                                                      '{}zvl_outband{}_{}.PNG'.format(temp_dict[temp], band, idx))
                        self.zvl.save_screenshot(r'c:\\Temp\\2.PNG', r'{}'.format(outbandpngpath))
                        time.sleep(.3)
                        self.zvl.remove_allmarker(1)
                        outbandpngpaths.append(outbandpngpath)
                        idx += 1

                    self.zvlexl.save_band_png(band, inbandpngpath, outbandpngpaths)
                    # 结果写入excel
                    self.zvlexl.write_results(band, results, temp)
                    return True
        except Exception as e:
            raise RuntimeError('ERROR:{}'.format(e))
            return False
        finally:
            self.zvlexl.close_file()
            self.zvl.close_inst()

    def set_edge(self, low_edge, up_edge):
        '''

        :param low_edge: float单位MHz
        :param up_edge: float单位MHz
        :return:
        '''
        try:

            low = '{}MHz'.format(low_edge)
            up = '{}MHz'.format(up_edge)
            self.zvl.set_freq(low, up)
            return True
        except Exception as e:
            self.logger.error('set_edge error {}'.format(e))
            return False

    def set_trace(self, tracen, form, means):
        '''

        :param tracen: int
        form:str,
        means:str,'S11','S12','S21','S22'
        :return:
        '''
        try:

            self.zvl.set_trace_form(tracen, form)
            self.zvl.change_trace_meas(tracen, means)
            if form == 'MLOG':
                self.zvl.set_div_value(tracen, 10)
                # zvl.set_ref_value(zvlhandler, tracen, -40)
            return True
        except Exception as e:
            self.logger.error('set_trace error {}'.format(e))
            return False

    def add_new_trace(self, tracen, form, means):
        try:

            self.zvl.add_trace(tracen, means, form)
            if form == 'MLOG':
                self.zvl.set_div_value(tracen, 10)
                # zvl.set_ref_value(zvlhandler, tracen, -40)
            return True
        except Exception as e:
            self.logger.error('add_new_trace error {}'.format(e))
            return False

    def get_max_loss(self, tracen, markern, indicator):
        '''
        带内最大回波损耗S21/S11/S22,max marker 绝对值
        :param tracen:int
        :param markern:int
        :param indicator:float
        :return:
        '''
        try:

            self.zvl.create_max_marker(tracen, markern)  # max marker
            # create_max_marker(zvlhandler, tracen, markern + 1)  # max marker
            _, marker1y = self.zvl.query_marker(tracen, markern)
            absy = abs(marker1y)
            opstr = str(absy) + indicator[0] + str(indicator[1])
            if eval(opstr):  # 满足指标
                return (absy, True)
            else:
                return (absy, False)  # 不满足指标
        except Exception as e:
            self.logger.error('get_max_loss error {}'.format(e))
            return None

    def get_min_loss(self, tracen, markern, indicator):
        '''
        带内最大插入损耗S21/S11/S22,min marker 绝对值
        :param tracen:int
        :param markern:int
        :param indicator:float
        :return:
        '''
        try:

            self.zvl.create_min_marker(tracen, markern)  # max marker
            # create_max_marker(zvlhandler, tracen, markern + 1)  # max marker
            _, marker1y = self.zvl.query_marker(tracen, markern)
            absy = abs(marker1y)
            opstr = str(absy) + indicator[0] + str(indicator[1])
            if eval(opstr):  # 满足指标
                return (absy, True)
            else:
                return (absy, False)  # 不满足指标
        except Exception as e:
            self.logger.error('get_min_loss error {}'.format(e))
            return None

    def get_max_avg_s21(self, tracen, markern, low_edge, up_edge, indicator):
        '''
        1个曲线最多建10个marker
        带内最大平均损耗S21
        :param tracen:int
        :param markern:int
        :param low_edge:float,单位MHz
        :param up_edge:float,单位MHz
        :param indicator:('<=',float)
        :return:
        '''
        try:
            interval = 5  # MHz
            startpoint = low_edge
            n = markern

            avglist = []
            pointlist = []
            endpoint = startpoint
            while endpoint <= up_edge:
                startpoint = endpoint
                endpoint = endpoint + interval
                if endpoint >= up_edge:
                    endpoint = up_edge
                    break
                midpoint = (startpoint + endpoint) / 2.0
                pointlist.append(midpoint)

            midpoint = (startpoint + endpoint) / 2.0
            pointlist.append(midpoint)
            self.logger.debug('midpoints={}'.format(pointlist))
            for point in pointlist:
                self.zvl.set_trace_marker(tracen, n, '{}MHz'.format(point))
                _, markery = self.zvl.query_marker(tracen, n)
                avglist.append(abs(markery))
                # n = n + 1
            avg = sum(avglist) / len(avglist)
            opstr = str(avg) + indicator[0] + str(indicator[1])
            self.logger.debug('opstr={}'.format(opstr))
            if eval(opstr):
                return (avg, True)
            else:
                return (avg, False)
        except Exception as e:
            self.logger.error('get_max_avg_s21 error {}'.format(e))
            return None

    def get_ripple_in_bw(self, tracen, markern, indicator):
        '''
        带内波动
        indicator:float
        :return:
        '''
        try:

            self.zvl.create_min_marker(tracen, markern)  # min marker
            self.zvl.create_max_marker(tracen, markern + 1)  # max marker
            _, marker1y = self.zvl.query_marker(tracen, markern)
            _, marker2y = self.zvl.query_marker(tracen, markern + 1)
            absy = abs(marker1y - marker2y)
            opstr = str(absy) + indicator[0] + str(indicator[1])
            if eval(opstr):  # 满足指标
                return (absy, True)
            else:
                return (absy, False)  # 不满足指标
        except Exception as e:
            self.logger.error('get_ripple_in_bw error{}'.format(e))
            return None

    def get_min_rejection_marker(self, tracen, markern):
        '''
        带外抑制 max marker 的x,y绝对值
        :param tracen:
        :param markern:
        :param indicator:
        :return:x,y,x的单位是Hz
        '''
        try:

            self.zvl.create_max_marker(tracen, markern)  # max marker
            marker1x, marker1y = self.zvl.query_marker(tracen, markern)
            absy = abs(marker1y)
            return marker1x / 1000000.0, absy
        except Exception as e:
            self.logger.error('get_min_rejection_marker error {}'.format(e))
            return None

    def get_min_rejection(self, absy, *indicator):
        try:
            opstr = str(absy) + indicator[0] + str(indicator[1])
            if eval(opstr):  # 满足指标
                return absy, True
            else:
                return absy, False  # 不满足指标
        except Exception as e:
            self.logger.error('get_min_rejection error {}'.format(e))
            return None

    def set_outband_trace_marker(self, tracen, markern, markerlist):
        try:

            for x in markerlist:
                markerx = '{}MHz'.format(x)
                self.zvl.set_trace_marker(tracen, markern, markerx)
                markern = markern + 1
        except Exception as e:
            self.logger.error('set_outband_trace_marker error {}'.format(e))

    def set_fixed_marker(self, *markerxs):
        '''
        获取对应markerx1和2的y1,y2值，并获取y1,y2绝对值中的最小值
        :param markerx1:
        :param markerx2:
        :return:[]
        '''
        try:

            markern = 1
            minabsy = None
            mini = 0
            for i in range(len(markerxs)):
                x = '{}MHz'.format(markerxs[i])
                self.logger.debug('markerx={}'.format(x))
                self.zvl.set_trace_marker(1, markern, x)
                time.sleep(.5)
                _, markery = self.zvl.query_marker(1, markern)
                self.logger.debug('markery={}'.format(markery))
                time.sleep(.5)

                if minabsy is not None:
                    if abs(markery) < minabsy:
                        minabsy = abs(markery)
                        mini = i
                else:
                    minabsy = abs(markery)
                    mini = i
                markern = markern + 1
            return minabsy, markerxs[mini]
        except Exception as e:
            self.logger.error('set_two_fixed_marker error {}'.format(e))
            return []

    def get_outband_rejection(self, minabsy, minx, *indicator):
        '''
        获取带外抑制
        :param minabsy:
                minx:
        :param indicator:
        :return:absys中的最小值，是否通过
        '''
        try:
            if minabsy is None:
                return None
            ret = False

            opstr = str(minabsy) + indicator[0] + str(indicator[1])
            if eval(opstr):  # 满足指标
                ret = True
            else:
                ret = False  # 不满足指标
            return ','.join([str(minx), str(minabsy)]), ret
        except Exception as e:
            self.logger.error('get_outband_rejection error {}'.format(e))
            return None
