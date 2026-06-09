import base64
import os
import tempfile
import unittest
from unittest.mock import MagicMock, patch


class TestStoreDatabaseBackend(unittest.TestCase):
    def test_returns_data_uri_prefix(self):
        from storagecore.storage import store

        uri = store(b"hello", "test.txt", "docs", "database")
        self.assertTrue(uri.startswith("data:text/plain;base64,"))

    def test_encodes_content_correctly(self):
        from storagecore.storage import store

        content = b"hello world"
        uri = store(content, "file.txt", "docs", "database")
        _, data = uri.split(",", 1)
        self.assertEqual(base64.b64decode(data), content)

    def test_explicit_content_type_used(self):
        from storagecore.storage import store

        uri = store(b"\x89PNG", "pic.png", "imgs", "database", content_type="image/png")
        self.assertTrue(uri.startswith("data:image/png;base64,"))

    def test_empty_content_produces_valid_uri(self):
        from storagecore.storage import store

        uri = store(b"", "empty.bin", "misc", "database")
        _, data = uri.split(",", 1)
        self.assertEqual(base64.b64decode(data), b"")

    def test_image_mime_inferred_from_extension(self):
        from storagecore.storage import store

        uri = store(b"x", "photo.jpg", "imgs", "database")
        self.assertTrue(uri.startswith("data:image/jpeg;base64,"))


class TestStoreFilesystemBackend(unittest.TestCase):
    def test_writes_file_and_returns_file_uri(self):
        from storagecore.storage import store

        with tempfile.TemporaryDirectory() as base:
            uri = store(b"data", "img.png", "avatars", "filesystem", storage_path=base)
            expected = os.path.join(base, "avatars", "img.png")
            self.assertEqual(uri, f"file:{expected}")
            self.assertTrue(os.path.exists(expected))

    def test_creates_missing_parent_directories(self):
        from storagecore.storage import store

        with tempfile.TemporaryDirectory() as base:
            store(b"x", "f.bin", "a/b/c", "filesystem", storage_path=base)
            self.assertTrue(os.path.exists(os.path.join(base, "a", "b", "c", "f.bin")))

    def test_content_written_to_disk(self):
        from storagecore.storage import store

        content = b"test content 123"
        with tempfile.TemporaryDirectory() as base:
            uri = store(content, "out.bin", "misc", "filesystem", storage_path=base)
            path = uri[len("file:") :]
            with open(path, "rb") as fh:
                self.assertEqual(fh.read(), content)

    def test_uri_has_file_prefix(self):
        from storagecore.storage import store

        with tempfile.TemporaryDirectory() as base:
            uri = store(b"x", "f.txt", "docs", "filesystem", storage_path=base)
            self.assertTrue(uri.startswith("file:"))

    def test_overwrite_existing_file(self):
        from storagecore.storage import store

        with tempfile.TemporaryDirectory() as base:
            store(b"first", "f.txt", "docs", "filesystem", storage_path=base)
            store(b"second", "f.txt", "docs", "filesystem", storage_path=base)
            path = os.path.join(base, "docs", "f.txt")
            with open(path, "rb") as fh:
                self.assertEqual(fh.read(), b"second")


class TestStoreS3Backend(unittest.TestCase):
    def test_calls_put_and_returns_aws_uri(self):
        from storagecore.storage import store

        arn = "arn:aws:s3:::my-bucket"
        with patch("storagecore.s3.S3Client") as MockS3:
            client = MagicMock()
            MockS3.return_value = client
            uri = store(
                b"img",
                "pic.jpg",
                "user_avatars",
                "s3",
                storage_path=arn,
                aws_region="us-east-1",
            )
        client.put.assert_called_once_with(
            "my-bucket", "user_avatars/pic.jpg", b"img", "image/jpeg"
        )
        self.assertEqual(uri, "aws:arn:aws:s3:::my-bucket/user_avatars/pic.jpg")

    def test_uri_starts_with_aws_prefix(self):
        from storagecore.storage import store

        with patch("storagecore.s3.S3Client") as MockS3:
            MockS3.return_value = MagicMock()
            uri = store(b"x", "f.png", "imgs", "s3", storage_path="arn:aws:s3:::bucket")
        self.assertTrue(uri.startswith("aws:arn:aws:s3:::"))

    def test_key_uses_folder_and_filename(self):
        from storagecore.storage import store

        with patch("storagecore.s3.S3Client") as MockS3:
            client = MagicMock()
            MockS3.return_value = client
            store(
                b"x",
                "avatar.png",
                "user_avatars",
                "s3",
                storage_path="arn:aws:s3:::bucket",
            )
        _, call_kwargs = client.put.call_args
        args = client.put.call_args[0]
        self.assertEqual(args[1], "user_avatars/avatar.png")


class TestStoreUnknownBackend(unittest.TestCase):
    def test_raises_value_error(self):
        from storagecore.storage import store

        with self.assertRaises(ValueError):
            store(b"x", "f.txt", "docs", "ftp")


class TestRetrieve(unittest.TestCase):
    def test_data_uri_decoded(self):
        from storagecore.storage import retrieve

        content = b"hello"
        b64 = base64.b64encode(content).decode()
        uri = f"data:text/plain;base64,{b64}"
        self.assertEqual(retrieve(uri), content)

    def test_file_uri_reads_disk(self):
        from storagecore.storage import retrieve

        with tempfile.TemporaryDirectory() as base:
            path = os.path.join(base, "test.txt")
            with open(path, "wb") as fh:
                fh.write(b"file content")
            self.assertEqual(retrieve(f"file:{path}"), b"file content")

    def test_s3_uri_calls_client_get(self):
        from storagecore.storage import retrieve

        with patch("storagecore.s3.S3Client") as MockS3:
            client = MagicMock()
            client.get.return_value = b"s3 data"
            MockS3.return_value = client
            result = retrieve(
                "aws:arn:aws:s3:::my-bucket/user_avatars/pic.jpg",
                aws_region="eu-west-1",
            )
        client.get.assert_called_once_with("my-bucket", "user_avatars/pic.jpg")
        self.assertEqual(result, b"s3 data")

    def test_unknown_uri_raises(self):
        from storagecore.storage import retrieve

        with self.assertRaises(ValueError):
            retrieve("ftp://example.com/file.txt")


class TestDelete(unittest.TestCase):
    def test_data_uri_is_noop(self):
        from storagecore.storage import delete

        delete("data:image/png;base64,abc")  # must not raise

    def test_file_uri_removes_file(self):
        from storagecore.storage import delete

        with tempfile.TemporaryDirectory() as base:
            path = os.path.join(base, "f.txt")
            with open(path, "wb") as fh:
                fh.write(b"x")
            delete(f"file:{path}")
            self.assertFalse(os.path.exists(path))

    def test_file_uri_missing_file_is_noop(self):
        from storagecore.storage import delete

        delete("file:/nonexistent/path/file.txt")  # must not raise

    def test_s3_uri_calls_client_delete(self):
        from storagecore.storage import delete

        with patch("storagecore.s3.S3Client") as MockS3:
            client = MagicMock()
            MockS3.return_value = client
            delete("aws:arn:aws:s3:::my-bucket/imgs/pic.jpg")
        client.delete.assert_called_once_with("my-bucket", "imgs/pic.jpg")

    def test_unknown_uri_raises(self):
        from storagecore.storage import delete

        with self.assertRaises(ValueError):
            delete("ftp://bad.uri/f.txt")


class TestParseHelpers(unittest.TestCase):
    def test_parse_s3_uri_bucket_and_key(self):
        from storagecore.storage import _parse_s3_uri

        bucket, key = _parse_s3_uri("aws:arn:aws:s3:::my-bucket/user_avatars/pic.jpg")
        self.assertEqual(bucket, "my-bucket")
        self.assertEqual(key, "user_avatars/pic.jpg")

    def test_parse_s3_uri_nested_key(self):
        from storagecore.storage import _parse_s3_uri

        bucket, key = _parse_s3_uri("aws:arn:aws:s3:::b/a/b/c/file.png")
        self.assertEqual(bucket, "b")
        self.assertEqual(key, "a/b/c/file.png")

    def test_bucket_from_storage_path_arn(self):
        from storagecore.storage import _bucket_from_storage_path

        self.assertEqual(
            _bucket_from_storage_path("arn:aws:s3:::my-bucket"), "my-bucket"
        )

    def test_bucket_from_storage_path_with_trailing_slash(self):
        from storagecore.storage import _bucket_from_storage_path

        self.assertEqual(_bucket_from_storage_path("arn:aws:s3:::bucket/"), "bucket")

    def test_store_s3_uri_round_trip(self):
        from storagecore.storage import _parse_s3_uri, store

        with patch("storagecore.s3.S3Client") as MockS3:
            MockS3.return_value = MagicMock()
            uri = store(
                b"data",
                "avatar.png",
                "user_avatars",
                "s3",
                storage_path="arn:aws:s3:::test-bucket",
            )
        bucket, key = _parse_s3_uri(uri)
        self.assertEqual(bucket, "test-bucket")
        self.assertEqual(key, "user_avatars/avatar.png")
