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

## Playwright automation scope

Two different surfaces are involved, and only one is automatable today:

- **oec.sh platform dashboard** (`platform.oec.sh` — backup creation, restore-to-different-server,
  stop/delete environment): **stays manual.** No oec.sh platform account credentials exist in
  either repo's `.env` files (only Odoo app login + SSH + Oracle host creds are stored). If this
  runbook is going to be re-run for other environments (`dentari-prod-2031`,
  `dentari-dev-8780`, ...), it's worth adding oec.sh platform credentials to enable
  Playwright-driving steps 1–2 and 6 as well — flagged as an open item below, not assumed here.
- **Odoo application itself** (both old and new env, same `/web/login` flow, same UI): fully
  reachable with Playwright using the credentials already in `.env.prod`
  (`ODOO_LOGIN_USERNAME`, `ODOO_LOGIN_PASSWORD`, `ODOO_ERP_URL`, `ODOO_DB`). All baseline capture
  and post-restore verification below is written as Playwright steps against this surface.

Convention: append `?debug=1` to Odoo URLs to reach Settings → Technical menus (Scheduled
Actions, etc.), consistent with how the `odoo-oecsh-ticket-deploy` skill already drives Odoo
dev-mode for this account.

## Steps

### 1. Pre-migration prep (Playwright-automated baseline capture)
- Confirm target server in oec.sh dashboard matches `1bf4ace1-9eea-4da9-a6b0-8497f6877c9a`.
  *(manual — dashboard, no creds to automate)*
- Create a fresh backup of `adaminfo-prod-1139` via its Backup Management tab (don't reuse a
  stale one). *(manual — dashboard)*
- Record baseline state via Playwright against the **old** env, to diff against post-migration:
  - Log in at `{ODOO_ERP_URL}/web/login` with `ODOO_LOGIN_USERNAME` / `ODOO_LOGIN_PASSWORD`.
  - Navigate to Apps (`/odoo/apps`), filter "Installed", snapshot the list → module name +
    version baseline.
  - Navigate to Settings → Technical → Scheduled Actions (`?debug=1` required) → snapshot
    active/inactive cron jobs.
  - Navigate to Settings → General Settings → note the Odoo version shown in the page footer/
    about dialog.
  - Screenshot each of the above and save under
    `docs/superpowers/specs/migration-baseline/` for later diffing.
  - Note DB size / filestore size from the oec.sh dashboard (not exposed in-app; manual read).
- Known platform risk to watch for: oec.sh's Odoo 18 deploy pipeline has a dependency-check
  stage that can fail with `ModuleNotFoundError: No module named 'OpenSSL'` (logged as
  `GEN_EMAIL/skew`) because it pins `cryptography` for Odoo 18 compat but doesn't itself
  install `pyOpenSSL`. Seen on an unrelated oec.sh Odoo 18 project; root cause is platform-side
  (base image + repo dep-scan), so it can resurface here. If hit: add/confirm a root
  `requirements.txt` pinning `pyOpenSSL>=24.0.0`, commit, push, redeploy.

### 2. Execute restore *(manual)*
- On `adaminfo-prod-1139` (old server) → Backup Management tab → select the fresh backup →
  Restore → target **"Different Server"** → select the new Oracle server → name the new
  environment → confirm.
- Leave the old environment running untouched on the old server — it's the rollback point.
  Do not stop or delete it yet.

### 3. Post-restore verification (Playwright-automated)
Against the new env's URL (expected to be the same `adaminfo-prod-1139.apps.oec.sh`, confirmed
per step 4 below — update `ODOO_DB`/URL locally first if the restore assigns a new DB id):

- Reachability: `browser_navigate` to the env URL, confirm login page loads (container
  running / HTTP OK) — no manual dashboard status check needed.
- Login: same `/web/login` flow with `ODOO_LOGIN_USERNAME` / `ODOO_LOGIN_PASSWORD` — confirms
  admin auth survived the restore. Log in separately as a non-admin user if one exists, to
  confirm regular-user auth too.
- Module list diff: repeat the Apps → Installed snapshot from step 1, diff against baseline —
  flag any module that disappeared or changed version.
- Scheduled Actions: repeat the Technical → Scheduled Actions snapshot, diff against baseline —
  confirm same jobs present and still enabled (a restore can sometimes land cron jobs
  paused — check explicitly, don't assume).
- Core workflows: **not yet enumerated** — which flows count as "critical" for this project
  isn't defined yet (see open items). Once known, script them as Playwright flows the same way
  (navigate → fill form → submit → snapshot result).
- PDF report: open an existing record with a print action, trigger it, use
  `browser_network_request`/`browser_network_requests` to confirm the report response is
  `200` with `content-type: application/pdf` (or a downloaded file appears) rather than an
  error page.
- Attachments: open a record with a known existing attachment/image, confirm it renders
  (screenshot — a broken image renders as a broken-image icon, easy to catch visually) rather
  than a 404.
- Email: Playwright can trigger a send (e.g. "Send Message" on a record, or a test email from
  Technical → Email → Outgoing Mail Servers → Test Connection) and confirm no error banner
  appears in the UI — but **cannot verify actual delivery**, since that happens outside the
  browser. Note this as a coverage gap; if delivery must be confirmed, that's a manual inbox
  check, not a Playwright step.
- Take a screenshot at each checkpoint, saved alongside the baseline screenshots for a
  before/after record.
- Watch logs for 24–48h after this checklist passes, before proceeding to decommission.
  *(manual — dashboard log view, no API/creds available to automate)*

### 4. Cutover check
- oec.sh is expected to preserve the environment's URL/slug automatically on restore, so no DNS
  or user-facing URL change is expected (confirmed: subdomain-only, no custom DNS in play).
- However, *how* the URL carries over (immediately after restore, vs. only once the old env is
  stopped) is not confirmed from documentation — treat this as a **live check during
  execution**: after restore completes, use Playwright to `browser_navigate` directly to
  `https://adaminfo-prod-1139.apps.oec.sh/web/login` and confirm whether it's already answering
  from the new server (e.g. via the module-list/version diff from step 3), or whether the old
  env must be stopped first for the new one to take over the slug. Adjust step order on the day
  if needed.

### 5. Rollback
- Old environment stays running (or stopped-but-not-deleted) on the old server for a hold
  period — suggest 3–7 days — as the rollback path. If a problem surfaces on the new env,
  revert by continuing to use / restarting the old one and investigate the new env separately.

### 6. Decommission *(manual)*
- After the hold period, with clean logs and verification complete, stop/delete the old
  environment on the old server. This step is manual — oec.sh does not do it automatically as
  part of the restore, and there are no platform credentials to automate it via Playwright
  (see open items).

## Open items to confirm before/at execution time
- Which app workflows count as "critical" for verification in step 3 (not yet enumerated —
  ask before running the checklist, or fill in once known).
- Exact behavior of URL takeover timing (step 4) — confirm live in the oec.sh dashboard during
  the restore, not assumed in advance.
- Whether to add oec.sh platform-dashboard credentials to `.env` so steps 1–2 and 6 (backup
  creation, restore trigger, decommission) can also be Playwright-driven, not just verification.
  Not done in this spec since no such credentials currently exist in either repo.

## Reuse

This is expected to be the first of several oec.sh environment migrations to Oracle Cloud
servers. Once this runbook is executed once successfully, it should generalize directly to
other oec.sh projects/environments (e.g. `dentari-prod-2031`, `dentari-dev-8780`) with only the
environment names/ids swapped — the Playwright verification steps in particular should port
directly since they only depend on the standard Odoo login/UI flow.
