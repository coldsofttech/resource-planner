from datetime import datetime, timezone

from django.test import SimpleTestCase

from apps.audit.constants import Action
from apps.audit.models import Audit

_TS = datetime(2024, 6, 1, 10, 0, 0, tzinfo=timezone.utc)


def _make_unsaved(**kwargs) -> Audit:
    defaults: dict = {
        "action": Action.CREATE,
        "resource_type": "project",
        "resource_code": "PROJ-1",
        "timestamp": _TS,
    }
    defaults.update(kwargs)
    return Audit(**defaults)


# ── Audit.__str__ ──────────────────────────────────────────────────────────────


class AuditStrTest(SimpleTestCase):
    def test_str_contains_action(self):
        entry = _make_unsaved(action=Action.UPDATE)
        self.assertIn("update", str(entry))

    def test_str_contains_resource_type(self):
        entry = _make_unsaved(resource_type="team")
        self.assertIn("team", str(entry))

    def test_str_contains_resource_code(self):
        entry = _make_unsaved(resource_code="TEAM-7")
        self.assertIn("TEAM-7", str(entry))

    def test_str_contains_timestamp_separator(self):
        entry = _make_unsaved()
        self.assertIn("@", str(entry))

    def test_str_with_none_resource_code_includes_none(self):
        entry = _make_unsaved(resource_code=None)
        self.assertIn("None", str(entry))

    def test_str_field_order_action_before_resource_type(self):
        entry = _make_unsaved(action=Action.CREATE, resource_type="project")
        result = str(entry)
        self.assertLess(result.index("create"), result.index("project"))

    def test_str_field_order_resource_type_before_code(self):
        entry = _make_unsaved(resource_type="project", resource_code="PROJ-1")
        result = str(entry)
        self.assertLess(result.index("project"), result.index("PROJ-1"))

    def test_str_field_order_code_before_timestamp(self):
        entry = _make_unsaved(resource_code="PROJ-1")
        result = str(entry)
        self.assertLess(result.index("PROJ-1"), result.index("@"))
