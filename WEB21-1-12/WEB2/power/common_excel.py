# coding:utf-8
import logging
import xlwings as xw
import pandas as pd
import re
import pythoncom
logger = logging.getLogger('ghost')


class BoardExcel(object):
    '''
    功放测试模板
    '''
    sheets_name = ['功放测试下行', '上行']

    dl_keywords = ['功放设定', 'Gain测试', '带内波动测试', 'VSWR测试', 'EVM测试',
                   'gain_vs_freq测试', '工作电流和功率测试', 'ACPR测试']  # 下行测试各小表的关键字
    suffix = ['开始', '结束']

    dl_rows = dict()
    ul_rows = dict()
    jump_row = 2  # 每张小表的开头两行跳过标题

    def open_excel(self, path):
        try:
            pythoncom.CoInitialize()
            self.app = xw.App(visible=False, add_book=False)
            self.app.display_alerts = False
            self.app.screen_updating = False
            self.wb = self.app.books.open(r'{}'.format(path))
            # self.wb = xw.Book(r'{}'.format(path))
            return True
        except Exception as e:
            raise NotImplementedError('no excel file')

    def set_sheetnum(self, num):
        self.sheet_num = int(num)

    def get_first_cell(self, shtname):
        '''
        获得所有行的第一个单元格内容
        :return:
        '''
        sht = self.wb.sheets(shtname)
        rowcount = sht.api.UsedRange.Rows.count
        rng = sht.range('A1:A{}'.format(rowcount))
        lst = rng.value
        return lst

    def get_dl_rows(self):
        '''
        获得下行所有关键字对应的小表的行号
        :return:
        '''
        ul_shtname = self.sheets_name[0]
        cell_lst = self.get_first_cell(ul_shtname)
        item_idx = {k: [] for k in self.dl_keywords}
        for idx, item in enumerate(cell_lst):
            if item is None:
                continue
            for keyword in self.dl_keywords:
                startkeyword = keyword + self.suffix[0]
                endkeyword = keyword + self.suffix[1]

                if item.startswith(startkeyword):
                    item_idx[keyword].append(idx + 1 + 1)
                if item.startswith(endkeyword):
                    item_idx[keyword].append(idx)
        self.dl_rows = item_idx

    def get_ul_rows(self):
        '''
        获得上行所有关键字对应的小表的行号
        :return:
        '''
        ul_shtname = self.sheets_name[1]
        cell_lst = self.get_first_cell(ul_shtname)
        item_idx = {k: [] for k in self.dl_keywords}
        for idx, item in enumerate(cell_lst):
            if item is None:
                continue
            for keyword in self.dl_keywords:
                startkeyword = keyword + self.suffix[0]  # 从测试开始
                endkeyword = keyword + self.suffix[1]  # 到测试结束

                if item.startswith(startkeyword):
                    item_idx[keyword].append(idx + 1 + 1)
                if item.startswith(endkeyword):
                    item_idx[keyword].append(idx)
        self.ul_rows = item_idx

    def get_id(self):
        '''
        获取基带板id
        :return:str
        '''
        try:
            sht = self.wb.sheets(BoardExcel.sheets_name[0])
            id = str(sht.range('B1').value)
            sn = str(sht.range('B2').value)
            return id, sn
        except Exception as e:
            raise ValueError('get_id error:{}'.format(e))
        finally:
            self.close_file()

    def get_band_para(self):
        '''
        获取基带设定条件
        :return:dataframe
                    中       低       高
B1  DL  2140.0  2112.5  2167.5
    UL  1950.0  1922.5  1977.5
B3  DL  1842.5  1807.5  1877.5
    UL  1747.5  1712.5  1782.5
B41 DL  2595.0  2557.5  2652.5
    UL  2595.0  2557.5  2652.5
E   DL  2350.0  2302.5  2397.5
    UL  2350.0  2302.5  2397.5
F   DL  1900.0  1882.5  1917.5
    UL  1900.0  1882.5  1917.5
        '''
        try:
            rows = self.dl_rows['功放设定']
            sht = self.wb.sheets(BoardExcel.sheets_name[0])
            startrow = rows[0]
            endrow = rows[1]
            df = sht.range('A{}:G{}'.format(startrow, endrow)).options(pd.DataFrame, header=2).value
            df.columns = [['高', '高', '中', '中', '低', '低'], ['DL', 'UL'] * 3]
            return df.stack()
        except Exception as e:
            raise ValueError('get_band_para error:{}'.format(e))

    def get_each_cellband_row(self, shtname, start, end):
        '''
        获得每个子表的cell_band的所在行
        :return:{'E':68}
        '''
        sht = self.wb.sheets(shtname)
        rng = sht.range('A{}:A{}'.format(start, end))
        lst = rng.value
        cell_dict = {}  # {}
        for idx, cell in enumerate(lst):
            if cell is None:
                continue
            cell = cell.upper()
            newcell = cell.strip()
            cell_dict.setdefault(newcell, idx + start)
        return cell_dict

    def get_gain_vs_freq_list(self, band):
        '''
        带外抑制的marker点
        :return:
        '''
        try:
            shtname = BoardExcel.sheets_name[self.sheet_num]
            sht = self.wb.sheets(shtname)
            if self.sheet_num == 0:
                rows_rng = self.dl_rows
            else:
                rows_rng = self.ul_rows
            rows = rows_rng['gain_vs_freq测试']
            row_dict = self.get_each_cellband_row(shtname, rows[0], rows[1])
            startrow = row_dict[str(band).upper()]
            value = None
            endrow = startrow
            # 向下遍历直到碰到非空白，即找到合并单元格的范围
            while value is None:
                endrow += 1
                rng = sht.range('A{}'.format(endrow))
                value = rng.value
                if value:
                    break
            rng = sht.range('B{}:B{}'.format(startrow, endrow - 1))
            lst = rng.value  # 返回列表
            return lst
        except Exception as e:
            logger.error('get_gain_vs_freq_list:{}'.format(e))
            return None

    def get_gain_dl_marker(self, band):
        '''
        获取下行测试增益的marker点
        :param band:
        :return:
        '''
        try:
            shtname = BoardExcel.sheets_name[0]
            sht = self.wb.sheets(shtname)
            rows_rng = self.dl_rows
            rows = rows_rng['Gain测试']
            row_dict = self.get_each_cellband_row(shtname, rows[0], rows[1])
            startrow = row_dict[str(band).upper()]
            value = None
            endrow = startrow
            # 向下遍历直到碰到非空白，即找到合并单元格的范围
            while value is None:
                endrow += 1
                rng = sht.range('A{}'.format(endrow))
                value = rng.value
                if value:
                    break
            rng = sht.range('B{}:B{}'.format(startrow, endrow - 1))
            lst = rng.value  # 返回列表
            return lst
        except Exception as e:
            logger.error('get_gain_dl_marker:{}'.format(e))
            return None

    def write_gain(self, temp=1, **kwargs):
        '''
        更新上行增益及带内波动
        :param kwargs:{'E':[，，，]}
        :return:
        '''
        try:
            shtname = BoardExcel.sheets_name[self.sheet_num]
            sht = self.wb.sheets(shtname)
            if self.sheet_num == 0:
                rows_rng = self.dl_rows
            else:
                rows_rng = self.ul_rows
            gain_rows = rows_rng['Gain测试']
            ripple_rows = rows_rng['带内波动测试']
            temp_rows = [['F', 'G'], ['H', 'I'], ['J', 'K']]  # 低温，常温，高温所在列
            value_row_base, norm_row_base = temp_rows[int(temp)]  # 常温结果所在列,常温结论所在列

            gain_row_dict = self.get_each_cellband_row(shtname, gain_rows[0], gain_rows[1])
            ripple_row_dict = self.get_each_cellband_row(shtname, ripple_rows[0], ripple_rows[1])

            for key, item in kwargs.items():
                if len(item) == 0:
                    continue
                gain_row_idx = gain_row_dict[key.upper()]
                ripple_row_idx = ripple_row_dict[key.upper()]
                gain_norm_dict = self.get_norm(shtname, gain_row_idx)

                ripple_norm_dict = self.get_norm(shtname, ripple_row_idx)

                # 记录增益
                row_range = value_row_base + str(gain_row_idx)
                norm_range = norm_row_base + str(gain_row_idx)
                lst = item[:-1]
                norm_lst = self.set_gain_conclusion(lst, gain_norm_dict)
                sht.range('{}'.format(row_range)).options(transpose=True).value = lst
                sht.range('{}'.format(norm_range)).options(transpose=True).value = norm_lst
                # 记录带内波动
                row_range = value_row_base + str(ripple_row_idx)
                norm_range = norm_row_base + str(ripple_row_idx)
                val = item[-1]
                norm = self.set_ripple_conclusion(val, ripple_norm_dict)
                sht.range('{}'.format(row_range)).options(transpose=True).value = val
                sht.range('{}'.format(norm_range)).options(transpose=True).value = norm

        except Exception as e:
            logger.error('write gain error:{}'.format(e))
        else:
            self.wb.save()

    def write_dl_gain(self, temp=1, **kwargs):
        '''
        下行的增益
        :param temp:
        :param kwargs:{'E':[(信号源输入，频谱输出，增益)，(信号源输入，频谱输出，增益),()]}
        :return:
        '''
        logger.debug('dl_gain={}'.format(kwargs))
        try:
            shtname = BoardExcel.sheets_name[self.sheet_num]
            sht = self.wb.sheets(shtname)
            if self.sheet_num == 0:
                rows_rng = self.dl_rows
            else:
                rows_rng = self.ul_rows
            rows = rows_rng['Gain测试']
            temp_rows = [['F', 'G', 'H', 'I'], ['J', 'K', 'L', 'M'], ['N', 'O', 'P', 'Q']]  # 低温，常温，高温所在列
            value_row_base, _, _, norm_row_base = temp_rows[int(temp)]  # 常温结果所在列,常温结论所在列
            row_dict = self.get_each_cellband_row(shtname, rows[0], rows[1])
            for key, item in kwargs.items():
                row_idx = row_dict[key.upper()]
                norm_list = self.get_norm(shtname, row_idx)
                row_range = value_row_base + str(row_idx)
                norm_range = norm_row_base + str(row_idx)
                sht.range('{}'.format(row_range)).options(expand='table').value = item
                con_list = []
                for i in item:
                    if len(i) >= 3:  #
                        conclu = self.set_ripple_conclusion(i[2], norm_list)
                        con_list.append(conclu)
                sht.range('{}'.format(norm_range)).options(transpose=True).value = con_list

        except Exception as e:
            logger.error('write_dl_gain error:{}'.format(e))
        else:
            self.wb.save()

    def write_ripple(self, temp=1, **kwargs):
        logger.debug('ripple_dict={}'.format(kwargs))
        try:
            shtname = BoardExcel.sheets_name[self.sheet_num]
            sht = self.wb.sheets(shtname)
            if self.sheet_num == 0:
                rows_rng = self.dl_rows
            else:
                rows_rng = self.ul_rows
            ripple_rows = rows_rng['带内波动测试']
            temp_rows = [['F', 'G'], ['H', 'I'], ['J', 'K']]  # 低温，常温，高温所在列
            value_row_base, norm_row_base = temp_rows[int(temp)]  # 常温结果所在列,常温结论所在列

            ripple_row_dict = self.get_each_cellband_row(shtname, ripple_rows[0], ripple_rows[1])

            for key, item in kwargs.items():
                ripple_row_idx = ripple_row_dict[key.upper()]
                ripple_norm_dict = self.get_norm(shtname, ripple_row_idx)
                # 记录带内波动
                row_range = value_row_base + str(ripple_row_idx)
                norm_range = norm_row_base + str(ripple_row_idx)
                val = '%.2f'%float(item)
                norm = self.set_ripple_conclusion(val, ripple_norm_dict)
                sht.range('{}'.format(row_range)).options(transpose=True).value = val
                sht.range('{}'.format(norm_range)).options(transpose=True).value = norm

        except Exception as e:
            logger.error('write_ripple error:{}'.format(e))
        else:
            self.wb.save()

    def write_vswr(self, temp=1, **kwargs):
        '''
        记录vswr
        :return:
        '''
        logger.debug('vswr={}'.format(kwargs))
        try:
            shtname = BoardExcel.sheets_name[self.sheet_num]
            sht = self.wb.sheets(shtname)
            if self.sheet_num == 0:
                rows_rng = self.dl_rows
            else:
                rows_rng = self.ul_rows
            rows = rows_rng['VSWR测试']

            temp_rows = [['F', 'G'], ['H', 'I'], ['J', 'K']]  # 低温，常温，高温所在列
            value_row_base, norm_row_base = temp_rows[int(temp)]  # 常温结果所在列,常温结论所在列

            row_dict = self.get_each_cellband_row(shtname, rows[0], rows[1])

            for key, item in kwargs.items():
                if len(item) == 0:
                    continue
                row_idx = row_dict[key.upper()]
                norm_dict = self.get_norm(shtname, row_idx)
                row_range = value_row_base + str(row_idx)
                norm_range = norm_row_base + str(row_idx)
                freq, db = item
                norm = self.set_ripple_conclusion(db, norm_dict)
                sht.range('{}'.format(row_range)).options(transpose=True).value = '@'.join([str(db), str(freq) + 'MHz'])
                sht.range('{}'.format(norm_range)).options(transpose=True).value = norm

        except Exception as e:
            logger.error('write gain error:{}'.format(e))
        else:
            self.wb.save()

    def write_gain_vs_freq(self, temp=1, **kwargs):
        '''
        记录gain_vs_frequency
        :return:
        '''
        logger.debug('gain_vs_freq={}'.format(kwargs))
        try:
            shtname = BoardExcel.sheets_name[self.sheet_num]
            sht = self.wb.sheets(shtname)
            if self.sheet_num == 0:
                rows_rng = self.dl_rows
            else:
                rows_rng = self.ul_rows
            rows = rows_rng['gain_vs_freq测试']

            temp_rows = [['F', 'G'], ['H', 'I'], ['J', 'K']]  # 低温，常温，高温所在列
            value_row_base, norm_row_base = temp_rows[int(temp)]  # 常温结果所在列,常温结论所在列
            row_dict = self.get_each_cellband_row(shtname, rows[0], rows[1])
            for key, item in kwargs.items():
                if len(item) == 0:
                    continue
                row_idx = row_dict[key.upper()]
                row_range = value_row_base + str(row_idx)
                sht.range('{}'.format(row_range)).options(transpose=True).value = item
        except Exception as e:
            logger.error('write gain error:{}'.format(e))
        else:
            self.wb.save()

    def write_current(self, temp=1, **kwargs):
        '''
        工作电流测试结果,暂时没有电流，所以没有结论
        {'E':[(信号源输入，频谱仪输出),(,),(,)]}
        :return:
        '''
        try:
            shtname = BoardExcel.sheets_name[self.sheet_num]
            sht = self.wb.sheets(shtname)
            if self.sheet_num == 0:
                rows_rng = self.dl_rows
            else:
                rows_rng = self.ul_rows
            rows = rows_rng['工作电流和功率测试']

            temp_rows = [['F', 'G', 'H', 'I'], ['J', 'K', 'L', 'M'], ['N', 'O', 'P', 'Q']]  # 低温，常温，高温所在列
            value_row_base, _, _, norm_row_base = temp_rows[int(temp)]  # 常温结果所在列,常温结论所在列
            row_dict = self.get_each_cellband_row(shtname, rows[0], rows[1])
            for key, item in kwargs.items():
                row_idx = row_dict[key.upper()]
                row_range = value_row_base + str(row_idx)

                sht.range('{}'.format(row_range)).options(expand='table').value = item
        except Exception as e:
            logger.error('write_current error:{}'.format(e))
        else:
            self.wb.save()

    def write_ACPR(self, temp=1, **kwargs):
        '''

        :param temp:
        :param kwargs: {'E':['lower/upper','','']}
        :return:
        '''
        try:
            shtname = BoardExcel.sheets_name[self.sheet_num]
            sht = self.wb.sheets(shtname)
            if self.sheet_num == 0:
                rows_rng = self.dl_rows
            else:
                rows_rng = self.ul_rows
            rows = rows_rng['ACPR测试']

            temp_rows = [['F', 'G'], ['H', 'I'], ['J', 'K']]  # 低温，常温，高温所在列
            value_row_base, norm_row_base = temp_rows[int(temp)]  # 常温结果所在列,常温结论所在列

            row_dict = self.get_each_cellband_row(shtname, rows[0], rows[1])

            for key, item in kwargs.items():
                row_idx = row_dict[key.upper()]
                norm_dict = self.get_norm(shtname, row_idx)
                row_range = value_row_base + str(row_idx)
                norm_range = norm_row_base + str(row_idx)
                norm_lst = []
                for i in item:
                    tlst = i.split('/')
                    norm = self.set_acpr_conclusion(tlst, norm_dict)
                    norm_lst.append(norm)
                sht.range('{}'.format(row_range)).options(transpose=True).value = item
                sht.range('{}'.format(norm_range)).options(transpose=True).value = norm_lst

        except Exception as e:
            logger.error('write ACPR error:{}'.format(e))
        else:
            self.wb.save()

    def write_EVM(self, temp=1, **kwargs):
        '''
        如果有EVM(功放)就写结论，因为标准是给功放定的
        :param temp:
        :param kwargs: {'E':[(EVM（功放+信号源）,EVM(信号源),EVM(功放)),(,,,)]}
        :return:
        '''
        try:
            shtname = BoardExcel.sheets_name[self.sheet_num]
            sht = self.wb.sheets(shtname)
            if self.sheet_num == 0:
                rows_rng = self.dl_rows
            else:
                rows_rng = self.ul_rows
            rows = rows_rng['EVM测试']

            temp_rows = [['F', 'G', 'H', 'I'], ['J', 'K', 'L', 'M'], ['N', 'O', 'P', 'Q']]  # 低温，常温，高温所在列
            value_row_base, _, _, norm_row_base = temp_rows[int(temp)]  # 常温结果所在列,常温结论所在列
            row_dict = self.get_each_cellband_row(shtname, rows[0], rows[1])
            for key, item in kwargs.items():
                row_idx = row_dict[key.upper()]
                norm_list = self.get_norm(shtname, row_idx)
                row_range = value_row_base + str(row_idx)
                norm_range = norm_row_base + str(row_idx)
                sht.range('{}'.format(row_range)).options(expand='table').value = item
                con_list = []
                for i in item:
                    if len(i) >= 3:  # 有功放EVM就写结论
                        conclu = self.set_ripple_conclusion(i[2], norm_list)
                        con_list.append(conclu)
                sht.range('{}'.format(norm_range)).options(transpose=True).value = con_list

        except Exception as e:
            logger.error('write_EVM error:{}'.format(e))
        else:
            self.wb.save()

    def get_evm(self, temp, band):
        '''
        获取EVM(信号源)
        :return:[高，中，低]
        '''
        try:
            shtname = BoardExcel.sheets_name[self.sheet_num]
            sht = self.wb.sheets(shtname)
            if self.sheet_num == 0:
                rows_rng = self.dl_rows
            else:
                rows_rng = self.ul_rows
            rows = rows_rng['EVM测试']

            temp_rows = [['F', 'G', 'H', 'I'], ['J', 'K', 'L', 'M'], ['N', 'O', 'P', 'Q']]  # 低温，常温，高温所在列
            _, value_row_base, _, norm_row_base = temp_rows[int(temp)]  # 常温结果所在列,常温结论所在列
            row_dict = self.get_each_cellband_row(shtname, rows[0], rows[1])
            first = row_dict[band]
            first_row = value_row_base + str(first)
            end_row = value_row_base + str(first + 2)

            evm = sht.range('{}:{}'.format(first_row, end_row)).options(transpose=True).value
            return evm
        except Exception as e:
            logger.error('get_evm error:{}'.format(e))
            return None

    def get_target_power(self, band):
        '''
        获取增益的标准输出功率
        band:'E','F'
        :return:
        '''
        try:
            shtname = BoardExcel.sheets_name[self.sheet_num]
            # sht = self.wb.sheets(shtname)
            if self.sheet_num == 0:
                rows_rng = self.dl_rows
            else:
                rows_rng = self.ul_rows
            rows = rows_rng['Gain测试']
            row_dict = self.get_each_cellband_row(shtname, rows[0], rows[1])
            row_idx = row_dict[band]
            norm_list = self.get_norm(shtname, row_idx)
            # 标准值
            targetstr = norm_list[1].split('@')[1]  # 带dBm的字符串
            target = float(re.findall(r'-?\d+\.?\d*e?-?\d*?', str(targetstr))[0])
            return target
        except Exception as e:
            logger.error('get_target_power error')
            return None

    def get_target_power_for_evm(self, band):
        '''
        获取EVM的标准输出功率
        :param band:
        :return:
        '''
        try:
            shtname = BoardExcel.sheets_name[self.sheet_num]
            # sht = self.wb.sheets(shtname)
            if self.sheet_num == 0:
                rows_rng = self.dl_rows
            else:
                rows_rng = self.ul_rows
            rows = rows_rng['工作电流和功率测试']
            row_dict = self.get_each_cellband_row(shtname, rows[0], rows[1])
            row_idx = row_dict[band]
            norm_list = self.get_norm(shtname, row_idx)
            # 标准值
            targetstr = norm_list[1].split('@')[1]  # 带dBm的字符串
            target = float(re.findall(r'-?\d+\.?\d*e?-?\d*?', str(targetstr))[0])
            return target
        except Exception as e:
            logger.error('get_target_power error')
            return None

    def get_level_input(self, temp, band):
        '''
        获取工作电流时信号源输入
        :param temp:
        :param band:
        :return:[]
        '''
        try:
            shtname = BoardExcel.sheets_name[self.sheet_num]
            sht = self.wb.sheets(shtname)
            if self.sheet_num == 0:
                rows_rng = self.dl_rows
            else:
                rows_rng = self.ul_rows
            rows = rows_rng['工作电流和功率测试']

            temp_rows = [['F', 'G', 'H', 'I'], ['J', 'K', 'L', 'M'], ['N', 'O', 'P', 'Q']]  # 低温，常温，高温所在列
            value_row_base, _, _, norm_row_base = temp_rows[int(temp)]  # 常温结果所在列,常温结论所在列
            row_dict = self.get_each_cellband_row(shtname, rows[0], rows[1])
            first = row_dict[band]
            first_row = value_row_base + str(first)
            end_row = value_row_base + str(first + 2)

            evm = sht.range('{}:{}'.format(first_row, end_row)).options(transpose=True).value
            return evm
        except Exception as e:
            logger.error('get_level_input error:{}'.format(e))
            return None

    def get_norm(self, shtname, startrow):
        '''
        读取指标规范,去掉有的指标中的@ ,%等字符，只提取数字
        :return:[下限，标准值，上限]
        '''
        try:
            sht = self.wb.sheets(shtname)
            dt = sht.range('C{}:E{}'.format(startrow, startrow)).value
            retlist = []
            for idx, item in enumerate(dt):
                if idx == 1:  # 标准值不变
                    retlist.append(item)
                    continue
                if item:
                    item = str(item).split('@')[0]
                    item = float(re.findall(r'-?\d+\.?\d*e?-?\d*?', str(item))[0])
                retlist.append(item)
            return retlist
        except Exception as e:
            logger.exception('get_norm error:{}'.format(e))
            return None

    def set_ripple_conclusion(self, ppm, norm_list):
        '''
        单个值满足上下限
        :param ppm: ppm/crest factor
        :param norm_list:[下限，标准值，上限]
        :return:
        '''
        try:
            if ppm is None:
                return 'FAIL'
            if norm_list is None:
                return ''
            flag_lst = []

            new_norm = [float(re.findall(r'-?\d+\.?\d*e?-?\d*?', str(item))[0])
                        if item is not None else None for
                        item in norm_list]
            if new_norm[0] is not None:
                indicator = '>='
                if indicator:
                    e1 = str(ppm) + indicator + str(new_norm[0])
                    if eval(e1):
                        flag_lst.append(True)
                    else:
                        return 'FAIL'
            if new_norm[2] is not None:
                indicator = '<='
                if indicator:
                    e1 = str(ppm) + indicator + str(new_norm[2])
                    if eval(e1):
                        flag_lst.append(True)
                    else:
                        return 'FAIL'

            if not flag_lst:
                return ''
            return 'PASS' if all(flag_lst) else 'FAIL'
        except Exception as e:
            logger.exception(e)
            return ''

    def set_gain_conclusion(self, gain_list, norm_list):
        '''
        多个值，返回多个结果
        :param gain_list:
        :param norm_list:[下限，标准，上限]
        :return: []
        '''
        try:
            if norm_list is None:
                return None
            indicator1 = None
            indicator2 = None
            con_list = []
            # for  item in norm_list:
            #     value = float(re.findall(r'-?\d+\.?\d*e?-?\d*?', str(item))[0]) if item is not None else None
            #     if value is None:
            #         continue
            new_norm = [float(re.findall(r'-?\d+\.?\d*e?-?\d*?', str(item))[0])
                        if item is not None else None for
                        item in norm_list]
            if new_norm[0] is not None:
                indicator1 = '>=' + str(new_norm[0])
            if new_norm[2] is not None:
                indicator2 = '<=' + str(new_norm[2])

            for power in gain_list:
                if indicator1 and indicator2:
                    e1 = str(power) + indicator1
                    e2 = str(power) + indicator2
                    if eval(e1) and eval(e2):
                        con_list.append('PASS')
                    else:
                        con_list.append('FAIL')
                elif indicator1:
                    e1 = str(power) + indicator1
                    if eval(e1):
                        con_list.append('PASS')
                    else:
                        con_list.append('FAIL')
                elif indicator2:
                    e1 = str(power) + indicator2
                    if eval(e1):
                        con_list.append('PASS')
                    else:
                        con_list.append('FAIL')
            return con_list
        except Exception as e:
            logger.error('set_gain_conclusion error:{}'.format(e))
            return None

    def set_acpr_conclusion(self, lst, nlst):
        '''
        多个值，一个结果
        :param lst:
        :param nlst:
        :return:
        '''
        try:
            if nlst is None:
                return None
            indicator1 = None
            indicator2 = None
            con_list = []

            new_norm = [float(re.findall(r'-?\d+\.?\d*e?-?\d*?', str(item))[0])
                        if item is not None else None for
                        item in nlst]
            if new_norm[0] is not None:
                indicator1 = '>=' + str(new_norm[0])
            if new_norm[2] is not None:
                indicator2 = '<=' + str(new_norm[2])

            for item in lst:
                if indicator1 and indicator2:
                    e1 = str(item) + indicator1
                    e2 = str(item) + indicator2
                    if eval(e1) and eval(e2):
                        con_list.append('PASS')
                    else:
                        con_list.append('FAIL')
                elif indicator1:
                    e1 = str(item) + indicator1
                    if eval(e1):
                        con_list.append('PASS')
                    else:
                        return 'FAIL'
                elif indicator2:
                    e1 = str(item) + indicator2
                    if eval(e1):
                        con_list.append('PASS')
                    else:
                        return 'FAIL'
            if not con_list:
                return None
            return 'PASS' if all(con_list) else 'FAIL'
        except Exception as e:
            logger.error('set_acpr_conclusion error:{}'.format(e))
            return None

    def close_file(self):
        try:
            if hasattr(self, 'wb'):
                self.wb.close()
                del self.wb
            if hasattr(self, 'app'):
                self.app.quit()
                del self.app

        except Exception as e:
            logger.error('{}'.format(e))


if __name__ == '__main__':
    xel = BoardExcel()
    xel.open_excel('1.xlsx')
    xel.set_sheetnum(0)
    # df = xel.get_band_para()
    xel.get_dl_rows()
    xel.write_ripple(1,**{'E':1.55})
    # print(xel.get_norm('功放测试下行', 284))
    # xel.write_gain(**{'E': []})
    # print(xel.get_gain_dl_marker('B1'))
    # xel.get_evm(1,'E')
    # print(xel.get_target_power('E'))
    # df = xel.get_band_para()
    # print(df)

    # df2 = df.loc['B1', 'DL']
    # print(df2.loc[['高', '中', '低']])
    # a = ['B1', 'B3']
    # df1 = df.loc[a]
    # print(df1)

    # print(df['中', '频点'].apply(lambda x: int(x)))  # 返回Series
    # s1 = df.loc['B41', (slice(None), '频点')]  # series
    # print(s1.values)  # list
    # dt=xel.get_txatt_norm()
    # print(dt)
    # 3.
    # dt = {'cell0_E': [
    #     ['0.61', '-0.15', '-0.33', '-0.25', '-0.53', '1.53', '0.69', '1.23', '1.24',
    #      '1.26', '1.17', '1.39', '0.64',
    #      '1.26', '-0.34', '-0.27', '1.05', '-0.01', '1.43', '-0.46'],
    #     ['1.56', '-0.04', '0.73', '0.77', '0.80', '1.15', '0.48', '0.98', '0.95', '0.80', '-0.96', '0.83', '1.10',
    #      '-0.53', '1.76', '-0.84', '0.14', '0.38', '-0.85', '0.28'],
    #     ['0.61', '0.48', '-1.23', '0.64', '-0.89', '-0.59', '1.41', '0.60', '-1.18', '-1.01', '0.59', '0.41', '1.20',
    #      '0.52', '0.36', '-0.69', '-1.17', '-0.82', '-0.97', '-1.23']]}
    #
    # xel.write_power_range(**dt)
    # 4.
    # dt = {'cell0_E': [(0,-1,-25,-35),(0,-1.2,-20,-30)]}
    # xel.write_ACPR(**dt)
    # 5.
    # dt = {'E': ['-11/-22','-33/-44','-33/-77'],'F':['-11/-22','-33/-44','-33/-77']}
    # xel.write_ACPR(**dt)

    # print(xel.get_ACPR_norm())
    # 6.
    # xel.write_gain(**{'E': [1, 2, 3, 4], 'F': [2, 2, 2, 3]})
    # 7.
    # xel.write_EVM(**{'E': [(220,23,2.3),(11,12,1),(12,2,1)],'F':[(220,23,2.3),(11,12,1),(12,2,1)]})
    # print(xel.get_evm(1,'E'))
    # xel.close_file()
    # a = xel.get_normaltemp_level_rows()

    # a=xel.get_txatt_norm()
    # 1.
    # a=xel.get_max_row_in_temp('cell1_b1')
    # print(a)
    # 2.
    # dt={'cell0_E':[[7,0.2,-1,-1],[8,0.3,-2,-2],[7,0.2,-3,-3]]}
    # xel.write_max_txatt(**dt)
    # xel.write_txatt_conclusion()
    # 4.
    # xel.write_current(**{'E': [(1,2),(3,4),(5,6)],'F':[(11,12),(13,14),(15,16)]})

    xel.close_file()
