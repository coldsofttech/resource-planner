from __future__ import annotations

import logging

from apps.wins.constants import SurveyPhase, SurveyStatus, WinCategory
from apps.wins.models import MonthlyWin, MonthlyWinSurvey, Win

logger = logging.getLogger(__name__)

_SUGGEST_PROMPT = """\
You are helping a team write a "Weekly Win" entry for a company-wide progress \
update. Weekly Wins are short, punchy summaries of what a team shipped.

Guidelines for great wins:
- The title should be a punchy headline
- The description should give context: what was delivered, and its benefits/outcomes
- Include next steps if relevant
- If this is a cost-saving win, call out the saving amount prominently

Team: {team_name}
Project/Programme: {project_line}
What has been delivered: {delivered}
Benefits delivered: {benefits}
Next steps: {next_steps}

Respond in EXACTLY this format, with no extra commentary:
TITLE: <a punchy one-line title>
DESCRIPTION: <a short description, 1-3 sentences>"""


class WinEntrySuggestEngine:
    """Uses AI to turn structured win details into a title + description."""

    @staticmethod
    def suggest(
        *,
        team_name: str,
        project_line: str,
        delivered: str,
        benefits: str,
        next_steps: str,
    ) -> dict:
        from apps.configurations.selectors import AI
        from apps.core.exceptions import ServiceUnavailableException

        if not AI.is_ai_enabled():
            raise ServiceUnavailableException("AI suggestions are not enabled.")

        prompt = _SUGGEST_PROMPT.format(
            team_name=team_name,
            project_line=project_line or "(none)",
            delivered=delivered or "(none)",
            benefits=benefits or "(none)",
            next_steps=next_steps or "(none)",
        )

        from aicore import AIClient

        client = AIClient(
            provider=AI.get_ai_provider(),
            model=AI.get_ai_model(),
            api_key=AI.get_anthropic_api_key(),
            region=AI.get_bedrock_region(),
            auth_mode=AI.get_bedrock_auth_mode(),
            iam_key=AI.get_bedrock_iam_key(),
            iam_secret=AI.get_bedrock_iam_secret(),
        )
        try:
            raw = client.complete(prompt, max_tokens=256)
        except Exception as exc:
            logger.warning("AI win-entry suggestion failed", exc_info=True)
            raise ServiceUnavailableException(
                "AI suggestion is temporarily unavailable. "
                "Please try again or enter the details manually."
            ) from exc

        return WinEntrySuggestEngine._parse(raw)

    @staticmethod
    def _parse(raw: str) -> dict:
        title = ""
        description_lines: list[str] = []
        in_description = False
        for line in raw.splitlines():
            stripped = line.strip()
            if stripped.upper().startswith("TITLE:"):
                title = stripped.split(":", 1)[1].strip()
                in_description = False
            elif stripped.upper().startswith("DESCRIPTION:"):
                description_lines.append(stripped.split(":", 1)[1].strip())
                in_description = True
            elif in_description and stripped:
                description_lines.append(stripped)

        return {
            "title": title[:255],
            "description": " ".join(description_lines).strip(),
        }


class WinReviewEngine:
    """Builds the review-complete PDF and dispatches it to configured recipients."""

    @staticmethod
    def build_pdf(win: Win) -> bytes:
        from exportcore import export_to_pdf

        from apps.configurations.selectors import General

        rows = [
            {"Team": entry.team.name, "Win": f"{entry.title}: {entry.description}"}
            for entry in win.entries.select_related("team").order_by(
                "team__name", "-created_at"
            )
        ]
        return export_to_pdf(
            rows=rows,
            title=f"Weekly Win — Week {win.week_number}",
            app_title=General.get_app_name(),
            base_url=General.get_app_url(),
        )

    @staticmethod
    def send_review_email(win: Win) -> None:
        from apps.configurations.selectors import Wins as WinsConfig
        from apps.core.exceptions import ValidationException
        from apps.core.utils import build_email_sender

        recipients = WinsConfig.get_review_email_recipients()
        if not recipients:
            raise ValidationException(
                "No Weekly Win review email recipients are configured."
            )

        pdf_bytes = WinReviewEngine.build_pdf(win)
        cc = (
            [win.reviewed_by.user.email]
            if win.reviewed_by and win.reviewed_by.user and win.reviewed_by.user.email
            else None
        )

        sender = build_email_sender()
        sender.send(
            to=recipients,
            cc=cc,
            subject=f"Weekly Win — Week {win.week_number}",
            body=(
                f"Attached is the Weekly Win summary for Week {win.week_number} "
                f"({win.start_date} to {win.end_date})."
            ),
            attachments=[
                {
                    "filename": f"weekly-win-week-{win.week_number}.pdf",
                    "data": pdf_bytes,
                }
            ],
        )


class MonthlyWinEngine:
    """Sends Monthly Wins survey invite emails to recipients."""

    @staticmethod
    def send_phase_emails(mw: MonthlyWin, phase: str) -> None:
        from apps.configurations.selectors import General
        from apps.core.utils import build_email_sender

        app_url = General.get_app_url().rstrip("/")
        sender = build_email_sender()

        surveys = (
            MonthlyWinSurvey.objects.select_related("recipient", "monthly_win")
            .prefetch_related("teams")
            .filter(monthly_win=mw, phase=phase, status=SurveyStatus.PENDING)
        )
        for survey in surveys:
            MonthlyWinEngine._send_survey_email(sender, survey, app_url)

    @staticmethod
    def send_survey_reminder(survey: MonthlyWinSurvey) -> None:
        from apps.configurations.selectors import General
        from apps.core.utils import build_email_sender

        app_url = General.get_app_url().rstrip("/")
        sender = build_email_sender()
        MonthlyWinEngine._send_survey_email(sender, survey, app_url)

    @staticmethod
    def _send_survey_email(sender, survey: MonthlyWinSurvey, app_url: str) -> None:
        from django.utils import timezone

        link = f"{app_url}/wins/monthly/survey/{survey.token}/"
        deadline = (
            survey.monthly_win.phase1_deadline
            if survey.phase == SurveyPhase.PHASE_1
            else survey.monthly_win.phase2_deadline
        )
        deadline_str = (
            f"\n\nPlease respond by {deadline.strftime('%d %b %Y %H:%M')}."
            if deadline
            else ""
        )
        recipient_name = survey.recipient.get_full_name() or survey.recipient.email

        if survey.phase == SurveyPhase.PHASE_1:
            phase_label = "Phase 1"
            team_list = ", ".join(t.name for t in survey.teams.all())
            body = (
                f"Hi {recipient_name},\n\n"
                f"You have been asked to nominate the best wins from your "
                f"team(s): {team_list}.\n\n"
                f"Please click the link below to complete the survey:\n"
                f"{link}{deadline_str}\n\n"
                f"This is an automated message from the Resource Planner."
            )
        else:
            phase_label = "Phase 2 (Final Selection)"
            # Plain-text email body, not a SQL query — bandit's B608 heuristic
            # matches on the English word "select" in this sentence.
            body = (
                f"Hi {recipient_name},\n\n"  # nosec B608
                f"Phase 2 of the Monthly Wins is now open. Please select the "
                f"best wins across all nominated teams.\n\n"
                f"Please click the link below to complete the survey:\n"
                f"{link}{deadline_str}\n\n"
                f"This is an automated message from the Resource Planner."
            )

        subject = f"Monthly Wins — {survey.monthly_win.name} — {phase_label} Survey"

        try:
            sender.send(to=[survey.recipient.email], subject=subject, body=body)
            survey.sent_at = timezone.now()
            survey.save(update_fields=["sent_at", "updated_at"])
        except Exception:
            logger.exception(
                "Failed to send Monthly Wins survey email for survey %s",
                survey.code,
            )


class MonthlyWinResultsEngine:
    """Builds the declared-results PDF and dispatches it to configured recipients."""

    @staticmethod
    def build_pdf(mw: MonthlyWin) -> bytes:
        from exportcore import export_to_pdf

        from apps.configurations.selectors import General
        from apps.wins import selectors

        category_labels = dict(WinCategory.choices)
        results = selectors.get_monthly_win_results(mw)
        rows = [
            {
                "Category": category_labels.get(r.category, r.category),
                "Rank": r.rank,
                "Team": r.entry.team.name,
                "Win": f"{r.entry.title}: {r.entry.description}",
                "Votes": r.vote_count,
            }
            for r in results
        ]
        return export_to_pdf(
            rows=rows,
            title=f"Monthly Wins — {mw.name} — Results",
            app_title=General.get_app_name(),
            base_url=General.get_app_url(),
        )

    @staticmethod
    def send_results_email(mw: MonthlyWin) -> None:
        from apps.configurations.selectors import Wins as WinsConfig
        from apps.core.exceptions import ValidationException
        from apps.core.utils import build_email_sender

        recipients = WinsConfig.get_review_email_recipients()
        if not recipients:
            raise ValidationException("No Wins review email recipients are configured.")

        pdf_bytes = MonthlyWinResultsEngine.build_pdf(mw)
        sender = build_email_sender()
        sender.send(
            to=recipients,
            subject=f"Monthly Wins — {mw.name} — Results Declared",
            body=(f"Attached are the declared results for Monthly Wins '{mw.name}'."),
            attachments=[
                {
                    "filename": f"monthly-win-{mw.code}-results.pdf",
                    "data": pdf_bytes,
                }
            ],
        )
