from django.contrib import admin

from base.models import Caja_Chica, Empleado, Local, Pago_Proveedor, Producto, Proveedor, Retiros, Rol, Sueldo_Semanal, Tipo_Especialidad, Tipo_Pago, Tipo_Ropa, User, JornadaLaboral, HorarioDeTrabajo

admin.site.register(User)
admin.site.register(Rol)
admin.site.register(Empleado)
admin.site.register(Sueldo_Semanal)
admin.site.register(Retiros)
admin.site.register(Tipo_Pago)
admin.site.register(Tipo_Especialidad)
admin.site.register(Tipo_Ropa)
admin.site.register(Caja_Chica)
admin.site.register(Producto)
admin.site.register(Proveedor)
admin.site.register(Pago_Proveedor)
admin.site.register(Local)
admin.site.register(JornadaLaboral)
admin.site.register(HorarioDeTrabajo)



