from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase

from apps.users.services import AdminUserService, BaseUserService, SSOUserService

# ---------------------------------------------------------------------------
# BaseUserService._assign_default_group
# ---------------------------------------------------------------------------


class AssignDefaultGroupTest(SimpleTestCase):
    def setUp(self):
        self.svc = BaseUserService()

    @patch("apps.users.services.get_administrators_group")
    @patch("apps.users.services.get_guests_group")
    def test_uses_administrators_group_when_is_admin_true(
        self, mock_guests, mock_admins
    ):
        mock_group = MagicMock()
        mock_admins.return_value = mock_group
        mock_user = MagicMock()

        self.svc._assign_default_group(mock_user, is_admin=True)

        mock_admins.assert_called_once()
        mock_guests.assert_not_called()
        mock_user.groups.add.assert_called_once_with(mock_group)

    @patch("apps.users.services.get_administrators_group")
    @patch("apps.users.services.get_guests_group")
    def test_uses_guests_group_when_is_admin_false(self, mock_guests, mock_admins):
        mock_group = MagicMock()
        mock_guests.return_value = mock_group
        mock_user = MagicMock()

        self.svc._assign_default_group(mock_user, is_admin=False)

        mock_guests.assert_called_once()
        mock_admins.assert_not_called()
        mock_user.groups.add.assert_called_once_with(mock_group)

    @patch("apps.users.services.get_guests_group")
    def test_uses_guests_group_by_default_when_is_admin_not_passed(self, mock_guests):
        mock_group = MagicMock()
        mock_guests.return_value = mock_group
        mock_user = MagicMock()

        self.svc._assign_default_group(mock_user)

        mock_guests.assert_called_once()
        mock_user.groups.add.assert_called_once_with(mock_group)

    @patch("apps.users.services.get_guests_group")
    def test_skips_group_add_when_guests_group_is_none(self, mock_guests):
        mock_guests.return_value = None
        mock_user = MagicMock()

        self.svc._assign_default_group(mock_user, is_admin=False)

        mock_user.groups.add.assert_not_called()

    @patch("apps.users.services.get_administrators_group")
    def test_skips_group_add_when_administrators_group_is_none(self, mock_admins):
        mock_admins.return_value = None
        mock_user = MagicMock()

        self.svc._assign_default_group(mock_user, is_admin=True)

        mock_user.groups.add.assert_not_called()

    @patch("apps.users.services.get_guests_group")
    def test_passes_group_object_to_groups_add(self, mock_guests):
        sentinel = MagicMock(name="guests_group")
        mock_guests.return_value = sentinel
        mock_user = MagicMock()

        self.svc._assign_default_group(mock_user, is_admin=False)

        mock_user.groups.add.assert_called_once_with(sentinel)

    @patch("apps.users.services.get_administrators_group")
    def test_passes_admin_group_object_to_groups_add(self, mock_admins):
        sentinel = MagicMock(name="admins_group")
        mock_admins.return_value = sentinel
        mock_user = MagicMock()

        self.svc._assign_default_group(mock_user, is_admin=True)

        mock_user.groups.add.assert_called_once_with(sentinel)


# ---------------------------------------------------------------------------
# AdminUserService.create — thin wrapper delegation
# ---------------------------------------------------------------------------


class AdminUserServiceDelegationTest(SimpleTestCase):
    @patch.object(BaseUserService, "_create_user")
    def test_delegates_to_create_user_with_is_superuser_true(self, mock_create):
        mock_create.return_value = MagicMock()
        svc = AdminUserService()

        svc.create(
            first_name="Alice",
            last_name="Admin",
            email="alice@example.com",
            password="StrongPass123!",
        )

        mock_create.assert_called_once_with(
            first_name="Alice",
            last_name="Admin",
            email="alice@example.com",
            is_superuser=True,
            password="StrongPass123!",
        )

    @patch.object(BaseUserService, "_create_user")
    def test_returns_result_from_create_user(self, mock_create):
        expected_user = MagicMock()
        mock_create.return_value = expected_user
        svc = AdminUserService()

        result = svc.create(
            first_name="Alice",
            last_name="Admin",
            email="alice@example.com",
            password="StrongPass123!",
        )

        self.assertIs(result, expected_user)


# ---------------------------------------------------------------------------
# SSOUserService.get_or_create — thin wrapper delegation
# ---------------------------------------------------------------------------


class SSOUserServiceDelegationTest(SimpleTestCase):
    @patch.object(BaseUserService, "_get_or_create_sso_user")
    def test_delegates_to_get_or_create_sso_user(self, mock_method):
        mock_user = MagicMock()
        mock_method.return_value = (mock_user, True)
        mock_provider = MagicMock()
        svc = SSOUserService()

        svc.get_or_create(
            email="sso@example.com",
            first_name="SSO",
            last_name="User",
            sso_provider=mock_provider,
            sso_uid="uid-001",
        )

        mock_method.assert_called_once_with(
            email="sso@example.com",
            first_name="SSO",
            last_name="User",
            sso_provider=mock_provider,
            sso_uid="uid-001",
        )

    @patch.object(BaseUserService, "_get_or_create_sso_user")
    def test_returns_tuple_from_private_method(self, mock_method):
        mock_user = MagicMock()
        mock_method.return_value = (mock_user, True)
        svc = SSOUserService()
        mock_provider = MagicMock()

        result = svc.get_or_create(
            email="sso@example.com",
            first_name="SSO",
            last_name="User",
            sso_provider=mock_provider,
            sso_uid="uid-001",
        )

        self.assertEqual(result, (mock_user, True))

    @patch.object(BaseUserService, "_get_or_create_sso_user")
    def test_created_false_propagates_for_existing_user(self, mock_method):
        mock_user = MagicMock()
        mock_method.return_value = (mock_user, False)
        svc = SSOUserService()

        _, created = svc.get_or_create(
            email="sso@example.com",
            first_name="SSO",
            last_name="User",
            sso_provider=MagicMock(),
            sso_uid="uid-001",
        )

        self.assertFalse(created)
