# Generated by Django 4.1.1 on 2022-11-12 22:27

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0006_local_logo'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='sueldo_semanal',
            name='semana',
        ),
    ]