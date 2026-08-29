from datetime import date
from decimal import Decimal
from io import BytesIO, StringIO
import csv

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from openpyxl import Workbook

from invoices.models import Invoice, InvoicePayment
from invoices.services import allocate_payment_to_rent_invoices
from leases.models import Lease
from payments.models import Payment
from properties.models import Property
from tenants.models import Tenant
from units.models import Unit
from arrears.models import Arrears
from arrears.views import sync_user_arrears


class UploadPaymentsTests(TestCase):
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
        Lease.objects.create(
            user=self.user,
            tenant=self.tenant,
            unit=self.unit,
            start_date=date(2026, 1, 1),
            monthly_rent=self.unit.rent_amount,
            is_active=True,
        )

    def make_upload(self, rows, headers=None):
        workbook = Workbook()
        sheet = workbook.active
        sheet.append(headers or ['property', 'house number', 'paid in date', 'code', 'details', 'amount'])
        for row in rows:
            sheet.append(row)
        stream = BytesIO()
        workbook.save(stream)
        stream.seek(0)
        return SimpleUploadedFile(
            'payments.xlsx',
            stream.read(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        )

    def make_csv_upload(self, rows, headers=None, delimiter=','):
        headers = headers or ['property', 'house number', 'paid in date', 'code', 'details', 'amount']
        stream = StringIO()
        writer = csv.writer(stream, delimiter=delimiter)
        writer.writerow(headers)
        for row in rows:
            writer.writerow(row)
        return SimpleUploadedFile(
            'payments.csv',
            stream.getvalue().encode('utf-8'),
            content_type='text/csv',
        )

    def upload(self, rows, headers=None):
        return self.client.post(reverse('payments:upload_payments'), {'file': self.make_upload(rows, headers)})

    def validate_upload(self, rows, headers=None):
        return self.client.post(reverse('payments:upload_payments'), {
            'file': self.make_upload(rows, headers),
            'validate_only': '1',
        })

    def upload_csv(self, rows, headers=None, delimiter=','):
        return self.client.post(reverse('payments:upload_payments'), {
            'file': self.make_csv_upload(rows, headers, delimiter),
        })

    def test_upload_matches_property_and_house_number_to_active_lease_tenant(self):
        response = self.upload([
            ['Green Court', 'A1', '2026-05-10', 'RCT', 'May rent deposit', '5000.00'],
        ])

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['count'], 1)

        payment = Payment.objects.get()
        self.assertEqual(payment.property, self.property)
        self.assertEqual(payment.unit, self.unit)
        self.assertEqual(payment.tenant, self.tenant)
        self.assertEqual(payment.code, 'RCT')
        self.assertEqual(payment.amount, Decimal('5000.00'))
        self.assertEqual(payment.balance, Decimal('5000.00'))
        self.assertEqual(payment.date, date(2026, 5, 10))
        self.assertEqual(payment.description, 'May rent deposit')
        self.assertEqual(payment.status, 'unclaimed')
        self.assertEqual(InvoicePayment.objects.count(), 0)

    def test_validate_upload_does_not_create_payments(self):
        response = self.validate_upload([
            ['Green Court', 'A1', '2026-05-10', 'RCT', 'May rent deposit', '5000.00'],
        ])

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['valid_rows'], 1)
        self.assertEqual(data['invalid_rows'], 0)
        self.assertEqual(Payment.objects.count(), 0)

    def test_upload_accepts_legacy_house_numner_header(self):
        response = self.upload(
            [
                ['Green Court', 'A1', '01-05-2026', 'RCT', '', '8,000.00'],
            ],
            headers=['PROPERTY', 'HOUSE_NUMNER', 'DATE', 'CODE', 'DETAILS', 'AMOUNT'],
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['count'], 1)

        payment = Payment.objects.get()
        self.assertEqual(payment.tenant, self.tenant)
        self.assertEqual(payment.unit, self.unit)
        self.assertEqual(payment.code, 'RCT')
        self.assertEqual(payment.amount, Decimal('8000.00'))
        self.assertEqual(payment.balance, Decimal('8000.00'))
        self.assertEqual(payment.date, date(2026, 5, 1))
        self.assertEqual(payment.description, '')

    def test_upload_matches_required_headers_regardless_of_case(self):
        response = self.upload(
            [
                ['Green Court', 'A1', '01-05-2026', 'RCT', 'Mixed case headers', '8000.00'],
            ],
            headers=['property', 'House_Number', 'Date', 'cOdE', 'details', 'amount'],
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'], data)
        self.assertEqual(data['count'], 1)

        payment = Payment.objects.get()
        self.assertEqual(payment.property, self.property)
        self.assertEqual(payment.unit, self.unit)
        self.assertEqual(payment.tenant, self.tenant)
        self.assertEqual(payment.code, 'RCT')
        self.assertEqual(payment.amount, Decimal('8000.00'))
        self.assertEqual(payment.date, date(2026, 5, 1))
        self.assertEqual(payment.description, 'Mixed case headers')

    def test_upload_accepts_tab_csv_with_house_number_and_ksh_amount(self):
        response = self.upload_csv(
            [
                ['Green Court', 'A1', '01-02-2026', 'YMO', 'Merchant Payment Online', 'Ksh9,200.00'],
            ],
            headers=['**PROPERTY**', '**HOUSE_NUMBER**', '**DATE**', '**CODE**', '**DETAILS**', '**AMOUNT**'],
            delimiter='\t',
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'], data)
        self.assertEqual(data['count'], 1)

        payment = Payment.objects.get()
        self.assertEqual(payment.property, self.property)
        self.assertEqual(payment.unit, self.unit)
        self.assertEqual(payment.tenant, self.tenant)
        self.assertEqual(payment.code, 'YMO')
        self.assertEqual(payment.amount, Decimal('9200.00'))
        self.assertEqual(payment.balance, Decimal('9200.00'))
        self.assertEqual(payment.date, date(2026, 2, 1))
        self.assertEqual(payment.description, 'Merchant Payment Online')

    def test_upload_accepts_csv_with_repeated_header_groups(self):
        blank_columns = [''] * 6
        headers = (
            ['PROPERTY', 'HOUSE_NUMBER', 'DATE', 'CODE', 'DETAILS', 'AMOUNT']
            + blank_columns
            + ['PROPERTY', 'House_NUMBER', 'DATE', 'CODE', 'DETAILS', 'AMOUNT']
            + blank_columns
            + ['PROPERTY', 'House_NUMBER', 'DATE', 'CODE', 'DETAILS', 'AMOUNT']
        )
        row = (
            ['Green Court', 'A1', '01-02-2026', 'YMO', 'Duplicate header groups', '9,200.00']
            + ([''] * (len(headers) - 6))
        )

        response = self.upload_csv([row], headers=headers)

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'], data)
        self.assertEqual(data['count'], 1)

        payment = Payment.objects.get()
        self.assertEqual(payment.property, self.property)
        self.assertEqual(payment.unit, self.unit)
        self.assertEqual(payment.tenant, self.tenant)
        self.assertEqual(payment.code, 'YMO')
        self.assertEqual(payment.amount, Decimal('9200.00'))
        self.assertEqual(payment.date, date(2026, 2, 1))
        self.assertEqual(payment.description, 'Duplicate header groups')

    def test_payment_list_filters_by_date_range(self):
        Payment.objects.create(
            user=self.user,
            property=self.property,
            unit=self.unit,
            tenant=self.tenant,
            amount=Decimal('1000.00'),
            date=date(2026, 5, 1),
            description='Before range',
        )
        in_range_payment = Payment.objects.create(
            user=self.user,
            property=self.property,
            unit=self.unit,
            tenant=self.tenant,
            amount=Decimal('2000.00'),
            date=date(2026, 5, 15),
            description='In range',
        )
        Payment.objects.create(
            user=self.user,
            property=self.property,
            unit=self.unit,
            tenant=self.tenant,
            amount=Decimal('3000.00'),
            date=date(2026, 6, 1),
            description='After range',
        )

        response = self.client.get(reverse('payments:payment_list'), {
            'start_date': '2026-05-10',
            'end_date': '2026-05-20',
        })

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, in_range_payment.description)
        self.assertNotContains(response, 'Before range')
        self.assertNotContains(response, 'After range')

    def test_manual_payment_matches_property_and_unit_to_active_lease_tenant(self):
        response = self.client.post(reverse('payments:payment_list'), {
            'property': self.property.id,
            'unit': self.unit.id,
            'code': '2CX',
            'amount': '8000.00',
            'description': '',
            'date': '2026-05-02',
        })

        self.assertEqual(response.status_code, 302)
        payment = Payment.objects.get()
        self.assertEqual(payment.property, self.property)
        self.assertEqual(payment.unit, self.unit)
        self.assertEqual(payment.tenant, self.tenant)
        self.assertEqual(payment.code, '2CX')
        self.assertEqual(payment.amount, Decimal('8000.00'))
        self.assertEqual(payment.status, 'unclaimed')

    def test_manual_payment_allocates_to_open_rent_invoice(self):
        """Regression: when an open rent invoice exists, creating a payment must
        allocate against it successfully instead of crashing. Previously the
        synchronous arrears sync (fired by post_save signals inside the
        select_for_update allocation transaction) could raise a non-ValueError
        that escaped ``except ValueError`` -> HTTP 500 and an orphaned payment.
        """
        Invoice.objects.create(
            user=self.user,
            unit=self.unit,
            tenant=self.tenant,
            amount=Decimal('12000.00'),
            type='Rent',
            due_date=date(2026, 4, 1),
            status='Unpaid',
        )

        response = self.client.post(reverse('payments:payment_list'), {
            'property': self.property.id,
            'unit': self.unit.id,
            'code': 'RC1',
            'amount': '8000.00',
            'description': 'Mid-month rent',
            'date': '2026-05-02',
        })

        # No 500; payment is created AND allocated atomically.
        self.assertEqual(response.status_code, 302)
        payment = Payment.objects.get()
        # Payment (KES 8,000) fully covers its share of the KES 12,000 invoice.
        self.assertEqual(payment.balance, Decimal('0.00'))      # 8000 - 8000
        self.assertEqual(payment.status, 'claimed')              # balance fully consumed

        self.assertEqual(InvoicePayment.objects.count(), 1)
        allocation = InvoicePayment.objects.first()
        self.assertEqual(allocation.amount_applied, Decimal('8000.00'))

        invoice = Invoice.objects.get()
        self.assertEqual(invoice.status, 'Partially Paid')      # 12000 - 8000 = 4000 still owed
        self.assertEqual(invoice.get_remaining_balance(), Decimal('4000.00'))

    def test_upload_rejects_unit_without_active_lease(self):
        Lease.objects.update(is_active=False)

        response = self.upload([
            ['Green Court', 'A1', '2026-05-10', 'RCT', 'May rent deposit', '5000.00'],
        ])

        data = response.json()
        self.assertFalse(data['success'])
        self.assertEqual(data['count'], 0)
        self.assertEqual(Payment.objects.count(), 0)
        self.assertIn('No active tenant found', data['errors'][0])

    def test_upload_skips_duplicate_payment(self):
        row = ['Green Court', 'A1', '2026-05-10', 'RCT', 'May rent deposit', '5000.00']
        first_response = self.upload([row])
        second_response = self.upload([row])

        self.assertTrue(first_response.json()['success'])
        second_data = second_response.json()
        self.assertTrue(second_data['success'])
        self.assertEqual(second_data['count'], 0)
        self.assertEqual(Payment.objects.count(), 1)
        self.assertIn('Duplicate payment skipped', second_data['duplicates'][0])

    def test_auto_attached_payment_fully_covers_overdue_invoice_resolves_arrears(self):
        invoice = Invoice.objects.create(
            user=self.user,
            unit=self.unit,
            tenant=self.tenant,
            amount=Decimal('12000.00'),
            type='Rent',
            due_date=date(2026, 4, 1),
            status='Unpaid',
        )

        self.client.get(reverse('arrears:arrears_report'))
        arrears = Arrears.objects.get(invoice=invoice)
        self.assertEqual(arrears.status, 'pending')

        response = self.client.post(reverse('payments:payment_list'), {
            'property': self.property.id,
            'unit': self.unit.id,
            'code': 'RC1',
            'amount': '12000.00',
            'description': 'Full rent payment',
            'date': '2026-05-02',
        })
        self.assertEqual(response.status_code, 302)

        sync_user_arrears(self.user)

        arrears = Arrears.objects.get(invoice=invoice)
        self.assertEqual(arrears.status, 'resolved')
        self.assertIsNotNone(arrears.date_resolved)

    def test_auto_attached_payment_partially_covers_overdue_invoice_reduces_arrears(self):
        invoice = Invoice.objects.create(
            user=self.user,
            unit=self.unit,
            tenant=self.tenant,
            amount=Decimal('12000.00'),
            type='Rent',
            due_date=date(2026, 4, 1),
            status='Unpaid',
        )

        self.client.get(reverse('arrears:arrears_report'))
        arrears = Arrears.objects.get(invoice=invoice)
        self.assertEqual(arrears.status, 'pending')

        response = self.client.post(reverse('payments:payment_list'), {
            'property': self.property.id,
            'unit': self.unit.id,
            'code': 'RC1',
            'amount': '5000.00',
            'description': 'Partial rent payment',
            'date': '2026-05-02',
        })
        self.assertEqual(response.status_code, 302)

        sync_user_arrears(self.user)

        arrears = Arrears.objects.get(invoice=invoice)
        self.assertEqual(arrears.status, 'pending')
        self.assertEqual(arrears.amount_due, Decimal('7000.00'))

    def test_auto_attached_payment_with_excess_keeps_credit_and_resolves_arrears(self):
        invoice = Invoice.objects.create(
            user=self.user,
            unit=self.unit,
            tenant=self.tenant,
            amount=Decimal('5000.00'),
            type='Rent',
            due_date=date(2026, 4, 1),
            status='Unpaid',
        )

        self.client.get(reverse('arrears:arrears_report'))
        arrears = Arrears.objects.get(invoice=invoice)
        self.assertEqual(arrears.status, 'pending')

        response = self.client.post(reverse('payments:payment_list'), {
            'property': self.property.id,
            'unit': self.unit.id,
            'code': 'RC1',
            'amount': '8000.00',
            'description': 'Overpayment',
            'date': '2026-05-02',
        })
        self.assertEqual(response.status_code, 302)

        payment = Payment.objects.get()
        self.assertEqual(payment.balance, Decimal('3000.00'))
        self.assertEqual(payment.status, 'unclaimed')

        sync_user_arrears(self.user)

        arrears = Arrears.objects.get(invoice=invoice)
        self.assertEqual(arrears.status, 'resolved')
