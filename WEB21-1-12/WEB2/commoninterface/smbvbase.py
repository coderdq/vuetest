'''
信号源，网口控制,测试灵敏度需要用到
SMBV表示信号源的配置
'''

import time
import logging
from commoninterface.instrument import InstBase
logger = logging.getLogger('ghost')


class SMBVBase(InstBase):
    def __init__(self):
        InstBase.__init__(self, 'SMBV')

    def set_smbv(self):
        if self.handle:
            self.handle.write_termination = '\n'
            self.handle.timeout = 20000

            self.ext_error_checking()

    def set_offset(self, offset):
        '''
        设置衰减值
        :param offset:
        :return:
        '''
        self.offset = offset

    def reset_smbv(self):
        if self.handle:
            self.handle.write_termination = '\n'
            self.handle.timeout = 10000
            self.handle.write('*RST')
            self.handle.write('*CLS')

            self.ext_error_checking()

    def set_freq(self, freq):
        '''
        设置频率
        :param freq:
        :return:
        '''
        logger.debug('*****set_freq')
        if self.handle:
            self.handle.write(':FREQ {}MHz'.format(freq))

    def set_TDD_lte(self, pci):
        '''
        TDD 上行配置
        :return:
        '''
        logger.debug('smbv set_TDD_lte')
        try:
            if self.handle:
                self.handle.write(':BB:EUTR:STAT ON')
                self.handle.write(':BB:EUTR:DUPL TDD')
                self.handle.write(':BB:EUTR:LINK UP')

                self.handle.write(':BB:EUTR:UL:BW BW5_00')  # 5M带宽
                self.handle.write(':BB:EUTR:TDD:UDConf 2')  # 2
                self.handle.write(':BB:EUTR:TDD:SPSConf 7')
                self.handle.write(':BB:EUTR:UL:PLC:CID {}'.format(pci))
                self.handle.write(':BB:EUTR:UL:REFS:DSSH 3')
                self.handle.write(':BB:EUTR:UL:REFS:DMRS 4')
                self.handle.write(':BB:EUTR:UL:UE1:STAT ON')
                self.handle.write(':BB:EUTR:UL:UE1:ID 100')
                self.handle.write(':BB:EUTR:UL:UE1:FRC:STAT ON')
                self.handle.write(':BB:EUTR:UL:UE1:FRC:TYPE A13')
                time.sleep(1)
                # trigger
                self.handle.write(':BB:EUTR:SEQ ARETrigger')
                time.sleep(1)
                self.handle.write(':BB:EUTR:TRIG:SOUR EXT')
                time.sleep(1)

                # self.handle.write(':BB:EUTR:TIMC:NTA NTA624')
                self.handle.write(':BB:EUTR:TIMC:NTA 624')
                time.sleep(.5)
                # RF/A mod
                self.handle.write('ROSC:SOUR EXT')
                self.handle.write(':POW:LEVel:IMM:OFFSET -{}'.format(self.offset))  # 衰减器
        except Exception as e:
            logger.error(e)
            print(e)

    def set_FDD_lte(self, pci):
        if self.handle:
            self.handle.write(':BB:EUTR:STAT ON')
            self.handle.write(':BB:EUTR:DUPL FDD')
            self.handle.write(':BB:EUTR:LINK UP')
            self.handle.write(':BB:EUTR:UL:BW BW5_00')  # 5M带宽
            self.handle.write(':BB:EUTR:UL:PLC:CID {}'.format(pci))
            self.handle.write(':BB:EUTR:UL:REFS:DSSH 3')
            self.handle.write(':BB:EUTR:UL:REFS:DMRS 4')
            self.handle.write(':BB:EUTR:UL:UE1:STAT ON')
            self.handle.write(':BB:EUTR:UL:UE1:ID 100')
            self.handle.write(':BB:EUTR:UL:UE1:FRC:STAT ON')
            self.handle.write(':BB:EUTR:UL:UE1:FRC:TYPE A13')
            # trigger
            self.handle.write(':BB:EUTR:SEQ ARETrigger')
            time.sleep(1)
            self.handle.write(':BB:EUTR:TRIG:SOUR EXT')
            # self.handle.write(':BB:EUTR:TCW:WS:NTAOffset NTA0')
            # RF/A mod
            self.handle.write('ROSC:SOUR EXT')
            self.handle.write(':POW:LEVel:IMM:OFFSET -{}'.format(self.offset))  # 衰减器

    def set_level(self, dbm):
        '''

        :param dbm:
        :return:
        '''
        try:
            if self.handle:
                self.handle.write(':POW {}'.format(dbm))
                return True
            else:
                # raise ModuleNotFoundError('SMBV not online')
                logger.error('SMBV not online')
                return False
        except Exception as e:
            logger.error(e)
            return False

    def set_rf_on(self):
        if self.handle:
            self.handle.write('OUTP ON')
            self.handle.write('IQ:STAT ON')

    def set_for_max_power(self, freq,level):
        '''
        测试工作电流,EVM时的设置
        :return:
        '''
        self.reset_smbv()
        if self.handle:
            self.set_freq(freq)
            self.handle.write(':BB:EUTR:STAT ON')
            self.handle.write(':BB:EUTR:DUPL FDD')
            self.handle.write(':BB:EUTR:LINK DOWN')
            self.handle.write(':BB:EUTR:DL:BW BW5_00')  # 5M带宽
            time.sleep(1)
            self.handle.write('IQ:STAT ON')  # MOD ON
            self.handle.write('OUTP ON')  # RF ON
            self.handle.write(':POW {}'.format(level))  # LEVEL

    def set_for_single_tone(self,freq,level):
        '''
        单音测试
        :return:
        '''

        if self.handle:
            self.set_freq(freq)
            self.handle.write(':BB:EUTR:STAT ON')
            self.handle.write('IQ:STAT OFF')  # MOD OFF
            self.handle.write('OUTP ON')  # RF ON
            self.handle.write(':POW {}'.format(level))  # LEVEL

    def close_smbvrf(self):
        if self.handle:
            self.handle.write('IQ:STAT OFF')  # MOD OFF
            self.handle.write('OUTP OFF')  # RF Off

    def set_for_harmonic(self, freq):
        '''
        谐波设置
        :param freq:
        :return:
        '''
        if self.handle:
            self.set_freq(freq)
            self.handle.write('SOUR:BB:ARB:STAT ON')
            self.handle.write('BB:ARB:MCAR:CARR:COUN 2')
            self.handle.write('BB:ARB:MCAR:CARR:SPAC 10 MHz')
            self.handle.write('BB:ARB:MCAR:CARR0:STAT ON')
            self.handle.write('BB:ARB:MCAR:CARR1:STAT ON')
            self.handle.write('BB:ARB:MCAR:CLO')
            self.handle.write('IQ:STAT ON')  # MOD ON
            self.handle.write('OUTP ON')  # RF ON


if __name__ == '__main__':
    smbv = SMBV()
    smbv.init_smbv('192.168.1.12')
    smbv.set_smbv()
