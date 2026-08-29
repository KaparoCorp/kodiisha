from datetime import timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Invitation, Profile


class InvitationFlowTests(TestCase):
    def setUp(self):
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='password12345',
        )
        self.admin_user.profile.role = Profile.ADMIN
        self.admin_user.profile.save()

        self.normal_user = User.objects.create_user(
            username='landlord',
            email='landlord@example.com',
            password='password12345',
        )

        from properties.models import Property
        self.admin_property = Property.objects.create(
            user=self.admin_user,
            name='Admin Property',
            address='1 Admin St',
            county='Nairobi',
            total_units=1,
            description='Property for invitation tests',
        )

    def test_admin_can_create_invites_for_each_role(self):
        self.client.login(username='admin', password='password12345')

        for role, _label in Profile.ROLE_CHOICES:
            email = f'invite-{role}@example.com'
            response = self.client.post(reverse('accounts:invitations'), {
                'email': email,
                'first_name': role.title(),
                'last_name': 'User',
                'role': role,
                'properties': [self.admin_property.id],
            })

            self.assertEqual(response.status_code, 200)
            invite = Invitation.objects.get(email=email)
            self.assertEqual(invite.role, role)
            self.assertEqual(invite.invited_by, self.admin_user)
            self.assertContains(response, str(invite.token))

    def test_non_admin_cannot_access_invitation_page(self):
        self.client.login(username='landlord', password='password12345')

        response = self.client.get(reverse('accounts:invitations'))

        self.assertEqual(response.status_code, 302)
        self.assertFalse(Invitation.objects.exists())

    def test_accepting_invite_creates_user_with_invited_role(self):
        invitation = Invitation.objects.create(
            email='newadmin@example.com',
            first_name='New',
            last_name='Admin',
            role=Profile.ADMIN,
            invited_by=self.admin_user,
            expires_at=timezone.now() + timedelta(days=7),
        )

        response = self.client.post(reverse('accounts:accept_invitation', args=[invitation.token]), {
            'username': 'newadmin',
            'first_name': 'New',
            'last_name': 'Admin',
            'password1': 'strong-password-123',
            'password2': 'strong-password-123',
        })

        self.assertEqual(response.status_code, 302)
        user = User.objects.get(username='newadmin')
        self.assertEqual(user.email, 'newadmin@example.com')
        self.assertEqual(user.profile.role, Profile.ADMIN)
        invitation.refresh_from_db()
        self.assertEqual(invitation.status, Invitation.ACCEPTED)
        self.assertIsNotNone(invitation.accepted_at)

    def test_accepted_invite_cannot_be_reused(self):
        invitation = Invitation.objects.create(
            email='accepted@example.com',
            role=Profile.CARETAKER,
            invited_by=self.admin_user,
            expires_at=timezone.now() + timedelta(days=7),
            status=Invitation.ACCEPTED,
            accepted_at=timezone.now(),
        )

        response = self.client.get(reverse('accounts:accept_invitation', args=[invitation.token]))

        self.assertEqual(response.status_code, 410)

    def test_expired_invite_cannot_be_accepted(self):
        invitation = Invitation.objects.create(
            email='expired@example.com',
            role=Profile.BOOKKEEPER,
            invited_by=self.admin_user,
            expires_at=timezone.now() - timedelta(days=1),
        )

        response = self.client.get(reverse('accounts:accept_invitation', args=[invitation.token]))

        self.assertEqual(response.status_code, 410)
        invitation.refresh_from_db()
        self.assertEqual(invitation.status, Invitation.EXPIRED)

    def test_public_registration_can_choose_role(self):
        response = self.client.post(reverse('accounts:register'), {
            'username': 'public-user',
            'first_name': 'Public',
            'last_name': 'User',
            'email': 'public@example.com',
            'password1': 'strong-password-123',
            'password2': 'strong-password-123',
            'role': Profile.ADMIN,
        })

        self.assertEqual(response.status_code, 302)
        user = User.objects.get(username='public-user')
        self.assertEqual(user.profile.role, Profile.ADMIN)

    def test_profile_settings_cannot_change_own_role(self):
        self.client.login(username='landlord', password='password12345')

        response = self.client.post(reverse('accounts:profile_settings'), {
            'first_name': 'Changed',
            'last_name': 'User',
            'email': 'landlord@example.com',
            'phone_number': '123456789',
            'notification_enabled': 'on',
            'role': Profile.ADMIN,
        })

        self.assertEqual(response.status_code, 302)
        self.normal_user.refresh_from_db()
        self.assertEqual(self.normal_user.profile.role, Profile.LANDLORD)
