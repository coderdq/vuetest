import logging
from datetime import datetime
from ftplib import FTP
import os
import sys
import time
import socket
import threading

logger = logging.getLogger('ghost')


class MyFTP(object):

    def __init__(self, host, port=21):
        """ 初始化 FTP 客户端
        参数:
                 host:ip地址

                 port:端口号
        """
        try:
            self.host = host
            self.port = port
            self.ftp = FTP()
            # 重新设置下编码方式
            self.ftp.encoding = 'gbk'
            self.login_tag = threading.Event()
            self.login_tag.clear()

        except Exception as e:
            raise ModuleNotFoundError('ftp初始化失败:{}'.format(e))

    def close(self):
        """ 退出ftp
        """
        logger.debug("close()---> FTP退出")
        self.ftp.quit()

    def is_same_size(self, local_file, remote_file):
        """判断远程文件和本地文件大小是否一致
           参数:
             local_file: 本地文件

             remote_file: 远程文件
        """
        try:
            remote_file_size = self.ftp.size(remote_file)
        except Exception as e:
            logger.error(e)
            remote_file_size = -1

        try:
            local_file_size = os.path.getsize(local_file)
        except Exception as e:
            logger.error(e)
            local_file_size = -1

        logger.debug('local_file_size:%d, remote_file_size:%d' % (local_file_size, remote_file_size))
        if remote_file_size == local_file_size:
            return True
        else:
            return False

    def login(self, username, password):
        """ 初始化 FTP 客户端
            参数:
                  username: 用户名

                 password: 密码
            """
        if self.login_tag.is_set():
            logger.debug('has already login ftp server')
            return True
        try:
            timeout = 60
            socket.setdefaulttimeout(timeout)
            # 0主动模式 1 #被动模式
            self.ftp.set_pasv(True)
            # 打开调试级别2，显示详细信息
            # self.ftp.set_debuglevel(2)
            self.ftp.connect(self.host, self.port)
            logger.debug('ftp成功连接到 %s' % self.host)
            self.ftp.login(username, password)
            self.login_tag.set()
            logger.debug('ftp成功登录到 %s' % self.host)
            return True
        except Exception as err:
            logger.error("FTP 连接或登录失败 ，错误描述为：%s" % err)
            self.login_tag.clear()
            return False

    def rpt_upgrade(self, local_file, bb_remote_file, arm_remote_file):
        '''
        上传升级文件
        local_file:[bb_file,arm_file]
        :return:
        '''
        i = 0
        logger.debug('local_file={}'.format(local_file))
        bb_file, arm_file = local_file
        errflg = False
        while 1:
            self.login('', '')
            if self.login_tag.is_set():
                if arm_remote_file is not None:
                    if not self.upload_file(arm_file, arm_remote_file):
                        logger.error('升级ARM失败')
                        errflg = True
                if bb_remote_file is not None:
                    if not self.upload_file(bb_file, bb_remote_file):
                        logger.error('升级BB失败')
                        errflg = True
                if errflg:
                    self.login_tag.clear()  #清除登录标志
                else:
                    return True
            i = i + 1
            if i > 10:
                break
            time.sleep(3)
        logger.error('升级失败')
        return False

    def get_file(self,path):
        '''
        获取当前目录下的文件列表
        :param path:
        :return:
        '''
        self.ftp.cwd(path)
        filedirlist=[]
        filelist=[]
        self.ftp.retrlines('LIST',filedirlist.append)
        for f in filedirlist:
            if f.startswith('d'):
                pass
            else:
                filelist.append(str(f).split()[-1])
        return filelist

    def upload_file(self, local_file, remote_file):
        """从本地上传文件到ftp

           参数:
             local_path: 本地文件

             remote_path: 远程文件
        """
        try:
            if not os.path.isfile(local_file):
                logger.error('%s 不存在' % local_file)
                return False

            dir = os.path.dirname(remote_file)
            remote_file_name = os.path.basename(remote_file)
            self.ftp.cwd(dir)  # 进入远程目录
            try:
                for file in self.get_file(dir):
                    if file.endswith('.tmp'):
                        self.ftp.delete(file)
                        logger.debug('delete tmp文件')
            except Exception as e:
                logger.error(e)
            # if  not local_file.endswith('.pkg'):
            #     logger.error('本地文件非pkg文件')
            #     return False
            logger.info('ftp上传开始,请等待大约1分钟')
            buf_size = 1024
            file_tmp_remote = '{}_{}.tmp'.format(str(datetime.now()), str(remote_file_name))
            file_final_remote = remote_file_name
            with open(local_file, 'rb') as fp:
                self.ftp.storbinary('STOR %s' % file_tmp_remote, fp, buf_size)
                self.ftp.rename(file_tmp_remote, file_final_remote)
                logger.debug('remote file:' + file_final_remote)
            logger.info('上传: %s' % local_file + "成功!")
            if not self.is_same_size(local_file, remote_file):
                logger.error('上传文件不相等: %s' % remote_file)
                return False
            return True
        except Exception as e:
            logger.error(e)
            return False

    def upload_file_tree(self, local_path, remote_path):
        """从本地上传目录下多个文件到ftp
           参数:

             local_path: 本地路径

             remote_path: 远程路径
        """
        if not os.path.isdir(local_path):
            logger.error('本地目录 %s 不存在' % local_path)
            return

        self.ftp.cwd(remote_path)
        logger.debug('切换至远程目录: %s' % self.ftp.pwd())

        local_name_list = os.listdir(local_path)
        for local_name in local_name_list:
            src = os.path.join(local_path, local_name)
            if os.path.isdir(src):
                try:
                    self.ftp.mkd(local_name)
                except Exception as err:
                    logger.error("目录已存在 %s ,具体错误描述为：%s" % (local_name, err))
                logger.debug("upload_file_tree()---> 上传目录： %s" % local_name)
                self.upload_file_tree(src, local_name)
            else:
                logger.debug("upload_file_tree()---> 上传文件： %s" % local_name)
                self.upload_file(src, local_name)
        self.ftp.cwd("..")


if __name__ == "__main__":
    my_ftp = MyFTP("192.254.1.132")
    my_ftp.login("", "")
    # 上传目录
    my_ftp.upload_file("F:/升级包/FemtoBS8125_SW1.0.8B4.union.pkg", "/tmp/femto.pkg")

    my_ftp.close()
