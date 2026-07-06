from __future__ import annotations

from collections import defaultdict
from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from apps.audit.services import AuditService
from apps.core.exceptions import (
    AlreadyExistsException,
    NotFoundException,
    ValidationException,
)
from apps.core.services import AuditableService, FilterableQueryService
from apps.wins import selectors
from apps.wins.constants import (
    MonthlyWinStatus,
    SurveyPhase,
    SurveyStatus,
    WinCategory,
    WinStatus,
)
from apps.wins.models import (
    MonthlyWin,
    MonthlyWinsRecipient,
    MonthlyWinSurvey,
    MonthlyWinSurveyNomination,
    Win,
    WinEntry,
)

_MAX_NOMINATIONS_PER_CATEGORY = 2


class WinService(AuditableService, FilterableQueryService):
    _MODULE = "wins"
    _RESOURCE_TYPE = "win"

    filterable_fields: dict[str, str] = {"status": "status"}
    search_fields: list[str] = []
    sortable_fields: list[str] = ["week_number", "start_date", "end_date", "status"]
    default_ordering: list[str] = ["-week_number"]
    filter_active_by_default: bool = False

    def get_queryset(self):
        return selectors.get_all_wins()

    def _snapshot(self, win: Win) -> dict:
        return {
            "week_number": win.week_number,
            "start_date": str(win.start_date),
            "end_date": str(win.end_date),
            "status": win.status,
        }

    def get(self, code: str, *args, **kwargs) -> Win:
        obj = selectors.get_win_by_code(code)
        if obj is None:
            raise NotFoundException(
                resource="Win", lookup_field="code", lookup_value=code
            )
        return obj

    @transaction.atomic
    def create(self, *, start_date) -> Win:
        from apps.configurations.selectors import Wins as WinsConfig

        end_date = start_date + timedelta(days=6)
        week_number = selectors.get_next_week_number(WinsConfig.get_start_number())

        win = Win.objects.create(
            week_number=week_number,
            start_date=start_date,
            end_date=end_date,
            status=WinStatus.OPEN,
            created_by=self.user,
            updated_by=self.user,
        )
        AuditService.log_create(
            module=self._MODULE,
            resource_type=self._RESOURCE_TYPE,
            resource_code=win.code,
            after=self._snapshot(win),
            actor=self.user,
        )
        return win

    def update(self, pk, *args, **kwargs):
        raise NotImplementedError

    @transaction.atomic
    def delete(self, code: str, *args, **kwargs) -> None:
        win = self.get(code=code)
        win_code = win.code
        before = self._snapshot(win)
        win.delete()
        AuditService.log_delete(
            module=self._MODULE,
            resource_type=self._RESOURCE_TYPE,
            resource_code=win_code,
            before=before,
            actor=self.user,
        )

    @transaction.atomic
    def review_complete(self, code: str) -> Win:
        win = self.get(code=code)
        if win.status != WinStatus.OPEN:
            raise ValidationException(
                "Only a Win in Open status can be marked review complete."
            )

        before = self._snapshot(win)
        win.status = WinStatus.REVIEW_COMPLETE
        win.reviewed_at = timezone.now()
        win.reviewed_by = getattr(self.user, "profile", None)
        win.updated_by = self.user
        win.save(
            update_fields=[
                "status",
                "reviewed_at",
                "reviewed_by",
                "updated_by",
                "updated_at",
            ]
        )
        AuditService.log_update(
            module=self._MODULE,
            resource_type=self._RESOURCE_TYPE,
            resource_code=win.code,
            before=before,
            after=self._snapshot(win),
            actor=self.user,
        )
        return win


class WinEntryService(AuditableService, FilterableQueryService):
    _MODULE = "wins"
    _RESOURCE_TYPE = "win_entry"

    filterable_fields: dict[str, str] = {"team": "team__code"}
    search_fields: list[str] = ["title", "description"]
    sortable_fields: list[str] = ["title", "created_at"]
    default_ordering: list[str] = ["-created_at"]
    filter_active_by_default: bool = False

    def __init__(self, *, win: Win, **context):
        super().__init__(**context)
        self.win = win

    def get_queryset(self):
        return selectors.get_win_entries(self.win)

    def _snapshot(self, entry: WinEntry) -> dict:
        return {
            "team": entry.team.code,
            "title": entry.title,
            "description": entry.description,
        }

    def get(self, code: str, *args, **kwargs) -> WinEntry:
        obj = selectors.get_win_entry_by_code(code)
        if obj is None:
            raise NotFoundException(
                resource="WinEntry", lookup_field="code", lookup_value=code
            )
        return obj

    def _assert_win_open(self, win: Win) -> None:
        if win.status != WinStatus.OPEN:
            raise ValidationException(
                "Entries can only be added or changed while the Win is Open."
            )

    @transaction.atomic
    def create(self, *, team, title: str, description: str = "") -> WinEntry:
        self._assert_win_open(self.win)

        entry = WinEntry.objects.create(
            win=self.win,
            team=team,
            title=title,
            description=description,
            created_by=self.user,
            updated_by=self.user,
        )
        AuditService.log_create(
            module=self._MODULE,
            resource_type=self._RESOURCE_TYPE,
            resource_code=entry.code,
            after=self._snapshot(entry),
            actor=self.user,
        )
        return entry

    @transaction.atomic
    def update(self, code: str, **kwargs) -> WinEntry:
        entry = self.get(code=code)
        self._assert_win_open(entry.win)
        before = self._snapshot(entry)
        update_fields: list[str] = ["updated_by", "updated_at"]

        if "team" in kwargs:
            entry.team = kwargs["team"]
            update_fields.append("team")
        if "title" in kwargs:
            entry.title = kwargs["title"]
            update_fields.append("title")
        if "description" in kwargs:
            entry.description = kwargs["description"]
            update_fields.append("description")

        entry.updated_by = self.user
        entry.save(update_fields=update_fields)

        AuditService.log_update(
            module=self._MODULE,
            resource_type=self._RESOURCE_TYPE,
            resource_code=entry.code,
            before=before,
            after=self._snapshot(entry),
            actor=self.user,
        )
        return entry

    @transaction.atomic
    def delete(self, code: str, *args, **kwargs) -> None:
        entry = self.get(code=code)
        self._assert_win_open(entry.win)
        entry_code = entry.code
        before = self._snapshot(entry)
        entry.delete()
        AuditService.log_delete(
            module=self._MODULE,
            resource_type=self._RESOURCE_TYPE,
            resource_code=entry_code,
            before=before,
            actor=self.user,
        )


def _build_entry_options(entries: list[WinEntry]) -> list[dict]:
    """Build survey/preview display options: 'Week N: [i] Title', indexed only
    when more than one entry shares the same (team, week)."""
    key_totals: dict[tuple[int, int], int] = defaultdict(int)
    for entry in entries:
        key_totals[(entry.team_id, entry.win_id)] += 1

    counters: dict[tuple[int, int], int] = defaultdict(int)
    options = []
    for entry in entries:
        key = (entry.team_id, entry.win_id)
        counters[key] += 1
        suffix = f" [{counters[key]}]" if key_totals[key] > 1 else ""
        label = f"Week {entry.win.week_number}:{suffix} {entry.title}".strip()
        options.append(
            {
                "code": entry.code,
                "label": label,
                "team_code": entry.team.code,
                "team_name": entry.team.name,
                "week_number": entry.win.week_number,
                "title": entry.title,
                "description": entry.description,
            }
        )
    return options


def _validate_nominations(
    nominations: list[dict], *, phase: str, allowed_team_codes: set | None = None
) -> None:
    """nominations: list of {"entry": WinEntry, "category": str}.

    Phase 1 allows up to 2 nominations per (team, category); Phase 2 allows up
    to 2 per category overall. An entry can never be nominated in both
    categories on the same survey.
    """
    if phase == SurveyPhase.PHASE_1:
        team_cat_counts: dict[tuple[str, str], int] = defaultdict(int)
        for nom in nominations:
            entry = nom["entry"]
            if (
                allowed_team_codes is not None
                and entry.team.code not in allowed_team_codes
            ):
                raise ValidationException(
                    f"'{entry.title}' does not belong to your team(s)."
                )
            key = (entry.team.code, nom["category"])
            team_cat_counts[key] += 1
            if team_cat_counts[key] > _MAX_NOMINATIONS_PER_CATEGORY:
                raise ValidationException(
                    f"You may select at most {_MAX_NOMINATIONS_PER_CATEGORY} "
                    f"{nom['category']} wins per team."
                )
    else:
        cat_counts: dict[str, int] = defaultdict(int)
        for nom in nominations:
            cat_counts[nom["category"]] += 1
            if cat_counts[nom["category"]] > _MAX_NOMINATIONS_PER_CATEGORY:
                raise ValidationException(
                    f"You may select at most {_MAX_NOMINATIONS_PER_CATEGORY} "
                    f"{nom['category']} wins."
                )

    entry_categories: dict[int, set] = defaultdict(set)
    for nom in nominations:
        entry_categories[nom["entry"].pk].add(nom["category"])
    for cats in entry_categories.values():
        if len(cats) > 1:
            raise ValidationException(
                "A win cannot be selected for both Delivery and Operational Excellence."
            )


class MonthlyWinsRecipientService(AuditableService, FilterableQueryService):
    _MODULE = "wins"
    _RESOURCE_TYPE = "monthly_wins_recipient"

    filterable_fields: dict[str, str] = {"team": "team__code"}
    search_fields: list[str] = ["user__email", "user__first_name", "user__last_name"]
    sortable_fields: list[str] = ["team__name", "user__email", "created_at"]
    default_ordering: list[str] = ["team__name", "user__email"]
    filter_active_by_default: bool = False

    def get_queryset(self):
        return selectors.get_all_recipients()

    def _snapshot(self, obj: MonthlyWinsRecipient) -> dict:
        return {"team": obj.team.code, "user": obj.user.email}

    def get(self, code: str, *args, **kwargs) -> MonthlyWinsRecipient:
        obj = selectors.get_recipient_by_code(code)
        if obj is None:
            raise NotFoundException(
                resource="MonthlyWinsRecipient", lookup_field="code", lookup_value=code
            )
        return obj

    @transaction.atomic
    def create(self, *, team, user) -> MonthlyWinsRecipient:
        if selectors.recipient_exists(team.pk, user.pk):
            raise AlreadyExistsException(
                detail=f"'{user.email}' is already a recipient for '{team.name}'."
            )
        obj = MonthlyWinsRecipient.objects.create(
            team=team, user=user, created_by=self.user, updated_by=self.user
        )
        AuditService.log_create(
            module=self._MODULE,
            resource_type=self._RESOURCE_TYPE,
            resource_code=obj.code,
            after=self._snapshot(obj),
            actor=self.user,
        )
        return obj

    @transaction.atomic
    def update(self, code: str, *, team=None, user=None) -> MonthlyWinsRecipient:
        obj = self.get(code=code)
        before = self._snapshot(obj)
        new_team = team or obj.team
        new_user = user or obj.user
        if selectors.recipient_exists(new_team.pk, new_user.pk, exclude_pk=obj.pk):
            raise AlreadyExistsException(
                detail=f"'{new_user.email}' is already a recipient for "
                f"'{new_team.name}'."
            )
        obj.team = new_team
        obj.user = new_user
        obj.updated_by = self.user
        obj.save(update_fields=["team", "user", "updated_by", "updated_at"])
        AuditService.log_update(
            module=self._MODULE,
            resource_type=self._RESOURCE_TYPE,
            resource_code=obj.code,
            before=before,
            after=self._snapshot(obj),
            actor=self.user,
        )
        return obj

    @transaction.atomic
    def delete(self, code: str, *args, **kwargs) -> None:
        obj = self.get(code=code)
        obj_code = obj.code
        before = self._snapshot(obj)
        obj.delete()
        AuditService.log_delete(
            module=self._MODULE,
            resource_type=self._RESOURCE_TYPE,
            resource_code=obj_code,
            before=before,
            actor=self.user,
        )


class MonthlyWinService(AuditableService, FilterableQueryService):
    _MODULE = "wins"
    _RESOURCE_TYPE = "monthly_win"

    filterable_fields: dict[str, str] = {"status": "status"}
    search_fields: list[str] = ["name"]
    sortable_fields: list[str] = ["name", "status", "created_at"]
    default_ordering: list[str] = ["-created_at"]
    filter_active_by_default: bool = False

    def get_queryset(self):
        return selectors.get_all_monthly_wins()

    def _snapshot(self, mw: MonthlyWin) -> dict:
        return {"name": mw.name, "status": mw.status}

    def get(self, code: str, *args, **kwargs) -> MonthlyWin:
        obj = selectors.get_monthly_win_by_code(code)
        if obj is None:
            raise NotFoundException(
                resource="MonthlyWin", lookup_field="code", lookup_value=code
            )
        return obj

    @transaction.atomic
    def create(
        self, *, name: str, win_codes: list[str], phase1_deadline=None
    ) -> MonthlyWin:
        if not name or not name.strip():
            raise ValidationException("Name is required.")
        wins = list(Win.objects.filter(code__in=win_codes))
        if not wins:
            raise ValidationException("Select at least one week.")

        mw = MonthlyWin.objects.create(
            name=name.strip(),
            phase1_deadline=phase1_deadline,
            created_by=self.user,
            updated_by=self.user,
        )
        mw.wins.set(wins)
        AuditService.log_create(
            module=self._MODULE,
            resource_type=self._RESOURCE_TYPE,
            resource_code=mw.code,
            after=self._snapshot(mw),
            actor=self.user,
        )
        return mw

    def update(self, pk, *args, **kwargs):
        raise NotImplementedError

    @transaction.atomic
    def delete(self, code: str, *args, **kwargs) -> None:
        mw = self.get(code=code)
        if mw.status != MonthlyWinStatus.DRAFT:
            raise ValidationException("Only a Draft Monthly Win can be deleted.")
        mw_code = mw.code
        before = self._snapshot(mw)
        mw.delete()
        AuditService.log_delete(
            module=self._MODULE,
            resource_type=self._RESOURCE_TYPE,
            resource_code=mw_code,
            before=before,
            actor=self.user,
        )

    def get_preview_teams(self, code: str) -> list[dict]:
        mw = self.get(code=code)
        win_ids = list(mw.wins.values_list("id", flat=True))
        team_ids = (
            WinEntry.objects.filter(win_id__in=win_ids)
            .values_list("team_id", flat=True)
            .distinct()
        )
        from apps.teams.models import Team

        return [
            {"code": t.code, "name": t.name}
            for t in Team.objects.filter(pk__in=team_ids).order_by("name")
        ]

    def get_preview_survey_data(
        self, code: str, *, phase: str, team_code: str | None = None
    ) -> dict:
        mw = self.get(code=code)
        if phase == SurveyPhase.PHASE_1:
            if not team_code:
                raise ValidationException("A team is required for the Phase 1 preview.")
            from apps.teams.selectors import get_team_by_code

            team = get_team_by_code(team_code)
            if team is None:
                raise NotFoundException(
                    resource="Team", lookup_field="code", lookup_value=team_code
                )
            win_ids = list(mw.wins.values_list("id", flat=True))
            entries = list(
                WinEntry.objects.filter(win_id__in=win_ids, team=team)
                .select_related("win", "team")
                .order_by("win__week_number", "created_at")
            )
        else:
            entry_ids = selectors.get_phase1_nominated_entry_ids(mw)
            entries = list(
                WinEntry.objects.filter(pk__in=entry_ids)
                .select_related("win", "team")
                .order_by("team__name", "win__week_number", "created_at")
            )

        return {
            "phase": phase,
            "entries": _build_entry_options(entries),
            "categories": [
                {"value": v, "label": lbl} for v, lbl in WinCategory.choices
            ],
        }

    @transaction.atomic
    def launch_phase1(self, code: str) -> MonthlyWin:
        from apps.wins.engine import MonthlyWinEngine

        mw = self.get(code=code)
        if mw.status != MonthlyWinStatus.DRAFT:
            raise ValidationException("Phase 1 can only be launched from Draft status.")

        win_ids = list(mw.wins.values_list("id", flat=True))
        if not win_ids:
            raise ValidationException(
                "Select at least one week before launching Phase 1."
            )

        team_ids = (
            WinEntry.objects.filter(win_id__in=win_ids)
            .values_list("team_id", flat=True)
            .distinct()
        )
        recipients = selectors.get_recipients_for_teams(list(team_ids))
        if not recipients.exists():
            raise ValidationException(
                "No recipients are configured for the teams with wins in the "
                "selected weeks."
            )

        teams_by_user = defaultdict(list)
        for recipient in recipients:
            teams_by_user[recipient.user_id].append(recipient.team)

        for user_id, teams in teams_by_user.items():
            survey = MonthlyWinSurvey.objects.create(
                monthly_win=mw,
                phase=SurveyPhase.PHASE_1,
                recipient_id=user_id,
            )
            survey.teams.set(teams)

        mw.status = MonthlyWinStatus.PHASE_1_OPEN
        mw.updated_by = self.user
        mw.save(update_fields=["status", "updated_by", "updated_at"])

        MonthlyWinEngine.send_phase_emails(mw, str(SurveyPhase.PHASE_1))
        return mw

    @transaction.atomic
    def complete_phase1(self, code: str) -> MonthlyWin:
        mw = self.get(code=code)
        if mw.status != MonthlyWinStatus.PHASE_1_OPEN:
            raise ValidationException("Phase 1 is not currently open.")
        mw.status = MonthlyWinStatus.PHASE_1_CLOSED
        mw.updated_by = self.user
        mw.save(update_fields=["status", "updated_by", "updated_at"])
        return mw

    @transaction.atomic
    def launch_phase2(self, code: str) -> MonthlyWin:
        from apps.wins.engine import MonthlyWinEngine

        mw = self.get(code=code)
        if mw.status != MonthlyWinStatus.PHASE_1_CLOSED:
            raise ValidationException(
                "Phase 2 can only be launched after Phase 1 is closed."
            )

        nominated_ids = list(selectors.get_phase1_nominated_entry_ids(mw))
        if not nominated_ids:
            raise ValidationException("No wins were nominated in Phase 1.")

        recipient_user_ids = (
            MonthlyWinSurvey.objects.filter(monthly_win=mw, phase=SurveyPhase.PHASE_1)
            .values_list("recipient_id", flat=True)
            .distinct()
        )
        for user_id in recipient_user_ids:
            MonthlyWinSurvey.objects.create(
                monthly_win=mw,
                phase=SurveyPhase.PHASE_2,
                recipient_id=user_id,
            )

        mw.status = MonthlyWinStatus.PHASE_2_OPEN
        mw.updated_by = self.user
        mw.save(update_fields=["status", "updated_by", "updated_at"])

        MonthlyWinEngine.send_phase_emails(mw, str(SurveyPhase.PHASE_2))
        return mw

    @transaction.atomic
    def complete_phase2(self, code: str) -> MonthlyWin:
        mw = self.get(code=code)
        if mw.status != MonthlyWinStatus.PHASE_2_OPEN:
            raise ValidationException("Phase 2 is not currently open.")
        mw.status = MonthlyWinStatus.PHASE_2_CLOSED
        mw.updated_by = self.user
        mw.save(update_fields=["status", "updated_by", "updated_at"])
        return mw

    @transaction.atomic
    def declare_winners(self, code: str) -> MonthlyWin:
        from apps.wins.models import MonthlyWinResult

        mw = self.get(code=code)
        if mw.status != MonthlyWinStatus.PHASE_2_CLOSED:
            raise ValidationException(
                "Winners can only be declared after Phase 2 is closed."
            )

        vote_counts: dict[tuple[int, str], int] = defaultdict(int)
        noms = MonthlyWinSurveyNomination.objects.filter(
            survey__monthly_win=mw,
            survey__phase=SurveyPhase.PHASE_2,
            is_dismissed=False,
        ).values("entry_id", "category")
        for nom in noms:
            vote_counts[(nom["entry_id"], nom["category"])] += 1

        MonthlyWinResult.objects.filter(monthly_win=mw).delete()
        for category, _label in WinCategory.choices:
            cat_votes = sorted(
                (
                    (entry_id, count)
                    for (entry_id, cat), count in vote_counts.items()
                    if cat == category
                ),
                key=lambda x: -x[1],
            )
            for rank, (entry_id, count) in enumerate(cat_votes[:2], start=1):
                MonthlyWinResult.objects.create(
                    monthly_win=mw,
                    entry_id=entry_id,
                    category=category,
                    rank=rank,
                    vote_count=count,
                )

        mw.status = MonthlyWinStatus.WINS_DECLARED
        mw.updated_by = self.user
        mw.save(update_fields=["status", "updated_by", "updated_at"])
        return mw

    def get_admin_survey_data(self, survey_code: str) -> dict:
        survey = selectors.get_survey_by_code(survey_code)
        if survey is None:
            raise NotFoundException(
                resource="MonthlyWinSurvey",
                lookup_field="code",
                lookup_value=survey_code,
            )
        mw = survey.monthly_win

        if survey.phase == SurveyPhase.PHASE_1:
            team_ids = list(survey.teams.values_list("id", flat=True))
            win_ids = list(mw.wins.values_list("id", flat=True))
            entries = list(
                WinEntry.objects.filter(win_id__in=win_ids, team_id__in=team_ids)
                .select_related("win", "team")
                .order_by("team__name", "win__week_number", "created_at")
            )
        else:
            entry_ids = selectors.get_phase1_nominated_entry_ids(mw)
            entries = list(
                WinEntry.objects.filter(pk__in=entry_ids)
                .select_related("win", "team")
                .order_by("team__name", "win__week_number", "created_at")
            )

        existing = [
            {"entry_code": n.entry.code, "category": n.category}
            for n in survey.nominations.select_related("entry").all()
        ]

        return {
            "code": survey.code,
            "phase": survey.phase,
            "status": survey.status,
            "recipient_name": survey.recipient.get_full_name()
            or survey.recipient.email,
            "team_names": [t.name for t in survey.teams.all()],
            "entries": _build_entry_options(entries),
            "categories": [
                {"value": v, "label": lbl} for v, lbl in WinCategory.choices
            ],
            "existing_nominations": existing,
        }

    @transaction.atomic
    def override_survey(
        self, survey_code: str, nominations_data: list[dict]
    ) -> MonthlyWinSurvey:
        survey = selectors.get_survey_by_code(survey_code)
        if survey is None:
            raise NotFoundException(
                resource="MonthlyWinSurvey",
                lookup_field="code",
                lookup_value=survey_code,
            )
        if survey.status != SurveyStatus.PENDING:
            raise ValidationException("Only a pending survey can be overridden.")

        allowed_team_codes = None
        if survey.phase == SurveyPhase.PHASE_1:
            allowed_team_codes = {t.code for t in survey.teams.all()}

        resolved = []
        for item in nominations_data:
            entry = selectors.get_win_entry_by_code(item["entry_code"])
            if entry is None:
                raise NotFoundException(
                    resource="WinEntry",
                    lookup_field="code",
                    lookup_value=item["entry_code"],
                )
            resolved.append({"entry": entry, "category": item["category"]})

        _validate_nominations(
            resolved, phase=survey.phase, allowed_team_codes=allowed_team_codes
        )

        survey.nominations.all().delete()
        for item in resolved:
            MonthlyWinSurveyNomination.objects.create(
                survey=survey, entry=item["entry"], category=item["category"]
            )

        survey.status = SurveyStatus.OVERRIDDEN
        survey.completed_at = timezone.now()
        survey.save(update_fields=["status", "completed_at", "updated_at"])
        return survey


class SurveyService:
    """Public, unauthenticated token-based survey access for recipients."""

    @staticmethod
    def get_survey_data(token) -> dict:
        survey = selectors.get_survey_by_token(token)
        if survey is None:
            raise NotFoundException(
                resource="Survey", lookup_field="token", lookup_value=str(token)
            )
        mw = survey.monthly_win

        if survey.phase == SurveyPhase.PHASE_1:
            team_ids = list(survey.teams.values_list("id", flat=True))
            win_ids = list(mw.wins.values_list("id", flat=True))
            entries = list(
                WinEntry.objects.filter(win_id__in=win_ids, team_id__in=team_ids)
                .select_related("win", "team")
                .order_by("team__name", "win__week_number", "created_at")
            )
        else:
            entry_ids = selectors.get_phase1_nominated_entry_ids(mw)
            entries = list(
                WinEntry.objects.filter(pk__in=entry_ids)
                .select_related("win", "team")
                .order_by("team__name", "win__week_number", "created_at")
            )

        existing = [
            {"entry_code": n.entry.code, "category": n.category}
            for n in survey.nominations.select_related("entry").all()
        ]

        return {
            "monthly_win_name": mw.name,
            "phase": survey.phase,
            "status": survey.status,
            "recipient_name": survey.recipient.get_full_name()
            or survey.recipient.email,
            "team_names": [t.name for t in survey.teams.all()],
            "deadline": (
                mw.phase1_deadline
                if survey.phase == SurveyPhase.PHASE_1
                else mw.phase2_deadline
            ),
            "entries": _build_entry_options(entries),
            "categories": [
                {"value": v, "label": lbl} for v, lbl in WinCategory.choices
            ],
            "existing_nominations": existing,
        }

    @staticmethod
    @transaction.atomic
    def submit_survey(token, nominations_data: list[dict]) -> MonthlyWinSurvey:
        survey = selectors.get_survey_by_token(token)
        if survey is None:
            raise NotFoundException(
                resource="Survey", lookup_field="token", lookup_value=str(token)
            )
        if survey.status != SurveyStatus.PENDING:
            raise ValidationException(
                "This survey has already been completed or overridden."
            )

        allowed_team_codes = None
        if survey.phase == SurveyPhase.PHASE_1:
            allowed_team_codes = {t.code for t in survey.teams.all()}

        resolved = []
        for item in nominations_data:
            entry = selectors.get_win_entry_by_code(item["entry_code"])
            if entry is None:
                raise NotFoundException(
                    resource="WinEntry",
                    lookup_field="code",
                    lookup_value=item["entry_code"],
                )
            resolved.append({"entry": entry, "category": item["category"]})

        _validate_nominations(
            resolved, phase=survey.phase, allowed_team_codes=allowed_team_codes
        )

        survey.nominations.all().delete()
        for item in resolved:
            MonthlyWinSurveyNomination.objects.create(
                survey=survey, entry=item["entry"], category=item["category"]
            )

        survey.status = SurveyStatus.COMPLETED
        survey.completed_at = timezone.now()
        survey.save(update_fields=["status", "completed_at", "updated_at"])
        return survey
