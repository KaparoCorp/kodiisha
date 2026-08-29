from datetime import date
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase, TransactionTestCase
from django.urls import reverse

from accounts.models import AuditLog
from invoices.models import Invoice, InvoicePayment
from invoices.services import create_invoices_for_units
from payments.models import Payment
from properties.models import Property
from tenants.models import Tenant
from units.models import Unit


class InvoiceFilterTests(TestCase):
    def setUp(self):
        from accounts.audit import _thread_locals
        if hasattr(_thread_locals, 'request'):
            del _thread_locals.request

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

    def make_invoice(self, amount, due_date):
        return Invoice.objects.create(
            user=self.user,
            unit=self.unit,
            tenant=self.tenant,
            amount=Decimal(amount),
            type='Rent',
            due_date=due_date,
        )

    def test_invoice_list_filters_by_due_date_range(self):
        before = self.make_invoice('1000.00', date(2026, 5, 1))
        in_range = self.make_invoice('2000.00', date(2026, 5, 15))
        after = self.make_invoice('3000.00', date(2026, 6, 1))

        response = self.client.get(reverse('invoices:invoice_list'), {
            'start_date': '2026-05-10',
            'end_date': '2026-05-20',
        })

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, in_range.invoice_number)
        self.assertNotContains(response, before.invoice_number)
        self.assertNotContains(response, after.invoice_number)

    def test_invoice_list_filters_by_unit(self):
        other_unit = Unit.objects.create(
            user=self.user,
            property=self.property,
            name='B2',
            rent_amount=Decimal('15000.00'),
            status='occupied',
        )
        selected_invoice = self.make_invoice('1000.00', date(2026, 5, 1))
        other_invoice = Invoice.objects.create(
            user=self.user,
            unit=other_unit,
            tenant=self.tenant,
            amount=Decimal('2000.00'),
            type='Rent',
            due_date=date(2026, 5, 2),
        )

        response = self.client.get(reverse('invoices:invoice_list'), {'unit': self.unit.id})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, selected_invoice.invoice_number)
        self.assertNotContains(response, other_invoice.invoice_number)

    def test_property_units_endpoint_returns_units_for_owned_property(self):
        Unit.objects.create(
            user=self.user,
            property=self.property,
            name='B2',
            rent_amount=Decimal('15000.00'),
            status='vacant',
        )
        other_user = User.objects.create_user(username='other', password='pass')
        other_property = Property.objects.create(
            user=other_user,
            name='Other Court',
            address='Other Road',
            county='Nairobi',
            total_units=1,
            description='Other property',
        )
        Unit.objects.create(
            user=other_user,
            property=other_property,
            name='C3',
            rent_amount=Decimal('17000.00'),
            status='vacant',
        )

        response = self.client.get(reverse('invoices:property_units', args=[self.property.id]))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            [unit['name'] for unit in response.json()['units']],
            ['A1', 'B2'],
        )

        forbidden_response = self.client.get(reverse('invoices:property_units', args=[other_property.id]))
        self.assertEqual(forbidden_response.status_code, 404)

    def test_single_invoice_generation_creates_invoice_for_selected_unit_only(self):
        other_unit = Unit.objects.create(
            user=self.user,
            property=self.property,
            name='B2',
            rent_amount=Decimal('15000.00'),
            status='occupied',
        )
        Tenant.objects.create(
            unit=other_unit,
            first_name='John',
            last_name='Smith',
            phone_number='0722222222',
            next_of_kin_phone_number='0733333333',
        )

        response = self.client.post(reverse('invoices:invoice_list'), {
            'single_generate': 'true',
            'property': self.property.id,
            'unit': self.unit.id,
            'due_date': '2026-05-01',
            'type': 'Rent',
        })

        self.assertRedirects(response, reverse('invoices:invoice_list'))
        invoices = Invoice.objects.all()
        self.assertEqual(invoices.count(), 1)
        invoice = invoices.get()
        self.assertEqual(invoice.unit, self.unit)
        self.assertEqual(invoice.tenant, self.tenant)
        self.assertEqual(invoice.amount, self.unit.rent_amount)

    def test_bulk_invoice_creation_helper_creates_multiple_invoices(self):
        other_unit = Unit.objects.create(
            user=self.user,
            property=self.property,
            name='B2',
            rent_amount=Decimal('15000.00'),
            status='occupied',
        )
        Tenant.objects.create(
            unit=other_unit,
            first_name='John',
            last_name='Smith',
            phone_number='0722222222',
            next_of_kin_phone_number='0733333333',
        )

        created_invoices = create_invoices_for_units(
            self.user,
            [self.unit, other_unit],
            date(2026, 5, 1),
            inv_type='Rent',
            apply_existing_credit=False,
        )

        self.assertEqual(len(created_invoices), 2)
        self.assertEqual(Invoice.objects.count(), 2)
        self.assertEqual({invoice.unit_id for invoice in created_invoices}, {self.unit.id, other_unit.id})
        self.assertTrue(all(invoice.status == 'Unpaid' for invoice in created_invoices))
        self.assertTrue(all(invoice.invoice_number.startswith('INV-202605-') for invoice in created_invoices))

    def test_single_invoice_generation_rejects_invalid_due_date(self):
        response = self.client.post(reverse('invoices:invoice_list'), {
            'single_generate': 'true',
            'property': self.property.id,
            'unit': self.unit.id,
            'due_date': 'not-a-date',
            'type': 'Rent',
        })

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Please enter a valid due date in YYYY-MM-DD format')
        self.assertEqual(Invoice.objects.count(), 0)

    def test_single_invoice_generation_rejects_unit_from_different_property(self):
        other_property = Property.objects.create(
            user=self.user,
            name='Blue Court',
            address='Side Road',
            county='Nairobi',
            total_units=1,
            description='Other owned property',
        )
        other_unit = Unit.objects.create(
            user=self.user,
            property=other_property,
            name='C3',
            rent_amount=Decimal('17000.00'),
            status='occupied',
        )

        response = self.client.post(reverse('invoices:invoice_list'), {
            'single_generate': 'true',
            'property': self.property.id,
            'unit': other_unit.id,
            'due_date': '2026-05-01',
            'type': 'Rent',
        })

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Selected unit does not belong to the selected property')
        self.assertEqual(Invoice.objects.count(), 0)


class InvoiceDeleteAuditRegressionTests(TransactionTestCase):
    def setUp(self):
        from accounts.audit import _thread_locals
        if hasattr(_thread_locals, 'request'):
            del _thread_locals.request

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

    def _make_invoice(self, amount, due_date):
        return Invoice.objects.create(
            user=self.user,
            unit=self.unit,
            tenant=self.tenant,
            amount=Decimal(amount),
            type='Rent',
            due_date=due_date,
        )

    def test_deleting_invoice_with_payment_records_audit_log_without_error(self):
        """Regression: the audit ``pre_delete`` handler must capture an
        InvoicePayment's string repr *eagerly* (at pre_delete time, while the
        related Invoice still exists).  The actual AuditLog row is written from
        a ``transaction.on_commit`` callback, which runs *after* the Invoice
        (and its InvoicePayments) have been deleted.  Lazily evaluating
        ``str(instance)`` there would re-fetch the now-gone Invoice via the FK
        descriptor and raise ``Invoice.DoesNotExist`` (HTTP 500 on
        ``POST /invoices/delete/``)."""
        invoice = self._make_invoice('5000.00', date(2026, 1, 1))
        payment = Payment.objects.create(
            user=self.user,
            property=self.property,
            unit=self.unit,
            tenant=self.tenant,
            code='P1',
            amount=Decimal('5000.00'),
            date=date.today(),
        )
        InvoicePayment.objects.create(
            invoice=invoice,
            payment=payment,
            amount_applied=Decimal('5000.00'),
        )

        url = reverse('invoices:delete_invoices')
        response = self.client.post(url, {'invoice_ids[]': [invoice.id]})

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['success'], response.json().get('message'))

        # With TransactionTestCase the view's ``with transaction.atomic()`` block
        # commits on exit, so the audit ``on_commit`` callbacks run synchronously
        # during the request -- exactly like production.  Before the fix the audit
        # ``_create`` evaluated ``str(instance)`` here, after the Invoice (and its
        # InvoicePayments) were deleted, raising ``Invoice.DoesNotExist``.
        self.assertFalse(Invoice.objects.filter(id=invoice.id).exists())
        self.assertTrue(
            AuditLog.objects.filter(
                model_name='invoices.invoicepayment',
                action=AuditLog.ACTION_DELETE,
            ).exists()
        )
