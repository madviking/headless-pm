# Changelog

All notable changes to this project are documented in this file.

This changelog follows a simple, human-curated format grouped by date and change type. Prefer clear, user-facing summaries over raw commit messages. Mark breaking changes explicitly.

## 2026-02-04

- Changed
  - Dashboard Task Management board now uses full-width layout on large displays to show more Kanban columns at once.
  - Reduced minimum Kanban column width so the full board fits more comfortably on wide screens.
- Fixed
  - Dashboard `/agents` page no longer errors due to type-only imports being treated as runtime imports.

## 2026-02-01

- Added
  - New task status `pending` to allow PMs to control when tasks become eligible for pickup (`pending → created`).
  - Migration script for MySQL installs that enforce ENUM values on task/changelog statuses: `migrations/add_pending_status.py`.
  - Backfill script to move existing unstarted tasks from `created` to `pending`: `migrations/backfill_created_to_pending.py`.
  - Python client now supports `tasks list` (with status/role filters) to view backlog tasks, including `pending`: `agents/client/headless_pm_client.py`.
- Documentation
  - Updated PM agent instructions to reflect the `pending → created` promotion step.
- Fixed
  - Fixed MySQL `changelog.old_status/new_status` inserts failing with “Data truncated” by persisting `TaskStatus` values (e.g. `pending`) instead of enum names (e.g. `PENDING`).
  - API now returns an actionable error if MySQL ENUM columns reject `pending` (points to `migrations/add_pending_status.py`).
  - Fixed `migrations/add_pending_status.py` MySQL ENUM parsing and added case-aware support for uppercase legacy schemas (adds `PENDING` where required).
  - Dashboard now surfaces API error `detail` messages for task status updates (helps diagnose 404s like missing task/agent).
  - Dashboard prevents task moves when the selected agent ID is stale/unregistered (clears localStorage and prompts to select a valid agent).
  - Dashboard Task Management epic filter now lists epics from the API instead of hardcoded placeholders.
  - Dashboard Task Management epic filter now filters tasks by the selected epic.
  - Dashboard now sends a default dev API key when `NEXT_PUBLIC_API_KEY` is unset (development only), preventing “empty dashboard” when the API auth middleware is enabled.
  - Playwright regression test covering the Task Management epic filter options.

## 2025-10-17

- Added
  - start.sh `--kill`/`-k` flag: interactively frees busy ports (6969 API, 6968 MCP, 3001 Dashboard) with confirmation before terminating listed processes.
- Changed
  - Startup supervisor made robust: removed fragile log pipes so real child PIDs are tracked; added `trap ... EXIT` for reliable cleanup; resilient `wait` so one child exiting doesn’t kill the others; skips starting a service if its port is busy and `--kill` isn’t used.
- Fixed
  - Resolved premature shutdown where services exited after launch due to parent script exiting and SIGHUP propagation; accurate PID tracking prevents orphaned pipes and early termination.
- Documentation
  - README updated with `./start.sh` usage (`--kill`), port-conflict guidance, dashboard notes, and troubleshooting steps for EADDRINUSE and Node 18+ requirements.

## 2025-10-16

- Added
  - UV packaging integrated and coordinated with MCP SDK v1.15.0 to ensure compatibility and reliable development flows (6241c14).
- Changed
  - Improved test reliability to consistently reach 100% on the current suite (6241c14).
  - Updated project `uv` configuration/format where applicable (5229536).
- Fixed
  - macOS ARM64 packaging: resolved `pydantic-core` mismatch and stabilized async tests (5229536).

## 2025-07-30

- Documentation
  - Added example dashboard environment file to simplify local setup (913c62a).

## 2025-06-28

- Fixed
  - Added missing dashboard `lib` directory from `new-runners` branch (e53ef6b).

## 2025-06-25

- Added
  - New services to run refactored routes; tests updated to simulate delay/wait behavior (0bae0b0).
- Changed
  - API now handles “waiting when no tasks exist”; clients can request the next task and wait longer as needed (0bae0b0, 66b0dbb).
  - Team roles restructured into subfolders; improve continuation prompts; clarify API authentication; expand docs and agent descriptions (66b0dbb, 6621ff4).
  - Setup improved for multiple architectures; increased test coverage (f87357d).
  - Improved task timeline visuals/behavior (318d327).
- Fixed
  - Edge cases where the next task was not assigned; better handling of stale locks (d7b1ab9).
  - Analytics page issues in the dashboard (d45ea5f).
  - General dashboard fixes (dd73b8e).
- Breaking Changes
  - Team roles moved into subfolders; update any hardcoded paths and initial prompts that reference them (66b0dbb).
  - Polling strategy changed: API performs the waiting; adjust clients and automation to call the next-task endpoint and allow long waits (66b0dbb).

## 2025-06-24–23

- Changed
  - Dashboard polling improvements and README screenshot updates (45ec56e).
- Documentation
  - Dashboard README updates, including the ability to disable services by leaving ports unset (ae9879b).

## 2025-06-19–18

- Added
  - Next.js Web Dashboard foundation and subsequent updates, including Epics (0d0c5e0, d3d15d8, b9c0016).
  - Python CLI helper `headless_pm_client.py` with comprehensive commands and `--help` (70fcd6c).
  - MCP server for natural-language commanding and a Claude Code installation script (70fcd6c).
- Changed
  - Simplified workflow: no longer routes through PM; agent registration now returns all mentions and the next task (cd6c425).
  - Improved continuous operation and service health checks; additional dashboard columns and test scripts (db4fa97, b4f9dbb).
  - Better status handling and improved initial/continuation prompts (bc63a38, 6621ff4).
- Removed
  - Deprecated/evaluate endpoint removed to reduce confusion (3223e2c, cd6c425).
- Fixed
  - MySQL column type generation issue corrected (1639f0f).
- Breaking Changes
  - One-time database reset required: older installations needed to drop tables prior to this sequence of changes (70fcd6c).
  - Evaluate endpoint removed; update any clients/scripts depending on it (3223e2c, cd6c425).

## 2025-06-16

- Initial Release
  - First public version of Headless PM enabling document-based coordination between LLM agents working on the same codebase (b8a8052).

---

Maintenance guidelines

- Categorize entries under: Added, Changed, Fixed, Removed, Deprecated, Security, Documentation, and Breaking Changes (when applicable).
- Prefer grouped, user-facing summaries rather than duplicating raw commit messages.
- When a change is potentially breaking, mark it under “Breaking Changes” with migration/upgrade notes.
- Keep sections grouped by date until version tags are introduced. If tags are added later, switch to version-based headings (e.g., v0.5.0 – YYYY-MM-DD).
- Update this file in the same pull request/commit that introduces the change.
