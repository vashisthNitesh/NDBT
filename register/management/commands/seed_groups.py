from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType

from register.models import (
    LorryOwner,
    Consignor,
    Vehicle,
    Location,
    Trip,
    Receipt,
    ReceiptAllocation,
    OwnerPayment,
    OwnerPaymentAllocation,
    TripDocument,
)


class Command(BaseCommand):
    help = 'Seeds initial user groups (Admin, Accounts, Data Entry, Viewer) with appropriate permissions.'

    def handle(self, *args, **options):
        # All register models
        all_models = [
            LorryOwner,
            Consignor,
            Vehicle,
            Location,
            Trip,
            Receipt,
            ReceiptAllocation,
            OwnerPayment,
            OwnerPaymentAllocation,
            TripDocument,
        ]

        # Content types for register models
        content_types = [ContentType.objects.get_for_model(m) for m in all_models]

        # Fetch permissions
        all_perms = Permission.objects.filter(content_type__in=content_types)

        # 1. Admin Group: All permissions
        admin_group, created = Group.objects.get_or_create(name='Admin')
        admin_group.permissions.set(all_perms)
        self.stdout.write(self.style.SUCCESS(f"{'Created' if created else 'Updated'} group 'Admin' ({admin_group.permissions.count()} perms)"))

        # 2. Accounts Group:
        # Trips, receipts, payments, masters, documents.
        # Can add, change, view. NO delete permissions!
        accounts_group, created = Group.objects.get_or_create(name='Accounts')
        accounts_perms = all_perms.filter(codename__regex=r'^(add|change|view)_')
        accounts_group.permissions.set(accounts_perms)
        self.stdout.write(self.style.SUCCESS(f"{'Created' if created else 'Updated'} group 'Accounts' ({accounts_group.permissions.count()} perms)"))

        # 3. Data Entry Group:
        # Trips, documents, masters. NO receipts or payments. NO delete!
        data_entry_models = [LorryOwner, Consignor, Vehicle, Location, Trip, TripDocument]
        data_entry_cts = [ContentType.objects.get_for_model(m) for m in data_entry_models]
        data_entry_group, created = Group.objects.get_or_create(name='Data Entry')
        data_entry_perms = Permission.objects.filter(
            content_type__in=data_entry_cts,
            codename__regex=r'^(add|change|view)_'
        )
        data_entry_group.permissions.set(data_entry_perms)
        self.stdout.write(self.style.SUCCESS(f"{'Created' if created else 'Updated'} group 'Data Entry' ({data_entry_group.permissions.count()} perms)"))

        # 4. Viewer Group:
        # Read + export. View permissions only across all models.
        viewer_group, created = Group.objects.get_or_create(name='Viewer')
        viewer_perms = all_perms.filter(codename__startswith='view_')
        viewer_group.permissions.set(viewer_perms)
        self.stdout.write(self.style.SUCCESS(f"{'Created' if created else 'Updated'} group 'Viewer' ({viewer_group.permissions.count()} perms)"))

        self.stdout.write(self.style.SUCCESS("All user groups successfully seeded!"))
