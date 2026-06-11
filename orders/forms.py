from django import forms
from apps.orders.models import Order, BillingData
from apps.payments.models import Payment, BankTransferPayment, CashPayment


class ShippingForm(forms.ModelForm):
    """Datos de envío — extiende los campos nuevos de Order."""

    class Meta:
        model = Order
        fields = ['first_name', 'last_name', 'email', 'phone', 'address', 'city']
        labels = {
            'first_name': 'Nombre',
            'last_name':  'Apellido',
            'email':      'Correo electrónico',
            'phone':      'Teléfono',
            'address':    'Dirección',
            'city':       'Ciudad',
        }
        widgets = {
            'first_name': forms.TextInput(attrs={'placeholder': 'Juan'}),
            'last_name':  forms.TextInput(attrs={'placeholder': 'Pérez'}),
            'email':      forms.EmailInput(attrs={'placeholder': 'juan@ejemplo.com'}),
            'phone':      forms.TextInput(attrs={'placeholder': '+595 981 000000'}),
            'address':    forms.TextInput(attrs={'placeholder': 'Av. Mariscal López 1234'}),
            'city':       forms.TextInput(attrs={'placeholder': 'Asunción'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault('class', 'form-input')
        if user:
            self.fields['email'].initial    = user.email
            self.fields['phone'].initial    = user.phone
            self.fields['address'].initial  = user.address
            self.fields['first_name'].initial = user.first_name
            self.fields['last_name'].initial  = user.last_name


class BillingForm(forms.ModelForm):
    class Meta:
        model  = BillingData
        fields = ['business_name', 'ruc']
        labels = {
            'business_name': 'Nombre / Razón Social',
            'ruc':           'RUC',
        }
        widgets = {
            'business_name': forms.TextInput(attrs={'placeholder': 'Empresa S.A.', 'class': 'form-input'}),
            'ruc':           forms.TextInput(attrs={'placeholder': '80012345-1',   'class': 'form-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.required = False   # se valida condicionalmente en la vista


class PaymentMethodForm(forms.Form):
    METHODS = [
        ('bank_transfer', 'Transferencia Bancaria'),
        ('cash',          'Efectivo'),
    ]
    payment_method = forms.ChoiceField(
        choices=METHODS,
        widget=forms.RadioSelect(attrs={'class': 'payment-radio'}),
        initial='cash',
    )
    wants_invoice = forms.BooleanField(required=False, label='Solicitar factura')


class BankTransferForm(forms.ModelForm):
    class Meta:
        model  = BankTransferPayment
        fields = ['bank', 'reference_number', 'transfer_date']
        labels = {
            'bank':             'Banco',
            'reference_number': 'Número de referencia',
            'transfer_date':    'Fecha de transferencia',
        }
        widgets = {
            'bank':             forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Banco Continental'}),
            'reference_number': forms.TextInput(attrs={'class': 'form-input', 'placeholder': '0001234567'}),
            'transfer_date':    forms.DateInput(attrs={'class': 'form-input', 'type': 'date'}),
        }


class CashForm(forms.ModelForm):
    class Meta:
        model  = CashPayment
        fields = ['amount_received', 'observations']
        labels = {
            'amount_received': 'Monto entregado',
            'observations':    'Observaciones',
        }
        widgets = {
            'amount_received': forms.NumberInput(attrs={'class': 'form-input', 'placeholder': '0.00', 'step': '0.01'}),
            'observations':    forms.Textarea(attrs={'class': 'form-input', 'rows': 3, 'placeholder': 'Opcional…'}),
        }