from django.db.models.signals import post_save, pre_delete, pre_save
from django.dispatch import receiver
from django.forms.models import model_to_dict
from django.utils import timezone
from django.db import transaction
from django.contrib.auth.models import User
import datetime
from decimal import Decimal

from .models import AuditLog, DeletedDataArchive, Profile
from .audit import get_current_user, get_current_ip

AUDITED_APPS = [
    'properties',
    'units',
    'tenants',
    'maintenance',
    'payments',
    'invoices',
    'leases',
    'water_bills',
    'arrears',
]


def _get_model_label(instance):
    return f"{instance._meta.app_label}.{instance._meta.model_name}"


def _get_changes(instance):
    original = getattr(instance, '_original_state', None)
    if original is None:
        return None
    current = model_to_dict(instance)
    changes = {}
    for field, old_value in original.items():
        new_value = current.get(field)
        if old_value != new_value:
            changes[field] = [str(old_value), str(new_value)]
    return changes or None


def _log_action(action, instance, changes=None, object_repr=None):
    user = get_current_user()
    ip = get_current_ip()
    if action != AuditLog.ACTION_DELETE and not user:
        return

    if object_repr is None:
        object_repr = str(instance)

    def _create():
        AuditLog.objects.create(
            user=user,
            action=action,
            model_name=_get_model_label(instance),
            object_id=str(instance.pk),
            object_repr=object_repr,
            ip_address=ip,
            changes=changes,
        )

    transaction.on_commit(_create)


def _cache_original_state(sender, instance, **kwargs):
    if kwargs.get('raw', False):
        return
    if hasattr(instance, '_original_state'):
        return
    if not instance.pk:
        instance._original_state = {}
        return
    try:
        old_instance = sender.objects.get(pk=instance.pk)
        instance._original_state = model_to_dict(old_instance)
    except sender.DoesNotExist:
        instance._original_state = {}


def _serialize_instance(instance):
    data = model_to_dict(instance)
    meta = instance._meta
    for field in meta.get_fields():
        if field.many_to_one or field.one_to_one:
            if field.auto_created:
                continue
            value = getattr(instance, field.name, None)
            if value is not None:
                try:
                    data[f"{field.name}__str"] = str(value)
                except Exception:
                    data[f"{field.name}__str"] = None
        elif field.many_to_many:
            try:
                values = list(getattr(instance, field.name).all())
                data[field.name] = [str(v) for v in values]
                data[f"{field.name}__pks"] = [v.pk for v in values]
            except Exception:
                data[field.name] = []
                data[f"{field.name}__pks"] = []
        elif field.concrete and not field.auto_created:
            value = data.get(field.name)
            if isinstance(value, (datetime.date, datetime.datetime, datetime.time)):
                data[field.name] = value.isoformat()
            elif isinstance(value, Decimal):
                data[field.name] = str(value)
    return data


def _get_admin_users():
    return User.objects.filter(
        is_superuser=True
    ) | User.objects.filter(
        profile__role=Profile.ADMIN
    )


def _send_deletion_emails(archive):
    from .emails import send_deletion_archive_email
    admin_users = _get_admin_users()
    for admin_user in admin_users:
        try:
            if admin_user.email:
                send_deletion_archive_email(admin_user, archive)
        except Exception:
            pass


def _handle_save(sender, instance, created, **kwargs):
    if kwargs.get('raw', False):
        return
    if created:
        _log_action(AuditLog.ACTION_CREATE, instance)
    else:
        changes = _get_changes(instance)
        if changes:
            _log_action(AuditLog.ACTION_UPDATE, instance, changes=changes)
    if hasattr(instance, '_original_state'):
        del instance._original_state


def _handle_delete(sender, instance, **kwargs):
    serialized_data = _serialize_instance(instance)
    object_repr = str(instance)
    user = get_current_user()
    ip = get_current_ip()

    def _create():
        audit_log = AuditLog.objects.create(
            user=user,
            action=AuditLog.ACTION_DELETE,
            model_name=_get_model_label(instance),
            object_id=str(instance.pk),
            object_repr=object_repr,
            ip_address=ip,
            changes=None,
        )
        archive = DeletedDataArchive.objects.create(
            model_name=_get_model_label(instance),
            object_id=str(instance.pk),
            object_repr=object_repr,
            serialized_data=serialized_data,
            deleted_by=user,
            ip_address=ip,
            audit_log=audit_log,
        )
        transaction.on_commit(lambda: _send_deletion_emails(archive))

    transaction.on_commit(_create)


def connect_audit_signals():
    from django.apps import apps
    for model in apps.get_models():
        if model._meta.app_label not in AUDITED_APPS:
            continue
        if model.__name__ == 'AuditLog':
            continue
        if model.__name__ == 'DeletedDataArchive':
            continue
        pre_save.connect(_cache_original_state, sender=model, weak=False)
        post_save.connect(_handle_save, sender=model, weak=False)
        pre_delete.connect(_handle_delete, sender=model, weak=False)
