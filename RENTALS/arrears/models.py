from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Arrears(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('resolved', 'Resolved'),
        ('written_off', 'Written Off'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    invoice = models.ForeignKey('invoices.Invoice', on_delete=models.CASCADE, related_name='arrears')
    tenant = models.ForeignKey('tenants.Tenant', on_delete=models.CASCADE, related_name='arrears')
    unit = models.ForeignKey('units.Unit', on_delete=models.CASCADE, related_name='arrears')
    
    amount_due = models.DecimalField(max_digits=12, decimal_places=2)
    days_overdue = models.IntegerField(default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    date_marked = models.DateTimeField(auto_now_add=True)
    date_resolved = models.DateTimeField(null=True, blank=True)
    
    notes = models.TextField(blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('invoice', 'tenant')
        ordering = ['-date_marked']
    
    def __str__(self):
        return f"Arrears: {self.tenant.first_name} {self.tenant.last_name} - KES {self.amount_due}"
    
    def mark_resolved(self):
        """Mark this arrears record as resolved."""
        self.status = 'resolved'
        self.date_resolved = timezone.now()
        self.save()

