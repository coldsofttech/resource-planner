from django.test import SimpleTestCase

from apps.permissions.models import PermissionCategory

# ── PermissionCategory.__str__ ────────────────────────────────────────────────


class PermissionCategoryStrTest(SimpleTestCase):
    def test_str_returns_label(self):
        cat = PermissionCategory(label="View Projects")
        self.assertEqual(str(cat), "View Projects")

    def test_str_with_different_label(self):
        cat = PermissionCategory(label="Manage Teams")
        self.assertEqual(str(cat), "Manage Teams")

    def test_str_with_empty_label(self):
        cat = PermissionCategory(label="")
        self.assertEqual(str(cat), "")
