from django.contrib import admin
from django.urls import path

from .import views

urlpatterns = [
    path("", views.home, name="home"),
    path("login", views.page_login, name="login"),
    path("logout", views.page_logout, name="logout"),
    path("registrar/<str:rol_desc>/", views.page_register, name="registrar"),


    path("proveedores/<int:local_id>/",
         views.page_proveedores, name="proveedores"),
    path("agregar-proveedor/<int:local_id>/",
         views.agregar_proveedor, name="agregar-proveedor"),
    path('eliminar-proveedor/<int:proveedor_id>/<int:local_id>/',
         views.eliminar_proveedor, name="eliminar-proveedor"),
    path('editar-proveedor/<int:local_id>/<int:proveedor_id>',
         views.editar_proveedor, name="editar-proveedor"),

    path("productos", views.page_producto, name="productos"),
    path("agregar-producto", views.agregar_producto, name="agregar-producto"),
    path('eliminar-producto/<int:producto_id>/',
         views.eliminar_producto, name="eliminar-producto"),
    path('editar-producto/<int:producto_id>',
         views.editar_producto, name="editar-producto"),

    path("roles", views.page_rol, name="roles"),
    path("agregar-rol", views.agregar_rol, name="agregar-rol"),
    path('eliminar-rol/<int:rol_id>/',
         views.eliminar_rol, name="eliminar-rol"),

    path("usuarios/<str:rol>/", views.page_usuarios, name="usuarios"),
    path('eliminar-usuario/<int:usuario_id>/',
         views.eliminar_usuario, name="eliminar-usuario"),
    path('editar-usuario/<int:usuario_id>/',
         views.editar_usuario, name="editar-usuario"),

    path("empleados", views.page_empleados, name="empleados"),
    path("editar-empleado/<int:empleado_id>",
         views.editar_empleado, name="editar-empleado"),
    path("actualizar-especialidades", views.actualizar_especialidades,
         name="actualizar-especialidades"),
    path("actualizar-ropas", views.actualizar_ropas,
         name="actualizar-ropas"),

    path("horarios/<int:empleado_id>",
         views.page_horarios, name="horarios"),
    path("agregar-horarios/<int:local_id>",
         views.agregar_horarios, name="agregar-horarios"),
    path("generar-eventos",
         views.generar_eventos_calendario, name="generar-eventos"),


    path("especialidades", views.page_especialidad, name="especialidades"),
    path("agregar-especialidad", views.agregar_especialidad,
         name="agregar-especialidad"),
    path("eliminar-especialidad/<int:especialidad_id>",
         views.eliminar_especialidad, name="eliminar-especialidad"),
    path("editar-especialidad/<int:especialidad_id>",
         views.editar_especialidad, name="editar-especialidad"),

    path("ropas", views.page_ropa, name="ropas"),
    path("agregar-ropa", views.agregar_ropa,
         name="agregar-ropa"),
    path("eliminar-ropa/<int:ropa_id>",
         views.eliminar_ropa, name="eliminar-ropa"),
    path("editar-ropa/<int:ropa_id>",
         views.editar_ropa, name="editar-ropa"),

    path("cajachica", views.page_cajachica, name="Cajachica"),
    path("agregarCajachica", views.agregar_cajachica,
         name="agregarCajachica"),
    path("eliminarcajachica/<int:cajachica_id>",
         views.eliminar_cajachica, name="eliminarCajachica"),
    path("editarcajachica/<int:cajachica_id>",
         views.editar_cajachica, name="editarCajachica"),

    path("pagos", views.pagos_proveedor, name="pagos"),
    path("agregar-pago", views.agregar_pagosproveedor,
         name="agregar-pago"),
    path("eliminar-pago/<int:pagosproveedor_id>",
         views.eliminar_pagosproveedor, name="eliminar-pago"),
    path("editar-pago/<int:pagosproveedor_id>",
         views.editar_pagosproveedor, name="editar-pago"),

    path("local/<int:local_id>", views.page_local, name='local'),
    path("locales", views.page_locales, name="locales"),
    path("agregar-local", views.agregar_local,
         name="agregar-local"),
    path('eliminar-local/<int:local_id>',
         views.eliminar_local, name="eliminar-local"),
    path('editar-local/<int:local_id>',
         views.editar_local, name="editar-local"),

    path("retiros/<int:local_id>", views.page_retiros, name="retiros"),
    path("agregar-retiro", views.agregar_retiro,
         name="agregar-retiro"),
    path('cancelar-retiro/<int:retiro_id>',
         views.cancelar_retiro, name="cancelar-retiro"),

    path("sueldo-semanal", views.sueldo_semanal, name="sueldos"),
    path("agregar-sueldo/<int:local_id>", views.agregar_sueldo_semanal,
         name="agregar-sueldo"),

    path("vistapresidente", views.vistapresidente, name="vistapresidente"),

    # reportes
    path("reporte-pagos/<int:local_id>/",
         views.reporte_pagos_proveedores, name="reporte-pagos"),
    path("actualizar-reporte-pagos", views.actualizar_reporte_pagos_proveedores,
         name="actualizar-reporte-pagos"),

    path("reporte-sueldos/<int:local_id>/",
         views.reporte_pagos_sueldos, name="reporte-sueldos"),
    path("actualizar-reporte-sueldos", views.actualizar_reporte_pagos_sueldos,
         name="actualizar-reporte-sueldos"),

    path("reporte-horarios-trabajados/<int:empleado_id>/",
         views.reporte_horarios_empleado, name="reporte-horarios-trabajados"),
    path("actualizar-reporte-horarios", views.actualizar_reporte_horarios,
         name="actualizar-reporte-horarios"),



    path("reporte-locales-pagos",
         views.reporte_pagos_por_local, name="reporte-locales-pagos"),
    path("actualizar-reporte-locales-pagos", views.actualizar_reporte_pagos_por_local,
         name="actualizar-reporte-locales-pagos"),


     path("about/", views.about, name="about"),

]
