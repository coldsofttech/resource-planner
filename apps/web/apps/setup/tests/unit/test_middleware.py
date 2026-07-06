from unittest.mock import patch

from django.test import RequestFactory

from apps.setup.middleware import _BYPASS_PREFIXES, SetupMiddleware


def _make_request(path: str):
    factory = RequestFactory()
    request = factory.get(path)
    request.path_info = path
    return request


def _make_middleware(get_response=None):
    sentinel = object()
    get_response = get_response or (lambda req: sentinel)
    return SetupMiddleware(get_response), sentinel


# ---------------------------------------------------------------------------
# Setup incomplete — non-bypass paths are redirected
# ---------------------------------------------------------------------------


class TestSetupIncomplete:
    def _run(self, path: str):
        middleware, _ = _make_middleware()
        request = _make_request(path)
        with patch(
            "apps.configurations.selectors.Setup.is_setup_complete",
            return_value=False,
        ):
            return middleware(request)

    def test_non_bypass_path_redirects_to_setup(self):
        response = self._run("/dashboard/")
        assert response.status_code == 302
        assert response["Location"] == "/setup/"

    def test_projects_path_redirects(self):
        response = self._run("/projects/")
        assert response.status_code == 302
        assert response["Location"] == "/setup/"

    def test_api_non_setup_path_redirects(self):
        response = self._run("/api/v1/teams/")
        assert response.status_code == 302

    def test_root_path_redirects(self):
        response = self._run("/")
        assert response.status_code == 302


# ---------------------------------------------------------------------------
# Setup incomplete — bypass paths are never blocked
# ---------------------------------------------------------------------------


class TestSetupIncompleteBypassPaths:
    """
    Bypass paths must pass through even when setup is not complete.
    Setup.is_setup_complete() is never called for these paths, so no
    mocking of the DB selector is required.
    """

    def _run(self, path: str):
        middleware, sentinel = _make_middleware()
        request = _make_request(path)
        return middleware(request), sentinel

    def test_setup_ui_path_passes_through(self):
        result, sentinel = self._run("/setup/")
        assert result is sentinel

    def test_login_path_passes_through(self):
        result, sentinel = self._run("/login/")
        assert result is sentinel

    def test_register_path_passes_through(self):
        result, sentinel = self._run("/register/")
        assert result is sentinel

    def test_onboarding_path_passes_through(self):
        result, sentinel = self._run("/onboarding/step-1/")
        assert result is sentinel

    def test_api_setup_path_passes_through(self):
        result, sentinel = self._run("/api/v1/setup/")
        assert result is sentinel

    def test_api_auth_path_passes_through(self):
        result, sentinel = self._run("/api/v1/auth/")
        assert result is sentinel

    def test_api_meta_path_passes_through(self):
        result, sentinel = self._run("/api/v1/meta/")
        assert result is sentinel

    def test_static_path_passes_through(self):
        result, sentinel = self._run("/static/css/main.css")
        assert result is sentinel

    def test_media_path_passes_through(self):
        result, sentinel = self._run("/media/uploads/file.png")
        assert result is sentinel

    def test_favicon_passes_through(self):
        result, sentinel = self._run("/favicon.ico")
        assert result is sentinel

    def test_setup_checker_not_called_for_bypass_paths(self):
        middleware, sentinel = _make_middleware()
        request = _make_request("/api/v1/setup/")
        with patch(
            "apps.configurations.selectors.Setup.is_setup_complete"
        ) as mock_check:
            result = middleware(request)
        mock_check.assert_not_called()
        assert result is sentinel


# ---------------------------------------------------------------------------
# Setup complete — all paths pass through
# ---------------------------------------------------------------------------


class TestSetupComplete:
    def _run(self, path: str):
        middleware, sentinel = _make_middleware()
        request = _make_request(path)
        with patch(
            "apps.configurations.selectors.Setup.is_setup_complete",
            return_value=True,
        ):
            return middleware(request), sentinel

    def test_dashboard_passes_through(self):
        result, sentinel = self._run("/dashboard/")
        assert result is sentinel

    def test_api_teams_passes_through(self):
        result, sentinel = self._run("/api/v1/teams/")
        assert result is sentinel

    def test_root_passes_through(self):
        result, sentinel = self._run("/")
        assert result is sentinel


# ---------------------------------------------------------------------------
# Bypass prefix registry
# ---------------------------------------------------------------------------


class TestBypassPrefixes:
    def test_all_expected_prefixes_are_present(self):
        expected = {
            "/setup/",
            "/login/",
            "/forgot-password/",
            "/register/",
            "/onboarding/",
            "/api/v1/meta/",
            "/api/v1/setup/",
            "/api/v1/auth/",
            "/api/v1/onboarding/",
            "/api/v1/products/options/",
            "/api/v1/bu/options/",
            "/static/",
            "/favicon",
            "/media/",
        }
        assert expected == set(_BYPASS_PREFIXES)
