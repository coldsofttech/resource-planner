import io

from django.test import TestCase
from rest_framework.test import APIClient

from apps.configurations.tests.factories import mark_setup_complete
from apps.skills.models import Skill
from apps.skills.tests.factories import make_skill
from apps.users.tests.factories import make_user

LIST_URL = "/api/v1/skills/"
OPTIONS_URL = "/api/v1/skills/options/"
STATS_URL = "/api/v1/skills/stats/"
DETAIL_URL = "/api/v1/skills/{}/"
ACTIVATE_URL = "/api/v1/skills/{}/activate/"
DEACTIVATE_URL = "/api/v1/skills/{}/deactivate/"
IMPORT_URL = "/api/v1/skills/import/"
IMPORT_SPECS_URL = "/api/v1/skills/import/specs/"
IMPORT_SAMPLE_URL = "/api/v1/skills/import/sample/"
EXPORT_URL = "/api/v1/skills/export/"
EXPORT_SPECS_URL = "/api/v1/skills/export/specs/"


# ── GET /skills/ ──────────────────────────────────────────────────────────────


class SkillListAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)
        make_skill("Python", is_active=True)
        make_skill("COBOL", is_active=False)

    def test_unauthenticated_returns_401(self):
        response = self.client.get(LIST_URL)
        self.assertEqual(response.status_code, 401)

    def test_defaults_to_active_only(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(LIST_URL)
        self.assertEqual(response.status_code, 200)
        skills = [r["skill"] for r in response.data["data"]["results"]]
        self.assertIn("Python", skills)
        self.assertNotIn("COBOL", skills)

    def test_is_active_false_returns_inactive(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(LIST_URL, {"is_active": "false"})
        self.assertEqual(response.status_code, 200)
        skills = [r["skill"] for r in response.data["data"]["results"]]
        self.assertIn("COBOL", skills)
        self.assertNotIn("Python", skills)

    def test_response_has_pagination(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(LIST_URL)
        self.assertIn("pagination", response.data["data"])

    def test_response_has_success_flag(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(LIST_URL)
        self.assertTrue(response.data["success"])

    def test_search_param_filters_by_skill(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(LIST_URL, {"search": "Python"})
        self.assertEqual(response.status_code, 200)
        skills = [r["skill"] for r in response.data["data"]["results"]]
        self.assertIn("Python", skills)
        self.assertEqual(len(skills), 1)

    def test_page_size_param_limits_results(self):
        make_skill("Java", is_active=True)
        self.client.force_authenticate(user=self.user)
        response = self.client.get(LIST_URL, {"page_size": 1})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["data"]["results"]), 1)


# ── GET /skills/stats/ ────────────────────────────────────────────────────────


class SkillStatsAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)
        make_skill("Python", is_active=True)
        make_skill("Java", is_active=True)
        make_skill("COBOL", is_active=False)

    def test_unauthenticated_returns_401(self):
        response = self.client.get(STATS_URL)
        self.assertEqual(response.status_code, 401)

    def test_returns_correct_stats(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(STATS_URL)
        self.assertEqual(response.status_code, 200)
        data = response.data["data"]
        self.assertEqual(data["total"], 3)
        self.assertEqual(data["active"], 2)
        self.assertEqual(data["inactive"], 1)


# ── GET /skills/options/ ─────────────────────────────────────────────────────


class SkillOptionsAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)

    def test_unauthenticated_returns_401(self):
        response = self.client.get(OPTIONS_URL)
        self.assertEqual(response.status_code, 401)

    def test_returns_200(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(OPTIONS_URL)
        self.assertEqual(response.status_code, 200)

    def test_response_has_success_flag(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(OPTIONS_URL)
        self.assertTrue(response.data["success"])

    def test_returns_only_active_skills(self):
        make_skill("Python", is_active=True)
        make_skill("COBOL", is_active=False)
        self.client.force_authenticate(user=self.user)
        response = self.client.get(OPTIONS_URL)
        skills = [e["skill"] for e in response.data["data"]]
        self.assertIn("Python", skills)
        self.assertNotIn("COBOL", skills)

    def test_returns_empty_list_when_no_active_skills(self):
        make_skill("COBOL", is_active=False)
        self.client.force_authenticate(user=self.user)
        response = self.client.get(OPTIONS_URL)
        self.assertEqual(response.data["data"], [])

    def test_each_entry_has_code_and_skill(self):
        skill = make_skill("Python", is_active=True)
        self.client.force_authenticate(user=self.user)
        response = self.client.get(OPTIONS_URL)
        entry = response.data["data"][0]
        self.assertIn("code", entry)
        self.assertIn("skill", entry)
        self.assertEqual(entry["code"], skill.code)
        self.assertEqual(entry["skill"], "Python")

    def test_does_not_include_extra_fields(self):
        make_skill("Python", is_active=True)
        self.client.force_authenticate(user=self.user)
        response = self.client.get(OPTIONS_URL)
        entry = response.data["data"][0]
        self.assertEqual(set(entry.keys()), {"code", "skill"})

    def test_results_ordered_alphabetically(self):
        make_skill("Rust", is_active=True)
        make_skill("Go", is_active=True)
        make_skill("Python", is_active=True)
        self.client.force_authenticate(user=self.user)
        response = self.client.get(OPTIONS_URL)
        names = [e["skill"] for e in response.data["data"]]
        self.assertEqual(names, sorted(names))


# ── GET /skills/<code>/ ───────────────────────────────────────────────────────


class SkillRetrieveAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)
        self.skill = make_skill("Python")

    def test_returns_skill_detail(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(DETAIL_URL.format(self.skill.code))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["data"]["skill"], "Python")

    def test_returns_404_for_unknown_code(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(DETAIL_URL.format("SKILL-9999"))
        self.assertEqual(response.status_code, 404)

    def test_response_includes_required_fields(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(DETAIL_URL.format(self.skill.code))
        data = response.data["data"]
        for field in [
            "code",
            "skill",
            "description",
            "is_active",
            "created_at",
            "updated_at",
        ]:
            self.assertIn(field, data)


# ── POST /skills/ ─────────────────────────────────────────────────────────────


class SkillCreateAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)

    def test_creates_skill(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(LIST_URL, {"skill": "Python"}, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["data"]["skill"], "Python")

    def test_creates_skill_with_description(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            LIST_URL, {"skill": "Python", "description": "Core language"}, format="json"
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["data"]["description"], "Core language")

    def test_creates_skill_with_is_active_false(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            LIST_URL, {"skill": "Python", "is_active": False}, format="json"
        )
        self.assertEqual(response.status_code, 201)
        self.assertFalse(response.data["data"]["is_active"])

    def test_duplicate_skill_returns_409(self):
        make_skill("Python")
        self.client.force_authenticate(user=self.user)
        response = self.client.post(LIST_URL, {"skill": "Python"}, format="json")
        self.assertEqual(response.status_code, 409)

    def test_missing_skill_returns_400(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(LIST_URL, {}, format="json")
        self.assertEqual(response.status_code, 400)

    def test_unauthenticated_returns_401(self):
        response = self.client.post(LIST_URL, {"skill": "Python"}, format="json")
        self.assertEqual(response.status_code, 401)


# ── PATCH /skills/<code>/ ─────────────────────────────────────────────────────


class SkillUpdateAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)
        self.skill = make_skill("Python")

    def test_updates_skill(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.patch(
            DETAIL_URL.format(self.skill.code), {"skill": "Rust"}, format="json"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["data"]["skill"], "Rust")

    def test_duplicate_skill_returns_409(self):
        make_skill("Java")
        self.client.force_authenticate(user=self.user)
        response = self.client.patch(
            DETAIL_URL.format(self.skill.code), {"skill": "Java"}, format="json"
        )
        self.assertEqual(response.status_code, 409)

    def test_returns_404_for_unknown_code(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.patch(
            DETAIL_URL.format("SKILL-9999"), {"skill": "X"}, format="json"
        )
        self.assertEqual(response.status_code, 404)

    def test_unauthenticated_returns_401(self):
        response = self.client.patch(
            DETAIL_URL.format(self.skill.code), {"skill": "X"}, format="json"
        )
        self.assertEqual(response.status_code, 401)


# ── DELETE /skills/<code>/ ────────────────────────────────────────────────────


class SkillDeleteAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)
        self.skill = make_skill("Python")

    def test_deletes_skill(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.delete(DETAIL_URL.format(self.skill.code))
        self.assertEqual(response.status_code, 204)
        self.assertFalse(Skill.objects.filter(pk=self.skill.pk).exists())

    def test_returns_404_for_unknown_code(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.delete(DETAIL_URL.format("SKILL-9999"))
        self.assertEqual(response.status_code, 404)

    def test_unauthenticated_returns_401(self):
        response = self.client.delete(DETAIL_URL.format(self.skill.code))
        self.assertEqual(response.status_code, 401)


# ── POST /skills/<code>/activate/ and /deactivate/ ───────────────────────────


class SkillActivateAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)

    def test_activates_inactive_skill(self):
        skill = make_skill("Python", is_active=False)
        self.client.force_authenticate(user=self.user)
        response = self.client.post(ACTIVATE_URL.format(skill.code))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["data"]["is_active"])

    def test_activate_idempotent(self):
        skill = make_skill("Python", is_active=True)
        self.client.force_authenticate(user=self.user)
        response = self.client.post(ACTIVATE_URL.format(skill.code))
        self.assertEqual(response.status_code, 200)

    def test_deactivates_active_skill(self):
        skill = make_skill("Java", is_active=True)
        self.client.force_authenticate(user=self.user)
        response = self.client.post(DEACTIVATE_URL.format(skill.code))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.data["data"]["is_active"])

    def test_activate_returns_404_for_unknown_code(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(ACTIVATE_URL.format("SKILL-9999"))
        self.assertEqual(response.status_code, 404)

    def test_deactivate_returns_404_for_unknown_code(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(DEACTIVATE_URL.format("SKILL-9999"))
        self.assertEqual(response.status_code, 404)

    def test_unauthenticated_activate_returns_401(self):
        skill = make_skill("Python", is_active=False)
        response = self.client.post(ACTIVATE_URL.format(skill.code))
        self.assertEqual(response.status_code, 401)

    def test_unauthenticated_deactivate_returns_401(self):
        skill = make_skill("Python", is_active=True)
        response = self.client.post(DEACTIVATE_URL.format(skill.code))
        self.assertEqual(response.status_code, 401)


# ── GET /skills/export/ ───────────────────────────────────────────────────────


class SkillExportAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)
        make_skill("Python")

    def test_unauthenticated_returns_401(self):
        response = self.client.get(EXPORT_URL)
        self.assertEqual(response.status_code, 401)

    def test_export_csv_returns_200(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(EXPORT_URL)
        self.assertEqual(response.status_code, 200)

    def test_export_specs_returns_200(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(EXPORT_SPECS_URL)
        self.assertEqual(response.status_code, 200)

    def test_export_specs_unauthenticated_returns_401(self):
        response = self.client.get(EXPORT_SPECS_URL)
        self.assertEqual(response.status_code, 401)


# ── POST /skills/import/ ──────────────────────────────────────────────────────


class SkillImportAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)

    def test_import_specs_returns_200(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(IMPORT_SPECS_URL)
        self.assertEqual(response.status_code, 200)

    def test_import_sample_returns_200(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(IMPORT_SAMPLE_URL)
        self.assertEqual(response.status_code, 200)

    def test_import_unauthenticated_returns_401(self):
        response = self.client.post(IMPORT_URL)
        self.assertEqual(response.status_code, 401)

    def test_import_specs_unauthenticated_returns_401(self):
        response = self.client.get(IMPORT_SPECS_URL)
        self.assertEqual(response.status_code, 401)

    def test_csv_import_creates_skills(self):
        self.client.force_authenticate(user=self.user)
        csv_content = b"skill\nPython\nJava"
        f = io.BytesIO(csv_content)
        f.name = "skills.csv"
        response = self.client.post(IMPORT_URL, {"file": f}, format="multipart")
        self.assertEqual(response.status_code, 207)
        self.assertTrue(Skill.objects.filter(skill="Python").exists())
        self.assertTrue(Skill.objects.filter(skill="Java").exists())

    def test_import_without_file_returns_422(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(IMPORT_URL, {}, format="multipart")
        self.assertEqual(response.status_code, 422)
