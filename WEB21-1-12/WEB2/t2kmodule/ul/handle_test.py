# coding:utf-8
'''
处理自动化测试
'''

import os
from shutil import copyfile
import atexit
import time
import modbus_tk
from asgiref.sync import async_to_sync
from celery.utils.log import get_task_logger
# from api.power_supply import PowerSupply_SCPI
from commoninterface.smbvbase import SMBVBase
from t2kmodule.ul.handle_board import B8125Handler, BT2KHandler
from .common_excel import BoardExcel
from commoninterface.winauto import T2KEXEOperate
from commoninterface.master import THDevice

logger = get_task_logger('ghost')


band_dict = {'B41': ('0', '5'), 'E': ('0', '0'), 'F': ('0', '2'),
             'B1': ('1', '4'), 'B3': ('1', '3')}


class DoULTest(object):

    def __init__(self,chl_name,chl_layer):
        # self.powsup = PowerSupply_SCPI()  # 电源
        self.smbv = SMBVBase()  # 信号源
        self.bd = None  # T2K
        # self.b_board = None  # 另一块8124/8125用于同步
        self.bdexl = BoardExcel()  # excel模板
        self.channel_name = chl_name
        self.channel_layer = chl_layer
        atexit.register(self.clean)

    def clean(self):
        self.smbv.close_inst()
        self.bdexl.close_file()

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

    def init_all(self, smbvconf, bdconf, thconf):
        try:
            exlpath = bdconf['DIR']
            smbvip = smbvconf['IP']  # 信号源IP地址
            exepath = smbvconf['PATH']  # 灵敏度测试软件路径
            self.smbv.set_offset(float(smbvconf['OFFSET']))
            # for test
            self.smbv.init_inst(smbvip)
            self.smbv.reset_smbv()
            self.smbv.close_inst()
            excel_path = self.make_dirs(exlpath)  # 复制excel模板
            cellid = str(bdconf.get('CELL', '0'))
            type, freqpoint_dict, freq_dict, ul_freq_dict = self.read_boardtype(excel_path, cellid)
            logger.debug(freqpoint_dict)  # 下行频点
            logger.debug(ul_freq_dict)  # 上行频率
            self.rpt_message('INFO:{}'.format(freqpoint_dict))
            self.rpt_message('INFO:{}'.format(ul_freq_dict))
            if type == '8125':
                self.bd = B8125Handler(**bdconf)
            elif type == 'T2K':
                self.bd = BT2KHandler(**bdconf)
            # T2K不区分主从片

            boardip = bdconf['IP']
            # if cellid == '1' and bb_conf:  # conf.json中有b_BOARD的配置且cellid='1'才启用
            #     self.b_board = B8125Handler(**bb_conf)  # 用于同步的8124/8125基带板
            self.th_dev = None
            if thconf:
                self.th_dev = THDevice()
            params_lst = [excel_path, exepath, smbvip, boardip, cellid, freqpoint_dict,
                          ul_freq_dict]
            self.gd_test(*params_lst, **thconf)
            self.rpt_message('测试完成OK')
        except Exception as e:
            logger.error('error.{}.'.format(e))
            self.rpt_message('ERROR:{}.'.format(e))
            self.rpt_message('测试失败')
            return False
        else:
            return True
        finally:
            self.bdexl.close_file()
            # self.powsup.close_ps()
            self.smbv.close_inst()

    def make_dirs(self, exlpath):
        '''
        根据excel测试模板复制一份excel
        :param exlpath:
        :return:
        '''
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
            excel_path, exepath, smbvip, boardip, cellid, freqpoint_dict, \
            ul_freq_dict = args
            thconf = kwargs
            # if not thconf:
            #     raise ModuleNotFoundError('高低温箱没有配置项')
            logger.debug(exepath)
            port = thconf.get('PORT', None)
            norm_temp = thconf.get('NORM_TEMP', None)
            low_temp = thconf.get('LOW_TEMP', None)
            high_temp = thconf.get('HIGH_TEMP', None)
            period = thconf.get('PERIOD', 20)  # 平衡持续时间,以分钟为单位
            if self.th_dev is None or not port:
                # 只进行常温测试
                self.do_test(excel_path, exepath, smbvip, boardip, cellid,
                             freqpoint_dict, ul_freq_dict)
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
                    self.do_test(excel_path, exepath, smbvip, boardip, cellid, freqpoint_dict,
                                 ul_freq_dict, 1)
                    logger.debug('******常温测试  finished****')
                if low_temp is not None:
                    logger.info('start 低温测试')
                    self.th_dev.set_temp_sv(int(low_temp) * 10)
                    self.handle_test(int(low_temp) * 10, period)
                    self.do_test(excel_path, exepath, smbvip, boardip, cellid, freqpoint_dict,
                                 ul_freq_dict, 0)
                    logger.debug('******低温测试  finished****')

                if high_temp is not None:
                    logger.info('start 高温测试')
                    self.th_dev.set_temp_sv(int(high_temp) * 10)
                    self.handle_test(int(high_temp) * 10, period)
                    self.do_test(excel_path, exepath, smbvip, boardip, cellid, freqpoint_dict,
                                 ul_freq_dict, 2)
                    logger.debug('******高温测试  finished****')

                logger.debug('高低温箱停止运行')
                self.th_dev.stop_dev()  # 停止运行
        except modbus_tk.modbus.ModbusError as e:
            logger.exception('th_dev {}'.format(e))
            raise StopIteration('th_dev')
        except Exception as e:
            logger.error('gd_test:{}'.format(e))
            raise StopIteration('gd_test:{}'.format(e))

    def get_workmode_funid(self, bandsdict):
        '''

        :param bandsdict: {'cell0':[],'cell1':[]}
        :return:
        '''
        logger.debug(bandsdict)
        cell0 = bandsdict['cell0']
        band0 = cell0[0] if len(cell0) > 0 else 'E'
        cell1 = bandsdict['cell1']
        band1 = cell1[0] if len(cell1) > 0 else 'B1'
        lst = list(band_dict[band0]) + list(band_dict[band1])
        return lst

    def do_test(self, excel_path, exepath, smbvip, boardip, cellid, freqpoint_dict,
                ul_freq_dict, temp=1):
        if excel_path is None:
            raise RuntimeError('excel does not exist!')
        if not self.bd.kill_arm_process():
            raise RuntimeError('KILL ARM FAILED')
        key_bands = freqpoint_dict.keys()
        sens_dict = dict()  # 灵敏度  {'E':[高,中，低],}
        # workmode_funid_lst = self.get_workmode_funid(bandsdict)

        for band in key_bands:
            mode = 'TDD' if band in ['B41', 'E', 'F'] else 'FDD'
            logger.info('开始测试band={}'.format(band))
            self.rpt_message('INFO:开始测试band={}'.format(band))
            cell_band = 'cell{}_{}'.format(cellid, band)
            sens_norm_list = self.read_sens_norm_from_excel(excel_path, cell_band)  # 读取每个band灵敏度指标
            if sens_norm_list is None:
                raise NotImplementedError('灵敏度指标为空')
            logger.debug('sens指标{}'.format(sens_norm_list))
            sens_on_band = []  # 灵敏度
            freq_points = freqpoint_dict[band]  # 频点[高，中，低]
            try:
                self.conf_device(smbvip)  # 初始化仪器仪表
                flag = self.conf_board()  # 设置T2K协程
                if not flag:
                    logger.error('基带板初始化设置异常')
                    self.rpt_message('ERROR:基带板初始化设置异常')
                    continue
                self.bd.conf_board_txatt()  # TDD和FDD的初始txatt不同
                for idx, freq_point in enumerate(freq_points):
                    self.smbv.reset_smbv()  # 关信号源
                    uplink_freq = ul_freq_dict[band][idx]  # 对应的上行频率
                    ret, pci = self.conf_board_on_some_freq(freq_point)  # 设置基带板一类参数，并返回PCI
                    if not ret:
                        logger.error('T2K 设置异常')
                        self.rpt_message('ERROR:T2K 设置异常')
                        continue
                    if pci is None:
                        logger.error('T2K 一类参数异常')
                        self.rpt_message('ERROR:T2K 一类参数异常')
                        continue
                    sens = self.repeat_sens_on_freq(cellid, smbvip, uplink_freq, mode, pci, boardip,
                                                    exepath, sens_norm_list)
                    sens_on_band.append(sens)
                    # FDD测试重启T2K
                    # self.bd.reboot()
                    # time.sleep(1)

                sens_dict.setdefault(cell_band, sens_on_band)  # 灵敏度
            except Exception as e:
                logger.error(e)
            finally:
                self.smbv.close_inst()

        if self.bdexl.open_excel(excel_path):
            self.bdexl.write_sens(temp, **sens_dict)
        self.bdexl.close_file()

    def conf_board(self):
        '''
        设置T2K
        :return:
        '''
        if self.bd is None:
            return True

        return self.bd.do_test()

    def conf_board_on_some_freq(self, freq):
        '''
        基于某频点
        freq:频点
        :return:
        '''
        try:
            logger.info('开始测试freq={}'.format(freq))
            self.rpt_message('INFO:开始测试freq={}'.format(freq))
            return self.bd.conf_para(freq)  # 设置频点并打开功放
        except Exception as e:
            logger.error(e)
            self.rpt_message('ERROR:{}'.format(e))
            return False

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
                indicator = self.bdexl.get_txatt_norm()['标准值']  # 获取txatt指标
                return indicator
        except Exception as e:
            raise RuntimeError(e)
        finally:
            self.bdexl.close_file()

    def read_sens_norm_from_excel(self, excel_path, cell_band):
        '''
        读取灵敏度指标范围
        :param excel_path:
        :return: [下限，上限]
        '''
        try:
            if self.bdexl.open_excel(excel_path):
                lowup = self.bdexl.get_sens_norm(cell_band)
                return lowup
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
                # bandsdict = self.bdexl.get_bands()
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

    def conf_smbv(self, ip, freq, mode, pci):
        '''
        设置信号源，level没有设置
        :param ip:
        :param freq: 频率,MHz为单位
        :param mode: TDD/FDD
        pci:从基带板读取的
        :return:
        '''
        i = 0
        while 1:
            i = i + 1
            if i > 3:
                raise ModuleNotFoundError('SMBV NOT ONLINE')
            try:
                self.smbv.init_inst(ip)
                break
            except Exception:
                time.sleep(5)
                self.smbv.close_inst()
                continue

        self.smbv.reset_smbv()
        print('***********')
        self.smbv.set_freq(freq)
        if mode == 'TDD':
            self.smbv.set_TDD_lte(pci)
        elif mode == 'FDD':
            self.smbv.set_FDD_lte(pci)
        self.smbv.set_rf_on()

    def repeat_sens_on_freq(self, cellid, ip, freq, mode, pci, boardip, exepath, normlist):
        '''
        重复获取灵敏度，有时读中兴软件会失败
        :return:
        '''
        i = 0
        while 1:
            flag = self.sens_on_somefreq(cellid, ip, freq, mode, pci, boardip, exepath, normlist)
            if i > 3:
                logger.error('无法操作中兴灵敏度软件')
                self.rpt_message('ERROR:无法操作中兴灵敏度软件')
                raise NotImplementedError('无法操作中兴灵敏度软件')
            if flag is False:
                logger.debug('操作中兴软件失败')
                self.rpt_message('ERROR:操作中兴软件失败')
                i = i + 1
                time.sleep(5)
                continue
            return flag

    def sens_on_somefreq(self, cellid, ip, freq, mode, pci, boardip, exepath, normlist):
        '''
        测试灵敏度，需要结合中兴的软件和信号源,顺序无所谓，只要基带板先配置
        cellid:0/1
        ip:信号源ip
        freq:信号源频率，上行
        mode:TDD/FDD
        pci:基带板pci
        boardip:基带板IP
        exepath:中兴软件路径
        normlist:灵敏度上下限
        :return:int level
        '''
        # if type == 'T2K':
        exeauto = T2KEXEOperate()
        # elif type == '8125':
        #     exeauto = EXEOperate()
        if exeauto is None:
            logger.error('基带板类型wrong')
            return False
        try:
            # 设置信号源
            self.conf_smbv(ip, freq, mode, pci)
            # 启动中兴软件
            print('**start exe****')
            exeauto.start_exe(boardip, exepath)

            if not exeauto.site_manage():
                logger.error('操作灵敏度软件错误')
                return False
            if not exeauto.enter_test_mode(cellid, mode):
                logger.error('操作灵敏度软件错误')
                return False
            if not exeauto.create_ue():
                logger.error('操作灵敏度软件错误')
                return False
            coord = exeauto.ready_for_check()  # 返回误码率表格所在位置
            low_sens = int(normlist[0])  # 灵敏度下限
            upper_sens = int(normlist[1])  # 灵敏度上限
            sens = low_sens
            i = 0
            while sens <= upper_sens:
                if i > 3:
                    raise ModuleNotFoundError('bbSMBV not online')
                if not self.smbv.set_level(sens):
                    # 设置信号源
                    time.sleep(3)
                    logger.debug('conf_smbv')
                    # self.conf_smbv(ip, freq, mode, pci)
                    i = i + 1
                    continue
                i = 0
                logger.debug('设置level={}'.format(sens))
                self.rpt_message('INFO:设置level={}'.format(sens))
                time.sleep(1)
                berlist = exeauto.check_result(coord)  # 误码率
                logger.debug('berlist={}'.format(berlist))
                self.rpt_message('INFO:berlist={}'.format(berlist))
                if not berlist:
                    time.sleep(3)
                    continue
                if self.check_sens_ok(berlist):  # 误码率达标
                    return sens
                sens += 1
                time.sleep(.5)
            # T2K FDD测试经常100，需要重启多次

            return None  # 在灵敏度指标范围内没有找到误码率为0的level
        except Exception as e:
            logger.error(e)
            return False
        finally:
            try:
                if exeauto:
                    exeauto.close_exe()
            except Exception as e:
                pass

    def check_sens_ok(self, lst):
        '''
        判断误码率每个值是否都小于3
        lst:float list
        :return:
        '''
        retlist = [True if item < 5 else False for item in lst]
        return all(retlist)

    def conf_device(self, smbvip):
        '''
        仪器初始化
        :return:
        '''
        # 初始化信号源
        logger.debug('设置信号源')
        self.smbv.init_inst(smbvip)
        self.smbv.reset_smbv()
        # self.powsup.init_ps(spport)
        # time.sleep(1)
        # self.powsup.reset_ps()
        # time.sleep(2)

    def reset_smbv(self, smbvip):
        # 初始化信号源
        self.smbv.init_inst(smbvip)
        self.smbv.reset_smbv()
