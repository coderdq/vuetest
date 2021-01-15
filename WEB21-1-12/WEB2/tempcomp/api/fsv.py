#! encoding = utf-8
'''
频谱仪使用，网口控制 192.168.1.11
'''
import time
import logging
import pandas as pd
import numpy as np

from commoninterface.fsvbase import FSVBase

logger = logging.getLogger('ghost')


class FSVCtrl(FSVBase):

    def __init__(self):
        FSVBase.__init__(self)

    def set_offset(self, offset):
        '''
        设置外部衰减器衰减值
        :param offset: 单位dB
        :return:
        '''
        self.offset = float(offset)
        logger.debug('offset={}'.format(offset))

    def reset_fsv(self):
        if self.handle:
            self.handle.write_termination = '\n'
            self.handle.timeout = 10000
            self.handle.write('*RST')
            self.handle.write('*CLS')

            self.handle.write('INIT:CONT OFF')
            self.handle.write('SYST:DISP:UPD ON')
            self.ext_error_checking()
            self.handle.write('INST SAN')  # mode选择Spectrum
            logger.debug('reset_fsv...')

    def set_freq(self, freq):
        '''
        为测输出功率进行设置
        :param freq:
        :return:
        '''
        if self.handle:
            self.handle.write('FREQ:CENT {}MHz'.format(freq))  # center freq

    def set_for_txatt(self, ref_level, freq):
        logger.debug('set_for_txatt')
        logger.debug(self.handle)
        if self.handle:
            self.handle.write('*RST;*CLS')
            self.handle.write('INST SAN')  # mode选择Spectrum
            self.handle.write('FREQ:CENT {}MHz'.format(freq))  # center freq
            self.handle.write('DISP:TRAC:Y:RLEV:OFFSET {}dB'.format(self.offset))  # REF OFFSET 加了衰减器的40dB
            self.handle.write('DISP:TRAC:Y:RLEV {}dBm'.format(ref_level))  # reference level
            # self.handle.write('DISP:TRAC:Y:RLEV:OFFS -10dB')  # reference level offset
            self.handle.write('CALC:MARKER:FUNC:POW:PRES EUTRA')  # EUTRA/LTE Square

            self.handle.write('POW:ACH:BWID:CHAN1 4.5MHz')  # TX bandwidth
            self.handle.write('POW:ACH:BWID:ACH 4.5MHz')  # adj channel bandwidth
            self.handle.write('POW:ACH:SPAC:CHAN 4.5MHz')  # TX Spacing
            self.handle.write('POW:ACH:SPAC 5MHz')  # 载波和ADJ之间的spacing

            # for test
            self.handle.write('SWE:TIME 1s')  # sweep time
            self.handle.write('POW:ACH:MODE REL')  # 取dB相对值
            self.handle.write('CALC:MARK:FUNC:POW:SEL ACP')
            self.handle.write('DET RMS')

            self.handle.write('BAND 100 KHz')  # resolution bandwidth
            self.handle.write('BAND:VIDeo 30 kHz')  # video bandwidth

    def set_for_evm(self, mode, freq):
        '''
        为测EVM进行设置
        :param freq:
        :return:
        '''
        if self.handle:
            mode = str(mode).upper()
            self.handle.write('*RST;*CLS')
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
            self.handle.query('*OPC?')
            return res
        except Exception as e:
            logger.error(e)
            return None

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

    def save_screenshot(self, dest):
        '''
        截图
        :return:
        '''
        # 截图
        self.handle.write('HCOP:DEV:LANG PNG')
        self.handle.write("MMEM:NAME  'c:\\Temp\\PC_Screenshot.PNG'")
        self.handle.write("HCOP:DEST 'MMEM'")
        self.handle.write('HCOP:ITEM:ALL')
        self.handle.write('HCOP')
        self.handle.query('*OPC?')
        self.ext_error_checking()

        self.ext_query_bin_data_to_file("MMEM:DATA?  'c:\\Temp\\PC_Screenshot.PNG'", r'{}'.format(dest))
        self.handle.query('*OPC?')

    def ext_query_bin_data_to_file(self, query, pc_file_path):
        if self.handle:
            file_data = self.handle.query_binary_values(query, datatype='s')[0]
            new_file = open(pc_file_path, "wb")
            new_file.write(file_data)
            new_file.close()

    def get_power(self, ref_level, freq):
        # self.set_for_txatt(freq)
        consumer = self.gen_several_power(ref_level, freq)
        power = self.sweep_ccdf(consumer)
        return power

    def gen_several_power(self, ref_level, freq):
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
                self.set_for_txatt(ref_level, freq)
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
                #取5次的平均值
                self.handle.write('SWE:COUN 5')
                self.handle.write('DISP:TRAC1:MODE AVER')
                self.handle.write('INIT;*WAI')
                # self.handle.write('INIT:CONM;*WAI')
                # ACP 返回，分割的字符串  TX Power,Adj lower,Adj Upper,Alt1 lower,Alt1 Upper
                # time.sleep(1)
                cpower = self.handle.query('CALC:MARK:FUNC:POW:RES? ACP', delay=5)
                time.sleep(5)
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
    fsv.set_offset(42.6)
    print('***')
    time.sleep(1)
    fsv.set_for_txatt(42.5, 2365)
    print(fsv.get_power(42.5, 2365))
    # fsv.get_EVM('TDD',2350)
    fsv.close_inst()
