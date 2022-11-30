from django import forms
from base.models import Retiros, Local, Caja_Chica, Pago_Proveedor, Sueldo_Semanal, Tipo_Especialidad, Tipo_Ropa, Empleado, HorarioDeTrabajo, User, Rol, Producto, Proveedor, Tipo_Pago
from django.contrib.auth.forms import UserCreationForm


class ProveedorForm(forms.ModelForm):

    class Meta:
        model = Proveedor
        fields = ['nombre',
                  'mail',
                  'direccion',
                  'telefono',
                  ]
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': "form-control mr-sm-2",
                'type': 'text',
                'placeholder': "Nombre",
                'aria-label': "Nombre"}),
            'mail': forms.TextInput(attrs={
                'class': "form-control mr-sm-2",
                'type': 'email',
                'placeholder': "Email",
                'aria-label': "Email"}),
            'direccion': forms.TextInput(attrs={
                'class': "form-control mr-sm-2",
                'type': 'text',
                'placeholder': "Dirección",
                'aria-label': "Dirección"}),
            'telefono': forms.TextInput(attrs={
                'class': "form-control mr-sm-2",
                'type': 'text',
                'placeholder': "Teléfono",
                'aria-label': "Teléfono"}),
        }


class ProductoForm(forms.ModelForm):

    proveedores = Proveedor.objects.all().values_list('id', 'nombre')
    proveedor = forms.ChoiceField(label='', choices=proveedores, widget=forms.Select(
        attrs={'required': 'true', 'class': "form-control"}))

    class Meta:
        model = Producto

        fields = ['codigo',
                  'descripcion',
                  'precio_costo',
                  'precio_venta',
                  'precio_mayoreo',
                  'proveedor',
                  'local',
                  ]
        widgets = {
            'codigo': forms.TextInput(attrs={
                'class': "form-control mr-sm-2",
                'type': 'text',
                'placeholder': "Codigo",
                'aria-label': "Codigo"}),
            'descripcion': forms.TextInput(attrs={
                'class': "form-control mr-sm-2",
                'type': 'text',
                'placeholder': "Descripcion",
                'aria-label': "Descripcion"}),
            'precio_costo': forms.TextInput(attrs={
                'class': "form-control mr-sm-2",
                'type': 'text',
                'placeholder': "Precio Costo",
                'aria-label': "Precio Costo"}),
            'precio_venta': forms.TextInput(attrs={
                'class': "form-control mr-sm-2",
                'type': 'text',
                'placeholder': "Precio Venta",
                'aria-label': "Precio Venta"}),
            'precio_mayoreo': forms.TextInput(attrs={
                'class': "form-control mr-sm-2",
                'type': 'text',
                'placeholder': "Precio Mayoreo ",
                'aria-label': "Precio Mayoreo"}),
        }


class RolForm(forms.ModelForm):

    class Meta:
        model = Rol
        fields = '__all__'


class UsuarioForm(UserCreationForm):

    class Meta:
        model = User
        fields = ['nombre',
                  'apellido',
                  'username',
                  'mail',
                  'password1',
                  'password2',
                  'direccion',
                  'telefono',
                  'fecha_nacimiento',
                  'dni',
                  ]


class UsuarioUpdateForm(forms.ModelForm):

    class Meta:
        model = User
        fields = ['nombre',
                  'apellido',
                  'direccion',
                  'telefono',
                  ]
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': "form-control mr-sm-2",
                'type': 'text',
                'placeholder': "Nombre",
                'aria-label': "Nombre"}),
            'apellido': forms.TextInput(attrs={
                'class': "form-control mr-sm-2",
                'type': 'text',
                'placeholder': "Apellido",
                'aria-label': "Apellido"}),
            'direccion': forms.TextInput(attrs={
                'class': "form-control mr-sm-2",
                'type': 'text',
                'placeholder': "Dirección",
                'aria-label': "Dirección"}),
            'telefono': forms.TextInput(attrs={
                'class': "form-control mr-sm-2",
                'type': 'text',
                'placeholder': "Teléfono",
                'aria-label': "Teléfono"}),
        }


class EmpleadoForm(forms.ModelForm):

    class Meta:
        model = Empleado
        fields = '__all__'
        exclude = ["usuario"]


class EmpleadoUpdateForm(forms.ModelForm):

    ropas = Tipo_Ropa.objects.all().values_list('id', 'descripcion')
    ropa = forms.ChoiceField(label='', choices=ropas, widget=forms.Select(
        attrs={'required': 'true', 'class': "form-control"}))

    especialidades = Tipo_Especialidad.objects.all().values_list('id', 'descripcion')
    especialidad = forms.ChoiceField(label='', choices=especialidades, widget=forms.Select(
        attrs={'required': 'true', 'class': "form-control"}))

    class Meta:
        model = Empleado
        fields = ['ropa',
                  'especialidad',
                  ]


class HorarioDeTrabajoForm(forms.ModelForm):

    class Meta:
        model = HorarioDeTrabajo
        fields = '__all__'


class EspecialidadForm(forms.ModelForm):

    class Meta:
        model = Tipo_Especialidad
        fields = '__all__'


class RopaForm(forms.ModelForm):

    class Meta:
        model = Tipo_Ropa
        fields = '__all__'


class CajaChicaForm(forms.ModelForm):

    class Meta:
        model = Caja_Chica
        fields = '__all__'


class PagosProveedorForm(forms.ModelForm):

    proveedores = Proveedor.objects.all().values_list('id', 'nombre')
    proveedor = forms.ChoiceField(label='', choices=proveedores, widget=forms.Select(
        attrs={'required': 'true', 'class': "form-control"}))

    tipos_pagos = Tipo_Pago.objects.all().values_list('id', 'descripcion')
    tipo_pago = forms.ChoiceField(label='', choices=tipos_pagos, widget=forms.Select(
        attrs={'required': 'true', 'class': "form-control"}))

    class Meta:
        model = Pago_Proveedor
        fields = ['proveedor',
                  'monto',
                  'local',
                  'tipo_pago',
                  'descripcion',
                  ]
        widgets = {
            'monto': forms.TextInput(attrs={
                'class': "form-control mr-sm-2",
                'type': 'text',
                'placeholder': "Monto",
                'aria-label': "Monto"}),
            'descripcion': forms.TextInput(attrs={
                'class': "form-control mr-sm-2",
                'type': 'text',
                'placeholder': "Descripción",
                'aria-label': "Descripción"}),
        }


class SueldoSemanalForm(forms.ModelForm):

    class Meta:
        model = Sueldo_Semanal
        fields = ['empleado', 'bono', 'tipo_pago']


class LocalForm(forms.ModelForm):

    class Meta:
        model = Local
        fields = '__all__'


class RetirosForm(forms.ModelForm):

    class Meta:
        model = Retiros
        fields = ['monto']
