from django import forms
from django.db.models import Q
from properties.models import Property
from .models import Unit
from tenants.models import Tenant
from accounts.access_utils import get_accessible_properties


class UnitForm(forms.ModelForm):
    tenant = forms.ModelChoiceField(
        queryset=Tenant.objects.none(),
        required=False,
        empty_label='-- Select Tenant --'
    )

    description = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
    )

    status = forms.ChoiceField(
        choices=Unit.STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
    )

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user is not None:
            accessible_props = get_accessible_properties(user)
            self.fields['property'].queryset = accessible_props
            # Allow any assignable tenant to validate (the dropdown is narrowed
            # per-property on the client). Include the currently assigned tenant
            # so editing an occupied unit never fails validation.
            qs = Tenant.objects.filter(
                Q(unit__isnull=True) | Q(unit__property__in=accessible_props)
            ).filter(status='inactive').distinct()
            if self.instance and self.instance.pk:
                from leases.models import Lease
                lease = Lease.objects.filter(unit=self.instance, is_active=True).select_related('tenant').first()
                if lease and lease.tenant:
                    qs = qs | Tenant.objects.filter(pk=lease.tenant.pk)
                    self.fields['tenant'].initial = lease.tenant
            self.fields['tenant'].queryset = qs
        else:
            self.fields['property'].queryset = Property.objects.none()

    def clean(self):
        cleaned_data = super().clean()
        # A unit may exist without a tenant attached. We only assign a tenant
        # when one is explicitly selected, so do not force a tenant here.
        return cleaned_data

    class Meta:
        model = Unit
        fields = ['property', 'name', 'rent_amount', 'description', 'status', 'tenant']
        widgets = {
            'property': forms.Select(attrs={'class': 'form-select'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'rent_amount': forms.NumberInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'tenant': forms.Select(attrs={'class': 'form-select', 'id': 'unitTenantSelect'}),
        }
