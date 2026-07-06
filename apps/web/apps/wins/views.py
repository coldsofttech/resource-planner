from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie

from apps.core.views import BaseView, ProtectedView
from apps.permissions.selectors import get_user_permissions


class WinsListView(ProtectedView):
    template_name = "wins/index.html"

    def get_context_data(self, **kwargs: object) -> dict[str, object]:
        ctx = super().get_context_data(**kwargs)
        perms = get_user_permissions(self.request.user)
        ctx["can_add_win"] = "wins.add_win" in perms
        ctx["can_delete_win"] = "wins.delete_win" in perms
        ctx["can_view_monthlywin"] = "wins.view_monthlywin" in perms
        return ctx


class WinDetailView(ProtectedView):
    template_name = "wins/detail.html"

    def get_context_data(self, **kwargs: object) -> dict[str, object]:
        from apps.configurations.selectors import AI

        ctx = super().get_context_data(**kwargs)
        ctx["win_code"] = self.kwargs["code"]
        perms = get_user_permissions(self.request.user)
        ctx["can_add_winentry"] = "wins.add_winentry" in perms
        ctx["can_change_winentry"] = "wins.change_winentry" in perms
        ctx["can_delete_winentry"] = "wins.delete_winentry" in perms
        ctx["can_review_complete_win"] = "wins.review_complete_win" in perms
        ctx["ai_enabled"] = AI.is_ai_enabled()
        return ctx


class MonthlyWinsListView(ProtectedView):
    template_name = "wins/monthly_index.html"

    def get_context_data(self, **kwargs: object) -> dict[str, object]:
        ctx = super().get_context_data(**kwargs)
        perms = get_user_permissions(self.request.user)
        ctx["can_add_monthlywin"] = "wins.add_monthlywin" in perms
        ctx["can_delete_monthlywin"] = "wins.delete_monthlywin" in perms
        ctx["can_add_monthlywinsrecipient"] = "wins.add_monthlywinsrecipient" in perms
        ctx["can_change_monthlywinsrecipient"] = (
            "wins.change_monthlywinsrecipient" in perms
        )
        ctx["can_delete_monthlywinsrecipient"] = (
            "wins.delete_monthlywinsrecipient" in perms
        )
        return ctx


class MonthlyWinDetailView(ProtectedView):
    template_name = "wins/monthly_detail.html"

    def get_context_data(self, **kwargs: object) -> dict[str, object]:
        ctx = super().get_context_data(**kwargs)
        ctx["monthly_win_code"] = self.kwargs["code"]
        perms = get_user_permissions(self.request.user)
        ctx["can_manage_monthlywin"] = "wins.manage_monthlywin" in perms
        return ctx


@method_decorator(ensure_csrf_cookie, name="dispatch")
class MonthlyWinSurveyView(BaseView):
    """Public, unauthenticated token-based survey page — no login required."""

    template_name = "wins/survey.html"

    def get_context_data(self, **kwargs: object) -> dict[str, object]:
        ctx = super().get_context_data(**kwargs)
        ctx["token"] = str(self.kwargs["token"])
        return ctx


class WinsConfigView(ProtectedView):
    template_name = "wins/config.html"

    def get_context_data(self, **kwargs: object) -> dict[str, object]:
        ctx = super().get_context_data(**kwargs)
        perms = get_user_permissions(self.request.user)
        ctx["can_change_wins_config"] = "configurations.change_configuration" in perms
        return ctx
