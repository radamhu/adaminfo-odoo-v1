# adaminfo-prod-1139 → Oracle Cloud Server Migration — Design

**Date:** 2026-09-04
**Status:** Approved for planning
**Environment:** `adaminfo-prod-1139` (oec.sh, env_id `cca3f63b-f16d-4b42-85f0-fb11827aa263`)
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

## Automation scope

Two different tools apply to two different surfaces — use whichever actually fits, not
Playwright for everything:

**oec.sh platform (`api.oec.sh/api/public/v1`, `Authorization: Bearer $ODOO_PUBLIC_API_KEY`)** —
`ODOO_PUBLIC_API_KEY` in `.env.prod`/`.env.dev` is an oec.sh account API key (same key works
across projects/environments on this account, per the `odoo-oecsh-ticket-deploy` skill), so
most platform-level steps are scriptable via `curl`, not browser automation. Confirmed against
the live `openapi.json`:

| Capability | Endpoint | Available? |
|---|---|---|
| List servers | `GET /servers` | ✅ |
| List/check backups | `GET /environments/{id}/backups` | ✅ |
| Get backup download URLs | `GET /backups/{id}/download` | ✅ |
| Environment detail (server_id, url, custom_domain, odoo_version, last_commit) | `GET /projects/{project_id}/environments` | ✅ |
| Health status | `GET /environments/{id}/status` | ✅ (`container_running`, `db_ready`, `http_ok`) |
| Logs | `GET /environments/{id}/logs` | ✅ |
| Stop / start / restart | `POST /environments/{id}/{stop,start,restart}` | ✅ |
| Delete (enqueue destruction) | `DELETE /environments/{id}` | ✅ |
| **Create a backup** | — | ❌ not exposed |
| **Restore to a different server** | — | ❌ not exposed |

So exactly two sub-steps stay dashboard-only because the platform simply doesn't expose them
via API: creating the pre-migration backup, and triggering the restore-to-different-server
itself. Every other platform action below (server confirmation, backup verification, health
checks, log watching, stop/delete) uses the API — faster and more reliable than clicking
through the dashboard, and scriptable for reuse on later environments.

Always resolve `project_id`/`env_id` fresh via `GET /projects` → `GET /projects/{id}/environments`
rather than hardcoding — per the same skill's convention.

**Odoo application itself** (`ODOO_ERP_URL`, `ODOO_LOGIN_USERNAME`/`PASSWORD`, `?debug=1` for
Technical menus) — this is where Playwright earns its place: anything the API can't see inside
the running app (module list correctness, cron enabled/disabled, PDF rendering, attachment
rendering, UI-level email trigger, actual workflow screens). All post-restore *application*
verification below is written as Playwright steps against this surface.

## Steps

### 1. Pre-migration prep
- Confirm target server via API: `GET /servers`, match id `1bf4ace1-9eea-4da9-a6b0-8497f6877c9a`
  (name/provider/region sanity check against Oracle Cloud + `eu-frankfurt-1`).
- Create a fresh backup of `adaminfo-prod-1139` via its Backup Management tab. *(manual —
  no create-backup endpoint exists)*
- Verify it via API: `GET /environments/{env_id}/backups?status=completed`, confirm the newest
  entry is recent and `total_size` is in the right ballpark (sanity check, not exact) before
  relying on it.
- Record baseline via Playwright against the **old** env:
  - Log in at `{ODOO_ERP_URL}/web/login`.
  - Apps (`/odoo/apps`) → filter "Installed" → snapshot module name + version list.
  - Settings → Technical → Scheduled Actions (`?debug=1`) → snapshot active/inactive cron jobs.
  - Screenshot each, saved under `docs/superpowers/specs/migration-baseline/`.
- Cross-check baseline against API environment detail (`GET /projects/{project_id}/environments`,
  filter to this env_id) for `odoo_version`, `branch`, `last_commit`, `server_id`, `url` — more
  authoritative than reading the UI footer.
- Known platform risk to watch for: oec.sh's Odoo 18 deploy pipeline has a dependency-check
  stage that can fail with `ModuleNotFoundError: No module named 'OpenSSL'` (logged as
  `GEN_EMAIL/skew`) because it pins `cryptography` for Odoo 18 compat but doesn't itself
  install `pyOpenSSL`. Seen on an unrelated oec.sh Odoo 18 project; root cause is platform-side,
  so it can resurface here. If hit: add/confirm a root `requirements.txt` pinning
  `pyOpenSSL>=24.0.0`, commit, push, redeploy.

### 2. Execute restore *(manual — no API for this)*
- On `adaminfo-prod-1139` (old server) → Backup Management tab → select the fresh backup →
  Restore → target **"Different Server"** → select the new Oracle server → name the new
  environment → confirm.
- Leave the old environment running untouched on the old server — it's the rollback point.
  Do not stop or delete it yet.

### 3. Post-restore verification
- **Health (API, fast/first check):** `GET /environments/{new_env_id}/status` — confirm
  `container_running`, `db_ready`, `http_ok` all true before doing anything UI-level.
- **Auth works end-to-end (Playwright):** log in at the new env's `/web/login` as admin, then
  as a non-admin user if one exists — proves the login path actually works, not just that the
  container is up.
- **Module list diff (Playwright):** repeat the Apps → Installed snapshot from step 1, diff
  against baseline — flag any module that disappeared or changed version.
- **Scheduled Actions diff (Playwright):** repeat the Technical → Scheduled Actions snapshot,
  diff against baseline — a restore can land cron jobs paused; check explicitly, don't assume.
- **Core workflows (Playwright):** **not yet enumerated** — which flows count as "critical"
  for this project isn't defined yet (see open items). Script them the same way once known.
- **PDF report (Playwright):** open an existing record with a print action, trigger it, use
  `browser_network_request`/`browser_network_requests` to confirm `200` +
  `content-type: application/pdf` rather than an error page.
- **Attachments (Playwright):** open a record with a known existing attachment/image, confirm
  it renders (a broken image shows a broken-image icon — easy to catch on screenshot).
- **Email (Playwright, partial):** trigger a send from the UI (e.g. "Send Message", or Technical
  → Email → Outgoing Mail Servers → Test Connection) and confirm no error banner. **Cannot
  verify actual delivery** — that happens outside the browser; if delivery must be confirmed,
  that's a manual inbox check, not a Playwright step.
- Screenshot at each Playwright checkpoint, saved alongside the baseline screenshots.
- **Log watch (API, 24–48h):** poll `GET /environments/{new_env_id}/logs` periodically over the
  hold window, grep for `ERROR`/`CRITICAL`, instead of manually watching the dashboard.

### 4. Cutover check (API — resolved, not a live guess)
- Query environment detail for **both** env_ids via `GET /projects/{project_id}/environments`:
  - Old env (`cca3f63b-f16d-4b42-85f0-fb11827aa263`): confirm `server_id` moved off the old
    server (or the env was stopped, once decommissioned).
  - New env: confirm `server_id` equals the new Oracle server, and `url` is
    `adaminfo-prod-1139.apps.oec.sh` (or wherever it landed) — this single check settles
    whether the URL already carried over or the old env needs stopping first, no need to guess
    live.

### 5. Rollback
- Old environment stays running (or `POST /environments/{old_env_id}/stop`, API — no need for
  dashboard) for a hold period — suggest 3–7 days. If a problem surfaces on the new env, revert
  by continuing to use / `POST .../start` on the old one and investigate the new env separately.

### 6. Decommission (API)
- After the hold period, with clean logs and verification complete:
  `POST /environments/{old_env_id}/stop`, then once fully confident,
  `DELETE /environments/{old_env_id}` (enqueues destruction). No dashboard clicking required.

## Open items to confirm before/at execution time
- Which app workflows count as "critical" for verification in step 3 — not yet enumerated; ask
  before running the checklist, or fill in once known. (Only remaining open item — the URL/
  server-takeover ambiguity from the previous draft is resolved via the step 4 API check.)

## Reuse

This is expected to be the first of several oec.sh environment migrations to Oracle Cloud
servers. Once executed once successfully, this runbook should generalize directly to other
oec.sh projects/environments (e.g. `dentari-prod-2031`, `dentari-dev-8780`) with only the
project/env ids swapped — both the API calls and the Playwright verification steps are written
generically enough to port directly.
