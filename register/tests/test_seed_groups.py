import io
from django.test import TestCase
from django.core.management import call_command
from django.contrib.auth.models import Group


class SeedGroupsTestCase(TestCase):
    def test_seed_groups_command(self):
        out = io.StringIO()
        call_command('seed_groups', stdout=out)

        admin = Group.objects.get(name='Admin')
        accounts = Group.objects.get(name='Accounts')
        data_entry = Group.objects.get(name='Data Entry')
        viewer = Group.objects.get(name='Viewer')

        # Admin has all permissions on register models
        self.assertGreater(admin.permissions.count(), 30)

        # Accounts has add, change, view but NO delete
        accounts_delete_perms = accounts.permissions.filter(codename__startswith='delete_')
        self.assertEqual(accounts_delete_perms.count(), 0)
        self.assertTrue(accounts.permissions.filter(codename='add_trip').exists())
        self.assertTrue(accounts.permissions.filter(codename='add_receipt').exists())
        self.assertTrue(accounts.permissions.filter(codename='add_ownerpayment').exists())

        # Data Entry has trip and document perms, but NO receipt, NO ownerpayment, NO delete
        data_entry_delete_perms = data_entry.permissions.filter(codename__startswith='delete_')
        self.assertEqual(data_entry_delete_perms.count(), 0)
        self.assertTrue(data_entry.permissions.filter(codename='add_trip').exists())
        self.assertFalse(data_entry.permissions.filter(codename='add_receipt').exists())
        self.assertFalse(data_entry.permissions.filter(codename='add_ownerpayment').exists())

        # Viewer has view only
        viewer_non_view = viewer.permissions.exclude(codename__startswith='view_')
        self.assertEqual(viewer_non_view.count(), 0)
        self.assertTrue(viewer.permissions.filter(codename='view_trip').exists())

        # Idempotent re-run
        call_command('seed_groups', stdout=out)
        self.assertEqual(Group.objects.count(), 4)
