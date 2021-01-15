'''
连接高低温箱，作为modbus master
'''
import time
import serial
import logging
from functools import wraps

import modbus_tk.defines as cst
from modbus_tk import modbus_rtu

'''
地址
'''
SLAVE_ADDR = 0x01  # 从机地址
CONTROL_MODE_ADDR = 1204
RUN_MODE_ADDR = 1000
POWER_FAILURE_MODE_ADDR = 1011
TEMP_PV_ADDR = 536  # 当前值
TEMP_SV_ADDR = 1870  # 设定值
START_ADDR1 = 212
START_ADDR2 = 1200
STOP_ADDR1 = 213
STOP_ADDR2 = 1200

ON_VALUE = 0xFF00
OFF_VALUE = 0

logger = logging.getLogger('ghost')


def handle_excep(func):
    @wraps(func)
    def with_handle(self, *args, **kwargs):
        i = 0
        while 1:
            if i > 3:
                raise StopIteration('handle thdevice error')
            ret = func(self, *args, **kwargs)
            if ret is False or ret is None:
                # 重连
                logger.error('thdevice reconnect')
                del self.master
                self.master = None
                time.sleep(1)
                self.connect_th(self.port)
                i = i + 1
                continue
            return ret

    return with_handle


class THDevice(object):
    def __init__(self):
        self.master = None
        self.port = None

    def connect_th(self, PORT):
        '''
        连接高低温箱
        :return:
        '''
        try:
            self.master = modbus_rtu.RtuMaster(serial.Serial(port=PORT, baudrate=9600, bytesize=8, parity='N',
                                                             stopbits=1, xonxoff=0))
            self.master.set_timeout(5.0)
            self.master.set_verbose(True)
            self.port = PORT
        except Exception as e:
            self.master = None
            logger.error('modbus connect error')
            raise StopIteration('modbus connect error:{}'.format(e))

        return True

    @handle_excep
    def set_fixed_mode(self):
        '''
        定值模式
        :return:
        '''
        try:
            # 运行方式 ON:定值，OFF：程式
            self.master.execute(SLAVE_ADDR, cst.WRITE_SINGLE_COIL, RUN_MODE_ADDR, 1, ON_VALUE)
            # 控制方式，ON:温度，OFF:温湿度
            self.master.execute(SLAVE_ADDR, cst.WRITE_SINGLE_COIL, CONTROL_MODE_ADDR, 1, ON_VALUE)
            # 停电方式，ON:停止关
            self.master.execute(SLAVE_ADDR, cst.WRITE_SINGLE_COIL, POWER_FAILURE_MODE_ADDR, 1, ON_VALUE)
            return True
        except Exception as e:
            # raise StopIteration('set_mode error {}'.format(e))
            # raise StopIteration('set_mode')
            return False

    @handle_excep
    def get_temp_pv(self):
        '''
        读取温度当前值
        :return:10*温度值
        '''
        try:
            current_value, = self.master.execute(SLAVE_ADDR, cst.READ_HOLDING_REGISTERS, TEMP_PV_ADDR, 1)  # 温度*10的值
            signed_pv = self.sxtn(current_value)
            return signed_pv
        except Exception as e:
            logger.error('get_temp_pv error {}'.format(e))
            return None

    @handle_excep
    def set_temp_sv(self, sv):
        '''
        设置温度设定值,温箱最低温度设置-70度,最高120度
        :param sv: 要设置的温度再乘以10
        :return:
        '''
        if sv < -700:
            sv = -700
        if sv > 12000:
            sv = 12000
        logger.debug('set_temp_sv {}'.format(sv))
        try:
            self.master.execute(SLAVE_ADDR, cst.WRITE_SINGLE_REGISTER, TEMP_SV_ADDR, 1, sv)
            return True
        except Exception as e:
            logger.error(e)
            return False
            # raise StopIteration('set_temp_sv error:{}'.format(e))

    @handle_excep
    def get_temp_sv(self):
        '''
        读取温度设定值
        :return:10*温度值
        '''
        try:
            sv, = self.master.execute(SLAVE_ADDR, cst.READ_HOLDING_REGISTERS, TEMP_SV_ADDR, 1)
            signed_sv = self.sxtn(sv)
            return signed_sv
        except Exception as e:
            return None
            # raise StopIteration('get_temp_sv error:{}'.format(e))

    def sxtn(self, a):
        '''
        将16进制数转成有符号整数
        :param a:
        :return:
        '''
        return ((a + 0x8000) & 0xffff) - 0x8000

    @handle_excep
    def start_dev(self):
        '''
        启动设备
        :return:
        '''
        try:
            self.master.execute(SLAVE_ADDR, cst.WRITE_SINGLE_COIL, START_ADDR1, 1, ON_VALUE)
            self.master.execute(SLAVE_ADDR, cst.WRITE_SINGLE_COIL, START_ADDR2, 1, ON_VALUE)
            return True
        except Exception as e:
            logger.error('start_dev error:{}'.format(e))
            return False

    def stop_dev(self):
        try:
            self.master.execute(SLAVE_ADDR, cst.WRITE_SINGLE_COIL, STOP_ADDR1, 1, ON_VALUE)
            self.master.execute(SLAVE_ADDR, cst.WRITE_SINGLE_COIL, STOP_ADDR2, 1, OFF_VALUE)
        except Exception as e:
            logger.error('stop_dev error:{}'.format(e))
            return False
        return True


if __name__ == '__main__':
    dev = THDevice()
    dev.connect_th('COM5')
    time.sleep(10)
    # dev.set_fixed_mode()
    # dev.start_dev()
    print(dev.get_temp_pv())
    # dev.set_temp_sv(140)
    dev.stop_dev()
