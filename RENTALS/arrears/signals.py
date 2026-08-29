import threading

from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from django.db import transaction

from invoices.models import Invoice, InvoicePayment
from payments.models import Payment
from .views import sync_user_arrears


_skip_arrears_sync = threading.local()


def should_skip_arrears_sync():
    return getattr(_skip_arrears_sync, 'active', False)


def set_skip_arrears_sync(active):
    _skip_arrears_sync.active = active


@receiver(pre_save, sender=Invoice)
def _cache_invoice_old_values(sender, instance, **kwargs):
    if instance.pk:
        try:
            old = Invoice.objects.get(pk=instance.pk)
            instance._old_status = old.status
            instance._old_due_date = old.due_date
        except Invoice.DoesNotExist:
            pass


@receiver(post_save, sender=Invoice)
def _sync_arrears_on_invoice_save(sender, instance, created, **kwargs):
    if should_skip_arrears_sync():
        return
    if created or getattr(instance, '_old_status', None) != instance.status or getattr(instance, '_old_due_date', None) != instance.due_date:
        if instance.user:
            transaction.on_commit(lambda: sync_user_arrears(instance.user, tenant=instance.tenant))


@receiver(post_save, sender=InvoicePayment)
def _sync_arrears_on_invoice_payment_save(sender, instance, created, **kwargs):
    if should_skip_arrears_sync():
        return
    if instance.invoice and instance.invoice.user:
        transaction.on_commit(lambda: sync_user_arrears(instance.invoice.user, tenant=instance.invoice.tenant))


@receiver(pre_save, sender=Payment)
def _cache_payment_old_values(sender, instance, **kwargs):
    if instance.pk:
        try:
            old = Payment.objects.get(pk=instance.pk)
            instance._old_balance = old.balance
        except Payment.DoesNotExist:
            pass


@receiver(post_save, sender=Payment)
def _sync_arrears_on_payment_save(sender, instance, created, **kwargs):
    if should_skip_arrears_sync():
        return
    if created or getattr(instance, '_old_balance', None) != instance.balance:
        if instance.user:
            transaction.on_commit(lambda: sync_user_arrears(instance.user, tenant=instance.tenant))
