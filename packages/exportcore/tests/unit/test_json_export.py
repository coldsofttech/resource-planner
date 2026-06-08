from __future__ import annotations

import json
import unittest

from exportcore.json_export import export_to_json


class ExportToJsonEmptyRowsTest(unittest.TestCase):
    def test_returns_bytes_for_empty_rows(self):
        result = export_to_json([])
        self.assertIsInstance(result, bytes)

    def test_returns_empty_array_for_empty_rows(self):
        result = export_to_json([])
        parsed = json.loads(result.decode("utf-8"))
        self.assertEqual(parsed, [])


class ExportToJsonSingleRowTest(unittest.TestCase):
    def setUp(self):
        self.rows = [{"Name": "Alice", "Role": "Engineer"}]
        self.result = export_to_json(self.rows)

    def test_returns_bytes(self):
        self.assertIsInstance(self.result, bytes)

    def test_output_is_valid_utf8(self):
        decoded = self.result.decode("utf-8")
        self.assertIsInstance(decoded, str)

    def test_output_is_valid_json(self):
        parsed = json.loads(self.result.decode("utf-8"))
        self.assertIsInstance(parsed, list)

    def test_single_record_present(self):
        parsed = json.loads(self.result.decode("utf-8"))
        self.assertEqual(len(parsed), 1)
        self.assertEqual(parsed[0]["Name"], "Alice")
        self.assertEqual(parsed[0]["Role"], "Engineer")


class ExportToJsonMultipleRowsTest(unittest.TestCase):
    def setUp(self):
        self.rows = [
            {"Name": "Alice", "Role": "Engineer"},
            {"Name": "Bob", "Role": "Designer"},
            {"Name": "Carol", "Role": "Manager"},
        ]
        self.result = export_to_json(self.rows)

    def test_all_records_present(self):
        parsed = json.loads(self.result.decode("utf-8"))
        self.assertEqual(len(parsed), 3)

    def test_record_values_are_correct(self):
        parsed = json.loads(self.result.decode("utf-8"))
        names = [r["Name"] for r in parsed]
        self.assertIn("Alice", names)
        self.assertIn("Bob", names)
        self.assertIn("Carol", names)

    def test_column_order_matches_first_row_key_order(self):
        parsed = json.loads(self.result.decode("utf-8"))
        self.assertEqual(list(parsed[0].keys()), ["Name", "Role"])


class ExportToJsonSpecialCharactersTest(unittest.TestCase):
    def test_handles_unicode_content(self):
        rows = [{"Name": "Ångström", "City": "München"}]
        result = export_to_json(rows)
        parsed = json.loads(result.decode("utf-8"))
        self.assertEqual(parsed[0]["Name"], "Ångström")
        self.assertEqual(parsed[0]["City"], "München")

    def test_handles_empty_string_values(self):
        rows = [{"Name": "Alice", "Notes": ""}]
        result = export_to_json(rows)
        parsed = json.loads(result.decode("utf-8"))
        self.assertEqual(parsed[0]["Notes"], "")

    def test_handles_special_characters_in_keys(self):
        rows = [{"Created On": "2024-01-01", "Is Active": "Yes"}]
        result = export_to_json(rows)
        parsed = json.loads(result.decode("utf-8"))
        self.assertIn("Created On", parsed[0])
        self.assertIn("Is Active", parsed[0])

    def test_handles_boolean_like_string_values(self):
        rows = [{"Active": "Yes"}, {"Active": "No"}]
        result = export_to_json(rows)
        parsed = json.loads(result.decode("utf-8"))
        self.assertEqual(parsed[0]["Active"], "Yes")
        self.assertEqual(parsed[1]["Active"], "No")


class ExportToJsonLargeInputTest(unittest.TestCase):
    def test_handles_large_number_of_rows(self):
        rows = [{"Index": str(i), "Value": f"item_{i}"} for i in range(500)]
        result = export_to_json(rows)
        parsed = json.loads(result.decode("utf-8"))
        self.assertEqual(len(parsed), 500)

    def test_handles_many_columns(self):
        rows = [{f"Col{i}": f"val{i}" for i in range(25)}]
        result = export_to_json(rows)
        parsed = json.loads(result.decode("utf-8"))
        self.assertEqual(len(parsed[0]), 25)
