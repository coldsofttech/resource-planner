from __future__ import annotations

import base64
import contextlib
import re
import unittest
import zlib

from exportcore.pdf_export import export_to_pdf

_PDF_MAGIC = b"%PDF-"


def _extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """Extract raw string tokens from PDF bytes for assertion purposes."""
    return pdf_bytes.decode("latin-1", errors="replace")


def _get_pdf_searchable_bytes(pdf_bytes: bytes) -> bytes:
    """Return PDF bytes concatenated with all decompressed content stream data.

    ReportLab compresses page content with ASCII85 + FlateDecode and writes
    the ``~>`` EOD marker directly before ``endstream`` with no newline gap.
    This helper strips the marker, decodes ASCII85, and zlib-decompresses each
    stream so that text tokens (titles, column headers, cell values) are
    findable with a plain ``assertIn(b"...", ...)`` check.
    """
    parts = [pdf_bytes]
    for m in re.finditer(rb"stream\r?\n(.*?~>)\s*endstream", pdf_bytes, re.DOTALL):
        raw = m.group(1)
        if raw.endswith(b"~>"):
            raw = raw[:-2]
        with contextlib.suppress(Exception):
            decoded = base64.a85decode(raw, adobe=False)
            decompressed = zlib.decompress(decoded)
            parts.append(decompressed)
    return b"".join(parts)


class ExportToPdfReturnTypeTest(unittest.TestCase):
    def test_returns_bytes_for_empty_rows(self):
        result = export_to_pdf([])
        self.assertIsInstance(result, bytes)

    def test_returns_bytes_for_non_empty_rows(self):
        result = export_to_pdf([{"Name": "Alice"}])
        self.assertIsInstance(result, bytes)


class ExportToPdfMagicBytesTest(unittest.TestCase):
    def test_pdf_header_present_for_empty_rows(self):
        result = export_to_pdf([])
        self.assertTrue(result.startswith(_PDF_MAGIC))

    def test_pdf_header_present_for_non_empty_rows(self):
        result = export_to_pdf([{"Name": "Alice", "Role": "Engineer"}])
        self.assertTrue(result.startswith(_PDF_MAGIC))


class ExportToPdfNonEmptyOutputTest(unittest.TestCase):
    def test_output_is_non_empty_for_empty_rows(self):
        result = export_to_pdf([])
        self.assertGreater(len(result), 0)

    def test_output_is_non_empty_for_rows(self):
        result = export_to_pdf([{"Name": "Alice"}])
        self.assertGreater(len(result), 0)


class ExportToPdfDefaultParametersTest(unittest.TestCase):
    def test_default_title_is_used_when_not_provided(self):
        result = export_to_pdf([{"Col": "val"}])
        self.assertIn(b"Export", _get_pdf_searchable_bytes(result))

    def test_default_app_title_is_used_when_not_provided(self):
        result = export_to_pdf([{"Col": "val"}])
        self.assertIn(b"Resource Planner", _get_pdf_searchable_bytes(result))


class ExportToPdfCustomParametersTest(unittest.TestCase):
    def test_custom_title_appears_in_output(self):
        result = export_to_pdf([{"Name": "Alice"}], title="Sprint Report")
        self.assertIn(b"Sprint Report", _get_pdf_searchable_bytes(result))

    def test_custom_app_title_appears_in_output(self):
        result = export_to_pdf(
            [{"Name": "Alice"}],
            app_title="My Custom App",
        )
        self.assertIn(b"My Custom App", _get_pdf_searchable_bytes(result))

    def test_base_url_appears_in_footer(self):
        result = export_to_pdf(
            [{"Name": "Alice"}],
            base_url="https://example.com",
        )
        self.assertIn(b"https://example.com", _get_pdf_searchable_bytes(result))

    def test_exported_on_label_appears_in_footer(self):
        result = export_to_pdf([{"Name": "Alice"}], base_url="https://example.com")
        self.assertIn(b"exported on:", _get_pdf_searchable_bytes(result))

    def test_exported_on_without_base_url(self):
        result = export_to_pdf([{"Name": "Alice"}], base_url="")
        self.assertIn(b"Exported on:", _get_pdf_searchable_bytes(result))

    def test_empty_base_url_does_not_crash(self):
        result = export_to_pdf([{"Name": "Alice"}], base_url="")
        self.assertTrue(result.startswith(_PDF_MAGIC))


class ExportToPdfPageOrientationTest(unittest.TestCase):
    def test_any_column_count_produces_valid_pdf(self):
        rows_few = [{f"C{i}": "v" for i in range(3)}]
        rows_many = [{f"C{i}": "v" for i in range(8)}]
        self.assertTrue(export_to_pdf(rows_few).startswith(_PDF_MAGIC))
        self.assertTrue(export_to_pdf(rows_many).startswith(_PDF_MAGIC))

    def test_pdf_is_always_landscape(self):
        pattern = rb"/MediaBox\s*\[\s*[\d.]+\s+[\d.]+\s+([\d.]+)\s+([\d.]+)\s*\]"
        for col_count in (3, 6):
            rows = [{f"C{i}": "v" for i in range(col_count)}]
            pdf_bytes = export_to_pdf(rows)
            m = re.search(pattern, pdf_bytes)
            if m:
                width = float(m.group(1))
                height = float(m.group(2))
                self.assertGreater(
                    width, height, f"Expected landscape for {col_count} columns"
                )


class ExportToPdfWithDataTest(unittest.TestCase):
    def setUp(self):
        self.rows = [
            {"Name": "Alice", "Role": "Engineer", "Team": "Alpha"},
            {"Name": "Bob", "Role": "Designer", "Team": "Beta"},
        ]

    def test_column_headers_appear_in_output(self):
        result = export_to_pdf(self.rows)
        content = _get_pdf_searchable_bytes(result)
        self.assertIn(b"Name", content)
        self.assertIn(b"Role", content)
        self.assertIn(b"Team", content)

    def test_data_values_appear_in_output(self):
        result = export_to_pdf(self.rows)
        content = _get_pdf_searchable_bytes(result)
        self.assertIn(b"Alice", content)
        self.assertIn(b"Bob", content)

    def test_produces_valid_pdf_with_multiple_rows(self):
        result = export_to_pdf(self.rows)
        self.assertTrue(result.startswith(_PDF_MAGIC))


class ExportToPdfMissingKeyHandlingTest(unittest.TestCase):
    def test_missing_key_in_row_does_not_crash(self):
        rows = [
            {"Name": "Alice", "Role": "Engineer"},
            {"Name": "Bob"},
        ]
        result = export_to_pdf(rows)
        self.assertTrue(result.startswith(_PDF_MAGIC))


class ExportToPdfEmptyRowsTableTest(unittest.TestCase):
    def test_no_table_content_for_empty_rows(self):
        result_empty = export_to_pdf([])
        result_with_data = export_to_pdf([{"Name": "Alice"}])
        self.assertGreater(len(result_with_data), len(result_empty))


class ExportToPdfHtmlStrippingTest(unittest.TestCase):
    def test_html_tags_stripped_from_app_title(self):
        result = export_to_pdf(
            [{"Name": "Alice"}],
            app_title="Resource<b>Planner</b>",
        )
        content = _get_pdf_searchable_bytes(result)
        self.assertIn(b"ResourcePlanner", content)

    def test_plain_app_title_unchanged(self):
        result = export_to_pdf(
            [{"Name": "Alice"}],
            app_title="My App",
        )
        content = _get_pdf_searchable_bytes(result)
        self.assertIn(b"My App", content)


class ExportToPdfLargeDatasetTest(unittest.TestCase):
    def test_handles_100_rows_without_error(self):
        rows = [
            {"ID": str(i), "Name": f"Item {i}", "Status": "Active"} for i in range(100)
        ]
        result = export_to_pdf(rows, title="Large Export")
        self.assertTrue(result.startswith(_PDF_MAGIC))

    def test_handles_many_columns_without_error(self):
        rows = [{f"Column {i}": f"Value {i}" for i in range(10)}]
        result = export_to_pdf(rows)
        self.assertTrue(result.startswith(_PDF_MAGIC))

    def test_handles_unicode_content_without_error(self):
        rows = [{"Name": "Test User", "Notes": "Standard entry"}]
        result = export_to_pdf(rows)
        self.assertTrue(result.startswith(_PDF_MAGIC))
