# coding:utf-8
import logging
import xlwings as xw
import pandas as pd
import re
import pythoncom
logger = logging.getLogger('ghost')


class BoardExcel(object):
    '''
    基带板测试模板
    '''
    sheets_name = ['基带板测试', '低温档位输出值', '常温档位输出值', '高温档位输出值', '上行']

    dl_keywords = ['基带设定', '输出功率测试', '带内波动测试', '可调精度测试', 'EVM测试', 'ACPR测试', '底噪测试',
                   '占用带宽测试', '频偏测试', '峰均比测试', '工作电流测试']  # 下行测试各小表的关键字
    suffix = ['开始', '结束']
    ul_keywords = ['基带设定', '接收灵敏度测试']

    dl_rows = dict()
    ul_rows = dict()
    ll_rows = dict()  # 低温档位输出表每个band所在的行
    hl_rows = dict()
    nl_rows = dict()  # 常温档位输出表
    jump_row = 3  # 每张小表的开头3行跳过标题

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

    def get_lowtemp_level_rows(self):
        '''
        获得低温档位输出值表的行所在行数
        :return:
        '''
        shtname = self.sheets_name[1]
        cell_lst = self.get_first_cell(shtname)  # 所有行首列单元格列表
        band_rows = dict()
        for idx, cell in enumerate(cell_lst):
            if cell is None:
                continue
            band_rows.setdefault(cell.upper(), idx + 1)
        self.ll_rows = band_rows

    def get_normaltemp_level_rows(self):
        '''
        获得常温档位输出值表的行数
        :return:
        '''
        shtname = self.sheets_name[2]
        cell_lst = self.get_first_cell(shtname)  # 所有行首列单元格列表
        band_rows = dict()
        for idx, cell in enumerate(cell_lst):
            if cell is None:
                continue
            band_rows.setdefault(cell.upper(), idx + 1)

        self.nl_rows = band_rows

    def get_hightemp_level_rows(self):
        '''
        获得高温档位输出值表的行数
        '''
        shtname = self.sheets_name[3]
        cell_lst = self.get_first_cell(shtname)  # 所有行首列单元格列表
        band_rows = dict()
        for idx, cell in enumerate(cell_lst):
            if cell is None:
                continue
            band_rows.setdefault(cell.upper(), idx + 1)
        self.hl_rows = band_rows

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

                if startkeyword in item:
                    item_idx[keyword].append(idx + 1 + 1)
                if endkeyword in item:
                    item_idx[keyword].append(idx)
        self.dl_rows = item_idx

    def get_ul_rows(self):
        '''
        获得上行所有关键字对应的小表的行号
        :return:
        '''
        ul_shtname = self.sheets_name[4]
        cell_lst = self.get_first_cell(ul_shtname)
        item_idx = {k: [] for k in self.ul_keywords}
        for idx, item in enumerate(cell_lst):
            if item is None:
                continue
            for keyword in self.ul_keywords:
                startkeyword = keyword + self.suffix[0]  # 从测试开始
                endkeyword = keyword + self.suffix[1]  # 到测试结束

                if startkeyword in item:
                    item_idx[keyword].append(idx + 1 + 1)
                if endkeyword in item:
                    item_idx[keyword].append(idx)

        self.ul_rows = item_idx

    def get_set_condition(self, cellid):
        '''
        cellid:0/1
        获取下行设定条件：测试板子类型，band,默认板子类型只有一种,要不都是8125，要不都是T2K
        :return:
        '''
        try:
            rows = self.dl_rows['基带设定']
            sht = self.wb.sheets(BoardExcel.sheets_name[0])
            startrow = rows[0] + 2
            endrow = rows[1]
            celllst = sht.range('A{}:G{}'.format(startrow, endrow)).value
            type = ''
            cellstr = 'cell{}'.format(cellid)
            bandstr = ''

            freqpoint_dict = dict()  # 高中低频点
            freq_dict = dict()  # 高中低频率
            for itemlst in celllst:
                for idx, item in enumerate(itemlst):
                    if item is None:
                        continue
                    if idx == 0:
                        temp = item.strip().split('_')
                        type = temp[0].upper()
                        thiscell = temp[2].lower()
                        bandstr = temp[3].upper()
                        if thiscell != cellstr:
                            break
                        continue
                    if idx % 2 != 0:
                        freqpoint_dict.setdefault(bandstr, [])
                        freqpoint_dict[bandstr].append(item)
                    else:
                        freq_dict.setdefault(bandstr, [])
                        freq_dict[bandstr].append(item)
            logger.debug(freqpoint_dict)
            logger.debug(freq_dict)
            return type, freqpoint_dict, freq_dict

        except Exception as e:
            raise RuntimeError('get_set_condition error:{}'.format(e))

    def get_id(self):
        '''
        获取基带板id
        :return:str
        '''
        try:
            sht = self.wb.sheets(BoardExcel.sheets_name[0])
            arm_ver = str(sht.range('B1').value)
            bb_ver = str(sht.range('B2').value)
            # a1 = sht.range('A1').value
            # a2 = sht.range('A2').value
            # arm_ver = a1.strip().split('：')[1].strip()
            # bb_ver = a2.strip().split('：')[1].strip()
            return arm_ver, bb_ver
        except Exception as e:
            raise ValueError('get_id error:{}'.format(e))
        finally:
            self.close_file()

    def get_band_dl_para(self):
        '''
        获取基带设定条件
        :return:dataframe
        '''
        try:
            rows = self.dl_rows['基带设定']
            sht = self.wb.sheets(BoardExcel.sheets_name[0])
            startrow = rows[0]
            endrow = rows[1]
            df = sht.range('A{}:G{}'.format(startrow, endrow)).options(pd.DataFrame, header=2).value
            df.columns = [['高', '高', '中', '中', '低', '低'], ['频点', '下行频率', '频点', '下行频率', '频点', '下行频率']]
            return df
        except Exception as e:
            raise ValueError('get_band_dl_para error:{}'.format(e))

    def get_ul_freq(self, cellid):
        '''

        :param cellid:0/1
        :return: {band:[高，中，低]}
        '''

        try:
            rows = self.ul_rows['基带设定']
            sht = self.wb.sheets(BoardExcel.sheets_name[4])
            startrow = rows[0] + 2
            endrow = rows[1]
            celllst = sht.range('A{}:G{}'.format(startrow, endrow)).value
            cellstr = 'cell{}'.format(cellid)
            bandstr = ''

            freq_dict = dict()  # 高中低频率
            for itemlst in celllst:
                for idx, item in enumerate(itemlst):
                    if item is None:
                        continue
                    if idx == 0:
                        temp = item.strip().split('_')
                        if len(temp) != 4:  # 满足8125_0_Cell1_B1字符串
                            break
                        thiscell = temp[2].lower()
                        bandstr = temp[3].upper()
                        if thiscell != cellstr:  # cell不是当前需要的主/从片
                            break
                        continue
                    if idx % 2 == 0:
                        freq_dict.setdefault(bandstr, [])
                        freq_dict[bandstr].append(item)
            return freq_dict

        except Exception as e:
            raise RuntimeError('get_ul_freq error:{}'.format(e))

    def get_txatt_norm(self):
        '''
        获取TXATT的指标规范
        :return:list [下限，标准值，上限]
        '''
        try:
            shtname = BoardExcel.sheets_name[0]
            sht = self.wb.sheets(shtname)
            rows = self.dl_rows[self.dl_keywords[1]]
            startrow = rows[0] + 3
            dt = sht.range('C{}:E{}'.format(startrow, startrow)).value
            return dt
        except Exception as e:
            raise NotImplementedError('get_txatt_norm error:{}'.format(e))

    def write_max_txatt(self, temp=1, **kwargs):
        '''
        更新最大档位输出值
        temp:0,1,2
        kwargs:{'CELL0_E':[[],[],[]],}
        :return:
        '''
        # logger.debug('write_max_txatt={}'.format(kwargs))
        # temp_dict = {0: '低温档位输出值', 1: '常温档位输出值', 2: '高温档位输出值'}
        # row_base = 'D'  # 在D列
        # try:
        #     sht = self.wb.sheets(temp_dict[int(temp)])
        #     for key, item in kwargs.items():
        #         row = self.get_max_row_in_temp(str(key))
        #         if row is None:
        #             continue
        #         lst = []
        #         for each in item:
        #             txatt, power, _, _ = each
        #             lst.extend([str(txatt * 100), str(power)])
        #         sht.range('{}{}'.format(row_base, row)).options(transpose=True).value = lst
        # except Exception as e:
        #     logger.error('write_max_txatt error:{}'.format(e))
        # else:
        #     self.wb.save()
        try:
            shtname = BoardExcel.sheets_name[0]
            sht = self.wb.sheets(shtname)
            rows = self.dl_rows['输出功率测试']
            temp_rows = [['F', 'G', 'H'], ['I', 'J', 'K'], ['L', 'M', 'N']]  # 低温，常温，高温所在列
            value_row_base, _, norm_row_base = temp_rows[int(temp)]  # 常温结果所在列,常温结论所在列
            row_dict = self.get_each_cellband_row(shtname, rows[0], rows[1])
            norm_list = self.get_norm(shtname, rows[0] + self.jump_row)

            for key, item in kwargs.items():
                row_idx = row_dict[key.upper()]
                row_range = value_row_base + str(row_idx)
                norm_range = norm_row_base + str(row_idx)
                lst = []
                norm_lst = []
                for each in item:
                    txatt, power, _, _ = each
                    ret = self.set_ccdf_colusition(power, norm_list)
                    norm_lst.append(ret)
                    lst.append([str(power), str(txatt * 100)])
                sht.range('{}'.format(row_range)).options(expand='table').value = lst
                sht.range('{}'.format(norm_range)).options(transpose=True).value = norm_lst

        except Exception as e:
            logger.error('write_max_txatt error:{}'.format(e))
        else:
            self.wb.save()

    def get_max_row_in_temp(self, cell_band, temp=1):
        '''
        获得档位测试表中最大功率输出的行号
        :param temp: 0低温、1常温、2高温
        cell_band:cell0_E/
        :return:
        '''

        if temp == 0:
            rows = self.ll_rows
        elif temp == 1:
            rows = self.nl_rows
        elif temp == 2:
            rows = self.hl_rows
        else:
            return None
        for key, item in rows.items():
            if cell_band.upper() in key:
                return item
        return None

    def write_power_range(self, temp=1, **kwargs):
        temp_dict = {0: '低温档位输出值', 1: '常温档位输出值', 2: '高温档位输出值'}
        col_base = 'F'  # 从第F列开始
        try:
            sht = self.wb.sheets(temp_dict[int(temp)])
            for key, item in kwargs.items():
                row_idx = self.get_max_row_in_temp(key) + 1
                if row_idx is None:
                    continue
                for freq_lsts in item:
                    row_flag = False
                    col_idx = col_base
                    for power in freq_lsts:
                        if row_flag:
                            range_str = 'A{}{}'.format(col_idx, row_idx)  # 列名从A-Z,再从AA-AZ
                        else:
                            range_str = '{}{}'.format(col_idx, row_idx)

                        sht.range('{}'.format(range_str)).value = power
                        if col_idx == 'Z':
                            col_idx = 'B'
                            row_flag = True
                        else:
                            col_idx = chr(ord(col_idx) + 2)
                    row_idx = row_idx + 2
            self.wb.save()
        except Exception as e:
            logger.error('write_power_range error:{}'.format(e))

    def get_each_cellband_row(self, shtname, start, end):
        '''
        获得每个子表的cell_band的所在行
        :return:{'CELL0_E':68}
        '''
        sht = self.wb.sheets(shtname)
        rng = sht.range('A{}:A{}'.format(start, end))
        lst = rng.value
        cell_dict = {}  # {}
        for idx, cell in enumerate(lst):
            if cell is None:
                continue
            cell = cell.upper()
            newcell = cell[cell.rfind('CELL'):]  # 原本每行标题是8125_0_CELL0_E,现在截取了CELL0_E
            cell_dict.setdefault(newcell, idx + start)
        return cell_dict

    def write_ACPR(self, temp=1, **kwargs):
        '''
        更新ACPR
        :param kwargs:{'cell0_E':[(txatt,power,adj_lower,adj_upper),(),()]}
        :return:
        '''
        # logger.debug('write_ACPR={}'.format(kwargs))
        try:
            shtname = BoardExcel.sheets_name[0]
            sht = self.wb.sheets(shtname)
            rows = self.dl_rows['ACPR测试']
            temp_rows = [['F', 'G'], ['H', 'I'], ['J', 'K']]  # 低温，常温，高温所在列
            value_row_base, norm_row_base = temp_rows[int(temp)]  # 常温结果所在列,常温结论所在列

            row_dict = self.get_each_cellband_row(shtname, rows[0], rows[1])

            norm_list = self.get_norm(shtname, rows[0] + self.jump_row)

            for key, item in kwargs.items():
                row_idx = row_dict[key.upper()]
                row_range = value_row_base + str(row_idx)
                norm_range = norm_row_base + str(row_idx)
                lst = []
                norm_lst = []
                for each in item:
                    _, _, adj_lower, adj_upper = each
                    ret = self.set_ACPR_colusition([adj_lower, adj_upper], norm_list)
                    norm_lst.append(ret)
                    lst.append('{}/{}'.format(adj_lower, adj_upper))
                sht.range('{}'.format(row_range)).options(transpose=True).value = lst
                sht.range('{}'.format(norm_range)).options(transpose=True).value = norm_lst

        except Exception as e:
            logger.error('write ACPR error:{}'.format(e))
        else:
            self.wb.save()

    def set_ACPR_colusition(self, lst, nlst):
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

    def get_norm(self, shtname, startrow):
        '''
        读取ACPR的指标规范
        :return:[下限，标准值，上限]
        '''
        try:
            sht = self.wb.sheets(shtname)
            dt = sht.range('C{}:E{}'.format(startrow, startrow)).value
            return dt
        except Exception as e:
            logger.exception('get_norm error:{}'.format(e))
            return None

    def write_ccdf(self, temp=1, **kwargs):
        '''
        {'B41':[(ppm,crest factor),(ppm,crest factor),(ppm,crest factor)]}
        :return:
        '''
        logger.debug('write_ccdf={}'.format(kwargs))
        try:
            shtname = BoardExcel.sheets_name[0]
            sht = self.wb.sheets(shtname)
            ppm_rows = self.dl_rows['频偏测试']
            cf_rows = self.dl_rows['峰均比测试']
            temp_rows = [['F', 'G'], ['H', 'I'], ['J', 'K']]  # 低温，常温，高温所在列
            value_row_base, norm_row_base = temp_rows[int(temp)]  # 常温结果所在列,常温结论所在列

            ppm_row_dict = self.get_each_cellband_row(shtname, ppm_rows[0], ppm_rows[1])
            cf_row_dict = self.get_each_cellband_row(shtname, cf_rows[0], cf_rows[1])
            ppm_norm = self.get_norm(shtname, ppm_rows[0] + self.jump_row)  # 指标
            cf_norm = self.get_norm(shtname, cf_rows[0] + self.jump_row)  # 指标

            for key, item in kwargs.items():
                ppm_row_range = value_row_base + str(ppm_row_dict[str(key).upper()])
                cf_row_range = value_row_base + str(cf_row_dict[str(key).upper()])
                ppm_pass_range = norm_row_base + str(ppm_row_dict[str(key).upper()])
                cf_pass_range = norm_row_base + str(cf_row_dict[str(key).upper()])
                lst1 = []
                lst2 = []
                ppm_lst = []
                cf_lst = []
                for each in item:
                    if each is None:
                        lst1.append('')
                        lst2.append('')
                        ppm_lst.append('')
                        cf_lst.append('')
                        continue
                    ppm, cf = each
                    ppm_lst.append(self.set_ccdf_colusition(ppm, ppm_norm))
                    cf_lst.append(self.set_ccdf_colusition(cf, cf_norm))
                    lst1.append('{}'.format(ppm))
                    lst2.append('{}'.format(cf))

                sht.range('{}'.format(ppm_row_range)).options(transpose=True).value = lst1
                sht.range('{}'.format(cf_row_range)).options(transpose=True).value = lst2
                sht.range('{}'.format(ppm_pass_range)).options(transpose=True).value = ppm_lst  # 写结论
                sht.range('{}'.format(cf_pass_range)).options(transpose=True).value = cf_lst  # 写结论

        except Exception as e:
            logger.error('write ccdf error:{}'.format(e))
        else:
            self.wb.save()

    def set_ccdf_colusition(self, ppm, norm_list):
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

    def write_EVM(self, temp=1, **kwargs):
        '''

        :return:
        '''
        logger.debug('write_EVM_dict={}'.format(kwargs))
        try:
            shtname = BoardExcel.sheets_name[0]
            sht = self.wb.sheets(shtname)
            evm_rows = self.dl_rows['EVM测试']
            temp_rows = [['F', 'G'], ['H', 'I'], ['J', 'K']]  # 低温，常温，高温所在列
            value_row_base, norm_row_base = temp_rows[int(temp)]  # 常温结果所在列,常温结论所在列
            row_dict = self.get_each_cellband_row(shtname, evm_rows[0], evm_rows[1])

            norm_list = self.get_norm(shtname, evm_rows[0] + self.jump_row)
            for key, item in kwargs.items():
                evm_range = value_row_base + str(row_dict[str(key).upper()])
                evm_pass_range = norm_row_base + str(row_dict[str(key).upper()])
                pass_lst = []
                for evm_value in item:
                    pass_lst.append(self.set_ccdf_colusition(evm_value, norm_list))

                sht.range('{}'.format(evm_range)).options(transpose=True).value = item
                sht.range('{}'.format(evm_pass_range)).options(transpose=True).value = pass_lst
        except Exception as e:
            logger.error('write EVM error:{}'.format(e))
        else:
            self.wb.save()

    def write_powerspectrum(self, temp=1, **kwargs):
        '''

        :return:
        '''
        logger.debug('write_powerspectrum={}'.format(kwargs))
        try:
            shtname = BoardExcel.sheets_name[0]
            sht = self.wb.sheets(shtname)
            rows = self.dl_rows['占用带宽测试']
            temp_rows = [['F', 'G'], ['H', 'I'], ['J', 'K']]  # 低温，常温，高温所在列
            value_row_base, norm_row_base = temp_rows[int(temp)]  # 常温结果所在列,常温结论所在列
            row_dict = self.get_each_cellband_row(shtname, rows[0], rows[1])
            norm_list = self.get_norm(shtname, rows[0] + self.jump_row)
            for key, item in kwargs.items():
                ps_range = value_row_base + str(row_dict[str(key).upper()])
                ps_pass_range = norm_row_base + str(row_dict[str(key).upper()])
                pass_lst = []
                for ps_value in item:
                    pass_lst.append(self.set_ccdf_colusition(ps_value, norm_list))

                sht.range('{}'.format(ps_range)).options(transpose=True).value = item
                sht.range('{}'.format(ps_pass_range)).options(transpose=True).value = pass_lst
        except Exception as e:
            logger.error('write_powerspectrum error:{}'.format(e))
        else:
            self.wb.save()

    def write_txatt_conclusion(self, temp=1):
        '''
        temp:0:低温，1：常温，2：高温
        更新输出功率，带内波动，Tx可调精度的 结论
        :return:
        '''
        try:
            power_row = self.dl_rows['输出功率测试']  # 输出功率和结论列
            # ripple_row = self.dl_rows['带内波动测试']  # 带内波动的记录值和结论
            # gear_row = self.dl_rows['可调精度测试']  # ['H60:H74', 'I60:I74']
            temp_rows = [['F', 'H', 'F', 'G', 'F', 'G'], ['I', 'K', 'H', 'I', 'H', 'I'], ['L', 'N', 'J', 'K', 'J', 'K']]
            power_row_base, power_con_base, ripple_row_base, ripple_con_base, gear_row_base, gear_con_base = temp_rows[
                int(temp)]
            shtname = BoardExcel.sheets_name[0]
            sht = self.wb.sheets(shtname)
            power_list = sht.range(
                '{}{}:{}{}'.format(power_row_base, power_row[0] + 3, power_row_base, power_row[1])).value
            power_norm_dict = self.get_norm(shtname, power_row[0] + self.jump_row)

            power_con_list = self.set_power_conclusion(power_list, power_norm_dict)  # 输出功率结论
            sht.range('{}{}:{}{}'.format(power_con_base, power_row[0] + 3, power_con_base, power_row[1])).options(
                transpose=True).value = power_con_list

            # ripple_list = sht.range(
            #     '{}{}:{}{}'.format(ripple_row_base, ripple_row[0] + 3, ripple_row_base, ripple_row[1])).value  # 带内波动
            # ripple_norm_list = self.get_norm(shtname, ripple_row[0] + self.jump_row)
            #
            # ripple_con_list = self.set_power_conclusion(ripple_list, ripple_norm_list)
            # sht.range('{}{}:{}{}'.format(ripple_con_base, ripple_row[0] + 3, ripple_con_base, ripple_row[1])).options(
            #     transpose=True).value = ripple_con_list  # 带内波动结论
            #
            # gear_list = sht.range(
            #     '{}{}:{}{}'.format(gear_row_base, gear_row[0] + 3, gear_row_base, gear_row[1])).value  # 可调精度
            # gear_norm_list = self.get_norm(shtname, gear_row[0] + self.jump_row)
            #
            # gear_con_list = self.set_power_conclusion(gear_list, gear_norm_list)
            # sht.range('{}{}:{}{}'.format(gear_con_base, gear_row[0] + 3, gear_con_base, gear_row[1])).options(
            #     transpose=True).value = gear_con_list

        except Exception as e:
            logger.error('write_txatt_conclusion error:{}'.format(e))
        else:
            self.wb.save()

    def set_power_conclusion(self, power_list, norm_dict):
        try:
            indicator1 = None
            indicator2 = None
            con_list = []
            for key, item in norm_dict.items():
                value = float(re.findall(r'-?\d+\.?\d*e?-?\d*?', str(item))[0]) if item is not None else None
                if value is None:
                    continue
                if '上限' in key:
                    indicator1 = '<=' + str(value)
                elif '下限' in key:
                    indicator2 = '>=' + str(value)

            for power in power_list:
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
            logger.error('set_power_conclusion error:{}'.format(e))
            return None

    def write_DANL(self, temp=1, **kwargs):
        '''
        底噪
        :param kwargs:
        :return:
        '''
        logger.debug('write_DANL_dict={}'.format(kwargs))
        try:
            shtname = BoardExcel.sheets_name[0]
            sht = self.wb.sheets(shtname)
            danl_rows = self.dl_rows['底噪测试']
            temp_rows = [['F', 'G'], ['H', 'I'], ['J', 'K']]  # 低温，常温，高温所在列
            value_row_base, norm_row_base = temp_rows[int(temp)]  # 常温结果所在列,常温结论所在列
            row_dict = self.get_each_cellband_row(shtname, danl_rows[0], danl_rows[1])
            norm_list = self.get_norm(shtname, danl_rows[0] + self.jump_row)
            for key, item in kwargs.items():
                danl_range = value_row_base + str(row_dict[str(key).upper()])
                danl_pass_range = norm_row_base + str(row_dict[str(key).upper()])
                pass_lst = []
                for danl_value in item:
                    pass_lst.append(self.set_ccdf_colusition(danl_value, norm_list))

                sht.range('{}'.format(danl_range)).options(transpose=True).value = item
                sht.range('{}'.format(danl_pass_range)).options(transpose=True).value = pass_lst
        except Exception as e:
            logger.error('write EVM error:{}'.format(e))
        else:
            self.wb.save()

    def write_current(self, temp=1, **kwargs):
        '''
        工作电流
        :param kwargs:
        :return:
        '''
        logger.debug('write_current_dict={}'.format(kwargs))
        try:
            shtname = BoardExcel.sheets_name[0]
            sht = self.wb.sheets(shtname)
            cur_rows = self.dl_rows['工作电流测试']
            temp_rows = [['F', 'G'], ['H', 'I'], ['J', 'K']]  # 低温，常温，高温所在列
            value_row_base, norm_row_base = temp_rows[int(temp)]  # 常温结果所在列,常温结论所在列
            row_dict = self.get_each_cellband_row(shtname, cur_rows[0], cur_rows[1])
            norm_list = self.get_norm(shtname, cur_rows[0] + self.jump_row)
            for key, item in kwargs.items():
                cur_range = value_row_base + str(row_dict[str(key).upper()])
                cur_pass_range = norm_row_base + str(row_dict[str(key).upper()])
                pass_lst = []
                for cur_value in item:
                    pass_lst.append(self.set_ccdf_colusition(cur_value, norm_list))

                sht.range('{}'.format(cur_range)).options(transpose=True).value = item
                sht.range('{}'.format(cur_pass_range)).options(transpose=True).value = pass_lst
        except Exception as e:
            logger.error('write_current error:{}'.format(e))
        else:
            self.wb.save()

    def close_file(self):
        try:
            if hasattr(self, 'wb'):
                self.wb.close()
                del self.wb
            if hasattr(self, 'app'):
                self.app.quit()
                del self.app
            # logger.debug('close excel..')
        except Exception as e:
            logger.error('{}'.format(e))


if __name__ == '__main__':
    xel = BoardExcel()
    xel.open_excel('EB1.xlsx')
    # df = xel.get_band_para()
    xel.get_dl_rows()

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
    dt = {'cell0_e': [(0, -1), (1, -2), (2, -3)]}
    xel.write_ccdf(**dt)

    # print(xel.get_ACPR_norm())
    # 6.
    # xel.write_EVM(**{'cell0_E':[11, 1.09, 1.13]})
    # 7.
    # xel.write_powerspectrum(**{'cell0_E': [11, 4.6, 4.5]})
    # xel.close_file()
    # a = xel.get_normaltemp_level_rows()

    # a=xel.get_txatt_norm()
    # 1.
    # a=xel.get_max_row_in_temp('cell1_b1')
    # print(a)
    # 2.
    # dt = {'cell0_E': [[7, 0.2, -1, -1], [8, 0.3, -2, -2], [7, 0.2, -3, -3]]}
    # xel.write_max_txatt(**dt)
    # xel.write_txatt_conclusion()
    # 4.
    # xel.write_max_txatt(**{'cell0_E': [1.4, 1.09, 1.13,1]})

    xel.close_file()
