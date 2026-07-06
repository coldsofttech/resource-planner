from django.test import TestCase

from apps.audit.constants import Action
from apps.audit.models import Audit
from apps.recharges.models import Recharge, RechargeDetail
from apps.recharges.tests.factories import make_recharge_type
from apps.sprints.constants import SprintDataImportStatus, SprintDataImportType
from apps.sprints.models import SprintDataImport
from apps.sprints.tests.factories import make_sprint
from apps.teams.tests.factories import make_team
from apps.users.tests.factories import make_user


def _make_import(sprint, team, user=None):
    if user is None:
        user = make_user()
    return SprintDataImport.objects.create(
        sprint=sprint,
        team=team,
        version_number=1,
        file_name="test.csv",
        status=SprintDataImportStatus.ACTIVE,
        import_type=SprintDataImportType.FORECAST,
        created_by=user,
        updated_by=user,
    )


# ── Recharge signals ──────────────────────────────────────────────────────────


class RechargeCreateSignalTest(TestCase):
    def setUp(self):
        self.sprint = make_sprint()

    def test_create_fires_audit_entry(self):
        Recharge.objects.create(sprint=self.sprint, type="forecast")
        self.assertTrue(
            Audit.objects.filter(
                module="recharges",
                resource_type="recharge",
                action=Action.CREATE,
            ).exists()
        )

    def test_audit_entry_contains_sprint_id(self):
        recharge = Recharge.objects.create(sprint=self.sprint, type="forecast")
        entry = Audit.objects.filter(
            module="recharges",
            resource_type="recharge",
            action=Action.CREATE,
            resource_code=recharge.code,
        ).first()
        self.assertIsNotNone(entry)
        self.assertEqual(entry.after["sprint_id"], self.sprint.pk)

    def test_audit_entry_contains_type(self):
        Recharge.objects.create(sprint=self.sprint, type="actual")
        entry = Audit.objects.filter(
            module="recharges",
            resource_type="recharge",
            action=Action.CREATE,
        ).first()
        self.assertIsNotNone(entry)
        self.assertEqual(entry.after["type"], "actual")

    def test_no_audit_on_update(self):
        recharge = Recharge.objects.create(sprint=self.sprint, type="forecast")
        count_before = Audit.objects.filter(
            module="recharges", resource_type="recharge"
        ).count()
        recharge.save()
        count_after = Audit.objects.filter(
            module="recharges", resource_type="recharge"
        ).count()
        self.assertEqual(count_before, count_after)


class RechargeDeleteSignalTest(TestCase):
    def setUp(self):
        self.sprint = make_sprint()

    def test_delete_fires_audit_entry(self):
        recharge = Recharge.objects.create(sprint=self.sprint, type="forecast")
        recharge.delete()
        self.assertTrue(
            Audit.objects.filter(
                module="recharges",
                resource_type="recharge",
                action=Action.DELETE,
            ).exists()
        )

    def test_audit_before_contains_snapshot(self):
        recharge = Recharge.objects.create(sprint=self.sprint, type="forecast")
        code = recharge.code
        recharge.delete()
        entry = Audit.objects.filter(
            module="recharges",
            resource_type="recharge",
            action=Action.DELETE,
            resource_code=code,
        ).first()
        self.assertIsNotNone(entry)
        self.assertIn("sprint_id", entry.before)
        self.assertIn("total_days", entry.before)

    def test_bulk_delete_fires_audit_per_record(self):
        Recharge.objects.create(sprint=self.sprint, type="forecast")
        Recharge.objects.create(sprint=self.sprint, type="actual")
        Recharge.objects.filter(sprint=self.sprint).delete()
        self.assertEqual(
            Audit.objects.filter(
                module="recharges",
                resource_type="recharge",
                action=Action.DELETE,
            ).count(),
            2,
        )


# ── RechargeDetail signals ────────────────────────────────────────────────────


class RechargeDetailCreateSignalTest(TestCase):
    def setUp(self):
        self.sprint = make_sprint()
        self.team = make_team()
        self.import_record = _make_import(self.sprint, self.team)

    def test_create_fires_audit_entry(self):
        RechargeDetail.objects.create(
            sprint=self.sprint,
            team=self.team,
            import_record=self.import_record,
            type="forecast",
        )
        self.assertTrue(
            Audit.objects.filter(
                module="recharges",
                resource_type="recharge_detail",
                action=Action.CREATE,
            ).exists()
        )

    def test_audit_entry_contains_team_id(self):
        detail = RechargeDetail.objects.create(
            sprint=self.sprint,
            team=self.team,
            import_record=self.import_record,
            type="forecast",
        )
        entry = Audit.objects.filter(
            module="recharges",
            resource_type="recharge_detail",
            action=Action.CREATE,
            resource_code=detail.code,
        ).first()
        self.assertIsNotNone(entry)
        self.assertEqual(entry.after["team_id"], self.team.pk)

    def test_audit_entry_contains_type_and_jira_id(self):
        RechargeDetail.objects.create(
            sprint=self.sprint,
            team=self.team,
            import_record=self.import_record,
            type="actual",
            jira_id="JIRA-42",
        )
        entry = Audit.objects.filter(
            module="recharges",
            resource_type="recharge_detail",
            action=Action.CREATE,
        ).first()
        self.assertIsNotNone(entry)
        self.assertEqual(entry.after["type"], "actual")
        self.assertEqual(entry.after["jira_id"], "JIRA-42")

    def test_no_audit_on_update(self):
        detail = RechargeDetail.objects.create(
            sprint=self.sprint,
            team=self.team,
            import_record=self.import_record,
            type="forecast",
        )
        count_before = Audit.objects.filter(
            module="recharges", resource_type="recharge_detail"
        ).count()
        detail.save()
        count_after = Audit.objects.filter(
            module="recharges", resource_type="recharge_detail"
        ).count()
        self.assertEqual(count_before, count_after)


class RechargeDetailDeleteSignalTest(TestCase):
    def setUp(self):
        self.sprint = make_sprint()
        self.team = make_team()
        self.import_record = _make_import(self.sprint, self.team)

    def test_delete_fires_audit_entry(self):
        detail = RechargeDetail.objects.create(
            sprint=self.sprint,
            team=self.team,
            import_record=self.import_record,
            type="forecast",
        )
        detail.delete()
        self.assertTrue(
            Audit.objects.filter(
                module="recharges",
                resource_type="recharge_detail",
                action=Action.DELETE,
            ).exists()
        )

    def test_audit_before_contains_snapshot(self):
        detail = RechargeDetail.objects.create(
            sprint=self.sprint,
            team=self.team,
            import_record=self.import_record,
            type="actual",
        )
        code = detail.code
        detail.delete()
        entry = Audit.objects.filter(
            module="recharges",
            resource_type="recharge_detail",
            action=Action.DELETE,
            resource_code=code,
        ).first()
        self.assertIsNotNone(entry)
        self.assertIn("sprint_id", entry.before)
        self.assertIn("team_id", entry.before)


# ── RechargeType signal logging ───────────────────────────────────────────────


class RechargeTypeSignalLoggingTest(TestCase):
    def test_create_logs_debug_message(self):
        with self.assertLogs("apps.recharges.signals", level="DEBUG") as cm:
            make_recharge_type("BAU")
        self.assertTrue(any("Created" in msg and "BAU" in msg for msg in cm.output))

    def test_update_logs_debug_message(self):
        rt = make_recharge_type("BAU")
        with self.assertLogs("apps.recharges.signals", level="DEBUG") as cm:
            rt.name = "BAU"
            rt.save()
        self.assertTrue(any("Updated" in msg for msg in cm.output))

    def test_delete_logs_debug_message(self):
        rt = make_recharge_type("PROJECT")
        with self.assertLogs("apps.recharges.signals", level="DEBUG") as cm:
            rt.delete()
        self.assertTrue(any("Deleted" in msg and "PROJECT" in msg for msg in cm.output))
