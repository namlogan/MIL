import gc
import tempfile
import unittest
import warnings
from pathlib import Path

from apps.flange_qc_v2.audit import AuditStore, MIGRATIONS
from apps.flange_qc_v2.domain import InspectionSnapshot, ValidationError


class AuditMigrationTests(unittest.TestCase):
    def test_migrations_are_non_destructive_create_statements(self) -> None:
        sql = "\n".join(migration.sql.lower() for migration in MIGRATIONS)

        self.assertIn("create table if not exists inspections", sql)
        self.assertNotIn("drop table", sql)
        self.assertNotIn("delete from", sql)
        self.assertNotIn("alter table", sql)

    def test_initialize_records_applied_migration_versions(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            store = AuditStore(Path(tmpdir) / "audit.sqlite")

            store.initialize()

            self.assertEqual(store.applied_versions(), [migration.version for migration in MIGRATIONS])


class AuditStoreTests(unittest.TestCase):
    def test_append_and_fetch_inspection_snapshot(self) -> None:
        snapshot = InspectionSnapshot.bootstrap_blocked(
            inspection_id="insp-audit-001",
            product_code="UNKNOWN",
            reason_codes=["UNKNOWN_PRODUCT"],
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            store = AuditStore(Path(tmpdir) / "audit.sqlite")
            store.initialize()

            store.append_inspection(snapshot)
            record = store.fetch_inspection("insp-audit-001")

        self.assertIsNotNone(record)
        assert record is not None
        self.assertEqual(record["inspection_id"], "insp-audit-001")
        self.assertEqual(record["product_code"], "UNKNOWN")
        self.assertEqual(record["decision"], "BLOCKED")
        self.assertEqual(record["payload"]["reason_codes"], ["UNKNOWN_PRODUCT"])

    def test_duplicate_inspection_id_is_rejected(self) -> None:
        snapshot = InspectionSnapshot.bootstrap_blocked(
            inspection_id="insp-duplicate",
            product_code="UNKNOWN",
            reason_codes=["UNKNOWN_PRODUCT"],
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            store = AuditStore(Path(tmpdir) / "audit.sqlite")
            store.initialize()
            store.append_inspection(snapshot)

            with self.assertRaisesRegex(ValidationError, "inspection already exists"):
                store.append_inspection(snapshot)

    def test_store_operations_close_sqlite_connections(self) -> None:
        snapshot = InspectionSnapshot.bootstrap_blocked(
            inspection_id="insp-close-connection",
            product_code="UNKNOWN",
            reason_codes=["UNKNOWN_PRODUCT"],
        )
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always", ResourceWarning)
            with tempfile.TemporaryDirectory() as tmpdir:
                store = AuditStore(Path(tmpdir) / "audit.sqlite")
                store.initialize()
                store.append_inspection(snapshot)
                store.fetch_inspection("insp-close-connection")
                store.applied_versions()
            gc.collect()

        resource_warnings = [
            warning for warning in caught if issubclass(warning.category, ResourceWarning)
        ]
        self.assertEqual(resource_warnings, [])


if __name__ == "__main__":
    unittest.main()
