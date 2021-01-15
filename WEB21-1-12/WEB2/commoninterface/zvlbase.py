#! encoding = utf-8

import logging

import time
import visa

from .instrument import InstBase

logger = logging.getLogger('ghost')


class ZVLBase(InstBase):
    def __init__(self):
        InstBase.__init__(self, 'ZVL')

    def reset_zvl(self):
        zvlhandle = self.handle
        if zvlhandle:
            zvlhandle.timeout = 2000
            zvlhandle.set_visa_attribute(visa.constants.VI_ATTR_TERMCHAR, 10)
            zvlhandle.set_visa_attribute(visa.constants.VI_ATTR_TERMCHAR_EN, True)
            zvlhandle.write_termination = '\n'
            # zvlhandle.write('*RST')
            zvlhandle.write('*CLS;*OPC?')

            self.ext_error_checking()
            zvlhandle.write('INIT:CONT ON')
            zvlhandle.write('INST:SEL NWA')
            zvlhandle.write('SYST:DISP:UPD ON')
            zvlhandle.write('SYST:ERR:DISP ON')
            self.set_pwr(-10)

    def new_setup(self, setupn):
        try:
            setupname = 'set{}'.format(setupn)
            zvlhandle = self.handle
            zvlhandle.write("MEM:DEF '{}'".format(setupname))
            zvlhandle.write("MEM:SEL '{}'".format(setupname))  # 选择新的setup
        except:
            errors = 'new_setup error'
            logger.error(errors)

    def query_name(self):
        try:
            zvlhandle = self.handle
            text = zvlhandle.query('*IDN?')
            return text.strip()
        except:
            return 'N.A.'

    def set_pwr(self, value):
        try:
            zvlhandle = self.handle
            zvlhandle.write('SOUR:POW {}'.format(value))
        except:
            errors = 'set_pwr error'
            logger.error(errors)

    def set_freq(self, start, stop):
        '''
        默认单位是HZ
        :param zvlhandle:
        :param start: str,'1GHz'
        :param stop: str,'3GHz'
        :return:
        '''
        try:
            # zvlhandle.write('FREQ:STAR {}'.format(start))
            # zvlhandle.write('FREQ:STOP {}'.format(stop))
            zvlhandle = self.handle
            zvlhandle.write('FREQ:STAR {};STOP {}'.format(start, stop))
            # zvlhandle.ext_error_checking()
        except:
            errors = 'set_freq error'
            logger.error(errors)

    def set_freq_span(self, center, span):
        '''

        :param zvlhandle:
        :param center: str
        :param span: str 1GHz
        :return:
        '''
        try:
            zvlhandle = self.handle
            zvlhandle.write('FREQ:CENT {}'.format(center))
            zvlhandle.write('FREQ:SPAN {}'.format(span))
        except:
            errors = 'set_freq_span error'
            logger.error(errors)

    def add_trace(self, n, means, form):
        '''
      增加trace
        :param zvlhandle:
        :param n: 1,2,3
        :param means: str,S11,S21,S12,S22
        form:str,SWR,MLOG
        :return:
        '''
        try:
            zvlhandle = self.handle
            zvlhandle.write("CALC:PAR:SDEF 'Trc{}','{}'".format(n, means))
            zvlhandle.write("CALC:FORM {}".format(form))
            zvlhandle.write("DISP:WIND:TRAC{}:FEED 'Trc{}'".format(n, n))  # 显示到界面
        except:
            errors = 'add_trace error'
            logger.error(errors)

    def delete_trace(self, n):
        try:
            zvlhandle = self.handle
            zvlhandle.write("CALC:PAR:DEL 'Trc{}'".format(n))
        except:
            errors = 'delete_trace error'
            logger.error(errors)

    def change_trace_meas(self, tracen, meas):
        '''

        :param zvlhandle:
        :param tracen:
        :param meas: str,'S11','S12','S22','S21'
        :return:
        '''
        try:
            zvlhandle = self.handle
            zvlhandle.write("CALC:PAR:SEL 'Trc{}'".format(tracen))
            zvlhandle.write("CALC:PAR:MEAS 'Trc{}','{}'".format(tracen, meas))
        except:
            errors = 'change_trace_meas error'
            logger.error(errors)

    def set_ref_value(self, tracen, value):
        '''
        设置参考值
        :param zvlhandle:
        :param tracen: 1,2,3
        :param value:
        :return:
        '''
        try:
            zvlhandle = self.handle
            zvlhandle.write("CALC:PAR:SEL 'Trc{}'".format(tracen))
            zvlhandle.write('DISP:WIND:TRAC{}:Y:RLEV {}'.format(tracen, value))
        except:
            errors = 'set_ref_value error'
            logger.error(errors)

    def set_div_value(self, tracen, value):
        '''
        设置每一格大小
        :param zvlhandle:
        :param tracen: 1,2,3
        :param value:
        :return:
        '''
        try:
            zvlhandle = self.handle
            zvlhandle.write("CALC:PAR:SEL 'Trc{}'".format(tracen))
            zvlhandle.write('DISP:WIND:TRAC{}:Y:PDIV {}'.format(tracen, value))
        except:
            errors = 'set_div_value error'
            logger.error(errors)

    def set_trace_form(self, tracen, value):
        '''
        设置trace的显示形式
        :param zvlhandle:
        :param tracen: 1,2,3
        :param value: str,SWR,MLIN,MLOG,PHAS,UPH,POL,SMITH
        :return:
        '''
        try:
            zvlhandle = self.handle
            zvlhandle.write("CALC:PAR:SEL 'Trc{}'".format(tracen))
            zvlhandle.write('CALC:FORM {}'.format(value))
        except:
            errors = 'set_trace_form error'
            logger.error(errors)

    def set_trace_marker(self, tracen, markern, x):
        '''
        设置trace的标记
        :param zvlhandle:
        tracen:1,2,3
        :param markern: 1,2,3
        :param x:str,1GHz
        :return:
        '''
        try:
            zvlhandle = self.handle
            zvlhandle.write("CALC:PAR:SEL 'Trc{}'".format(tracen))
            zvlhandle.write('CALC:MARK{} ON'.format(markern))  # create marker
            time.sleep(0.1)
            zvlhandle.write('CALC:MARK{}:X {}'.format(markern, x))
        except:
            errors = 'set_trace_marker error'
            logger.error(errors)

    def create_max_marker(self, tracen, markern):
        try:
            zvlhandle = self.handle
            zvlhandle.write("CALC:PAR:SEL 'Trc{}'".format(tracen))
            zvlhandle.write('CALC:MARK{} ON'.format(markern))
            time.sleep(0.1)
            zvlhandle.write('CALC:MARK{}:FUNC:EXEC MAX'.format(markern))
            self.ext_error_checking()
        except:
            errors = 'create_max_marker error'
            logger.error(errors)

    def create_min_marker(self, tracen, markern):
        try:
            zvlhandle = self.handle
            zvlhandle.write("CALC:PAR:SEL 'Trc{}'".format(tracen))
            zvlhandle.write('CALC:MARK{} ON'.format(markern))
            time.sleep(0.1)
            zvlhandle.write('CALC:MARK{}:FUNC:EXEC MIN'.format(markern))
            self.ext_error_checking()
            zvlhandle.query('*OPC?')
        except:
            errors = 'create_min_marker error'
            logger.error(errors)

    def query_marker(self, tracen, markern):
        '''
        查询marker位置
        :param zvlhandle:
        :param tracen:
        :param markern:
        :return:x:float 单位Hz
         y:float
        '''
        try:
            zvlhandle = self.handle
            zvlhandle.write("CALC:PAR:SEL 'Trc{}'".format(tracen))
            # markerX = float(zvlhandle.query('CALC:MARK{}:X?'.format(markern)))
            # markerY = float(zvlhandle.query('CALC:MARK{}:Y?'.format(markern)))
            strxy = zvlhandle.query('CALC:MARK{}:FUNC:RES?'.format(markern))
            # zvlhandle.ext_error_checking()
            markerX, markerY = strxy.split(',')
            return float(markerX), float(markerY)
        except:
            errors = 'query_marker error'
            logger.error(errors)

    def remove_allmarker(self, tracen):
        '''
        没有单独的删除某个marker的命令，只有全删
        :param zvlhandle:
        :param tracen:
        :return:
        '''
        try:
            zvlhandle = self.handle
            zvlhandle.write("CALC:PAR:SEL 'Trc{}'".format(tracen))
            zvlhandle.write('CALC:MARK:AOFF')
            time.sleep(0.1)
            self.ext_error_checking()
        except:
            errors = 'remove_allmarker error'
            logger.error(errors)

    def save_screenshot(self, src, dest):
        '''

        :param zvlhandle:
        :param path:str
        :return:
        '''
        try:
            zvlhandle = self.handle
            zvlhandle.write('HCOP:DEV:LANG PNG')
            zvlhandle.write("MMEM:NAME '{}'".format(src))
            zvlhandle.write("HCOP:DEST 'MMEM'")
            zvlhandle.write('HCOP:ITEM:ALL')
            zvlhandle.write('HCOP')
            zvlhandle.query('*OPC?')
            # print('screeshot ing...')
            self.ext_error_checking()
            self.ext_query_bin_data_to_file("MMEM:DATA?  '{}'".format(src), dest)

            zvlhandle.query('*OPC?')
        except:
            errors = 'save_screenshot error'
            logger.error(errors)

    def sel_color(self):
        try:
            zvlhandler = self.handle
            zvlhandler.write('SYST:DISP:COL DBAC')  # DARK background
            zvlhandler.write('SYST:DISP:COL BWS')  # black and white solid
            zvlhandler.write('DISP:CMAP13:RGB 1,0,0,SOLid,2')  # red
            zvlhandler.write('DISP:CMAP14:RGB 0,0,1,SOLid,2')  # blue
            zvlhandler.write('DISP:CMAP:MARK OFF')
            zvlhandler.write('DISP:WIND:TITL ON')
            zvlhandler.write("DISP:WIND:TITL:DATA 'S11&S21'")  # 显示标题
        except:
            errors = 'sel_color error'
            logger.error(errors)

    def auto_scale(self, tracen):
        try:
            zvlhandler = self.handle
            zvlhandler.write("DISP:WIND:TRAC:Y:SCAL:AUTO ONCE,'Trc{}'".format(tracen))
            self.set_div_value(tracen, 10)
        except:
            errors = 'auto scale error'
            logger.error(errors)
