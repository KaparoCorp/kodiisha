from django import forms
from .models import WaterBill
from units.models import Unit
from accounts.access_utils import get_accessible_properties


class WaterBillForm(forms.ModelForm):
    class Meta:
        model = WaterBill
        fields = ['unit', 'previous_reading', 'current_reading', 'rate', 'due_date']
        widgets = {
            'unit': forms.Select(attrs={'class': 'form-select', 'placeholder': 'Select Unit'}),
            'previous_reading': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Previous Month Reading'}),
            'current_reading': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Current Month Reading'}),
            'rate': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Rate Per Unit', 'step': '0.01'}),
            'due_date': forms.DateInput(attrs={'class': 'form-control datepicker', 'placeholder': 'Due Date'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            acc_props = get_accessible_properties(user)
            self.fields['unit'].queryset = Unit.objects.filter(property__in=acc_props).select_related('property').order_by('property__name', 'name')
