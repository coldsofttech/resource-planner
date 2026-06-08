"""Unit tests for apps.setup.constants — enum values and construction."""

from django.test import SimpleTestCase

from apps.setup.constants import DatabaseType, DeploymentType, EmailType, StorageType


class TestDeploymentType(SimpleTestCase):
    def test_local_value(self):
        self.assertEqual(DeploymentType.LOCAL.value, "local")

    def test_aws_value(self):
        self.assertEqual(DeploymentType.AWS.value, "aws")

    def test_from_string_local(self):
        self.assertEqual(DeploymentType("local"), DeploymentType.LOCAL)

    def test_from_string_aws(self):
        self.assertEqual(DeploymentType("aws"), DeploymentType.AWS)

    def test_invalid_value_raises(self):
        with self.assertRaises(ValueError):
            DeploymentType("gcp")

    def test_all_members_present(self):
        members = {m.value for m in DeploymentType}
        self.assertEqual(members, {"local", "aws"})


class TestDatabaseType(SimpleTestCase):
    def test_sqlite_value(self):
        self.assertEqual(DatabaseType.SQLITE.value, "sqlite")

    def test_postgresql_value(self):
        self.assertEqual(DatabaseType.POSTGRESQL.value, "postgresql")

    def test_from_string_sqlite(self):
        self.assertEqual(DatabaseType("sqlite"), DatabaseType.SQLITE)

    def test_from_string_postgresql(self):
        self.assertEqual(DatabaseType("postgresql"), DatabaseType.POSTGRESQL)

    def test_invalid_value_raises(self):
        with self.assertRaises(ValueError):
            DatabaseType("mysql")

    def test_all_members_present(self):
        members = {m.value for m in DatabaseType}
        self.assertEqual(members, {"sqlite", "postgresql"})


class TestStorageType(SimpleTestCase):
    def test_database_value(self):
        self.assertEqual(StorageType.DATABASE.value, "database")

    def test_filesystem_value(self):
        self.assertEqual(StorageType.FILE_SYSTEM.value, "filesystem")

    def test_s3_value(self):
        self.assertEqual(StorageType.AMAZON_S3.value, "s3")

    def test_from_string_database(self):
        self.assertEqual(StorageType("database"), StorageType.DATABASE)

    def test_from_string_filesystem(self):
        self.assertEqual(StorageType("filesystem"), StorageType.FILE_SYSTEM)

    def test_from_string_s3(self):
        self.assertEqual(StorageType("s3"), StorageType.AMAZON_S3)

    def test_invalid_value_raises(self):
        with self.assertRaises(ValueError):
            StorageType("gcs")

    def test_all_members_present(self):
        members = {m.value for m in StorageType}
        self.assertEqual(members, {"database", "filesystem", "s3"})


class TestEmailType(SimpleTestCase):
    def test_console_value(self):
        self.assertEqual(EmailType.CONSOLE.value, "console")

    def test_smtp_value(self):
        self.assertEqual(EmailType.SMTP.value, "smtp")

    def test_from_string_console(self):
        self.assertEqual(EmailType("console"), EmailType.CONSOLE)

    def test_from_string_smtp(self):
        self.assertEqual(EmailType("smtp"), EmailType.SMTP)

    def test_invalid_value_raises(self):
        with self.assertRaises(ValueError):
            EmailType("sendgrid")

    def test_all_members_present(self):
        members = {m.value for m in EmailType}
        self.assertEqual(members, {"console", "smtp"})
