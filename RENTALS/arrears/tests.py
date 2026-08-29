from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase, TransactionTestCase
from django.urls import reverse
from django.db import transaction
from django.utils import timezone

from arrears.models import Arrears
from arrears.views import sync_user_arrears, _get_synced_tenant_ids
from invoices.models import Invoice, InvoicePayment
from payments.models import Payment
from properties.models import Property
from tenants.models import Tenant
from units.models import Unit


class ArrearsReportTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='landlord', password='pass')
        self.client.force_login(self.user)
        self.property = Property.objects.create(
            user=self.user,
            name='Green Court',
            address='Main Road',
            county='Nairobi',
            total_units=1,
            description='Test property',
        )
        self.unit = Unit.objects.create(
            user=self.user,
            property=self.property,
            name='A1',
            rent_amount=Decimal('12000.00'),
            status='occupied',
        )
        self.tenant = Tenant.objects.create(
            unit=self.unit,
            first_name='Jane',
            last_name='Doe',
            phone_number='0700000000',
            next_of_kin_phone_number='0711111111',
        )

    def make_invoice(self, status='Unpaid'):
        return Invoice.objects.create(
            user=self.user,
            unit=self.unit,
            tenant=self.tenant,
            amount=Decimal('12000.00'),
            type='Rent',
            due_date=timezone.now().date() - timedelta(days=10),
            status=status,
        )

    def test_report_creates_and_shows_arrears_for_overdue_invoice(self):
        invoice = self.make_invoice()

        response = self.client.get(reverse('arrears:arrears_report'))

        self.assertEqual(response.status_code, 200)
        arrears = Arrears.objects.get(invoice=invoice)
        self.assertEqual(arrears.amount_due, Decimal('12000.00'))
        self.assertEqual(arrears.days_overdue, 10)
        self.assertContains(response, invoice.invoice_number)
        self.assertContains(response, 'Jane Doe')

    def test_report_uses_remaining_invoice_balance(self):
        invoice = self.make_invoice(status='Partially Paid')
        payment = Payment.objects.create(
            user=self.user,
            property=self.property,
            unit=self.unit,
            tenant=self.tenant,
            amount=Decimal('5000.00'),
            balance=Decimal('0.00'),
            date=date.today(),
            status='claimed',
        )
        invoice.invoice_payments.create(payment=payment, amount_applied=Decimal('5000.00'))

        self.client.get(reverse('arrears:arrears_report'))

        arrears = Arrears.objects.get(invoice=invoice)
        self.assertEqual(arrears.amount_due, Decimal('7000.00'))

    def test_report_handles_no_arrears(self):
        response = self.client.get(reverse('arrears:arrears_report'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Rows')
        self.assertContains(response, 'per_page')

    def test_report_resolves_arrears_when_invoice_is_paid(self):
        invoice = self.make_invoice()
        self.client.get(reverse('arrears:arrears_report'))
        invoice.status = 'Paid'
        invoice.save()

        self.client.get(reverse('arrears:arrears_report'))

        arrears = Arrears.objects.get(invoice=invoice)
        self.assertEqual(arrears.status, 'resolved')
        self.assertIsNotNone(arrears.date_resolved)


class TenantScopedSyncTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='landlord', password='pass')
        self.other_user = User.objects.create_user(username='other_landlord', password='pass')
        self.property = Property.objects.create(
            user=self.user,
            name='Green Court',
            address='Main Road',
            county='Nairobi',
            total_units=2,
            description='Test property',
        )
        self.unit_a = Unit.objects.create(
            user=self.user,
            property=self.property,
            name='A1',
            rent_amount=Decimal('12000.00'),
            status='occupied',
        )
        self.unit_b = Unit.objects.create(
            user=self.user,
            property=self.property,
            name='B1',
            rent_amount=Decimal('10000.00'),
            status='occupied',
        )
        self.tenant_a = Tenant.objects.create(
            unit=self.unit_a,
            first_name='Jane',
            last_name='Doe',
            phone_number='0700000000',
            next_of_kin_phone_number='0711111111',
        )
        self.tenant_b = Tenant.objects.create(
            unit=self.unit_b,
            first_name='John',
            last_name='Smith',
            phone_number='0722222222',
            next_of_kin_phone_number='0733333333',
        )

    def make_invoice(self, tenant, status='Unpaid'):
        return Invoice.objects.create(
            user=self.user,
            unit=tenant.unit,
            tenant=tenant,
            amount=Decimal('12000.00'),
            type='Rent',
            due_date=timezone.now().date() - timedelta(days=10),
            status=status,
        )

    def test_tenant_scoped_sync_does_not_affect_other_tenant_arrears(self):
        invoice_a = self.make_invoice(self.tenant_a)
        invoice_b = self.make_invoice(self.tenant_b)

        Arrears.objects.create(
            invoice=invoice_a,
            tenant=self.tenant_a,
            unit=self.unit_a,
            user=self.user,
            amount_due=invoice_a.amount,
            days_overdue=10,
            status='pending',
        )
        arrears_b = Arrears.objects.create(
            invoice=invoice_b,
            tenant=self.tenant_b,
            unit=self.unit_b,
            user=self.user,
            amount_due=invoice_b.amount,
            days_overdue=10,
            status='pending',
        )

        payment = Payment.objects.create(
            user=self.user,
            property=self.property,
            unit=self.unit_a,
            tenant=self.tenant_a,
            amount=Decimal('12000.00'),
            balance=Decimal('0.00'),
            date=date.today(),
            status='claimed',
        )
        InvoicePayment.objects.create(invoice=invoice_a, payment=payment, amount_applied=Decimal('12000.00'))
        invoice_a.status = 'Paid'
        invoice_a.save()

        sync_user_arrears(self.user, tenant=self.tenant_a)

        arrears_a = Arrears.objects.get(invoice=invoice_a)
        arrears_b.refresh_from_db()
        self.assertEqual(arrears_a.status, 'resolved')
        self.assertEqual(arrears_b.status, 'pending')

    def test_same_tenant_sync_is_deduplicated_within_transaction(self):
        invoice = self.make_invoice(self.tenant_a)
        sync_user_arrears(self.user, tenant=self.tenant_a)

        with transaction.atomic():
            sync_user_arrears(self.user, tenant=self.tenant_a)
            sync_user_arrears(self.user, tenant=self.tenant_a)
            arrears = Arrears.objects.get(invoice=invoice)
            self.assertEqual(arrears.status, 'pending')
