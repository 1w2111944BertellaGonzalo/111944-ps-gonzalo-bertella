# Generated by Django 4.1.1 on 2022-11-16 23:27

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0013_alter_sueldo_semanal_bono'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='retiros',
            name='descripcion',
        ),
    ]
