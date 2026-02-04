#!/usr/bin/env python3
"""
Backfill migration: move existing unstarted tasks from `created` to `pending`.

Use when you introduce `pending` as a readiness gate and you already have a backlog
of tasks sitting in `created` that should *not* be eligible for pickup yet.

Criteria (conservative):
- task.status == 'created'
- task.locked_by_id IS NULL (not currently assigned)
- there has never been a status transition on this task (no changelog rows where old_status != new_status)

This script is idempotent.
"""

from __future__ import annotations

import sys
from pathlib import Path

from sqlalchemy import text

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.models.database import engine


def migrate():
    print("Starting backfill: created → pending for unstarted tasks...")

    with engine.connect() as conn:
        # Update tasks
        update_tasks = conn.execute(
            text(
                """
                UPDATE task
                SET status = 'pending'
                WHERE status = 'created'
                  AND locked_by_id IS NULL
                  AND NOT EXISTS (
                    SELECT 1
                    FROM changelog c
                    WHERE c.task_id = task.id
                      AND c.old_status <> c.new_status
                  )
                """
            )
        )
        print(f"✅ Updated {update_tasks.rowcount or 0} task rows to pending")

        # Add a changelog entry for visibility (only if not already present)
        insert_changelog = conn.execute(
            text(
                """
                INSERT INTO changelog (task_id, old_status, new_status, changed_by, notes, changed_at)
                SELECT t.id, 'created', 'pending', 'system_migration',
                       'Backfilled to pending (task readiness gate)', CURRENT_TIMESTAMP
                FROM task t
                WHERE t.status = 'pending'
                  AND NOT EXISTS (
                    SELECT 1
                    FROM changelog c
                    WHERE c.task_id = t.id
                      AND c.old_status = 'created'
                      AND c.new_status = 'pending'
                      AND c.changed_by = 'system_migration'
                  )
                """
            )
        )
        print(f"✅ Inserted {insert_changelog.rowcount or 0} changelog rows")

        conn.commit()
        print("✅ Backfill completed.")


if __name__ == "__main__":
    migrate()

