import re
import copy
import logging

logger = logging.getLogger('ghost')


class FlatProcess(object):
    '''
    频补文件处理
    '''

    def __init__(self):
        self.flat_comp = None  # 内存的频补表

    def init_flat_comp(self, freqpoint_dict, test_temp, centertemp):
        '''
        初始化频补表，21开始
        :param freqpoint_dict:
        :param centertemp:
        :return:
        '''
        band_keys = freqpoint_dict.keys()
        flat_comp = dict()
        flat_comp['TemperList'] = [float(item) for item in test_temp]
        for key in band_keys:
            band_dict = dict()
            bandstr = re.sub('\D', '', key.split('_')[-1])
            band_dict['Band'] = int(bandstr)
            for point in freqpoint_dict[key]:
                d_info = dict(zip(['Freq', 'Calib', 'Temp'], [int(point), 21, centertemp]))
                band_dict.setdefault('BandInfo', []).append(d_info)
            flat_comp.setdefault('FreqCaliTable', []).append(band_dict)
        self.flat_comp = copy.deepcopy(flat_comp)

    def init_comp_from_file(self, comp):
        '''
        从设备文件中取出内容
        :param comp: {}
        :return:
        '''
        self.flat_comp = comp

    def read_and_set(self, freqpoint_dict, centertemp):
        '''
        初始读取内存，比较待测数据，更新到内存
        :param freqpoint_dict:
        :param centertemp:
        :return:
        '''
        freq_keys = freqpoint_dict.keys()
        flag = False
        for cellband in freq_keys:
            freq_points = freqpoint_dict[str(cellband)]
            bandstr = re.sub('\D', '', cellband.split('_')[-1])
            band = int(bandstr)
            existbandinfo = []  # [{'Freq':,'Calib':,'Temp':}]
            bandlist_in_flat = self.flat_comp['FreqCaliTable']
            for d_band in bandlist_in_flat:
                if d_band['Band'] != band:
                    continue
                existbandinfo = d_band['BandInfo']
            existpoints = [item['Freq'] for item in existbandinfo] if existbandinfo else []
            for point in freq_points:
                if int(point) in existpoints:
                    continue
                d_info = dict(zip(['Freq', 'Calib', 'Temp'], [int(point), 21, centertemp]))  # {}
                existbandinfo.append(d_info)
                flag = True
            # 排序频点
            existbandinfo.sort(key=lambda x: x['Freq'])  # 按频点从小到大排序
            self.update_flat_comp_json(band, existbandinfo)
        return flag

    def update_flat_comp_json(self, band, bandinfo):
        '''
        更新内存表的某band信息
        :param band: int
        :param bandinfo: []
        :return:
        '''
        flat_json = self.flat_comp
        freqcalitable = flat_json['FreqCaliTable']  # []
        newbandinfo = bandinfo
        for idx, bi in enumerate(bandinfo):
            if isinstance(bi, list):
                newbi = dict(zip(['Freq', 'Calib', 'Temp'], bi))
                newbandinfo[idx] = newbi

        for item in freqcalitable:
            itemband = item['Band']
            if int(itemband) == int(band):
                item['BandInfo'] = newbandinfo
                break
        else:
            band_dict = {'Band': band, 'BandInfo': newbandinfo}
            flat_json.setdefault('FreqCaliTable', []).append(band_dict)

    def read_bandinfo(self, band):
        '''

        :param band:int
        :return:[[freq,calib,temp],[freq,cali,temp],[freq,cali,temp]]
        '''
        flat_json = self.flat_comp
        freqcalitable = flat_json['FreqCaliTable']  # []
        bandinfo = []
        for item in freqcalitable:
            itemband = item['Band']
            if itemband == band:
                bandinfo = [list(some.values()) for some in item['BandInfo']]
                break
        return bandinfo

    def set_bandinfo(self, band, freq, cali):
        '''
        某band的某频点的补偿值,在原有基础上叠加
        :param band:
        :param freq:
        :param cali:
        :return:
        '''
        flat_json = self.flat_comp
        freqcalitable = flat_json['FreqCaliTable']  # []
        for item in freqcalitable:
            itemband = item['Band']
            if itemband == int(band):
                bandinfo = item['BandInfo']
                for freqitem in bandinfo:
                    if freqitem['Freq'] == float(freq):
                        freqitem['Calib'] = round(freqitem['Calib'] + cali, 2)
                        break
                break

    def get_json(self):
        return copy.deepcopy(self.flat_comp)


class GainProcess(object):
    def __init__(self):
        self.gain_comp = None  # 内存的温补表

    def init_gain_comp(self, freqpoint_dict, test_temp):
        '''
        初始化温补表
        :return:
        '''
        band_keys = freqpoint_dict.keys()
        gain_comp = dict()
        gain_comp['TemperList'] = [float(item) for item in test_temp]
        for key in band_keys:
            band_dict = dict()
            bandstr = re.sub('\D', '', key.split('_')[-1])
            band_dict['Band'] = int(bandstr)
            for point in freqpoint_dict[key]:
                callst = [0.0] * len(test_temp)
                d_info = dict(zip(['Freq', 'Poly', 'List'], [int(point), [0] * 4, callst]))
                band_dict.setdefault('BandInfo', []).append(d_info)
            gain_comp.setdefault('TempCompTable', []).append(band_dict)
        self.gain_comp = copy.deepcopy(gain_comp)

    def init_comp_from_file(self, comp):
        '''
        :param comp: {}
        :return:
        '''
        # # 将80度改为75度
        # templist = comp['TemperList']
        # if 80 in templist:
        #     templist[-1] = 75
        self.gain_comp = comp
        # self.gain_comp['TemperList'] = templist

    def get_json(self):
        return copy.deepcopy(self.gain_comp)

    def read_bandinfo(self, tempidx, band, freq_point):
        '''
        读取某temp某band某频点的温补值
        :param band: int
        :return:[,,]
        '''
        gain_comp = self.gain_comp
        tempcomptable = gain_comp['TempCompTable']
        cali = None
        for item in tempcomptable:
            itemband = item['Band']
            if itemband == int(band):
                iteminfo = item['BandInfo']
                for freqitem in iteminfo:
                    if freqitem['Freq'] == int(freq_point):
                        cali = freqitem['List'][tempidx]
                        break
                break
        return cali

    def read_and_set(self, freqpoint_dict):
        logger.debug('read_and_set')
        freq_keys = freqpoint_dict.keys()
        flag = False
        templist = self.gain_comp['TemperList']
        for cellband in freq_keys:
            freq_points = freqpoint_dict[str(cellband)]
            bandstr = re.sub('\D', '', cellband.split('_')[-1])
            band = int(bandstr)
            existbandinfo = []  # [{'Freq':,'Poly':,'List':}]
            bandlist_in_gain = self.gain_comp['TempCompTable']
            for d_band in bandlist_in_gain:
                if d_band['Band'] != band:
                    continue
                existbandinfo = d_band['BandInfo']
            existpoints = [item['Freq'] for item in existbandinfo] if existbandinfo else []
            for point in freq_points:
                if int(point) in existpoints:
                    continue
                d_info = dict(zip(['Freq', 'Poly', 'List'], [int(point), [0] * 4, [0.0] * len(templist)]))  # {}
                existbandinfo.append(d_info)
                flag = True
            # 排序频点
            existbandinfo.sort(key=lambda x: x['Freq'])  # 按频点从小到大排序
            self.update_gain_comp_json(band, existbandinfo)
        return flag

    def update_gain_comp_json(self, band, bandinfo):
        '''

        :param band:
        :param bandinfo: [{Freq,Poly,List},{}]或者[[],[],[]]
        :return:
        '''
        gain_json = self.gain_comp
        freqcalitable = gain_json['TempCompTable']  # []
        newbandinfo = bandinfo
        for idx, bi in enumerate(bandinfo):
            if isinstance(bi, list):
                newbi = dict(zip(['Freq', 'Poly', 'List'], bi))
                newbandinfo[idx] = newbi

        for item in freqcalitable:
            itemband = item['Band']
            if int(itemband) == int(band):
                item['BandInfo'] = newbandinfo
                break
        else:
            band_dict = {'Band': band, 'BandInfo': newbandinfo}
            gain_json.setdefault('TempCompTable', []).append(band_dict)

    def read_tempidx(self, temp):
        try:
            templist = self.gain_comp['TemperList']
            return templist.index(float(temp))
        except Exception:
            return None

    def set_bandinfo(self, tempidx, nexttempidx, band, freq, cali):
        '''
        设置某温度下的某band的某频点的补偿值,在原有基础上叠加,相邻温度复制当前的补偿值
        :param band:
        :param freq:
        :param cali:
        :return:
        '''
        if tempidx is None:
            return
        gain_json = self.gain_comp
        freqcalitable = gain_json['TempCompTable']  # []
        for item in freqcalitable:
            itemband = item['Band']
            if itemband == int(band):
                bandinfo = item['BandInfo']
                for freqitem in bandinfo:
                    if freqitem['Freq'] == float(freq):
                        logger.debug('freq={},oldvalue={},cali={}'.format(freq,freqitem['List'][tempidx],cali))
                        freqitem['List'][tempidx] = round(freqitem['List'][tempidx] + cali, 2)
                        logger.debug('new value={}'.format(freqitem['List'][tempidx]))
                        if nexttempidx is not None:
                            freqitem['List'][nexttempidx] = freqitem['List'][tempidx]  # 复制
                        break
                break

    def copy_bandinfo(self, tempidx, band, freq, cali):
        '''
        下一温度复制上一温度的补偿值
        :param tempidx:
        :param band:
        :param freq:
        :return:
        '''
        gain_json = self.gain_comp
        freqcalitable = gain_json['TempCompTable']  # []
        for item in freqcalitable:
            itemband = item['Band']
            if itemband == int(band):
                bandinfo = item['BandInfo']
                for freqitem in bandinfo:
                    if freqitem['Freq'] == float(freq):
                        freqitem['List'][tempidx] = cali
                        break
                break
        logger.debug(gain_json)

    def copy_30and40(self):
        '''
        将-20度的补偿复制给-30，-40的温度补偿
        :return:
        '''
        try:
            idx2 = self.read_tempidx(-20)
            if idx2 == -1:
                return
            idx3 = self.read_tempidx(-30)
            idx4 = self.read_tempidx(-40)
            if idx3 != -1 or idx4 != -1:
                gain_json = self.gain_comp
                freqcalitable = gain_json['TempCompTable']  # []
                for item in freqcalitable:
                    bandinfo = item['BandInfo']
                    for freqitem in bandinfo:
                        if idx3 != -1:
                            freqitem['List'][idx3] = freqitem['List'][idx2]
                        if idx4 != -1:
                            freqitem['List'][idx4] = freqitem['List'][idx2]
        except Exception as e:
            logger.error(e)

    def copy_70(self):
        '''
        将70度的补偿值复制给80度
        :return:
        '''
        try:
            idx2 = self.read_tempidx(70)
            if idx2 == -1:
                return
            idx3 = self.read_tempidx(80)
            if idx3 != -1:
                gain_json = self.gain_comp
                freqcalitable = gain_json['TempCompTable']  # []
                for item in freqcalitable:
                    bandinfo = item['BandInfo']
                    for freqitem in bandinfo:
                        if idx3 != -1:
                            freqitem['List'][idx3] = freqitem['List'][idx2]
        except Exception as e:
            logger.error(e)
