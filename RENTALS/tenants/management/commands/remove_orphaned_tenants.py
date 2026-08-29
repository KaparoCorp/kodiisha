from django.core.management.base import BaseCommand
from tenants.models import Tenant


class Command(BaseCommand):
    help = 'Remove tenants that do not have any unit attached'

    def handle(self, *args, **options):
        orphaned = Tenant.objects.filter(unit__isnull=True)
        count = orphaned.count()
        if count == 0:
            self.stdout.write(self.style.NOTICE('No orphaned tenants found.'))
            return
        self.stdout.write(f'Found {count} orphaned tenant(s) to remove.')
        deleted, _ = orphaned.delete()
        self.stdout.write(self.style.SUCCESS(f'Removed {deleted} orphaned tenant(s).'))