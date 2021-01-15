from django.db import models


class T2KULModel(models.Model):
    smbv_ip = models.CharField(max_length=20)  # 信号源IP
    smbv_offset = models.CharField(max_length=3)  # 信号源衰减器大小dB
    board_ip = models.CharField(max_length=20)  # T2K ip
    cellid = models.CharField(max_length=2)  # T2K 小区
    # masterip=models.CharField(max_length=20)  #8125主片IP
    # slaveip=models.CharField(max_length=20)  #8125从片IP
    lowtemp = models.SmallIntegerField(null=True)  # 高低温的低温
    normtemp = models.SmallIntegerField(null=True)  # 高低温的常温
    hightemp = models.SmallIntegerField(null=True)  # 高低温的高温
    port = models.SmallIntegerField(null=True)  # 高低温的串口号
    period = models.SmallIntegerField(null=True)  # 高低温的时间间隔
    exe_path = models.CharField(max_length=255)  # 灵敏度软件地址
    template_path = models.CharField(max_length=255)  # 测试模板地址


class T2KDLModel(models.Model):
    fsvip = models.CharField(max_length=20)
    fsvoffset = models.CharField(max_length=3)
    t2kdir = models.CharField(max_length=255)
    board_ip = models.CharField(max_length=20)
    cellid = models.CharField(max_length=2)
    lowtemp = models.SmallIntegerField(null=True)
    normtemp = models.SmallIntegerField(null=True)
    hightemp = models.SmallIntegerField(null=True)
    port = models.SmallIntegerField(null=True)
    period = models.SmallIntegerField(null=True)
