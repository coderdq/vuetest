# coding:utf-8
'''
处理自动化测试
'''
import os
from shutil import copyfile
import logging
import time
import modbus_tk
from asgiref.sync import async_to_sync
from celery.utils.log import get_task_logger
from .fsv import FSVCtrl

from .handle_board import B8125Handler, BT2KHandler
from .common_excel import BoardExcel
from commoninterface.master import THDevice


logger = get_task_logger('ghost')
band_dict = {'B41': ('0', '5'), 'E': ('0', '0'), 'F': ('0', '2'),
             'B1': ('1', '4'), 'B3': ('1', '3')}


class DoDlTest(object):

    def __init__(self,chl_name,chl_layer):
        self.fsv = FSVCtrl()  # 频谱仪
        # self.powsup = PowerSupply_SCPI()  # 电源
        self.bd = None
        self.bdexl = BoardExcel()  # excel模板
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
            fsvoffset = float(fsvconf.get('OFFSET', 41))
            self.fsv.set_offset(fsvoffset)  # 设置衰减值
            # for test
            self.fsv.init_fsv(fsvip)
            excel_path = self.make_dirs(exlpath)  # 复制excel模板
            cellid = str(bdconf.get('CELL', '0'))
            type, freqpoint_dict, freq_dict, ul_freq_dict = self.read_boardtype(excel_path, cellid)
            if type == '8125':
                self.bd = B8125Handler(**bdconf)
            elif type == 'T2K':
                self.bd = BT2KHandler(**bdconf)
            self.th_dev = None
            if thconf:
                self.th_dev = THDevice()  # 高低温箱初始化
            params_lst = [excel_path, fsvip, cellid, type, freqpoint_dict, freq_dict, ul_freq_dict]
            self.gd_test(*params_lst, **thconf)
            self.rpt_message('测试完成ok')
            # self.do_test(*params_lst,**temp_dict)
        except Exception as e:
            logger.error('error.{}.'.format(e))
            self.rpt_message('ERROR:{}'.format(e))
            self.rpt_message('测试失败')
            return False
        else:
            return True
        finally:
            self.bdexl.close_file()
            self.fsv.close_fsv()
            # self.powsup.close_ps()

    def make_dirs(self, exlpath):
        '''
        根据excel测试模板复制一份excel
        :param exlpath:
        :return:
        '''
        try:
            if self.bdexl.open_excel(exlpath):
                arm_id, bb_id = self.bdexl.get_id()
                dirname = os.path.dirname(exlpath)
                if arm_id:
                    new_path = os.path.join(os.path.join(dirname, str(arm_id)), str(bb_id))
                else:
                    new_path = dirname
                if not os.path.exists(new_path):
                    os.makedirs(new_path)
                newexl_name = str(bb_id) + '.xlsx'
                end_path = os.path.join(new_path, newexl_name)
                if os.path.exists(end_path):
                    return end_path
                else:
                    copyfile(exlpath, end_path)
                return end_path
            else:
                return None
        except Exception as e:
            logger.error(e)
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
            excel_path, fsvip, cellid, type, freqpoint_dict, freq_dict, ul_freq_dict = args
            thconf = kwargs
            # if not thconf:
            #     raise ModuleNotFoundError('高低温箱没有配置项')

            port = thconf.get('PORT', None)
            norm_temp = thconf.get('NORM_TEMP', None)
            low_temp = thconf.get('LOW_TEMP', None)
            high_temp = thconf.get('HIGH_TEMP', None)
            period = thconf.get('PERIOD', 20)  # 平衡持续时间,以分钟为单位
            if self.th_dev is None or not port:
                # 只进行常温测试
                logger.info('只进行常温测试')
                self.do_test(excel_path, fsvip, cellid, type, freqpoint_dict, freq_dict, ul_freq_dict, 1)
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
                    self.do_test(excel_path, fsvip, cellid, type, freqpoint_dict, freq_dict, ul_freq_dict,
                                 1)
                    logger.debug('******常温测试  finished****')
                if low_temp is not None:
                    logger.info('start 低温测试')
                    self.th_dev.set_temp_sv(int(low_temp) * 10)
                    self.handle_test(int(low_temp) * 10, period)
                    self.do_test(excel_path, fsvip, cellid, type, freqpoint_dict, freq_dict, ul_freq_dict,
                                 0)
                    logger.debug('******低温测试  finished****')

                if high_temp is not None:
                    logger.info('start 高温测试')
                    self.th_dev.set_temp_sv(int(high_temp) * 10)
                    self.handle_test(int(high_temp) * 10, period)
                    self.do_test(excel_path, fsvip, cellid, type, freqpoint_dict, freq_dict, ul_freq_dict,
                                 2)
                    logger.debug('******高温测试  finished****')

                logger.debug('高低温箱停止运行')
                self.th_dev.stop_dev()  # 停止运行
        except modbus_tk.modbus.ModbusError as e:
            logger.exception('{}'.format(e))
            raise StopIteration('th_dev')

    def do_test(self, excel_path, fsvip, cellid, type, freqpoint_dict, freq_dict, ul_freq_dict, temp=1):
        if excel_path is None:
            raise RuntimeError('excel does not exist!')
        if not self.bd.kill_arm_process():
            raise RuntimeError('KILL ARM FAILED')
        key_bands = freqpoint_dict.keys()
        power_txatt_dict = dict()  # {'B41':[(高txatt,高power,adj lower,adj upper),(中),(低)],'E':[(),(),()]}
        # power_range_dict = dict()  # {'B41':[[],[],[]]}
        evm_dict = dict()  # {'B41':[,,],[,,]}
        ccdf_dict = dict()
        danl_dict = dict()  # {'B41':[,,]}
        power_spectrum_dict = dict()  # 占用带宽 {'B41':[,,],'E':[,,]}
        # current_dict = dict()  # 读取 电流 {'E':[,,],}
        for band in key_bands:
            mode = 'TDD' if band in ['B41', 'E', 'F'] else 'FDD'
            logger.info('开始测试band={}'.format(band))
            self.rpt_message('INFO:开始测试band={}'.format(band))
            each_band_power_txatt = []
            # power_range_on_band = []
            evm_on_band = []
            ccdf_on_band = []
            danl_on_band = []
            power_spectrum_on_band = []  # 每个band有高中低三个频点，对应有三个带宽
            # current_on_band = []  # 工作电流
            freq_points = freqpoint_dict[band]
            freqs = freq_dict[band]
            ul_start, ul_stop = self.get_ul_center(ul_freq_dict[band])  # 上行频率，用于测底噪用
            indicator = self.read_excel_txatt_norm(excel_path)
            workmode, funid = band_dict[band]
            if self.bd.do_test(workmode, funid):
                default_txatt = self.bd.conf_board_txatt()  # TDD和FDD的初始txatt不同
                for idx, freq_point in enumerate(freq_points):
                    if not self.conf_board_on_some_freq(freq_point):  # 设置基带板一类参数，并返回PCI
                        logger.error('设置一类参数异常')
                        self.rpt_message('ERROR:设置一类参数异常')
                        continue
                    self.conf_device(fsvip)
                    freq = freqs[idx]
                    logger.debug('freq={}'.format(freq))
                    self.rpt_message('INFO:freq={}'.format(freq))
                    result = self.get_max_power(indicator, freq, default_txatt, type)
                    logger.info('get_max_power={}'.format(result))
                    self.rpt_message('INFO:get_max_power={}'.format(result))
                    if result:
                        each_band_power_txatt.append(result)
                        #for test
                        evm = self.evm_on_some_freq_and_txatt(mode, freq)
                        logger.debug('evm={}'.format(evm))
                        if evm == 0:
                            evm = None
                        evm_on_band.append(evm)
                        ccdf = self.ccdf_on_some_freq_and_txatt(mode, freq)
                        logger.debug('ccdf={}'.format(ccdf))
                        ccdf_on_band.append(ccdf)
                        #计算带宽
                        power_spectrum = self.bandwidth_on_some_freq_and_txatt(mode, freq)
                        logger.debug('power_spectrum={}'.format(power_spectrum))
                        power_spectrum_on_band.append(power_spectrum)
                        # 计算底噪
                        danl = self.DANL_ON_some_freq(temp, ul_start, ul_stop, excel_path, freq)
                        danl_on_band.append(danl)
                        # 5-9取消测试21个档位
                        # maxtxatt = result[0]
                        # power_range_on_freq = self.txatt_range_test_on_some_freq(type, freq, maxtxatt, default_txatt)
                        # power_range_on_band.append(power_range_on_freq)

            cell_band = 'cell{}_{}'.format(cellid, band)
            power_txatt_dict.setdefault(cell_band, each_band_power_txatt)
            # power_range_dict.setdefault(cell_band, power_range_on_band)  #21个档位
            evm_dict.setdefault(cell_band, evm_on_band)
            ccdf_dict.setdefault(cell_band, ccdf_on_band)
            danl_dict.setdefault(cell_band, danl_on_band)
            power_spectrum_dict.setdefault(cell_band, power_spectrum_on_band)
            # current_dict.setdefault(cell_band, current_on_band)  # 工作电流

        if self.bdexl.open_excel(excel_path):
            self.bdexl.write_max_txatt(temp, **power_txatt_dict)
            self.bdexl.write_ACPR(temp, **power_txatt_dict)  # ACPR(LOWER/UPPER)
            # self.bdexl.write_power_range(temp, **power_range_dict) #21个档位输出功率
            self.bdexl.write_ccdf(temp, **ccdf_dict)  # PPM和峰均比
            self.bdexl.write_EVM(temp, **evm_dict)  # EVM
            self.bdexl.write_DANL(temp, **danl_dict)  # 底噪
            self.bdexl.write_powerspectrum(temp, **power_spectrum_dict)
        self.bdexl.close_file()

    def txatt_range_test_on_some_freq(self, type, freq, maxtxatt, default_txatt):
        '''
        txatt档位测试,21个档位
        衰减增大，功率越小
        :return:
        '''
        # fsv.set_for_txatt(freq)
        level_num = 20
        power_lst = []  # [(),()]
        self.fsv.set_for_txatt(freq)
        if type == '8125':
            base = maxtxatt - default_txatt
            if base < -6:
                base = -6
            ct = base
            for i in range(level_num):
                ct = ct + 1
                self.bd.set_power_compensation(ct, 0)
                time.sleep(2)
                power = self.fsv.get_power(freq)[0]
                power_lst.append(power)
        elif type == 'T2K':
            ct = maxtxatt
            for i in range(level_num):
                ct = ct + 1
                self.bd.set_txatt(ct)
                time.sleep(1)
                power = self.fsv.get_power(freq)[0]
                power_lst.append(power)
        # logger.debug('power_lst={}'.format(power_lst))
        return power_lst

    def evm_on_some_freq_and_txatt(self, mode, freq):
        '''
        在基带板最大功率输出下的EVM
        :return:
        '''
        return self.fsv.get_EVM(mode, freq)

    def ccdf_on_some_freq_and_txatt(self, mode, freq):
        '''

        :param mode:
        :param freq:
        :return: (ppm,crest factor)
        '''

        return self.fsv.get_CCDF(mode, freq)

    def bandwidth_on_some_freq_and_txatt(self, mode, freq):
        '''

        :param mode:
        :param freq:
        :return: float Mhz
        '''
        return self.fsv.get_power_spectrum(mode, freq)

    def DANL_ON_some_freq(self, temp, start, stop, exlpath, freq):
        '''
        底噪，基带板设置成某频点，频谱仪在其band的[高，低频率]，且基带板要关闭射频开关
        temp:0:低温 1：常温 2：高温
        :param center_freq:
        :return:
        '''
        tempstr = ''
        if temp == 0:
            tempstr = '低温'
        elif temp == 1:
            tempstr = '常温'
        elif temp == 2:
            tempstr = '高温'

        self.bd.set_rf(0)  # 关闭射频
        time.sleep(3)
        pngpath = os.path.join(os.path.dirname(exlpath), '{}_DANL_{}.PNG'.format(tempstr, freq))
        danl = self.fsv.set_for_DANL(start, stop)
        self.fsv.save_screenshot(pngpath)
        # 打开射频
        self.bd.set_rf(1)
        time.sleep(1)
        return danl

    def conf_board_on_some_freq(self, freq):
        '''
        基于某频点
        freq:频点
        :return:
        '''

        logger.info('开始测试freq={}'.format(freq))
        try:
            flag = self.bd.conf_para(freq)  # 设置频点并打开功放
            return flag
        except Exception as e:
            logger.error(e)
            return False

    def get_max_power(self, power_indicator, freq, default_txatt, type):
        '''
        获取基带板的最大输出功率及对应的txatt
        indicator:标准值 str
        freq:频率 str
        default_txatt :int
        type:str
        :return:(float power,int txatt)
        '''
        norm = power_indicator  # 标准值
        current_txatt = self.bd.read_txatt()
        logger.debug('current_txatt={}'.format(current_txatt))
        ref_level = 10
        self.fsv.set_for_txatt(ref_level, freq)
        if current_txatt is not None:
            power = self.fsv.get_power(ref_level, freq)[0]
            logger.debug('current_power={}'.format(power))
            if power is not None:
                if type == '8125':
                    while True:
                        delta = round(float(power)) - int(norm) + current_txatt - default_txatt
                        logger.debug('delta={}'.format(delta))
                        if delta < -6:
                            delta = -6
                        self.bd.set_power_compensation(delta, 0)
                        time.sleep(2)
                        current_txatt = self.bd.read_txatt()
                        logger.debug('curr_txatt={}'.format(current_txatt))
                        if current_txatt is None:
                            raise RuntimeError('read txatt error')
                        time.sleep(1)
                        plst = self.fsv.get_power(ref_level, freq)
                        logger.debug('plst={}'.format(plst))
                        if plst is None:
                            break
                        power = plst[0]
                        if abs(float(power) - int(norm)) < 1:
                            return (current_txatt, float(power), float(plst[1]), float(plst[2]))
                        if delta == -6:
                            return (current_txatt, float(power), float(plst[1]), float(plst[2]))
                elif type == 'T2K':
                    while True:
                        delta = round(float(power)) - int(norm)
                        new_txatt = current_txatt + delta
                        logger.debug('new_txatt={}'.format(new_txatt))
                        if new_txatt < default_txatt:
                            new_txatt = default_txatt
                        self.bd.set_txatt(new_txatt)
                        time.sleep(2)
                        current_txatt = self.bd.read_txatt()
                        logger.debug('curr_txatt={}'.format(current_txatt))
                        if current_txatt is None:
                            raise RuntimeError('read txatt error')
                        plst = self.fsv.get_power(ref_level, freq)
                        logger.debug('plst={}'.format(plst))
                        if plst is None:
                            break
                        power = plst[0]
                        if abs(float(power) - int(norm)) < 1:
                            return (current_txatt, float(power), float(plst[1]), float(plst[2]))
                        if current_txatt == default_txatt:
                            return (current_txatt, float(power), float(plst[1]), float(plst[2]))

        return None

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

    def read_excel_txatt_norm(self, excel_path):
        '''
        读取excel的上下行功率，频点等参数
        :param excel_path:
        :return:
        '''
        try:
            if self.bdexl.open_excel(excel_path):
                indicator = self.bdexl.get_txatt_norm()[1]  # 获取txatt指标
                return indicator
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
                self.bdexl.get_dl_rows()
                self.bdexl.get_ul_rows()
                # self.bdexl.get_normaltemp_level_rows()
                type, freqpoint_dict, freq_dict = self.bdexl.get_set_condition(cellid)
                ul_freq_dict = self.bdexl.get_ul_freq(cellid)
                return type, freqpoint_dict, freq_dict, ul_freq_dict
        except Exception as e:
            raise RuntimeError('read_boardtype ERROR:{}'.format(e))

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
            if i > 3:
                raise ModuleNotFoundError('FSV NOT ONLINE')
            i = i + 1
            try:
                self.fsv.init_fsv(fsvip)
                time.sleep(1)
                self.fsv.reset_fsv()
                time.sleep(1)
                break
            except Exception:
                time.sleep(3)
                continue
