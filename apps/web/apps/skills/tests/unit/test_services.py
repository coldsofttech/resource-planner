from django.test import SimpleTestCase

from apps.core.exceptions import ValidationException
from apps.skills.services import SkillImportService
from apps.skills.tests.factories import make_csv_file


class SkillImportValidateFileTest(SimpleTestCase):
    def setUp(self):
        self.svc = SkillImportService(user=None)

    def test_accepts_csv_file(self):
        f = make_csv_file("skill\nPython", "skills.csv")
        self.svc.validate_file(f)

    def test_rejects_unsupported_extension(self):
        f = make_csv_file("skill\nPython", "skills.xlsx")
        with self.assertRaises(ValidationException):
            self.svc.validate_file(f)

    def test_rejects_txt_extension(self):
        f = make_csv_file("skill\nPython", "skills.txt")
        with self.assertRaises(ValidationException):
            self.svc.validate_file(f)

    def test_rejects_file_exceeding_size_limit(self):
        f = make_csv_file("skill\nPython", "skills.csv")
        f.size = (SkillImportService.MAX_IMPORT_FILE_SIZE_MB + 1) * 1024 * 1024
        with self.assertRaises(ValidationException):
            self.svc.validate_file(f)

    def test_accepts_file_at_exact_size_limit(self):
        f = make_csv_file("skill\nPython", "skills.csv")
        f.size = SkillImportService.MAX_IMPORT_FILE_SIZE_MB * 1024 * 1024
        self.svc.validate_file(f)


class SkillImportValidateRowTest(SimpleTestCase):
    def setUp(self):
        self.svc = SkillImportService(user=None)

    def test_valid_row_returns_no_errors(self):
        errors = self.svc.validate_row({"skill": "Python"}, row_num=2)
        self.assertEqual(errors, [])

    def test_missing_skill_returns_error(self):
        errors = self.svc.validate_row({"skill": ""}, row_num=2)
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0]["field"], "skill")

    def test_skill_exceeding_max_length_returns_error(self):
        errors = self.svc.validate_row({"skill": "A" * 21}, row_num=3)
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0]["field"], "skill")

    def test_skill_at_max_length_is_valid(self):
        errors = self.svc.validate_row({"skill": "A" * 20}, row_num=2)
        self.assertEqual(errors, [])

    def test_error_includes_row_number(self):
        errors = self.svc.validate_row({"skill": ""}, row_num=5)
        self.assertEqual(errors[0]["row"], 5)

    def test_whitespace_only_skill_is_invalid(self):
        errors = self.svc.validate_row({"skill": "   "}, row_num=2)
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0]["field"], "skill")

    def test_none_skill_is_invalid(self):
        errors = self.svc.validate_row({"skill": None}, row_num=2)
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0]["field"], "skill")
