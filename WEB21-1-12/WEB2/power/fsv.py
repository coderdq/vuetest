#! encoding = utf-8
'''
频谱仪使用，网口控制 192.168.1.11
'''

import time
import logging

from commoninterface.fsvbase import FSVBase

logger = logging.getLogger('ghost')


class FSVCtrl(FSVBase):

    def __init__(self):
        FSVBase.__init__(self)

    def set_for_txatt(self,ref_level,  freq):
        '''
        5M带宽下功率的读取
        :param freq:
        :return:
        '''
        if self.handle:
            self.handle.write('*RST;*CLS')
            self.handle.ext_clear_status()
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
            self.handle.write('SWE:TIME 0.5s')  # sweep time
            self.handle.write('POW:ACH:MODE REL')  # 取dB相对值
            self.handle.write('CALC:MARK:FUNC:POW:SEL ACP')
            self.handle.write('DET RMS')

    def set_for_single_tone(self, freq, target):
        '''
        单音信号下的功率测量
        target:dBm
        :return:
        '''
        try:
            if self.handle:
                self.handle.write('*RST;*CLS')

                self.handle.write('INIT:CONT OFF')
                self.handle.write('SYST:DISP:UPD ON')

                self.handle.write('FREQ:CENT {}MHz'.format(freq))  # center freq
                self.handle.write('FREQ:SPAN 20MHz')  #span
                self.handle.write('DISP:TRAC:Y:RLEV:OFFSET {}dB'.format(self.offset))  # REF OFFSET 加了衰减器的40dB
                ref = int(target) + 3
                self.handle.write('DISP:TRAC:Y:RLEV {}dBm'.format(ref))  # reference level
                self.handle.write('BAND 200KHz')  # resolution bandwidth
                self.handle.write('BAND:VID 200KHz')  # video bandwidth
                self.handle.write('SWE:TIME 0.5s')  # sweep time
        except Exception as e:
            logger.error(e)

    def get_single_tone_power(self,freq,target):
        '''
        获得单音信号的功率，找的peak点
        :return:
        '''
        i=0
        while 1:
            i=i+1
            if i>=6:
                return None
            try:
                if self.handle:
                    self.handle.write('INIT:CONT OFF')
                    self.handle.write('INIT;*WAI')
                    self.handle.write('CALC:MARK:TRAC 1')
                    self.handle.write('CALC:MARK:FUNC:FPE 1')
                    power=self.handle.query('CALC:MARK:FUNC:FPE:Y?')
                    self.handle.query('*OPC?')
                    return '%.2f'%float(power)
            except Exception as e:
                logger.error(e)
                self.close_inst()
                self.init_again()
                time.sleep(3)
                self.reset_fsv()
                self.set_for_single_tone(freq,target)
                time.sleep(1)
                continue

    def read_evmall(self):
        '''
        读取表格中EVM ALL
        :return:
        '''
        try:
            if self.handle:
                self.handle.write('INIT:CONT OFF')
                self.handle.write('DISP:TABL ON')  # Display list
                self.handle.write('INIT;*WAI')
                # self.handle.write('INIT:CONM;*WAI')
                evm_all = self.handle.query('FETCH:SUMMARY:EVM:MAX?', delay=1)
                self.handle.query('*OPC?')
                # logger.debug('evm_all={}'.format(evm_all))
                evm_all = evm_all.split('\n')[0]
                return '%.2f' % float(evm_all)
            return None
        except Exception as e:
            logger.error(e)
            return None

    def get_single_power(self):
        '''
        continue single sweep
        获取输出功率
        :return:[str tx power,str adj lower,str adj upper]
        '''
        try:
            if self.handle:
                # self.handle.write('*CLS')
                # self.handle.ext_clear_status()
                self.handle.write('INIT:CONT OFF')
                self.handle.write('CALC:MARK:FUNC:POW:SEL ACP')
                self.handle.write('DET RMS')
                # self.handle.write('SWE:COUN 20')

                self.handle.write('INIT;*WAI')
                # res = self.handle.query('TRAC:DATA? TRACE1')  # 以,分割的字符串,成员均为字符串
                # time.sleep(2)
                # self.handle.query('*OPC?')
                # print(res)
                # print(len(res))

                cpower = self.handle.query('CALC:MARK:FUNC:POW:RES? ACP')
                self.handle.query('*OPC?')
                cpower1 = [item.strip() for item in cpower.split(',')]
                ret = ['%.2f' % float(item) for item in cpower1]
                return ret[:3]
        except Exception as e:
            logger.error('get_power error:{}'.format(e))
            return None
        else:
            return None

    def just_test(self):
        if self.handle:
            self.handle.write('*CLS')
            self.handle.ext_clear_status()
            self.handle.write('INIT:CONT OFF')

            self.handle.write('INIT;*WAI')
            res = self.handle.query('TRAC:DATA? TRACE1')  # 以,分割的字符串,成员均为字符串
            time.sleep(2)
            self.handle.query('*OPC?')
            # print(res)
            lst = res.split(',')
            print(len(lst))
            # res=self.handle.query('DISP:TRAC1:X?')
            # time.sleep(2)
            # self.handle.query('*OPC?')
            # print(res)
            # lst=res.split(',')
            # print(len(lst))
            res=self.handle.query('DISP:TRAC:X:START?')
            time.sleep(2)
            self.handle.query('*OPC?')
            print(res)
            lst = res.split(',')
            print(len(lst))


if __name__ == '__main__':
    fsv = FSVCtrl()
    fsv.init_inst('192.168.1.11')
    fsv.reset_fsv()
    # fsv.set_offset(46)
    # fsv.set_for_txatt('2302.5')
    # print(fsv.get_single_power())
    fsv.just_test()
    # fsv.set_for_evm('FDD', 2350)
    #
    # fsv.close_inst()
    # fsv.set_for_single_tone('2300',-20)
    # print(fsv.get_single_tone_power())
