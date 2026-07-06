from __future__ import annotations

from django.db.models import QuerySet

from apps.resource_plans.models import Plan, PlanComment


def get_all_resource_plan_comments(plan: Plan) -> QuerySet[PlanComment]:
    return (
        PlanComment.objects.select_related(
            "comment__created_by__profile",
            "comment__updated_by__profile",
        )
        .prefetch_related("comment__mentions__user")
        .filter(plan=plan)
        .order_by("-comment__is_pinned", "-comment__created_at")
    )


def get_pinned_resource_plan_comments_count(plan: Plan) -> int:
    return PlanComment.objects.filter(plan=plan, comment__is_pinned=True).count()


def get_resource_plan_comment_by_code(code: str) -> PlanComment | None:
    try:
        return (
            PlanComment.objects.select_related(
                "plan",
                "comment__created_by__profile",
                "comment__updated_by__profile",
            )
            .prefetch_related("comment__mentions__user")
            .get(code=code)
        )
    except PlanComment.DoesNotExist:
        return None
