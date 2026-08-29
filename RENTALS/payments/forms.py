from django import forms
from .models import Payment
from units.models import Unit
from accounts.access_utils import get_accessible_properties

class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ['property', 'unit', 'code', 'amount', 'description', 'date']
        widgets = {
            'property': forms.Select(attrs={'class': 'form-select', 'placeholder': 'Select Property'}),
            'unit': forms.Select(attrs={'class': 'form-select', 'placeholder': 'Select House/Unit'}),
            'code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Receipt/reference code'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Amount'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Details'}),
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            acc_props = get_accessible_properties(user)
            self.fields['property'].queryset = acc_props
            self.fields['unit'].queryset = Unit.objects.filter(property__in=acc_props).select_related('property').order_by('property__name', 'name')
