# coding:utf-8
'''
操作中兴的软件,8125的与T2K的软件不同
'''
import os
import re
import logging
import time
import psutil
import copy

from pywinauto import mouse
from pywinauto.application import Application

logger = logging.getLogger('ghost')


class EXEOperate(object):
    # exe_path = r'F:\auto_test_projs\协议\测试灵敏度软件\81248125\TDD_Release -tdd-union\bin\MTS.exe'
    process_name = 'MTS.exe'

    def exe_is_active(self, process_name):
        """
        判断"**.exe"进程是否存在
        :return: 进程存在，返回False，否则为True
        """
        processes_name = []
        pids = psutil.pids()
        for pid in pids:
            p = psutil.Process(pid)
            processes_name.append(p.name())

        if process_name in processes_name:
            print('{} is active.'.format(process_name))
            return True
        else:
            print('{} is not active.'.format(process_name))
            return False

    def start_exe(self, ip, exe_path):
        '''
        打开exe软件
        ip:字符串'',基带板IP
        :return:
        '''
        if self.exe_is_active(self.process_name):
            os.system(r'taskkill /F /IM {}'.format(self.process_name))
            time.sleep(2)
        try:
            if hasattr(self, 'app'):
                del self.app
            self.app = Application(backend='uia').start(r'{}'.format(exe_path))
            time.sleep(0.5)
            self.ip = ip
        except Exception as e:
            logger.error(e)

    def site_manage(self):
        '''
        站点管理
        :return:
        '''
        try:
            mts_dlg = self.app.Dialog  # MTS dialog
            dlg_login = mts_dlg.window(title='登录')  # 登录dialog
            # time.sleep(0.1)

            dlg_login.window(title="站点管理...").click()  # 点击站点管理按钮
            # time.sleep(.2)
            # 弹出站点管理对话框
            dlg_info = dlg_login.Dialog2
            listbox = dlg_info.ListBox  # 站点信息Listbox
            # items = listbox.texts()  # list内容
            row_count = listbox.item_count()  # 行数，包含标题行
            if row_count > 1:  # 有站点信息，需要清空
                # 清空list
                for i in range(row_count - 1):
                    # a = listbox.get_item(1)
                    b = listbox.get_item_rect(1)  # 返回第1行item的4个点,第0行是header
                    # a.select()  #只是选中，没有按下鼠标，删除按钮仍然无效
                    item_position = self.get_coords(b)
                    mouse.click(button='left', coords=item_position)  # 点击第一行item
                    # listbox.type_keys("{HOME}")#选中第一行
                    # time.sleep(.5)
                    dlg_info.Button3.click()  # 删除
                    closedlg = self.app['MTS']
                    closedlg.Button.click()
            time.sleep(.5)
            # 添加IP信息
            dlg_info.Button.click()  # 添加
            dlg_add = mts_dlg.Dialog4
            dlg_add.Edit.set_text('aa')  # 基站名
            ip_lst = self.get_ip_list(self.ip)
            dlg_add.Edit5.set_text(ip_lst[0])
            dlg_add.Edit4.set_text(ip_lst[1])
            dlg_add.Edit3.set_text(ip_lst[2])
            dlg_add.Edit2.set_text(ip_lst[3])
            # time.sleep(.3)
            dlg_add.Button1.click()  # 点击确定
            time.sleep(.5)
            dlg_info.Button6.click()  # 站点管理Dialog点击确定按钮
            # time.sleep(0.1)

            fail_num = 0
            while 1:
                dlg_login.Button2.click()  # 登录确定按钮
                time.sleep(3)
                dlg = self.app.window(title='MTS', class_name='#32770')

                if dlg.exists():  # 与基站通信超时对话框弹出
                    dlg.Button.click()  # 确定按钮
                    time.sleep(.2)
                    fail_num += 1
                    if fail_num > 3:
                        raise RuntimeError('与基站通信超时')
                    continue
                break
            return True
        except Exception as e:
            logger.error('site_manage error:{}'.format(e))
            return False

    def get_coords(self, rect):
        '''
        rect:(left,top,right,bottom)
        从四角的坐标得到中心坐标点
        :return:(intx,inty)
        '''
        numbers = re.findall(r'\d+', str(rect))
        numberlist = [int(number) for number in numbers]
        return int((numberlist[0] + numberlist[2]) / 2), int((numberlist[1] + numberlist[3]) / 2)

    def get_ip_list(self, ipstr):
        '''
        ipstr:str '192.254.1.16'
        :return: ['192','254','1','16']
        '''
        return ipstr.split('.')

    def enter_test_mode(self):
        '''
        进入测试模式
        :return:
        '''
        try:
            mts_dlg = self.app.Dialog
            menu = mts_dlg.Menu2
            rect = menu.window(title='系统(S)').rectangle()
            item_position = self.get_coords(rect)
            mouse.click(button='left', coords=item_position)
            # time.sleep(.1)
            test = mts_dlg.window(best_match='进入测试模式')
            test_text = test.texts()[0]  # 检查是否是'进入测试模式',有时是'退出测试模式',这时就不点了
            if test_text == '进入测试模式':
                rect = test.rectangle()
                mouse.click(button='left', coords=self.get_coords(rect))
                # time.sleep(.2)
                dlg = self.app.window(title='MTS')
                dlg.Button.click()

            time.sleep(.2)
            # 点击工作区
            pane = mts_dlg.Pane2
            rect = pane.rectangle()
            mouse.click(button='left', coords=self.get_coords(rect))
            return True
        except Exception as e:
            raise NotImplementedError('进入测试模式失败')

    def create_ue(self):
        '''
        创建UE
        :return:
        '''
        try:
            mts_dlg = self.app.Dialog
            tree_view = mts_dlg['SysTreeView32']
            navi_tree = tree_view.TreeItem
            ue_management = navi_tree.TreeItem1

            rect = ue_management.rectangle()
            coord = self.get_coords(rect)
            mouse.click(button='right', coords=coord)  # 右键弹出建立模拟UE
            pop_coord = (coord[0] + 5, coord[1] + 5)
            mouse.click(button='left', coords=pop_coord)
            time.sleep(1)

            cell_choose = mts_dlg.Dialog2
            dlg_title = cell_choose.texts()[0]
            if dlg_title != '小区选择':
                logger.error('通讯超时')
                cell_choose.Button.click()  # 点击确定
                # 弹出小区选择对话框，选择小区下拉框为空
                cell_choose = mts_dlg.Dialog2
                # 选择小区下拉框
                cbox = cell_choose.ComboBox
                item_count = cbox.item_count()
                if item_count == 0:
                    logger.error('通讯超时')
                    cell_choose.Cancel.click()  # 点击取消
                    return False
                else:
                    return True
            else:
                cell_choose.Button.click()
                time.sleep(1)

                cell_create = mts_dlg.Dialog2
                cell_create.Button.click()
                time.sleep(1)
                uplink_pusch_test = navi_tree.TreeItem6  # UPlink PUSCH TEST
                rect = uplink_pusch_test.rectangle()
                coord = self.get_coords(rect)
                mouse.click(button='right', coords=coord)  # 右键弹出创建任务
                pop_coord = (coord[0] + 5, coord[1] + 5)  # 点击弹出的菜单
                mouse.click(button='left', coords=pop_coord)
                time.sleep(.3)
                task_create = mts_dlg.Dialog2  # 创建任务对话框，点击确定即可
                task_create.Button2.click()
                time.sleep(3)
                return True
        except Exception as e:
            raise NotImplementedError('创建UE模块失败')

    def ready_for_check(self):
        '''
        读误码率前的准备操作，包括清空上面的表格，获取误码率表格的rect
        :return:
        '''
        try:
            self.clear_upper_table()
            mts_dlg = self.app.Dialog
            mylistbox = None
            mylistbox = mts_dlg.Dialog2.TabControl.ListBox2  # PUSCH test statics TAB下的第二张表
            rect = mylistbox.get_item_rect(1)
            self.click_pop_clear(rect)  # 点击清空
            time.sleep(3)
            return rect
        except Exception as e:
            raise NotImplementedError('表格清空失败')

    def check_result(self, rect):
        '''
        查看误码率列表
        :return:字符串列表
        '''
        try:
            mts_dlg = self.app.Dialog
            # 查看结果
            mylistbox = None
            mylistbox = mts_dlg.Dialog2.TabControl.ListBox2  # PUSCH test statics TAB下的第二张表
            # 点击右键暂停显示
            self.click_pop_menu(rect)
            # 读取暂停后的列表内容
            berlist = self.get_ber()

            # 再点击继续显示菜单
            self.click_pop_menu(rect)
            self.click_pop_clear(rect)  # 点击清空
            return berlist
        except Exception as e:
            logger.error('check result error:{}'.format(e))
            return None

    def click_pop_menu(self, rect):
        '''
        点击右键弹出的菜单暂停显示
        :param rect:
        :return:
        '''
        coord = self.get_coords(rect)
        after_coord = (coord[0] - 300, coord[1] - 100)  # 由于右键位置在右下角，需要偏下
        mouse.click(button='right', coords=after_coord)  # 右键弹出菜单
        time.sleep(.1)
        pop_coord = (after_coord[0] + 10, after_coord[1] + 5)  # 点击弹出的暂停显示
        mouse.click(button='left', coords=pop_coord)
        time.sleep(.5)

    def click_pop_clear(self, rect):
        '''
        点击右键清除选项
        :param rect:
        :return:
        '''
        coord = self.get_coords(rect)
        after_coord = (coord[0] - 300, coord[1] - 100)  # 由于右键位置在右下角，需要偏下
        mouse.click(button='right', coords=after_coord)  # 右键弹出菜单
        time.sleep(.1)
        pop_coord = (after_coord[0] + 20, after_coord[1] + 30)  # 点击弹出的清空
        mouse.click(button='left', coords=pop_coord)
        time.sleep(.5)

    def clear_upper_table(self):
        '''
        清空误码率表格上面的另一张表
        :return:
        '''
        mts_dlg = self.app.Dialog
        listbox = mts_dlg.Dialog2.TabControl.ListBox
        time.sleep(.5)
        rect = listbox.get_item_rect(1)
        self.click_pop_clear(rect)  # 清空
        time.sleep(1)
        self.click_pop_menu(rect)  # 暂停显示
        time.sleep(.5)
        del listbox

    def get_ber(self):
        '''
        得到误码率,取前10行即可
        :return:intlist
        '''
        try:
            mts_dlg = self.app.Dialog
            listbox = mts_dlg.Dialog2.TabControl.ListBox2  # PUSCH test statics TAB下的第二张表
            allitems = listbox.descendants(control_type='ListItem')[:10]
            items = allitems
            del listbox
            alllist = [item.texts() for item in items]
            target = 16
            berlist = []
            if target < 0:
                return berlist
            for everylist in alllist:
                if len(everylist) <= 1:
                    continue
                if len(everylist) > 9:
                    berlist.append(float(everylist[target]))
                # if len(berlist)>10:
                #     break
            return berlist
        except Exception as e:
            logger.error(e)
            return None

    def close_exe(self):
        '''
        关闭软件
        :return:
        '''
        if self.app:
            mts_dlg = self.app.Dialog
            mts_dlg.close()
            time.sleep(.5)
            closedlg = mts_dlg['MTSDialog2']
            # print(closedlg.print_control_identifiers())
            closedlg.Button.click()
            time.sleep(5)
            del self.app


class T2KEXEOperate(object):
    process_name = 'MTS.exe'

    def exe_is_active(self, process_name):
        """
        判断"**.exe"进程是否存在
        :return: 进程存在，返回False，否则为True
        """
        processes_name = []
        pids = psutil.pids()
        for pid in pids:
            p = psutil.Process(pid)
            processes_name.append(p.name())

        if process_name in processes_name:
            # print('{} is active.'.format(process_name))
            return True
        else:
            # print('{} is not active.'.format(process_name))
            return False

    def start_exe(self, ip, exe_path):
        '''
        打开exe软件
        ip:字符串'',基带板IP
        :return:
        '''
        if self.exe_is_active(self.process_name):
            os.system(r'taskkill /F /IM {}'.format(self.process_name))
            time.sleep(2)
        try:
            if hasattr(self, 'app'):
                try:
                    del self.app
                except:
                    pass
            self.app = Application(backend='win32').start(r'{}'.format(exe_path))
            logger.debug(self.app)
            time.sleep(0.5)
            self.ip = ip
        except Exception as e:
            logger.error(e)

    def site_manage(self):
        '''
        IP配置
        :return:
        '''
        try:
            ip_lst = self.get_ip_list(self.ip)
            dlg_mts = self.app['登录']
            # print(dlg_mts.print_control_identifiers())
            dlg_login = dlg_mts
            ippane = dlg_login.child_window(class_name='SysIPAddress32')
            alledit = ippane.children()
            ipl = [item.text_block() for item in alledit]
            if ipl[::-1] == ip_lst:
                dlg_login.child_window(title='确定(&O)', class_name='Button').drag_mouse()
                # mouse.click(coords=(625,433))
                time.sleep(1)
                return True
            ipedit_btn = dlg_login.child_window(title="IP配置...", class_name="Button")
            ipedit_btn.drag_mouse()  # 点击站点管理按钮
            time.sleep(1)
            # 弹出站点管理对话框
            dlg_info = self.app['基站管理']
            listbox = dlg_info.child_window(title='List2', class_name='SysListView32')  # 站点信息Listbox
            row_count = listbox.item_count()  # 行数，包含标题行
            if row_count >= 1:  # 有站点信息，需要清空
                # 清空list
                for i in range(row_count):
                    b = listbox.get_item(0)  #
                    b.click()
                    time.sleep(1)
                    dlg_info.Button3.drag_mouse()  # 删除
                    closedlg = self.app['MTS']
                    closedlg.Button.drag_mouse()
            time.sleep(.5)
            # 添加IP信息
            dlg_info.Button.drag_mouse()  # 添加
            time.sleep(1)
            dlg_add = self.app['增加站点信息']
            alledit = dlg_add.children(class_name='Edit')[:5]
            new_edit = ['aa'] + ip_lst[::-1]
            for idx, item in enumerate(alledit):
                item.set_text(new_edit[idx])

            time.sleep(.3)
            dlg_add.Button1.drag_mouse()  # 点击确定
            time.sleep(.1)
            dlg_info.Button4.drag_mouse()  # 站点管理Dialog点击确定按钮
            time.sleep(.1)
            dlg_login = self.app['登录']  # 登录dialog
            dlg_login.Button.drag_mouse()  # 登录确定按钮
            time.sleep(5)
            return True
        except Exception as e:
            logger.error('site_manage error:{}'.format(e))
            return False

    def get_coords(self, rect):
        '''
        rect:[left,top,right,bottom]
        从四角的坐标得到中心坐标点
        :return:(intx,inty)
        '''
        numbers = re.findall(r'\d+', str(rect))
        numberlist = [int(number) for number in numbers]
        return int((numberlist[0] + numberlist[2]) / 2), int((numberlist[1] + numberlist[3]) / 2)

    def get_left_coord(self, rect):
        '''
        从四角坐标得到左上角的坐标点
        :param rect:
        :return:
        '''
        numbers = re.findall(r'\d+', str(rect))
        numberlist = [int(number) for number in numbers]
        return numberlist[0], numberlist[1]

    def get_ip_list(self, ipstr):
        '''
        ipstr:str '192.254.1.16'
        :return: ['192','254','1','16']
        '''
        return ipstr.split('.')

    def modify_test_mode(self, cellid, mode):
        '''
        进入测试模式
        cellid:0/1
        mode:TDD, FDD
        :return:
        '''
        time.sleep(1)
        mts_dlg = self.app['MTS']

        try:
            # print(mts_dlg.print_control_identifiers())
            mts_dlg.menu_select('开始(S)->进入测试')
            # 弹出dialog ,选择小区id和制式TDD/FDD
            dialog = self.app.Dialog
            dialog.Edit.set_text(str(cellid))
            time.sleep(.1)
            dialog.ComboBox.Edit2.set_text(str(mode))
            dialog.Button.drag_mouse()  # OK
            time.sleep(1)
            # 弹出确认框
            mts = self.app.window(class_name='#32770')
            mts.Button.drag_mouse()  # 是
            time.sleep(1)
            # 点击工作区
            # pane = mts_dlg.MDIClient
            # pane.drag_mouse()
            # rect = pane.rectangle()
            # mouse.click(button='left', coords=self.get_coords(rect))
            time.sleep(.1)
            return True
        except Exception as e:
            try:
                mts = self.app.window(class_name='#32770')
                if mts.exists():
                    mts.Button.drag_mouse()
                    return False
                mts_dlg.menu_select('开始(S)->退出测试模式')
            except Exception as e:
                raise NotImplementedError('进入测试失败')
            else:
                # 弹出确认框
                mts = self.app['MTS']
                mts.Button.click()  # 是
                time.sleep(3)
                return False

    def enter_test_mode(self, cellid, mode):
        if self.modify_test_mode(cellid, mode):
            return True
        else:
            return False

    def create_ue(self):
        '''
        创建UE
        :return:
        '''
        try:
            mts_dlg = self.app['MTS']

            tree_view = mts_dlg.TreeView
            navi_tree = tree_view
            uemenu = navi_tree.get_item('\\测试管理\\UE管理')
            time.sleep(.3)
            uemenu.click(button='right')
            menu = self.app.PopupMenu
            rect = menu.rectangle()
            coord = self.get_coords(rect)
            mouse.click(button='left', coords=coord)  # 点击右键弹出的建立模拟UE
            cell_choose = self.app.Dialog
            dlg_title = cell_choose.texts()[0]

            if dlg_title != '小区选择':
                logger.error('通讯超时')
                cell_choose.Button.click()  # 点击确定
                # 弹出小区选择对话框，选择小区下拉框为空
                cell_choose = self.app.Dialog
                # 选择小区下拉框
                cbox = cell_choose.ComboBox
                item_count = cbox.item_count()
                if item_count == 0:
                    logger.error('通讯超时')
                    cell_choose.Cancel.click()  # 点击取消
                    return False
                else:
                    return True
            else:
                cell_choose.Button.click()
                time.sleep(2)
                # 小区创建create UE
                cell_create = self.app.window(class_name='#32770')
                cell_create.Button.click()
                time.sleep(2)
                uplink_pusch_test = navi_tree.get_item('\\测试管理\\RCT测试项\\上行灵敏度测试')  # 上行灵敏度测试
                uplink_pusch_test.click(button='right')
                menu = self.app.PopupMenu
                rect = menu.rectangle()
                coord = self.get_coords(rect)
                mouse.click(button='left', coords=coord)  # 点击右键弹出的创建任务
                time.sleep(1)
                task_create = self.app.Dialog  # 创建任务对话框，点击确定即可
                time.sleep(1)
                task_create.Button.click()  # 确定按钮
                time.sleep(1)
                return True
        except Exception as e:
            logger.error('error:{}'.format(e))
            raise NotImplementedError('创建UE模块失败')

    def tick_tbbler(self, cord):
        '''
        勾选误码率TBBLER[0]-[9],AVERTBBLER
        :return:
        '''
        tbbler0 = [cord[0] + 60, cord[1] + 46]
        mouse.click(button='left', coords=tbbler0)
        for i in range(10):
            tbbler = [tbbler0[0], tbbler0[1] + 18]
            mouse.click(button='left', coords=tbbler)
            tbbler0 = tbbler

    def ready_for_check(self):
        '''
        读误码率前的准备操作，包括清空上面的表格，获取误码率表格的rect
        :return:
        '''
        self.clear_upper_table()
        mts_dlg = self.app['MTS']
        testdlg = mts_dlg.MDIClient.child_window(title='Uplink PUSCH test Statistics').child_window(
            class_name='SysTabControl32'
        )
        list_dlg = testdlg.child_window(class_name='#32770')
        listbox = list_dlg.ListView2
        rect = listbox.rectangle()
        print(rect)
        coord = self.get_coords(rect)
        # coord = (581, 434)
        self.click_pop_clear(coord)  # 点击清空

        return coord

    def click_pop_menu(self, coord):
        '''
        点击右键弹出的菜单暂停显示
        :param rect:
        :return:
        '''
        # after_coord=(coord[0]-300,coord[1]-100)  #由于右键位置在右下角，需要偏下
        after_coord = copy.deepcopy(coord)
        mouse.click(button='right', coords=after_coord)  # 右键弹出菜单
        time.sleep(.3)
        pop_coord = (after_coord[0] + 10, after_coord[1] + 5)  # 点击弹出的暂停显示
        mouse.click(button='left', coords=pop_coord)
        time.sleep(.2)

    def click_pop_clear(self, coord):
        '''
        点击右键清除选项
        :param rect:
        :return:
        '''
        # after_coord = (coord[0] - 300, coord[1] - 100)  # 由于右键位置在右下角，需要偏下
        after_coord = copy.deepcopy(coord)
        mouse.click(button='right', coords=after_coord)  # 右键弹出菜单
        time.sleep(.3)
        pop_coord = (after_coord[0] + 20, after_coord[1] + 30)  # 点击弹出的清空
        mouse.click(button='left', coords=pop_coord)
        time.sleep(.5)

    def clear_upper_table(self):
        '''
        清空误码率表格上面的另一张表
        :return:
        '''
        mts_dlg = self.app['MTS']
        testdlg = mts_dlg.MDIClient.child_window(title='Uplink PUSCH test Statistics').child_window(
            class_name='SysTabControl32'
        )
        list_dlg = testdlg.child_window(class_name='#32770')
        # print(list_dlg.print_control_identifiers())
        time.sleep(.5)
        # listbox = list_dlg.descendants(class_name='SysListView32')[0]
        listbox = list_dlg.ListView
        rect = listbox.rectangle()
        coord = self.get_coords(rect)
        self.click_pop_menu(coord)  # 暂停显示
        self.click_pop_clear(coord)  # 清空

    def check_result(self, coord):
        '''
        查看误码率列表
        :return:字符串列表
        '''
        try:
            logger.debug('exe check_result')
            time.sleep(9)
            # 点击右键暂停显示
            self.click_pop_menu(coord)
            # 读取暂停后的列表内容
            berlist = self.get_ber()  # 大约3秒
            self.click_pop_clear(coord)  # 点击清空
            # 再点击继续显示菜单
            self.click_pop_menu(coord)

            return berlist
        except Exception as e:
            logger.error('check result error:{}'.format(e))
            return None

    def get_ber(self):
        '''
        得到误码率,取前10行即可
        :return:intlist
        '''
        try:
            logger.debug('exe get_ber')
            mts_dlg = self.app['MTS']
            testdlg = mts_dlg.MDIClient.child_window(title='Uplink PUSCH test Statistics').child_window(
                class_name='SysTabControl32'
            )
            list_dlg = testdlg.child_window(class_name='#32770')
            # listbox = mts_dlg.Dialog2.TabControl.ListBox2  # PUSCH test statics TAB下的第二张表
            listbox = list_dlg.ListView2
            row_count = listbox.item_count()
            target = 16
            berlist = []
            for index in range(0, row_count):  # 读AverTbbler这列
                berlist.append(float(listbox.get_item(index, target).text()))
            logger.debug(berlist)
            print(berlist)
            # allitems = listbox.children(control_type='ListItem')[:10]
            # allitems=listbox.items()
            # print('****')
            # items = allitems
            # print(items[0].text())
            # alllist = [item.text() for item in items]
            return berlist
        except Exception as e:
            logger.error(e)
            return None

    def close_exe(self):
        '''
        关闭软件
        :return:
        '''
        try:
            if self.app:
                mts_dlg = self.app['MTS']
                mts_dlg.close()

        except Exception as e:
            logger.error(e)
            time.sleep(3)
            closedlg = self.app.window(title='MTS', class_name='#32770')
            closedlg.Button.click()
            time.sleep(5)
            logger.error('close exe ok')



# 站点管理按钮点击
# app.Dialog.Button4.click()
# exe_path = r'F:\auto_test_projs\协议\测试灵敏度软件\81248125\TDD_Release -tdd-union\bin\MTS.exe'
if __name__ == '__main__':
    exe_path = r'F:\auto_test_projs\协议\测试灵敏度软件\T2K\bin\MTS.exe'

    exe = T2KEXEOperate()
    exe.start_exe('192.254.1.86', exe_path)
    # exe.close_exe()
    if exe.site_manage():
        exe.enter_test_mode(0, 'TDD')
        exe.create_ue()
        coord = exe.ready_for_check()

        exe.check_result(coord)

    # exe.close_exe()
