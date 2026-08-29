from django import forms
from django.core.validators import RegexValidator
from .models import Tenant
from properties.models import Property
from units.models import Unit
from accounts.access_utils import get_accessible_properties

class TenantForm(forms.ModelForm):
    kra_pin = forms.CharField(
        max_length=11,
        required=False,
        validators=[
            RegexValidator(
                regex=r'^[A-Za-z]\d{9}[A-Za-z]$',
                message='Enter a valid KRA PIN (1 letter, 9 digits, 1 letter, e.g. A123456789B)',
            ),
        ],
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'A123456789B',
            'maxlength': '11',
        }),
    )

    unit = forms.ModelChoiceField(
        queryset=Unit.objects.none(),
        required=False,
        empty_label='No Unit',
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'addTenantUnit'}),
    )

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        queryset = Property.objects.none()
        if user is not None and user.is_authenticated:
            queryset = get_accessible_properties(user).order_by('name')
        self.fields['property'].queryset = queryset
        self.fields['unit'].queryset = Unit.objects.none()
        if self.instance and self.instance.pk:
            if self.instance.property_id:
                self.fields['property'].initial = self.instance.property_id
                self.fields['unit'].queryset = Unit.objects.filter(property_id=self.instance.property_id)
            elif self.instance.unit_id:
                self.fields['property'].initial = self.instance.unit.property_id
                self.fields['unit'].queryset = Unit.objects.filter(property_id=self.instance.unit.property_id)

    def clean_kra_pin(self):
        value = self.cleaned_data.get('kra_pin')
        if value:
            return value.upper()
        return None

    class Meta:
        model = Tenant
        fields = ['property', 'unit', 'first_name', 'last_name', 'phone_number', 'next_of_kin_name', 'description', 'deposit_required', 'deposit_amount', 'next_of_kin_phone_number', 'kra_pin', 'id_card_front', 'id_card_back']
        widgets = {
            'property': forms.Select(attrs={'class': 'form-select'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'next_of_kin_name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'deposit_required': forms.CheckboxInput(attrs={'class': 'form-check-input', 'id': 'depositCheck'}),
            'deposit_amount': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Enter deposit amount'}),
            'next_of_kin_phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'id_card_front': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*', 'capture': 'environment'}),
            'id_card_back': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*', 'capture': 'environment'}),
        }
