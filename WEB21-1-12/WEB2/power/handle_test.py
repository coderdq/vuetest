# coding:utf-8
'''
处理自动化测试
'''
import time
import copy
import threading
import logging
import os
import math
from shutil import copyfile

import modbus_tk
import queue
from asgiref.sync import async_to_sync
from celery.utils.log import get_task_logger
from commoninterface.master import THDevice
from .common_excel import BoardExcel
from .zvl_test import HandleZVL
from .fsv_test import HandleFSVAndSMBV


logger = get_task_logger('ghost')


class DOTEST(object):
    def __init__(self,chl_name,chl_layer):
        self.fsv_smbv = None  # 信号源和频谱仪
        self.zvl = None  # 矢网
        self.th_dev = None  # 高低温箱
        self.bdexl = BoardExcel()  # 读写excel
        self.exlpath = None
        self.th1_evt = threading.Event()
        self.th1_evt.clear()
        self.que = queue.Queue()
        self.channel_name = chl_name
        self.channel_layer = chl_layer
        # self.th1 = threading.Thread(target=self.output_data)  # 输出结果到excel
        # self.th1.setDaemon(True)
        # self.th1.start()

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

    def init_all(self, conf_dict):
        '''
        df_need
                   中       低       高
B1 DL  2140.0  2112.5  2167.5
   UL  1950.0  1922.5  1977.5
B3 DL  1842.5  1807.5  1877.5
   UL  1747.5  1712.5  1782.5
        :param conf_dict:
        :return:
        '''
        try:
            fsv_conf = conf_dict.get('FSV', {})  # 频谱仪
            fsv_ip = fsv_conf['IP']
            fsv_offset = fsv_conf['OFFSET']
            zvl_conf = conf_dict.get('ZVL', {})  # 矢网
            zvl_ip = zvl_conf['IP']
            zvl_offset = zvl_conf.get('OFFSET', 41)
            smbv_conf = conf_dict.get('SMBV', {})  # 信号源
            smbv_ip = smbv_conf['IP']
            amp_conf = conf_dict.get('POWER', {})  # 功放配置
            th_conf = conf_dict.get('THDEVICE', {})  # 高低温箱配置
            if th_conf:
                self.th_dev = THDevice()
            epath = amp_conf['DIR']
            excel_path = self.make_dirs(epath)
            if excel_path is None:
                raise RuntimeError('excel does not exist!')
            self.exlpath = excel_path
            logger.debug(self.exlpath)
            self.rpt_message('INFO:excel_path={}'.format(self.exlpath))
            zvl_state = amp_conf['ZVLSTATE']  # 是否需要矢网，需要矢网就不需要频谱，信号源
            if zvl_state == '1':
                self.zvl = HandleZVL(zvl_ip, zvl_offset)
            else:
                self.fsv_smbv = HandleFSVAndSMBV(fsv_ip, smbv_ip, fsv_offset)

            bands = amp_conf['BAND'].strip().split(',')  # 需要测的band列表
            isdl = str(amp_conf['DL'])  # 是否是测下行 '1'测下行，'0'测上行
            read_ul = False
            if isdl == '1':  # 测下行
                self.bdexl.set_sheetnum(0)  # excel的第一个sheet

            else:  # 测上行
                self.bdexl.set_sheetnum(1)  # excel的第二个sheet
                read_ul = True

            df = self.read_excel_para(excel_path, read_ul)
            band_lst = [item.upper() for item in bands]
            df_need = df.loc[band_lst]
            params_lst = [band_lst, df_need, isdl]
            self.gd_test(*params_lst, **th_conf)
            return True,excel_path
            # loop = asyncio.get_event_loop()
            # loop.run_until_complete(self.gd_test(*params_lst, **th_conf))
            # loop.close()

            # self.do_test(band_lst, df_need)

        except Exception as e:
            logger.error(e)
            self.rpt_message('ERROR:{}'.format(e))
            return False
        finally:
            self.bdexl.close_file()
            self.zvl.close_zvl()
            self.fsv_smbv.close_all()


    def read_excel_para(self, excel_path, read_ul):
        '''
        获取频率参数
        :return:
        '''
        logger.debug('read excel para')
        try:
            if self.bdexl.open_excel(excel_path):
                self.bdexl.get_dl_rows()
                if read_ul:
                    self.bdexl.get_ul_rows()
                df = self.bdexl.get_band_para()
                if df is None:
                    raise NotImplementedError('excel para empty')
                return df
        except Exception as e:
            logger.error('read excel para error:{}'.format(e))
        finally:
            self.bdexl.close_file()

    def make_dirs(self, exlpath):
        '''
        根据excel测试模板复制一份excel
        :param exlpath:
        :return:
        '''
        try:
            logger.debug(exlpath)
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
                i=0
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
        logger.info('start 功放测试....')

    def gd_test(self, *args, **kwargs):
        try:
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
                self.do_test(1, *args)
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
                    self.do_test(1, *args)
                    logger.debug('******常温测试  finished****')
                if low_temp is not None:
                    logger.info('start 低温测试')
                    self.th_dev.set_temp_sv(int(low_temp) * 10)
                    self.handle_test(int(low_temp) * 10, period)
                    self.do_test(0, *args)
                    logger.debug('******低温测试  finished****')

                if high_temp is not None:
                    logger.info('start 高温测试')
                    self.th_dev.set_temp_sv(int(high_temp) * 10)
                    self.handle_test(int(high_temp) * 10, period)
                    self.do_test(2, *args)
                    logger.debug('******高温测试  finished****')

                logger.debug('高低温箱停止运行')
                self.th_dev.stop_dev()  # 停止运行
        except modbus_tk.modbus.ModbusError as e:
            logger.exception('{}'.format(e))
            raise StopIteration('th_dev')

    def do_test(self, temp=1, *args):
        '''

        :param lband: ['B1','B3']
        :param df:
           中       低       高
B1 DL  2140.0  2112.5  2167.5
   UL  1950.0  1922.5  1977.5
B3 DL  1842.5  1807.5  1877.5
   UL  1747.5  1712.5  1782.5
        :return:
        '''
        lband, df, isdl = args
        # logger.debug('args={}'.format(args))
        dl_ul = 'DL' if isdl == '1' else 'UL'  # 是测上行还是下行

        self.test_zvl(temp, lband, df, dl_ul)
        self.test_fsv_and_smbv(temp, lband, df, dl_ul)
        if self.fsv_smbv:
            self.fsv_smbv.close_rf()
        logger.debug('test finished')
        self.rpt_message('INFO:test finished')

    def test_zvl(self, temp, lbd, df, dl_ul):
        '''
        上行基于矢网测试
        上行的增益，带内波动，带外抑制，vswr,
        下行基于矢网的测试：vswr,带外抑制
        :return:
        '''
        if self.zvl is None:
            return
        flag = True
        if dl_ul == 'DL':
            flag = False
        logger.debug('test_zvl_ul')
        # self.que.put('0')  #类型，写excel的类型
        self.zvl.init_zvl(self.exlpath)
        gain_dict = dict(zip(lbd, [[]] * len(lbd)))  # {'E':[高增益，中增益，低增益，带内波动],'F':[]}
        vswr_dict = dict(zip(lbd, [[]] * len(lbd)))  # {'E':[x,y],'F':[x,y]}
        gain_freq_dict = dict(zip(lbd, [[]] * len(lbd)))  # {'E':[,,,,,],'F':[,,,,,]}
        for band in lbd:
            freqlst = df.loc[band, dl_ul].loc[['高', '中', '低']].values
            logger.debug(freqlst)
            self.rpt_message('INFO:{}'.format(freqlst))
            if flag:  # 只有上行才用矢网测增益和带内波动
                ret_gain = self.zvl.get_gain(*freqlst)  # list
                gain_dict[band] = ret_gain
            vswr_ret = self.zvl.get_vswr(*freqlst, dl_ul, temp)  # list
            vswr_dict[band] = vswr_ret
            markerlist = self.get_marker1(band)
            freq_ret = self.zvl.get_gain_vs_freq(markerlist, dl_ul, temp)  # list
            gain_freq_dict[band] = freq_ret
        self.que.put([temp, '0', [gain_dict, vswr_dict, gain_freq_dict]])
        time.sleep(.5)
        self.th1_evt.set()
        self.output_data()

    def get_marker1(self, band):
        '''
        读取excel的带外抑制点
        :return:list
        '''
        excel_path = copy.deepcopy(self.exlpath)
        try:
            if self.bdexl.open_excel(excel_path):
                return self.bdexl.get_gain_vs_freq_list(band)
            return None
        except Exception as e:
            logger.error('get_marker error {}'.format(e))
            return None
        finally:
            self.bdexl.close_file()

    def test_fsv_and_smbv(self, temp, lband, df, dl_ul):
        '''
        测试下行的增益，带内波动，EVM
        :param temp:
        :param lband:
        :param df:
        :param dl_ul:
        :return:
        '''
        if dl_ul == 'UL':
            return
        if self.fsv_smbv is None:
            return
        logger.debug('test_fsv_and_smbv')
        self.fsv_smbv.init_all()

        current_dict = dict(zip(lband, [[]] * len(lband)))  # {'E':[(信号源输入，频谱仪输出，ACPR),(,,)]}
        evm_dict = dict(zip(lband, [[]] * len(lband)))  # {'E':[(功放+信号源的evm,信号源的evm,功放的evm),()]}
        gain_dict = dict(zip(lband, [[]] * len(lband)))  # {'E':[(信号源输入，频谱输出，增益),(),()],'F':[,,,,,]}
        ripple_dict = dict(zip(lband, [None] * len(lband)))  # {'E':None,'F':None}
        try:
            for band in lband:
                logger.debug('测试band{}'.format(band))
                self.rpt_message('INFO:测试band{}'.format(band))
                freqlst = df.loc[band, dl_ul].loc[['高', '中', '低']].values
                target_power_for_gain = None
                target_power_for_evm = None
                evm_alone_lst = None  # 信号源evm[高，中，低]
                markerlist = None
                if self.bdexl.open_excel(self.exlpath):
                    target_power_for_gain = self.bdexl.get_target_power(band)  # dBm
                    target_power_for_evm = self.bdexl.get_target_power_for_evm(band)  # dBm
                    logger.debug('target_power_for_evm={}'.format(target_power_for_evm))
                    self.rpt_message('INFO:target_power_for_evm={}'.format(target_power_for_evm))
                    evm_alone_lst = self.bdexl.get_evm(temp, band)
                    markerlist = self.bdexl.get_gain_dl_marker(band)  # 增益的marker点
                self.bdexl.close_file()
                if target_power_for_gain is None:
                    raise NotImplementedError('no target power')
                if target_power_for_evm is None:
                    raise NotImplementedError('no target power')
                # 增益，带内波动
                if markerlist:
                    gainlist = []
                    alllist = []
                    for marker in markerlist:
                        level, power, gain = self.fsv_smbv.get_max_single_tone(marker, target_power_for_gain)
                        gainlist.append(float(gain))
                        alllist.append((level, power, gain))
                    ripple = max(gainlist) - min(gainlist)  # 带内波动
                    ripple_dict[band] = ripple
                    gain_dict[band] = alllist

                for idx, freq in enumerate(freqlst):
                    power_list = self.fsv_smbv.get_max_power(freq, target_power_for_evm)
                    current_dict.setdefault(band, []).append(power_list)
                    evm = self.fsv_smbv.get_evm(freq)
                    evm_list = [None] * 3
                    if evm_alone_lst != [None] * 3 and evm:
                        evm_of_amp = '%.2f' % (math.sqrt(pow(float(evm), 2) - pow(float(evm_alone_lst[idx]), 2)))
                        evm_list = [evm, evm_alone_lst[idx], evm_of_amp]

                    evm_dict.setdefault(band, []).append(evm_list)
            self.que.put([temp, '1', [gain_dict, ripple_dict, current_dict, evm_dict]])
            time.sleep(.3)
            self.th1_evt.set()
            self.output_data()
        except Exception as e:
            logger.error('test_fsv_and_smbv error {}'.format(e))
            self.rpt_message('ERROR:test_fsv_and_smbv error {}'.format(e))
        finally:
            self.bdexl.close_file()
            self.fsv_smbv.close_all()

    def output_data(self):
        '''
        输出数据到excel
        :return:
        '''
        try:
            if self.th1_evt.is_set():
                outlst = self.que.get()
                if len(outlst) < 3:
                    logger.error('output error')
                temp, pattern, valst = outlst
                if pattern == '0':
                    self.write_zvl_result(valst, temp)
                elif pattern == '1':
                    self.write_fsv_result(valst, temp)
                self.th1_evt.clear()
        except Exception as e:
            logger.error(e)

    def write_zvl_result(self, retlst, temp):
        '''
        记录矢网的测试结果，包括增益，带内波动，带外抑制
        retlst:[]
        :return:
        '''
        logger.debug('write_zvl_result')
        self.rpt_message('INFO:write_zvl_result')
        gain_dict, vswr_dict, gain_freq_dict = retlst

        excel_path = copy.deepcopy(self.exlpath)
        try:
            if self.bdexl.open_excel(excel_path):
                self.bdexl.write_gain(temp, **gain_dict)
                self.bdexl.write_vswr(temp, **vswr_dict)
                self.bdexl.write_gain_vs_freq(temp, **gain_freq_dict)
        except Exception as e:
            logger.error('write zvl result error {}'.format(e))
        finally:
            self.bdexl.close_file()

    def write_fsv_result(self, retlist, temp):
        logger.debug('write_fsv_result')
        self.rpt_message('INFO:write_fsv_result')
        gain_dict, ripple_dict, current_dict, evm_dict = retlist

        excel_path = copy.deepcopy(self.exlpath)
        ct = dict()  # {'E':[(信号源输入，频谱输出),(信号源输入，频谱输出),()]}
        acpr_dict = dict()  # {'E':[高，中，低]}
        try:
            if self.bdexl.open_excel(excel_path):
                if current_dict is not None:
                    for key, item in current_dict.items():
                        lst1 = [io[:2] for io in item]
                        ct[key] = lst1
                        lst2 = [io[2] for io in item]
                        acpr_dict[key] = lst2

                    self.bdexl.write_current(temp, **ct)
                    self.bdexl.write_ACPR(temp, **acpr_dict)
                self.bdexl.write_EVM(temp, **evm_dict)
                self.bdexl.write_dl_gain(temp, **gain_dict)
                self.bdexl.write_ripple(temp, **ripple_dict)

        except Exception as e:
            logger.error('write_fsv_result error {}'.format(e))
        finally:
            self.bdexl.close_file()
