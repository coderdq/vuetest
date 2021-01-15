# coding:utf-8
'''
温度补偿自动化测试
'''
import os
import datetime
import re
import json
from shutil import copyfile

import time
import modbus_tk
import threading
import atexit
from asgiref.sync import async_to_sync

from .api.fsv import FSVCtrl
from .baseboard.handle_board import BT2KHandler
from .excel.common_excel import BoardExcel
from commoninterface.master import THDevice
from .ftp.ftp_client import MyFTP
from .api.file_process import FlatProcess, GainProcess
from commoninterface.utils import PropagatingThread


class TcompTEST(object):

    def __init__(self,chl_name,chl_layer,log):
        self.channel_name = chl_name
        self.channel_layer = chl_layer
        self.logger = log
        self.fsv = FSVCtrl()  # 频谱仪
        self.bd = None
        self.bdexl = BoardExcel()  # excel模板
        self.th_dev = None
        self.process_flat = FlatProcess()
        self.process_gain = GainProcess()

        self.adjust_evt = threading.Event()
        self.adjust_evt.clear()
        self.wait_evt = threading.Event()
        self.wait_evt.clear()
        self.wait_thread = PropagatingThread(target=self.check_cpu_temp)
        self.wait_thread.setDaemon(True)
        self.wait_thread.start()
        self.adjust_thread = None
        atexit.register(self.clean)

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

    def clean(self):
        self.fsv.close_inst()
        self.bdexl.close_file()

    def init_all(self, fsvconf, bdconf, thconf):
        try:
            fsvip = fsvconf['IP']
            exlpath = fsvconf['DIR']

            self.bd = BT2KHandler(**bdconf)
            bip = bdconf['IP']  # 设备IP
            if thconf:
                self.th_dev = THDevice()  # 高低温箱初始化
            ret = self.bd.read_bb_sn()
            if ret is None:
                raise RuntimeError('no serial number or productno')
            bbver, sn, productno = ret  # 返回BB版本，序列号,物料号
            excel_path = self.make_dirs(exlpath, sn, bbver, productno)  # 复制excel模板
            fsvoffset = self.read_offset(excel_path)
            # for test
            self.fsv.init_inst(fsvip)
            self.fsv.set_offset(fsvoffset)  # 设置衰减值
            self.fsv.reset_fsv()
            self.fsv.close_inst()

            params_lst = [productno, excel_path, bip, fsvip]
            self.gd_test(*params_lst, **thconf)
            return True,excel_path
        except Exception as e:
            self.logger.error('error.{}.'.format(e))
            self.rpt_message('ERROR.{}.'.format(e))
            return False
        finally:
            self.bdexl.close_file()
            self.fsv.close_inst()

    def make_dirs(self, exlpath, sn, bbver, pno):
        '''
        根据excel测试模板复制一份excel
        :param exlpath:
        :return:
        '''

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
                self.bdexl.write_productno(pno)
            else:
                return None
            return end_path
        except Exception as e:
            self.logger.error(e)
        finally:
            self.bdexl.close_file()

    def gd_test(self, *args, **kwargs):
        try:
            thconf = kwargs
            # if not thconf:
            #     raise ModuleNotFoundError('高低温箱没有配置项')
            port = thconf.get('PORT', None)
            # for test
            # self.do_test(*args)
            if self.th_dev.connect_th(PORT='COM{}'.format(port)):
                self.logger.info('高低温箱connected**')
                self.th_dev.set_fixed_mode()
                self.th_dev.start_dev()
                self.do_test(*args)
                self.logger.debug('高低温箱20度运行')
                # self.th_dev.stop_dev()  # 停止运行
                self.th_dev.set_temp_sv(int(20 * 10))  # 设置成20度
        except modbus_tk.modbus.ModbusError as e:
            self.logger.exception('{}'.format(e))
            raise StopIteration('th_dev')

    def do_test(self, *args):
        productno, excel_path, bip, fsvip = args
        if excel_path is None:
            raise RuntimeError('excel does not exist!')
        if not self.bd.do_set_bd():
            raise RuntimeError('强建小区失败')

        self.do_test_on_cellid(productno, excel_path, bip, fsvip)
        self.bd.switch_reboot()  # 开启检测不到采集就重启的开关

    def set_bd_rf(self, freqpoint_dict):
        key_bands = freqpoint_dict.keys()
        for cellband in key_bands:
            if 'CELL0' in cellband.upper():
                cellid = '0'
                self.bd.set_rf('1', 0)
            else:
                cellid = '1'
                self.bd.set_rf('0', 0)
            freq_points = freqpoint_dict[str(cellband)]
            self.conf_board_on_some_freq(cellid, freq_points[0])

    def do_test_on_cellid(self, productno, excel_path, bip, fsvip):
        freqpoint_dict, freq_dict = self.read_boardtype(excel_path)  # 返回各band的频点，频率
        self.logger.debug(freqpoint_dict)
        self.logger.debug(freq_dict)
        power_range, test_temp, centertemp = self.read_excel_txatt_norm(excel_path)  # 功率的指标[下限，标准值，上限]
        self.logger.debug(power_range)

        test_temp = [float(item) for item in test_temp]
        centertemp = float(centertemp)

        if not self.bd.do_compensation('0'):
            return
        # 初始化温补,频补表
        self.init_flat_and_gain_comp(productno, freqpoint_dict, test_temp, centertemp, bip, excel_path)
        # 打开该打开的射频开关并将档位设置成0档
        self.set_bd_rf(freqpoint_dict)
        self.set_cpu_temp(centertemp, 0,0)
        if self.process_flat.read_and_set(freqpoint_dict, centertemp):
            self.update_bb_flat_comp(productno, bip, excel_path)
        if self.process_gain.read_and_set(freqpoint_dict):
            self.update_bb_gain_comp(productno, bip, excel_path)

        # for test
        flg = self.repeat_flat_comp(centertemp, fsvip, freqpoint_dict, freq_dict, power_range, productno, bip,
                                    excel_path)
        if not flg:
            self.rpt_message('基准温度补偿失败')
            raise RuntimeError('基准温度补偿失败')
        self.repeat_gain_comp(test_temp, centertemp, fsvip, power_range, freqpoint_dict,
                              freq_dict, productno, bip, excel_path)

    def repeat_gain_comp(self, test_temp, centertemp, fsvip, power_range, freqpoint_dict, freq_dict,
                         productno, bip, excel_path):
        '''
        温度补偿
        :return:
        '''
        key_bands = freqpoint_dict.keys()
        target = power_range[1]
        length = len(test_temp)
        centeridx = test_temp.index(centertemp)
        # 测试不同温度下补偿值
        self.logger.debug('开始温度补偿测试')
        self.rpt_message('开始温度补偿测试')
        # 温度[20,10,0,-10,-20,40,50,60,70]
        if centeridx >= 1:
            newrange = list(range(centeridx - 1, -1, -1)) + list(range(centeridx + 1, length))  # 序号[]
        else:
            newrange = list(range(centeridx + 1, length))
        self.logger.debug(newrange)
        for index, idx in enumerate(newrange):  # 按从基准温度降温到最低温度再升温度
            temp = test_temp[idx]  # 取温度
            self.logger.debug('待测温度{}'.format(temp))
            self.rpt_message('待测温度{}'.format(temp))
            tempidx = self.process_gain.read_tempidx(temp)
            # 取下一温度的tempidx
            nexttemp = None
            nexttempidx = None
            if temp < centertemp:
                nexttemp = int(temp) - 10  # 减10度，20,10,0，-10，-20，...
                self.logger.debug('下一复制温度{}'.format(nexttemp))
                nexttempidx = self.process_gain.read_tempidx(nexttemp)
            else:
                nexttemp = int(temp) + 10  # 加10度，40,50,60,70
                nexttempidx = self.process_gain.read_tempidx(nexttemp)
                self.logger.debug('下一复制温度{}'.format(nexttemp))
            if temp > 0:
                self.set_cpu_temp(temp - 1, 1, 1)  # 低于目标温度1度即可，因为运行着温度会上升
            else:
                self.set_cpu_temp(temp + 1, 1, -1)  # 低温时，最好高于目标温度1度，因为温度会下降
            # fg = self.set_temp_comp(fsvip, target, freqpoint_dict, freq_dict, tempidx, nexttempidx)
            # if not fg:
            #     raise RuntimeError('温度补偿失败')
            # self.update_bb_gain_comp(productno, bip, excel_path)
            self.logger.debug('复测{}度'.format(temp))
            power_dict = dict()  # {'B41':[power,power,power],'E':[power,power,power]}
            d1 = dict()
            try:
                self.conf_device(fsvip)
                for cellband in key_bands:
                    if 'CELL0' in cellband.upper():
                        cellid = '0'
                        self.bd.set_rf('1', 0)
                    else:
                        cellid = '1'
                        self.bd.set_rf('0', 0)
                    bandstr = cellband.split('_')[-1]
                    band = re.sub('\D', '', bandstr)  # band的数字，1/3/41/38/39
                    freq_points = freqpoint_dict[str(cellband)]
                    freqs = freq_dict[str(cellband)]
                    power_dict.setdefault(cellband, [('', '')] * len(freq_points))
                    d1.setdefault(cellband, [''] * len(freq_points))
                    for ii, freq_point in enumerate(freq_points):
                        if not freq_point:
                            continue
                        freq = freqs[ii]
                        if not self.conf_board_on_some_freq(cellid, freq_point):  # 设置基带板一类参数，并返回PCI
                            self.logger.error('设置一类参数异常')
                            continue
                        i = 0
                        while True:
                            i = i + 1
                            if i > 10:
                                self.logger.error('{}-{}温补失败'.format(temp, freq_point))
                                self.rpt_message('{}-{}温补失败'.format(temp, freq_point))
                                self.fsv.close_inst()
                                os.system('pause')
                                break

                            result = self.power_test_on_some_freq(cellid, fsvip, freq, power_range)
                            if result is None:
                                self.conf_board_on_some_freq(cellid, freq_point)
                                continue
                            if result[0]:
                                power_dict[cellband][ii] = result[1:]
                                break
                            else:
                                # if i > 7:
                                #     self.logger.error('{}-{}温补失败'.format(temp, freq_point))
                                #     self.rpt_message('{}-{}温补失败'.format(temp, freq_point))
                                #     self.fsv.close_inst()
                                #     os.system('pause')
                                #     break
                                # for test
                                currenttemp = self.bd.repeat_get_temp()  # 获取基带板温度
                                self.logger.debug('复补当前设备温度{}'.format(currenttemp))
                                self.rpt_message('复补当前设备温度{}'.format(currenttemp))
                                if abs(currenttemp - temp) >= 2:
                                    if temp > 0:
                                        self.set_cpu_temp(temp - 1, 1, 1)
                                    else:
                                        self.set_cpu_temp(temp + 1, 1, -1)
                                result = self.power_test_on_some_freq(cellid, fsvip, freq, power_range)
                                if result is None:
                                    self.conf_board_on_some_freq(cellid, freq_point)
                                    continue
                                power = result[1]  # 获取功率
                                self.logger.debug('fsv read power={}'.format(power))
                                self.rpt_message('fsv read power={}'.format(power))
                                value = float(power) - float(target)
                                # if i > 1:
                                #     value = value * 0.6
                                if abs(value)<=0.4:
                                    value=0.15 if value>0 else -0.15
                                self.logger.debug('power-target={}'.format(value))
                                self.rpt_message('power-target={}'.format(value))
                                self.process_gain.set_bandinfo(tempidx, nexttempidx, band, freq_point,
                                                               float('%6.2f' % value))
                                self.update_bb_gain_comp(productno, bip, excel_path)
                        d1[cellband][ii] = self.process_gain.read_bandinfo(tempidx, band, freq_point)

            except Exception as e:
                self.logger.error(e)
                self.rpt_message('ERROR:{}'.format(e))
            finally:
                self.fsv.close_inst()
            try:
                eid = (list(range(-20, 80, 10))).index(temp)
                if self.bdexl.open_excel(excel_path):
                    self.bdexl.write_cali(eid, **d1)
                    self.bdexl.write_power(eid, **power_dict)
            except Exception as e:
                self.logger.error(e)
            finally:
                self.bdexl.close_file()

        # 增加-30，-40度的补偿值，复制-20度的补偿值
        self.process_gain.copy_30and40()
        self.process_gain.copy_70()
        self.update_bb_gain_comp(productno, bip, excel_path)

    def update_bb_gain_comp(self, productno, bip, excel_path):
        '''
        将本地温补表更新到BB
        :return:
        '''
        self.logger.debug('update_bb_gain_comp')
        i = 0
        while 1:
            if i > 3:
                raise RuntimeError('补偿文件异常')
            try:
                if self.bd.remove_gain_comp_json():  # 删除原gaincomp.json文件
                    if self.write_gain_comp_json(productno, bip, excel_path):  # 写文件并上传
                        self.bd.refresh_comp()  # 刷新
                        break
                    else:
                        self.reset_bd()
                        time.sleep(3)
                i = i + 1
            except Exception as e:
                self.reset_bd()
                i = i + 1

    def update_bb_flat_comp(self, productno, bip, excel_path):
        self.logger.debug('update_bb_flat_comp')
        i = 0
        while 1:
            if i > 3:
                raise RuntimeError('补偿文件异常')
            try:
                if self.bd.remove_flat_comp_json():  # 删除原gaincomp.json文件
                    if self.write_flat_comp_json(productno, bip, excel_path):  # 写文件并上传
                        self.bd.refresh_comp()  # 刷新
                        break
                    else:
                        self.reset_bd()
                        time.sleep(3)
                i = i + 1
            except Exception as e:
                self.reset_bd()
                i = i + 1

    def init_flat_and_gain_comp(self, productno, freqpoint_dict, test_temp, centertemp, bip, excel_path):
        '''
        初始化温补，频补表到内存
        :return:
        '''
        ret = self.bd.read_flat_and_gain_json(productno)
        if ret is None:
            self.process_flat.init_flat_comp(freqpoint_dict, test_temp, centertemp)
            self.process_gain.init_gain_comp(freqpoint_dict, test_temp)
            self.update_bb_flat_comp(productno, bip, excel_path)
            self.update_bb_gain_comp(productno, bip, excel_path)
        else:
            fj, gj = ret
            if fj is None:
                self.process_flat.init_flat_comp(freqpoint_dict, test_temp, centertemp)
                self.update_bb_flat_comp(productno, bip, excel_path)
            else:
                self.process_flat.init_comp_from_file(fj)
            if gj is None:
                self.process_gain.init_gain_comp(freqpoint_dict, test_temp)
                self.update_bb_gain_comp(productno, bip, excel_path)
            else:
                self.process_gain.init_comp_from_file(gj)

    def repeat_flat_comp(self, centertemp, fsvip, freqpoint_dict, freq_dict, power_range, productno, bip, excel_path):
        '''
        多次平坦度补偿，直到达标
        :return:
        '''
        target = float(power_range[1])
        lower = float(power_range[0])  # 下限
        upper = float(power_range[2])  # 上限
        freq_keys = freqpoint_dict.keys()
        freq_values = freqpoint_dict.values()
        tempidx = list(range(-20, 80, 10)).index(centertemp)
        # self.set_flat_comp(fsvip, target, freqpoint_dict, freq_dict, productno, bip, excel_path)
        # 基准温度下温补默认为0
        temp_cali_dict = dict(zip(freq_keys, [[0] * len(list(freq_values)[0])] * len(freq_keys)))
        power_dict = dict()  # {'B41':[power,power,power],'E':[power,power,power]}
        try:
            self.conf_device(fsvip)
            for cellband in freq_keys:
                self.logger.debug('cellband={}'.format(cellband))
                self.rpt_message('cellband={}'.format(cellband))
                if 'CELL0' in cellband.upper():
                    cellid = '0'
                    self.bd.set_rf('1', 0)
                else:
                    cellid = '1'
                    self.bd.set_rf('0', 0)
                bandstr = cellband.split('_')[-1]
                band = re.sub('\D', '', bandstr)  # band的数字，1/3/41/38/39
                freq_points = freqpoint_dict[str(cellband)]
                freqs = freq_dict[str(cellband)]
                power_dict.setdefault(cellband, [('', '')] * len(freq_points))
                for idx, point in enumerate(freq_points):
                    freq = freqs[idx]
                    self.conf_board_on_some_freq(cellid, point)  # 设置基带板频点
                    i = 0
                    while 1:
                        i = i + 1
                        if i > 9:
                            return False
                        # 复测
                        # for test
                        plst = self.get_fsv_power(fsvip, target, freq)
                        if plst is None:
                            time.sleep(10)
                            continue
                        power = float(plst)  # 读取频谱仪功率
                        if lower <= power <= upper:
                            power_dict[cellband][idx] = power, 'PASS'
                            break
                        power_dict[cellband][idx] = power, 'FAIL'
                        delta = power - target
                        if abs(delta)<=0.4:
                            delta=0.15 if delta>0 else -0.15
                        self.logger.debug('flat delta={}'.format(delta))
                        cali = float('%.2f' % delta)
                        self.process_flat.set_bandinfo(band, point, cali)
                        # 更新设备频补补偿表
                        self.update_bb_flat_comp(productno, bip, excel_path)
            else:
                return True
        except Exception as e:
            self.logger.error(e)
        finally:
            self.fsv.close_inst()
            try:
                if self.bdexl.open_excel(excel_path):
                    self.bdexl.write_power(tempidx, **power_dict)
                    self.bdexl.write_cali(tempidx, **temp_cali_dict)
            except Exception:
                pass
            finally:
                self.bdexl.close_file()

    def power_test_on_some_freq(self, cellid, fsvip, freq, power_range):
        '''
        freq:频率
        power_range:功率标准[下限，理想值,上限，]
        :return:
        '''
        lower = float(power_range[0])  # 下限
        upper = float(power_range[2])  # 上限
        # for test
        plst = self.get_fsv_power(fsvip, float(power_range[1]), freq)
        if plst is None:
            return None
        power = float(plst)  # 读取频谱仪功率
        # txatt = self.bd.read_txatt(cellid)
        if power >= lower and power <= upper:
            return True, power, 'PASS'
        elif power > upper:
            # self.bd.set_rf(cellid, 0)  # 关闭射频
            self.logger.error('功率{}超限'.format(power))
        else:
            # self.bd.set_rf(cellid, 0)  # 关闭射频
            self.logger.error('功率{}不达标'.format(power))
        return False, power, 'FAIL'

    def conf_board_on_some_freq(self, cellid, freq):
        '''
        基于某频点

        freq:频点
        :return:
        '''
        self.logger.debug('conf_board_on_some_freq')
        try:
            flag = self.bd.conf_para(cellid, freq)  # 设置频点并打开功放
            return flag
        except Exception as e:
            self.logger.error(e)
            return False

    def get_and_send_powercali(self, cellid, fsvip, band, freq_points, freqs, target):
        '''
        遍历band的三个频点，得到功率补偿，发送给BB
        band:
        freq_points:频点，用于发给基带板
        freqs:频率,用于设置频谱仪
        target:功率理想值dBm
        return [[int(freq), float(cali),温度],,]
        '''
        temp = self.bd.repeat_get_temp()  # 获取基带板温度
        if temp is None:
            raise IOError('get temp failed')
        self.logger.debug('current temp={}'.format(temp))
        for idx, point in enumerate(freq_points):
            freq = freqs[idx]
            self.conf_board_on_some_freq(cellid, point)  # 设置基带板频点
            plst = self.get_fsv_power(fsvip, target, freq)

            if plst is None:
                raise IOError('read fsv power failed')
            power = plst
            self.logger.debug('fsv read power={}'.format(power))
            value = float(power) - float(target)
            cali = float('%.2f' % value)
            self.process_flat.set_bandinfo(band, point, cali)  # 更新内存

    def get_fsv_power(self, fsvip, upper, freq):
        '''
        读取频谱仪功率
        upper:输出功率上限，用来设置ref level,ref level=upper+3
        :return:
        '''
        i = 0
        ref_level = float(upper) + 7
        lowedge = float(upper) - 21 - 4
        while 1:
            try:
                if i >= 3:
                    return None
                i = i + 1
                self.fsv.set_for_txatt(ref_level, freq)
                time.sleep(1)
                plst = []
                j = 0
                # sweep time 1s,读5次取平均值
                # 12.23 频谱仪读平均值5次
                while j < 1:
                    power = self.fsv.get_power(ref_level, freq)  # 读取频谱仪功率,返回列表
                    self.logger.debug('get_fsv_power={}'.format(power[0]))
                    if power is not None:
                        # plst.append(power)
                        # for test
                        if float(power[0]) > lowedge:
                            plst.append(power)
                        else:
                            self.logger.error('before reset_bd,power={}'.format(power[0]))
                            self.reset_bd()  # 可能设备重启了，导致输出-19以下
                            return None
                    else:
                        break
                    j = j + 1
                if plst:
                    plst = [float(item[0]) for item in plst]
                    self.logger.debug('power list={}'.format(plst))
                    return sum(plst) / len(plst)
                time.sleep(3)
            except Exception as e:
                self.logger.error(e)
                time.sleep(3)
                self.fsv.close_inst()
                self.conf_device(fsvip)
                time.sleep(3)
                continue

    def reset_bd(self):
        if not self.bd.do_set_bd():
            raise RuntimeError('强建小区失败')

    def read_excel_txatt_norm(self, excel_path):
        '''
        读取excel的上下行功率，频点等参数
        :param excel_path:
        :return:
        '''
        try:
            if self.bdexl.open_excel(excel_path):
                normlist = self.bdexl.get_txatt_norm()  # 读取输出功率标准
                templist = self.bdexl.read_cpu_temp()  # 读取一系列待测温度
                centertemp = self.bdexl.read_cpu_center_temp()  # 读取基准温度

                return normlist, templist, centertemp
        except Exception as e:
            raise RuntimeError(e)
        finally:
            self.bdexl.close_file()

    def read_boardtype(self, excel_path):
        '''
        从excel中读取board类型及主从片频点，频率
        :param excel_path:
        :return:
        '''
        try:
            if self.bdexl.open_excel(excel_path):
                freqpoint_dict, freq_dict = self.bdexl.get_set_condition()
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

    def conf_device(self, fsvip):
        '''
        仪器初始化
        :return:
        '''
        self.logger.debug('conf_fsv')
        # for test
        i = 0
        while 1:
            i = i + 1
            if i >= 3:
                self.logger.error('fsv error')
                raise RuntimeError('fsv error')
            try:
                self.fsv.init_inst(fsvip)
                time.sleep(1)
                self.fsv.reset_fsv()
                time.sleep(1)
            except Exception as e:
                self.logger.error(e)
                time.sleep(10)
                self.fsv.close_inst()
            else:
                break

    def set_flat_comp(self, fsvip, target, freqpoint_dict, freq_dict, productno, bip, excel_path):
        '''
        平坦度补偿
        :return:
        '''
        try:
            self.logger.debug('基准平坦度补偿')
            key_bands = freqpoint_dict.keys()
            self.conf_device(fsvip)

            for cellband in key_bands:
                self.logger.debug('cellband={}'.format(cellband))
                if 'CELL0' in cellband.upper():
                    cellid = '0'
                    self.bd.set_rf('1', 0)
                else:
                    cellid = '1'
                    self.bd.set_rf('0', 0)
                bandstr = cellband.split('_')[-1]
                band = re.sub('\D', '', bandstr)  # band的数字，1/3/41/38/39
                freq_points = freqpoint_dict[str(cellband)]
                freqs = freq_dict[str(cellband)]

                self.get_and_send_powercali(cellid, fsvip, band, freq_points, freqs,
                                            target)  # 写平坦度补偿表
            # 更新设备频补补偿表
            self.update_bb_flat_comp(productno, bip, excel_path)
        except Exception as e:
            self.logger.error(e)
            raise RuntimeError(e)
        finally:
            self.fsv.close_inst()

    def set_temp_comp(self, fsvip, target, freqpoint_dict, freq_dict, tempidx, nexttempidx):
        '''
        温度补偿

        :return:补偿值{'':[],'':[]}
        '''
        i = 0
        while 1:
            if i > 3:
                return False
            try:
                key_bands = freqpoint_dict.keys()

                self.conf_device(fsvip)
                for cellband in key_bands:
                    self.logger.debug('cellband={}'.format(cellband))
                    if 'CELL0' in cellband.upper():
                        cellid = '0'
                        self.bd.set_rf('1', 0)
                    else:
                        cellid = '1'
                        self.bd.set_rf('0', 0)
                    bandstr = cellband.split('_')[-1]
                    band = re.sub('\D', '', bandstr)  # band的数字，1/3/41/38/39
                    # bandinfo=self.process_gain.read_bandinfo(int(band))
                    freq_points = freqpoint_dict[str(cellband)]
                    freqs = freq_dict[str(cellband)]
                    for idx, point in enumerate(freq_points):
                        freq = freqs[idx]
                        self.conf_board_on_some_freq(cellid, point)  # 设置基带板频点
                        # for test
                        plst = self.get_fsv_power(fsvip, target, freq)
                        if plst is None:
                            raise IOError('read fsv power failed')
                        power = plst
                        self.logger.debug('fsv read power={}'.format(power))
                        value = float(power) - float(target)
                        self.process_gain.set_bandinfo(tempidx, nexttempidx, band, point, float('%6.2f' % value))
                return True
            except Exception as e:
                self.logger.error(e)
                i = i + 1
            finally:
                self.fsv.close_inst()

    def set_cpu_temp(self, target, bias, direction):
        '''
        设定设备到达某温度
        target:温度
        bias:偏离目标温度多少度

        :return:
        '''
        # for test
        # logger.debug('wait for test...')
        # time.sleep(10)
        self.logger.debug('温度设定目标{}'.format(target))
        self.rpt_message('温度设定目标{}'.format(target))
        # time.sleep(3)
        # for test
        if not self.adjust_thread or not self.adjust_thread.is_alive():
            self.adjust_thread = PropagatingThread(target=self.adjust_cpu_temp, args=(target, bias, direction))
            self.adjust_evt.set()
            self.adjust_thread.setDaemon(True)
            self.adjust_thread.start()

            self.adjust_thread.join()

    def write_gain_comp_json(self, productno, bip, excel_path):
        '''
        写文件并ftp上传给T2K
        :return:
        '''
        myftp = MyFTP(str(bip))
        try:
            js = self.process_gain.get_json()
            dirname = os.path.dirname(excel_path)
            pno = productno

            remote_file = '/mnt/flash/scbs/{}_GainComp.json'.format(pno)
            local_file = os.path.join(dirname, 'GainComp.json')
            with open(local_file, 'wb') as f:
                f.write(json.dumps(js, indent=4, ensure_ascii=False).encode('utf-8'))
            if myftp.rpt_json(local_file, remote_file):
                return True
        except Exception as e:
            self.logger.error('write_gain_comp_json ERROR:{}'.format(e))
            return False
        finally:
            myftp.close()

    def write_flat_comp_json(self, productno, bip, excel_path):
        '''
        将本地频补表上传给BB
        :param productno:
        :param bip:
        :param excel_path:
        :return:
        '''
        myftp = MyFTP(str(bip))
        try:
            js = self.process_flat.get_json()
            dirname = os.path.dirname(excel_path)
            pno = productno

            remote_file = '/mnt/flash/scbs/{}_FlatComp.json'.format(pno)
            local_file = os.path.join(dirname, 'FlatComp.json')
            with open(local_file, 'wb') as f:
                f.write(json.dumps(js, indent=4, ensure_ascii=False).encode('utf-8'))
            if myftp.rpt_json(local_file, remote_file):
                return True
        except Exception as e:
            self.logger.error('write_flat_comp_json ERROR:{}'.format(e))
            return False
        finally:
            myftp.close()

    def check_cpu_temp(self):
        '''
        读取设备温度
        :return:
        '''
        a, b, c, d, e = [-100] * 5
        i = 0
        MAX = 90
        while True:
            if i > MAX:
                break
            if self.wait_evt.is_set():
                temp = self.bd.repeat_get_temp()  # 获取基带板温度
                self.logger.debug('current cpu temp={}'.format(temp))
                self.rpt_message('current cpu temp={}'.format(temp))
                if temp is None:
                    i = i + 1
                    continue
                f = temp
                a, b, c, d, e = b, c, d, e, f
                if a == e or abs(a - e) <= 1:
                    self.logger.debug('cpu hit {}'.format(e))
                    self.rpt_message('cpu hit {}'.format(e))
                    self.wait_evt.clear()
                    # self.adjust_flag = True
                    self.adjust_evt.set()
                else:
                    time.sleep(50)
            else:
                self.logger.debug('wait evt')
                self.wait_evt.wait()
                i = 0
                a, b, c, d, e = [-100] * 5

            i = i + 1

    def adjust_cpu_temp(self, target, bias, direction=1):
        '''

        :param target:
        :param bias:
        :param direction: 1,表示目标温度为正，-1表示目标温度为负或0
        :return:
        '''
        x = 0.7
        y = 0.4
        z = 0.7
        i = 0
        period = 1
        oldt = None
        if bias == 0:
            trg = [0, 0]
        else:
            if direction > 0:
                trg = [-2, 0]
            else:
                trg = [0, 2]
        while True:
            Tset = self.th_dev.get_temp_pv() / 10.0  # 温箱温度
            self.logger.debug('th temp={}'.format(Tset))
            self.logger.debug('last th setvalue={}'.format(oldt))
            if oldt is not None and abs(Tset - oldt) >= 0.3:
                time.sleep(30)
                self.logger.debug('wait th-dev hit setvalue')
                continue
            if oldt is not None and self.adjust_evt.is_set():
                self.wait_evt.set()
                self.adjust_evt.clear()
            self.logger.debug('wait adjust_evt')
            self.adjust_evt.wait()
            try:
                if self.adjust_evt.is_set():
                    Tact = self.bd.repeat_get_temp()  # 获取基带板温度
                    self.logger.debug('cpu temp={}'.format(Tact))
                    self.rpt_message('cpu temp={}'.format(Tact))
                    if Tact is None:
                        raise IOError('get temp failed')
                    delta = float(target) - float(Tact)
                    self.logger.debug('temp delta={}'.format(delta))

                    if trg[0] <= delta <= trg[1]:
                        i += 1
                        time.sleep(30)
                    elif abs(delta) >= 10:
                        i = 0
                        T = Tset + delta * x
                        oldt = T
                        self.logger.debug('SET T={}'.format(T))
                        self.th_dev.set_temp_sv(int(T * 10))
                        time.sleep(60 * 10)
                    elif abs(delta) >= 3:
                        i = 0
                        T = Tset + delta * y
                        oldt = T
                        self.logger.debug('SET T={}'.format(T))
                        self.th_dev.set_temp_sv(int(T * 10))
                        time.sleep(60 * int(period))
                    else:
                        i = 0
                        if delta > 0:
                            T = Tset + z
                        else:
                            T = Tset - z
                        oldt = T
                        self.th_dev.set_temp_sv(int(T * 10))
                        time.sleep(30 * 1)  # 1分钟
                    if i >= 1:
                        self.logger.debug('hit target')
                        break
            except Exception as e:
                self.logger.error(e)
                self.reset_bd()
