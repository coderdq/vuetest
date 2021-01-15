'''
调试基带板
'''
import asyncio
import logging
import copy
import time
import os
from abc import ABCMeta, abstractmethod

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

    def check_enter(self):
        '''
        检查是否能输入命令
        :return:
        '''
        self.bd.execute_enter()

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

    @abstractmethod
    def get_temp(self):
        pass

    @abstractmethod
    def set_rf(self, cellid, onoff):
        pass

    def start_ftp(self):
        '''
        开启ftpserver
        :return:
        '''
        logger.debug('start ftp server')
        self.bd.start_ftp()

    def start_upgrade(self):
        logger.debug('基带板开始升级')
        self.bd.start_upgrade()

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

    def do_ftp(self):
        '''
        打开ftp
        :param args:
        :return:
        '''
        try:
            i = 0
            while 1:
                if i > 3:
                    break
                if self.login():
                    if not self.bd.kill_arm():
                        continue
                    logger.debug('开始登陆')
                    self.do_clear_trash()
                    if not self.login_board():
                        i = i + 1
                        continue
                    time.sleep(.5)
                    self.run_process()
                    self.start_ftp()
                    self.bd.logout_host()
                    return True
                i = i + 1
                time.sleep(5)
            return False
        except Exception as e:
            logger.error(e)
            return False

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
                self.bd.set_gpsmode()
                self.bd.enb_cell()  # 强建小区
                return True

    def do_clear_arm(self):
        try:
            i = 0
            while 1:
                i = i + 1
                if i >= 3:
                    break
                if self.login():
                    logger.debug('删除sanhui_t2k')
                    self.bd.clear_tar()
                    return True
                time.sleep(5)
            return False
        except Exception as e:
            logger.error(e)
            return False

    def do_untar_arm(self, arm_file_name):
        try:
            i = 0
            period = 60
            while 1:
                i = i + 1
                if i >= 3:
                    break
                if self.login():
                    if arm_file_name:
                        logger.debug('删除sanhui_t2k')
                        self.bd.clear_tar()
                        if not self.bd.do_untar_arm(arm_file_name, period):
                            logger.error('解压ARM的TAR包failed')
                            period += 30
                            continue
                        logger.debug('成功解压ARM的TAR包')
                    return True
                time.sleep(5)
            return False
        except Exception as e:
            logger.error(e)
            return False

    def do_chmod_armtar(self, ipstr):
        try:
            i = 0
            while 1:
                i = i + 1
                if i >= 3:
                    break
                if self.login():
                    logger.debug('修改权限')
                    self.bd.chmod_armtar()
                    # 修改first_ip
                    self.bd.modify_firstip(ipstr)
                    return True
                time.sleep(5)
            return False
        except Exception as e:
            logger.error(e)
            return False

    def do_modify_boardinfo(self):
        try:
            i = 0
            while 1:
                if i > 3:
                    break
                if self.login():
                    # self.bd.remove_m('/mnt/flash/scbs', 'BoardInfo.txt')
                    self.bd.set_all_band(0, 1, 0, 4)  # EB1
                    return True
                i = i + 1
                time.sleep(5)
            return False
        except Exception as e:
            logger.error(e)
            return False

    def do_reboot(self):
        try:
            i = 0
            while 1:
                i = i + 1
                if i >= 3:
                    break
                if self.login():
                    logger.debug('reboot')
                    self.bd.execute_some_command('reboot')
                    return True
                time.sleep(5)
            return False
        except Exception as e:
            logger.error(e)
            return False

    def do_upgrade(self):
        try:
            i = 0
            while 1:
                if i > 3:
                    break
                if self.login():

                    if not self.login_board():
                        i = i + 1
                        continue
                    self.run_process()
                    self.bd.set_gpsmode()
                    logger.debug('基带板发送升级命令')
                    self.start_upgrade()
                    return True
                i = i + 1
                time.sleep(5)
            return False
        except Exception as e:
            logger.error(e)
            return False

    def do_get_process_name(self):
        '''
        检查是否升级成功
        :return:
        '''
        process_keyword = self.process_name[1]
        process_name = ''
        try:
            i = 0
            while 1:
                if i > 5:
                    break
                if self.login():
                    time.sleep(.5)
                    logger.debug('开始登陆')
                    if not self.login_board():
                        i = i + 1
                        continue
                    process_name = self.bd.get_process_name(process_keyword)
                    if process_name:
                        return process_name
                i = i + 1
                time.sleep(5)
            return process_name
        except Exception as e:
            logger.error(e)
            return ''

    def do_clear_trash(self):
        '''
        清理垃圾文件
        :return:
        '''
        self.bd.remove_trash()

    def reconnect_board(self):
        if self.login():
            logger.info('begin to pad board..')
            if self.login_board():  # 登录板子
                time.sleep(1)
                self.run_process()  # pad 进程
                return True
            return False
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
                self.bd.send_debug_tempfreq()
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

    def repeat_get_temp(self):
        '''
        读取温度
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
                temp = self.get_temp()
                if temp is not None:
                    return temp  # 返回温度
            time.sleep(2)

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
                    if not self.bd.kill_arm():
                        continue
                    if not self.login_board():  # 登录板子
                        continue
                    self.run_process()  # pad 进程
                    self.bd.set_gpsmode()
                    self.bd.enb_cell()

                    return True
                time.sleep(5)
            except Exception as e:
                logger.error(e)
                continue

    def do_compensation(self, cellid):
        '''
        功率补偿
        :return:
        '''
        # if not self.fresh_tempfreq():
        #     logger.error('操作平坦度补偿表失败')
        #     return False
        # # 杀掉arm进程
        # if not self.kill_arm_process():
        #     logger.error('kill arm failed.')
        #     return False
        # if not self.check_cell_state():
        #     logger.error('cell build failed')
        #     return False
        i = 0
        flag = False
        while 1:
            i = i + 1
            if i >= 3:
                return flag
            if self.login():
                if cellid == '0':
                    self.bd.remove_flat_json()  # 删除平坦度补偿表
                time.sleep(.1)
                if not self.login_board():  # 登录板子
                    continue
                self.run_process()  # pad 进程
                self.bd.send_debug_tempfreq()
                time.sleep(.1)
                # f1 = self.bd.kill_arm()  # 杀掉arm程序
                # if not f1:
                #     continue
                # 关闭另一个cell的射频
                if cellid == '0':
                    self.set_rf('1', 0)
                else:
                    self.set_rf('0', 0)
                break

        # temp = self.repeat_check_temp()
        # if temp is None:
        #     return False
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
        读取BB版本和序列号
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
                if not self.login_board():  # 登录板子
                    continue
                self.run_process()  # pad 进程
                ret = self.bd.get_macaddr()
                logger.debug('sn={}'.format(ret))
                if ret is None:
                    continue
                return ret
            time.sleep(5)


class B8125Handler(BoardHandler):

    def __init__(self, **kwargs):
        type = '8125'
        super(B8125Handler, self).__init__(type, **kwargs)

    def login_board(self):
        try:
            self.check_enter()
            flag = self.login_band(0, '')
            return flag
        except Exception as e:
            logger.error(e)
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
            if new_class1_para is None:
                raise RuntimeError('query_class1_para error')
            self.bd.set_rf(cellid, 1)  # 打开
            if float(new_class1_para[1]) == float(freq):
                logger.debug('一类参数设置成功')
                break
            i = i + 1
            time.sleep(.5)

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

    def set_rf(self, cellid, onoff):
        self.bd.set_rf(cellid, onoff)

    def get_temp(self):
        '''
        读取基带板温度
        :return:
        '''
        return self.bd.read_temp()


if __name__ == '__main__':
    bd = BT2KHandler()
    bd.login()
