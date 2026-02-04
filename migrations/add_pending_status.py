#!/usr/bin/env python3
"""
Migration: add support for TaskStatus 'pending' in databases that enforce enums.

Why:
- Older MySQL installs may use ENUM columns for `task.status` and `changelog.old_status/new_status`.
- Adding a new enum value in Python isn't enough; MySQL must be altered to accept it.

This script is safe to run multiple times (idempotent where possible).
"""

from __future__ import annotations

import sys
from pathlib import Path
import re
from typing import List, Optional

from sqlalchemy import text

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.models.database import engine


def _parse_mysql_enum_values(column_type: str) -> Optional[List[str]]:
    """
    Parse a MySQL COLUMN_TYPE string like:
      enum('a','b','c')
    into a list of values.
    """
    m = re.match(r"^enum\((.*)\)$", column_type.strip(), re.IGNORECASE)
    if not m:
        return None
    inner = m.group(1)
    # Values are single-quoted and comma-separated; handle escaped quotes via backslash.
    values = []
    current = ""
    in_quote = False
    escape = False
    for ch in inner:
        if escape:
            current += ch
            escape = False
            continue
        if ch == "\\":
            escape = True
            continue
        if ch == "'":
            in_quote = not in_quote
            if not in_quote:
                values.append(current)
                current = ""
            continue
        if in_quote:
            current += ch
    return values


def _mysql_pick_pending_token(values: List[str]) -> str:
    """
    Some legacy DBs store enum members as uppercase names (e.g. 'CREATED'),
    others store lowercase values (e.g. 'created').

    Prefer matching the existing style.
    """
    has_upper = any(v == v.upper() and v != v.lower() for v in values)
    has_lower = any(v == v.lower() and v != v.upper() for v in values)
    if has_upper and not has_lower:
        return "PENDING"
    return "pending"


def _mysql_get_column_type(conn, table_name: str, column_name: str) -> Optional[str]:
    row = conn.execute(
        text(
            """
            SELECT COLUMN_TYPE
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = DATABASE()
              AND TABLE_NAME = :table_name
              AND COLUMN_NAME = :column_name
            """
        ),
        {"table_name": table_name, "column_name": column_name},
    ).fetchone()
    return row[0] if row else None


def _mysql_get_column_default(conn, table_name: str, column_name: str) -> Optional[str]:
    row = conn.execute(
        text(
            """
            SELECT COLUMN_DEFAULT
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = DATABASE()
              AND TABLE_NAME = :table_name
              AND COLUMN_NAME = :column_name
            """
        ),
        {"table_name": table_name, "column_name": column_name},
    ).fetchone()
    return row[0] if row else None


def _mysql_column_is_nullable(conn, table_name: str, column_name: str) -> Optional[bool]:
    row = conn.execute(
        text(
            """
            SELECT IS_NULLABLE
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = DATABASE()
              AND TABLE_NAME = :table_name
              AND COLUMN_NAME = :column_name
            """
        ),
        {"table_name": table_name, "column_name": column_name},
    ).fetchone()
    if not row:
        return None
    return str(row[0]).upper() == "YES"


def _mysql_set_column_default(
    conn,
    *,
    table_name: str,
    column_name: str,
    default_value: str,
) -> bool:
    """
    For non-ENUM columns (VARCHAR/TEXT), ensure a DB-level default exists.
    Returns True if an ALTER was executed.
    """
    current_default = _mysql_get_column_default(conn, table_name, column_name)
    if current_default == default_value:
        return False

    column_type = _mysql_get_column_type(conn, table_name, column_name)
    if not column_type:
        print(f"⚠️  MySQL: {table_name}.{column_name} not found; skipping default change")
        return False

    nullable = _mysql_column_is_nullable(conn, table_name, column_name)
    null_sql = "NULL" if nullable else "NOT NULL"
    alter_sql = (
        f"ALTER TABLE {table_name} "
        f"MODIFY COLUMN {column_name} {column_type} {null_sql} DEFAULT '{default_value}'"
    )
    print(f"🔧 MySQL: setting default for {table_name}.{column_name} to '{default_value}'")
    conn.execute(text(alter_sql))
    return True


def _mysql_alter_enum_add_value(
    conn,
    *,
    table_name: str,
    column_name: str,
    new_value: str,
    set_default: Optional[str] = None,
) -> bool:
    """
    If the column is an ENUM, append `new_value` (preserving existing values) and alter the column.
    Returns True if an ALTER was executed.
    """
    column_type = _mysql_get_column_type(conn, table_name, column_name)
    if not column_type:
        print(f"⚠️  MySQL: {table_name}.{column_name} not found; skipping")
        return False

    values = _parse_mysql_enum_values(column_type)
    if values is None:
        # Not an enum (likely TEXT/VARCHAR) — no migration needed.
        print(f"ℹ️  MySQL: {table_name}.{column_name} is not ENUM; skipping enum expansion")
        return False

    if new_value in values:
        print(f"✅ MySQL: {table_name}.{column_name} already includes '{new_value}'")
        return False

    values.append(new_value)
    nullable = _mysql_column_is_nullable(conn, table_name, column_name)
    null_sql = "NULL" if nullable else "NOT NULL"
    def _sql_quote(value: str) -> str:
        # In SQL string literals, escape single quotes by doubling them.
        return "'" + value.replace("'", "''") + "'"

    enum_sql = ",".join([_sql_quote(v) for v in values])
    default_sql = f" DEFAULT '{set_default}'" if set_default else ""

    alter_sql = (
        f"ALTER TABLE {table_name} "
        f"MODIFY COLUMN {column_name} ENUM({enum_sql}) {null_sql}{default_sql}"
    )
    print(f"🔧 MySQL: altering {table_name}.{column_name} to add '{new_value}'")
    conn.execute(text(alter_sql))
    return True


def migrate():
    print("Starting migration: add TaskStatus 'pending' support...")

    dialect = engine.dialect.name.lower()
    with engine.connect() as conn:
        if dialect == "mysql":
            changed = False
            # Ensure DB-level default (some environments set statuses directly in DB).
            task_status_type = _mysql_get_column_type(conn, "task", "status")
            task_status_values = _parse_mysql_enum_values(task_status_type or "") or []
            pending_token = _mysql_pick_pending_token(task_status_values)
            changed |= _mysql_set_column_default(
                conn,
                table_name="task",
                column_name="status",
                default_value=pending_token,
            )
            changed |= _mysql_alter_enum_add_value(
                conn,
                table_name="task",
                column_name="status",
                new_value=pending_token,
                set_default=pending_token,
            )
            changed |= _mysql_alter_enum_add_value(
                conn,
                table_name="changelog",
                column_name="old_status",
                new_value=pending_token,
            )
            changed |= _mysql_alter_enum_add_value(
                conn,
                table_name="changelog",
                column_name="new_status",
                new_value=pending_token,
            )
            if changed:
                conn.commit()
            print("✅ Migration completed (MySQL).")
            return

        if dialect == "sqlite":
            # SQLite typically stores enums as TEXT without a constraint.
            # If you have a legacy CHECK constraint, you may need to rebuild the table.
            print("✅ Migration not required for SQLite (status stored as TEXT).")
            return

        if dialect in {"postgresql", "postgres"}:
            # This project commonly uses TEXT, but if an enum type is used, it must be altered.
            # We intentionally no-op here to avoid guessing type names.
            print("ℹ️  PostgreSQL detected; no automatic enum migration applied.")
            print("   If task.status uses a Postgres enum type, add 'pending' via ALTER TYPE ... ADD VALUE.")
            return

        print(f"ℹ️  Unsupported/unknown dialect '{dialect}'; no changes applied.")


if __name__ == "__main__":
    migrate()
