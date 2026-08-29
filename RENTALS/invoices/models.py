from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

# Create your models here.
import uuid
from units.models import Unit
from tenants.models import Tenant
from payments.models import Payment
from django.db.models import Sum

class Invoice(models.Model):
    STATUS_CHOICES = [('Paid', 'Paid'), ('Partially Paid', 'Partially Paid'), ('Unpaid', 'Unpaid')]
    TYPE_CHOICES = [('Rent', 'Rent'), ('Water', 'Water'), ('Service', 'Service')]

    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    invoice_number = models.CharField(max_length=50, unique=True, editable=False)
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='Rent')
    due_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Unpaid')
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.invoice_number:
            # Matches your screenshot format: INV-YearMonth-ShortUUID
            self.invoice_number = f"INV-{self.due_date.strftime('%Y%m')}-{uuid.uuid4().hex[:8]}"
        super().save(*args, **kwargs)
    
    def get_amount_paid(self):
        result = self.invoice_payments.aggregate(total=Sum('amount_applied'))
        return result['total'] or 0
    
    def get_remaining_balance(self):
        """Calculate remaining balance"""
        return self.amount - self.get_amount_paid()
    
    def update_status(self):
        """Update invoice status based on payments"""
        remaining = self.get_remaining_balance()
        if remaining <= 0:
            self.status = 'Paid'
        elif remaining < self.amount:
            self.status = 'Partially Paid'
        else:
            self.status = 'Unpaid'
        self.save()


class InvoicePayment(models.Model):
    """Track payments applied to invoices (supports partial payments)"""
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='invoice_payments')
    payment = models.ForeignKey(Payment, on_delete=models.CASCADE, related_name='invoice_attachments')
    amount_applied = models.DecimalField(max_digits=10, decimal_places=2)  # Amount of payment used for this invoice
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('invoice', 'payment')
    
    def __str__(self):
        return f"{self.invoice.invoice_number} - {self.amount_applied}"