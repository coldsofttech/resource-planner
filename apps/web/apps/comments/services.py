from __future__ import annotations

from django.utils.html import strip_tags

from apps.comments.models import Comment
from apps.to_do.constants import TODO_MENTION_MARKER
from apps.to_do.models import Todo
from apps.users.models import User


def has_todo_marker(comment_html: str) -> bool:
    """Whether a comment body carries the '#todo' actionable marker.

    Comment bodies are stored as contenteditable HTML, so tags are stripped
    before checking for the plain-text marker.
    """
    return TODO_MENTION_MARKER in strip_tags(comment_html).lower()


def create_todo_for_mention(
    *,
    actor: User,
    mentioned_user: User,
    comment: Comment,
    link: str,
    context_label: str,
) -> Todo | None:
    """Create an action item for a mentioned user if the comment is marked '#todo'.

    Shared by every comment-owning feature (projects, resource plans, ...) so the
    marker-detection and to-do creation logic lives in one place rather than being
    duplicated per feature, mirroring how mention notifications are already handled
    per-feature but backed by the shared `apps.comments` models.
    """
    if not has_todo_marker(comment.comment):
        return None

    from apps.to_do.services import TodoService

    return TodoService(user=actor).create_from_mention(
        comment=comment,
        mentioned_user=mentioned_user,
        link=link,
        context_label=context_label,
    )
