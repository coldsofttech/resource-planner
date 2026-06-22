from apps.comments.models import Comment, CommentMention
from apps.users.models import User


def make_comment(
    comment: str = "This is a test comment.",
    is_edited: bool = False,
    is_pinned: bool = False,
    **overrides,
) -> Comment:
    return Comment.objects.create(
        comment=comment,
        is_edited=is_edited,
        is_pinned=is_pinned,
        **overrides,
    )


def make_comment_mention(
    comment: Comment | None = None,
    user: User | None = None,
    **overrides,
) -> CommentMention:
    if comment is None:
        comment = make_comment()
    if user is None:
        from apps.users.tests.factories import make_user

        user = make_user()
    return CommentMention.objects.create(comment=comment, user=user, **overrides)
