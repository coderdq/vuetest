'''
信号源，网口控制,测试灵敏度需要用到
'''

import time
import logging
from commoninterface.smbvbase import SMBVBase

logger = logging.getLogger('ghost')


class SMBV(SMBVBase):
    def __init__(self):
        SMBVBase.__init__(self)





if __name__ == '__main__':
    smbv = SMBV()
    smbv.init_smbv('192.168.1.12')
    smbv.set_smbv()
    smbv.reset_smbv()
    smbv.set_for_max_power(2350)

    smbv.set_level(-19.8)
