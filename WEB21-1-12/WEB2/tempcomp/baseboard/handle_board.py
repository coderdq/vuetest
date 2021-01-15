'''
调试基带板
'''

import logging
import copy
import time
import os
from abc import abstractmethod

from telnet.client import Ctrl_8125, Ctrl_T2K

logger = logging.getLogger('ghost')


class BoardHandler(object):
    type_dict = {'8125': Ctrl_8125, 'T2K': Ctrl_T2K}
    process_dict = {'8125': ['MGR.EXE', 'Product_lte'], 'T2K': ['PLAT.EXE', 'APP_lte']}

    def __init__(self, type, **kwargs):
        self.config = kwargs
        # self.cellid = str(self.config.get('CELL', '0'))
        if str(type) in BoardHandler.type_dict.keys():
            self.bd = BoardHandler.type_dict[str(type)]()
            self.process_name = BoardHandler.process_dict[str(type)]
        else:
            raise ValueError('board type does not exist')

    def login(self):
        '''
        telnet连接
        :return: 
        '''

        interval = 20
        ip = self.config.get('IP', '')
        if not ip:
            raise ValueError('ip input error')
        i = 0
        while True:
            ret = self.bd.login_host(ip)
            if ret:
                break
            if i >= 30:
                raise IOError('board is not online')
            i = i + 1
            time.sleep(interval)
        return True

    @abstractmethod
    def login_board(self):
        pass

    def login_band(self, subip, cellid='0'):
        '''
        登录基带板
        :return:
        '''

        interval = 10
        i = 0
        ret = False
        telnet_subip_flag = False
        while True:
            if str(cellid) == '0':
                logger.debug('login cell 0')
                ret = self.bd.login_baseboard()
            elif str(cellid) == '1':
                if subip:
                    logger.debug('waiting for cell 1...')
                    if not telnet_subip_flag:
                        telnet_subip_flag = self.bd.telnet_board(subip)  # 登录8125的从片
                    if telnet_subip_flag:
                        time.sleep(5)
                        logger.info('login cell1')
                        ret = self.bd.login_baseboard()
                else:
                    ret = self.bd.login_baseboard()
            if ret:
                break
            if i >= 30:
                self.bd.execute_some_command('reboot')
                raise IOError('board is not online')
            i = i + 1
            time.sleep(interval)
        return True

    def run_process(self):
        '''
        使能进程
        :return:
        '''
        process_name = self.process_name
        i = 0
        while 1:
            process_ids = self.bd.check_ps(*process_name)
            # pad 进程
            self.bd.pad_process(*process_ids)
            if process_ids:
                break
            i = i + 1
            if i > 10:
                raise IOError('ps no content!!')
            time.sleep(10)

    def conf_band(self, *args):
        try:
            cellid, workmode, funid = args
            result = '0'
            if self.login():  # 连接板子
                time.sleep(2)
                result = self.set_band(cellid, workmode, funid)
                logger.debug('set_mode result={}'.format(result))
                if result == '0':  # 不用修改
                    logger.info('mode不用修改')
                    return True
                elif result == '1':  # 修改成功
                    time.sleep(5)
                    logger.debug('begin to reboot...')
                    time.sleep(10)
                    logger.info('mode修改成功，将自动重启')
                    return True
                else:  # 修改失败
                    logger.info('mode修改失败')
                    return False
        except Exception as e:
            logger.error('{}'.format(e))
            return False

    def repeat_conf_frameoffset(self, cellid):
        i = 0

        while 1:
            if cellid == '0':
                if self.check_frameoffset(cellid):
                    return True
            if self.conf_frameoffset(cellid):
                if self.check_frameoffset(cellid):
                    return True
            i = i + 1
            time.sleep(2)
            if i > 3:
                return False

    def conf_frameoffset(self, cellid):
        try:
            if self.login():
                result = self.reset_frameoffset(cellid)
                logger.debug('reset_frameoffset result={}'.format(result))
                if result == '0':
                    logger.info('帧偏移不用修改')
                    return True
                elif result == '1':  # 修改成功
                    time.sleep(5)
                    logger.debug('begin to reboot...')
                    time.sleep(10)
                    logger.info('帧偏移已关闭，将自动重启')
                    return True
                else:
                    logger.info('帧偏移修改失败')
                    return False
        except Exception as e:
            logger.error('{}'.format(e))
            return False

    def check_frameoffset(self, cellid):
        '''
        检查frameoffset是否修改成功，读取文件获得frameoffset
        :return:
        '''
        i = 0

        try:
            while 1:
                i = i + 1
                if i > 3:
                    return False
                if self.login():
                    if not self.login_board():  # 登录板子
                        continue
                    self.run_process()  # pad 进程
                    value = self.get_frameoffset(cellid)
                    logger.debug('get frameoffset={}'.format(value))
                    if value is None:
                        continue
                    if str(value) == '0':
                        logger.debug('帧偏移已为0')
                        return True
                    else:
                        return False

        except Exception as e:
            logger.error('{}'.format(e))
            return False

    def repeat_conf_switch(self, cellid):
        i = 0
        while 1:
            if self.conf_switch(cellid):
                logger.info('conf_switch ok')
                return True
            i = i + 1
            time.sleep(5)
            if i > 3:
                return False

    def conf_switch(self, cellid):
        try:
            if self.login():
                result = self.reset_antiswitch(cellid)
                logger.debug('reset_antiswitch result={}'.format(result))
                if result == '0':
                    logger.info('降干扰/温补,频补开关不用修改')
                    return True
                elif result == '1':  # 修改成功
                    time.sleep(5)
                    logger.debug('begin to reboot...')
                    time.sleep(10)
                    logger.info('降干扰/温补,频补开关已关闭，将重启')
                    return True
                else:
                    logger.info('降干扰/温补,频补开关修改失败')
                    return False
        except Exception as e:
            logger.error('{}'.format(e))
            return False

    @abstractmethod
    def get_frameoffset(self, cellid):
        pass

    @abstractmethod
    def set_clocksrc(self):
        pass

    @abstractmethod
    def set_band_on_TDD(self, *args):
        '''
        设置要求的band，只在8125主片或T2K载波0设置TDD，TDD测试顺序：B41,E,F
        :return:'0'--band不用修改  '1':修改成功  '2'：修改失败
        '''
        pass

    @abstractmethod
    def set_band_on_FDD(self, *args):
        pass

    def set_band(self, *args):
        try:
            cellid, workmode, funid = args
            logger.debug('workmode={},funid={}'.format(workmode, funid))

            result = '0'
            if cellid == '0':
                result = self.set_band_on_TDD(workmode, funid)
            elif cellid == '1':
                result = self.set_band_on_FDD(workmode, funid)
            return result
        except Exception as e:
            raise ValueError('set_band error:{}'.format(e))

    @abstractmethod
    def conf_class1_para(self, cellid, freq):
        '''
        基于某band下读取一类参数并设置频点
        :return:
        '''
        pass

    @abstractmethod
    def query_class1_para(self, *args):
        pass

    @abstractmethod
    def read_txatt(self, cellid):
        '''
        因为有时读取失败，所以多次读取尝试
        :return:
        '''
        pass

    @abstractmethod
    def set_txatt(self, cellid, txatt):
        pass

    def check_cell_state(self, cellid):
        '''
        检查GPS是否同步
        :return:
        '''
        i = 0
        flag = False
        while 1:
            i = i + 1
            if i >= 3:
                return flag
            if self.login():
                if not self.login_board():  # 登录板子
                    continue
                self.run_process()  # pad 进程
                self.bd.set_gpsmode()  # 不设置这个会导致GPS无法同步
                flag = self.bd.repeat_check_cell_state(cellid)  # 查看小区状态
                if not flag:
                    continue
                return flag

    def reconnect_board(self):
        if self.login():
            logger.info('begin to pad board..')
            if self.login_board():  # 登录板子
                time.sleep(1)
                self.run_process()  # pad 进程
                return True
            return False
        return False

    @abstractmethod
    def reset_frameoffset(self, cellid):
        pass

    @abstractmethod
    def reset_antiswitch(self, cellid):
        pass

    @abstractmethod
    def set_rf(self, cellid, onoff):
        pass

    def check_enter(self):
        '''
        检查是否能输入命令
        :return:
        '''
        self.bd.execute_enter()

    @abstractmethod
    def check_bandinfo(self, cellid):
        pass

    @abstractmethod
    def conf_board_txatt(self, *args):
        '''
        type:str
        cellid:str
        初始化txatt为初始默认值
        :return:int
        '''
        pass

    @abstractmethod
    def add_route(self, *args):
        pass

    @abstractmethod
    def get_temp(self):
        pass

    def check_route(self, cellid):
        '''
        从片配置路由
        :param pcip:
        :return:
        '''
        try:
            subip = self.config.get('SUBIP', '')
            pcip = str(self.config.get('PCIP', ''))  # 电脑的IP,用于8125从片配置路由
            i = 0
            while 1:
                if self.login():

                    if cellid == '0':
                        break
                    if self.bd.telnet_board(subip):
                        return self.add_route(pcip)
                i = i + 1
                if i > 10:
                    return False
                time.sleep(30)
            logger.debug('check route ok.')
            return True
        except Exception as e:
            logger.error('check_route error:{}'.format(e))
            return False

    def repeat_conf_clocksrc(self):
        i = 0
        while 1:
            if self.conf_clocksrc():
                logger.info('conf_clocksrc ok')
                return True

            i = i + 1
            time.sleep(5)
            if i > 3:
                return False

    def conf_clocksrc(self):
        try:
            if self.login():
                result = self.set_clocksrc()
                logger.debug('set_clocksrc result={}'.format(result))
                if result == '0':
                    logger.info('时钟源是GPS,不用修改')
                    return True
                elif result == '1':  # 修改成功
                    time.sleep(5)
                    logger.debug('begin to reboot...')
                    time.sleep(10)
                    logger.info('时钟源设置成GPS，将重启')
                    return True
                else:
                    logger.info('时钟源设置GPS失败')
                    return False
        except Exception as e:
            logger.error('{}'.format(e))
            return False

    def conf_para(self, cellid, freq):
        '''
        设置一类参数后等待小区建立
        :return:
        '''
        i = 0
        flag = False

        while 1:
            try:
                if i > 3:
                    return flag
                if self.login():
                    if not self.login_board():  # 登录板子
                        i = i + 1
                        continue
                    self.run_process()  # pad 进程
                    self.conf_class1_para(cellid, freq)  # 设置一类参数，返回PCI
                    time.sleep(1)
                    flag = self.bd.repeat_check_cell_state(cellid)
                    if flag:
                        return flag
                i = i + 1
            except Exception as e:
                logger.error(e)
                i = i + 1

    def send_powercali(self, cali_list):
        '''
        发送功率补偿值
        :return:
        '''
        i = 0
        flag = False
        while 1:
            i = i + 1
            if i >= 3:
                return flag
            if self.login():
                if not self.login_board():  # 登录板子
                    continue
                self.run_process()  # pad 进程
                for cali in cali_list:
                    self.bd.send_powercali(*cali)
                self.bd.send_debug_tempfreq()  # 刷新
                return True

    def kill_arm_process(self):
        i = 0
        flag = False
        while 1:
            if i > 3:
                return flag
            if self.login():
                flag = self.bd.kill_arm()
                if flag:
                    return flag
            i = i + 1
            time.sleep(3)

    def check_clock_src(self):
        i = 0
        while 1:
            if i > 3:
                logger.debug('check clock src failed')
                return False
            if self.login():
                if not self.login_board():  # 登录板子
                    i = i + 1
                    continue
                self.run_process()  # pad 进程
                src = self.bd.get_clock_src()
                if src is not None:
                    if int(src) == 2:
                        logger.debug('clock src is gps')
                        return True
                    else:
                        logger.debug('clock src not gps')
                        return False
            i = i + 1
            time.sleep(5)

    def check_temp(self):
        '''
        判断热稳定,30分钟内达到稳定
        :return:
        '''
        i = 0
        j = 0
        MAX = 30
        a, b, c, d, e = 0, 0, 0, 0, 0
        while 1:
            if i > MAX:
                logger.error('无法达到热稳定')
                return None
            i = i + 1
            temp = self.get_temp()
            if temp is None:
                return None
            logger.debug('temp={}'.format(temp))
            f = temp
            j = j + 1
            a, b, c, d, e = b, c, d, e, f
            # for test
            if j >= 1:
                if a == e or abs(a - e) <= 1:
                    return e
            # for test
            time.sleep(1)

    def repeat_check_temp(self):
        '''
        检查是否达到热稳定
        :return:
        '''
        i = 0
        while 1:
            i = i + 1
            if i > 3:
                return None
            if self.login():
                if not self.login_board():
                    continue
                self.run_process()  # pad 进程
                logger.debug('start check temp...')
                temp = self.check_temp()
                if temp is not None:
                    return temp  # 返回温度
            time.sleep(2)

    def repeat_get_temp(self):
        '''
        读取温度
        :return:
        '''
        i = 0
        while 1:
            try:
                i = i + 1
                if i > 3:
                    return None
                if self.login():
                    if not self.login_board():
                        continue
                    self.run_process()  # pad 进程
                    temp = self.get_temp()
                    if temp is not None:
                        return temp  # 返回温度
                time.sleep(10)
            except Exception as e:
                logger.error(e)

    def reboot(self):
        i = 0
        flag = False
        while 1:
            if i > 3:
                return flag
            if self.login():
                self.bd.execute_some_command('reboot')
                logger.debug('reboot')
                time.sleep(10)
                return True
            i = i + 1

    def remove_gain_comp_json(self):
        i = 0
        flag = False
        while 1:
            if i > 3:
                return flag
            if self.login():
                self.bd.remove_gain_json()
                return True
            i = i + 1

    def remove_flat_comp_json(self):
        i = 0
        flag = False
        while 1:
            if i > 3:
                return flag
            if self.login():
                self.bd.remove_flat_json()
                return True
            i = i + 1

    def set_gps_mode(self):
        '''
        kill arm程序并设置gps mode
        :return:
        '''
        logger.debug('set_gps_mode')
        i = 0
        while 1:
            try:
                i = i + 1
                if i >= 3:
                    logger.debug('set_gps_mode failed')
                    return False
                if self.login():
                    if not self.login_board():  # 登录板子
                        continue
                    self.run_process()  # pad 进程
                    self.bd.set_gpsmode()
                    if not self.bd.kill_arm():
                        continue
                    return True
                time.sleep(5)
            except Exception as e:
                logger.error(e)
                continue

    def start_arm_process(self):
        '''
        启动ARM进程
        :return:
        '''
        logger.debug('start_arm_process')
        i = 0
        while 1:
            i = i + 1
            if i >= 3:
                logger.debug('start_arm_process failed')
                return False
            if self.login():
                self.bd.start_run_arm()
                return True
            time.sleep(5)

    def do_compensation(self, cellid):
        '''
        功率补偿
        :return:
        '''
        i = 0
        flag = False
        while 1:
            i = i + 1
            if i >= 3:
                return flag
            if self.login():
                # if cellid == '0':
                #     self.bd.remove_flat_json()  # 删除平坦度补偿表
                #     self.bd.remove_gain_json()  # 删除温补表
                time.sleep(.1)
                if not self.login_board():  # 登录板子
                    continue
                self.run_process()  # pad 进程
                time.sleep(.1)
                self.bd.start_ftp()  # 开启ftp服务
                break
        return True

    def refresh_comp(self):
        i = 0
        flag = False
        while 1:
            i = i + 1
            if i >= 3:
                return flag
            if self.login():
                if not self.login_board():  # 登录板子
                    continue
                self.run_process()  # pad 进程
                self.bd.send_debug_tempfreq()  # 刷新
                break
        return True

    def switch_reboot(self):
        i = 0
        flag = False
        while 1:
            i = i + 1
            if i >= 3:
                return flag
            if self.login():
                if not self.login_board():  # 登录板子
                    continue
                self.run_process()  # pad 进程
                self.bd.switch_reboot_flag(1)
                break
        return True

    def test_sniffer(self, cellid):
        '''
        测试下行接收sniffer,测试sniffer要等GPS同步上，除非是强建小区
        :return:
        '''
        logger.debug('test_sniffer')
        i = 0
        while 1:
            i = i + 1
            if i >= 5:
                logger.debug('test_sniffer failed')
                return None
            if self.login():
                if cellid == '0':
                    self.bd.remove_flat_json()  # 删除平坦度补偿表
                if not self.login_board():  # 登录板子
                    continue
                self.run_process()  # pad 进程
                flag = self.bd.repeat_check_cell_state('0')
                if not flag:
                    continue
                ret = self.bd.set_airsync_para(39150)
                if ret is not None:
                    return ret
            time.sleep(5)

    def read_bb_sn(self):
        '''
        读取BB版本和序列号,物料号
        :return:
        '''
        logger.debug('read_bb_sn')
        i = 0
        while 1:
            i = i + 1
            if i >= 3:
                logger.debug('read_bb_sn failed')
                return None
            if self.login():
                logger.debug('read productno')
                pncode = self.bd.get_productno()  # 获取物料号
                if pncode is None:
                    return None
                # if not self.login_board():  # 登录板子
                #     continue
                #
                # self.run_process()  # pad 进程
                sn = self.bd.get_macaddr()
                logger.debug('sn={}'.format(sn))
                if sn is None:
                    continue
                bbver = self.bd.get_bbver()
                if bbver is None:
                    continue
                return bbver, sn, pncode
            time.sleep(5)

    def do_set_bd(self):
        '''
        设置基带板强建小区
        :return:
        '''
        i = 0
        flag = False
        while 1:
            i = i + 1
            if i >= 3:
                return flag
            if self.login():
                f1 = self.bd.kill_arm()  # 杀掉arm程序
                if not f1:
                    continue
                if not self.login_board():  # 登录板子
                    continue
                self.run_process()  # pad 进程
                self.bd.set_pwrbackoff_switch()  # 关闭70度之后的功率保护
                self.bd.switch_reboot_flag(0)
                self.bd.enb_cell()  # 强建小区
                time.sleep(3)
                self.bd.start_ftp()  # 开启ftp服务
                return True

    def read_flat_and_gain_json(self, productno):
        '''
        读取频补表，温补表内容到内存
        :param productno:
        :return:
        '''
        i = 0
        ret = None
        while True:
            i = i + 1
            if i > 3:
                return ret
            if self.login():
                flat_file = '{}_FlatComp.json'.format(productno)
                gain_file = '{}_GainComp.json'.format(productno)
                flat_json = self.bd.read_gain_json(flat_file)
                gain_json = self.bd.read_gain_json(gain_file)
                return flat_json, gain_json


class B8125Handler(BoardHandler):

    def __init__(self, **kwargs):
        type = '8125'
        super(B8125Handler, self).__init__(type, **kwargs)

    def login_board(self, cellid=None):
        try:
            self.check_enter()

            # ip = self.config.get('IP')
            subip = self.config.get('SUBIP', '')  # T2K没有SUBIP字段
            flag = self.login_band(subip, cellid)
            return flag
        except Exception as e:
            logger.error(e)
            return False

    def set_band_on_TDD(self, workmode, funid):
        '''
        设置要求的band，只在8125主片或T2K载波0设置TDD，TDD测试顺序：B41,E,F
        :return:'0'--band不用修改  '1':修改成功  '2'：修改失败
        '''
        # stages=['5','0','2'] #b41,e,f的主片funid
        # state=0

        # masterWorkMode, masterFunId = self.check_bandinfo()
        # logger.debug('now master workmode,funid={},{}'.format(masterWorkMode, masterFunId))
        # if masterWorkMode == str(workmode) and str(masterFunId) == str(funid):
        #     return '0'
        # else:
        if self.login_board():
            self.run_process()  # 起进程
            mode_set = [workmode, '1', funid, '3']  # 从片b1
            if self.bd.set_mode(*mode_set):  # 设置主片
                return '1'
            # logger.debug('set new mode={}'.format(mode_set))
        return '2'

    def set_band_on_FDD(self, workmode, funid):
        # slaveWorkMode, slaveFunId = self.check_bandinfo()
        # logger.debug('now slave workmode,funid={},{}'.format(slaveWorkMode, slaveFunId))
        # if slaveWorkMode == str(workmode) and str(slaveFunId) == str(funid):
        #     return '0'
        # else:
        if self.login_board(cellid=0):  # 设置从片MODE也在主片中设置
            self.run_process()  # 起进程
            mode_set = ['0', workmode, '0', funid]  # 主片E,目前主片不支持B41
            if self.bd.set_mode(*mode_set):  # 设置从片
                logger.debug('set new mode={}'.format(mode_set))
                return '1'
        return '2'

    def conf_class1_para(self, cellid, freq):
        '''
        基于某band下读取一类参数并设置频点
        :return:当前频点下的PCI，信号源需要用
        '''
        i = 0
        try:
            while 1:
                if i > 3:
                    raise NotImplementedError('一类参数设置失败')
                class1_para = self.query_class1_para()  # 先读
                logger.debug('get_class1_para={}'.format(class1_para))
                if class1_para is None:
                    raise NotImplementedError('一类参数设置失败')
                set_para = copy.deepcopy(class1_para)
                set_para[0] = int(freq)
                set_para[1] = 0  # 5M带宽
                set_para[2] = 0  # 功率级别最大
                # pci = set_para[3]  # 获取一类参数中PCI
                self.bd.set_class1(*set_para)  # 再设置
                logger.info('set_class1_para={}'.format(set_para))
                time.sleep(.5)
                new_class1_para = self.query_class1_para()
                if new_class1_para is None:
                    raise RuntimeError('query_class1_para error')
                self.bd.set_rf(1)  # 打开
                if float(new_class1_para[1]) == float(freq):
                    break
                i = i + 1
                time.sleep(3)
        except Exception as e:
            raise NotImplementedError('设置一类参数错误')

    def query_class1_para(self, cellid=None):
        i = 0
        while 1:
            para = self.bd.query_class1_para(cellid)
            if para:
                return para
            i = i + 1
            if i > 3:
                return None
            time.sleep(5)

    def read_txatt(self, cellid):
        '''
        因为有时读取失败，所以多次读取尝试
        :return:
        '''
        i = 0
        txatt = None
        while 1:
            try:
                txatt = self.bd.get_txatt()
            except Exception as e:
                logger.error(e)
                self.reconnect_board()
            i = i + 1
            if txatt:
                return txatt
            time.sleep(9)
            if i > 5:
                return txatt

    def set_txatt(self, cellid, txatt):
        cellid = None
        self.bd.set_txatt(cellid, txatt)

    def set_power_compensation(self, cp, tp):
        i = 0
        while 1:
            try:
                self.bd.set_power_compensation(cp, tp)
                break
            except Exception as e:
                logger.error(e)
                self.reconnect_board()
            # self.bd.set_power_compensation(cp, tp)
            i = i + 1
            if i > 3:
                break
            time.sleep(2)

    def reset_frameoffset(self, cellid):
        '''
        查询当前帧偏移是否为0，不是则设置为0，是则不设置
        主从片的帧偏移文件位置不一样
        TDD通过命令修改，会自动重启
        FDD不能通过命令设置帧偏移，只能修改文件来修改帧偏移,需要手动重启
        :return:
        '''
        if cellid == '0':
            if self.login_board():
                self.run_process()  # 起进程
                self.bd.reset_frameoffset(cellid)
                # time.sleep(1)
                # self.bd.exit()
                return '1'
            return '2'
        else:
            if self.bd.reset_frameoffset(cellid):  # FDD通过文件修改，因为通过命令无法修改
                return '1'
            else:
                return '2'

    def reset_antiswitch(self, cellid):

        if self.login_board():
            self.run_process()
            self.bd.reset_antiswitch()  # 8215关闭降干扰开关
            # time.sleep(1)
            # self.bd.exit()
            return '1'
        return '2'

    def set_clocksrc(self):
        if self.login_board():
            time.sleep(1)
            self.run_process()
            self.bd.set_clocksrc()
            # time.sleep(1)
            # self.bd.exit()
            return '1'
        return '2'

    def set_rf(self, cellid, onoff):
        self.bd.set_rf(cellid, onoff)

    def check_bandinfo(self, cellid):
        '''
        检查band修改成功是否
        :return:
        '''
        i = 0

        while 1:
            blst = self.bd.get_boardinfo()
            if blst:
                mastermode, slavemode, masterfid, slavefid = blst
                if cellid == '0':
                    return mastermode, masterfid
                elif cellid == '1':
                    return slavemode, slavefid
            i = i + 1
            if i > 3:
                return None
            time.sleep(10)

    def conf_board_txatt(self):
        '''
        type:str
        cellid:str
        初始化txatt为初始默认值
        :return:int
        '''
        self.set_power_compensation(0, 0)
        # 这时读取txatt 8125 tdd 初始衰减为6dB,FDD 初始衰减为7dB
        time.sleep(1)
        default_txatt = self.read_txatt()
        logger.info('default_txatt={}'.format(default_txatt))
        return default_txatt

    def get_frameoffset(self, cellid):

        i = 0
        while 1:
            value = self.bd.get_frameoffset(cellid)
            if not value is None and len(value) > 0:
                return value
            time.sleep(3)
            i = i + 1
            if i > 3:
                return None

    def add_route(self, pcip):
        '''
        从片添加路由
        :param pcip:
        :return:
        '''
        # 先telnet从片添加路由
        if self.bd.add_route(pcip):
            # PC cmd添加
            ip = self.config.get('IP')
            subip = self.config.get('SUBIP', '')  # T2K没有SUBIP字段
            cmd = 'route ADD {} MASK 255.255.255.255 {}'.format(subip, ip)
            logger.debug(cmd)
            os.system(cmd)
            return True
        return False


class BT2KHandler(BoardHandler):

    def __init__(self, **kwargs):
        type = 'T2K'
        super(BT2KHandler, self).__init__(type, **kwargs)

    def login_board(self):
        try:

            # T2K没有主从片
            subip = ''
            flag = self.login_band(subip)
            return flag
        except Exception as e:
            logger.error(e)
            return False

    def set_band_on_TDD(self, cellid, workmode, funid):
        '''
        设置要求的band，只在8125主片或T2K载波0设置TDD，TDD测试顺序：B41,E,F
        :return:'0'--band不用修改  '1':修改成功  '2'：修改失败
        '''
        # stages=['5','0','2'] #b41,e,f的主片funid
        # state=0

        # masterWorkMode, masterFunId = self.check_bandinfo()
        # logger.debug('now master workmode,funid={},{}'.format(masterWorkMode, masterFunId))
        # if masterWorkMode == str(workmode) and str(masterFunId) == str(funid):
        #     return '0'
        # else:
        # 写文件修改
        if self.bd.set_mode(cellid, workmode, funid):
            return '1'
        return '2'

    def set_band_on_FDD(self, cellid, workmode, funid):
        # slaveWorkMode, slaveFunId = self.check_bandinfo()
        # logger.debug('now slave workmode,funid={},{}'.format(slaveWorkMode, slaveFunId))
        # if slaveWorkMode == str(workmode) and str(slaveFunId) == str(funid):
        #     return '0'
        # else:
        if self.bd.set_mode(cellid, workmode, funid):
            return '1'
        return '2'

    def conf_class1_para(self, cellid, freq):
        '''
        基于某band下读取一类参数并设置频点
        :return:
        '''

        i = 0
        while 1:
            if i > 3:
                raise NotImplementedError('设置一类参数异常')
            class1_para = self.query_class1_para(cellid)  # 先读
            logger.debug('get_class1_para={}'.format(class1_para))
            if class1_para is None:
                raise RuntimeError('query_class1_para error')
            set_para = copy.deepcopy(class1_para)
            set_para[1] = int(freq)
            set_para[2] = 0  # 5M带宽
            set_para[3] = 0  # 功率级别
            self.bd.set_class1(*set_para)  # 再设置
            logger.info('set_class1_para={}'.format(set_para))
            time.sleep(.5)
            new_class1_para = self.query_class1_para(cellid)
            logger.debug(new_class1_para)
            if new_class1_para is None:
                raise RuntimeError('query_class1_para error')
            self.bd.set_rf(cellid, 1)  # 打开
            if float(new_class1_para[1]) == float(freq):
                logger.debug('一类参数设置成功')
                break
            i = i + 1
            time.sleep(3)

    def query_class1_para(self, cellid):
        i = 0
        while 1:
            para = self.bd.query_class1_para(cellid)
            if para:
                return para
            i = i + 1
            if i > 3:
                logger.error('query class1 para failed')
                return None
            time.sleep(5)

    def read_txatt(self, cellid):
        '''
        因为有时读取失败，所以多次读取尝试
        :return:
        '''
        i = 0
        txatt = None
        while 1:
            try:
                txatt = self.bd.get_txatt(cellid)
            except Exception as e:
                logger.error(e)
                self.reconnect_board()
            i = i + 1
            if txatt:
                return txatt
            time.sleep(9)
            if i > 5:
                return txatt

    def set_txatt(self, cellid, txatt):
        logger.debug('set_txatt')

        i = 0
        while 1:
            if i > 5:
                raise NotImplementedError('set txatt failed')
            i = i + 1
            try:
                self.bd.set_txatt(cellid, txatt)
                return
            except Exception as e:
                logger.error(e)
                self.reconnect_board()
            time.sleep(3)

    def reset_frameoffset(self, cellid):
        '''
        查询当前帧偏移是否为0，不是则设置为0，是则不设置
        主从片的帧偏移文件位置不一样
        TDD通过命令修改，会自动重启
        FDD不能通过命令设置帧偏移，只能修改文件来修改帧偏移,需要手动重启
        :return:
        '''
        # 直接修改不判断原先的值

        if self.login_board():
            self.run_process()  # 起进程
            self.bd.reset_frameoffset(cellid)
            # time.sleep(1)
            # self.bd.exit()
            return '1'
        else:
            return '2'

    def reset_antiswitch(self, cellid):

        if self.login_board():
            self.run_process()
            self.bd.reset_power_compesation(cellid)  # T2K关闭温补，频补
            # time.sleep(1)
            # self.bd.exit()
            return '1'
        return '2'

    def set_clocksrc(self):
        if self.login_board():
            time.sleep(1)
            self.run_process()
            self.bd.set_clocksrc()
            # time.sleep(1)
            # self.bd.exit()
            return '1'
        return '2'

    def set_rf(self, cellid, onoff):
        self.bd.set_rf(cellid, onoff)

    def check_bandinfo(self, cellid):
        '''
        检查band修改成功是否
        :return:
        '''
        i = 0
        # cellid = str(self.cellid)
        while 1:
            blst = self.bd.get_boardinfo()
            if blst:
                mastermode, slavemode, masterfid, slavefid = blst
                if cellid == '0':
                    return mastermode, masterfid
                elif cellid == '1':
                    return slavemode, slavefid
            i = i + 1
            if i > 3:
                return None
            time.sleep(10)

    def conf_board_txatt(self, cellid):
        '''
        type:str
        cellid:str
        初始化txatt为初始默认值
        :return:int
        '''

        if cellid == '0':
            return 7
        elif cellid == '1':
            return 31

    def get_frameoffset(self, cellid):

        return self.bd.get_frameoffset(cellid)

    def add_route(self, pcip):
        return True

    def get_temp(self):
        '''
        读取基带板温度
        :return:
        '''
        return self.bd.read_temp()

    def read_json(self, filename):
        return self.bd.read_gain_json(filename)


if __name__ == '__main__':
    pass
