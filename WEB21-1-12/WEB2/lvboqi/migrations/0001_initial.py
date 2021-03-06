# Generated by Django 2.2 on 2020-10-13 09:35

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='LVBOQI',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ip', models.CharField(max_length=20)),
                ('max', models.CharField(max_length=10)),
                ('band', models.CharField(max_length=10)),
                ('dir', models.CharField(max_length=255)),
                ('lowtemp', models.SmallIntegerField(null=True)),
                ('normtemp', models.SmallIntegerField(null=True)),
                ('hightemp', models.SmallIntegerField(null=True)),
                ('port', models.SmallIntegerField(null=True)),
                ('period', models.SmallIntegerField(null=True)),
            ],
        ),
    ]
