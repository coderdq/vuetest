from django.db import models


# Create your models here.

class CalibModel(models.Model):
    fsvip = models.CharField(max_length=20)  # 频谱仪IP
    ip = models.CharField(max_length=20)  # T2K ip
    template_path = models.CharField(max_length=255)  # 测试模板地址
    lowtemp = models.SmallIntegerField(null=True)  # 高低温的低温
    normtemp = models.SmallIntegerField(null=True)  # 高低温的常温
    hightemp = models.SmallIntegerField(null=True)  # 高低温的高温
    port = models.SmallIntegerField(null=True)  # 高低温的串口号
    period = models.SmallIntegerField(null=True)  # 高低温的时间间隔


class UpgradeModel(models.Model):
    ip = models.CharField(max_length=20)  # T2K ip
    armfile_path = models.CharField(max_length=255, null=True, blank=True)  # ARM包地址
    bbfile_path = models.CharField(max_length=255, null=True, blank=True)  # BB文件地址
