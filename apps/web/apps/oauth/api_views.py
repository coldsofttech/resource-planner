import secrets

from django.contrib.auth import login
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request

from apps.core.exceptions import NotFoundException, ValidationException
from apps.core.viewsets import BaseViewSet
from apps.oauth.selectors import get_active_provider_by_code
from apps.oauth.serializers import OAuthCreateSerializer, OAuthSerializer
from apps.oauth.services import OAuthFlowService, OAuthService

# Session key names for the OAuth state machine.
# Module-level so tests and any future middleware can reference them
# without importing the viewset class.
_SESSION_STATE = "oauth_state"
_SESSION_PROVIDER = "oauth_provider_code"
_SESSION_REDIRECT = "oauth_redirect_uri"


@extend_schema(tags=["Authentication: OAuth"])
class OAuthViewSet(BaseViewSet):
    service_class = OAuthService

    _PUBLIC_ACTIONS = {"authorize", "callback"}

    def get_permissions(self):
        if self.action in self._PUBLIC_ACTIONS:
            return [AllowAny()]
        return [IsAuthenticated()]

    def get_authenticators(self):
        # get_authenticators() is called during initialize_request(), before
        # DRF sets self.action. Use getattr to avoid AttributeError there.
        if getattr(self, "action", None) in self._PUBLIC_ACTIONS:
            return []
        return super().get_authenticators()

    def get_retrieve_serializer_class(self):
        return OAuthSerializer

    def get_create_serializer_class(self):
        return OAuthCreateSerializer

    def get_create_custom_message(self):
        return "OAuth provider created successfully."

    @extend_schema(
        summary="Create OAuth provider",
        request=OAuthCreateSerializer,
        responses={
            201: OAuthSerializer,
            400: OpenApiResponse(description="Validation error."),
            409: OpenApiResponse(description="Provider with this name already exists."),
        },
    )
    def create(self, request: Request):
        """POST /auth/oauth/"""
        return super().create(request)

    @extend_schema(
        summary="Begin OAuth login",
        description=(
            "Generates a one-time state token, stores it in the session, builds the "
            "IdP authorization URL, and returns it so the client can redirect the "
            "user. Query param `redirect_uri` must be the frontend callback URL the "
            "IdP will redirect back to."
        ),
        responses={
            200: OpenApiResponse(
                description="Authorization URL and state token returned."
            ),
            400: OpenApiResponse(description="redirect_uri query param is missing."),
            404: OpenApiResponse(description="OAuth provider not found or inactive."),
        },
    )
    @action(
        detail=False,
        methods=["get"],
        url_path=r"(?P<provider_code>[^/.]+)/authorize",
        url_name="authorize",
    )
    def authorize(self, request: Request, provider_code: str = ""):
        """GET /auth/oauth/<provider_code>/authorize/?redirect_uri=<uri>"""
        redirect_uri = request.query_params.get("redirect_uri", "").strip()
        if not redirect_uri:
            raise ValidationException("redirect_uri is required.")

        provider = get_active_provider_by_code(provider_code)
        if provider is None:
            raise NotFoundException(
                resource="OAuth provider",
                lookup_field="code",
                lookup_value=provider_code,
            )

        state = secrets.token_urlsafe(32)
        self._save_oauth_session(
            request, state=state, provider_code=provider_code, redirect_uri=redirect_uri
        )

        svc = OAuthFlowService(user=request.user, request=request)
        authorization_url = svc.build_authorize_url(
            provider=provider, redirect_uri=redirect_uri, state=state
        )

        return self.response(
            data={"authorization_url": authorization_url, "state": state},
            message="Authorization URL generated.",
            status_code=status.HTTP_200_OK,
        )

    @extend_schema(
        summary="Complete OAuth login",
        description=(
            "Exchanges the authorization code for an access token, retrieves user info "
            "from the IdP, creates or links the local user, and establishes a Django "
            "session. Request body: {code, state}."
        ),
        responses={
            200: OpenApiResponse(
                description="Login successful. Returns basic user info."
            ),
            400: OpenApiResponse(
                description=(
                    "Validation error — one of: code or state missing, state does not "
                    "match session, or provider returned no email address."
                )
            ),
            404: OpenApiResponse(description="OAuth provider not found or inactive."),
            503: OpenApiResponse(
                description="Token exchange or userinfo request to the IdP failed."
            ),
        },
    )
    @action(
        detail=False,
        methods=["post"],
        url_path="callback",
        url_name="callback",
    )
    def callback(self, request: Request):
        """POST /auth/oauth/callback/"""
        code, state = self._validate_callback_request(request)
        provider, redirect_uri = self._resolve_oauth_session(request, state)

        svc = OAuthFlowService(user=request.user, request=request)
        user = svc.complete_login(
            provider=provider, code=code, redirect_uri=redirect_uri
        )

        user.backend = "django.contrib.auth.backends.ModelBackend"
        login(request, user)

        return self.response(
            data={
                "user": {
                    "id": user.pk,
                    "email": user.email,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "is_superuser": user.is_superuser,
                }
            },
            message="Login successful.",
            status_code=status.HTTP_200_OK,
        )

    def _save_oauth_session(
        self,
        request: Request,
        *,
        state: str,
        provider_code: str,
        redirect_uri: str,
    ) -> None:
        request.session[_SESSION_STATE] = state
        request.session[_SESSION_PROVIDER] = provider_code
        request.session[_SESSION_REDIRECT] = redirect_uri
        request.session.save()

    def _validate_callback_request(self, request: Request) -> tuple[str, str]:
        code = (request.data.get("code") or "").strip()
        state = (request.data.get("state") or "").strip()
        if not code:
            raise ValidationException("code is required.")
        if not state:
            raise ValidationException("state is required.")
        return code, state

    def _resolve_oauth_session(self, request: Request, state: str):
        session_state = request.session.get(_SESSION_STATE)
        provider_code = request.session.get(_SESSION_PROVIDER)
        redirect_uri = request.session.get(_SESSION_REDIRECT)

        if not session_state or state != session_state:
            raise ValidationException("Invalid or expired OAuth state.")

        for key in (_SESSION_STATE, _SESSION_PROVIDER, _SESSION_REDIRECT):
            request.session.pop(key, None)

        provider = get_active_provider_by_code(provider_code)
        if provider is None:
            raise NotFoundException(
                resource="OAuth provider",
                lookup_field="code",
                lookup_value=provider_code,
            )

        return provider, redirect_uri
