from django import forms
from .models import Maintenance
from units.models import Unit
from accounts.access_utils import get_accessible_properties


class MaintenanceForm(forms.ModelForm):
    class Meta:
        model = Maintenance
        fields = ['property', 'unit', 'date', 'description', 'amount', 'status']
        widgets = {
            'property': forms.Select(attrs={'class': 'form-select', 'placeholder': 'Select Property'}),
            'unit': forms.Select(attrs={'class': 'form-select', 'placeholder': 'Select Unit'}),
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Description'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Amount'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            acc_props = get_accessible_properties(user)
            self.fields['property'].queryset = acc_props
            self.fields['unit'].queryset = Unit.objects.filter(property__in=acc_props).select_related('property').order_by('property__name', 'name')
