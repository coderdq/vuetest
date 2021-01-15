# Generated by Django 2.2 on 2020-10-15 01:02

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='POWER',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('fsvip', models.CharField(max_length=20)),
                ('fsvoffset', models.CharField(max_length=3)),
                ('zvlip', models.CharField(max_length=20)),
                ('zvloffset', models.CharField(max_length=3)),
                ('smbvip', models.CharField(max_length=20)),
                ('powerdir', models.CharField(max_length=255)),
                ('band', models.CharField(max_length=3)),
                ('zvlused', models.CharField(max_length=2)),
                ('dl', models.CharField(max_length=20)),
                ('lowtemp', models.SmallIntegerField(null=True)),
                ('normtemp', models.SmallIntegerField(null=True)),
                ('hightemp', models.SmallIntegerField(null=True)),
                ('port', models.SmallIntegerField(null=True)),
                ('period', models.SmallIntegerField(null=True)),
            ],
        ),
    ]