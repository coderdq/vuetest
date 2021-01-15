#! encoding = utf-8
'''
频谱仪使用，网口控制 192.168.1.11
'''
import time
import logging
import pandas as pd
import numpy as np
import re
from commoninterface.fsvbase import FSVBase

logger = logging.getLogger('ghost')


class FSVCtrl(FSVBase):

    def __init__(self):
        FSVBase.__init__(self)

    def set_for_txatt(self, ref_level, freq):
        logger.debug('set_for_txatt')
        if self.handle:
            self.handle.write('*RST;*CLS')
            self.handle.write('INST SAN')  # mode选择Spectrum
            self.handle.write('FREQ:CENT {}MHz'.format(freq))  # center freq
            self.handle.write('DISP:TRAC:Y:RLEV:OFFSET {}dB'.format(self.offset))  # REF OFFSET 加了衰减器的40dB
            self.handle.write('DISP:TRAC:Y:RLEV {}dBm'.format(ref_level))  # reference level
            # self.handle.write('DISP:TRAC:Y:RLEV:OFFS -10dB')  # reference level offset
            self.handle.write('BAND 100KHz')  # resolution bandwidth
            # self.handle.write('BAND:VID:AUTO ON')  # video bandwidth auto
            self.handle.write('BAND:VID 1MHz')  # video bandwidth
            self.handle.write('CALC:MARKER:FUNC:POW:PRES EUTRA')  # EUTRA/LTE Square

            self.handle.write('POW:ACH:BWID:CHAN1 4.5MHz')  # TX bandwidth
            self.handle.write('POW:ACH:BWID:ACH 4.5MHz')  # adj channel bandwidth
            self.handle.write('POW:ACH:SPAC:CHAN 4.5MHz')  # TX Spacing
            self.handle.write('POW:ACH:SPAC 5MHz')  # 载波和ADJ之间的spacing

            # self.handle.write('SWE:TIME 0.2s')  # sweep time
            self.handle.write('SWE:TIME 2s')  # sweep time
            self.handle.write('POW:ACH:MODE REL')  # 取dB相对值
            self.handle.write('CALC:MARK:FUNC:POW:SEL ACP')
            self.handle.write('DET RMS')

    def get_single_power(self):
        '''
        continue single sweep
        获取输出功率
        :return:[str tx power,str adj lower,str adj upper]
        '''
        try:
            if self.handle:
                self.handle.write('*CLS')
                self.handle.write('INIT:CONT OFF')
                self.handle.write('CALC:MARK:FUNC:POW:SEL ACP')
                self.handle.write('DET RMS')
                # self.handle.write('SWE:COUN 20')

                self.handle.write('INIT;*WAI')
                # self.handle.write('INIT:CONM;*WAI')
                # ACP 返回，分割的字符串  TX Power,Adj lower,Adj Upper,Alt1 lower,Alt1 Upper
                # time.sleep(1)
                cpower = self.handle.query('CALC:MARK:FUNC:POW:RES? ACP', delay=1)
                self.handle.query('*OPC?')
                cpower1 = [item.strip() for item in cpower.split(',')]

                ret = ['%.2f' % float(item) for item in cpower1]

                return ret[:3]
        except Exception as e:
            logger.error('get_power error:{}'.format(e))
            return None
        else:
            return None


if __name__ == '__main__':
    fsv = FSVCtrl()
    fsv.init_inst('192.168.1.11')
    fsv.reset_fsv()
    fsv.set_offset(8)

    # fsv.get_power(2397.5)
    # fsv.get_EVM('TDD',2350)
    fsv.close_inst()
