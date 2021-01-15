import logging
import telnetlib
import time
import re

logger = logging.getLogger('ghost')


class TelnetClient(object):
    def __init__(self):
        self.tn = telnetlib.Telnet()

    def execute_some_command(self, command):
        self.tn.write(command.encode('ascii') + b'\n')
        time.sleep(1)
        # 忽略中文
        command_result = self.tn.read_very_eager().decode('ascii', 'ignore')
        # logger.debug('***命令执行结果:%s******' % command_result)
        return command_result

    def execute_enter(self):
        '''
        按下enter键
        :return:
        '''
        self.tn.write(b'\n')
        time.sleep(2)
        ret = self.tn.read_very_eager().decode('ascii', 'ignore')
        i = 0
        while True:
            ret = ret.strip('\n\r').strip()
            if ret.startswith('#'):
                logger.info('telnet命令输入界面激活成功')
                break
            if i > 10:
                raise IOError('can not activate..')
            logger.info('telnet命令输入界面激活失败')
            time.sleep(10)
            self.tn.write(b'\n')
            time.sleep(1)
            ret = self.tn.read_very_eager().decode('ascii', 'ignore')
            i = i + 1

    def logout_host(self):
        self.tn.write(b'exit\n')
        time.sleep(.5)


class Ctrl_BOARD(TelnetClient):
    def __init__(self):
        TelnetClient.__init__(self)

    def check_ps(self, *args):
        '''
        传入进程关键字
        8125的关键字 ./MGR.EXE 和/Product_lte_tdd.o 56 60 1.0.8B6.union的进程号
        :return:
        '''
        ret = self.execute_some_command('ps')  # 返回str
        lines = ret.split('\r\n')  # 按行分割的列表
        process_id_list = []
        for process in args:
            for eachline in lines:
                if process in eachline:
                    line_list = eachline.split()  # 可分割任意个空白字符
                    process_id_list.append(line_list[0])
        return process_id_list

    def get_process_name(self, keyword):
        '''
        根据关键字获得进程的名字
        :return:
        '''
        ret = self.execute_some_command('ps')  # 返回str
        lines = ret.split('\r\n')  # 按行分割的列表
        process_name = ''
        for eachline in lines:
            if keyword in eachline:
                line_list = eachline.split()  # 可分割任意个空白字符
                process_name = line_list[-1]
        return process_name

    def pad_process(self, *args):
        '''
        起进程,传入进程号
        :return:
        '''
        for process_id in args:
            command = 'pad {}'.format(process_id)
            logger.debug(command)
            self.execute_some_command(command)

    def exit(self):
        self.execute_some_command('exit')

    def get_txatt(self, cellid=None):
        '''
        T2K有cellid，0--小区0  2---小区1
        查询txatt,读取内容为 TxAtten=6.0dB//有时候TxAtten=0(0x0)
        :return:返回  int dB
        '''
        try:
            keyword = 'TxAtten'
            regex = re.compile('\d+')
            cmd = 'txatt'
            if cellid is None:
                cmd = 'txatt'
            elif int(cellid) == 0:
                cmd = 'txatt {}'.format(int(cellid))
            elif int(cellid) == 1:
                cmd = 'txatt {}'.format(int(cellid) + 1)

            logger.debug(cmd)
            txatt = self.execute_some_command(cmd)
            # logger.debug('txatt ret={}'.format(txatt))
            if keyword in txatt:
                linelst = txatt.split('\r\n')
                for line in linelst:
                    if not line:
                        continue
                    if keyword in line:
                        _, value = [tmp.strip() for tmp in line.strip().split('=')]
                        txatt_value = regex.findall(value)[0]
                        return int(txatt_value)
        except Exception as e:
            raise ValueError('read txatt error :{}'.format(e))
        else:
            return None

    def set_class1(self, *args):
        '''
        设置一类参数 中心频率,带宽，功率级别，PCI,PLMN,TAC,
        :return:
        '''
        class_str = ','.join([str(arg) for arg in args])
        self.execute_some_command('FT_PARA_Class1Set {}'.format(class_str))

    def kill_arm(self):
        '''
        杀掉arm程序
        :return:
        '''
        try:
            ret = self.execute_some_command('ps')  # 返回str
            lines = ret.split('\r\n')  # 按行分割的列表
            process_id_list = []
            process = 'synway_arm'
            for eachline in lines:
                if process in eachline:
                    line_list = eachline.split()  # 可分割任意个空白字符
                    process_id_list.append(line_list[0])
            logger.debug(process_id_list)
            if len(process_id_list) > 0:
                cmd = 'kill -9 {}'.format(' '.join(process_id_list))
                self.execute_some_command(cmd)
                time.sleep(2)
            return True
        except Exception as e:
            logger.error(e)
            return False


class Ctrl_8125(Ctrl_BOARD):
    username = '/ushell'
    password = 'zte'

    def __init__(self):
        Ctrl_BOARD.__init__(self)

    def login_host(self, host_ip):
        '''
        telnet连接主片
        :param host_ip:
        :return:
        '''
        try:
            if hasattr(self, 'tn'):
                try:
                    self.tn.close()
                except:
                    pass
                del self.tn
            logger.debug('telnet..')
            self.tn = telnetlib.Telnet()
            self.tn.open(host_ip, port=23, timeout=5)

        except:
            logger.error('telnet连接{}失败'.format(host_ip))
            self.tn.close()
            del self.tn
            self.tn = telnetlib.Telnet()
            return False
        else:
            return True

    def login_baseboard(self):
        '''
        登录基带板/登录主片ushell
        :return:
        '''
        self.tn.write(Ctrl_8125.username.encode('ascii') + b'\n')
        time.sleep(1)
        self.tn.read_until(b'input password', timeout=10)
        self.tn.read_very_eager().decode('ascii', 'ignore')
        time.sleep(1)
        self.tn.write(Ctrl_8125.password.encode('ascii') + b'\n')
        time.sleep(1)
        command_result = self.tn.read_very_eager().decode('ascii', 'ignore')
        # logger.debug('login ushell reply={}'.format(command_result))
        if 'input password' in command_result:
            self.tn.write(Ctrl_8125.password.encode('ascii') + b'\n')
            time.sleep(2)
            command_result = self.tn.read_very_eager().decode('ascii', 'ignore')
            logger.debug('again login ushell reply={}'.format(command_result))
            if 'success' not in command_result:
                logger.warning('登录ushell失败')
                return False
            else:
                logger.warning('登录ushell成功')
                return True
        elif 'success' in command_result:
            logger.warning('登录ushell成功')
            return True
        elif '$$' in command_result:
            logger.warning('登录ushell成功')
            return True
        else:
            logger.warning('登录ushell失败')
            return False

    def check_cell_state(self, cellid=None):
        '''
        查看小区状态 2表示小区建立了
        :return:
        '''
        try:
            keyword = 'ucCellState'
            keyword1 = 'ucCellOpr'
            keyword2 = 'ucOprType'
            keyvalue = '2'
            keyvalue1 = '0'
            keyvalue2 = '0'
            cellstate = self.execute_some_command('CcmDbgShowCell')

            if keyword in cellstate:
                linelst = cellstate.split('\r\n')
                for line in linelst:
                    if not line:
                        continue
                    if keyword + ':' in line:
                        # logger.debug('cell line={}'.format(line))
                        cell_dict = self.str_2_dict(line)
                        if cell_dict:
                            logger.debug('cell_dict={}'.format(cell_dict))
                            uccellstate = cell_dict[keyword]
                            cellopr = cell_dict[keyword1]
                            oprtype = cell_dict[keyword2]
                            if uccellstate == keyvalue and cellopr == keyvalue1 and \
                                    oprtype == keyvalue2:
                                logger.info('小区建立成功')
                                return True
                        break
        except Exception as e:
            logger.error('check_cell_state error :{}'.format(e))
            self.exit()
            return False
        else:
            return False

    def str_2_dict(self, strdict):
        try:
            ret_dict = {}
            a = [tmp.strip() for tmp in strdict.strip().strip(';').split(',')]
            for item in a:
                if item:
                    key_value = [tmp.strip() for tmp in item.split(':')]
                    ret_dict[key_value[0]] = key_value[1]
            return ret_dict
        except Exception as e:
            logger.error('str_2_dict error:{}'.format(e))
            return None

    def repeat_check_cell_state(self, cellid=None):
        '''
        重复10次检测小区，每隔1分钟检测一次
        :return:
        '''
        n = 0
        MAX = 14
        INTERVAL = 30
        flag = False
        try:
            while 1:
                logger.info('begin to check_cell_state  every minute...')
                flag = self.check_cell_state(cellid)
                if flag:
                    logger.debug('cell is ok...')
                    break
                n = n + 1
                if n > MAX:
                    logger.error('build cell failed')
                    self.execute_some_command('exit')
                    self.execute_some_command('reboot')
                    self.execute_some_command('reboot')
                    break
                time.sleep(INTERVAL)
        except Exception as e:
            logger.error(e)
            return False
        return flag

    def query_class1_para(self, cellid=None):
        '''
        查询一类参数
        基带板返回值

******** Param Query Result ********

 - WorkMode                =    10.
 - CenterFreq              = 40936.
 - SysBandWidth            =     0.
 - CellSpeRefSigPwr        =     0.
 - PhyCellId               =    88.
 - PLMNID                  = 46000.
 - TAC                     =   212.
 - SubFrameAssignment      =     2.
 - SpecialSubframePatterns =     7.
 - dwParamFrameOff         =     0.

*************Param Query Result End*********
        :return:
        '''
        try:
            allstr = self.execute_some_command('FT_PARA_ParaQuery')
            # logger.debug(allstr)
            linelist = allstr.split('\r\n')
            keywords = ['CenterFreq', 'SysBandWidth', 'CellSpeRefSigPwr', 'PhyCellId',
                        'PLMNID', 'TAC', 'SubFrameAssignment', 'SpecialSubframePatterns']
            para_dict = {}
            for line in linelist:
                if not line or line.startswith('#'):
                    continue
                for keyword in keywords:
                    if keyword in line and '=' in line:
                        _, value = line.strip().split('=')
                        if value is not None:
                            para_dict.setdefault(keyword.strip(), value.strip().strip('.'))
                            break
            if len(para_dict) == len(keywords):
                retlist = [para_dict[key] for key in keywords]
                return retlist

        except Exception as e:
            raise ValueError('query_class1_para error:{}'.format(e))
        else:
            return None

    def config_ip(self, *args):
        '''
        修改主从片ip
        :return:
        '''
        bip_str = ','.join(["\"" + "255.0.0.0" + "\"", "\"" + "192.168.1.1" + "\""])
        for idx, ip_str in enumerate(args):
            if not ip_str:
                continue
            liststr = "\"" + ip_str + "\"" + "," + bip_str
            command = 'BspIfConfig ' + str(idx) + ',' + liststr
            logger.debug('bspifconfig={}'.format(command))
            self.tn.write(command.encode('ascii') + b"\n")

    def set_arm_conf(self, ip):
        command = 'SetArmCfgInfo ' + "\"" + str(ip) + "\"" + ',' + '30010'
        logger.debug(command)
        ret_str = self.execute_some_command(command)
        if str(ip) in ret_str and 'success' in ret_str:
            return True
        else:
            return False

    def set_mode(self, *args):
        '''
        设置主从片制式
        :param args: 主片制式，从片制式，主片频段，从片频段
        :return:
        '''
        try:
            mod_str = ','.join([str(arg) for arg in args])
            cmd = 'FT_SYS_LTEModeSet {}'.format(mod_str)
            logger.debug('set_mode cmd={}'.format(cmd))
            retstr = self.execute_some_command(cmd)  # 有时候没有回复，只能默认成功了
            keyword = 'SendSysRspWithoutData'
            regex = re.compile(keyword, flags=re.IGNORECASE)
            linelist = retstr.split('\r\n')
            flag = True
            for line in linelist:
                line = line.strip().strip('.')
                if regex.search(line):
                    result = line.split(':')[1].strip()  # 输出1竟然带空格了
                    if result in [1, '1']:
                        flag = True
                    else:  # result=2/3/0都是失败
                        flag = False
                    break
            return flag
        except Exception as e:
            raise NotImplementedError('set_mode error')

    def telnet_board(self, ipstr):
        '''
        从主片telnet登录从片
        :param ipstr:
        :param username:
        :param password:
        :return:
        '''
        # ret_str=self.execute_some_command('telnet {}'.format(ipstr))
        # print(ret_str)
        # logger.debug(ret_str)
        # self.execute_enter()
        if not ipstr:  # 从片IP为空
            return False
        time.sleep(3)
        command = 'telnet {}'.format(ipstr)
        self.tn.write(command.encode('ascii') + b'\n')
        time.sleep(1)
        data = self.tn.read_until(b'Entering', timeout=20)
        ret_str = data.decode(errors='ignore')
        # ret_str = self.tn.read_very_eager().decode('ascii', 'ignore')
        # logger.debug(ret_str)
        if not ret_str:
            logger.error('open {} error'.format(ipstr))
            return False
        if "can't connect" in ret_str:
            logger.error('open {} error'.format(ipstr))
            return False
        elif 'Entering' in ret_str:
            logger.info('telnet连接{}成功'.format(ipstr))
            return True
            # logger.debug('login FDD')
            # flag=self.login_baseboard()
            # if flag:
            #      logger.error('登录基带板{}成功'.format(ipstr))
            # else:
            #      logger.info('登录基带板{}失败'.format(ipstr))
            # return flag
        else:
            return False
            # self.execute_some_command(self.username)
            # login_ret = self.execute_some_command(self.password)
            # if 'success' not in login_ret:
            #     logger.error('登录基带板{}失败'.format(ipstr))
            #     return False
            # else:
            #     logger.info('登录基带板{}成功'.format(ipstr))
            #     return True

    def set_txatt(self, cellid, txatt):
        '''
        设置衰减

        :param value:dB
        :return:
        '''
        value = float(txatt) * 100

        logger.debug('board txatt={}'.format(value))
        self.execute_some_command('BspSetTxAtt 0,{}'.format(value))
        # self.execute_some_command('BspSetTxAtt 1,{}'.format(value))

    def set_rf(self, onoff):
        '''
            设置射频开关
            onoff:0:关闭，1：打开
            :return:
        '''
        cmd = 'FT_SYS_RFStatusSet {}'.format(onoff)
        logger.debug(cmd)
        self.execute_some_command(cmd)

    def get_boardinfo(self):
        '''
        读取配置文件中主从片的band设置
        MasterWorkMode,SlaveWorkMode:0/1->TDD/FDD
        MasterFunId,SlaveFunId:0:移动E段,1：移动D段,2：移动F段,3：联通B1,4:电信B3,5:B41,6:B5,7:B8
        :return:[]字符串列表
        '''
        # self.execute_enter()
        time.sleep(1)
        try:
            keywords = ['MasterWorkMode', 'SlaveWorkMode', 'MasterFunId', 'SlaveFunId']
            self.execute_some_command('cd /mnt/flash/Ru')
            allstr = self.execute_some_command('cat RruInfo.txt')
            linelist = allstr.split('\r\n')
            band_dict = {}
            for line in linelist:
                if not line or line.startswith('#'):
                    continue
                for keyword in keywords:
                    if keyword in line and '=' in line:
                        # logger.debug('boardinfo line={}'.format(line))
                        _, value = line.strip().split('=')
                        band_dict.setdefault(keyword.strip(), value.strip())
                        break
            if len(band_dict) == len(keywords):
                retlist = [band_dict[key] for key in keywords]
                logger.debug('boardinfo={}'.format(retlist))
                return retlist

        except Exception as e:
            raise ValueError('get_boardinfo error:{}'.format(e))
        else:
            return None

    def set_power_compensation(self, curpower, targetpower):
        '''
        必须参数是Int
        :param curpower: int
        :param targetpower: int
        :return:
        '''
        cmd = 'FT_TEST_PowerCompensationSet {},{}'.format(curpower, targetpower)
        logger.debug('power_comp_cmd={}'.format(cmd))
        self.execute_some_command(cmd)

    def get_frameoffset(self, cellid):
        '''
        读取帧偏移
        :return:
        '''
        self.execute_enter()
        time.sleep(2)
        if str(cellid) == '0':
            path = '/mnt/flash/SW1/data/modb'
        else:
            path = '/mnt/flash/slavecluster/modb'
        try:
            keyword = 'FrameOffset'
            ret = self.execute_some_command('cd {}'.format(path))
            logger.debug(ret)
            allstr = self.execute_some_command('cat modb.xml |grep {}'.format(keyword))
            logger.debug('cat modb.xml ret={}'.format(allstr))
            idx = allstr.index('value')
            value_start_idx = allstr.find('=', idx) + 2
            value_end_idx = allstr.find('"', value_start_idx)
            value = allstr[value_start_idx:value_end_idx]
            logger.debug('frameoffset_value={}'.format(value))
            return str(value)
        except Exception as e:
            logger.error('get_frameoffset error:{}'.format(e))
            return None

    def get_antiswitch(self, mode):
        '''
        读取降干扰开关
        :return:
        '''
        self.execute_enter()
        time.sleep(2)
        if mode == 'TDD':
            path = '/mnt/flash/SW1/data/modb'
        else:
            path = '/mnt/flash/slavecluster/modb'
        try:
            keyword = 'AntiSwitch'
            self.execute_some_command('cd {}'.format(path))
            allstr = self.execute_some_command('cat modb.xml |grep {}'.format(keyword))
            idx = allstr.index('value')
            value_start_idx = allstr.find('=', idx) + 2
            value_end_idx = allstr.find('"', value_start_idx)
            value = allstr[value_start_idx:value_end_idx]
            logger.debug('antiswitch_value={}'.format(value))
            return str(value)
        except Exception as e:
            raise RuntimeError('get_antiswitch error:{}'.format(e))

    def reset_frameoffset(self, cellid):
        '''
        关闭帧偏移,帧偏移设置成0 TDD可以走命令下发设置，FDD只能靠改文件修改。
        :return:
        '''
        try:
            if str(cellid) == '0':
                self.execute_some_command('FT_PARA_FrameOffSet 0')  # 会自动重启
            else:
                self.execute_enter()
                time.sleep(1)
                path = '/mnt/flash/slavecluster/modb'
                keyword = 'FrameOffset'
                substr = '/{}/s/value=\S*/value="0"/'.format(keyword)
                cmd = "sed -i '{}' modb.xml".format(substr)
                logger.debug(cmd)
                i = 0
                # 有时修改xml文件没有成功，需要反复修改几次
                while 1:
                    if i > 10:
                        return False
                    cdret = self.execute_some_command('cd {}'.format(path))
                    logger.debug('cd {}'.format(path))
                    time.sleep(1)
                    if 'cd' in cdret:
                        self.execute_some_command(cmd)
                        break
                    else:
                        time.sleep(10)
                        i = i + 1
                time.sleep(10)
                self.execute_some_command('sync')  # 刷新文件系统缓冲区
                time.sleep(5)
                self.execute_some_command('reboot')  # 修改后要重启
                return True
        except Exception as e:
            logger.error('reset_frameoffset error:{}'.format(e))
            return False

    def reset_antiswitch(self):
        '''
        关闭降干扰开关
        :return:
        '''
        self.execute_some_command('SetAntiSwitch 0')

    def add_route(self, pcip):
        '''
        Destination     Gateway         Genmask         Flags Metric Ref    Use Iface
192.168.1.50    199.253.1.17    255.255.255.255 UGH   0      0        0 eth1
192.168.1.4     199.253.1.17    255.255.255.255 UGH   0      0        0 eth1
192.254.1.16    199.253.1.17    255.255.255.255 UGH   0
        从片添加路由,telnet进入从片后即可输入下面的命令
        :return:
        '''
        gatewaystr = self.execute_some_command('route')
        # 获得其中的gateway
        linelist = gatewaystr.split('\r\n')
        newline = ''
        for idx, line in enumerate(linelist):
            if not line:
                continue
            if 'gateway' in line.lower():
                newline = linelist[idx + 1]
                break
        if newline:
            newlinelst = newline.split()
            gateway = newlinelst[1]  # 默认gateway在第二列
            cmd = 'route add -host {} gw {} dev eth1'.format(pcip, gateway)
            logger.debug(cmd)
            self.execute_some_command(cmd)  # 添加路由
            return self.check_route(pcip, gateway)
        return False

    def check_route(self, pcip, gateway):
        # 检查是否添加成功
        gatewaystr = self.execute_some_command('route')
        # 获得其中的gateway
        linelist = gatewaystr.split('\r\n')
        newlinelst = ''
        for idx, line in enumerate(linelist):
            if not line:
                continue
            if 'gateway' in line.lower():
                newlinelst = linelist[idx + 1:]
                break
        if newlinelst:
            for line in newlinelst:
                lst = line.split()
                if len(lst) < 2:
                    continue
                if lst[0] == pcip and lst[1] == gateway:
                    logger.debug('add_route success')
                    return True
        return False

    def set_clocksrc(self):
        '''
        设置同步方式为GPS同步
        :return:
        '''
        cmd = 'FT_PARA_ClockSrcSet 2'
        self.execute_some_command(cmd)

    def set_freq(self, freq):
        '''
        设置频率
        freq:Mhz
        :return:
        '''
        freq = 1000 * freq  # Khz
        cmd = 'BspSetTxFreq 0,{}'.format(freq)
        logger.debug(cmd)
        self.execute_some_command(cmd)

    def start_ftp(self):
        cmd = 'RosFtpStart'
        logger.debug(cmd)
        self.execute_some_command(cmd)

    def start_upgrade(self):
        cmd = 'OAM_VMP_VersionInstall'
        logger.debug(cmd)
        self.execute_some_command(cmd)

    def remove_trash(self):
        '''
        删除垃圾文件
        :return:
        '''
        paths = ['/mnt/flash/', '/mnt/flash/BIN/']
        files = ['DefaultCpu.bin', 'DefaultFpga.bin']
        for path in paths:
            for file in files:
                cmd = 'rm {}{}'.format(path, file)
                logger.debug(cmd)
                self.execute_some_command(cmd)
        cmd = 'rm {}cpu*'.format(paths[1])
        logger.debug(cmd)
        self.execute_some_command(cmd)

    def get_freq(self):
        '''
        获取频率
        :return:
        '''
        try:
            cmd = 'BspGetTxFreq 0'
            retstr = self.execute_some_command(cmd)
            keyword = 'value'
            regex = re.compile('\d+')
            if keyword in retstr:
                linelst = retstr.split('\r\n')
                for line in linelst:
                    if not line:
                        continue
                    if keyword in line:
                        _, value = [tmp.strip() for tmp in line.strip().split('=')]
                        txatt_value = regex.findall(value)[0]
                        return float(txatt_value) / 1000
            return None
        except Exception as e:
            logger.error(e)
            return None


class Ctrl_T2K(Ctrl_BOARD):
    username = '/ugdb'
    password = 'csk'

    def __init__(self):
        super(Ctrl_T2K, self).__init__()

    def login_host(self, host_ip):
        try:
            if hasattr(self, 'tn'):
                try:
                    self.tn.close()
                except:
                    pass
                del self.tn
            self.tn = telnetlib.Telnet()
            self.tn.open(host_ip, port=23, timeout=5)
        except:
            logger.error('telnet failed')
            self.tn.close()
            del self.tn
            self.tn = telnetlib.Telnet()
            return False
        else:
            logger.info('telnet成功')
            try:
                flag = self.exter_login()
            except Exception:
                return False
            return True

    def exter_login(self):
        '''
        最外部登录
        :return:
        '''
        user = 'root'
        pwd = 'sh@88861158'
        time.sleep(1)
        self.tn.write(user.encode('ascii') + b'\n\p')
        time.sleep(1)
        self.tn.read_until(b'Password:', timeout=2)
        retstr = self.tn.read_very_eager().decode('ascii', 'ignore')
        if retstr.startswith('#'):
            return True
        self.tn.write(pwd.encode('ascii') + b'\n')
        time.sleep(1)
        command_result = self.tn.read_very_eager().decode('ascii', 'ignore')
        if 'Done' in command_result:
            logger.warning('登录root成功')
            return True
        else:
            logger.warning('登录root失败')
            return False

    def login_baseboard(self):
        '''
        登录基带板
        :return:
        '''
        time.sleep(.5)
        self.tn.write(self.username.encode('ascii') + b'\n')
        time.sleep(1)
        self.tn.read_until(b'input password', timeout=1)
        self.tn.read_very_eager().decode('ascii', 'ignore')
        self.tn.write(self.password.encode('ascii') + b'\n')
        time.sleep(.5)
        command_result = self.tn.read_very_eager().decode('ascii', 'ignore')
        # logger.debug('login ushell reply={}'.format(command_result))
        if 'input password' in command_result:
            self.tn.write(self.password.encode('ascii') + b'\n')
            time.sleep(2)
            command_result = self.tn.read_very_eager().decode('ascii', 'ignore')
            logger.debug('again login ugdb reply={}'.format(command_result))
            if 'success' not in command_result:
                logger.warning('登录ugdb失败')
                return False
            else:
                logger.warning('登录ugdb成功')
                return True
        elif 'success' in command_result:
            logger.warning('登录ugdb成功')
            return True
        elif '$$' in command_result:
            logger.warning('登录ugdb成功')
            return True
        else:
            logger.warning('登录ugdb失败')
            return False

    def get_boardinfo(self):
        '''
        读取配置文件中主从片的band设置
        MasterWorkMode,SlaveWorkMode:0/1->TDD/FDD
        MasterFunId,SlaveFunId:0:移动E段,1：移动D段,2：移动F段,3：联通B1,4:电信B3,5:B41,6:B5,7:B8
        :return:[]字符串列表
        '''
        # self.execute_enter()
        time.sleep(1)
        try:
            keywords = ['MasterWorkMode', 'SlaveWorkMode', 'MasterFunId', 'SlaveFunId']
            self.execute_some_command('cd /mnt/flash/scbs')
            allstr = self.execute_some_command('cat BoardInfo.txt')
            linelist = allstr.split('\r\n')
            band_dict = {}
            for line in linelist:
                if not line or line.startswith('#'):
                    continue
                for keyword in keywords:
                    if keyword in line and '=' in line:
                        # logger.debug('boardinfo line={}'.format(line))
                        _, value = line.strip().split('=')
                        band_dict.setdefault(keyword.strip(), value.strip())
                        break
            if len(band_dict) == len(keywords):
                retlist = [band_dict[key] for key in keywords]
                # logger.debug('boardinfo={}'.format(retlist))
                return retlist

        except Exception as e:
            logger.error('get_boardinfo error:{}'.format(e))
            return None
        else:
            return None

    def set_mode(self, cellid, funid):
        '''
        设置mode,默认主载波TDD，从载波FDD,修改文件
        :param mode:
        :param args:
        :return:
        '''
        if int(cellid) == 0:
            keywords = ['MasterWorkMode', 'MasterFunId']
            workmode = 0
        else:
            keywords = ['SlaveWorkMode', 'SlaveFunId']
            workmode = 1
        try:
            self.execute_enter()
            time.sleep(1)
            path = '/mnt/flash/scbs/BoardInfo.txt'
            substr1 = '/^{}=/c\{}={}'.format(keywords[0], keywords[0], workmode)
            substr2 = '/^{}=/c\{}={}'.format(keywords[1], keywords[1], funid)
            cmd1 = "sed -i '{}' {}".format(substr1, path)
            cmd2 = "sed -i '{}' {}".format(substr2, path)

            self.execute_some_command(cmd1)
            self.execute_some_command(cmd2)
            time.sleep(2)
            self.execute_some_command('sync')  # 刷新文件系统缓冲区
            time.sleep(5)
            self.execute_some_command('reboot')  # 修改后要重启
            return True
        except Exception as e:
            logger.error('set_mode error:{}'.format(e))
            return False

    def query_class1_para(self, cellid):
        '''
        查询一类参数
        基带板返回值

******** Param Query Result ********

 - dwCellId                =    0.
 - CenterFreq              = 40936.
 - SysBandWidth            =     0.
 - CellSpeRefSigPwr        =     0.
 - PhyCellId               =    88.
 - TAC                     =   212.
 - SubFrameAssignment      =     2.
 - SpecialSubframePatterns =     7.

*************Param Query Result End*********
        :return:
        '''
        try:
            allstr = self.execute_some_command('FT_PARA_ParaQuery {}'.format(cellid))
            linelist = allstr.split('\r\n')
            keywords = ['dwCellId', 'CenterFreq', 'SysBandWidth', 'CellSpeRefSigPwr', 'PhyCellId',
                        'TAC', 'SubFrameAssignment', 'SpecialSubframePatterns']
            para_dict = {}
            for line in linelist:
                if not line or line.startswith('#'):
                    continue
                if ',' in line:
                    continue
                if '=' in line and '-' in line:
                    for keyword in keywords:
                        if keyword in para_dict.keys():
                            continue
                        if keyword in line:
                            _, value = line.strip().split('=')
                            if value is not None:
                                para_dict.setdefault(keyword.strip(), value.strip().strip('.'))
                                break
            if len(para_dict) == len(keywords):
                retlist = [para_dict[key] for key in keywords]
                return retlist

        except Exception as e:
            raise ValueError('query_class1_para error:{}'.format(e))
        else:
            return None

    def str_2_dict(self, strdict):
        try:
            ret_dict = {}
            a = [tmp.strip() for tmp in strdict.strip().strip(';').split(',')]
            for item in a:
                if item:
                    key_value = [tmp.strip() for tmp in item.split(':')]
                    ret_dict[key_value[0]] = key_value[1]
            return ret_dict
        except Exception as e:
            logger.error('str_2_dict error:{}'.format(e))
            return None

    def check_cell_state(self, cellid=None):
        '''
        查看小区状态 2表示小区建立了
        T2K小区状态上报是一次性报两个小区，所以要区分小区
        :return:
        '''
        try:
            keyword = 'ucCellState'
            keyword1 = 'wCellId'
            keyvalue = '2'
            keyvalue1 = str(cellid)
            cellstate = self.execute_some_command('CELLDbgShowCell')
            # logger.debug(cellstate)
            if keyword in cellstate:
                linelst = cellstate.split('\r\n')
                for line in linelst:
                    if not line:
                        continue
                    if not (keyword1 + ":") in line:
                        continue
                    if keyword + ':' in line:
                        cell_dict = self.str_2_dict(line)
                        if cell_dict:
                            uccellstate = cell_dict[keyword]
                            wcellid = cell_dict[keyword1]
                            if uccellstate == keyvalue and wcellid == keyvalue1:
                                logger.info('小区{}建立成功'.format(cellid))
                                return True
                            elif wcellid == keyvalue1:
                                return False
        except Exception as e:
            logger.error('check_cell_state error :{}'.format(e))
            self.exit()
            return False
        else:
            return False

    def repeat_check_cell_state(self, cellid=None):
        '''
        重复10次检测小区，每隔1分钟检测一次
        :return:
        '''
        n = 0
        MAX = 60
        INTERVAL = 10
        flag = False
        try:
            while 1:
                logger.info('begin to check_cell_state  every minute...')
                flag = self.check_cell_state(cellid)
                if flag:
                    break
                n = n + 1
                if n > MAX:
                    break
                time.sleep(INTERVAL)
        except Exception as e:
            logger.error(e)
            return False
        return flag

    def set_rf(self, cellid, onoff):
        '''
        设置射频开关
        onoff:0:关闭，1：打开
        :return:
        '''
        cmd = 'FT_SYS_RFStatusSet {},{}'.format(cellid, onoff)
        logger.debug(cmd)
        self.execute_some_command('FT_SYS_RFStatusSet {},{}'.format(cellid, onoff))

    def set_txatt(self, cellid, txatt):
        '''
        设置衰减 cellid,channelid,txatt

        :param value:dB
        :return:
        '''
        value = float(txatt) * 100
        cmd = 'BspSetTxAtt {},0,{}'.format(cellid, int(value))
        logger.debug(cmd)
        self.execute_some_command(cmd)

    def reset_frameoffset(self, cellid):
        '''
        设置后会重启，通过命令
        :param cellid: 0/1
        :return:
        '''
        cmd = 'FT_PARA_DirectFrameOffSet 0,{}'.format(cellid)
        logger.debug(cmd)
        self.execute_some_command(cmd)
        return True

    def reset_power_compesation(self, cellid):
        '''
        关闭温补，频补，不会重启
        :param cellid:
        :return:
        '''
        cmd = 'FT_PowerCompesation_Switch {},0,0'.format(cellid)
        logger.debug(cmd)
        self.execute_some_command(cmd)
        return True

    def get_frameoffset(self, cellid):
        '''
        T2K通过命令修改的帧偏移，不知道帧偏移文件路径，可以通过命令获取,暂时不做
        :param cellid:
        :return:
        '''
        if str(cellid) == '1':
            return '0'
        try:
            cmd = 'FT_PARA_DirectFrameOffGet'
            retstr = self.execute_some_command(cmd)
            keyword = 'FrameOff:'
            if keyword in retstr:
                linelst = retstr.split('\r\n')
                for line in linelst:
                    if not line:
                        continue
                    if keyword in line:
                        idx = line.index(keyword) + len(keyword)
                        frameoff_value = str(line[idx:]).strip()
                        return frameoff_value
            return None
        except Exception as e:
            logger.error(e)
            return None

    def set_clocksrc(self):
        '''
        设置同步方式为GPS同步
        :return:
        '''
        cmd = 'FT_PARA_ClockSrcSet 2'
        self.execute_some_command(cmd)

    def get_clock_src(self):
        '''
        获取时钟源 为2则是GPS同步
        :return:
        '''
        try:
            cmd = 'FT_PARA_ClockSrcGet'
            retstr = self.execute_some_command(cmd)
            keyword = 'sdwTmp_val'
            regex = re.compile('\d+')
            if keyword in retstr:
                linelst = retstr.split('\r\n')
                for line in linelst:
                    if not line:
                        continue
                    if keyword in line:
                        idx = line.index(keyword)
                        keyline = line[idx:]
                        _, value = [tmp.strip() for tmp in keyline.strip().split('=')]
                        src_value = regex.findall(value)[0]
                        return int(src_value)
            return None
        except Exception as e:
            logger.error(e)
            return None

    def adjust(self):
        '''
        发送校准命令
        :return:
        '''
        cmd = 'PioltTestTrigPhy 1'
        self.execute_some_command(cmd)

    def start_ftp(self):
        cmd = 'FtpServerStart'
        self.execute_some_command(cmd)

    def start_upgrade(self):
        cmd = 'OAM_VersionInstall'
        logger.debug(cmd)
        self.execute_some_command(cmd)

    def remove_trash(self):
        pass

    def do_untar_arm(self, armtar, period):
        '''
        解压arm tar包到指定目录
        :return:
        '''
        try:
            cmd = 'cd /mnt/flash'
            self.execute_some_command(cmd)
            cmd = 'tar -xvf {}'.format(armtar)
            logger.debug(cmd)
            # ret=self.execute_some_command(cmd)
            self.tn.write(cmd.encode('ascii') + b'\n')
            time.sleep(int(period))
            # 忽略中文
            command_result = self.tn.read_very_eager().decode('ascii', 'ignore')
            if 'arm_guide' in command_result:
                self.execute_some_command('cd /mnt/flash/sanhui_t2k')
                armfilesize = self.read_filesize('synway_arm9.bin')
                guidesize = self.read_filesize('synway_arm_guide.bin')
                logger.debug('synway_arm_guide.bin:{}'.format(guidesize))
                if abs(guidesize - armfilesize) > 1024 * 100:
                    return False
                return True
            else:
                return False
        except Exception as e:
            logger.error(e)
            return False

    def read_filesize(self, filename):
        '''
        返回文件大小，单位是字节
        :param filename:
        :return:
        '''
        regex = re.compile(r'-?\d+\.?\d*e?-?\d*?')
        cmd = "ls -l %s |awk '{print $5}'" % filename
        logger.debug(cmd)
        self.tn.write(cmd.encode('ascii') + b'\n')
        time.sleep(1)
        command_result = self.tn.read_very_eager().decode('ascii', 'ignore')
        ret = regex.findall(command_result)
        return float(ret[-1])

    def chmod_armtar(self):
        # chmod
        cmd = 'cd /mnt/flash/sanhui_t2k/'
        self.execute_some_command(cmd)
        cmd = 'ls'
        self.execute_some_command(cmd)
        cmd = 'chmod 755 rcS'
        logger.debug(cmd)
        self.execute_some_command(cmd)

    def modify_firstip(self, ipstr):
        '''
        修改server.conf中的FIRST_IP的值
        :return:
        '''
        path = '/mnt/flash/sanhui_t2k/server.conf'
        keyword = 'FIRST_IP'
        substr = '/^{}=/c\{}={}'.format(keyword, keyword, ipstr)
        cmd = "sed -i '{}' {}".format(substr, path)
        logger.debug(cmd)
        self.execute_some_command(cmd)
        time.sleep(2)
        self.execute_some_command('sync')  # 刷新文件系统缓冲区

    def clear_tar(self):
        cmd = 'cd /mnt/flash'
        self.execute_some_command(cmd)
        # 删除文件夹sanhui_t2k
        cmd = 'rm -rf {}'.format('sanhui_t2k/')
        logger.debug(cmd)
        self.execute_some_command(cmd)

    def set_all_band(self, *args):
        '''
        设置EB1
        :return:
        '''
        keywords = ['MasterWorkMode', 'SlaveWorkMode', 'MasterFunId', 'SlaveFunId']
        try:
            path = '/mnt/flash/scbs/BoardInfo.txt'
            for i in range(len(args)):
                substr = '/^{}=/c\{}={}'.format(keywords[i], keywords[i], args[i])
                cmd = "sed -i '{}' {}".format(substr, path)
                self.execute_some_command(cmd)
            time.sleep(2)
            self.execute_some_command('sync')  # 刷新文件系统缓冲区
            return True
        except Exception as e:
            logger.error('set_mode error:{}'.format(e))
            return False

    def remove_m(self, path, filename):
        '''
        去掉文件的^M字符
        :return:
        '''
        cmd = 'cd {}'.format(path)
        self.execute_some_command(cmd)
        cmd = 'dos2unix {}'.format(filename)
        self.execute_some_command(cmd)

    def set_gpsmode(self):
        cmd = 'BspSetGpsMode 0'
        logger.debug(cmd)
        self.execute_some_command(cmd)
        return True

    def enb_cell(self):
        '''
        强建小区
        :return:
        '''
        cmd = 'g_dwEnbSyncSwitchFlag 0'
        logger.debug(cmd)
        self.execute_some_command(cmd)

    def read_temp(self):
        '''
        读取板子温度
        :return:
        '''
        cmd = 'FT_SYS_TemperatureQuery'
        logger.debug(cmd)
        try:
            retstr = self.execute_some_command(cmd)
            keyword = 'get temperature'
            regex = re.compile(r'^[\-|0-9][0-9]*')
            if keyword in retstr:
                linelst = retstr.split('\r\n')
                for line in linelst:
                    if not line:
                        continue
                    if keyword in line:
                        idx = line.index(keyword)
                        keyline = line[idx:]
                        *_, value = [tmp.strip() for tmp in keyline.strip().split()]
                        src_value = regex.findall(value)[0]
                        return int(src_value)
            return None

        except Exception as e:
            return None

    def send_powercali(self, *args):
        '''
        功率补偿
        :param band: int,38/39/40/41/1/3
        :param freqpoint: int
        :param cali: int
        :param temp: int
        :return:
        '''
        para = ','.join([str(item) for item in args])
        cmd = 'FT_WriteFreqCaliTableToFile {}'.format(para)
        logger.debug(cmd)
        self.execute_some_command(cmd)

    def send_debug_tempfreq(self):
        '''
        刷新
        :return:
        '''
        cmd = 'FT_Debug_TempFreq'
        logger.debug(cmd)
        self.execute_some_command(cmd)
        time.sleep(3)

    def remove_flat_json(self):
        '''
        删除平坦度补偿表
        :return:
        '''
        cmd = 'cd /mnt/flash/scbs'
        logger.debug(cmd)
        self.execute_some_command(cmd)
        name = '*_FlatComp.json'
        # cmd="rm -f $(find . -name '{}')".format(name)
        cmd = 'rm -f {}'.format(name)
        logger.debug(cmd)
        self.execute_some_command(cmd)

    def remove_gain_json(self):
        '''
        删除温补表
        :return:
        '''
        cmd = 'cd /mnt/flash/scbs'
        self.execute_some_command(cmd)
        name = '*_GainComp.json'
        # cmd="rm -f $(find . -name '{}')".format(name)
        cmd = 'rm -f {}'.format(name)
        logger.debug(cmd)
        self.execute_some_command(cmd)

    def set_airsync_para(self, freqpoint):
        try:
            cmd = 'FT_PARA_AIRSYNCPARA_SET {}'.format(freqpoint)
            logger.debug(cmd)
            self.tn.write(cmd.encode('ascii') + b'\n')
            time.sleep(1)
            retstr = self.tn.read_until(b'Recv Sniffer Rst from BB:', timeout=20).decode('ascii', 'ignore')
            allstr = self.tn.read_very_eager().decode('ascii', 'ignore')
            linelist = allstr.split('\r\n')
            keywords = ['sdwRSRP', 'sdwRSRQ']
            para_dict = {}
            for line in linelist:
                if len(para_dict) == len(keywords):
                    retlist = [para_dict[key] for key in keywords]
                    return retlist
                for keyword in keywords:
                    if keyword in para_dict.keys():
                        continue
                    if keyword in line:
                        _, value = line.strip().split('=')
                        if value is not None:
                            para_dict.setdefault(keyword.strip(), value.strip().strip('.'))
                            break
            return None
        except Exception as e:
            logger.error(e)
            return None

    def start_run_arm(self):
        cmd = 'cd /mnt/flash/sanhui_t2k'
        self.execute_some_command(cmd)
        cmd = './rcS'
        self.execute_some_command(cmd)

    def get_macaddr(self):
        '''

        :return: serialnumber
        '''
        try:
            cmd = 'cd /mnt/flash/scbs'
            self.execute_some_command(cmd)
            cmd = 'cat BoardInfo.txt'
            allstr = self.execute_some_command(cmd)
            linelist = allstr.split('\r\n')
            sn=''
            keyword='SerialNumber'
            for line in linelist:
                if '#' in line:
                    continue
                if not '=' in line:
                    continue
                if keyword in line:
                    sn = line.strip().strip('\r\n').split('=')[-1]
                    return str(sn)
            return sn
        except Exception as e:
            logger.error(e)
            return None

    def reboot(self):
        cmd = 'reboot'
        logger.debug(cmd)
        self.execute_some_command(cmd)

    def get_productno(self):
        '''
        获取物料号,/mnt/flash/sanhui_t2k/Product.conf
        :return:
        '''
        cmd = 'cd /mnt/flash/scbs'
        self.execute_some_command(cmd)
        cmd = 'cat BoardInfo.txt'
        allstr = self.execute_some_command(cmd)
        linelist = allstr.split('\r\n')
        keyword='PNCode'
        for line in linelist:
            if '#' in line:
                continue
            if not '=' in line:
                continue

            if keyword in line:
                logger.debug(line)
                key_value=line.strip().strip('\r\n').split('=')
                pncode = key_value[1]
                return str(pncode)
        return None

    def set_pwrbackoff_switch(self):
        cmd = 'FT_Test_PwrBackOff 0,0'
        logger.debug(cmd)
        self.execute_some_command(cmd)

    def get_bbver(self):
        '''
        获取BB版本
        :return:
        '''
        try:
            ret = self.execute_some_command('ps')  # 返回str
            lines = ret.split('\r\n')  # 按行分割的列表
            bb_ver = ''
            process = 'APP_lte'
            for eachline in lines:
                if process in eachline:
                    line_list = eachline.split()  # 可分割任意个空白字符
                    bb_ver = line_list[-1]
            return bb_ver
        except Exception as e:
            logger.error(e)
            return None

    def read_gain_json(self,filename):
        '''
        获取温补表内容
        :param filename:温补表文件名
        :return:dict {}
        '''
        import json
        try:
            cmd='cd /mnt/flash/scbs'
            self.execute_some_command(cmd)
            cmd='cat {}'.format(filename)
            ret=self.execute_some_command(cmd)
            #去掉头部cat 命令字符串，去掉尾部#
            ret1=ret.strip().lstrip(cmd).rstrip('#\n')
            # logger.debug(ret1)
            retdict=json.loads(ret1)
            return retdict
        except Exception as e:
            logger.error(e)
            return None

    def switch_reboot_flag(self,onoff):
        '''
        BB 15版本后才有，检测到不采集是否重启的开关
        :param onoff: 0 表示不重启 1表示重启
        :return:
        '''
        cmd='FT_MISC_RebootByMonitorRaStatus {}'.format(onoff)
        self.execute_some_command(cmd)


if __name__ == '__main__':
    '''
    不需要登录名，密码
    '''
    host_ip = '192.254.1.16'
    # host_ip = '192.254.1.16'
    # subip = '199.253.1.16'

    # username = '/ushell'
    # password = 'zte'
    # t_client = Ctrl_8125()
    #
    # if t_client.login_host(host_ip):  # telnet连接主片
    #     pname=t_client.get_process_name('Product_lte')
    #     print(pname)
    #     t_client.execute_enter()
    #     t_client.telnet_board(subip)  # telnet从片
    #     t_client.add_route('192.168.1.4')
    #
    t2k = Ctrl_T2K()
    if t2k.login_host(host_ip):
        t2k.remove_trash()
        t2k.do_untar_arm('ARM_T2K_V2.0.0.17_2B-EB1-T2K_202006281026.tar')
    #     print(t2k.get_boardinfo())
    #     t2k.set_mode('TDD', '5')
    #     if t2k.login_baseboard():
    #         pass
    #     ls = t2k.check_ps('PLAT.EXE', 'APP_lte')
    #     t2k.pad_process(*ls)
    #     print(t2k.query_class1_para(0))
