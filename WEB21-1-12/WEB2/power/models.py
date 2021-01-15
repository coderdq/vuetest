from django.db import models

class POWER(models.Model):
    fsvip = models.CharField(max_length=20)
    fsvoffset = models.CharField(max_length=3)
    zvlip = models.CharField(max_length=20)
    zvloffset = models.CharField(max_length=3)
    smbvip = models.CharField(max_length=20)
    powerdir = models.CharField(max_length=255)
    band = models.CharField(max_length=3)
    zvlused = models.CharField(max_length=2)
    dl = models.CharField(max_length=20)
    lowtemp = models.SmallIntegerField(null=True)  # 高低温的低温
    normtemp = models.SmallIntegerField(null=True)  # 高低温的常温
    hightemp = models.SmallIntegerField(null=True)  # 高低温的高温
    port = models.SmallIntegerField(null=True)  # 高低温的串口号
    period = models.SmallIntegerField(null=True)  # 高低温的时间间隔

