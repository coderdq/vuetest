# coding:utf-8
import os
import logging

import time
from celery.utils.log import get_task_logger
from asgiref.sync import async_to_sync
from t2kmachine.common.handle_board import BT2KHandler
from .ftp_client import MyFTP

logger = get_task_logger('ghost')


class DOUpgrade(object):
    def __init__(self,chl_name,chl_layer):
        self.bd = None
        self.upload_tag = False
        self.upgrade_success_tag = False
        self.channel_name = chl_name
        self.channel_layer = chl_layer

    def rpt_message(self, msg):
        try:
            if self.channel_layer and self.channel_name:
                print('rpt_msg')
                async_to_sync(self.channel_layer.send)(
                    self.channel_name,
                    {
                        "type": "send.message",
                        "message": msg
                    }
                )
        except Exception as e:
            print('rpt_msg error:{}'.format(e))

    def init_all(self, bdconf):
        try:
            ip = bdconf['IP']  # 板子的IP
            if ip is None:
                return False
            bb_path = bdconf.get('BB_PATH', '')  # 待升级的文件路径
            arm_path = bdconf.get('ARM_PATH', '')
            bb_file_name = None
            arm_file_name = None
            if bb_path:
                bb_file_name = os.path.basename(bb_path)
            if bb_file_name and not bb_file_name.endswith('pkg'):
                raise IOError('升级包非pkg')
            self.bd = BT2KHandler(**bdconf)
            if arm_path:
                arm_file_name = os.path.basename(arm_path)
            if arm_file_name and not arm_file_name.endswith('.tar'):
                raise IOError('arm非tar包')
            print('do_test..')
            ret = self.do_test(ip, bb_path, arm_path)
            self.rpt_message('测试完成OK')
            return ret
        except Exception as e:
            logger.error(e)
            self.rpt_message('ERROR:{}'.format(e))
            return False

    def start_upgrade(self, arm_file_name, bb_path):
        '''
        基带板升级
        :return:
        '''

        if self.upload_tag:
            if arm_file_name:
                # self.bd.do_clear_arm()
                ipstr = '192.168.1.4'
                if self.bd.do_untar_arm(arm_file_name):
                    self.bd.do_chmod_armtar(ipstr)
            self.bd.do_modify_boardinfo()
            if bb_path:
                if self.bd.do_upgrade():
                    self.upgrade_success_tag = True
                    return True
                else:
                    self.upload_tag = False
                    return False
            else:
                self.bd.do_reboot()
            self.upgrade_success_tag = True
            return True
        else:
            logger.debug('wait上传')
            self.rpt_message('INFO:wait上传')
            time.sleep(10)

    def do_test(self, ip, bb_path, arm_path):
        '''
        升级，先开ftpserver,再传ftp文件升级
        :param ip:
        :param path:
        :return:
        '''
        i = 0
        while True:
            i = i + 1
            if i > 3:
                break
            if self.upgrade_success_tag:
                break
            # 开启基带板ftp
            if not self.bd.do_ftp():
                logger.error('基带板start ftp server failed')
                self.rpt_message('ERROR:基带板start ftp server failed')
                time.sleep(20)
                continue
            # 连接ftp，上传升级文件
            time.sleep(1)
            myftp = MyFTP(str(ip))
            if bb_path:
                bb_remote_file = '/tmp/femto.pkg'
            else:
                bb_remote_file = None
            arm_remote_file = None
            arm_file_name = ''
            if arm_path:
                arm_file_name = os.path.basename(arm_path)
                arm_remote_file = '/mnt/flash/{}'.format(arm_file_name)
                logger.debug(arm_remote_file)
                self.rpt_message('INFO:{}'.format(arm_remote_file))

            paths = [bb_path, arm_path]

            if myftp.rpt_upgrade(paths, bb_remote_file, arm_remote_file):
                logger.info('ftp上传文件成功')
                self.rpt_message('INFO:ftp上传文件成功')
                self.upload_tag = True
                time.sleep(1)
            else:
                logger.error('ftp上传文件失败')
                self.rpt_message('ERROR:ftp上传文件失败')
                self.upload_tag = False
                continue

            flag = self.start_upgrade(arm_file_name, bb_path)
            if flag:
                logger.info('升级命令执行成功')
                self.rpt_message('INFO:升级命令执行成功')
                break

            time.sleep(30)
        if self.upgrade_success_tag:
            return True  # 升级不确认

        return False

    def check_result(self, bb_path):
        '''
        检查ps中升级是否成功
        :return:
        '''
        # logger.info('等待重启,等待约8分钟..')
        # time.sleep(480)
        time.sleep(3)
        bb_file_name = os.path.basename(bb_path)
        idx1 = bb_file_name.find('SW') + len('SW')
        idx2 = bb_file_name.find('.pkg')
        key = bb_file_name[idx1:idx2]
        logger.debug('process key={}'.format(key))
        process_name = self.bd.do_get_process_name()
        logger.debug('process_name={}'.format(process_name))
        if process_name:
            if key in process_name:
                logger.info('升级成功')
                return True
        return False

    def wait_and_check(self, bdip):
        state = True
        new_state = state
        cmd = 'ping -n 6 -w 100 {}'.format(bdip)
        i = 0
        while 1:
            logger.debug('time')
            ret = os.system(cmd)
            if ret:
                # 没ping通
                logger.debug('第{}次'.format(i))
                logger.debug('ping failed')
                new_state = False
            else:
                new_state = True
            if state and not new_state:
                logger.debug('reboot1...')
                return True
            elif not state and not new_state:
                logger.debug('reboot2...')
                return True
            state = new_state
            time.sleep(15)
            i = i + 1
            if i > 40:  # 超过10分钟一直都ping的通则未重启，则升级失败
                logger.debug('ping always ok..')
                return False
