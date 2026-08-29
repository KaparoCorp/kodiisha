from django.db import models
from django.contrib.auth.models import User
from tenants.models import Tenant
from units.models import Unit
from django.utils import timezone
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver

class Lease(models.Model):
	user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
	tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='leases')
	unit = models.ForeignKey(Unit, on_delete=models.CASCADE, related_name='leases')
	start_date = models.DateField()
	end_date = models.DateField(blank=True, null=True)
	monthly_rent = models.DecimalField(max_digits=10, decimal_places=2)
	deposit_held = models.DecimalField(max_digits=10, decimal_places=2, default=0)
	is_active = models.BooleanField(default=True)
	created_at = models.DateTimeField(default=timezone.now)
	updated_at = models.DateTimeField(auto_now=True)

	def save(self, *args, **kwargs):
		# Rent snapshotting: only set monthly_rent on creation
		if not self.pk:
			self.monthly_rent = self.unit.rent_amount
		super().save(*args, **kwargs)

	def clean(self):
		# Enforce only one active lease per unit
		if self.is_active:
			active_leases = Lease.objects.filter(unit=self.unit, is_active=True)
			if self.pk:
				active_leases = active_leases.exclude(pk=self.pk)
			if active_leases.exists():
				raise models.ValidationError('A unit cannot have more than one active lease.')

	def __str__(self):
		return f"Lease: {self.tenant} - {self.unit} ({'Active' if self.is_active else 'Inactive'})"

@receiver(post_save, sender=Lease)
def update_unit_status_on_active_lease(sender, instance, **kwargs):
	if instance.is_active:
		instance.unit.status = 'occupied'
		instance.unit.save()
	else:
		# If no other active lease exists for this unit, mark as vacant
		if not Lease.objects.filter(unit=instance.unit, is_active=True).exclude(pk=instance.pk).exists():
			instance.unit.status = 'vacant'
			instance.unit.save()
