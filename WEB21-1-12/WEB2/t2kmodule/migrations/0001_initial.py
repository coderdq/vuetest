# Generated by Django 2.2 on 2020-09-30 06:26

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='T2KDLModel',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('fsvip', models.CharField(max_length=20)),
                ('fsvoffset', models.CharField(max_length=3)),
                ('t2kdir', models.CharField(max_length=255)),
                ('board_ip', models.CharField(max_length=20)),
                ('cellid', models.CharField(max_length=2)),
                ('lowtemp', models.SmallIntegerField(null=True)),
                ('normtemp', models.SmallIntegerField(null=True)),
                ('hightemp', models.SmallIntegerField(null=True)),
                ('port', models.SmallIntegerField(null=True)),
                ('period', models.SmallIntegerField(null=True)),
            ],
        ),
        migrations.CreateModel(
            name='T2KULModel',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('smbv_ip', models.CharField(max_length=20)),
                ('smbv_offset', models.CharField(max_length=3)),
                ('board_ip', models.CharField(max_length=20)),
                ('cellid', models.CharField(max_length=2)),
                ('lowtemp', models.SmallIntegerField(null=True)),
                ('normtemp', models.SmallIntegerField(null=True)),
                ('hightemp', models.SmallIntegerField(null=True)),
                ('port', models.SmallIntegerField(null=True)),
                ('period', models.SmallIntegerField(null=True)),
                ('exe_path', models.CharField(max_length=255)),
                ('template_path', models.CharField(max_length=255)),
            ],
        ),
    ]
