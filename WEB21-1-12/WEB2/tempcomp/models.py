"""
T2K整机温度补偿表
"""
from django.db import models


class TCompModel(models.Model):
    boardip = models.CharField(max_length=20)  # 设备IP地址
    fsvip = models.CharField(max_length=10)  # 频谱仪IP地址
    dir = models.CharField(max_length=255)  # 测试模板目录
    port = models.SmallIntegerField(null=True)  # 高低温的串口号

