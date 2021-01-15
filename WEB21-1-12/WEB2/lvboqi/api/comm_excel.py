# coding:utf-8
import logging
import xlwings as xw
import pandas as pd
import re
import copy
import pythoncom

logger = logging.getLogger('ghost')


class ZVLExcel(object):
    # 在excel中的位置
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

            logger.error('no excel file:{}'.format(e))
            return False

    def get_sheet_name(self, band):

        shtname = 'FDD'
        if str(band) in ['39', '40', '41']:
            shtname = 'TDD'
        elif str(band).upper().startswith('GSM'):
            shtname='GSM'

        return shtname

    def get_id(self, band):
        '''
        获取器件型号与序列号
        :return:
        '''
        try:
            shtname = self.get_sheet_name(band)
            sht = self.wb.sheets(shtname)
            rng = sht.range('B2:B3').value  # ['',]
            return rng
        except Exception as e:
            logger.error('{}'.format(e))
            return None
        finally:
            self.close_file()

    def close_file(self):
        try:
            if self.wb is not None:
                self.wb.close()
                del self.wb
            if self.app is not None:
                self.app.quit()
                del self.app
        except Exception as e:
            logger.error('{}'.format(e))

    def get_used_a(self, shtname):
        '''
        返回当前sheet的已用A列数据列表
        :param band:
        :return: []
        '''
        try:
            sht = self.wb.sheets(shtname)
            rowcount = sht.api.UsedRange.Rows.count  # 行数
            rng = sht.range('A1:A{}'.format(rowcount))
            lst = rng.value
            return lst
        except Exception as e:
            logger.error('{}'.format(e))
            return None

    def get_band_position(self, shtname):
        '''
        找到所有band区域的起始行
        :param shtname:
        :return: []
        '''
        try:
            lst = self.get_used_a(shtname)

            # 找到Band的所在区域
            bandrows = [idx + 1 for idx, item in enumerate(lst) if isinstance(item, str) and
                        item.lower() == 'band']

            return bandrows
        except Exception as e:
            logger.error('{}'.format(e))
            return None

    def get_bandx_edge(self, band):
        '''
        获得band的上行下行edge以及左右边带上下限
        :return:[上行频率，下行频率,左带外上限，右带外下限]
        '''
        try:
            shtname = self.get_sheet_name(band)
            lst = self.get_used_a(shtname)

            if lst is None:
                return None

            bandx = 'band{}'.format(band)
            aa = bandx.strip().replace(' ', '').lower()
            sht = self.wb.sheets(shtname)
            row = [idx + 1 for idx, item in enumerate(lst) if isinstance(item, str) and
                   item.strip().replace(' ', '').lower() == aa]  # 第几行

            if not row:
                return None
            rng = sht.range('A{}'.format(row[0])).options(expand='table').value
            print(rng)
            _, low_edge, up_edge = rng[1]  # 单元格Low_edge,UP_edge下的值
            _,leftlow_edge,_=rng[2]  #左带外上限
            _,_,rightup_edge=rng[3]  #右带外下限
            return (low_edge, up_edge,leftlow_edge,rightup_edge)
        except Exception as e:
            logger.error('get_bandx_edge error {}'.format(e))
            return None

    def get_testitems_position(self, band):
        '''
        读取对应band的测试项区域
        :param band:
        :return:[起始行，结束行]
        '''
        try:
            shtname = self.get_sheet_name(band)
            bandrows = self.get_band_position(shtname)

            if bandrows is None:
                return None

            sht = self.wb.sheets(shtname)
            rowcount = sht.api.UsedRange.Rows.count  # 行数
            edges = self.get_bandx_edge(band)

            if edges is None:
                return None
            length = len(bandrows)
            span = []
            targidx = 0
            targrow = 0
            for idx, row in enumerate(bandrows):
                rng = sht.range('C{}:D{}'.format(row + 1, row + 1)).value  # 比较LOW edge 和UP edge
                if rng[0] == edges[0] and rng[1] == edges[1]:
                    targidx = idx
                    targrow = row
                    break
            if targidx == (length - 1):
                span = [targrow, rowcount]
            else:
                span = [targrow, bandrows[targidx + 1]]
            endrow = 0
            rngband = sht.range('C{}:C{}'.format(span[0] + 1, span[1])).value
            # 按C列为空来分割band区域
            for idx, row in enumerate(rngband):
                if row is None:
                    endrow = idx
                    break
            endrow += span[0]
            if endrow == span[0]:
                endrow = rowcount
            return span[0], endrow
        except Exception as e:
            logger.error('{}'.format(e))
            return None

    def read_testitems(self, band):
        '''
        返回对应band的测试区域的DataFrame
        :param band:
        :return: DataFrame
        '''
        try:
            rowtup = self.get_testitems_position(band)
            if rowtup is None:
                logger.debug('found no band')
                return None
            startrow, endrow = rowtup
            shtname = self.get_sheet_name(band)
            sht = self.wb.sheets(shtname)
            colcount = sht.api.UsedRange.Columns.count  # 列数
            if endrow > startrow:
                rng = sht.range((startrow, 1), (endrow, colcount)).options(pd.DataFrame, index=False).value
                return rng
            return None
        except Exception as e:
            logger.error('{}'.format(e))
            return None

    def get_inband_items(self, fulldf):
        '''
        获得带内测试的内容dataframe,要求默认表格band内前5行是带内测试
        fulldf:单个band的所有区域
        :return:带内的Low Edge,UP Edge,指标要求
        '''
        try:
            retdf = fulldf.iloc[:5, [2, 3, 4]]
            return retdf
        except Exception as e:
            logger.error('get_inband_items error {}'.format(e))
            return None

    def get_inband_indicator(self, fulldf):
        '''
        获得带内测试的指标，默认前5行为带内测试
        :param fulldf:
        :return:指标的列表[(‘<=’,指标)]
        '''
        try:
            retdf = fulldf.iloc[:5, 4]
            ids = []
            for item in retdf.values:
                value = float(re.findall(r'-?\d+\.?\d*e?-?\d*?', item)[0])
                operator = re.split(r'-?\d+\.?\d*e?-?\d*?', item)[0]
                ids.append((operator, value))
            return ids
        except Exception as e:
            logger.error('get_inband_indicator error {}'.format(e))
            return None

    def get_outband_items(self, fulldf):
        '''
        获得带外测试的Low Edge,UP Edge,指标运算符，指标要求四列
        :param fulldf:
        :return:
        '''
        try:
            dfs = copy.deepcopy(fulldf)
            indsdf = dfs.iloc[5:, 4]
            idsvalue = []
            idsoperator = []
            for item in indsdf.values:
                value = float(re.findall(r'-?\d+\.?\d*e?-?\d*?', item)[0])
                operator = re.split(r'-?\d+\.?\d*e?-?\d*?', item)[0]
                idsvalue.append(value)
                idsoperator.append(operator)
            dfs.iloc[5:, 4] = idsoperator
            dfs.iloc[5:, 5] = idsvalue
            retdf = dfs.iloc[5:, [2, 3, 4, 5]]
            return retdf
        except Exception as e:
            logger.error('get_outband_items error {}'.format(e))
            return None

    def write_results(self, band, resultlist,temp=0):
        '''
              将结果写到对应band的实测值和测试结果列,暂时只写温度25度下的
              :param resultlist:
              :return:
              '''
        temp_dict = {0: ('H', 'I'), 1: ('F', 'G'), 2: ('J', 'K')}
        try:
            rowlist = self.get_testitems_position(band)
            translist = []
            for ret in resultlist:
                if ret is None:
                    translist.append(('', ''))
                else:
                    r, check = ret
                    if check:
                        translist.append((r, 'Pass'))
                    else:
                        translist.append((r, 'Fail'))
            # translist = [(ret, 'Pass') if check else (ret, 'Fail') for ret, check in resultlist]
            if rowlist:
                startrow, endrow = rowlist
                retrow = '{}{}:{}{}'.format(temp_dict[temp][0], startrow + 1, temp_dict[temp][1], endrow)
                shtname = self.get_sheet_name(band)
                sht = self.wb.sheets(shtname)
                sht.range('{}'.format(retrow)).value = translist
            # 保存
            self.wb.save()

        except Exception as e:
            logger.error('write_results error {}'.format(e))


    def save_band_png(self, band, inbandpngpath, outpngs):
        '''
        将带内测试图片插入到excel表格
        :param band:
        :param pngpath:
        :return:
        '''
        try:
            rowlist = self.get_testitems_position(band)
            if rowlist:
                startrow, endrow = rowlist
                retrow1 = 'L{}'.format(startrow + 1)
                retrow2 = 'M{}'.format(startrow + 6)

                shtname = self.get_sheet_name(band)
                sht = self.wb.sheets(shtname)
                sht.range('{}'.format(retrow1)).add_hyperlink(r'{}'.format(inbandpngpath),
                                                              text_to_display='inband{}'.format(band))
                # for i in range(len(outbandpngs)):
                #     retrow='M{}'.format(startrow+6+i)
                #     sht.range('{}'.format(retrow)).add_hyperlink(r'{}'.format(outbandpngs[i]),
                #                                               text_to_display='outband{}_{}'.format(band,i+1))
                for i in range(len(outpngs)):
                    retrow = 'L{}'.format(startrow + 6 + i)
                    sht.range('{}'.format(retrow)).add_hyperlink(r'{}'.format(outpngs[i]),
                                                                 text_to_display='out{}'.format(i + 1))
                # 保存
            self.wb.save()
        except Exception as e:
            logger.error('save_png error {}'.format(e))


if __name__ == '__main__':
    import os

    zex = ZVLExcel()
    zex.open_excel('F://测试模板//新双工器测试模板.xlsx')
    # df1=zex.read_testitems('GSMUL')
    # print(df1)
    # df2=zex.get_outband_items(df1)
    # print(df2)
    # l=df2.iloc[-1,1]
    # print(l)
    print(zex.get_testitems_position('GSMDL'))
    # print(zex.get_id('39'))
    zex.close_file()
    # device_type, device_id = zex.get_id('39')
    # dirname = os.path.dirname('C:\\tmp\\ZVL\\test.xlsx')
    # device_type_path = os.path.join(dirname, str(device_type))
    # device_id_path = os.path.join(device_type_path, str(device_id))
    # if not os.path.exists(device_type_path):
    #     os.makedirs(device_type_path)
    # if not os.path.exists(device_id_path):
    #     os.makedirs(device_id_path)
