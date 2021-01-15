# coding:utf-8
'''
频谱仪的测试项，EVM,谐波,需要用到信号源
'''
import time
import logging
from .fsv import FSVCtrl
from .smbv import SMBV

logger = logging.getLogger('ghost')


class HandleFSVAndSMBV(object):
    def __init__(self, fsvip, smbvip, offset):
        self.fsv = None
        self.smbv = None
        self.fsvip = fsvip
        self.smbvip = smbvip
        self.offset = offset

    def close_rf(self):
        '''
        关闭信号源输入
        :return:
        '''
        if self.smbv is not None:
            self.smbv.close_smbvrf()
        if self.fsv is not None:
            self.fsv.close_inst()

    def init_all(self):
        logger.debug('init fsv&smbv')
        self.fsv = FSVCtrl()
        self.fsv.init_inst(self.fsvip)
        self.fsv.reset_fsv()
        self.fsv.set_offset(self.offset)
        self.smbv = SMBV()
        self.smbv.init_inst(self.smbvip)
        self.smbv.set_smbv()
        # if state=='1':
        #     self.init_depend_on_state()

    def close_all(self):
        self.fsv.close_inst()
        self.smbv.close_inst()

    def reconnect_fsv(self):
        i = 0
        while 1:
            try:
                i = i + 1
                if i >= 3:
                    raise RuntimeError('FSV not online')
                self.fsv.close_inst()
                self.fsv.init_again()
                self.fsv.reset_fsv()
                break
            except Exception as e:
                logger.error(e)
                time.sleep(6)

    def get_max_single_tone(self, freq, target):
        '''
        获取单音下的增益
        :param freq:
        :param target:
        :return:增益dB
        '''
        if self.fsv is None or self.smbv is None:
            logger.error('no fsv or no smbv')
            return
        logger.debug('单音freq={}'.format(freq))
        level = -20  # 信号源起始level

        self.smbv.set_for_single_tone(freq, level)
        self.reconnect_fsv()
        self.fsv.set_for_single_tone(freq, target)
        power = float(self.fsv.get_single_tone_power(freq, target))

        while power <= target - 1:
            level += 1
            lastp = power
            self.smbv.set_level(level)
            time.sleep(.1)
            power = float(self.fsv.get_single_tone_power(freq, target))
            logger.debug('fsv power={}'.format(power))
            if abs(lastp - power) < 0.3:
                return '%.2f' % float(level), power, '%.2f' % (power - float(level))

        for i in range(15):
            level += 0.1
            self.smbv.set_level(level)
            # time.sleep(.1)
            power = float(self.fsv.get_single_tone_power(freq, target))
            # logger.debug('fsv power={}'.format(power))
            if power >= target:
                logger.debug('hit target power {},level={}'.format(power, level))
                break
        return '%.2f' % float(level), power, '%.2f' % (power - float(level))

    def get_max_power(self, freq, target):
        '''
        获取5M带宽下的最大输出功率
        :param freq:MHz
        target:目标最大功率dBm
        :return:(信号源输入，频谱仪输出功率，ACPR)
        '''
        if self.fsv is None or self.smbv is None:
            logger.error('no fsv or no smbv')
            return
        self.reconnect_fsv()
        logger.debug('get_max_power')
        logger.debug('测EVM时freq={}'.format(freq))
        level = -20  # 信号源起始level
        self.smbv.set_for_max_power(freq, level)
        self.fsv.set_for_txatt(10,freq)

        powerlst = self.fsv.get_power(10,freq)
        power = float(powerlst[0])
        while power <= target - 1:
            level += 1
            lastp = power
            self.smbv.set_level(level)
            powerlst = self.fsv.get_power(10,freq)
            power = float(powerlst[0])  # 频谱仪输出
            logger.debug('fsv power={}'.format(power))
            if abs(lastp - power) < 0.3:
                acpr = '{}/{}'.format(powerlst[1], powerlst[2])
                return '%.2f' % float(level), power, acpr

        for i in range(15):
            level += 0.1
            self.smbv.set_level(level)
            powerlst = self.fsv.get_power(10,freq)
            power = float(powerlst[0])
            logger.debug('fsv power={}'.format(power))
            if power >= target:
                logger.debug('hit target power {},level={}'.format(target, level))
                break
        acpr = '{}/{}'.format(powerlst[1], powerlst[2])
        return '%.2f' % float(level), power, acpr

    def get_evm(self, freq):
        '''
        读取ACPR LOWER/UPPER
        :return:
        '''
        self.smbv.set_rf_on()
        self.fsv.set_for_evm('FDD', freq)
        evm_all = self.fsv.read_evmall()
        logger.debug('evm_all={}'.format(evm_all))
        return evm_all
