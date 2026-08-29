from django import forms
from .models import Property

class PropertyForm(forms.ModelForm):
    class Meta:
        model = Property
        fields = ['name', 'address', 'county', 'total_units', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Riverside Apartments'}),
            'address': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '123 Street, City'}),
            'county': forms.Select(attrs={'class': 'form-control'}),
            'total_units': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '0'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Optional details...'}),
        }
