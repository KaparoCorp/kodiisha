import uuid

from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone


class Profile(models.Model):
    # Role Choices
    ADMIN = 'admin'
    LANDLORD = 'landlord'
    CARETAKER = 'caretaker'
    BOOKKEEPER = 'bookkeeper'
    
    ROLE_CHOICES = [
        (ADMIN, 'Admin'),
        (LANDLORD, 'Landlord'),
        (CARETAKER, 'Caretaker'),
        (BOOKKEEPER, 'Bookkeeper'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=30, blank=True)
    last_name = models.CharField(max_length=30, blank=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=LANDLORD)
    phone_number = models.CharField(max_length=15, blank=True)
    avatar = models.ImageField(upload_to='avatars/', default='default_avatar.png')
    notification_enabled = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.user.username}'s Profile ({self.get_role_display()})"


class Invitation(models.Model):
    PENDING = 'pending'
    ACCEPTED = 'accepted'
    EXPIRED = 'expired'

    STATUS_CHOICES = [
        (PENDING, 'Pending'),
        (ACCEPTED, 'Accepted'),
        (EXPIRED, 'Expired'),
    ]

    email = models.EmailField()
    first_name = models.CharField(max_length=30, blank=True)
    last_name = models.CharField(max_length=30, blank=True)
    role = models.CharField(max_length=20, choices=Profile.ROLE_CHOICES, default=Profile.LANDLORD)
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    invited_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_invitations')
    accepted_at = models.DateTimeField(blank=True, null=True)
    expires_at = models.DateTimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    properties = models.ManyToManyField('properties.Property', blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.email} ({self.get_role_display()})"

    @property
    def is_expired(self):
        return timezone.now() >= self.expires_at

    def can_accept(self):
        return self.status == self.PENDING and not self.accepted_at and not self.is_expired

    def mark_expired(self):
        if self.status == self.PENDING and self.is_expired:
            self.status = self.EXPIRED
            self.save(update_fields=['status'])


class PropertyAccess(models.Model):
    """Tracks which users have been granted access to which properties."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='property_accesses')
    property = models.ForeignKey('properties.Property', on_delete=models.CASCADE, related_name='granted_accesses')
    granted_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='granted_accesses')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'property')
        verbose_name_plural = 'Property accesses'

    def __str__(self):
        return f"{self.user.username} → {self.property.name}"


class AuditLog(models.Model):
    ACTION_CREATE = 'create'
    ACTION_UPDATE = 'update'
    ACTION_DELETE = 'delete'
    ACTION_CHOICES = [
        (ACTION_CREATE, 'Create'),
        (ACTION_UPDATE, 'Update'),
        (ACTION_DELETE, 'Delete'),
    ]

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, db_index=True)
    action = models.CharField(max_length=10, choices=ACTION_CHOICES, db_index=True)
    model_name = models.CharField(max_length=100, db_index=True)
    object_id = models.CharField(max_length=255)
    object_repr = models.CharField(max_length=255)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    changes = models.JSONField(null=True, blank=True)

    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['model_name', 'object_id']),
            models.Index(fields=['user', 'timestamp']),
        ]

    def __str__(self):
        return f"{self.user} {self.action} {self.model_name} #{self.object_id}"


class DeletedDataArchive(models.Model):
    model_name = models.CharField(max_length=100, db_index=True)
    object_id = models.CharField(max_length=255)
    object_repr = models.CharField(max_length=255)
    serialized_data = models.JSONField()
    deleted_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='deleted_archives')
    deleted_at = models.DateTimeField(auto_now_add=True, db_index=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    audit_log = models.ForeignKey(AuditLog, on_delete=models.SET_NULL, null=True, blank=True, related_name='deleted_data_archive')

    class Meta:
        ordering = ['-deleted_at']
        indexes = [
            models.Index(fields=['model_name', 'object_id']),
            models.Index(fields=['deleted_by', 'deleted_at']),
        ]

    def __str__(self):
        return f"Archive: {self.model_name} #{self.object_id} ({self.deleted_at})"


# Signals to handle profile creation/saving
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()
