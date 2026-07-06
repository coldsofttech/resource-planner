from django.http import HttpResponse
from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request

from apps.configurations.selectors import Wins as WinsConfigSelector
from apps.configurations.selectors import get_config_value
from apps.configurations.services import AdminConfigurationService
from apps.core.exceptions import NotFoundException
from apps.core.permissions import HasPermission
from apps.core.viewsets import BaseViewSet
from apps.wins.engine import (
    MonthlyWinResultsEngine,
    WinEntrySuggestEngine,
    WinReviewEngine,
)
from apps.wins.serializers import (
    MonthlyWinCreateSerializer,
    MonthlyWinDetailSerializer,
    MonthlyWinListSerializer,
    MonthlyWinsRecipientCreateSerializer,
    MonthlyWinsRecipientListSerializer,
    MonthlyWinsRecipientUpdateSerializer,
    MonthlyWinSurveyListSerializer,
    MonthlyWinSurveySubmitSerializer,
    WinCreateSerializer,
    WinDetailSerializer,
    WinEntryCreateSerializer,
    WinEntryListSerializer,
    WinEntrySuggestSerializer,
    WinEntryUpdateSerializer,
    WinListSerializer,
    WinsConfigSerializer,
    WinsConfigUpdateSerializer,
)
from apps.wins.services import (
    MonthlyWinService,
    MonthlyWinsRecipientService,
    SurveyService,
    WinEntryService,
    WinService,
)

_WINS_CONFIG_MAP = {
    "win_start_number": "WIN_START_NUMBER",
    "wins_review_email_recipients": "WINS_REVIEW_EMAIL_RECIPIENTS",
}


def _current_wins_config() -> dict:
    return {
        "win_start_number": WinsConfigSelector.get_start_number(),
        "wins_review_email_recipients": get_config_value(
            "WINS_REVIEW_EMAIL_RECIPIENTS"
        ),
    }


def _resolve_member(code: str):
    from apps.users.selectors import get_member_by_code

    profile = get_member_by_code(code)
    if profile is None:
        raise NotFoundException(
            resource="Member", lookup_field="code", lookup_value=code
        )
    return profile.user


def _resolve_team(team_code: str):
    from apps.teams.selectors import get_team_by_code

    team = get_team_by_code(team_code)
    if team is None:
        raise NotFoundException(
            resource="Team", lookup_field="code", lookup_value=team_code
        )
    return team


@extend_schema(tags=["Wins"])
class WinViewSet(BaseViewSet):
    service_class = WinService

    def get_permissions(self):
        action_perms = {
            "list": "wins.view_win",
            "retrieve": "wins.view_win",
            "create": "wins.add_win",
            "destroy": "wins.delete_win",
            "review_complete": "wins.review_complete_win",
            "review_pdf": "wins.review_complete_win",
            "send_review": "wins.review_complete_win",
            "options": "wins.view_win",
        }
        from rest_framework.permissions import IsAuthenticated

        perm = action_perms.get(self.action)
        if perm:
            return [IsAuthenticated(), HasPermission(perm)]
        return [IsAuthenticated()]

    @extend_schema(
        summary="List Weekly Win options",
        description=(
            "Returns a lightweight list of weeks (code + label) for use in "
            "picker fields such as the Monthly Wins week selector."
        ),
        responses={200: OpenApiResponse(description="List of week options.")},
    )
    def options(self, request: Request):
        """GET /wins/options/"""
        wins = self.service.get_queryset().order_by("-week_number")
        data = [
            {
                "code": w.code,
                "name": f"Week {w.week_number} ({w.start_date} to {w.end_date})",
            }
            for w in wins
        ]
        return self.response(data=data)

    def get_list_serializer_class(self):
        return WinListSerializer

    def get_retrieve_serializer_class(self):
        return WinDetailSerializer

    def get_create_serializer_class(self):
        return WinCreateSerializer

    def get_create_response_serializer_class(self):
        return WinDetailSerializer

    @extend_schema(
        summary="List Weekly Wins",
        description="Returns a paginated list of Weekly Win weeks.",
        responses={200: WinListSerializer(many=True)},
    )
    def list(self, request: Request):
        """GET /wins/"""
        return super().list(request)

    @extend_schema(
        summary="Create a new Weekly Win week",
        request=WinCreateSerializer,
        responses={201: WinDetailSerializer},
    )
    def create(self, request: Request):
        """POST /wins/"""
        return super().create(request)

    @extend_schema(
        summary="Retrieve a Weekly Win",
        responses={
            200: WinDetailSerializer,
            404: OpenApiResponse(description="Win not found."),
        },
    )
    def retrieve(self, request: Request, code=None):
        """GET /wins/<code>/"""
        obj = self.service.get(code=code)
        serializer = WinDetailSerializer(obj, context=self.get_serializer_context())
        return self.response(data=serializer.data)

    @extend_schema(
        summary="Delete a Weekly Win",
        responses={
            204: OpenApiResponse(description="Win deleted successfully."),
            404: OpenApiResponse(description="Win not found."),
        },
    )
    def destroy(self, request: Request, code=None):
        """DELETE /wins/<code>/"""
        self.service.delete(code=code)
        return self.response(
            message=self.get_delete_custom_message(),
            status_code=self.get_delete_status_code(),
        )

    @extend_schema(
        summary="Mark a Weekly Win as review complete",
        responses={
            200: WinDetailSerializer,
            404: OpenApiResponse(description="Win not found."),
            422: OpenApiResponse(description="Win is not in Open status."),
        },
    )
    def review_complete(self, request: Request, code=None):
        """POST /wins/<code>/review-complete/"""
        win = self.service.review_complete(code=code)
        data = WinDetailSerializer(win, context=self.get_serializer_context()).data
        return self.response(data=data, message="Win marked as review complete.")

    @extend_schema(
        summary="Download the Weekly Win review PDF",
        responses={200: OpenApiResponse(description="PDF file attachment.")},
    )
    def review_pdf(self, request: Request, code=None):
        """GET /wins/<code>/review-pdf/"""
        win = self.service.get(code=code)
        content = WinReviewEngine.build_pdf(win)
        response = HttpResponse(content, content_type="application/pdf")
        response["Content-Disposition"] = (
            f"attachment; filename=weekly-win-week-{win.week_number}.pdf"
        )
        return response

    @extend_schema(
        summary="Send the Weekly Win review email",
        responses={
            200: OpenApiResponse(description="Review email sent."),
            422: OpenApiResponse(description="No recipients configured."),
        },
    )
    def send_review(self, request: Request, code=None):
        """POST /wins/<code>/send-review/"""
        win = self.service.get(code=code)
        WinReviewEngine.send_review_email(win)
        return self.response(message="Review email sent successfully.")


@extend_schema(tags=["Wins"])
class WinEntryViewSet(BaseViewSet):
    def get_permissions(self):
        from rest_framework.permissions import IsAuthenticated

        action_perms = {
            "list": "wins.view_winentry",
            "retrieve": "wins.view_winentry",
            "create": "wins.add_winentry",
            "partial_update": "wins.change_winentry",
            "destroy": "wins.delete_winentry",
            "suggest": "wins.add_winentry",
        }
        perm = action_perms.get(self.action)
        if perm:
            return [IsAuthenticated(), HasPermission(perm)]
        return [IsAuthenticated()]

    def _get_win(self, win_code: str):
        return WinService(user=self.request.user, request=self.request).get(
            code=win_code
        )

    def _entry_service(self, win_code: str) -> WinEntryService:
        win = self._get_win(win_code)
        return WinEntryService(win=win, user=self.request.user, request=self.request)

    @extend_schema(
        summary="List entries for a Weekly Win",
        responses={200: WinEntryListSerializer(many=True)},
    )
    def list(self, request: Request, win_code=None):
        """GET /wins/<win_code>/entries/"""
        params = self.get_list_params(request)
        result = self._entry_service(win_code).list(params=params)
        return self.paginated_response(
            result=result, serializer_class=WinEntryListSerializer
        )

    @extend_schema(
        summary="Add an entry to a Weekly Win",
        request=WinEntryCreateSerializer,
        responses={
            201: WinEntryListSerializer,
            422: OpenApiResponse(description="Win is not in Open status."),
        },
    )
    def create(self, request: Request, win_code=None):
        """POST /wins/<win_code>/entries/"""
        serializer = WinEntryCreateSerializer(
            data=request.data, context=self.get_serializer_context()
        )
        serializer.is_valid(raise_exception=True)
        team = _resolve_team(serializer.validated_data["team"])
        entry = self._entry_service(win_code).create(
            team=team,
            title=serializer.validated_data["title"],
            description=serializer.validated_data.get("description", ""),
        )
        data = WinEntryListSerializer(entry, context=self.get_serializer_context()).data
        return self.response(
            data=data,
            message="Entry added successfully.",
            status_code=status.HTTP_201_CREATED,
        )

    @extend_schema(
        summary="Update a Weekly Win entry",
        request=WinEntryUpdateSerializer,
        responses={
            200: WinEntryListSerializer,
            404: OpenApiResponse(description="Entry not found."),
            422: OpenApiResponse(description="Win is not in Open status."),
        },
    )
    def partial_update(self, request: Request, win_code=None, code=None):
        """PATCH /wins/<win_code>/entries/<code>/"""
        serializer = WinEntryUpdateSerializer(
            data=request.data, partial=True, context=self.get_serializer_context()
        )
        serializer.is_valid(raise_exception=True)
        validated = dict(serializer.validated_data)
        if "team" in validated:
            validated["team"] = _resolve_team(validated["team"])
        entry = self._entry_service(win_code).update(code=code, **validated)
        data = WinEntryListSerializer(entry, context=self.get_serializer_context()).data
        return self.response(data=data, message="Entry updated successfully.")

    @extend_schema(
        summary="Delete a Weekly Win entry",
        responses={
            204: OpenApiResponse(description="Entry deleted successfully."),
            404: OpenApiResponse(description="Entry not found."),
            422: OpenApiResponse(description="Win is not in Open status."),
        },
    )
    def destroy(self, request: Request, win_code=None, code=None):
        """DELETE /wins/<win_code>/entries/<code>/"""
        self._entry_service(win_code).delete(code=code)
        return self.response(
            message="Entry deleted successfully.",
            status_code=status.HTTP_204_NO_CONTENT,
        )

    @extend_schema(
        summary="Suggest a title/description via AI",
        description=(
            "Uses AI to turn structured win details into a suggested title and "
            "description. Available only when AI_ENABLED=true."
        ),
        request=WinEntrySuggestSerializer,
        responses={
            200: OpenApiResponse(description="Suggested title + description."),
            503: OpenApiResponse(description="AI suggestions are not enabled."),
        },
    )
    def suggest(self, request: Request, win_code=None):
        """POST /wins/<win_code>/entries/suggest/"""
        serializer = WinEntrySuggestSerializer(
            data=request.data, context=self.get_serializer_context()
        )
        serializer.is_valid(raise_exception=True)
        suggestion = WinEntrySuggestEngine.suggest(**serializer.validated_data)
        return self.response(data=suggestion, message="Suggestion generated.")


@extend_schema(tags=["Wins: Monthly"])
class MonthlyWinsRecipientViewSet(BaseViewSet):
    service_class = MonthlyWinsRecipientService

    def get_permissions(self):
        from rest_framework.permissions import IsAuthenticated

        action_perms = {
            "list": "wins.view_monthlywinsrecipient",
            "retrieve": "wins.view_monthlywinsrecipient",
            "create": "wins.add_monthlywinsrecipient",
            "partial_update": "wins.change_monthlywinsrecipient",
            "destroy": "wins.delete_monthlywinsrecipient",
        }
        perm = action_perms.get(self.action)
        if perm:
            return [IsAuthenticated(), HasPermission(perm)]
        return [IsAuthenticated()]

    def get_list_serializer_class(self):
        return MonthlyWinsRecipientListSerializer

    def get_retrieve_serializer_class(self):
        return MonthlyWinsRecipientListSerializer

    def get_create_serializer_class(self):
        return MonthlyWinsRecipientCreateSerializer

    def get_update_serializer_class(self):
        return MonthlyWinsRecipientUpdateSerializer

    @extend_schema(
        summary="List Monthly Wins recipients",
        responses={200: MonthlyWinsRecipientListSerializer(many=True)},
    )
    def list(self, request: Request):
        """GET /wins/monthly/recipients/"""
        return super().list(request)

    @extend_schema(
        summary="Add a Monthly Wins recipient",
        request=MonthlyWinsRecipientCreateSerializer,
        responses={
            201: MonthlyWinsRecipientListSerializer,
            409: OpenApiResponse(description="Already a recipient for this team."),
        },
    )
    def create(self, request: Request):
        """POST /wins/monthly/recipients/"""
        serializer = MonthlyWinsRecipientCreateSerializer(
            data=request.data, context=self.get_serializer_context()
        )
        serializer.is_valid(raise_exception=True)
        team = _resolve_team(serializer.validated_data["team"])
        user = _resolve_member(serializer.validated_data["user"])
        obj = self.service.create(team=team, user=user)
        data = MonthlyWinsRecipientListSerializer(
            obj, context=self.get_serializer_context()
        ).data
        return self.response(
            data=data,
            message="Recipient added successfully.",
            status_code=status.HTTP_201_CREATED,
        )

    @extend_schema(
        summary="Update a Monthly Wins recipient",
        request=MonthlyWinsRecipientUpdateSerializer,
        responses={
            200: MonthlyWinsRecipientListSerializer,
            404: OpenApiResponse(description="Recipient not found."),
        },
    )
    def partial_update(self, request: Request, code=None):
        """PATCH /wins/monthly/recipients/<code>/"""
        serializer = MonthlyWinsRecipientUpdateSerializer(
            data=request.data, partial=True, context=self.get_serializer_context()
        )
        serializer.is_valid(raise_exception=True)
        validated = dict(serializer.validated_data)
        if "team" in validated:
            validated["team"] = _resolve_team(validated["team"])
        if "user" in validated:
            validated["user"] = _resolve_member(validated["user"])
        obj = self.service.update(code=code, **validated)
        data = MonthlyWinsRecipientListSerializer(
            obj, context=self.get_serializer_context()
        ).data
        return self.response(data=data, message="Recipient updated successfully.")

    @extend_schema(
        summary="Remove a Monthly Wins recipient",
        responses={
            204: OpenApiResponse(description="Recipient removed."),
            404: OpenApiResponse(description="Recipient not found."),
        },
    )
    def destroy(self, request: Request, code=None):
        """DELETE /wins/monthly/recipients/<code>/"""
        self.service.delete(code=code)
        return self.response(
            message="Recipient removed successfully.",
            status_code=status.HTTP_204_NO_CONTENT,
        )


@extend_schema(tags=["Wins: Monthly"])
class MonthlyWinViewSet(BaseViewSet):
    service_class = MonthlyWinService

    def get_permissions(self):
        from rest_framework.permissions import IsAuthenticated

        manage_actions = (
            "launch_phase1",
            "complete_phase1",
            "launch_phase2",
            "complete_phase2",
            "declare_winners",
            "survey_admin_data",
            "override_survey",
            "results_pdf",
            "send_results",
        )
        action_perms = {
            "list": "wins.view_monthlywin",
            "retrieve": "wins.view_monthlywin",
            "create": "wins.add_monthlywin",
            "destroy": "wins.delete_monthlywin",
            "preview_teams": "wins.view_monthlywin",
            "preview_survey": "wins.view_monthlywin",
            "surveys": "wins.view_monthlywin",
            "results": "wins.view_monthlywin",
            "options": "wins.view_monthlywin",
        }
        for action in manage_actions:
            action_perms[action] = "wins.manage_monthlywin"

        perm = action_perms.get(self.action)
        if perm:
            return [IsAuthenticated(), HasPermission(perm)]
        return [IsAuthenticated()]

    def get_list_serializer_class(self):
        return MonthlyWinListSerializer

    def get_retrieve_serializer_class(self):
        return MonthlyWinDetailSerializer

    def get_create_serializer_class(self):
        return MonthlyWinCreateSerializer

    def get_create_response_serializer_class(self):
        return MonthlyWinDetailSerializer

    @extend_schema(
        summary="List Monthly Win options",
        description=(
            "Returns a lightweight list of Monthly Wins (code + label) for use "
            "in picker fields such as the Monthly Wins report selector."
        ),
        responses={200: OpenApiResponse(description="List of Monthly Win options.")},
    )
    def options(self, request: Request):
        """GET /wins/monthly/options/"""
        monthly_wins = self.service.get_queryset().order_by("-created_at")
        data = [{"code": mw.code, "name": mw.name} for mw in monthly_wins]
        return self.response(data=data)

    @extend_schema(
        summary="List Monthly Wins",
        responses={200: MonthlyWinListSerializer(many=True)},
    )
    def list(self, request: Request):
        """GET /wins/monthly/"""
        return super().list(request)

    @extend_schema(
        summary="Create a Monthly Win",
        request=MonthlyWinCreateSerializer,
        responses={201: MonthlyWinDetailSerializer},
    )
    def create(self, request: Request):
        """POST /wins/monthly/"""
        serializer = MonthlyWinCreateSerializer(
            data=request.data, context=self.get_serializer_context()
        )
        serializer.is_valid(raise_exception=True)
        mw = self.service.create(
            name=serializer.validated_data["name"],
            win_codes=serializer.validated_data["win_codes"],
            phase1_deadline=serializer.validated_data.get("phase1_deadline"),
        )
        data = MonthlyWinDetailSerializer(
            mw, context=self.get_serializer_context()
        ).data
        return self.response(
            data=data,
            message="Monthly Win created successfully.",
            status_code=status.HTTP_201_CREATED,
        )

    @extend_schema(
        summary="Retrieve a Monthly Win",
        responses={
            200: MonthlyWinDetailSerializer,
            404: OpenApiResponse(description="Monthly Win not found."),
        },
    )
    def retrieve(self, request: Request, code=None):
        """GET /wins/monthly/<code>/"""
        obj = self.service.get(code=code)
        data = MonthlyWinDetailSerializer(
            obj, context=self.get_serializer_context()
        ).data
        return self.response(data=data)

    @extend_schema(
        summary="Delete a Monthly Win",
        responses={
            204: OpenApiResponse(description="Monthly Win deleted successfully."),
            404: OpenApiResponse(description="Monthly Win not found."),
            422: OpenApiResponse(description="Only a Draft Win can be deleted."),
        },
    )
    def destroy(self, request: Request, code=None):
        """DELETE /wins/monthly/<code>/"""
        self.service.delete(code=code)
        return self.response(
            message="Monthly Win deleted successfully.",
            status_code=status.HTTP_204_NO_CONTENT,
        )

    @extend_schema(
        summary="List teams available for the Phase 1 preview",
        responses={200: OpenApiResponse(description="List of teams.")},
    )
    def preview_teams(self, request: Request, code=None):
        """GET /wins/monthly/<code>/preview-teams/"""
        teams = self.service.get_preview_teams(code)
        return self.response(data=teams)

    @extend_schema(
        summary="Preview a Phase 1 or Phase 2 survey (read-only)",
        parameters=[
            OpenApiParameter(
                name="phase",
                type=str,
                location=OpenApiParameter.QUERY,
                required=True,
            ),
            OpenApiParameter(
                name="team",
                type=str,
                location=OpenApiParameter.QUERY,
                required=False,
                description="Required when phase=phase_1.",
            ),
        ],
        responses={200: OpenApiResponse(description="Preview survey data.")},
    )
    def preview_survey(self, request: Request, code=None):
        """GET /wins/monthly/<code>/preview-survey/?phase=phase_1&team=TEAM-1"""
        phase = request.query_params.get("phase", "")
        team_code = request.query_params.get("team")
        data = self.service.get_preview_survey_data(
            code, phase=phase, team_code=team_code
        )
        return self.response(data=data)

    @extend_schema(
        summary="Launch Phase 1",
        description="Creates one survey per recipient and emails the survey link.",
        responses={
            200: MonthlyWinDetailSerializer,
            422: OpenApiResponse(description="Cannot launch Phase 1."),
        },
    )
    def launch_phase1(self, request: Request, code=None):
        """POST /wins/monthly/<code>/launch-phase1/"""
        mw = self.service.launch_phase1(code)
        data = MonthlyWinDetailSerializer(
            mw, context=self.get_serializer_context()
        ).data
        return self.response(
            data=data, message="Phase 1 launched. Survey emails have been sent."
        )

    @extend_schema(
        summary="Close Phase 1",
        responses={
            200: MonthlyWinDetailSerializer,
            422: OpenApiResponse(description="Phase 1 is not open."),
        },
    )
    def complete_phase1(self, request: Request, code=None):
        """POST /wins/monthly/<code>/complete-phase1/"""
        mw = self.service.complete_phase1(code)
        data = MonthlyWinDetailSerializer(
            mw, context=self.get_serializer_context()
        ).data
        return self.response(data=data, message="Phase 1 closed.")

    @extend_schema(
        summary="Launch Phase 2",
        description=(
            "Creates one consolidated survey per Phase 1 recipient covering all "
            "nominated wins, and emails the survey link."
        ),
        responses={
            200: MonthlyWinDetailSerializer,
            422: OpenApiResponse(description="Cannot launch Phase 2."),
        },
    )
    def launch_phase2(self, request: Request, code=None):
        """POST /wins/monthly/<code>/launch-phase2/"""
        mw = self.service.launch_phase2(code)
        data = MonthlyWinDetailSerializer(
            mw, context=self.get_serializer_context()
        ).data
        return self.response(
            data=data, message="Phase 2 launched. Survey emails have been sent."
        )

    @extend_schema(
        summary="Close Phase 2",
        responses={
            200: MonthlyWinDetailSerializer,
            422: OpenApiResponse(description="Phase 2 is not open."),
        },
    )
    def complete_phase2(self, request: Request, code=None):
        """POST /wins/monthly/<code>/complete-phase2/"""
        mw = self.service.complete_phase2(code)
        data = MonthlyWinDetailSerializer(
            mw, context=self.get_serializer_context()
        ).data
        return self.response(data=data, message="Phase 2 closed.")

    @extend_schema(
        summary="Declare winners",
        description=(
            "Tallies non-dismissed Phase 2 nominations and ranks the top 2 "
            "per category."
        ),
        responses={
            200: MonthlyWinDetailSerializer,
            422: OpenApiResponse(description="Phase 2 is not closed."),
        },
    )
    def declare_winners(self, request: Request, code=None):
        """POST /wins/monthly/<code>/declare/"""
        mw = self.service.declare_winners(code)
        data = MonthlyWinDetailSerializer(
            mw, context=self.get_serializer_context()
        ).data
        return self.response(data=data, message="Winners declared.")

    @extend_schema(
        summary="List surveys for a Monthly Win",
        responses={200: MonthlyWinSurveyListSerializer(many=True)},
    )
    def surveys(self, request: Request, code=None):
        """GET /wins/monthly/<code>/surveys/"""
        from apps.wins import selectors

        mw = self.service.get(code=code)
        qs = selectors.get_monthly_win_surveys(mw)
        data = MonthlyWinSurveyListSerializer(
            qs, many=True, context=self.get_serializer_context()
        ).data
        return self.response(data=data)

    @extend_schema(
        summary="List declared results for a Monthly Win",
        responses={200: OpenApiResponse(description="Declared results.")},
    )
    def results(self, request: Request, code=None):
        """GET /wins/monthly/<code>/results/"""
        from apps.wins import selectors

        mw = self.service.get(code=code)
        qs = selectors.get_monthly_win_results(mw)
        data = [
            {
                "category": r.category,
                "rank": r.rank,
                "vote_count": r.vote_count,
                "team_name": r.entry.team.name,
                "title": r.entry.title,
                "description": r.entry.description,
            }
            for r in qs
        ]
        return self.response(data=data)

    @extend_schema(
        summary="Get survey data for admin override",
        responses={
            200: OpenApiResponse(description="Survey + entry data."),
            404: OpenApiResponse(description="Survey not found."),
        },
    )
    def survey_admin_data(self, request: Request, survey_code=None):
        """GET /wins/monthly/surveys/<survey_code>/admin-data/"""
        data = self.service.get_admin_survey_data(survey_code)
        return self.response(data=data)

    @extend_schema(
        summary="Override a survey on behalf of a non-responding recipient",
        request=MonthlyWinSurveySubmitSerializer,
        responses={
            200: OpenApiResponse(description="Survey overridden."),
            404: OpenApiResponse(description="Survey not found."),
            422: OpenApiResponse(description="Validation error."),
        },
    )
    def override_survey(self, request: Request, survey_code=None):
        """POST /wins/monthly/surveys/<survey_code>/override/"""
        serializer = MonthlyWinSurveySubmitSerializer(
            data=request.data, context=self.get_serializer_context()
        )
        serializer.is_valid(raise_exception=True)
        nominations = [dict(n) for n in serializer.validated_data["nominations"]]
        self.service.override_survey(survey_code, nominations)
        return self.response(message="Survey overridden successfully.")

    @extend_schema(
        summary="Download the Monthly Win declared-results PDF",
        responses={200: OpenApiResponse(description="PDF file attachment.")},
    )
    def results_pdf(self, request: Request, code=None):
        """GET /wins/monthly/<code>/results-pdf/"""
        mw = self.service.get(code=code)
        content = MonthlyWinResultsEngine.build_pdf(mw)
        response = HttpResponse(content, content_type="application/pdf")
        response["Content-Disposition"] = (
            f"attachment; filename=monthly-win-{mw.code}-results.pdf"
        )
        return response

    @extend_schema(
        summary="Send the Monthly Win declared-results email",
        responses={
            200: OpenApiResponse(description="Results email sent."),
            422: OpenApiResponse(description="No recipients configured."),
        },
    )
    def send_results(self, request: Request, code=None):
        """POST /wins/monthly/<code>/send-results/"""
        mw = self.service.get(code=code)
        MonthlyWinResultsEngine.send_results_email(mw)
        return self.response(message="Results email sent successfully.")


@extend_schema(tags=["Wins: Monthly Survey"])
class SurveyViewSet(BaseViewSet):
    """Public, unauthenticated token-based survey access for recipients."""

    authentication_classes: list = []
    permission_classes = [AllowAny]

    @extend_schema(
        summary="Get survey data by token",
        responses={
            200: OpenApiResponse(description="Survey + entry data."),
            404: OpenApiResponse(description="Survey not found."),
        },
    )
    def retrieve(self, request: Request, token=None):
        """GET /wins/monthly/survey/<token>/"""
        data = SurveyService.get_survey_data(token)
        return self.response(data=data)

    @extend_schema(
        summary="Submit survey nominations",
        request=MonthlyWinSurveySubmitSerializer,
        responses={
            200: OpenApiResponse(description="Survey submitted."),
            404: OpenApiResponse(description="Survey not found."),
            422: OpenApiResponse(description="Validation error."),
        },
    )
    def submit(self, request: Request, token=None):
        """POST /wins/monthly/survey/<token>/submit/"""
        serializer = MonthlyWinSurveySubmitSerializer(
            data=request.data, context=self.get_serializer_context()
        )
        serializer.is_valid(raise_exception=True)
        nominations = [dict(n) for n in serializer.validated_data["nominations"]]
        SurveyService.submit_survey(token, nominations)
        return self.response(message="Survey submitted successfully.")


@extend_schema(tags=["Wins: Configuration"])
class WinsConfigViewSet(BaseViewSet):
    def get_permissions(self):
        if self.action == "partial_update":
            return [
                IsAuthenticated(),
                HasPermission("configurations.change_configuration"),
            ]
        return [IsAuthenticated()]

    @extend_schema(
        summary="Get Wins configuration",
        responses={200: OpenApiResponse(response=WinsConfigSerializer)},
    )
    def retrieve(self, request):
        """GET /wins/config/"""
        serializer = WinsConfigSerializer(_current_wins_config())
        return self.response(data=serializer.data)

    @extend_schema(
        summary="Update Wins configuration",
        request=WinsConfigUpdateSerializer,
        responses={200: OpenApiResponse(response=WinsConfigSerializer)},
    )
    def partial_update(self, request):
        """PATCH /wins/config/"""
        serializer = WinsConfigUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        svc = AdminConfigurationService(user=request.user, request=request)
        for field, code in _WINS_CONFIG_MAP.items():
            if field in serializer.validated_data:
                svc.set_config(config_code=code, value=serializer.validated_data[field])

        return self.response(
            data=WinsConfigSerializer(_current_wins_config()).data,
            message="Wins configuration updated successfully.",
        )
