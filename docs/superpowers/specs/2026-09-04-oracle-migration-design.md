# adaminfo-prod-1139 → Oracle Cloud Server Migration — Design

**Date:** 2026-09-04
**Status:** Approved for planning
**Environment:** `adaminfo-prod-1139` (oec.sh, DB id `cca3f63b-f16d-4b42-85f0-fb11827aa263`)
**Target server:** Oracle Cloud instance, oec.sh dashboard id `1bf4ace1-9eea-4da9-a6b0-8497f6877c9a` (`158.180.55.49`, user `ubuntu`)
**Current URL:** https://adaminfo-prod-1139.apps.oec.sh/ (oec.sh subdomain only, no custom DNS)

## Context

oec.sh is migrating its underlying prod server infrastructure to Oracle Cloud instances.
`adaminfo-prod-1139` is one of the environments that needs to move. oec.sh support gave the
exact platform mechanism for this: restore a backup to a different server, which creates a full
working copy of the environment there. This is the first environment migrated under this
mechanism — the same runbook is expected to apply to other oec.sh projects/environments later.

## Approach

**Primary: oec.sh native "restore to different server."** Use the platform's built-in
backup/restore feature rather than manual `pg_dump`/`rsync`. The platform already owns DB,
filestore, and config copy for this operation; duplicating that manually adds risk and effort
for no benefit when the native path exists and preserves the environment URL automatically.

**Fallback only, not used unless primary fails:** manual migration per oec.sh's public
[Odoo migration guide](https://oec.sh/guides/odoo-migration) — `pg_dump -Fc` + `rsync` for DB
and filestore, SSH into old and new instances directly, `pg_restore --no-owner`, chown
filestore, adjust `odoo.conf` if the DB port differs. Only invoke this if the native restore
errors out or doesn't support this server pair.

Downtime is not a hard constraint (confirmed: flexible, no maintenance window required) — old
env keeps serving traffic on its current URL throughout, so there's no forced cutover moment
until the old env is stopped/deleted at the end.

## Steps

### 1. Pre-migration prep
- Confirm target server in oec.sh dashboard matches `1bf4ace1-9eea-4da9-a6b0-8497f6877c9a`.
- Create a fresh backup of `adaminfo-prod-1139` via its Backup Management tab (don't reuse a
  stale one).
- Record baseline state to diff against post-migration:
  - Odoo version, installed module list (standard + custom `adaminfo-odoo-v1` addons +
    any OCA/third-party)
  - DB size, filestore size
  - Active cron/scheduled actions
  - Any external integrations/webhooks/API keys pointing at this env's URL or DB id
- Known platform risk to watch for: oec.sh's Odoo 18 deploy pipeline has a dependency-check
  stage that can fail with `ModuleNotFoundError: No module named 'OpenSSL'` (logged as
  `GEN_EMAIL/skew`) because it pins `cryptography` for Odoo 18 compat but doesn't itself
  install `pyOpenSSL`. Seen on an unrelated oec.sh Odoo 18 project; root cause is platform-side
  (base image + repo dep-scan), so it can resurface here. If hit: add/confirm a root
  `requirements.txt` pinning `pyOpenSSL>=24.0.0`, commit, push, redeploy.

### 2. Execute restore
- On `adaminfo-prod-1139` (old server) → Backup Management tab → select the fresh backup →
  Restore → target **"Different Server"** → select the new Oracle server → name the new
  environment → confirm.
- Leave the old environment running untouched on the old server — it's the rollback point.
  Do not stop or delete it yet.

### 3. Post-restore verification (before any cutover decision)
- New env reaches healthy state: container running, HTTP OK (dashboard status, or
  `GET /environments/{id}/status` if the API is reachable).
- Login works: admin account + at least one regular user.
- Installed module list matches the pre-migration inventory.
- Core app workflows exercise cleanly (confirm which flows are critical for this project before
  running this step — not yet enumerated in this spec).
- PDF report generation renders correctly.
- Outbound email sending works.
- Cron/scheduled actions are present and enabled.
- Filestore attachments: spot-check a handful of existing documents/images load correctly.
- Watch logs for 24–48h after verification passes, before proceeding to decommission.

### 4. Cutover check
- oec.sh is expected to preserve the environment's URL/slug automatically on restore, so no DNS
  or user-facing URL change is expected (confirmed: subdomain-only, no custom DNS in play).
- However, *how* the URL carries over (immediately after restore, vs. only once the old env is
  stopped) is not confirmed from documentation — treat this as a **live check during
  execution**: after restore completes, verify in the dashboard whether the new env already
  answers on `adaminfo-prod-1139`'s URL, or whether the old env must be stopped first for the
  new one to take over the slug. Adjust step order on the day if needed.

### 5. Rollback
- Old environment stays running (or stopped-but-not-deleted) on the old server for a hold
  period — suggest 3–7 days — as the rollback path. If a problem surfaces on the new env,
  revert by continuing to use / restarting the old one and investigate the new env separately.

### 6. Decommission
- After the hold period, with clean logs and verification complete, stop/delete the old
  environment on the old server. This step is manual — oec.sh does not do it automatically as
  part of the restore.

## Open items to confirm before/at execution time
- Which app workflows count as "critical" for verification in step 3 (not yet enumerated —
  ask before running the checklist, or fill in once known).
- Exact behavior of URL takeover timing (step 4) — confirm live in the oec.sh dashboard during
  the restore, not assumed in advance.

## Reuse

This is expected to be the first of several oec.sh environment migrations to Oracle Cloud
servers. Once this runbook is executed once successfully, it should generalize directly to
other oec.sh projects/environments (e.g. `dentari-prod-2031`, `dentari-dev-8780`) with only the
environment names/ids swapped.
