from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from invoices.models import Invoice
from django.db.models import Q


class Command(BaseCommand):
    help = 'Check and mark overdue invoices as arrears'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=0,
            help='Number of days to consider as overdue (default: 0, meaning today)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Perform a dry run without making any changes'
        )
        parser.add_argument(
            '--user',
            type=int,
            help='Mark overdue invoices for a specific user ID (if not specified, marks for all users)'
        )

    def handle(self, *args, **options):
        days_overdue = options.get('days', 0)
        dry_run = options.get('dry_run', False)
        user_id = options.get('user', None)

        # Calculate the overdue date
        today = timezone.now().date()
        overdue_date = today - timedelta(days=days_overdue)

        # Query for overdue unpaid and partially paid invoices
        query = Q(
            due_date__lte=overdue_date,
            status__in=['Unpaid', 'Partially Paid']
        )

        if user_id:
            query &= Q(user_id=user_id)

        overdue_invoices = Invoice.objects.filter(query).select_related(
            'tenant', 'unit', 'user'
        ).order_by('due_date')

        count = overdue_invoices.count()

        if count == 0:
            self.stdout.write(
                self.style.SUCCESS('✓ No overdue invoices found.')
            )
            return

        self.stdout.write(
            self.style.WARNING(
                f'Found {count} overdue invoice(s) with due_date on or before {overdue_date}'
            )
        )

        if dry_run:
            self.stdout.write(self.style.WARNING('🔍 DRY RUN MODE - No changes will be made.\n'))
            for invoice in overdue_invoices:
                days_overdue_count = (today - invoice.due_date).days
                self.stdout.write(
                    f'  • Invoice {invoice.invoice_number}: {invoice.tenant.first_name} '
                    f'{invoice.tenant.last_name} - KES {invoice.amount} '
                    f'(Overdue by {days_overdue_count} days, Status: {invoice.status})'
                )
            return

        # Mark invoices as arrears in the Arrears model
        from arrears.models import Arrears

        marked_count = 0
        for invoice in overdue_invoices:
            days_overdue_count = (today - invoice.due_date).days

            # Check if an Arrears record already exists for this invoice
            arrears_record, created = Arrears.objects.get_or_create(
                invoice=invoice,
                defaults={
                    'tenant': invoice.tenant,
                    'unit': invoice.unit,
                    'user': invoice.user,
                    'days_overdue': days_overdue_count,
                    'amount_due': invoice.get_remaining_balance(),
                    'status': 'pending',
                }
            )

            if created:
                marked_count += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✓ Marked as arrears: Invoice {invoice.invoice_number} - '
                        f'{invoice.tenant.first_name} {invoice.tenant.last_name} '
                        f'(KES {invoice.get_remaining_balance()}, {days_overdue_count} days overdue)'
                    )
                )
            else:
                # Update the days_overdue count
                arrears_record.days_overdue = days_overdue_count
                arrears_record.amount_due = invoice.get_remaining_balance()
                arrears_record.save()
                self.stdout.write(
                    self.style.WARNING(
                        f'⚠ Updated arrears record: Invoice {invoice.invoice_number} '
                        f'(Now {days_overdue_count} days overdue)'
                    )
                )

        self.stdout.write(
            self.style.SUCCESS(f'\n✓ Successfully marked {marked_count} new arrears record(s).')
        )
