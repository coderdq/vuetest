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

    def set_for_evm(self, mode, freq):
        '''
        为测EVM进行设置
        :param freq:
        :return:
        '''
        if self.handle:
            mode = str(mode).upper()
            self.handle.write('*RST;*CLS')
            self.handle.ext_clear_status()
            self.handle.write('INIT:CONT OFF')
            self.handle.write('SYST:DISP:UPD ON')
            # self.handle.ext_error_checking()

            self.handle.write('INST LTE')  # mode选择LTE
            # self.handle.write('SWE:COUN 3')
            self.handle.write('TRIG:MODE EXT')  # external trigger
            # for test
            # self.handle.write('TRIG:MODE IMM')  # free run
            self.handle.write('DISP:TRAC:Y:RLEV:OFFS {}dB'.format(self.offset))  # Ext Att 40dB,与外部衰减对应
            self.handle.write('FREQ:CENT {}MHz'.format(freq))  # CENT FREQ
            self.handle.write('CONF:DUPL {}'.format(mode))  # TDD/FDD
            self.handle.write('CONF:LDIR DL')  # DL/UL
            self.handle.write('CONF:DL:BW BW5_00')  # dl-bandwidth 5MHz

    def get_single_CCDF(self):
        '''
        设置同读EVM时设置一样
        :return:
        '''

        try:
            if self.handle:
                self.handle.ext_clear_status()
                self.handle.write('INIT:CONT OFF')
                self.handle.write('DISP:TABL ON')  # Display list
                self.handle.write('INIT;*WAI')
                # self.handle.write('INIT:CONM;*WAI')
                sampling_error = self.handle.query('FETCH:SUMMARY:SERROR?', delay=1)
                # power = self.handle.query('FETCH:SUMMARY:POW?')
                self.handle.query('*OPC?')
                se = sampling_error.split('\n')[0]

                crest_factor = self.handle.query('FETCH:SUMMARY:CREST?', delay=1)  # 默认取mean
                self.handle.query('*OPC?')
                cf = crest_factor.split('\n')[0]
                return '%.2f' % float(se), '%.2f' % float(cf)
            return None
        except Exception as e:
            logger.error(e)
            return None

    def get_several_ccdf(self, mode, freq):
        r = 0
        while True:
            n = yield r
            if not n:
                return
            resstr = self.get_single_CCDF()
            if resstr is not None:
                r = resstr
            else:
                r = None
                self.close_inst()
                self.init_again()
                time.sleep(1)
                self.reset_fsv()
                self.set_for_evm(mode, freq)
                time.sleep(1)
            time.sleep(.5)

    def get_CCDF(self, mode, freq):
        self.set_for_evm(mode, freq)
        consumer = self.get_several_ccdf(mode, freq)
        ccdf = self.sweep_ccdf(consumer)
        return ccdf

    def sweep_ccdf(self, c):
        c.__next__()
        n = 0
        ccdf = None
        while n < 6:
            n = n + 1
            r = c.send(n)
            if r is not None:
                ccdf = r
                break
        c.close()
        return ccdf

    def get_EVM(self, mode, freq):
        '''
        读取EVM
        :return:
        '''
        self.set_for_evm(mode, freq)
        consumer = self.gen_maxEVM(mode, freq)
        maxevmlist = self.sweep_several(consumer)
        return max(maxevmlist)

    def sweep_several(self, c):
        '''
        single sweep 多次，结果取平均值
        :return:[float,float]
        '''
        c.__next__()
        n = 0
        evmlist = []
        while n < 6:
            n = n + 1
            r = c.send(n)
            evmlist.append(r)
        c.close()
        evmlist = [float(evm) for evm in evmlist]
        logger.debug('evmaxlist={}'.format(evmlist))
        return evmlist

    def gen_asum(self):
        '''
            产生asum数据字符串
        :return:
        '''
        try:
            self.handle.write('INIT:CONT OFF')
            self.handle.write('UNIT:EVM PCT')
            self.handle.write('DISP:TABL OFF')
            # self.handle.write("CALC1:FEED 'STAT:ASUM'")
            self.handle.write("CALC2:FEED 'STAT:ASUM'")
            self.handle.write('INIT;*WAI')
            # self.handle.write('INIT:CONM;*WAI')
            res = self.handle.query('TRAC:DATA? TRACE1', delay=1)  # 以,分割的字符串,成员均为字符串
            # time.sleep(5)
            self.handle.query('*OPC?')
            return res
        except Exception as e:
            logger.error(e)
            return None

    def get_power_spectrum(self, mode, freq):
        '''
        获得占用带宽MHz
        :return: float mhz
        '''
        try:
            if self.handle:
                self.set_for_evm(mode, freq)
                self.handle.write('INIT:CONT OFF')
                self.handle.write('UNIT:EVM PCT')
                self.handle.write('DISP:TABL OFF')
                self.handle.write("CALC2:FEED 'SPEC:PSPE'")
                self.handle.write('INIT;*WAI')
                res = self.handle.query('TRAC:DATA? TRACE1')  # 以,分割的字符串,成员均为字符串
                time.sleep(2)
                self.handle.query('*OPC?')
                mhz = self.compute_inband_width(res)
                return mhz
        except Exception as e:
            raise NotImplementedError('get_power_spectrum error:{}'.format(e))

    def compute_inband_width(self, restr):
        '''
        计算占用带宽,
        :return:
        '''
        restr = re.sub(r'\S?NAN\S?', '', restr)  # 去掉NAN无效字符串
        relist = [float(item) for item in restr.split(',')]
        # maxum = max(relist)
        logger.debug('length={}'.format(len(relist)))
        # relist.remove(maxum)  # 删除一个最大值
        newlist=self.remove_fifty(relist)
        maxum = max(newlist)
        minum = min(newlist)
        delta = (maxum + minum) / 2.0
        greaterlist = [item for item in newlist if item >= delta]
        n = len(greaterlist)+50
        mhz = n * 7.68 / 1024.0  # 占用带宽MHz
        return '%.2f' % mhz

    def remove_fifty(self,alist):
        '''
        去掉中间50个点再算带宽
        :return:
        '''
        mid=len(alist)//2
        return alist[:mid-25]+alist[mid+25:]

    def gen_maxEVM(self, mode, freq):
        r = 0
        while True:
            n = yield r
            if not n:
                return
            resstr = self.gen_asum()
            if resstr:
                maxret = self.fetch_max(resstr)
                if maxret:
                    r = maxret
                else:
                    r = 0
            else:
                r = 0
                self.close_inst()
                self.init_again()
                time.sleep(1)
                self.reset_fsv()
                self.set_for_evm(mode, freq)
                time.sleep(1)
            time.sleep(.5)

    def fetch_max(self, resstr):
        '''

        :param resstr:
        :return:
        '''
        if not resstr:
            return None
        reslist = resstr.strip('\n\r\t').split(',')
        # logger.debug('reslist={}'.format(reslist))
        reslen = len(reslist)
        narray = np.array(reslist)
        frame = pd.DataFrame(narray.reshape((reslen // 7, 7)), columns=['subframe', 'alloc_ID', 'num_RB',
                                                                        'rel_power', 'modulation', 'abs_power', 'EVM']
                             )
        # frame['EVM']=frame['EVM'].map(lambda x:'%.4f'%x)
        frame['EVM'] = frame['EVM'].apply(pd.to_numeric)  # str->float
        allid_frame = frame[frame['alloc_ID'] == '-5']  # RS Ant1
        if not allid_frame.empty:
            sort_frame = allid_frame.sort_values(by='EVM', ascending=False)
            maxEVM = sort_frame.iloc[0]['EVM']
            return '%.2f' % float(maxEVM)
        return None

    def set_for_DANL(self, start, stop):
        '''
        底噪设置，使用上行频带
        :return:str
        '''
        i=0
        while 1:
            if i>3:
                return None
            i=i+1
            try:
                if self.handle:
                    self.handle.write('*RST;*CLS')
                    self.handle.ext_clear_status()
                    self.handle.write('INST SAN')  # mode选择Spectrum
                    self.handle.write('DISP:TRAC:Y:RLEV:OFFSET {}dB'.format(self.offset))  # REF OFFSET 加了衰减器的40dB
                    self.handle.write('DISP:TRAC:Y:RLEV -10dBm')  # reference level
                    self.handle.write('BAND 100KHz')  # resolution bandwidth
                    # self.handle.write('BAND:VID:AUTO ON')  # video bandwidth auto
                    self.handle.write('BAND:VID 1MHz')  # video bandwidth
                    self.handle.write('INIT:CONT OFF')
                    self.handle.write('FREQ:START {}MHz'.format(start))  # 上行的频率
                    self.handle.write('FREQ:STOP {}MHz'.format(stop))  # 上行的频率
                    self.handle.write('SWE:COUN 16')
                    self.handle.write('DISP:TRAC1:MODE MAXH')  # MAX HOLD
                    self.handle.write('INIT;*WAI')

                    self.handle.write('CALC1:MARKER1:MAX')
                    y = self.handle.query('CALC:MARK1:Y?')

                    return '%.2f' % (float(y)-self.offset-10)  #加了衰减的底噪测试值要减去底噪再减去频谱仪内置10dB
                else:
                    return None
            except Exception as e:
                logger.error(e)
                time.sleep(3)
                self.close_inst()
                self.init_again()
                self.reset_fsv()
                continue

    def get_power(self, ref_level,freq):
        # self.set_for_txatt(freq)
        logger.debug('get_power')
        consumer = self.gen_several_power(ref_level,freq)
        power = self.sweep_ccdf(consumer)
        return power

    def gen_several_power(self,ref_level, freq):
        r = 0
        while True:
            n = yield r
            if not n:
                return
            resstr = self.get_single_power()
            if resstr:
                r = resstr
            else:
                logger.error('get None')
                r = None
                self.close_inst()
                self.init_again()
                time.sleep(3)
                self.reset_fsv()
                self.set_for_txatt(ref_level,freq)
                time.sleep(1)
            time.sleep(1)

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
    fsv.set_offset(51)
    # fsv.set_for_evm('TDD', 2397.5)
    # fsv.get_EVM('TDD',2350)
    fsv.get_power_spectrum('TDD',2397.5)
    fsv.close_inst()
