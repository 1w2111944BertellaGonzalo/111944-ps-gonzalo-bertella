import datetime
from io import StringIO
import json
from django.db.models import Q
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from base.utils import obtener_dias_de_semana, get_inicios_de_semana_unicos_locales_por_mes, agregar_eventos, genereate_csv_response, export_productos_data
from BerSur.settings import DIAS_LABORABLES, MESES, CALENDARS_URLS
from base.models import (User,
                         HorarioDeTrabajo,
                         Empleado,
                         Caja_Chica,
                         Local,
                         Pago_Proveedor,
                         Retiros,
                         Sueldo_Semanal,
                         Tipo_Especialidad,
                         Tipo_Pago,
                         Tipo_Ropa,
                         Producto,
                         Rol,
                         JornadaLaboral
                         )
from base.models import Proveedor
from .forms import CajaChicaForm, EmpleadoForm, EmpleadoUpdateForm, EspecialidadForm, LocalForm, PagosProveedorForm, ProductoForm, ProveedorForm, RetirosForm, RolForm, RopaForm, SueldoSemanalForm, UsuarioForm, HorarioDeTrabajoForm, UsuarioUpdateForm

# Create your views here.


def home(request):
    if not request.user.is_authenticated:
        redirect('login')
    context = {}

    try:
        usuario = User.objects.get(id=request.user.id)
    except:
        return redirect('login')

    if usuario.rol.descripcion == 'Presidente':
        return redirect('vistapresidente')

    if usuario.rol.descripcion == 'Gerente':
        return redirect('vistapresidente')

    if usuario.rol.descripcion == 'Encargado':
        local = Local.objects.get(encargado=usuario)
        return redirect('local', local.id)

    if usuario.rol.descripcion == 'Empleado':
        empleado = Empleado.objects.get(usuario=usuario)
        locales = empleado.local_set.all()
        context.update({'empleado': empleado, 'locales': locales})
        if empleado.especialidad.descripcion == 'CAJERO':
            hoy = datetime.date.today()
            retiros = Retiros.objects.filter(cajero=empleado, fecha__date=hoy)
            context.update({'page': 'cajero', 'retiros': retiros})

    return render(request, 'base/home.html', context)

# LOGGIN


def page_login(request):
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == "POST":
        email = request.POST.get('email')
        password = request.POST.get('password')

        try:
            usuario = User.objects.get(mail=email)
        except:
            messages.error(request, 'No existe un usuario con este mail')

        usuario = authenticate(request, mail=email, password=password)

        if usuario:
            login(request, usuario)
            if usuario.rol == 'Encargado':
                local = Local.objects.get(encargado=usuario)
                return redirect('local', local.id)
            return redirect('home')
        else:
            messages.error(request, 'Contraseña incorrecta')
    return render(request, 'base/login.html', context=None)


def page_logout(request):

    if request.user.is_authenticated:
        logout(request)
        return redirect('login')

    return redirect('home')


def page_register(request, rol_desc):
    rol = Rol.objects.get(descripcion=rol_desc)
    locales = Local.objects.all()

    form_usuario = UsuarioForm()
    if rol.descripcion == 'Empleado':
        form_empleado = EmpleadoForm()
        especialidades = Tipo_Especialidad.objects.all()
        ropas = Tipo_Ropa.objects.all()

    if request.method == "POST":
        mail_obtenido = request.POST.get('mail')
        username = request.POST.get("username")

        if User.objects.filter(Q(mail=mail_obtenido) | Q(username=username)).first():
            return HttpResponse('Un Usuario con este mail o nombre de usuario ya existe!')

        form_usuario = UsuarioForm(request.POST)

        if form_usuario.is_valid():
            usuario = form_usuario.save(commit=False)
            usuario.rol = rol
            usuario.save()

            if rol.descripcion == 'Encargado':
                # hacemos .get porque en este caso lista_locales devuelve 1 solo local
                nombre_local = request.POST.get("lista_locales")
                local = Local.objects.get(nombre=nombre_local)
                local.encargado = usuario
                local.save()

            if rol.descripcion == 'Empleado':
                ropa_id = request.POST.get("ropa")
                ropa = Tipo_Ropa.objects.get(pk=ropa_id)
                especialidad_id = request.POST.get('especialidad')
                especialidad = Tipo_Especialidad.objects.get(
                    pk=especialidad_id)
                sueldo_por_hora = request.POST.get('sueldo_por_hora')
                empleado = Empleado.objects.create(usuario=usuario,
                                                   ropa=ropa,
                                                   especialidad=especialidad,
                                                   sueldo_por_hora=sueldo_por_hora)
                empleado.save()

                # hacemos .getlist porque en este caso lista_locales devuelve n locales
                lista_locales = request.POST.getlist("lista_locales")
                locales_seleccionados = Local.objects.filter(
                    nombre__in=lista_locales)
                for local in locales_seleccionados:
                    local.empleado.add(empleado)

                if request.user.rol.descripcion == 'Encargado':
                    local = Local.objects.get(encargado=request.user)
                    local.empleado.add(empleado)
                    return redirect('empleados', local.id)
            return redirect('home')
        else:
            messages.error(request, f"Ocurrió un error al registrar")

    context = {'form_usuario': form_usuario,
               'page': 'register', 'locales': locales, 'rol': rol}

    if rol.descripcion == 'Empleado':
        context.update({'form_empleado': form_empleado, 'ropas': ropas,
                        'especialidades': especialidades})
        if request.user.rol.descripcion == 'Encargado':
            local = Local.objects.get(encargado=request.user)
            context.update({'local': local})

    return render(request, 'base/registrar.html', context)


@login_required(login_url='login')
def vistapresidente(request):
    if request.user.rol.descripcion != 'Presidente':
        return redirect('home')
    locales = Local.objects.all()
    context = {'locales': locales}

    return render(request, 'base/vistapresidente.html', context)


@login_required(login_url='login')
def reporte_pagos_proveedores(request, local_id):
    local = Local.objects.get(id=local_id)

    hoy = datetime.date.today()
    mes_actual = hoy.month
    year_actual = hoy.year

    if request.method == "POST":
        if request.POST.get("chartExport"):
            datos_chart = json.load(
                StringIO(request.POST.get("chartExport"))
            )
            labels = json.load(
                StringIO(request.POST.get("labelsExport"))
            )
            response = genereate_csv_response(
                labels,
                "Proveedor",
                datos_chart,
                f"Reporte Pagos Semanales",
            )
            return response

    local_years = local.years_del_local

    local_meses = []
    for mes in local.meses_del_local:
        local_meses.append(MESES[mes-1])

    semanas_del_local_del_mes = local.obtener_semanas_del_local_por_mes(
        mes_actual, year_actual)

    proveedores_con_pagos = local.obtener_proveedores_con_pagos_este_mes(
        mes_actual, year_actual)

    # por semana, muestra el total de pagos realizados a proveedores
    inicios_de_semana = []
    for semana in semanas_del_local_del_mes:
        fecha = datetime.date.fromisocalendar(
            2022, semana, 1).strftime("%d/%m/%Y")
        inicios_de_semana.append(f'Semana del {fecha}')

    pagos_por_semana = {proveedor.id: {
        'nombre_prov': proveedor.nombre,
        'montos': ['null']*len(inicios_de_semana)
    } for proveedor in proveedores_con_pagos}

    for idx, semana in enumerate(semanas_del_local_del_mes):
        pagos_de_la_semana = local.obtener_pagos_por_semana(semana)
        for proveedor_id, values in pagos_de_la_semana.items():
            pagos_por_semana[proveedor_id]['montos'][idx] = values['monto']

    context = {'local': local, 'pagos_por_semana': pagos_por_semana,
               'local_meses': local_meses, 'local_years': local_years, 'inicios_de_semana': inicios_de_semana}
    return render(request, 'base/reporte_pago_proveedores.html', context)


@login_required(login_url='login')
def actualizar_reporte_pagos_proveedores(request):
    if request.method == "GET" and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        local_id = request.GET.get('local_id')
        local = Local.objects.get(id=local_id)

        year = request.GET.get('year')
        mes = request.GET.get('mes')
        numero_mes = MESES.index(mes) + 1

        semanas_del_local_del_mes = local.obtener_semanas_del_local_por_mes(
            numero_mes, year)

        inicios_de_semana = []
        for semana in semanas_del_local_del_mes:
            fecha = datetime.date.fromisocalendar(
                2022, semana, 1).strftime("%d/%m/%Y")
            inicios_de_semana.append(f'Semana del {fecha}')

        pagos_por_semana = {pago.proveedor.id: {
            'nombre_prov': pago.proveedor.nombre,
            'montos': ['null']*len(inicios_de_semana)
        } for pago in local.pago_proveedor_set.all()}

        for idx, semana in enumerate(semanas_del_local_del_mes):
            pagos_de_la_semana = local.obtener_pagos_por_semana(semana)
            for proveedor_id, values in pagos_de_la_semana.items():
                pagos_por_semana[proveedor_id]['montos'][idx] = values['monto']

        return JsonResponse({'pagos_por_semana': pagos_por_semana, 'inicios_de_semana': inicios_de_semana})


@login_required(login_url='login')
def reporte_pagos_sueldos(request, local_id):
    local = Local.objects.get(id=local_id)

    hoy = datetime.date.today()
    mes_actual = hoy.month
    year_actual = hoy.year

    if request.method == "POST":
        if request.POST.get("chartExport"):
            datos_chart = json.load(
                StringIO(request.POST.get("chartExport"))
            )
            labels = json.load(
                StringIO(request.POST.get("labelsExport"))
            )
            response = genereate_csv_response(
                labels,
                "Proveedor",
                datos_chart,
                f"Reporte Pagos Semanales",
            )
            return response

    local_years = local.years_del_local
    local_meses = []
    for mes in local.meses_del_local:
        local_meses.append(MESES[mes-1])

    # por semana, muestra el total de pagos realizados a proveedores
    semanas_del_local_del_mes = local.obtener_semanas_del_local_por_mes(
        mes_actual, year_actual)

    empleados_con_sueldo = local.obtener_empleados_con_sueldo_este_mes(
        mes_actual, year_actual)

    inicios_de_semana = []
    for semana in semanas_del_local_del_mes:
        fecha = datetime.date.fromisocalendar(
            2022, semana, 1).strftime("%d/%m/%Y")
        inicios_de_semana.append(f'Semana del {fecha}')

    pagos_sueldos_por_semana = {empleado.id: {
        'nombre_emp': empleado.usuario.nombre,
        'montos': ['null']*len(semanas_del_local_del_mes)
    } for empleado in empleados_con_sueldo}

    for idx, semana in enumerate(semanas_del_local_del_mes):
        sueldos_de_semana = local.obtener_sueldos_por_semana(semana)
        for empleado_id, values in sueldos_de_semana.items():
            pagos_sueldos_por_semana[empleado_id]['montos'][idx] = values['monto']

    context = {'local': local, 'pagos_sueldos_por_semana': pagos_sueldos_por_semana,
               'local_meses': local_meses, 'local_years': local_years, 'inicios_de_semana': inicios_de_semana}
    return render(request, 'base/reporte_pago_sueldos.html', context)


@login_required(login_url='login')
def actualizar_reporte_pagos_sueldos(request):
    if request.method == "GET" and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        local_id = request.GET.get('local_id')
        local = Local.objects.get(id=local_id)

        year = request.GET.get('year')
        mes = request.GET.get('mes')
        numero_mes = MESES.index(mes) + 1

        semanas_del_local_del_mes = local.obtener_semanas_del_local_por_mes(
            numero_mes, year)

        empleados_con_sueldo = local.obtener_empleados_con_sueldo_este_mes(
            numero_mes, year)

        inicios_de_semana = []
        for semana in semanas_del_local_del_mes:
            fecha = datetime.date.fromisocalendar(
                2022, semana, 1).strftime("%d/%m/%Y")
            inicios_de_semana.append(f'Semana del {fecha}')

        pagos_sueldos_por_semana = {empleado.id: {
            'nombre_emp': empleado.usuario.nombre,
            'montos': ['null']*len(semanas_del_local_del_mes)
        } for empleado in empleados_con_sueldo}

        for idx, semana in enumerate(semanas_del_local_del_mes):
            sueldos_de_semana = local.obtener_sueldos_por_semana(semana)
            for empleado_id, values in sueldos_de_semana.items():
                pagos_sueldos_por_semana[empleado_id]['montos'][idx] = values['monto']

        return JsonResponse({'pagos_sueldos_por_semana': pagos_sueldos_por_semana, 'inicios_de_semana': inicios_de_semana})


@login_required(login_url='login')
def reporte_pagos_por_local(request):

    if request.user.rol.descripcion != 'Presidente':
        redirect('home')

    locales = Local.objects.all()

    hoy = datetime.date.today()
    mes_actual = hoy.month
    year_actual = hoy.year

    if request.method == "POST":
        if request.POST.get("chartExport"):
            datos_chart = json.load(
                StringIO(request.POST.get("chartExport"))
            )
            labels = json.load(
                StringIO(request.POST.get("labelsExport"))
            )
            response = genereate_csv_response(
                labels,
                "Proveedor",
                datos_chart,
                f"Reporte Pagos Semanales",
            )
            return response

    inicios_de_semana_unicos = get_inicios_de_semana_unicos_locales_por_mes(
        locales, mes_actual, year_actual)

    semanas_unicas_del_mes = []
    for local in locales:
        semanas_unicas_del_mes += local.obtener_semanas_del_local_por_mes(
            mes_actual, year_actual)

    semanas_unicas_del_mes = list(set(semanas_unicas_del_mes))

    pagos_por_local = {}
    local_meses = []
    local_years = []
    for local in locales:
        # obtener todos los meses y años activos de cada local
        local_years += local.years_del_local
        for mes in local.meses_del_local:
            meses = [MESES[mes-1]]
            local_meses += meses

        montos = ['null']*len(semanas_unicas_del_mes)

        for idx, semana in enumerate(semanas_unicas_del_mes):
            monto_total_semanal = local.calcular_total_pagos_por_semana(
                semana, year_actual)
            if monto_total_semanal != 0:
                montos[idx] = monto_total_semanal

        pagos_por_local[local.id] = {'nombre': local.nombre, 'montos': montos}

    local_meses = list(set(local_meses))
    local_years = list(set(local_years))

    context = {'local': local, 'pagos_por_local': pagos_por_local,
               'local_meses': local_meses, 'local_years': local_years, 'inicios_de_semana': inicios_de_semana_unicos}
    return render(request, 'base/reporte_locales_pagos.html', context)


@login_required(login_url='login')
def actualizar_reporte_pagos_por_local(request):
    if request.method == "GET" and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        locales = Local.objects.all()

        year = request.GET.get('year')
        mes = request.GET.get('mes')
        numero_mes = MESES.index(mes) + 1

        inicios_de_semana_unicos = get_inicios_de_semana_unicos_locales_por_mes(
            locales, numero_mes, year)

        semanas_unicas_del_mes = []
        for local in locales:
            semanas_unicas_del_mes += local.obtener_semanas_del_local_por_mes(
                numero_mes, year)

        semanas_unicas_del_mes = list(set(semanas_unicas_del_mes))

        pagos_por_local = {}

        for local in locales:

            montos = ['null']*len(semanas_unicas_del_mes)

            for idx, semana in enumerate(semanas_unicas_del_mes):
                monto_total_semanal = local.calcular_total_pagos_por_semana(
                    semana, year)
                if monto_total_semanal != 0:
                    montos[idx] = monto_total_semanal

            pagos_por_local[local.id] = {
                'nombre': local.nombre, 'montos': montos}

        return JsonResponse({'pagos_por_local': pagos_por_local, 'inicios_de_semana': inicios_de_semana_unicos})


@login_required(login_url='login')
def reporte_horarios_empleado(request, empleado_id):
    empleado = Empleado.objects.get(id=empleado_id)

    hoy = datetime.date.today()
    semana = hoy.isocalendar().week

    # obtenemos todos los dias de la semana para los labels
    dias = obtener_dias_de_semana(semana, hoy.year)
    # obtenemos todas las fechas de los primeros dias de las semanas en las cuales el empleado tiene un horario asignado
    semanas_con_horarios_asignados = empleado.obtener_semanas_con_horarios_asignados()
    if not semanas_con_horarios_asignados:
        messages.error(
            request, 'Este empleado no tiene horarios de trabajo asignados')
        return redirect(request.META['HTTP_REFERER'])
    # obtener lista horas asignadas
    lista_total_horas_asignadas = empleado.obtener_lista_de_horas_asignadas(
        semana, hoy.year)
    # obtener lista horas trabajadas
    try:
        lista_total_horas_trabajadas = empleado.obtener_lista_de_horas_trabajadas_y_dias(
            semana, hoy.year)
    except:
        lista_total_horas_trabajadas = []

    suma_horas_asignadas = sum(lista_total_horas_asignadas)
    suma_horas_trabajadas = sum(lista_total_horas_trabajadas)

    context = {
        'empleado': empleado,
        'lista_total_horas_asignadas': lista_total_horas_asignadas,
        'lista_total_horas_trabajadas': lista_total_horas_trabajadas,
        'suma_horas_asignadas': suma_horas_asignadas,
        'suma_horas_trabajadas': suma_horas_trabajadas,
        'semanas_con_horarios_asignados': semanas_con_horarios_asignados,
        'dias': dias
    }
    return render(request, 'base/reporte_horarios_empleado.html', context)


@login_required(login_url='login')
def actualizar_reporte_horarios(request):
    if request.method == "GET" and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        empleado = Empleado.objects.get(id=request.GET.get('empleado_id'))

        semana_year = request.GET.get('semana_year')
        semana = int(semana_year[:2])
        year = int(semana_year[3:8])
        # obtenemos todos los dias de la semana para los labels
        dias = obtener_dias_de_semana(semana, year)
        # obtenemos todas las fechas de los primeros dias de las semanas en las cuales el empleado tiene un horario asignado
        semanas_con_horarios_asignados = empleado.obtener_semanas_con_horarios_asignados()
        # obtener lista horas asignadas
        lista_total_horas_asignadas = empleado.obtener_lista_de_horas_asignadas(
            semana, year)
        # obtener lista horas trabajadas
        try:
            lista_total_horas_trabajadas = empleado.obtener_lista_de_horas_trabajadas_y_dias(
                semana, year)
        except:
            lista_total_horas_trabajadas = []
        suma_horas_asignadas = sum(lista_total_horas_asignadas)
        suma_horas_trabajadas = sum(lista_total_horas_trabajadas)

        empleado = {
            'nombre': empleado.usuario.nombre,
            'apellido': empleado.usuario.apellido
        }

        return JsonResponse({
            'empleado': empleado,
            'lista_total_horas_asignadas': lista_total_horas_asignadas,
            'lista_total_horas_trabajadas': lista_total_horas_trabajadas,
            'suma_horas_asignadas': suma_horas_asignadas,
            'suma_horas_trabajadas': suma_horas_trabajadas,
            'semanas_con_horarios_asignados': semanas_con_horarios_asignados,
            'dias': dias
        })


# PROVEEDOR

@login_required(login_url='login')
def page_proveedores(request, local_id):
    local = Local.objects.get(id=local_id)
    proveedores = local.proveedor.all()
    context = {'proveedores': proveedores, 'local': local}
    return render(request, 'base/proveedores.html', context)


@login_required(login_url='login')
def agregar_proveedor(request, local_id):

    form = ProveedorForm()
    if request.method == "POST":
        local = Local.objects.get(id=local_id)

        nombre_obtenido = request.POST.get('nombre')  # pepe
        nombre_obtenido = nombre_obtenido.upper()
        if Proveedor.objects.filter(nombre=nombre_obtenido).first():

            return HttpResponse('Un proveedor con este nombre ya existe!')

        mail = request.POST.get("mail")
        telefono = request.POST.get('telefono')
        direccion = request.POST.get('direccion')
        proveedor = Proveedor.objects.create(nombre=nombre_obtenido,
                                             mail=mail,
                                             telefono=telefono,
                                             direccion=direccion)

        proveedor.save()
        local.proveedor.add(proveedor)
        local.save()
        # si es encargado redirecciona a su local
        # si no a una tabla general

        return redirect('proveedores', local_id)

    context = {'form': form}
    return render(request, 'base/agregar_proveedor.html', context)


@login_required(login_url='login')
def eliminar_proveedor(request, proveedor_id, local_id):
    proveedor = Proveedor.objects.get(id=proveedor_id)
    proveedor.delete()
    return redirect('proveedores', local_id)


@login_required(login_url='login')
def editar_proveedor(request, local_id, proveedor_id):
    proveedor = Proveedor.objects.get(id=proveedor_id)
    form = ProveedorForm(instance=proveedor)
    if request.method == "POST":
        nombre = request.POST.get("nombre")
        mail = request.POST.get("mail")
        direccion = request.POST.get('direccion')
        telefono = request.POST.get('telefono')

        proveedor.nombre = nombre
        proveedor.mail = mail
        proveedor.direccion = direccion
        proveedor.telefono = telefono

        proveedor.save()

        return redirect('proveedores', local_id)

    context = {"form": form}
    return render(request, 'base/editar_proveedor.html', context)


# PRODUCTO

@login_required(login_url='login')
def page_producto(request):
    productos = Producto.objects.all()

    if request.method == "POST":
        response = export_productos_data(productos)
        return response

    context = {'productos': productos}
    return render(request, 'base/productos.html', context)


@login_required(login_url='login')
def agregar_producto(request):
    form = ProductoForm()
    proveedores = Proveedor.objects.all()
    locales = Local.objects.all()
    if request.method == "POST":

        codigo_obtenido = request.POST.get('codigo')
        if Producto.objects.filter(codigo=codigo_obtenido).first():
            return HttpResponse('Un Producto con este codigo ya existe!')

        descripcion = request.POST.get("descripcion")
        precio_costo = request.POST.get('precio_costo')
        precio_venta = request.POST.get('precio_venta')
        precio_mayoreo = request.POST.get('precio_mayoreo')
        proveedor_id = request.POST.get('proveedor')
        proveedor = Proveedor.objects.get(pk=proveedor_id)

        local_id = request.POST.get("local")
        local = Local.objects.get(id=local_id)

        Producto.objects.create(codigo=codigo_obtenido,
                                descripcion=descripcion,
                                precio_costo=precio_costo,
                                precio_venta=precio_venta,
                                precio_mayoreo=precio_mayoreo,
                                proveedor=proveedor,
                                local=local
                                )

        return redirect('productos')

    context = {'form': form, 'proveedores': proveedores, 'locales': locales}
    return render(request, 'base/agregar_producto.html', context)


@login_required(login_url='login')
def eliminar_producto(request, producto_id):
    producto = Producto.objects.get(id=producto_id)
    producto.delete()
    return redirect('productos')


@login_required(login_url='login')
def editar_producto(request, producto_id):
    producto = Producto.objects.get(id=producto_id)
    form_producto = ProductoForm(instance=producto)
    if request.method == "POST":

        codigo = request.POST.get('codigo')
        descripcion = request.POST.get('descripcion')
        precio_costo = request.POST.get('precio_costo')
        precio_venta = request.POST.get('precio_venta')
        precio_mayoreo = request.POST.get('precio_mayoreo')
        proveedor_id = request.POST.get('proveedor')
        proveedor = Proveedor.objects.get(id=proveedor_id)

        producto.codigo = codigo
        producto.descripcion = descripcion
        producto.precio_costo = precio_costo
        producto.precio_venta = precio_venta
        producto.precio_mayoreo = precio_mayoreo
        producto.proveedor = proveedor

        producto.save()

        return redirect('productos')

    context = {"form_producto": form_producto}
    return render(request, 'base/editar_producto.html', context)


# ROLES

@login_required(login_url='login')
def page_rol(request):
    roles = Rol.objects.all()
    context = {'roles': roles}
    return render(request, 'base/roles.html', context)


@login_required(login_url='login')
def agregar_rol(request):
    form = RolForm()
    if request.method == "POST":

        descripcion_obtenida = request.POST.get('descripcion')
        descripcion_obtenida = descripcion_obtenida.upper()
        if Rol.objects.filter(descripcion=descripcion_obtenida).first():
            return HttpResponse('Un Rol con esta descripcion ya existe!')

        Rol.objects.create(descripcion=descripcion_obtenida)
        return redirect('roles')

    context = {'form': form}
    return render(request, 'base/agregar_rol.html', context)


@login_required(login_url='login')
def eliminar_rol(request, rol_id):
    rol = Rol.objects.get(id=rol_id)
    rol.delete()
    return redirect('roles')


# USUARIO

@login_required(login_url='login')
def page_usuarios(request, rol):
    if rol == 'Empleado':
        return redirect('empleados')
    usuarios = User.objects.filter(rol__descripcion=rol)

    context = {'usuarios': usuarios, 'rol': rol}
    return render(request, 'base/usuarios.html', context)


@login_required(login_url='login')
def eliminar_usuario(request, usuario_id):
    usuario = User.objects.get(id=usuario_id)
    rol_usuario = usuario.rol
    usuario.delete()

    if rol_usuario.descripcion == 'Empleado':
        if request.user.rol == 'Encargado':
            local = Local.objects.get(encargado=request.user)
            return redirect('empleados', local.id)
        return redirect('empleados')

    if rol_usuario.descripcion == 'Encargado':
        return redirect('usuarios', rol_usuario.descripcion)

    if rol_usuario.descripcion == 'Gerente':
        return redirect('usuarios', rol_usuario.descripcion)

    else:
        return redirect('home')


@login_required(login_url='login')
def editar_usuario(request, usuario_id):
    usuario = User.objects.get(id=usuario_id)
    form = UsuarioUpdateForm(instance=usuario)
    if request.method == "POST":

        nombre = request.POST.get("nombre")
        apellido = request.POST.get("apellido")
        direccion = request.POST.get('direccion')
        telefono = request.POST.get('telefono')

        usuario.nombre = nombre
        usuario.apellido = apellido
        usuario.direccion = direccion
        usuario.telefono = telefono
        usuario.save()
        return redirect('usuarios')

    context = {"form": form}
    return render(request, 'base/editar_usuario.html', context)

# TipoEspecialidad


@login_required(login_url='login')
def page_especialidad(request):
    especialidades = Tipo_Especialidad.objects.all()
    context = {'especialidades': especialidades}
    return render(request, 'base/especialidades.html', context)


@login_required(login_url='login')
def agregar_especialidad(request):
    form = EspecialidadForm()
    if request.method == "POST":

        especialidad_obtenida = request.POST.get('descripcion')
        if Tipo_Especialidad.objects.filter(descripcion=especialidad_obtenida).first():
            return HttpResponse('Una Especialidad con esta descripcion ya existe!')

        Tipo_Especialidad.objects.create(descripcion=especialidad_obtenida)
        return redirect('especialidades')

    context = {'form': form}
    return render(request, 'base/agregar_especialidad.html', context)


@login_required(login_url='login')
def eliminar_especialidad(request, especialidad_id):
    especialidad = Tipo_Especialidad.objects.get(id=especialidad_id)
    especialidad.delete()
    return redirect('especialidades')


@login_required(login_url='login')
def editar_especialidad(request, especialidad_id):
    especialidad = Tipo_Especialidad.objects.get(id=especialidad_id)
    if request.method == "POST":
        form = EspecialidadForm(request.POST, instance=especialidad)
        if form.is_valid():
            form.save()
            return redirect('especialidades')
    else:
        form = EspecialidadForm(instance=especialidad)

    context = {"form": form}
    return render(request, 'base/editar_especialidad.html', context)


# Empleado

@login_required(login_url='login')
def page_empleados(request):
    especialidades = Tipo_Especialidad.objects.all()
    ropas = Tipo_Ropa.objects.all()
    nombre_local = request.GET.get('local')
    local = None
    if nombre_local:
        local = Local.objects.get(nombre=nombre_local)
        empleados = local.empleado.all()
    else:
        empleados = Empleado.objects.all()

    if request.method == "POST":
        empelado_id = request.POST.get("empleado_id")
        empleado = Empleado.objects.get(id=empelado_id)

        local_id = request.POST.get("local_id")
        local = Local.objects.get(id=local_id)

        today = datetime.date.today()

        for idx, dia in enumerate(DIAS_LABORABLES):
            hora_ingreso = request.POST.get(f"ingreso_{dia}")
            hora_salida = request.POST.get(f"salida_{dia}")

            try:
                ingreso = datetime.datetime.fromisocalendar(
                    today.year, today.isocalendar().week, idx+1)
                ingreso = ingreso.replace(
                    hour=int(hora_ingreso[:2]), minute=int(hora_ingreso[-2:]))

                salida = datetime.datetime.fromisocalendar(
                    today.year, today.isocalendar().week, idx+1)
                salida = ingreso.replace(
                    hour=int(hora_salida[:2]), minute=int(hora_salida[-2:]))

                horario_de_trabajo, created = HorarioDeTrabajo.objects.get_or_create(
                    horario_ingreso=ingreso, horario_salida=salida, empleado=empleado, local=local)
                horario_de_trabajo.save()
            except ValueError as exc:
                continue
        return redirect(request.META['HTTP_REFERER'])

    if local:
        horarios_por_empleado = {empleado.id: {
            'nombre': empleado.usuario.nombre,
            'apellido': empleado.usuario.apellido,
            'usuario_id': empleado.usuario.id,
            'especialidad': empleado.especialidad.descripcion,
            'ropa': empleado.ropa.descripcion,
            'mail': empleado.usuario.mail,
            'direccion': empleado.usuario.direccion,
            'telefono': empleado.usuario.telefono,
            'fecha_nacimiento': empleado.usuario.fecha_nacimiento.strftime("%d/%m/%Y"),
            'dni': empleado.usuario.dni,
            'horarios': empleado.obtener_horarios_de_trabajo_semana_actual(local=local),
            'locales': [local.nombre for local in empleado.local_set.all()]
        } for empleado in empleados}
    else:
        horarios_por_empleado = {empleado.id: {
            'nombre': empleado.usuario.nombre,
            'apellido': empleado.usuario.apellido,
            'usuario_id': empleado.usuario.id,
            'especialidad': empleado.especialidad.descripcion,
            'ropa': empleado.ropa.descripcion,
            'mail': empleado.usuario.mail,
            'direccion': empleado.usuario.direccion,
            'telefono': empleado.usuario.telefono,
            'fecha_nacimiento': empleado.usuario.fecha_nacimiento.strftime("%d/%m/%Y"),
            'dni': empleado.usuario.dni,
            'horarios': empleado.obtener_horarios_de_trabajo_semana_actual(),
            'locales': [local.nombre for local in empleado.local_set.all()]
        } for empleado in empleados}

    context = {'horarios_por_empleado': horarios_por_empleado,
               'especialidades': especialidades, 'ropas': ropas, 'dias_laborables': DIAS_LABORABLES}
    if nombre_local:
        context.update({'local': local})
    return render(request, 'base/empleados.html', context)


@login_required(login_url='login')
def actualizar_especialidades(request):
    if request.method == "GET" and request.headers.get('x-requested-with') == 'XMLHttpRequest':

        especialidades = Tipo_Especialidad.objects.all()

        especialidad_obtenida = request.GET.get('especialidad')
        if not especialidad_obtenida:
            messages.error(request, 'Error al obtener la especialidad!')
            return redirect(request.META['HTTP_REFERER'])

        if especialidades.filter(descripcion=especialidad_obtenida).first():
            messages.error(
                request, 'Una Especialidad con esta descripcion ya existe!')
            return redirect(request.META['HTTP_REFERER'])

        especialidades.create(descripcion=especialidad_obtenida)

        descripciones_especialidades = [
            especialidad.descripcion for especialidad in especialidades]

        return JsonResponse({'especialidades': descripciones_especialidades})


@login_required(login_url='login')
def actualizar_ropas(request):
    if request.method == "GET" and request.headers.get('x-requested-with') == 'XMLHttpRequest':

        ropas = Tipo_Ropa.objects.all()

        ropa_obtenida = request.GET.get('ropa')
        if not ropa_obtenida:
            messages.error(request, 'Error al obtener la ropa!')
            return redirect(request.META['HTTP_REFERER'])

        if ropas.filter(descripcion=ropa_obtenida).first():
            messages.error(request, 'Una Ropa con esta descripcion ya existe!')
            return redirect(request.META['HTTP_REFERER'])

        ropas.create(descripcion=ropa_obtenida)

        descripciones_ropas = [ropa.descripcion for ropa in ropas]

        return JsonResponse({'ropas': descripciones_ropas})


@login_required(login_url='login')
def editar_empleado(request, empleado_id):
    empleado = Empleado.objects.get(id=empleado_id)
    usuario = User.objects.get(id=empleado.usuario.id)
    form_empleado = EmpleadoUpdateForm(instance=empleado)
    form_usuario = UsuarioUpdateForm(instance=usuario)
    locales = Local.objects.all()
    if request.method == "POST":

        nombre = request.POST.get("nombre")
        apellido = request.POST.get("apellido")
        direccion = request.POST.get('direccion')
        telefono = request.POST.get('telefono')
        ropa_id = request.POST.get("ropa")
        ropa = Tipo_Ropa.objects.get(pk=ropa_id)
        especialidad_id = request.POST.get('especialidad')
        especialidad = Tipo_Especialidad.objects.get(pk=especialidad_id)

        empleado.usuario.nombre = nombre
        empleado.usuario.apellido = apellido
        empleado.usuario.direccion = direccion
        empleado.usuario.telefono = telefono
        empleado.ropa = ropa
        empleado.especialidad = especialidad
        empleado.usuario.save()

        empleado.save()

        lista_locales = request.POST.getlist('lista_locales')
        locales_seleccionados = Local.objects.filter(id__in=lista_locales)

        for local in locales:
            if local in locales_seleccionados:
                # agregmos el empleado a este local
                local.empleado.add(empleado)

            else:
                # lo eliminamos del local
                local.empleado.remove(empleado)

        if request.user.rol == 'Encargado':

            return redirect('empleados', request.user.local)
        return redirect('empleados')

    context = {"form_empleado": form_empleado, 'form_usuario': form_usuario,
               'locales': locales, 'empleado': empleado}
    return render(request, 'base/editar_empleado.html', context)


# HORARIO
def page_horarios(request, empleado_id):
    empleado = Empleado.objects.get(id=empleado_id)
    horarios = empleado.horariodetrabajo_set.all()
    locales = empleado.local_set.all()
    urls_calendarios = {}
    for local in locales:
        urls_calendarios[local.nombre_completo] = CALENDARS_URLS[local.mail]
    context = {'empleado': empleado, 'horarios': horarios,
               'urls_calendarios': urls_calendarios}
    return render(request, 'base/horarios.html', context)


def agregar_horarios(request, local_id):

    local = Local.objects.get(id=local_id)
    empleados = local.empleado.all()

    if request.method == "POST":
        local_id = request.POST.get("local_id")
        local = Local.objects.get(id=local_id)

        empleado_id = request.POST.get("empleado_id")
        empleado = Empleado.objects.get(id=empleado_id)

        today = datetime.date.today()

        # for empleado in empleados:
        for idx, dia in enumerate(DIAS_LABORABLES):
            hora_ingreso = request.POST.get(f"ingreso_{dia}")
            hora_salida = request.POST.get(f"salida_{dia}")

            try:
                ingreso = datetime.datetime.fromisocalendar(
                    today.year, today.isocalendar().week, idx+1)
                ingreso = ingreso.replace(
                    hour=int(hora_ingreso[:2]), minute=int(hora_ingreso[-2:]))

                salida = datetime.datetime.fromisocalendar(
                    today.year, today.isocalendar().week, idx+1)
                salida = ingreso.replace(
                    hour=int(hora_salida[:2]), minute=int(hora_salida[-2:]))

                horario_de_trabajo, created = HorarioDeTrabajo.objects.get_or_create(
                    horario_ingreso=ingreso, horario_salida=salida, empleado=empleado, local=local)
                horario_de_trabajo.save()

            except ValueError as exc:
                continue

        return redirect(request.META['HTTP_REFERER'])

    if local:
        horarios_por_empleado = {empleado.id: {
            'nombre': empleado.usuario.nombre,
            'apellido': empleado.usuario.apellido,
            'especialidad': empleado.especialidad.descripcion,
            'ropa': empleado.ropa.descripcion,
            'mail': empleado.usuario.mail,
            'direccion': empleado.usuario.direccion,
            'telefono': empleado.usuario.telefono,
            'fecha_nacimiento': empleado.usuario.fecha_nacimiento.strftime("%d/%m/%Y"),
            'dni': empleado.usuario.dni,
            'horarios': empleado.obtener_horarios_de_trabajo_semana_actual(local=local)
        } for empleado in empleados}
    else:
        horarios_por_empleado = {empleado.id: {
            'nombre': empleado.usuario.nombre,
            'apellido': empleado.usuario.apellido,
            'especialidad': empleado.especialidad.descripcion,
            'ropa': empleado.ropa.descripcion,
            'mail': empleado.usuario.mail,
            'direccion': empleado.usuario.direccion,
            'telefono': empleado.usuario.telefono,
            'fecha_nacimiento': empleado.usuario.fecha_nacimiento.strftime("%d/%m/%Y"),
            'dni': empleado.usuario.dni,
            'horarios': empleado.obtener_horarios_de_trabajo_semana_actual()
        } for empleado in empleados}

    context = {'horarios_por_empleado': horarios_por_empleado,
               'local': local, 'dias_laborables': DIAS_LABORABLES}
    return render(request, 'base/agregar_horario.html', context)


def generar_eventos_calendario(request):
    if request.method == "GET" and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        local_id = request.GET.get("local_id")
        local = Local.objects.get(id=local_id)
        agregar_eventos(local)
        return JsonResponse({'status': 1})

# def eliminar_horario(request, horario_id):
#     horario = Horario.objects.get(id=horario_id)
#     horario.delete()
#     return redirect('Horario')


# def editar_horario(request, horario_id):
#     horario = Horario.objects.get(id=horario_id)
#     if request.method == "POST":
#         form = HorarioForm(request.POST, instance=horario)
#         if form.is_valid():
#             form.save()
#             return redirect('Horario')
#     else:
#         form = HorarioForm(instance=horario)

#     context = {"form": form}
#     return render(request, 'base/editar_horario.html', context)


# ROPA

@login_required(login_url='login')
def page_ropa(request):
    ropas = Tipo_Ropa.objects.all()
    context = {'ropas': ropas}
    return render(request, 'base/tipo_ropas.html', context)


@login_required(login_url='login')
def agregar_ropa(request):
    form = RopaForm()
    if request.method == "POST":

        ropa_obtenida = request.POST.get('descripcion')
        if Tipo_Ropa.objects.filter(descripcion=ropa_obtenida).first():
            return HttpResponse('Un tipo de Ropa con esta descripcion ya existe!')

        talle = request.POST.get("talle")

        Tipo_Ropa.objects.create(descripcion=ropa_obtenida,
                                 talle=talle)
        return redirect('ropas')

    context = {'form': form}
    return render(request, 'base/agregar_ropa.html', context)


@login_required(login_url='login')
def eliminar_ropa(request, ropa_id):
    ropa = Tipo_Ropa.objects.get(id=ropa_id)
    ropa.delete()
    return redirect('ropas')


@login_required(login_url='login')
def editar_ropa(request, ropa_id):
    ropa = Tipo_Ropa.objects.get(id=ropa_id)
    if request.method == "POST":
        form = RopaForm(request.POST, instance=ropa)
        if form.is_valid():
            form.save()
            return redirect('ropas')
    else:
        form = RopaForm(instance=ropa)

    context = {"form": form}
    return render(request, 'base/editar_ropa.html', context)


# Caja CHICA

@login_required(login_url='login')
def page_cajachica(request):
    cajas = Caja_Chica.objects.all()
    context = {'cajas': cajas}
    return render(request, 'base/cajachica.html', context)


@login_required(login_url='login')
def agregar_cajachica(request):
    form = Caja_Chica()
    locales = Local.object.all()
    if request.method == "POST":

        caja_obtenida = request.POST.get('caja')  # pepe
        caja_obtenida = caja_obtenida.upper()
        if Caja_Chica.objects.filter(descripcion=caja_obtenida).first():
            return HttpResponse('Una Caja Chica para este Local ya existe!')

        local_id = request.POST.get('local')
        local = Local.objects.get(pk=local_id)
        monto_semanal = request.POST.get("monto_semanal")
        semana = request.POST.get('semana')

        Caja_Chica.objects.create(local=local,
                                  monto_semanal=monto_semanal,
                                  semana=semana
                                  )
        return redirect('Cajachica')

    context = {'form': form, 'locales': locales}
    return render(request, 'base/agregar_cajachica.html', context)


@login_required(login_url='login')
def eliminar_cajachica(request, cajachica_id):
    cajachica = Caja_Chica.objects.get(id=cajachica_id)
    cajachica.delete()
    return redirect('Cajachica')


@login_required(login_url='login')
def editar_cajachica(request, cajachica_id):
    cajachica = Caja_Chica.objects.get(id=cajachica_id)
    if request.method == "POST":
        form = CajaChicaForm(request.POST, instance=cajachica)
        if form.is_valid():
            form.save()
            return redirect('Cajachica')
    else:
        form = CajaChicaForm(instance=cajachica)

    context = {"form": form}
    return render(request, 'base/editar_cajachica.html', context)


# PAGO PROVEEDORES
@login_required(login_url='login')
def pagos_proveedor(request):
    PagosProveedor = Pago_Proveedor.objects.all()
    context = {'PagosProveedor': PagosProveedor}
    return render(request, 'base/pagosproveedor.html', context)


@login_required(login_url='login')
def agregar_pagosproveedor(request):
    form = PagosProveedorForm()
    proveedores = Proveedor.objects.all()
    locales = Local.objects.all()
    tipopagos = Tipo_Pago.objects.all()
    nombre_local = request.GET.get('local')
    if nombre_local:
        local = Local.objects.get(nombre=nombre_local)
    if request.method == "POST":

        if not local:
            local_id = request.POST.get('local')
            local = Local.objects.get(id=local_id)
        proveedor_id = request.POST.get('proveedor')
        proveedor = Proveedor.objects.get(id=proveedor_id)
        monto = request.POST.get("monto")
        tipo_pago_id = request.POST.get('tipos_pagos')
        tipo_pago = Tipo_Pago.objects.get(id=tipo_pago_id)
        descripcion = request.POST.get('descripcion')

        Pago_Proveedor.objects.create(proveedor=proveedor,
                                      monto=monto,
                                      local=local,
                                      tipo_pago=tipo_pago,
                                      descripcion=descripcion
                                      )

        return redirect('local', local_id=local.id)

    context = {'form': form, 'proveedores': proveedores,
               'tipopagos': tipopagos, 'locales': locales}
    if nombre_local:
        context.update({'local': local})
    return render(request, 'base/agregar_pagosproveedor.html', context)


@login_required(login_url='login')
def eliminar_pagosproveedor(request, pagosproveedor_id):
    pagosproveedor = Pago_Proveedor.objects.get(id=pagosproveedor_id)
    pagosproveedor.delete()
    return redirect('local', local_id=pagosproveedor.local_id)


@login_required(login_url='login')
def editar_pagosproveedor(request, pagosproveedor_id):
    pagosproveedor = Pago_Proveedor.objects.get(id=pagosproveedor_id)
    form = PagosProveedorForm(instance=pagosproveedor)
    if request.method == "POST":

        monto = request.POST.get('monto')
        tipo_pago_id = request.POST.get('tipo_pago')
        tipo_pago = Tipo_Pago.objects.get(id=tipo_pago_id)
        proveedor_id = request.POST.get('proveedor')
        proveedor = Proveedor.objects.get(id=proveedor_id)
        descripcion = request.POST.get('descripcion')

        pagosproveedor.monto = monto
        pagosproveedor.tipo_pago = tipo_pago
        pagosproveedor.proveedor = proveedor
        pagosproveedor.descripcion = descripcion

        pagosproveedor.save()

        return redirect('local', local_id=pagosproveedor.local_id)

    context = {"form": form}
    return render(request, 'base/editar_pagosproveedor.html', context)


# Sueldo Semanal
@login_required(login_url='login')
def sueldo_semanal(request):
    # filtrar por local
    sueldos_semanales = Sueldo_Semanal.objects.all()
    context = {'sueldos_semanales': sueldos_semanales}
    return render(request, 'base/sueldo_semanal.html', context)


@login_required(login_url='login')
def agregar_sueldo_semanal(request, local_id):

    # jornada = JornadaLaboral.objects.first()
    # horas_trabajadas = jornada.horas_trabajadas()

    form = SueldoSemanalForm()
    local = Local.objects.get(id=local_id)
    sueldos_por_empleado = local.get_sueldos_semanales_por_empleado()
    tipo_pagos = Tipo_Pago.objects.all()

    if request.method == "POST":
        empelado_id = request.POST.get("empleado_id")
        empleado = Empleado.objects.get(id=empelado_id)

        today = datetime.date.today()

        lista_jornadas = []
        for idx, dia in enumerate(DIAS_LABORABLES):
            hora_ingreso = request.POST.get(f"ingreso_{dia}")
            hora_salida = request.POST.get(f"salida_{dia}")

            try:
                ingreso = datetime.datetime.fromisocalendar(
                    today.year, today.isocalendar().week, idx+1)
                ingreso = ingreso.replace(
                    hour=int(hora_ingreso[:2]), minute=int(hora_ingreso[-2:]))

                salida = datetime.datetime.fromisocalendar(
                    today.year, today.isocalendar().week, idx+1)
                salida = ingreso.replace(
                    hour=int(hora_salida[:2]), minute=int(hora_salida[-2:]))

                jornada_laboral, created = JornadaLaboral.objects.get_or_create(
                    horario_ingreso=ingreso, horario_salida=salida)
                lista_jornadas.append(jornada_laboral)
            except ValueError as exc:
                continue

        # bono = request.POST.get('bono')

        local = Local.objects.get(id=local_id)

        sueldo_semanal, created = Sueldo_Semanal.objects.get_or_create(empleado=empleado,
                                                                       local=local,
                                                                       fecha__week=today.isocalendar().week)

        sueldo_semanal.actualizar_jornadas_laborales(lista_jornadas)
        sueldo_semanal.save()

        return redirect('agregar-sueldo', local_id)

    context = {'form': form, 'sueldos_por_empleado': sueldos_por_empleado,
               'tipo_pagos': tipo_pagos, 'dias_laborables': DIAS_LABORABLES}
    return render(request, 'base/agregar_sueldo_semanal.html', context)


@login_required(login_url='login')
def eliminar_sueldosemanal(request, sueldosemanal_id):
    sueldosemanal = Sueldo_Semanal.objects.get(id=sueldosemanal_id)
    sueldosemanal.delete()
    return redirect('Sueldosemanal')


@login_required(login_url='login')
def editar_sueldosemanal(request, sueldosemanal_id):
    sueldosemanal = Pago_Proveedor.objects.get(id=sueldosemanal_id)
    if request.method == "POST":
        form = SueldoSemanalForm(request.POST, instance=sueldosemanal)
        if form.is_valid():
            form.save()
            return redirect('Sueldosemanal')
    else:
        form = SueldoSemanalForm(instance=sueldosemanal)

    context = {"form": form}
    return render(request, 'base/editar_sueldosemanal.html', context)


@login_required(login_url='login')
def page_locales(request):
    cajas_chicas = Caja_Chica.objects.filter(
        semana__week=datetime.date.today().isocalendar()[1])
    context = {'cajas_chicas': cajas_chicas}
    return render(request, 'base/locales.html', context)


@login_required(login_url='login')
def agregar_local(request):
    form = LocalForm()
    encargados = User.objects.filter(rol__descripcion='Encargado')
    empleados = Empleado.objects.all()
    proveedores = Proveedor.objects.all()
    if request.method == "POST":

        nombre_obtenida = request.POST.get('nombre')
        nombre_obtenida = nombre_obtenida.upper()
        if Local.objects.filter(nombre=nombre_obtenida).first():
            return HttpResponse('Un local con este nombre ya existe!')

        lista_empleados = request.POST.getlist('lista_empleados')
        lista_proveedores = request.POST.getlist('lista_proveedores')

        empleados_seleccionados = Empleado.objects.filter(
            id__in=lista_empleados)
        proveedores_seleccionados = Proveedor.objects.filter(
            id__in=lista_proveedores)

        logo = request.FILES.get('logo')
        mail = request.POST.get("mail")
        direccion = request.POST.get("direccion")  # ERRROR
        telefono = request.POST.get("telefono")

        local = Local.objects.create(nombre=nombre_obtenida,
                                     mail=mail,
                                     direccion=direccion,
                                     telefono=telefono,
                                     logo=logo
                                     )
        local.save()

        for empleado in empleados_seleccionados:
            local.empleado.add(empleado)

        for proveedor in proveedores_seleccionados:
            local.proveedor.add(proveedor)

        encargado_id = request.POST.get('encargado')
        if encargado_id:
            encargado = User.objects.get(id=encargado_id)
            local.encargado = encargado
            local.save()

        return redirect('local', local.id)

    context = {'form': form, 'encargados': encargados, 'empleados': empleados,
               'proveedores': proveedores}
    return render(request, 'base/agregar_local.html', context)


@login_required(login_url='login')
def eliminar_local(request, local_id):
    locales = LocalForm.objects.get(id=local_id)
    locales.delete()
    return redirect('locales')


@login_required(login_url='login')
def editar_local(request, local_id):
    local = Local.objects.get(id=local_id)
    if request.method == "POST":
        form = LocalForm(request.POST, instance=local)
        if form.is_valid():
            form.save()
            return redirect('locales')
    else:
        form = LocalForm(instance=local)

    context = {"form": form}
    return render(request, 'base/editar_local.html', context)


@login_required(login_url='login')
def page_local(request, local_id):
    # desde esta view tenemos que poder agregar un pago y un retiro
    # y redireccionar a las views de empleado, proveedor y productos
    hoy = datetime.date.today()
    semana = hoy.isocalendar().week

    local = Local.objects.get(id=local_id)
    retiros = Retiros.objects.filter(local=local, fecha__date=hoy)
    pagos = Pago_Proveedor.objects.filter(local=local, fecha__week=semana)

    total_retiros_hoy = local.total_retiros_hoy

    try:
        caja_chica = Caja_Chica.objects.get(
            semana__week=semana, local=local)  # trae caja chica del local en la semana actual
    except:
        caja_chica = Caja_Chica.objects.create(
            local=local,
            monto_semanal=0,
            semana=datetime.date.today()
        )

    if request.method == "POST":
        caja_chica.monto_semanal = request.POST.get('monto')
        caja_chica.save()
        return redirect('local', local.id)

    monto_inicial = caja_chica.monto_semanal
    monto_actual = local.monto_actual

    context = {
        'rol': request.user.rol.descripcion,
        'local': local,
        'retiros': retiros,
        'pagos': pagos,
        'monto_inicial': monto_inicial,
        'monto_actual': monto_actual,
        'total_retiros_hoy': total_retiros_hoy
    }
    return render(request, 'base/local.html', context)


# RETIROS
@login_required(login_url='login')
def page_retiros(request, local_id):
    retiros = Retiros.objects.filter(local=local_id)
    context = {'retiros': retiros}
    return render(request, 'base/retiros.html', context)


@login_required(login_url='login')
def agregar_retiro(request):
    form_retiro = RetirosForm()
    nombre_local = request.GET.get('local')
    if nombre_local:
        local = Local.objects.get(nombre=nombre_local)

    if request.method == "POST":

        monto = request.POST.get("monto")

        cajero = Empleado.objects.get(usuario_id=request.user.id)  #

        if cajero not in local.empleado.all():
            return HttpResponse('Este empleado no estar registrado en este local!')

        Retiros.objects.create(monto=monto,
                               local=local,
                               cajero=cajero)
        return redirect('home')

    context = {'form_retiro': form_retiro}
    if nombre_local:
        context.update({'local': local})
    return render(request, 'base/agregar_retiro.html', context)


@login_required(login_url='login')
def cancelar_retiro(request, retiro_id):
    retiro = Retiros.objects.get(id=retiro_id)
    retiro.cancelado = True
    retiro.save()
    return redirect('home')


def about(request):
    return render(request, "base/about.html")
