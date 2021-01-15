from django.db import models

# Create your models here.
class TCompModel(models.Model):
    boardip = models.CharField(max_length=20) #板子IP
    fsvip = models.CharField(max_length=10) #频谱仪IP
    dir = models.CharField(max_length=255)    #模板路径
    port = models.SmallIntegerField(null=True)  # 高低温的串口号

