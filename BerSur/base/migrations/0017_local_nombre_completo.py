# Generated by Django 4.1.1 on 2022-11-22 00:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0016_horariodetrabajo_local'),
    ]

    operations = [
        migrations.AddField(
            model_name='local',
            name='nombre_completo',
            field=models.CharField(default='nombre', max_length=300),
            preserve_default=False,
        ),
    ]
