from django.db.models import QuerySet

from apps.wins.constants import SurveyPhase
from apps.wins.models import (
    MonthlyWin,
    MonthlyWinResult,
    MonthlyWinsRecipient,
    MonthlyWinSurvey,
    MonthlyWinSurveyNomination,
    Win,
    WinEntry,
)


def get_all_wins() -> QuerySet[Win]:
    return (
        Win.objects.select_related("created_by", "updated_by", "reviewed_by")
        .prefetch_related("entries__team")
        .all()
    )


def get_win_by_code(code: str) -> Win | None:
    try:
        return (
            Win.objects.select_related("created_by", "updated_by", "reviewed_by")
            .prefetch_related("entries__team")
            .get(code=code)
        )
    except Win.DoesNotExist:
        return None


def week_number_exists(week_number: int) -> bool:
    return Win.objects.filter(week_number=week_number).exists()


def get_next_week_number(start_number: int) -> int:
    last = Win.objects.order_by("-week_number").first()
    return (last.week_number + 1) if last else start_number


def get_win_entries(win: Win) -> QuerySet[WinEntry]:
    return WinEntry.objects.select_related("team", "created_by", "updated_by").filter(
        win=win
    )


def get_win_entry_by_code(code: str) -> WinEntry | None:
    try:
        return WinEntry.objects.select_related("win", "team").get(code=code)
    except WinEntry.DoesNotExist:
        return None


def get_all_recipients() -> QuerySet[MonthlyWinsRecipient]:
    return MonthlyWinsRecipient.objects.select_related(
        "team", "user", "created_by", "updated_by"
    ).all()


def get_recipient_by_code(code: str) -> MonthlyWinsRecipient | None:
    try:
        return MonthlyWinsRecipient.objects.select_related("team", "user").get(
            code=code
        )
    except MonthlyWinsRecipient.DoesNotExist:
        return None


def recipient_exists(team_id: int, user_id: int, exclude_pk: int | None = None) -> bool:
    qs = MonthlyWinsRecipient.objects.filter(team_id=team_id, user_id=user_id)
    if exclude_pk is not None:
        qs = qs.exclude(pk=exclude_pk)
    return qs.exists()


def get_recipients_for_teams(team_ids) -> QuerySet[MonthlyWinsRecipient]:
    return MonthlyWinsRecipient.objects.select_related("team", "user").filter(
        team_id__in=team_ids
    )


def get_all_monthly_wins() -> QuerySet[MonthlyWin]:
    return (
        MonthlyWin.objects.select_related("created_by", "updated_by")
        .prefetch_related("wins")
        .all()
    )


def get_monthly_win_by_code(code: str) -> MonthlyWin | None:
    try:
        return (
            MonthlyWin.objects.select_related("created_by", "updated_by")
            .prefetch_related("wins")
            .get(code=code)
        )
    except MonthlyWin.DoesNotExist:
        return None


def get_monthly_win_surveys(monthly_win: MonthlyWin) -> QuerySet[MonthlyWinSurvey]:
    return (
        MonthlyWinSurvey.objects.select_related("recipient")
        .prefetch_related("teams")
        .filter(monthly_win=monthly_win)
    )


def get_survey_by_code(code: str) -> MonthlyWinSurvey | None:
    try:
        return (
            MonthlyWinSurvey.objects.select_related("monthly_win", "recipient")
            .prefetch_related("teams")
            .get(code=code)
        )
    except MonthlyWinSurvey.DoesNotExist:
        return None


def get_survey_by_token(token) -> MonthlyWinSurvey | None:
    try:
        return (
            MonthlyWinSurvey.objects.select_related("monthly_win", "recipient")
            .prefetch_related("teams")
            .get(token=token)
        )
    except (MonthlyWinSurvey.DoesNotExist, ValueError, TypeError):
        return None


def get_monthly_win_results(monthly_win: MonthlyWin) -> QuerySet[MonthlyWinResult]:
    return MonthlyWinResult.objects.select_related("entry__team", "entry__win").filter(
        monthly_win=monthly_win
    )


def get_phase1_nominated_entry_ids(monthly_win: MonthlyWin):
    return (
        MonthlyWinSurveyNomination.objects.filter(
            survey__monthly_win=monthly_win,
            survey__phase=SurveyPhase.PHASE_1,
            is_dismissed=False,
        )
        .values_list("entry_id", flat=True)
        .distinct()
    )
