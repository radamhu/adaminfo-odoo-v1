# Migration Log: adaminfo-prod-1139 → new Oracle Cloud server

Task 3 (pre-migration prep) executed 2026-09-06.

## Preflight

Command:

```bash
python -m migration.preflight adaminfo-prod-1139 1bf4ace1-9eea-4da9-a6b0-8497f6877c9a
```

Output:

```
Target server OK: instance-20260822-0943 (1bf4ace1-9eea-4da9-a6b0-8497f6877c9a, custom/custom)
Environment: adaminfo-prod-1139 (cca3f63b-f16d-4b42-85f0-fb11827aa263) on server 3ddc7289-f81f-432a-be31-5a0f0d19b386, url https://adaminfo-prod-1139.apps.oec.sh
Latest completed backup: b85da376-aad5-44d0-8890-0e22f4a9a8e7, completed_at=2026-09-06T12:08:34.585687Z, total_size=5410984 bytes, is_verified=False
```

- Target server: `instance-20260822-0943` (`1bf4ace1-9eea-4da9-a6b0-8497f6877c9a`) — OK
- Environment: `adaminfo-prod-1139` (`cca3f63b-f16d-4b42-85f0-fb11827aa263`), currently on server `3ddc7289-f81f-432a-be31-5a0f0d19b386`, url `https://adaminfo-prod-1139.apps.oec.sh`
- Latest completed backup: id `b85da376-aad5-44d0-8890-0e22f4a9a8e7`, completed_at `2026-09-06T12:08:34.585687Z` (today), total_size `5410984` bytes (~5.2 MB), `is_verified=False`

No re-run needed — the backup was already fresh (completed today), so the fallback "create a fresh backup via oec.sh dashboard" step in the brief was not required.

## Baseline capture (old environment)

Logged into `https://adaminfo-prod-1139.apps.oec.sh` as `admin` (credentials from `.env.prod`) via Playwright and captured:

- Installed modules: 71 modules with `state = installed`, listed with technical name + `installed_version` in `docs/superpowers/specs/migration-baseline/baseline.md`. Screenshot: `docs/superpowers/specs/migration-baseline/apps-installed-old.png` (Apps page, Installed filter, Apps-category filter removed to show the full technical module list, full-page).
- Scheduled Actions: 26 cron jobs, all under Settings → Technical → Automation → Scheduled Actions (dev mode enabled via `?debug=1`), listed with name + active state in `docs/superpowers/specs/migration-baseline/baseline.md`. Screenshot: `docs/superpowers/specs/migration-baseline/scheduled-actions-old.png` (full-page).

This is the pre-migration "before" snapshot. Task 5 (post-restore) will re-capture the same two lists on the new server and diff against `baseline.md`.

## Restore

Task 4 (restore to new server) executed 2026-09-06.

**Restore via oec.sh dashboard:**
- Backup used: `b85da376-aad5-44d0-8890-0e22f4a9a8e7` (from Preflight, completed 2026-09-06 12:08:34 UTC)
- Target server: `instance-20260822-0943` (1bf4ace1-9eea-4da9-a6b0-8497f6877c9a)
- Restore completion time: reported by human at 2026-09-06, approximately 15:00 UTC (environment created_at 2026-09-06T14:52:28.623803Z, updated_at 2026-09-06T15:00:13.888306Z)

**New environment details (resolved via API):**
- Name: `adaminfo-prod-1139`
- ID: `c0672b12-b1b6-43c9-8414-7917246d0136`
- Server ID: `1bf4ace1-9eea-4da9-a6b0-8497f6877c9a`
- URL: `https://adaminfo-prod-1139-1.apps.oec.sh`
- Status: `running`
