from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

# Create your models here.
from properties.models import Property # Import the Property model

class Unit(models.Model):
    STATUS_CHOICES = [
        ('occupied', 'Occupied'),
        ('vacant', 'Vacant'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='units')
    name = models.CharField(max_length=100)
    rent_amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='vacant')
    tenant_name = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} - {self.property.name}"
    
    def get_assigned_tenant(self):
        """Get the currently assigned tenant for this unit"""
        from leases.models import Lease
        active_lease = self.leases.filter(is_active=True).select_related('tenant').first()
        if active_lease:
            return active_lease.tenant
        if hasattr(self, 'prefetched_tenants'):
            return self.prefetched_tenants[0] if self.prefetched_tenants else None
        return self.tenants.first()
    
    def get_tenant_display_name(self):
        """Get full name of assigned tenant"""
        tenant = self.get_assigned_tenant()
        if tenant:
            return f"{tenant.first_name} {tenant.last_name}"
        return None
    
    def is_occupied(self):
        """Check if unit is occupied based on assigned tenant"""
        return self.get_assigned_tenant() is not None