from unittest.mock import MagicMock

from django.test import SimpleTestCase

from apps.permissions.backends import PermissionCategoryBackend
from apps.permissions.constants import PermissionScope

# ── authenticate ──────────────────────────────────────────────────────────────


class PermissionCategoryBackendAuthenticateTest(SimpleTestCase):
    def setUp(self):
        self.backend = PermissionCategoryBackend()

    def test_returns_none_always(self):
        result = self.backend.authenticate(request=None, username="any", password="any")
        self.assertIsNone(result)

    def test_returns_none_with_no_credentials(self):
        result = self.backend.authenticate(request=None)
        self.assertIsNone(result)

    def test_returns_none_regardless_of_credentials(self):
        for username, password in [("admin", "pass"), ("", ""), ("x", None)]:
            with self.subTest(username=username):
                self.assertIsNone(
                    self.backend.authenticate(
                        request=None, username=username, password=password
                    )
                )


# ── _scope_covers_object ──────────────────────────────────────────────────────


class PermissionCategoryBackendScopeCoverageTest(SimpleTestCase):
    def setUp(self):
        self.backend = PermissionCategoryBackend()
        self.user = MagicMock()
        self.user.pk = 42

    def test_all_scope_grants_access_to_any_object(self):
        obj = MagicMock()
        self.assertTrue(
            self.backend._scope_covers_object(self.user, PermissionScope.ALL, obj)
        )

    def test_none_scope_denies_access_to_any_object(self):
        obj = MagicMock()
        self.assertFalse(
            self.backend._scope_covers_object(self.user, PermissionScope.NONE, obj)
        )

    def test_self_scope_grants_access_to_owned_object(self):
        obj = MagicMock()
        obj.created_by_id = 42
        self.assertTrue(
            self.backend._scope_covers_object(self.user, PermissionScope.SELF, obj)
        )

    def test_self_scope_denies_access_to_unowned_object(self):
        obj = MagicMock()
        obj.created_by_id = 99
        self.assertFalse(
            self.backend._scope_covers_object(self.user, PermissionScope.SELF, obj)
        )

    def test_self_scope_denies_when_object_has_no_created_by_id(self):
        self.assertFalse(
            self.backend._scope_covers_object(self.user, PermissionScope.SELF, object())
        )

    def test_team_scope_grants_access_when_user_is_team_member(self):
        team = MagicMock()
        team.members.filter.return_value.exists.return_value = True
        obj = MagicMock()
        obj.team = team
        self.assertTrue(
            self.backend._scope_covers_object(self.user, PermissionScope.TEAM, obj)
        )

    def test_team_scope_denies_access_when_user_is_not_team_member(self):
        team = MagicMock()
        team.members.filter.return_value.exists.return_value = False
        obj = MagicMock()
        obj.team = team
        self.assertFalse(
            self.backend._scope_covers_object(self.user, PermissionScope.TEAM, obj)
        )

    def test_team_scope_denies_when_object_has_no_team_attribute(self):
        self.assertFalse(
            self.backend._scope_covers_object(self.user, PermissionScope.TEAM, object())
        )
