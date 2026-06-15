import logging
import os

from django.contrib.contenttypes.models import ContentType
from django.db import transaction

from apps.core.exceptions import AlreadyExistsException, ConflictException
from apps.core.services import (
    ContextService,
    ExportService,
    FilterableQueryService,
    ImportService,
)
from apps.users.models import User, UserAvatar, UserProfile
from apps.users.selectors import (
    get_administrators_group,
    get_guests_group,
    superuser_exists,
    user_exists,
)

logger = logging.getLogger(__name__)


def _build_display_name(first_name: str, last_name: str) -> str:
    """Return 'lastname, firstname', or whichever part is present."""
    first = (first_name or "").strip()
    last = (last_name or "").strip()
    if last and first:
        return f"{last}, {first}"
    return last or first


class BaseUserService:
    def _assign_default_group(self, user: User, *, is_admin: bool = False) -> None:
        group = get_administrators_group() if is_admin else get_guests_group()
        if group is not None:
            user.groups.add(group)
        else:
            logger.warning(
                "System group '%s' not found; skipping group assignment for user '%s'.",
                "Administrators" if is_admin else "Guests",
                user.email,
            )

    def _create_user(
        self,
        *,
        first_name,
        last_name,
        email,
        is_superuser=False,
        password=None,
        created_by=None,
    ):
        from apps.auth.constants import AuthMode
        from apps.configurations.selectors import Auth

        if user_exists(email):
            raise AlreadyExistsException(detail="User already exists.")

        if is_superuser and superuser_exists():
            raise ConflictException(detail="An admin user already exists.")

        user_data = {
            "username": email,
            "email": email,
            "first_name": first_name,
            "last_name": last_name,
        }

        display_name = _build_display_name(first_name, last_name)

        if is_superuser:
            user = User.objects.create_superuser(**user_data, password=password)
            UserProfile.objects.create(
                user=user,
                display_name=display_name,
                created_by=created_by,
            )
            self._assign_default_group(user, is_admin=True)
            return user

        auth_mode = Auth.get_auth_mode()
        if auth_mode == AuthMode.CLASSIC:
            user = User.objects.create_user(**user_data, password=password)
            UserProfile.objects.create(
                user=user,
                display_name=display_name,
                created_by=created_by,
            )
        elif auth_mode == AuthMode.SAML or auth_mode == AuthMode.OAUTH:
            user = User.objects.create_user(**user_data)
            user.set_unusable_password()
            user.save()
            UserProfile.objects.create(
                user=user,
                display_name=display_name,
                created_by=created_by,
            )

        self._assign_default_group(user, is_admin=False)
        return user

    def _create_sso_user(
        self,
        *,
        first_name,
        last_name,
        email,
        sso_provider,
        sso_uid,
        created_by=None,
    ):
        """Create a new user and link them to an SSO provider."""
        if user_exists(email):
            raise AlreadyExistsException(detail="User already exists.")

        ct = ContentType.objects.get_for_model(sso_provider)

        with transaction.atomic():
            user = User.objects.create_user(
                username=email,
                email=email,
                first_name=first_name or "",
                last_name=last_name or "",
            )
            user.set_unusable_password()
            user.save()

            UserProfile.objects.create(
                user=user,
                display_name=_build_display_name(first_name or "", last_name or ""),
                sso_provider_content_type=ct,
                sso_provider_object_id=sso_provider.pk,
                sso_uid=sso_uid,
                created_by=created_by,
            )
            self._assign_default_group(user, is_admin=False)

        return user

    def _get_or_create_sso_user(
        self,
        *,
        email,
        first_name,
        last_name,
        sso_provider,
        sso_uid,
        created_by=None,
    ):
        """Find or create a user for an SSO login. Returns (user, created)."""
        ct = ContentType.objects.get_for_model(sso_provider)

        # 1. Lookup by SSO UID + provider — fastest path for returning users.
        profile = (
            UserProfile.objects.filter(
                sso_provider_content_type=ct,
                sso_provider_object_id=sso_provider.pk,
                sso_uid=sso_uid,
            )
            .select_related("user")
            .first()
        )
        if profile:
            return profile.user, False

        # 2. Existing user (created by admin) with matching email — link them.
        try:
            user = User.objects.get(email=email)
            profile = user.profile
            profile.sso_provider_content_type = ct
            profile.sso_provider_object_id = sso_provider.pk
            profile.sso_uid = sso_uid
            profile.save()
            return user, False
        except User.DoesNotExist:
            pass

        # 3. Brand-new SSO user.
        user = self._create_sso_user(
            first_name=first_name,
            last_name=last_name,
            email=email,
            sso_provider=sso_provider,
            sso_uid=sso_uid,
            created_by=created_by,
        )
        return user, True


class UserAvatarService(ContextService):
    """Handles avatar storage and SSO avatar sync."""

    _AVATAR_FOLDER = "user_avatars"
    _CONTENT_TYPE_EXT: dict[str, str] = {
        "image/jpeg": ".jpg",
        "image/png": ".png",
        "image/gif": ".gif",
        "image/webp": ".webp",
    }

    def sync_from_url(self, user: User, picture_url: str) -> None:
        """
        Best-effort avatar sync from an SSO provider URL.
        Silently skips on any failure so that login is never interrupted.
        """
        if not picture_url:
            return
        try:
            content, content_type = self._fetch(picture_url)
            ext = self._CONTENT_TYPE_EXT.get(content_type, ".jpg")
            profile_code = getattr(getattr(user, "profile", None), "code", None) or str(
                user.pk
            )
            filename = f"{profile_code}_avatar{ext}"
            uri = self._store(content, filename, content_type)
            self._upsert(user, uri)
        except Exception:
            logger.warning(
                "Avatar sync skipped for user %s — download or storage failed.",
                user.pk,
                exc_info=True,
            )

    def upload(self, file_data: bytes, filename: str, content_type: str) -> None:
        """Store an avatar uploaded by the authenticated user."""
        uri = self._store(file_data, filename, content_type)
        self._upsert(self.user, uri)

    def _fetch(self, url: str) -> tuple[bytes, str]:
        import urllib.request

        req = urllib.request.Request(url)  # nosec B310
        req.add_header("User-Agent", "ResourcePlanner/1.0")
        with urllib.request.urlopen(req, timeout=10) as resp:  # nosec B310
            content = resp.read()
            raw_ct = resp.headers.get("Content-Type", "image/jpeg")
            content_type = raw_ct.split(";")[0].strip()
        return content, content_type

    def _store(self, content: bytes, filename: str, content_type: str) -> str:
        from storagecore import store as storagecore_store

        from apps.configurations.selectors import Infra

        storage_type = Infra.get_storage_type().value
        try:
            storage_path = Infra.get_storage_path()
        except Exception:
            storage_path = ""

        return storagecore_store(
            content=content,
            filename=filename,
            folder=self._AVATAR_FOLDER,
            storage_type=storage_type,
            storage_path=storage_path,
            aws_region=os.environ.get("AWS_REGION", ""),
            aws_access_key=os.environ.get("AWS_ACCESS_KEY_ID", ""),
            aws_secret_key=os.environ.get("AWS_SECRET_ACCESS_KEY", ""),
            content_type=content_type,
        )

    def _upsert(self, user: User, uri: str) -> None:
        from storagecore import delete as storagecore_delete

        existing = UserAvatar.objects.filter(user=user).first()
        if existing is None:
            UserAvatar.objects.create(user=user, avatar=uri)
            return

        old_uri = existing.avatar
        existing.avatar = uri
        existing.save(update_fields=["avatar", "updated_at"])

        # Delete the old file after the DB record is safely updated.
        # storagecore.delete() is a no-op for data: URIs so this is
        # safe to call unconditionally regardless of storage backend.
        if old_uri and old_uri != uri:
            try:
                storagecore_delete(
                    old_uri,
                    aws_region=os.environ.get("AWS_REGION", ""),
                    aws_access_key=os.environ.get("AWS_ACCESS_KEY_ID", ""),
                    aws_secret_key=os.environ.get("AWS_SECRET_ACCESS_KEY", ""),
                )
            except Exception:
                logger.warning(
                    "Failed to delete old avatar %r for user %s.",
                    old_uri,
                    user.pk,
                    exc_info=True,
                )


class UserPreferencesService(ContextService):
    def update_theme(self, theme: str) -> None:
        profile, _ = UserProfile.objects.get_or_create(
            user=self.user,
            defaults={
                "display_name": _build_display_name(
                    self.user.first_name, self.user.last_name
                )
            },
        )
        profile.theme = theme
        profile.save(update_fields=["theme", "updated_at"])


class UserProfileService(ContextService):
    """Reads and updates the authenticated user's full profile."""

    def get_me(self) -> dict:
        from apps.auth.constants import AuthMode
        from apps.configurations.selectors import Auth
        from apps.users.constants import ThemeChoices

        user = self.user
        profile: UserProfile | None = getattr(user, "profile", None)

        # SSO info
        is_sso = bool(profile and profile.sso_uid)
        sso_provider_name: str | None = None
        if is_sso and profile and profile.sso_provider:
            sso_provider_name = getattr(profile.sso_provider, "name", None)

        # Avatar URL (null if no avatar recorded)
        has_avatar = UserAvatar.objects.filter(user=user).exists()
        avatar_url = "/api/v1/users/me/avatar/" if has_avatar else None

        # Groups
        groups = [
            {
                "name": g.name,
                "description": getattr(g, "profile", None)
                and g.profile.description
                or "",
            }
            for g in user.groups.prefetch_related().all()
        ]

        # Workforce fields from profile
        location = employment_type = role = None
        skills: list[dict] = []
        theme = ThemeChoices.LIGHT
        timezone = "UTC"
        display_name = ""
        password_last_changed = None

        if profile:
            theme = profile.theme
            timezone = profile.timezone or "UTC"
            display_name = profile.display_name or ""
            password_last_changed = profile.password_last_changed

            if profile.location:
                loc = profile.location
                location = {
                    "code": loc.code,
                    "label": f"{loc.city}, {loc.country}"
                    if hasattr(loc, "city")
                    else str(loc),
                }

            if profile.employment_type:
                et = profile.employment_type
                location_name = getattr(et, "name", str(et))
                employment_type = {"code": et.code, "label": location_name}

            if profile.role:
                r = profile.role
                role = {"code": r.code, "label": getattr(r, "name", str(r))}

            skills = [
                {"code": s.code, "skill": s.skill}
                for s in profile.skills.filter(is_active=True)
            ]

        auth_mode = Auth.get_auth_mode()
        is_classic = auth_mode == AuthMode.CLASSIC or user.is_superuser

        return {
            "profile_code": profile.code if profile else None,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "email": user.email,
            "display_name": display_name,
            "theme": theme,
            "timezone": timezone,
            "avatar_url": avatar_url,
            "is_sso": is_sso,
            "sso_provider_name": sso_provider_name,
            "is_classic": is_classic,
            "last_login": user.last_login,
            "password_last_changed": password_last_changed,
            "groups": groups,
            "location": location,
            "employment_type": employment_type,
            "role": role,
            "skills": skills,
        }

    def update_profile(
        self,
        *,
        first_name: str | None = None,
        last_name: str | None = None,
        display_name: str | None = None,
        timezone: str | None = None,
        skills: list[str] | None = None,
    ) -> None:
        from apps.users.constants import TIMEZONE_CHOICES

        user = self.user
        user_dirty = False

        if first_name is not None:
            user.first_name = first_name.strip()
            user_dirty = True
        if last_name is not None:
            user.last_name = last_name.strip()
            user_dirty = True

        if user_dirty:
            user.save(update_fields=["first_name", "last_name"])

        profile, _ = UserProfile.objects.get_or_create(
            user=user,
            defaults={
                "display_name": _build_display_name(user.first_name, user.last_name)
            },
        )
        profile_fields: list[str] = []

        if display_name is not None:
            profile.display_name = display_name.strip()
            profile_fields.append("display_name")

        if timezone is not None:
            valid_tzs = {tz for tz, _ in TIMEZONE_CHOICES}
            if timezone not in valid_tzs:
                from apps.core.exceptions import ValidationException

                raise ValidationException("Invalid timezone.")
            profile.timezone = timezone
            profile_fields.append("timezone")

        if profile_fields:
            profile_fields.append("updated_at")
            profile.save(update_fields=profile_fields)

        if skills is not None:
            from apps.skills.models import Skill

            skill_objs = Skill.objects.filter(code__in=skills, is_active=True)
            profile.skills.set(skill_objs)

    def change_password(self, *, current_password: str, new_password: str) -> None:
        from django.contrib.auth.password_validation import validate_password
        from django.core.exceptions import ValidationError as DjangoValidationError
        from django.utils import timezone

        from apps.auth.constants import AuthMode
        from apps.configurations.selectors import Auth
        from apps.core.exceptions import ValidationException

        user = self.user
        auth_mode = Auth.get_auth_mode()
        if auth_mode != AuthMode.CLASSIC and not user.is_superuser:
            raise ValidationException(
                "Password changes are not available for SSO accounts."
            )

        if not user.check_password(current_password):
            raise ValidationException("Current password is incorrect.")

        if user.check_password(new_password):
            raise ValidationException(
                "New password must be different from your current password."
            )

        try:
            validate_password(new_password, user=user)
        except DjangoValidationError as exc:
            raise ValidationException(str(exc.messages[0])) from exc

        user.set_password(new_password)
        user.save(update_fields=["password"])

        profile = getattr(user, "profile", None)
        if profile:
            profile.password_last_changed = timezone.now()
            profile.save(update_fields=["password_last_changed", "updated_at"])

    @staticmethod
    def get_timezone_options() -> list[dict]:
        from apps.users.constants import TIMEZONE_CHOICES

        return [{"value": tz, "label": tz} for tz, _ in sorted(TIMEZONE_CHOICES)]

    def get_avatar_bytes(self) -> tuple[bytes, str] | None:
        """Return (content, content_type) for the user's current avatar, or None."""
        import os

        from storagecore import retrieve

        record = UserAvatar.objects.filter(user=self.user).first()
        if record is None:
            return None

        uri = record.avatar
        try:
            content_type = "image/jpeg"
            if uri.startswith("data:"):
                mime_part = uri[5 : uri.index(";")]
                content_type = mime_part
            elif "." in uri.split("/")[-1]:
                ext = uri.split(".")[-1].lower()
                content_type = {
                    "jpg": "image/jpeg",
                    "jpeg": "image/jpeg",
                    "png": "image/png",
                    "gif": "image/gif",
                    "webp": "image/webp",
                }.get(ext, "image/jpeg")

            data = retrieve(
                uri,
                aws_region=os.environ.get("AWS_REGION", ""),
                aws_access_key=os.environ.get("AWS_ACCESS_KEY_ID", ""),
                aws_secret_key=os.environ.get("AWS_SECRET_ACCESS_KEY", ""),
            )
            return data, content_type
        except FileNotFoundError:
            return None
        except Exception:
            logger.warning(
                "Could not retrieve avatar for user %s.", self.user.pk, exc_info=True
            )
            return None


class AdminUserService(BaseUserService, ContextService):
    def create(self, *, first_name, last_name, email, password):
        return self._create_user(
            first_name=first_name,
            last_name=last_name,
            email=email,
            is_superuser=True,
            password=password,
        )


class SSOUserService(BaseUserService, ContextService):
    def get_or_create(self, *, email, first_name, last_name, sso_provider, sso_uid):
        return self._get_or_create_sso_user(
            email=email,
            first_name=first_name,
            last_name=last_name,
            sso_provider=sso_provider,
            sso_uid=sso_uid,
        )


class MembersService(FilterableQueryService):
    """Manages workforce details for all members (admin-facing)."""

    _MODULE = "users"
    _RESOURCE_TYPE = "member"

    filterable_fields: dict[str, str] = {
        "role": "role__code",
        "employment_type": "employment_type__code",
        "location": "location__code",
        "team": "user__team_assignments__team__code",
        "skill": "skills__code",
    }
    search_fields: list[str] = [
        "user__first_name",
        "user__last_name",
        "user__email",
        "display_name",
    ]
    sortable_fields: list[str] = [
        "user__last_name",
        "user__first_name",
        "user__email",
        "joined_date",
    ]
    default_ordering: list[str] = ["user__last_name", "user__first_name"]
    filter_active_by_default: bool = False

    def get_queryset(self):
        from apps.users.selectors import get_all_members

        return get_all_members()

    def apply_filters(self, qs, filters: dict):
        is_active_raw = filters.get("is_active", "")
        if str(is_active_raw).lower() == "all":
            pass
        elif str(is_active_raw).lower() in ("false", "0"):
            qs = qs.filter(user__is_active=False)
        else:
            qs = qs.filter(user__is_active=True)
        qs = super().apply_filters(qs, filters)
        if filters.get("team") or filters.get("skill"):
            qs = qs.distinct()
        return qs

    def get(self, code: str) -> UserProfile:
        from apps.core.exceptions import NotFoundException
        from apps.users.selectors import get_member_by_code

        obj = get_member_by_code(code)
        if obj is None:
            raise NotFoundException(
                resource="Member", lookup_field="code", lookup_value=code
            )
        return obj

    @transaction.atomic
    def update(self, code: str, **kwargs: object) -> UserProfile:
        from apps.core.exceptions import ValidationException

        profile = self.get(code)

        profile.updated_by = self.user
        update_fields = ["updated_at", "updated_by"]

        if "location" in kwargs:
            loc_code = kwargs.pop("location")
            if loc_code:
                from apps.locations.models import Location

                try:
                    profile.location = Location.objects.get(
                        code=loc_code, is_active=True
                    )
                except Location.DoesNotExist as exc:
                    raise ValidationException(
                        f"Location '{loc_code}' not found."
                    ) from exc
            else:
                profile.location = None
            update_fields.append("location")

        if "employment_type" in kwargs:
            et_code = kwargs.pop("employment_type")
            if et_code:
                from apps.employment_types.models import EmploymentType

                try:
                    profile.employment_type = EmploymentType.objects.get(
                        code=et_code, is_active=True
                    )
                except EmploymentType.DoesNotExist as exc:
                    raise ValidationException(
                        f"Employment type '{et_code}' not found."
                    ) from exc
            else:
                profile.employment_type = None
            update_fields.append("employment_type")

        if "role" in kwargs:
            role_code = kwargs.pop("role")
            if role_code:
                from apps.roles.models import Role

                try:
                    profile.role = Role.objects.get(code=role_code, is_active=True)
                except Role.DoesNotExist as exc:
                    raise ValidationException(f"Role '{role_code}' not found.") from exc
            else:
                profile.role = None
            update_fields.append("role")

        for field in ("joined_date", "leaving_date", "default_holidays"):
            if field in kwargs:
                setattr(profile, field, kwargs.pop(field))
                update_fields.append(field)

        profile.save(update_fields=update_fields)
        return profile


class MembersExportService(ExportService):
    EXPORT_FIELD_LABELS: dict[str, str] = {
        "code": "Code",
        "first_name": "First Name",
        "last_name": "Last Name",
        "display_name": "Display Name",
        "email": "Email",
        "is_active": "Active",
        "location": "Location",
        "employment_type": "Employment Type",
        "role": "Role",
        "joined_date": "Joined Date",
        "leaving_date": "Leaving Date",
        "default_holidays": "Default Holidays",
        "created_at": "Created On",
        "created_by": "Created By",
        "updated_at": "Updated On",
        "updated_by": "Updated By",
    }
    DEFAULT_EXPORT_FIELDS: list[str] = [
        "code",
        "first_name",
        "last_name",
        "display_name",
        "email",
        "is_active",
        "location",
        "employment_type",
        "role",
        "joined_date",
    ]
    EXPORT_FILENAME = "members_export"
    EXPORT_MODULE_NAME = "Members"

    def _get_field_value(self, obj: UserProfile, field: str) -> str:
        if field in ("first_name", "last_name", "email"):
            return str(getattr(obj.user, field, "") or "")
        if field == "is_active":
            return "Yes" if obj.user.is_active else "No"
        if field == "location":
            if obj.location:
                return f"{obj.location.city}, {obj.location.country}"
            return ""
        if field == "employment_type":
            return obj.employment_type.name if obj.employment_type else ""
        if field == "role":
            return obj.role.role if obj.role else ""
        return super()._get_field_value(obj, field)

    def export(
        self,
        fields: list[str] | None = None,
        export_format: str = "csv",
        filters: dict | None = None,
    ):
        from apps.core.exceptions import ValidationException
        from apps.users.selectors import get_all_members

        resolved = [
            f
            for f in (fields or self.DEFAULT_EXPORT_FIELDS)
            if f in self.EXPORT_FIELD_LABELS
        ] or self.DEFAULT_EXPORT_FIELDS

        qs = get_all_members()
        if filters:
            is_active_raw = filters.get("is_active")
            if str(is_active_raw or "").lower() == "all":
                pass
            elif str(is_active_raw or "").lower() in ("false", "0"):
                qs = qs.filter(user__is_active=False)
            else:
                qs = qs.filter(user__is_active=True)
            search = (filters.get("search") or "").strip()
            if search:
                from django.db.models import Q

                qs = qs.filter(
                    Q(user__first_name__icontains=search)
                    | Q(user__last_name__icontains=search)
                    | Q(user__email__icontains=search)
                    | Q(display_name__icontains=search)
                )

        rows = self._prepare_rows(list(qs), resolved)

        fmt = export_format.lower()
        if fmt == "csv":
            return self._export_csv(rows)
        if fmt == "xlsx":
            return self._export_xlsx(rows)
        if fmt == "pdf":
            return self._export_pdf(rows)
        if fmt == "json":
            return self._export_json(rows)
        allowed = "csv, xlsx, pdf, json"
        raise ValidationException(
            f"Unsupported export format '{export_format}'. Allowed: {allowed}."
        )


class UsersAdminService(FilterableQueryService):
    """Admin-facing user management (activate, deactivate, create, delete, reset)."""

    _MODULE = "users"
    _RESOURCE_TYPE = "user"

    filterable_fields: dict[str, str] = {}
    search_fields: list[str] = [
        "user__first_name",
        "user__last_name",
        "user__email",
        "display_name",
    ]
    sortable_fields: list[str] = [
        "user__last_name",
        "user__first_name",
        "user__email",
        "created_at",
    ]
    default_ordering: list[str] = ["user__last_name", "user__first_name"]
    filter_active_by_default: bool = False

    def get_queryset(self):
        from apps.users.selectors import get_all_users

        return get_all_users()

    def apply_filters(self, qs, filters: dict):
        is_active_raw = filters.get("is_active", "")
        if str(is_active_raw).lower() == "all":
            pass
        elif str(is_active_raw).lower() in ("false", "0"):
            qs = qs.filter(user__is_active=False)
        else:
            qs = qs.filter(user__is_active=True)

        auth_type = filters.get("auth_type", "")
        if auth_type == "classic":
            qs = qs.filter(sso_provider_content_type__isnull=True)
        elif auth_type == "oauth":
            qs = qs.filter(sso_provider_content_type__app_label="oauth")
        elif auth_type == "saml":
            qs = qs.filter(sso_provider_content_type__app_label="saml")

        return super().apply_filters(qs, filters)

    def get(self, code: str) -> UserProfile:
        from apps.core.exceptions import NotFoundException
        from apps.users.selectors import get_user_by_profile_code

        obj = get_user_by_profile_code(code)
        if obj is None:
            raise NotFoundException(
                resource="User", lookup_field="code", lookup_value=code
            )
        return obj

    def stats(self) -> dict:
        from django.db.models import Count, Q

        qs = UserProfile.objects.aggregate(
            total=Count("id"),
            active=Count("id", filter=Q(user__is_active=True)),
            inactive=Count("id", filter=Q(user__is_active=False)),
            classic=Count("id", filter=Q(sso_provider_content_type__isnull=True)),
        )
        return {
            "total": qs["total"],
            "active": qs["active"],
            "inactive": qs["inactive"],
            "classic": qs["classic"],
            "sso": qs["total"] - qs["classic"],
        }

    @transaction.atomic
    def create(self, *, first_name: str, last_name: str, email: str) -> UserProfile:
        from apps.auth.constants import AuthMode
        from apps.configurations.selectors import Auth
        from apps.core.exceptions import PermissionException

        auth_mode = Auth.get_auth_mode()
        if auth_mode != AuthMode.CLASSIC:
            raise PermissionException(
                "Admin user creation is only available in classic auth mode."
            )

        user = BaseUserService()._create_user(
            first_name=first_name,
            last_name=last_name,
            email=email,
            password=None,
            created_by=self.user,
        )
        profile = user.profile
        profile.must_change_password = True
        profile.save(update_fields=["must_change_password", "updated_at"])

        from apps.auth.services import AdminPasswordResetService

        AdminPasswordResetService().send_reset_link(user)
        return profile

    @transaction.atomic
    def activate(self, code: str) -> UserProfile:
        profile = self.get(code)
        profile.user.is_active = True
        profile.user.save(update_fields=["is_active"])
        logger.info("User profile %s activated by %s.", code, self.user)
        return profile

    @transaction.atomic
    def deactivate(self, code: str) -> UserProfile:
        profile = self.get(code)
        profile.user.is_active = False
        profile.user.save(update_fields=["is_active"])
        logger.info("User profile %s deactivated by %s.", code, self.user)
        return profile

    @transaction.atomic
    def delete(self, code: str) -> None:
        profile = self.get(code)
        user = profile.user
        user.delete()
        logger.info("User profile %s permanently deleted by %s.", code, self.user)

    def send_admin_password_reset(self, code: str) -> None:
        from apps.auth.constants import AuthMode
        from apps.configurations.selectors import Auth
        from apps.core.exceptions import ValidationException

        auth_mode = Auth.get_auth_mode()
        if auth_mode != AuthMode.CLASSIC:
            raise ValidationException(
                "Password reset is only available for classic auth users."
            )

        profile = self.get(code)
        ct = profile.sso_provider_content_type
        if ct is not None:
            raise ValidationException("Password reset is not available for SSO users.")

        from apps.auth.services import AdminPasswordResetService

        AdminPasswordResetService().send_reset_link(profile.user)


class GroupsAdminService(FilterableQueryService):
    """Admin-facing group management (create, activate, deactivate, delete, members)."""

    _MODULE = "users"
    _RESOURCE_TYPE = "group"

    filterable_fields: dict[str, str] = {
        "is_admin_group": "is_admin_group",
        "is_system": "is_system",
    }
    search_fields: list[str] = ["group__name", "description"]
    sortable_fields: list[str] = ["group__name", "created_at"]
    default_ordering: list[str] = ["group__name"]
    filter_active_by_default: bool = False

    def get_queryset(self):
        from apps.users.selectors import get_all_groups

        return get_all_groups()

    def apply_filters(self, qs, filters: dict):
        is_active_raw = filters.get("is_active", "")
        if str(is_active_raw).lower() == "all":
            pass
        elif str(is_active_raw).lower() in ("false", "0"):
            qs = qs.filter(is_active=False)
        elif str(is_active_raw).lower() in ("true", "1"):
            qs = qs.filter(is_active=True)
        return super().apply_filters(qs, filters)

    def get(self, code: str):
        from apps.core.exceptions import NotFoundException
        from apps.users.selectors import get_group_by_code

        obj = get_group_by_code(code)
        if obj is None:
            raise NotFoundException(
                resource="Group", lookup_field="code", lookup_value=code
            )
        return obj

    def stats(self) -> dict:
        from django.db.models import Count, Q

        from apps.users.models import GroupProfile

        qs = GroupProfile.objects.aggregate(
            total=Count("id"),
            active=Count("id", filter=Q(is_active=True)),
            inactive=Count("id", filter=Q(is_active=False)),
            admin_groups=Count("id", filter=Q(is_admin_group=True)),
        )
        return {
            "total": qs["total"],
            "active": qs["active"],
            "inactive": qs["inactive"],
            "admin_groups": qs["admin_groups"],
        }

    @transaction.atomic
    def create(self, *, name: str, description: str = ""):
        from apps.core.exceptions import AlreadyExistsException
        from apps.users.models import Group, GroupProfile

        if Group.objects.filter(name=name).exists():
            raise AlreadyExistsException(
                detail="A group with this name already exists."
            )

        group = Group.objects.create(name=name)
        profile = GroupProfile.objects.create(
            group=group,
            description=description,
            created_by=self.user,
            updated_by=self.user,
        )
        return profile

    @transaction.atomic
    def update(self, code: str, **data):
        from apps.core.exceptions import AlreadyExistsException
        from apps.users.models import Group

        profile = self.get(code)
        name = data.get("name")
        if name and name != profile.group.name:
            if Group.objects.filter(name=name).exclude(pk=profile.group.pk).exists():
                raise AlreadyExistsException(
                    detail="A group with this name already exists."
                )
            profile.group.name = name
            profile.group.save(update_fields=["name"])

        if "description" in data:
            profile.description = data["description"]

        profile.updated_by = self.user
        profile.save(update_fields=["description", "updated_by", "updated_at"])
        return self.get(code)

    @transaction.atomic
    def activate(self, code: str):
        profile = self.get(code)
        profile.is_active = True
        profile.updated_by = self.user
        profile.save(update_fields=["is_active", "updated_by", "updated_at"])
        logger.info("Group %s activated by %s.", code, self.user)
        return self.get(code)

    @transaction.atomic
    def deactivate(self, code: str):
        profile = self.get(code)
        profile.is_active = False
        profile.updated_by = self.user
        profile.save(update_fields=["is_active", "updated_by", "updated_at"])
        logger.info("Group %s deactivated by %s.", code, self.user)
        return self.get(code)

    @transaction.atomic
    def delete(self, code: str) -> None:
        profile = self.get(code)
        group = profile.group
        group.delete()
        logger.info("Group %s permanently deleted by %s.", code, self.user)

    def list_members(self, code: str, params):
        from django.db.models import Q

        from apps.core.services import paginate_queryset
        from apps.users.selectors import get_group_members

        self.get(code)  # raises NotFoundException if not found
        qs = get_group_members(code)

        filters = params.filters or {}
        is_active_raw = filters.get("is_active", "")
        if str(is_active_raw).lower() == "all":
            pass
        elif str(is_active_raw).lower() in ("false", "0"):
            qs = qs.filter(user__is_active=False)
        else:
            qs = qs.filter(user__is_active=True)

        search = (params.search or "").strip()
        if search:
            qs = qs.filter(
                Q(user__first_name__icontains=search)
                | Q(user__last_name__icontains=search)
                | Q(user__email__icontains=search)
                | Q(display_name__icontains=search)
            )

        return paginate_queryset(qs, params.page, params.page_size)

    @transaction.atomic
    def assign_member(self, code: str, member_code: str) -> None:
        from apps.core.exceptions import AlreadyExistsException, NotFoundException
        from apps.users.models import UserProfile

        profile = self.get(code)
        try:
            member = UserProfile.objects.select_related("user").get(code=member_code)
        except UserProfile.DoesNotExist as exc:
            raise NotFoundException(
                resource="Member", lookup_field="code", lookup_value=member_code
            ) from exc

        if member.user.groups.filter(pk=profile.group.pk).exists():
            raise AlreadyExistsException(detail="Member is already in this group.")

        profile.group.user_set.add(member.user)
        logger.info(
            "Member %s assigned to group %s by %s.", member_code, code, self.user
        )

    @transaction.atomic
    def unassign_member(self, code: str, member_code: str) -> None:
        from apps.core.exceptions import NotFoundException
        from apps.users.models import UserProfile

        profile = self.get(code)
        try:
            member = UserProfile.objects.select_related("user").get(code=member_code)
        except UserProfile.DoesNotExist as exc:
            raise NotFoundException(
                resource="Member", lookup_field="code", lookup_value=member_code
            ) from exc

        profile.group.user_set.remove(member.user)
        logger.info(
            "Member %s removed from group %s by %s.", member_code, code, self.user
        )


class GroupsExportService(ExportService):
    EXPORT_FIELD_LABELS: dict[str, str] = {
        "name": "Name",
        "code": "Code",
        "description": "Description",
        "is_admin_group": "Admin Group",
        "is_active": "Active",
        "member_count": "Member Count",
        "created_at": "Created On",
        "created_by": "Created By",
    }
    DEFAULT_EXPORT_FIELDS: list[str] = [
        "name",
        "code",
        "description",
        "is_admin_group",
        "is_active",
        "member_count",
    ]
    EXPORT_FILENAME = "groups_export"
    EXPORT_MODULE_NAME = "Groups"

    def _get_field_value(self, obj, field: str) -> str:
        if field == "name":
            return obj.group.name
        if field == "is_active":
            return "Yes" if obj.is_active else "No"
        if field == "is_admin_group":
            return "Yes" if obj.is_admin_group else "No"
        if field == "member_count":
            return str(getattr(obj, "member_count", 0) or 0)
        return super()._get_field_value(obj, field)

    def export(
        self,
        fields: list[str] | None = None,
        export_format: str = "csv",
        filters: dict | None = None,
    ):
        from apps.core.exceptions import ValidationException
        from apps.users.selectors import get_all_groups

        resolved = [
            f
            for f in (fields or self.DEFAULT_EXPORT_FIELDS)
            if f in self.EXPORT_FIELD_LABELS
        ] or self.DEFAULT_EXPORT_FIELDS

        qs = get_all_groups()
        if filters:
            is_active_raw = filters.get("is_active")
            if str(is_active_raw or "").lower() == "all":
                pass
            elif str(is_active_raw or "").lower() in ("false", "0"):
                qs = qs.filter(is_active=False)
            elif str(is_active_raw or "").lower() in ("true", "1"):
                qs = qs.filter(is_active=True)
            search = (filters.get("search") or "").strip()
            if search:
                from django.db.models import Q

                qs = qs.filter(
                    Q(group__name__icontains=search) | Q(description__icontains=search)
                )

        rows = self._prepare_rows(list(qs), resolved)

        fmt = export_format.lower()
        if fmt == "csv":
            return self._export_csv(rows)
        if fmt == "xlsx":
            return self._export_xlsx(rows)
        if fmt == "pdf":
            return self._export_pdf(rows)
        if fmt == "json":
            return self._export_json(rows)
        allowed = "csv, xlsx, pdf, json"
        raise ValidationException(
            f"Unsupported export format '{export_format}'. Allowed: {allowed}."
        )


class GroupsImportService(ImportService):
    SUPPORTED_IMPORT_FORMATS = ["csv"]
    MAX_IMPORT_ROWS = 1_000
    MAX_IMPORT_FILE_SIZE_MB = 5

    def validate_file(self, file) -> None:
        from apps.core.exceptions import ValidationException

        _, ext = os.path.splitext(file.name)
        if ext.lower().lstrip(".") not in self.SUPPORTED_IMPORT_FORMATS:
            raise ValidationException(
                "Unsupported file format. Allowed: "
                f"{', '.join(self.SUPPORTED_IMPORT_FORMATS)}."
            )
        file_size_mb = file.size / (1024 * 1024)
        if file_size_mb > self.MAX_IMPORT_FILE_SIZE_MB:
            raise ValidationException(
                "File too large. Maximum allowed size: "
                f"{self.MAX_IMPORT_FILE_SIZE_MB} MB."
            )

    def validate_row(self, row: dict, row_num: int) -> list[dict]:
        errors: list[dict] = []
        name = (row.get("name") or "").strip()
        if not name:
            errors.append(
                {"row": row_num, "field": "name", "message": "Name is required."}
            )
        elif len(name) > 150:
            errors.append(
                {
                    "row": row_num,
                    "field": "name",
                    "message": "Name must be 150 characters or fewer.",
                }
            )
        return errors

    def bulk_import(self, file, dry_run: bool = False) -> dict:
        import csv
        import io

        from apps.core.exceptions import ValidationException
        from apps.users.models import Group

        content = file.read().decode("utf-8-sig")
        reader = csv.DictReader(io.StringIO(content))

        required_columns = {"name"}
        actual_columns = set(reader.fieldnames or [])
        missing = required_columns - actual_columns
        if missing:
            raise ValidationException(
                f"Missing required column(s): {', '.join(sorted(missing))}."
            )

        rows = list(reader)
        if len(rows) > self.MAX_IMPORT_ROWS:
            raise ValidationException(
                f"Too many rows. Maximum allowed: {self.MAX_IMPORT_ROWS}."
            )

        total = len(rows)
        created_rows: list[dict] = []
        errors: list[dict] = []
        group_svc = GroupsAdminService(user=self.user)

        for row_num, row in enumerate(rows, start=2):
            row_errors = self.validate_row(row, row_num)
            if row_errors:
                errors.extend(row_errors)
                continue

            name = row["name"].strip()
            description = (row.get("description") or "").strip()

            if Group.objects.filter(name=name).exists():
                errors.append(
                    {
                        "row": row_num,
                        "field": "name",
                        "message": f"A group named '{name}' already exists.",
                    }
                )
                continue

            if not dry_run:
                group_svc.create(name=name, description=description)

            created_rows.append({"row": row_num, "field": "name", "message": name})

        return {
            "total": total,
            "created_rows": created_rows,
            "errors": errors,
            "dry_run": dry_run,
        }


class UsersExportService(ExportService):
    EXPORT_FIELD_LABELS: dict[str, str] = {
        "code": "Code",
        "display_name": "Display Name",
        "first_name": "First Name",
        "last_name": "Last Name",
        "email": "Email",
        "auth_type": "Auth Type",
        "last_login": "Last Login",
        "is_active": "Active",
        "created_at": "Created On",
        "created_by": "Created By",
    }
    DEFAULT_EXPORT_FIELDS: list[str] = [
        "display_name",
        "email",
        "auth_type",
        "last_login",
        "is_active",
        "created_at",
    ]
    EXPORT_FILENAME = "users_export"
    EXPORT_MODULE_NAME = "Users"

    def _get_field_value(self, obj: UserProfile, field: str) -> str:
        if field in ("first_name", "last_name", "email"):
            return str(getattr(obj.user, field, "") or "")
        if field == "is_active":
            return "Yes" if obj.user.is_active else "No"
        if field == "last_login":
            val = obj.user.last_login
            return val.strftime("%Y-%m-%d %H:%M") if val else ""
        if field == "auth_type":
            ct = obj.sso_provider_content_type
            if ct is None:
                return "classic"
            return ct.app_label
        return super()._get_field_value(obj, field)

    def export(
        self,
        fields: list[str] | None = None,
        export_format: str = "csv",
        filters: dict | None = None,
    ):
        from apps.core.exceptions import ValidationException
        from apps.users.selectors import get_all_users

        resolved = [
            f
            for f in (fields or self.DEFAULT_EXPORT_FIELDS)
            if f in self.EXPORT_FIELD_LABELS
        ] or self.DEFAULT_EXPORT_FIELDS

        qs = get_all_users()
        if filters:
            is_active_raw = filters.get("is_active")
            if str(is_active_raw or "").lower() == "all":
                pass
            elif str(is_active_raw or "").lower() in ("false", "0"):
                qs = qs.filter(user__is_active=False)
            else:
                qs = qs.filter(user__is_active=True)
            search = (filters.get("search") or "").strip()
            if search:
                from django.db.models import Q

                qs = qs.filter(
                    Q(user__first_name__icontains=search)
                    | Q(user__last_name__icontains=search)
                    | Q(user__email__icontains=search)
                    | Q(display_name__icontains=search)
                )

        rows = self._prepare_rows(list(qs), resolved)

        fmt = export_format.lower()
        if fmt == "csv":
            return self._export_csv(rows)
        if fmt == "xlsx":
            return self._export_xlsx(rows)
        if fmt == "pdf":
            return self._export_pdf(rows)
        if fmt == "json":
            return self._export_json(rows)
        allowed = "csv, xlsx, pdf, json"
        raise ValidationException(
            f"Unsupported export format '{export_format}'. Allowed: {allowed}."
        )
