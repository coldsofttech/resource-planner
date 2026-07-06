from __future__ import annotations

import logging
from html.parser import HTMLParser

from apps.core.exceptions import NotFoundException
from apps.core.utils import build_email_sender
from apps.recharges import selectors
from apps.recharges.services import RechargeEmailService

logger = logging.getLogger(__name__)


def _html_to_text(html: str) -> str:
    """Strip HTML tags and return plain text (for email fallback body)."""

    class _Stripper(HTMLParser):
        def __init__(self) -> None:
            super().__init__()
            self._parts: list[str] = []

        def handle_data(self, data: str) -> None:
            self._parts.append(data)

        def get_text(self) -> str:
            return " ".join(self._parts).strip()

    stripper = _Stripper()
    stripper.feed(html or "")
    return stripper.get_text()


class RechargeEmailEngine:
    """Orchestrate creation and dispatch of recharge emails via emailcore."""

    def __init__(self, user) -> None:
        self._user = user
        self._service = RechargeEmailService(user=user)

    def trigger_all(self, sprint_code: str, type_val: str) -> dict:
        """
        Ensure a RechargeEmail record exists for every project group that has
        recharge rows for the given sprint + type, then dispatch all emails.

        Returns a summary dict with sent/error counts.
        """
        groups = selectors.get_email_review_groups(sprint_code, type_val)
        sent = 0
        errors = 0

        sender = build_email_sender()

        for group in groups:
            try:
                email_obj = self._service.create_or_update(
                    sprint_code=sprint_code,
                    type_val=type_val,
                    group_code=group["group_code"],
                    to=group["to"],
                    cc=group["cc"],
                    subject=group["subject"],
                    body=group["body"],
                )
                self._dispatch(sender, email_obj)
                self._service.mark_sent(email_obj.code)
                sent += 1
            except Exception as exc:  # noqa: BLE001
                errors += 1
                existing = selectors.get_recharge_email_by_sprint_type_group(
                    sprint_code, type_val, group["group_code"]
                )
                if existing:
                    try:
                        self._service.mark_error(existing.code, str(exc))
                    except Exception:  # noqa: BLE001
                        logger.exception(
                            "Failed to record recharge email error status."
                        )

        return {"sent": sent, "errors": errors, "total": len(groups)}

    def trigger_single(self, email_code: str) -> None:
        """Resend a single RechargeEmail by its code."""
        obj = selectors.get_recharge_email_by_code(email_code)
        if obj is None:
            raise NotFoundException(
                resource="RechargeEmail", lookup_field="code", lookup_value=email_code
            )
        sender = build_email_sender()
        try:
            self._dispatch(sender, obj)
            self._service.mark_sent(obj.code)
        except Exception as exc:  # noqa: BLE001
            self._service.mark_error(obj.code, str(exc))
            raise

    @staticmethod
    def _dispatch(sender, email_obj) -> None:
        """Send the email via emailcore using the stored to/cc/subject/body fields."""
        to_addresses = [c["email"] for c in (email_obj.to or []) if c.get("email")]
        cc_addresses = [c["email"] for c in (email_obj.cc or []) if c.get("email")]
        plain_body = _html_to_text(email_obj.body)

        sender.send(
            to=to_addresses,
            subject=email_obj.subject,
            body=plain_body,
            html_body=email_obj.body,
            cc=cc_addresses or None,
        )
