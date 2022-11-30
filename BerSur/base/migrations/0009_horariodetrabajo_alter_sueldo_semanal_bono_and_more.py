# Generated by Django 4.1.1 on 2022-11-13 00:18

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0008_empleado_sueldo_por_hora'),
    ]

    operations = [
        migrations.CreateModel(
            name='HorarioDeTrabajo',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('fecha', models.DateTimeField()),
                ('horario_ingreso', models.DateTimeField()),
                ('horario_salida', models.DateTimeField()),
                ('empleado', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='base.empleado')),
            ],
        ),
        migrations.AlterField(
            model_name='sueldo_semanal',
            name='bono',
            field=models.FloatField(max_length=300, null=True),
        ),
        migrations.DeleteModel(
            name='Horario',
        ),
    ]