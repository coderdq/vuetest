# coding:utf-8
'''
处理自动化测试
'''
import os
import datetime
from shutil import copyfile
import logging
import time
import modbus_tk
from celery.utils.log import get_task_logger
from asgiref.sync import async_to_sync
from ..common.fsv import FSVCtrl
from ..common.handle_board import BT2KHandler
from ..common.common_excel import BoardExcel
from commoninterface.master import THDevice


logger = get_task_logger('ghost')
band_dict = {'B41': ('0', '5'), 'E': ('0', '0'), 'F': ('0', '2'),
             'B1': ('1', '4'), 'B3': ('1', '3')}


class DOCalibrate(object):

    def __init__(self,chl_name,chl_layer):
        self.fsv = FSVCtrl()  # 频谱仪
        self.bd = None
        self.bdexl = BoardExcel()  # excel模板
        self.th_dev = None
        self.channel_name = chl_name
        self.channel_layer = chl_layer

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

    def init_all(self, fsvconf, bdconf, thconf):
        try:
            fsvip = fsvconf['IP']
            exlpath = fsvconf['DIR']
            self.bd = BT2KHandler(**bdconf)
            if thconf:
                self.th_dev = THDevice()  # 高低温箱初始化
            # for test
            self.fsv.init_inst(fsvip)
            # for test
            ret = self.bd.read_bb_sn()
            if ret is None:
                raise RuntimeError('no serial number')
            bbver, sn = ret
            # sn = '111'
            # bbver = '2222'
            excel_path = self.make_dirs(exlpath, sn, bbver)  # 复制excel模板
            logger.debug(excel_path)


            fsvoffset = self.read_offset(excel_path)
            self.fsv.set_offset(fsvoffset)  # 设置衰减值
            self.fsv.close_inst()

            params_lst = [excel_path, fsvip]
            self.gd_test(*params_lst, **thconf)
            self.rpt_message('测试完成OK')
        except Exception as e:
            logger.error('error.{}.'.format(e))
            self.rpt_message('error:{}.'.format(e))
            self.rpt_message('测试失败')
            return False
        else:
            return True,excel_path
        finally:
            self.bdexl.close_file()
            self.fsv.close_inst()

    def make_dirs(self, exlpath, sn, bbver):
        '''
        根据excel测试模板复制一份excel
        :param exlpath:
        :return:
        '''
        logger.debug(exlpath)
        try:
            today = datetime.date.today().strftime('%y-%m-%d')  # 返回字符串
            dirname = os.path.dirname(exlpath)
            new_path = os.path.join(dirname, today)
            if sn:
                new_path = os.path.join(new_path, sn)
            if not os.path.exists(new_path):
                os.makedirs(new_path)
            # newexl_name = str(sn) + '.xlsx'
            newexl_name = '1.xlsx'
            end_path = os.path.join(new_path, newexl_name)
            if os.path.exists(end_path):
                return end_path
            else:
                copyfile(exlpath, end_path)

            if self.bdexl.open_excel(end_path):
                # 写入bb ver,serialnumber
                self.bdexl.write_bbver_sn(bbver, sn)
            else:
                return None
            self.bdexl.close_file()
            return end_path
        except Exception as e:
            logger.error(e)
            self.rpt_message('ERROR:{}.'.format(e))
        finally:
            self.bdexl.close_file()

    def check_temp(self, target_temp):
        i = 0
        j = 0
        logger.debug('check temp {}'.format(target_temp))
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
                logger.info('i={},hit target {}'.format(i, target_temp))
                if i >= 3:
                    logger.info('高低温箱达到温度{}'.format(target_temp))
                    break
                i = i + 1
            else:
                i = 0
            time.sleep(30)

    def handle_test(self, target_temp, period):
        '''
        设置高低温温度
        :param target_temp:
        period:以分钟为单位，到达温度后的持续时间
        :return:
        '''
        self.check_temp(target_temp)
        logger.info('到达温度后开始等待{}分钟'.format(period))
        time.sleep(60 * int(period))
        # 使用矢网测试
        logger.info('start 基带板测试....')

    def gd_test(self, *args, **kwargs):
        try:
            excel_path, fsvip = args
            thconf = kwargs
            logger.debug('thdevice={}'.format(thconf))
            port = thconf.get('PORT', None)
            norm_temp = thconf.get('NORM_TEMP', None)
            low_temp = thconf.get('LOW_TEMP', None)
            high_temp = thconf.get('HIGH_TEMP', None)
            period = thconf.get('PERIOD', 20)  # 平衡持续时间,以分钟为单位
            if self.th_dev is None or not port:
                # 只进行常温测试
                logger.info('只进行常温测试')
                self.rpt_message('INFO:只进行常温测试.')
                self.do_test(excel_path, fsvip, 1)
                return
            if self.th_dev.connect_th(PORT='COM{}'.format(port)):
                logger.info('高低温箱connected**')
                self.th_dev.set_fixed_mode()

                if norm_temp is not None:
                    logger.info('start 常温测试')
                    self.th_dev.set_temp_sv(int(norm_temp) * 10)
                self.th_dev.start_dev()  # 开始运行
                if norm_temp is not None:
                    self.handle_test(int(norm_temp) * 10, period)
                    self.do_test(excel_path, fsvip, 1)
                    logger.debug('******常温测试  finished****')
                if low_temp is not None:
                    logger.info('start 低温测试')
                    self.th_dev.set_temp_sv(int(low_temp) * 10)
                    self.handle_test(int(low_temp) * 10, period)
                    self.do_test(excel_path, fsvip, 0)

                    logger.debug('******低温测试  finished****')

                if high_temp is not None:
                    logger.info('start 高温测试')
                    self.th_dev.set_temp_sv(int(high_temp) * 10)
                    self.handle_test(int(high_temp) * 10, period)
                    self.do_test(excel_path, fsvip, 2)
                    logger.debug('******高温测试  finished****')

                logger.debug('高低温箱停止运行')
                self.th_dev.stop_dev()  # 停止运行
        except modbus_tk.modbus.ModbusError as e:
            logger.exception('{}'.format(e))
            raise StopIteration('th_dev')

    def do_test(self, excel_path, fsvip, temp=1):
        if excel_path is None:
            raise RuntimeError('excel does not exist!')
        # 设置gps mode
        if not self.bd.do_set_bd():
            raise RuntimeError('set_gps_mode failed')
        # 测试sniffer
        # if not self.sniffer_test_on_board('0', temp, excel_path):
        #     raise RuntimeError('test_sniffer failed')

        # cellid 0,1用合路器切换
        for cellid in ['0', '1']:
        #for test
        # for cellid in ['0']:
            # for test
            logger.debug('开始测试cell{}'.format(cellid))
            self.rpt_message('INFO:开始测试cell{}'.format(cellid))
            self.do_test_on_cellid(cellid, excel_path, fsvip, temp)
        # 启动ARM进程
        # self.bd.start_arm_process()

    def do_test_on_cellid(self, cellid, excel_path, fsvip, temp=1):
        freqpoint_dict, freq_dict = self.read_boardtype(excel_path, cellid)
        logger.debug(freqpoint_dict)
        key_bands = freqpoint_dict.keys()
        power_txatt_dict = dict()  # {'B41':[(高txatt,高power),(中),(低)],'E':[(),(),()]}
        cali_dict = dict()
        for band in key_bands:
            try:
                self.conf_device(fsvip)
                logger.info('开始测试band={}'.format(band))
                self.rpt_message('INFO:开始测试band={}'.format(band))
                cell_band = 'cell{}_{}'.format(cellid, band)
                power_range = self.read_excel_txatt_norm(excel_path, cell_band)  # 功率的指标[下限，标准值，上限]
                each_band_power_txatt = []
                freq_points = freqpoint_dict[band]
                freqs = freq_dict[band]

                if self.bd.do_compensation(cellid):
                    calilist = self.get_and_send_powercali(cellid, fsvip, band, freq_points, freqs,
                                                           power_range[1])
                    cell_band = 'cell{}_{}'.format(cellid, band)
                    cali_dict.setdefault(cell_band, calilist)
                else:
                    logger.error('band{}频补准备工作失败'.format(band))
                    self.rpt_message('ERROR:band{}频补准备工作失败'.format(band))
                    continue
                for idx, freq_point in enumerate(freq_points):
                    if not freq_point:
                        continue
                    if not self.conf_board_on_some_freq(cellid, freq_point):  # 设置基带板一类参数，并返回PCI
                        logger.error('设置一类参数异常')
                        self.rpt_message('ERROR:设置一类参数异常')
                        continue

                    freq = freqs[idx]
                    result = self.power_test_on_some_freq(cellid, fsvip, freq, power_range)
                    if result is None:
                        break
                    each_band_power_txatt.append(result[1:])
                    if not result[0]:  # 有异常也不退出
                        time.sleep(3)
                        continue
                power_txatt_dict.setdefault(cell_band, each_band_power_txatt)
            except Exception as e:
                logger.error(e)
                self.rpt_message('ERROR:{}.'.format(e))
            finally:
                self.fsv.close_inst()
        try:
            if self.bdexl.open_excel(excel_path):
                self.bdexl.write_cali(temp, **cali_dict)
                self.bdexl.write_max_txatt(temp, **power_txatt_dict)
        except Exception as e:
            logger.error(e)
            self.rpt_message('ERROR:{}.'.format(e))
        finally:
            self.bdexl.close_file()

    def power_test_on_some_freq(self, cellid, fsvip, freq, power_range):
        '''
        freq:频率
        power_range:功率标准[下限，理想值,上限，]
        :return:
        '''
        # self.fsv.set_for_txatt(freq)
        # plst=self.fsv.get_power(freq)
        lower = float(power_range[0])  # 下限
        upper = float(power_range[2])  # 上限
        plst = self.get_fsv_power(fsvip, float(power_range[1]), freq)
        if plst is None:
            return None
        power = float(plst)  # 读取频谱仪功率
        txatt = self.bd.read_txatt(cellid)
        if power >= lower and power <= upper:
            # 读取txatt
            return True, power, txatt
        elif power > upper:
            self.bd.set_rf(cellid, 0)  # 关闭射频
            logger.error('功率{}超限'.format(power))
            self.rpt_message('ERROR:功率{}超限.'.format(power))
        else:
            self.bd.set_rf(cellid, 0)  # 关闭射频
            logger.error('功率{}不达标'.format(power))
            self.rpt_message('ERROR:功率{}不达标'.format(power))
        return False, power, txatt
        # return None
        # # 读取txatt
        # txatt = self.bd.read_txatt(cellid)
        # return power, txatt, plst[1], plst[2]

    def conf_board_on_some_freq(self, cellid, freq):
        '''
        基于某频点
        freq:频点
        :return:
        '''
        logger.debug('conf_board_on_some_freq')
        try:
            flag = self.bd.conf_para(cellid, freq)  # 设置频点并打开功放
            return flag
        except Exception as e:
            logger.error(e)
            return False

    def get_and_send_powercali(self, cellid, fsvip, band, freq_points, freqs, target):
        '''
        遍历band的三个频点，得到功率补偿，发送给BB
        band:
        freq_points:频点，用于发给基带板
        freqs:频率,用于设置频谱仪
        target:功率理想值dBm

        return 功率补偿值列表
        '''
        str_2_int = {'E': 40, 'F': 39, 'B1': 1, 'B3': 3, 'B41': 41}
        bandint = str_2_int[band]
        temp = self.bd.repeat_get_temp()  # 获取基带板温度
        if temp is None:
            raise IOError('get temp failed')
        logger.debug('current temp={}'.format(temp))
        # self.conf_device(fsvip)
        cali_list = []
        calis = []
        for idx, point in enumerate(freq_points):
            freq = freqs[idx]
            self.conf_board_on_some_freq(cellid, point)  # 设置基带板频点
            plst = self.get_fsv_power(fsvip, target, freq)
            if plst is None:
                raise IOError('read fsv power failed')
            power = plst
            logger.debug('fsv read power={}'.format(power))
            self.rpt_message('INFO:fsv read power={}'.format(power))
            value = 21 + float(power) - float(target)
            calis.append('%4.2f' % value)
            cali = int(value * 100)
            cali_list.append([bandint, int(point), cali, temp])
        self.bd.send_powercali(cali_list)
        return calis

    def get_fsv_power(self, fsvip, upper, freq):
        '''
        读取频谱仪功率
        upper:输出功率上限，用来设置ref level,ref level=upper+3
        :return:
        '''
        i = 0
        ref_level = float(upper) + 7
        while 1:
            try:
                if i >= 3:
                    return None
                i = i + 1
                self.fsv.set_for_txatt(ref_level, freq)
                time.sleep(1)
                plst = []
                j = 0
                # sweep time 2s,读5次取平均值
                while j < 5:
                    power = self.fsv.get_power(ref_level, freq)  # 读取频谱仪功率,返回列表
                    if power is not None:
                        plst.append(power)
                    else:
                        break
                    j = j + 1
                if plst:
                    plst = [float(item[0]) for item in plst]
                    logger.debug('power list={}'.format(plst))
                    return sum(plst) / len(plst)
                time.sleep(3)
            except Exception as e:
                logger.error(e)
                time.sleep(3)
                self.conf_device(fsvip)
                time.sleep(3)
                continue

    def get_ul_center(self, ul_list):
        '''
        获取上行频率的中心频率
        ul_list:[]
        :return:
        '''
        start = ul_list[2] - 2.5
        stop = ul_list[0] + 2.5
        logger.debug('ul={},{}'.format(start, stop))
        return start, stop

    def read_excel_txatt_norm(self, excel_path, cell_band):
        '''
        读取excel的上下行功率，频点等参数
        :param excel_path:
        :return:
        '''
        try:
            if self.bdexl.open_excel(excel_path):
                normlist = self.bdexl.get_txatt_norm(cell_band)
                # lower = norm['下限']  # 获取txatt指标
                # upper=norm['上限']
                # target=norm['标准值']
                logger.debug('normlist={}'.format(normlist))
                return normlist
        except Exception as e:
            raise RuntimeError(e)
        finally:
            self.bdexl.close_file()

    def read_boardtype(self, excel_path, cellid):
        '''
        从excel中读取board类型及主从片频点，频率
        :param excel_path:
        cellid :0/1
        :return:
        '''
        try:
            if self.bdexl.open_excel(excel_path):
                freqpoint_dict, freq_dict = self.bdexl.get_set_condition(cellid)
                return freqpoint_dict, freq_dict
        except Exception as e:
            raise RuntimeError('read_boardtype ERROR:{}'.format(e))
        finally:
            self.bdexl.close_file()

    def read_offset(self, excel_path):
        try:
            if self.bdexl.open_excel(excel_path):
                self.bdexl.get_dl_rows()
                offset = self.bdexl.get_offset()
                return offset
        except Exception as e:
            raise RuntimeError('read_offset ERROR:{}'.format(e))
        finally:
            self.bdexl.close_file()

    def conf_powersupply(self, port):
        '''
        设置电源的电压为12V，电流最大，给基带板供电
        :return:
        '''
        pass
        # self.powsup.init_ps(port)
        # time.sleep(1)
        # self.powsup.reset_ps()
        # time.sleep(3)
        # self.powsup.set_voltage(12)
        # maxcur = self.powsup.read_maxcurrent()
        # if maxcur is None:
        #     maxcur = 20
        # self.powsup.set_current(maxcur)
        # self.powsup.set_output(1)  # 打开输出开关

    def conf_device(self, fsvip):
        '''
        仪器初始化
        :return:
        '''
        i = 0
        while 1:
            i = i + 1
            if i >= 3:
                raise RuntimeError('fsv error')
            try:
                self.fsv.init_inst(fsvip)
                time.sleep(1)
                self.fsv.reset_fsv()
                time.sleep(1)
            except Exception as e:
                logger.error(e)
                time.sleep(5)
                self.fsv.close_inst()
            else:
                break
