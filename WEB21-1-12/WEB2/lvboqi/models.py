from django.db import models


class LVBOQI(models.Model):
    ip = models.CharField(max_length=20)
    max = models.CharField(max_length=10)
    band = models.CharField(max_length=10)
    dir = models.CharField(max_length=255)
    lowtemp = models.SmallIntegerField(null=True)  # 高低温的低温
    normtemp = models.SmallIntegerField(null=True)  # 高低温的常温
    hightemp = models.SmallIntegerField(null=True)  # 高低温的高温
    port = models.SmallIntegerField(null=True)  # 高低温的串口号
    period = models.SmallIntegerField(null=True)  # 高低温的时间间隔
