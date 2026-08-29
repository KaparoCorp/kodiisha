from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

# Create your models here.
from properties.models import Property
from units.models import Unit
from tenants.models import Tenant

class WaterBill(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)
    previous_reading = models.IntegerField()
    current_reading = models.IntegerField()
    consumption = models.IntegerField(editable=False)
    rate = models.DecimalField(max_digits=10, decimal_places=2)
    amount = models.DecimalField(max_digits=12, decimal_places=2, editable=False)
    due_date = models.DateField()
    status = models.CharField(max_length=10, default='Unpaid')
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        self.consumption = self.current_reading - self.previous_reading
        self.amount = self.consumption * self.rate
        super().save(*args, **kwargs)

    def get_amount_paid(self):
        allocations = self.payment_allocations.all()
        return sum(allocation.amount_applied for allocation in allocations)

    def get_remaining_balance(self):
        return self.amount - self.get_amount_paid()

    def update_status(self):
        self.status = 'Paid' if self.get_remaining_balance() <= 0 else 'Unpaid'
        self.save(update_fields=['status'])


class WaterBillPayment(models.Model):
    STATUS_CHOICES = [
        ('claimed', 'Claimed'),
        ('unclaimed', 'Unclaimed'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='water_bill_payments')
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE, related_name='water_bill_payments')
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='water_bill_payments')
    code = models.CharField(max_length=50, blank=True, null=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    description = models.TextField(blank=True, null=True)
    date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='unclaimed')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.pk and self.balance == 0:
            self.balance = self.amount
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.tenant.first_name} {self.tenant.last_name} - {self.amount}"


class WaterBillPaymentAllocation(models.Model):
    water_bill = models.ForeignKey(WaterBill, on_delete=models.CASCADE, related_name='payment_allocations')
    payment = models.ForeignKey(WaterBillPayment, on_delete=models.CASCADE, related_name='allocations')
    amount_applied = models.DecimalField(max_digits=12, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('water_bill', 'payment')

    def __str__(self):
        return f"Water bill {self.water_bill_id} - {self.amount_applied}"
