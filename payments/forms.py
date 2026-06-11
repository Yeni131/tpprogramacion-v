from django import forms
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
import re

from .models import ShippingAddress, BillingInfo, PaymentInfo


# ---------------------------------------------------------------------------
# Widgets personalizados
# ---------------------------------------------------------------------------

class DateInput(forms.DateInput):
    input_type = "date"


# ---------------------------------------------------------------------------
# Formulario de Envío
# ---------------------------------------------------------------------------

class ShippingAddressForm(forms.ModelForm):
    """Datos de envío obligatorios en el checkout."""

    class Meta:
        model = ShippingAddress
        fields = [
            "email",
            "first_name",
            "last_name",
            "phone",
            "address",
            "city",
            "state",
            "postal_code",
            "country",
        ]
        widgets = {
            "email": forms.EmailInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "correo@ejemplo.com",
                    "autocomplete": "email",
                }
            ),
            "first_name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Tu nombre",
                    "autocomplete": "given-name",
                }
            ),
            "last_name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Tu apellido",
                    "autocomplete": "family-name",
                }
            ),
            "phone": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "+593 99 999 9999",
                    "autocomplete": "tel",
                }
            ),
            "address": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Calle, número, sector",
                    "autocomplete": "street-address",
                }
            ),
            "city": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Tu ciudad",
                    "autocomplete": "address-level2",
                }
            ),
            "state": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Provincia (opcional)",
                }
            ),
            "postal_code": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Código postal (opcional)",
                }
            ),
            "country": forms.TextInput(
                attrs={
                    "class": "form-control",
                }
            ),
        }

    def clean_phone(self):
        phone = self.cleaned_data.get("phone", "")
        # Acepta formatos: +593999999999, 0999999999, etc.
        cleaned = re.sub(r"[\s\-\(\)]", "", phone)
        if not re.match(r"^\+?\d{7,15}$", cleaned):
            raise forms.ValidationError(
                _("Ingresa un número de teléfono válido (7-15 dígitos).")
            )
        return phone

    def clean_first_name(self):
        value = self.cleaned_data.get("first_name", "").strip()
        if len(value) < 2:
            raise forms.ValidationError(_("El nombre debe tener al menos 2 caracteres."))
        return value

    def clean_last_name(self):
        value = self.cleaned_data.get("last_name", "").strip()
        if len(value) < 2:
            raise forms.ValidationError(_("El apellido debe tener al menos 2 caracteres."))
        return value


# ---------------------------------------------------------------------------
# Formulario de Facturación
# ---------------------------------------------------------------------------

class BillingInfoForm(forms.ModelForm):
    """Datos de facturación; campos obligatorios solo cuando se solicita factura."""

    class Meta:
        model = BillingInfo
        fields = ["business_name", "ruc", "billing_email", "billing_address"]
        widgets = {
            "business_name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Nombre o Razón Social",
                }
            ),
            "ruc": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Ej: 1234567890001",
                    "maxlength": "13",
                }
            ),
            "billing_email": forms.EmailInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "facturacion@empresa.com",
                }
            ),
            "billing_address": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Dirección fiscal (opcional)",
                }
            ),
        }

    def __init__(self, *args, requires_invoice=False, **kwargs):
        super().__init__(*args, **kwargs)
        self.requires_invoice = requires_invoice
        if requires_invoice:
            self.fields["business_name"].required = True
            self.fields["ruc"].required = True
        else:
            for field in self.fields.values():
                field.required = False

    def clean_ruc(self):
        ruc = self.cleaned_data.get("ruc", "").strip()
        if self.requires_invoice:
            # RUC ecuatoriano: 13 dígitos
            if not re.match(r"^\d{13}$", ruc):
                raise forms.ValidationError(
                    _("El RUC debe tener exactamente 13 dígitos.")
                )
        return ruc


# ---------------------------------------------------------------------------
# Formulario de Pago: selector del método
# ---------------------------------------------------------------------------

class PaymentMethodForm(forms.Form):
    """Selección del método de pago."""

    method = forms.ChoiceField(
        choices=PaymentInfo.Method.choices,
        widget=forms.RadioSelect(attrs={"class": "payment-method-radio"}),
        label=_("Método de pago"),
    )


# ---------------------------------------------------------------------------
# Formulario de Transferencia Bancaria
# ---------------------------------------------------------------------------

class BankTransferForm(forms.ModelForm):
    """Datos específicos para pago por transferencia bancaria."""

    class Meta:
        model = PaymentInfo
        fields = ["bank_name", "reference_number", "transfer_date", "transfer_receipt"]
        widgets = {
            "bank_name": forms.Select(
                choices=[
                    ("", _("Selecciona tu banco")),
                    ("Banco Pichincha", "Banco Pichincha"),
                    ("Banco Guayaquil", "Banco Guayaquil"),
                    ("Banco Pacífico", "Banco Pacífico"),
                    ("Banco Internacional", "Banco Internacional"),
                    ("Banco Produbanco", "Produbanco"),
                    ("Banco Bolivariano", "Banco Bolivariano"),
                    ("Banco del Austro", "Banco del Austro"),
                    ("Cooperativa JEP", "Cooperativa JEP"),
                    ("Otro", _("Otro")),
                ],
                attrs={"class": "form-control"},
            ),
            "reference_number": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Número de referencia o comprobante",
                }
            ),
            "transfer_date": DateInput(
                attrs={
                    "class": "form-control",
                    "max": str(timezone.now().date()),
                }
            ),
            "transfer_receipt": forms.ClearableFileInput(
                attrs={"class": "form-control", "accept": "image/*,.pdf"}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["bank_name"].required = True
        self.fields["reference_number"].required = True
        self.fields["transfer_date"].required = True
        self.fields["transfer_receipt"].required = False

    def clean_transfer_date(self):
        date = self.cleaned_data.get("transfer_date")
        if date and date > timezone.now().date():
            raise forms.ValidationError(
                _("La fecha de transferencia no puede ser futura.")
            )
        return date


# ---------------------------------------------------------------------------
# Formulario de Pago en Efectivo
# ---------------------------------------------------------------------------

class CashPaymentForm(forms.ModelForm):
    """Datos específicos para pago en efectivo."""

    class Meta:
        model = PaymentInfo
        fields = ["cash_amount_tendered", "cash_pickup_location"]
        widgets = {
            "cash_amount_tendered": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "0.00",
                    "step": "0.01",
                    "min": "0",
                }
            ),
            "cash_pickup_location": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Punto de entrega o dirección acordada",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["cash_amount_tendered"].required = False
        self.fields["cash_pickup_location"].required = False


# ---------------------------------------------------------------------------
# Formulario combinado del Checkout (para uso en la vista)
# ---------------------------------------------------------------------------

class CheckoutForm(forms.Form):
    """
    Formulario maestro que encapsula todos los sub-formularios del checkout.
    Úsalo en la vista para un manejo simplificado.
    """

    requires_invoice = forms.BooleanField(
        required=False,
        label=_("Solicitar factura"),
        widget=forms.CheckboxInput(attrs={"id": "id_requires_invoice", "class": "form-check-input"}),
    )
    payment_method = forms.ChoiceField(
        choices=PaymentInfo.Method.choices,
        widget=forms.RadioSelect(attrs={"class": "payment-method-radio"}),
        label=_("Método de pago"),
    )
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(
            attrs={
                "class": "form-control",
                "rows": 3,
                "placeholder": "Instrucciones especiales para tu pedido (opcional)",
            }
        ),
        label=_("Notas adicionales"),
    )