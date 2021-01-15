# coding:utf-8
'''
矢网的测试项，包括增益，带内波动，VSWR
一个曲线最多建10个marker
'''
import os
import logging
from commoninterface.zvlbase import ZVLBase

logger = logging.getLogger('ghost')


class HandleZVL(object):
    def __init__(self, ip, offset):
        self.zvl = None
        self.ip = ip
        self.offset = float(offset)

    def init_zvl(self, path):
        logger.debug('init zvl')
        self.zvl = ZVLBase()
        self.zvl.init_inst(self.ip)
        self.zvl.reset_zvl()
        self.path = path  # 存储图片的路径

    def close_zvl(self):
        self.zvl.close_inst()

    def set_edge(self, low_edge, up_edge):
        '''

        :param low_edge: float单位MHz
        :param up_edge: float单位MHz
        :return:
        '''
        try:
            low = '{}MHz'.format(low_edge)
            up = '{}MHz'.format(up_edge)
            self.zvl.set_freq(low, up)
            return True
        except Exception as e:
            logger.error('set_edge error {}'.format(e))
            return False

    def set_trace(self, tracen, form, means):
        '''

        :param tracen: int
        form:str,
        means:str,'S11','S12','S21','S22'
        :return:
        '''
        try:

            self.zvl.set_trace_form(tracen, form)
            self.zvl.change_trace_meas(tracen, means)
            if form == 'MLOG':
                self.zvl.set_div_value(tracen, 10)
                # zvl.set_ref_value(zvlhandler, tracen, -40)
            return True
        except Exception as e:
            logger.error('set_trace error {}'.format(e))
            return False

    def read_markery(self, tracen, markern, x):
        x_str = '{}MHz'.format(x)
        self.zvl.set_trace_marker(tracen, markern, x_str)  # 设置marker点
        _, marker1y = self.zvl.query_marker(tracen, markern)
        return marker1y

    def read_max_marker(self, tracen, markern):
        try:
            self.zvl.create_max_marker(tracen, markern)  # max marker
            # create_max_marker(zvlhandler, tracen, markern + 1)  # max marker
            marker1x, marker1y = self.zvl.query_marker(tracen, markern)
            return float(marker1x) / 1000000.0, marker1y
        except Exception as e:
            logger.error('get_max_loss error {}'.format(e))
            return None

    def get_ripple_in_bw(self, tracen, markern):
        '''
        带内波动
        :return:
        '''
        try:
            self.zvl.create_min_marker(tracen, markern)  # min marker
            self.zvl.create_max_marker(tracen, markern + 1)  # max marker
            _, marker1y = self.zvl.query_marker(tracen, markern)
            _, marker2y = self.zvl.query_marker(tracen, markern + 1)
            absy = abs(float(marker1y) - float(marker2y))
            return absy

        except Exception as e:
            logger.error('get_ripple_in_bw error{}'.format(e))
            return None

    def get_gain(self, *args):
        '''
        读取增益及带内波动
        S21 dBmg
        :return:高，中，低点增益，带内波动
        '''
        logger.debug('zvl get gain')
        high, mid, low = args  # 高中低
        self.zvl.remove_allmarker(1)
        self.set_edge(low, high)
        tracen = 1
        self.set_trace(tracen, 'MLOG', 'S21')
        markern = 1
        # 读高，中，低点的增益
        high_markery = float(self.read_markery(tracen, markern, high))
        markern += 1
        mid_markery = float(self.read_markery(tracen, markern, mid))
        markern += 1
        low_markery = float(self.read_markery(tracen, markern, low))
        # 带内波动
        markern += 1
        ripple = self.get_ripple_in_bw(tracen, markern)  # 绝对值
        ret = [high_markery + self.offset, mid_markery + self.offset,
               low_markery + self.offset, ripple]
        ret2 = ['%.2f' % float(item) for item in ret]
        return ret2

    def get_vswr(self, *args):
        '''
        VSWR S11,SWR
        :return:max markerx,max markery
        '''
        logger.debug('zvl get_vswr')
        self.zvl.remove_allmarker(1)
        high, mid, low, dl_ul,temp = args  # 高中低
        tracen = 1
        markern = 1
        start = float(low) - 2.5
        end = float(high) + 2.5
        self.set_edge(start, end)
        self.set_trace(tracen, 'SWR', 'S11')
        marker = self.read_max_marker(tracen, markern)
        # 截图
        pngpath = os.path.join(os.path.dirname(self.path), '{}{}_{}_VSWR.PNG'.format(temp, dl_ul,end))
        self.zvl.save_screenshot(r'c:\\Temp\\1.PNG', r'{}'.format(pngpath))
        # mstr='@'.join([str(item) for item in marker])
        marker2 = ['%.2f' % float(item) for item in marker]
        return marker2

    def get_gain_vs_freq(self, markerlist,dl_ul, temp):
        '''
        825~835MHz,870~880,890~915,935~960,1570.42~1585,
        1710~1785,1805~1880,1920~1980,2110~2170,
        2570~2620,1880~1915,2300~2400,2400~2483.5
        截图三张,一张图最多截10个marker
        markerlist:[]
        :return:
        '''

        logger.debug('zvl get_gain_vs_freq')
        self.zvl.remove_allmarker(1)
        tracen = 1
        markern = 1
        self.set_trace(tracen, 'MLOG', 'S21')
        markery_list = []  # 所有点的增益，注意要加上offset
        try:
            # 第一张图
            self.set_edge(700, 1700)
            marker_lst = markerlist[:10]
            for marker in marker_lst:
                mstr = '{}MHz'.format(marker)
                self.zvl.set_trace_marker(tracen, markern, mstr)
                _, marker1y = self.zvl.query_marker(tracen, markern)  # str
                markery_list.append(marker1y)
                markern += 1
            pngpath = os.path.join(os.path.dirname(self.path), '{}{}_gain_vs_freq_1.PNG'.format(temp,dl_ul))
            self.zvl.save_screenshot(r'c:\\Temp\\1.PNG', r'{}'.format(pngpath))
            self.zvl.remove_allmarker(1)
            # 第二张图
            marker_lst = markerlist[10:20]
            markern = 1
            self.set_edge(1700, 3000)
            for marker in marker_lst:
                mstr = '{}MHz'.format(marker)
                self.zvl.set_trace_marker(tracen, markern, mstr)
                _, marker1y = self.zvl.query_marker(tracen, markern)
                markery_list.append(marker1y)
                markern += 1
            pngpath = os.path.join(os.path.dirname(self.path), '{}{}_gain_vs_freq_2.PNG'.format(temp,dl_ul))
            self.zvl.save_screenshot(r'c:\\Temp\\1.PNG', r'{}'.format(pngpath))
            self.zvl.remove_allmarker(1)
            # 第三张图
            marker_lst = markerlist[20:]
            markern = 1
            for marker in marker_lst:
                mstr = '{}MHz'.format(marker)
                self.zvl.set_trace_marker(tracen, markern, mstr)
                _, marker1y = self.zvl.query_marker(tracen, markern)
                markery_list.append(marker1y)
                markern += 1
            pngpath = os.path.join(os.path.dirname(self.path), '{}{}_gain_vs_freq_3.PNG'.format(temp,dl_ul))
            self.zvl.save_screenshot(r'c:\\Temp\\1.PNG', r'{}'.format(pngpath))
        except Exception as e:
            logger.error(e)
        finally:
            # logger.debug(markery_list)
            ret = ['%.2f' % (float(item) + self.offset) for item in markery_list]
            return ret
