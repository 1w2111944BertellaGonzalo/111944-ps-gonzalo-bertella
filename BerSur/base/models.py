import datetime
from django.db import models
from django.db.models import Q
from django.contrib.auth.models import AbstractUser
import math
from BerSur.settings import DIAS_LABORABLES


class Rol(models.Model):
    descripcion = models.TextField(max_length=300)

    def __str__(self):
        return f'{self.descripcion}'


class Tipo_Especialidad(models.Model):
    descripcion = models.TextField(max_length=300)

    def __str__(self):
        return f'{self.descripcion}'


class Tipo_Ropa(models.Model):
    descripcion = models.TextField(max_length=300)
    talle = models.CharField(max_length=300)

    def __str__(self):
        return f'{self.descripcion}'


class Tipo_Pago(models.Model):
    descripcion = models.TextField(max_length=300)

    def __str__(self):
        return f'{self.descripcion}'


class User(AbstractUser):
    nombre = models.CharField(max_length=200, null=True)
    apellido = models.CharField(max_length=200, null=True)
    mail = models.EmailField(null=True, unique=True)
    direccion = models.TextField(max_length=200, null=True)
    telefono = models.CharField(max_length=20, null=True)
    fecha_nacimiento = models.DateTimeField(null=True, auto_now=False)
    dni = models.IntegerField(null=True)
    rol = models.ForeignKey(Rol, on_delete=models.CASCADE, null=True)
    es_activo = models.BooleanField(null=True)
    USERNAME_FIELD = 'mail'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return f'{self.nombre}'


class Empleado(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    ropa = models.ForeignKey(Tipo_Ropa, on_delete=models.CASCADE)
    especialidad = models.ForeignKey(
        Tipo_Especialidad, on_delete=models.CASCADE)
    sueldo_por_hora = models.FloatField(max_length=300)

    def __str__(self):
        return f'{self.usuario}'

    def obtener_horarios_de_trabajo_semana_actual(self, local=None):
        hoy = datetime.date.today()
        semana_actual = hoy.isocalendar().week
        if local:
            horarios_de_trabajo = self.horariodetrabajo_set.filter(
            empleado=self, horario_ingreso__week=semana_actual, horario_ingreso__year=hoy.year, local=local)
        else:
            horarios_de_trabajo = self.horariodetrabajo_set.filter(
            empleado=self, horario_ingreso__week=semana_actual, horario_ingreso__year=hoy.year)

        horarios = {'Lunes': ['null'],
                    'Martes': ['null'],
                    'Miércoles': ['null'],
                    'Jueves': ['null'],
                    'Viernes': ['null'],
                    'Sábado': ['null']}
        for horario in horarios_de_trabajo:
            horarios[DIAS_LABORABLES[horario.horario_ingreso.weekday()]] = [horario.horario_ingreso.strftime("%H:%M"), horario.horario_salida.strftime("%H:%M"), horario.horas_asignadas[:5]]
        return horarios

    def obtener_semanas_con_horarios_asignados(self):

        semanas_con_horarios_asignados = {}
        for horario in self.horariodetrabajo_set.all():
            semana = horario.horario_ingreso.isocalendar().week
            year = horario.horario_ingreso.isocalendar().year
            fecha = datetime.date.fromisocalendar(
                year, semana, 1).strftime("%d/%m/%Y")
            semanas_con_horarios_asignados[f'Semana del {fecha}'] = {
                'semana': semana, 'year': year}

        return semanas_con_horarios_asignados

    def obtener_lista_de_horas_asignadas(self, semana, year):
        lista_total_horas_asignadas = []

        horarios_asignados = self.horariodetrabajo_set.filter(
            empleado=self, horario_ingreso__week=semana, horario_ingreso__year=year)
        for horario in horarios_asignados:
            lista_total_horas_asignadas.append(
                horario.horas_asignadas_absolutas)
        return lista_total_horas_asignadas

    def obtener_lista_de_horas_trabajadas_y_dias(self, semana, year):
        """
        devuelve una lista de horas absolutas trabajadas del empleado y una lista de los dias
        """
        sueldo_semanal = self.sueldo_semanal_set.get(
            empleado=self, fecha__week=semana, fecha__year=year)

        lista_total_horas_trabajadas = []
        for jornada in sueldo_semanal.jornadas_laborales.all():
            lista_total_horas_trabajadas.append(
                jornada.horas_trabajadas_absolutas)

        return lista_total_horas_trabajadas


class Proveedor(models.Model):
    nombre = models.CharField(max_length=300)
    mail = models.EmailField(max_length=300)
    telefono = models.CharField(max_length=300)
    direccion = models.TextField(max_length=300)

    def __str__(self):
        return f'{self.nombre}'


class Local(models.Model):
    nombre = models.CharField(max_length=300)
    nombre_completo = models.CharField(max_length=300)
    mail = models.EmailField(max_length=300)
    direccion = models.TextField(max_length=200)
    telefono = models.CharField(max_length=20)
    proveedor = models.ManyToManyField(Proveedor, null=True)
    encargado = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    empleado = models.ManyToManyField(Empleado, null=True)
    ubicacion = models.CharField(max_length=300, null=True)
    logo = models.ImageField(null=True, default="bersurlogo.png")

    def __str__(self):
        return f'{self.nombre}'

    # TODO: muy probablemente, siempre que filtremos por semana, también tenemos que filtrar por año :)

    hoy = datetime.date.today()
    semana_actual = hoy.isocalendar().week
    year_actual = hoy.year

# recorrer todos los empleados y buscar si hay un sueldo semanal esta semana para ese empleado
    def get_sueldos_semanales_por_empleado(self):
        """
        devuelve todos los empleados del local y su sueldo esta semana,
        si no tiene un sueldo se le carga null para los dias de la semana
        """
        sueldos_por_empleado = {empleado.id: {
                                'nombre': empleado.usuario.nombre,
                                'apellido': empleado.usuario.apellido,
                                'dni': empleado.usuario.dni,
                                'horarios': {'Lunes': ['null'],
                                             'Martes': ['null'],
                                             'Miércoles': ['null'],
                                             'Jueves': ['null'],
                                             'Viernes': ['null'],
                                             'Sábado': ['null']},
                                'total_horas': 'null',
                                'total_a_cobrar': 'null'} for empleado in self.empleado.all()}
        # para obtener el sueldo acorde al dia
        # tenemos que recorrer todos los dias de la semana y verificar si el dia del horario de ingreso
        # es igual al dia que se está recorriendo
        # si es así se guarda la hora y el minuto de los horarios de ingreso y salida
        # si no es así se guarda null
        for empleado in self.empleado.all():
            try:
                sueldo_semanal = Sueldo_Semanal.objects.get(
                    empleado=empleado, fecha__week=self.semana_actual, local=self)
                for jornada in sueldo_semanal.jornadas_laborales.all():
                    # hay que obtener el numero de dia de la semana
                    dia = DIAS_LABORABLES[jornada.horario_ingreso.weekday()]
                    ingreso = jornada.horario_ingreso.strftime("%H:%M")
                    salida = jornada.horario_salida.strftime("%H:%M")
                    horas_trabajadas = jornada.horas_trabajadas
                    sueldos_por_empleado[empleado.id]['horarios'][dia] = [
                        ingreso, salida, horas_trabajadas[:5]]
                total_horas = sueldo_semanal.get_total_horas_trabajadas()
                sueldos_por_empleado[empleado.id]['total_horas'] = horas_decimales_a_horas_y_minutos(
                    total_horas)
                sueldos_por_empleado[empleado.id]['total_a_cobrar'] = sueldo_semanal.calcular_sueldo_total(
                    total_horas=total_horas)
            except Exception as exc:
                print(exc)

        return sueldos_por_empleado

    def obtener_proveedores_con_pagos_este_mes(self, mes, year):
        proveedores = [pago.proveedor for pago in self.pago_proveedor_set.filter(fecha__month=mes, fecha__year=year)]
        return proveedores

    def obtener_empleados_con_sueldo_este_mes(self, mes, year):
        empleados = [sueldo.empleado for sueldo in self.sueldo_semanal_set.filter(fecha__month=mes, fecha__year=year)]
        return empleados

    def obtener_empleados_con_sueldo_esta_semana(self, semana):
        empleados = [sueldo.empleado for sueldo in self.sueldo_semanal_set.filter(fecha__week=semana)]
        return empleados

    # TODO: a parte de la semana, hay que filtrar por año
    def obtener_sueldos_por_semana(self, semana):
        sueldos_de_semana={}
        for sueldo in self.sueldo_semanal_set.filter(fecha__week=semana):
            if sueldo.empleado.id not in sueldos_de_semana:
                sueldos_de_semana[sueldo.empleado.id] = {'nombre': sueldo.empleado.usuario.nombre, 'monto': sueldo.calcular_sueldo_total()}
            else:
                sueldos_de_semana[sueldo.empleado.id]['monto'] += sueldo.calcular_sueldo_total()          
        return sueldos_de_semana

    @property
    def obtener_semanas_del_local(self):
        semanas_del_local = []
        for caja_chica in self.caja_chica_set.all():
            semana_del_local = caja_chica.semana.isocalendar().week
            semanas_del_local.append(semana_del_local)
        return semanas_del_local

    semanas_del_local = obtener_semanas_del_local

    def obtener_semanas_del_local_por_mes(self, mes, year):
        semanas_del_local = []
        for caja_chica in self.caja_chica_set.filter(semana__year=year, semana__month=mes):
            semana_del_local = caja_chica.semana.isocalendar().week
            semanas_del_local.append(semana_del_local)
        return semanas_del_local

    @property
    def obtener_meses_del_local(self):
        meses_del_local = []
        for caja_chica in self.caja_chica_set.all():
            mes_del_local = caja_chica.semana.month
            meses_del_local.append(mes_del_local)
        meses_del_local = list(set(meses_del_local))
        return meses_del_local

    meses_del_local = obtener_meses_del_local

    @property
    def obtener_years_del_local(self):
        years_del_local = []
        for caja_chica in self.caja_chica_set.all():
            year_del_local = caja_chica.semana.year
            years_del_local.append(year_del_local)
        years_del_local = list(set(years_del_local))
        return years_del_local

    years_del_local = obtener_years_del_local

    def calcular_total_retiros_por_dia(self, dia):
        total = 0
        for retiro in self.retiros_set.filter(Q(fecha__date=dia), Q(cancelado=False)):
            total += retiro.monto
        return total

    @property
    def obtener_total_retiros_hoy(self):
        return self.calcular_total_retiros_por_dia(self.hoy)

    total_retiros_hoy = obtener_total_retiros_hoy

    def obtener_pagos_por_semana(self, semana):
        pagos_a_proveedores={}
        for pago in self.pago_proveedor_set.filter(fecha__week=semana):
            if pago.proveedor.id not in pagos_a_proveedores:
                pagos_a_proveedores[pago.proveedor.id] = {'nombre': pago.proveedor.nombre, 'monto': pago.monto}
            else:
                pagos_a_proveedores[pago.proveedor.id]['monto'] += pago.monto          
        return pagos_a_proveedores

    def calcular_total_pagos_por_mes(self, mes, year):
        total = 0
        for pago in self.pago_proveedor_set.filter(fecha__month=mes, fecha__year=year):
            total += pago.monto
        return total

    def calcular_total_pagos_por_semana(self, semana, year):
        total = 0
        for pago in self.pago_proveedor_set.filter(fecha__week=semana, fecha__year=year):
            total += pago.monto
        return total

    @property
    def obtener_total_pagos_semana_actual(self):
        return self.calcular_total_pagos_por_semana(self.semana_actual, self.year_actual)

    total_pagos_semana_actual = obtener_total_pagos_semana_actual

    def calcular_total_sueldos_por_semana(self, semana):
        total = 0
        for pago in self.sueldo_semanal_set.filter(fecha__week=semana):
            total += pago.calcular_sueldo_total()
        return total

    @property
    def obtener_total_sueldos_semana_actual(self):
        return self.calcular_total_sueldos_por_semana(self.semana_actual)

    total_sueldos_semana_actual = obtener_total_sueldos_semana_actual

    @property
    def obtener_monto_actual(self):
        monto_a_descontar = 0
        for pago in self.pago_proveedor_set.filter(fecha__week=self.semana_actual):
            monto_a_descontar += pago.monto

        caja_chica_semana = self.caja_chica_set.get(
            semana__week=self.semana_actual)
        monto_actual = caja_chica_semana.monto_semanal - monto_a_descontar
        return monto_actual

    monto_actual = obtener_monto_actual


class Pago_Proveedor(models.Model):
    proveedor = models.ForeignKey(Proveedor, on_delete=models.CASCADE)
    monto = models.FloatField(max_length=300)
    fecha = models.DateTimeField(auto_now=True)
    local = models.ForeignKey(Local, on_delete=models.CASCADE)
    tipo_pago = models.ForeignKey(Tipo_Pago, on_delete=models.CASCADE)
    descripcion = models.TextField(max_length=300)

    def __str__(self):
        return f'{self.proveedor}'


class Caja_Chica(models.Model):  # DUDA CON LA CAJA CHICA y LOCAL
    local = models.ForeignKey(Local, on_delete=models.CASCADE)
    monto_semanal = models.FloatField(max_length=300)
    semana = models.DateTimeField(max_length=300)

    def __str__(self):
        return f'{self.local}'


class HorarioDeTrabajo(models.Model):
    """
    Horario a trabajar predefinido de un empleado
    """
    empleado = models.ForeignKey(Empleado, on_delete=models.CASCADE)
    horario_ingreso = models.DateTimeField(auto_now=False)
    horario_salida = models.DateTimeField(auto_now=False)
    local = models.ForeignKey(Local, on_delete=models.CASCADE)

    def __str__(self):
        return f'{self.empleado}, {self.horario_ingreso}'

    @property
    def horas_asignadas(self):
        horas_asignadas = calcular_diferencia_horarios(
            self.horario_salida, self.horario_ingreso)
        return horas_asignadas

    @property
    def horas_asignadas_absolutas(self):
        horas = timedelta_str_to_float(self.horas_asignadas)
        return horas


class JornadaLaboral(models.Model):
    """
    Horario real trabajado en una jornada
    """
    horario_ingreso = models.DateTimeField(auto_now=False)
    horario_salida = models.DateTimeField(auto_now=False)

    def __str__(self):
        return f'{self.horario_ingreso}'

    @property
    def horas_trabajadas(self):
        horas_trabajadas = calcular_diferencia_horarios(
            self.horario_salida, self.horario_ingreso)
        return horas_trabajadas

    @property
    def horas_trabajadas_absolutas(self):
        horas = timedelta_str_to_float(self.horas_trabajadas)
        return horas


class Sueldo_Semanal(models.Model):
    empleado = models.ForeignKey(Empleado, on_delete=models.CASCADE)
    jornadas_laborales = models.ManyToManyField(JornadaLaboral)
    bono = models.FloatField(max_length=300, default=0)
    fecha = models. DateTimeField(auto_now=True)
    tipo_pago = models.ForeignKey(
        Tipo_Pago, on_delete=models.CASCADE, null=True)
    local = models.ForeignKey(Local, on_delete=models.CASCADE)

    def __str__(self):
        return f'{self.empleado}'

    def get_total_horas_trabajadas(self):
        total_horas = 0
        for jornada in self.jornadas_laborales.all():
            horas_jornada = timedelta_str_to_float(jornada.horas_trabajadas)
            total_horas += horas_jornada

        # total_horas = "{:0>8}".format(sumar_horarios(lista_horarios))
        return total_horas

    def calcular_sueldo_total(self, total_horas=None):
        if not total_horas:
            total_horas = self.get_total_horas_trabajadas()
            # total_horas = timedelta_str_to_float(total_horas_trabajadas)

        sueldo_total = total_horas * self.empleado.sueldo_por_hora
        if self.bono:
            sueldo_total += self.bono
        return sueldo_total

    def actualizar_jornadas_laborales(self, lista_jornadas):
        for jornada in self.jornadas_laborales.all():
            if jornada not in lista_jornadas:
                self.jornadas_laborales.remove(jornada)
            else:
                lista_jornadas.remove(jornada)

        for jornada in lista_jornadas:
            self.jornadas_laborales.add(jornada)


class Retiros(models.Model):
    local = models.ForeignKey(Local, on_delete=models.CASCADE)
    fecha = models.DateTimeField(auto_now=True)
    monto = models.FloatField(max_length=300)
    cajero = models.ForeignKey(Empleado, on_delete=models.CASCADE)
    cancelado = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.local} ${self.monto}'


class Producto(models.Model):
    codigo = models.CharField(max_length=300)
    descripcion = models.TextField(max_length=300)
    precio_costo = models.FloatField(max_length=300)
    precio_venta = models.FloatField(max_length=300)
    precio_mayoreo = models.FloatField(max_length=300)
    proveedor = models.ForeignKey(Proveedor, on_delete=models.CASCADE)
    local = models.ForeignKey(Local, on_delete=models.CASCADE, null=True)

    def __str__(self):
        return f'{self.codigo}'


# common
def calcular_diferencia_horarios(end, start):
    diff = end - start

    # days, seconds = diff.days, diff.seconds
    # hours = days * 24 + seconds // 3600
    # minutes = (seconds % 3600) // 60
    diferencia = "{:0>8}".format(str(datetime.timedelta(seconds=diff.seconds)))

    return diferencia


def sumar_horarios(lista_horarios):
    total_horas = datetime.timedelta()
    for i in lista_horarios:
        (h, m, s) = i.split(':')
        d = datetime.timedelta(hours=int(h), minutes=int(m), seconds=int(s))
        total_horas += d
    return str(total_horas)


def timedelta_str_to_float(time_to_parse):
    """
    dado horas, min y seg en formato '08:30:00' devuelve un float con el total de horas, ej: 8.50
    """
    horas = int(time_to_parse[:2])
    minutos = int(time_to_parse[3:5])
    minutos = int((minutos/60)*100)
    total_horas = horas + float(f'0.{minutos}')

    return total_horas


def horas_decimales_a_horas_y_minutos(horas):
    decimales_horas = math.modf(horas)
    minutos = decimales_horas[0] * 0.6
    horas_pareseadas = decimales_horas[1] + minutos
    return horas_pareseadas
