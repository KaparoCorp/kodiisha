from django.db import models
from django.utils import timezone

# Create your models here.
from units.models import Unit
from properties.models import Property

class Tenant(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
    ]

    unit = models.ForeignKey(Unit, on_delete=models.CASCADE, related_name='tenants', blank=True, null=True)
    property = models.ForeignKey(Property, on_delete=models.SET_NULL, related_name='tenants', blank=True, null=True)
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=20)
    next_of_kin_name = models.CharField(max_length=255, blank=True, null=True)
    next_of_kin_phone_number = models.CharField(max_length=20)
    description = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='inactive')
    
    # Deposit Fields
    deposit_required = models.BooleanField(default=True)
    deposit_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    # KRA & ID Document Fields
    kra_pin = models.CharField(
        max_length=11, blank=True, null=True,
        help_text="KRA PIN: 1 letter, 9 digits, 1 letter (e.g. A123456789B)",
    )
    id_card_front = models.ImageField(upload_to='tenant_documents/id_cards/front/', blank=True, null=True)
    id_card_back = models.ImageField(upload_to='tenant_documents/id_cards/back/', blank=True, null=True)

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def get_display_property(self):
        """Return the direct property if set, otherwise fall back to the unit's property."""
        if self.property_id:
            return self.property
        if self.unit_id:
            return self.unit.property
        return None

    def __str__(self):
        unit_name = self.unit.name if self.unit else "No Unit"
        return f"{self.first_name} {self.last_name} - {unit_name}"
