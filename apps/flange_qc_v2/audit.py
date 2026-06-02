from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from apps.flange_qc_v2.domain import InspectionSnapshot, ValidationError


@dataclass(frozen=True)
class Migration:
    version: int
    sql: str


MIGRATIONS = (
    Migration(
        version=1,
        sql="""
        CREATE TABLE IF NOT EXISTS inspections (
            inspection_id TEXT PRIMARY KEY,
            product_code TEXT NOT NULL,
            product_spec_version TEXT NOT NULL,
            phase TEXT NOT NULL,
            decision TEXT NOT NULL,
            reason_codes_json TEXT NOT NULL,
            payload_json TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS rule_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            inspection_id TEXT NOT NULL,
            rule_id TEXT NOT NULL,
            decision TEXT NOT NULL,
            reason_code TEXT NOT NULL,
            payload_json TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (inspection_id) REFERENCES inspections(inspection_id)
        );
        CREATE TABLE IF NOT EXISTS qc_feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            inspection_id TEXT NOT NULL,
            feedback_type TEXT NOT NULL,
            payload_json TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (inspection_id) REFERENCES inspections(inspection_id)
        );
        """,
    ),
)


class AuditStore:
    def __init__(self, path: str | Path):
        self.path = Path(path)

    def initialize(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    version INTEGER PRIMARY KEY,
                    applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            applied = set(self._applied_versions(connection))
            for migration in MIGRATIONS:
                if migration.version in applied:
                    continue
                connection.executescript(migration.sql)
                connection.execute(
                    "INSERT INTO schema_migrations (version) VALUES (?)",
                    (migration.version,),
                )

    def applied_versions(self) -> list[int]:
        with self._connect() as connection:
            return self._applied_versions(connection)

    def append_inspection(self, snapshot: InspectionSnapshot) -> None:
        payload = snapshot.to_payload()
        product = payload["product"]
        try:
            with self._connect() as connection:
                connection.execute(
                    """
                    INSERT INTO inspections (
                        inspection_id,
                        product_code,
                        product_spec_version,
                        phase,
                        decision,
                        reason_codes_json,
                        payload_json,
                        created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        payload["inspection_id"],
                        product["code"],
                        product["spec_version"],
                        payload["phase"],
                        payload["decision"],
                        json.dumps(payload["reason_codes"], sort_keys=True),
                        json.dumps(payload, sort_keys=True),
                        payload["created_at"],
                    ),
                )
        except sqlite3.IntegrityError as exc:
            raise ValidationError(f"inspection already exists: {snapshot.inspection_id}") from exc

    def fetch_inspection(self, inspection_id: str) -> dict[str, Any] | None:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT
                    inspection_id,
                    product_code,
                    product_spec_version,
                    phase,
                    decision,
                    reason_codes_json,
                    payload_json,
                    created_at
                FROM inspections
                WHERE inspection_id = ?
                """,
                (inspection_id,),
            ).fetchone()
        if row is None:
            return None
        return {
            "inspection_id": row["inspection_id"],
            "product_code": row["product_code"],
            "product_spec_version": row["product_spec_version"],
            "phase": row["phase"],
            "decision": row["decision"],
            "reason_codes": json.loads(row["reason_codes_json"]),
            "payload": json.loads(row["payload_json"]),
            "created_at": row["created_at"],
        }

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def _applied_versions(self, connection: sqlite3.Connection) -> list[int]:
        rows = connection.execute(
            "SELECT version FROM schema_migrations ORDER BY version"
        ).fetchall()
        return [int(row["version"]) for row in rows]
