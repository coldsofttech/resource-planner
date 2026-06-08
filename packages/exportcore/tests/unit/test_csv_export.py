from __future__ import annotations

import csv
import io
import unittest

from exportcore.csv_export import export_to_csv


class ExportToCsvEmptyRowsTest(unittest.TestCase):
    def test_returns_bytes_for_empty_rows(self):
        result = export_to_csv([])
        self.assertIsInstance(result, bytes)

    def test_returns_empty_bytes_for_empty_rows(self):
        result = export_to_csv([])
        self.assertEqual(result, b"")


class ExportToCsvSingleRowTest(unittest.TestCase):
    def setUp(self):
        self.rows = [{"Name": "Alice", "Role": "Engineer"}]
        self.result = export_to_csv(self.rows)

    def test_returns_bytes(self):
        self.assertIsInstance(self.result, bytes)

    def test_output_is_valid_utf8(self):
        decoded = self.result.decode("utf-8")
        self.assertIsInstance(decoded, str)

    def test_header_row_is_present(self):
        reader = csv.DictReader(io.StringIO(self.result.decode("utf-8")))
        self.assertEqual(reader.fieldnames, ["Name", "Role"])

    def test_data_row_is_present(self):
        reader = csv.DictReader(io.StringIO(self.result.decode("utf-8")))
        rows = list(reader)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["Name"], "Alice")
        self.assertEqual(rows[0]["Role"], "Engineer")


class ExportToCsvMultipleRowsTest(unittest.TestCase):
    def setUp(self):
        self.rows = [
            {"Name": "Alice", "Role": "Engineer"},
            {"Name": "Bob", "Role": "Designer"},
            {"Name": "Carol", "Role": "Manager"},
        ]
        self.result = export_to_csv(self.rows)

    def test_all_data_rows_are_present(self):
        reader = csv.DictReader(io.StringIO(self.result.decode("utf-8")))
        rows = list(reader)
        self.assertEqual(len(rows), 3)

    def test_row_values_are_correct(self):
        reader = csv.DictReader(io.StringIO(self.result.decode("utf-8")))
        rows = list(reader)
        names = [r["Name"] for r in rows]
        self.assertIn("Alice", names)
        self.assertIn("Bob", names)
        self.assertIn("Carol", names)

    def test_column_order_matches_first_row_key_order(self):
        reader = csv.DictReader(io.StringIO(self.result.decode("utf-8")))
        self.assertEqual(reader.fieldnames, ["Name", "Role"])


class ExportToCsvColumnOrderTest(unittest.TestCase):
    def test_column_order_preserved_across_multiple_columns(self):
        rows = [{"A": "1", "B": "2", "C": "3", "D": "4"}]
        result = export_to_csv(rows)
        reader = csv.DictReader(io.StringIO(result.decode("utf-8")))
        self.assertEqual(reader.fieldnames, ["A", "B", "C", "D"])


class ExportToCsvSpecialCharactersTest(unittest.TestCase):
    def test_handles_commas_in_values(self):
        rows = [{"Name": "Smith, John", "City": "New York"}]
        result = export_to_csv(rows)
        reader = csv.DictReader(io.StringIO(result.decode("utf-8")))
        rows_parsed = list(reader)
        self.assertEqual(rows_parsed[0]["Name"], "Smith, John")

    def test_handles_double_quotes_in_values(self):
        rows = [{"Quote": 'She said "hello"'}]
        result = export_to_csv(rows)
        reader = csv.DictReader(io.StringIO(result.decode("utf-8")))
        rows_parsed = list(reader)
        self.assertEqual(rows_parsed[0]["Quote"], 'She said "hello"')

    def test_handles_newlines_in_values(self):
        rows = [{"Notes": "Line 1\nLine 2"}]
        result = export_to_csv(rows)
        reader = csv.DictReader(io.StringIO(result.decode("utf-8")))
        rows_parsed = list(reader)
        self.assertEqual(rows_parsed[0]["Notes"], "Line 1\nLine 2")

    def test_handles_unicode_content(self):
        rows = [{"Name": "Ångström", "City": "München"}]
        result = export_to_csv(rows)
        reader = csv.DictReader(io.StringIO(result.decode("utf-8")))
        rows_parsed = list(reader)
        self.assertEqual(rows_parsed[0]["Name"], "Ångström")
        self.assertEqual(rows_parsed[0]["City"], "München")

    def test_handles_empty_string_values(self):
        rows = [{"Name": "Alice", "Notes": ""}]
        result = export_to_csv(rows)
        reader = csv.DictReader(io.StringIO(result.decode("utf-8")))
        rows_parsed = list(reader)
        self.assertEqual(rows_parsed[0]["Notes"], "")

    def test_handles_boolean_like_string_values(self):
        rows = [{"Active": "Yes"}, {"Active": "No"}]
        result = export_to_csv(rows)
        reader = csv.DictReader(io.StringIO(result.decode("utf-8")))
        rows_parsed = list(reader)
        self.assertEqual(rows_parsed[0]["Active"], "Yes")
        self.assertEqual(rows_parsed[1]["Active"], "No")


class ExportToCsvOutputStructureTest(unittest.TestCase):
    def test_exactly_one_header_row(self):
        rows = [{"Col": "val1"}, {"Col": "val2"}]
        result = export_to_csv(rows)
        lines = result.decode("utf-8").splitlines()
        self.assertIn("Col", lines[0])

    def test_total_lines_equals_header_plus_data_rows(self):
        rows = [{"A": str(i)} for i in range(5)]
        result = export_to_csv(rows)
        reader = csv.DictReader(io.StringIO(result.decode("utf-8")))
        data_rows = list(reader)
        self.assertEqual(len(data_rows), 5)
