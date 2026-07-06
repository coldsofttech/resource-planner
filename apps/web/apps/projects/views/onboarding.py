from apps.core.views import BaseView, ProtectedView


class OnboardingPortalView(BaseView):
    template_name = "projects/onboarding/index.html"


class OnboardingReviewView(ProtectedView):
    template_name = "projects/onboarding/review.html"


class CreateDemandView(ProtectedView):
    template_name = "projects/onboarding/create.html"

    def get_context_data(self, **kwargs: object) -> dict[str, object]:
        context = super().get_context_data(**kwargs)
        context["requester_email"] = self.request.user.email
        return context
