from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
import pprint

from .models import DeletedDataArchive


def send_deletion_archive_email(admin_user, archive):
    if not getattr(settings, 'EMAIL_HOST', ''):
        return
    subject = f"[PROPATIA] Data Deletion Archive: {archive.model_name} #{archive.object_id}"
    context = {
        'archive': archive,
        'admin_user': admin_user,
        'site_name': 'PROPATIA',
        'admin_url': '/admin/accounts/deleteddataarchive/',
        'serialized_data_pprint': pprint.pformat(archive.serialized_data, width=120),
    }
    html_body = render_to_string('accounts/emails/deletion_archive.html', context)
    text_body = strip_tags(html_body)
    email = EmailMultiAlternatives(
        subject=subject,
        body=text_body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[admin_user.email],
    )
    email.attach_alternative(html_body, 'text/html')
    email.send()


def send_invitation_email(invitation, accept_url):
    if not getattr(settings, 'EMAIL_HOST', ''):
        return
    subject = "You're invited to join PROPATIA"
    context = {
        'invitation': invitation,
        'accept_url': accept_url,
        'site_name': 'PROPATIA',
    }
    html_body = render_to_string('accounts/emails/invitation.html', context)
    text_body = strip_tags(html_body)
    email = EmailMultiAlternatives(
        subject=subject,
        body=text_body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[invitation.email],
    )
    email.attach_alternative(html_body, 'text/html')
    email.send()
