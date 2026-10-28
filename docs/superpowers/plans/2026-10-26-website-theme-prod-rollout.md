# Website Theme Prod Rollout Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Install `website` + `website_adaminfo_theme` on prod (`adaminfo-prod-1240`, branch `main`) so it serves the same homepage as `adaminfo-dev-1869`, with a working contact form.

**Architecture:** Fast-forward `main` to `development`, take an oec.sh backup, deploy prod, install the theme module over XML-RPC (pulls `website` as a dependency; the module's `post_init_hook` applies site defaults), fix the contact-form recipient in the Website Builder, then verify with a repeatable check script and a browser pass. Rollback is restoring the backup.

**Tech Stack:** Odoo 18.0 (oec.sh), XML-RPC via `seed.connection.OdooClient`, oec.sh MCP tools (`oecsh_create_backup`, `oecsh_deploy_environment`, `oecsh_wait_for_task`, `oecsh_get_runtime_logs`), pytest.

**Spec:** [docs/superpowers/specs/2026-10-05-adaminfo-website-design.md](../specs/2026-10-05-adaminfo-website-design.md), plus the 2026-10-26 theme changes (commits `b549d65`, `60f4713`).

## Global Constraints

- Prod environment: `adaminfo-prod-1240`, env id `8a0b0649-d366-4311-a3a3-b38b71880d49`, branch `main`, URL `https://adaminfo-prod-1240.apps.oec.sh`.
- Prod database: `adams-organization_adaminfo_adaminfo-prod-1240` (not the env UUID in `.env.prod`; `_detect_db`'s hostname fallback is wrong too).
- Dev reference: `adaminfo-dev-1869`, env id `11e4aa83-45a8-492f-a0c9-b88aa1347ca2`, database `adams-organization_adaminfo_adaminfo-dev-1869`.
- Theme module version after install: `18.0.1.1.0`. Website name `Adam Informatika`, LinkedIn `https://www.linkedin.com/in/adaminformatika`.
- Contact-form recipient: `roland@adaminformatika.hu` (prod `res.company` email).
- No custom domain / DNS cutover in this plan (`custom_domain` is null on prod; separate work).
- Every prod-mutating step (push to `main`, deploy, install, Builder save) needs the user's explicit go at execution time.

## Review Focus

- **Contact form sends to nobody.** Homepage form ships `email_to` empty, so Odoo skips the signature check and creates a `mail.mail` with no recipient. Expected: a submission reaches `roland@adaminformatika.hu`. Task 4 sets the recipient in the Builder (it computes the signature with prod's own secret; the dev hash in `sections.xml` is useless on prod); Task 1's check asserts the stored form has a non-empty `email_to`.
- **Auto-installed side modules.** Installing `website` on prod also auto-installs what dev got: `website_crm`, `website_crm_sms`, `website_mail`, `website_payment`, `website_project`, `website_sms`, `social_media`, `google_recaptcha`. Expected: no change to existing CRM/sales/invoicing data. Task 3 records the before/after installed set.
- **Website configurator hijacks the first backend login.** Installing `website` registers the configurator todo. Expected: admin lands in the normal backend. Task 3 marks it done.
- **Stale cached assets.** Expected: first public hit renders the navy/gold theme, not Odoo default. Task 3 deletes `assets_%` attachments.
- **Wrong DB name in tooling.** Expected: scripts authenticate against the real prod DB. Task 1's CLI takes `--db` explicitly.

---

### Task 1: Rollout check script

**Files:**
- Create: `seed/verify_website_theme.py`
- Test: `tests/test_verify_website_theme.py`

**Interfaces:**
- Consumes: `seed.connection.OdooClient(url, db, username, password)` with `.search_read(model, domain, fields, limit)`.
- Produces: `check_theme_rollout(client: OdooClient) -> dict[str, bool]` with exactly these keys:
  `theme_installed` (module `website_adaminfo_theme` state `installed` and `installed_version == "18.0.1.1.0"`),
  `website_named` (website id 1 `name == "Adam Informatika"`),
  `linkedin_set` (`social_linkedin == "https://www.linkedin.com/in/adaminformatika"`),
  `footer_minimalist` (an active `ir.ui.view` with key `website.template_footer_minimalist` and `website_id == 1`, searched with `context={'active_test': False}`),
  `footer_override` (active view key `website_adaminfo_theme.footer_minimalist_content` with `website_id == 1`),
  `form_recipient_set` (some `ir.ui.view` whose `arch_db` contains `contactus_form` and `name="email_to"` with a non-empty `value=`; search key `website_adaminfo_theme.section_contact`, website-specific copy preferred).
  CLI: `python -m seed.verify_website_theme --env .env.prod --db <db>` prints one `PASS|FAIL key` line per check, exit code 1 if any FAIL.

- [ ] **Step 1: Write the failing tests** (mock `xmlrpc.client.ServerProxy` like `tests/test_verify_customer_operations_dashboard.py`)

```python
def test_all_checks_pass_on_dev_like_state(): ...
    # mocked rows mirroring dev-1869 as of 2026-10-26 + a contact view whose arch
    # has name="email_to" value="roland@adaminformatika.hu"
    assert check_theme_rollout(client) == dict.fromkeys(KEYS, True)

def test_empty_email_to_fails_form_recipient_check(): ...
    # arch contains name="email_to" with no value attribute
    assert check_theme_rollout(client)["form_recipient_set"] is False

def test_generic_only_minimalist_view_fails(): ...
    # only website_id False row for website.template_footer_minimalist
    assert check_theme_rollout(client)["footer_minimalist"] is False
```

- [ ] **Step 2: Run** `pytest tests/test_verify_website_theme.py -v` — expected FAIL (`ModuleNotFoundError: seed.verify_website_theme`).
- [ ] **Step 3: Implement** `check_theme_rollout` and the `argparse` CLI (`--env`, `--db`) in `seed/verify_website_theme.py`. Use `OdooClient.execute`-style `execute_kw` with `context` for the `active_test=False` search (add an optional `context: dict | None = None` kwarg to `OdooClient.search_read` if needed, passed through in the kwargs dict).
- [ ] **Step 4: Run** `pytest -v` — expected all PASS (existing suite included).
- [ ] **Step 5: Run against dev:** `python -m seed.verify_website_theme --env .env.dev --db adams-organization_adaminfo_adaminfo-dev-1869` — expected PASS for every key except `form_recipient_set` (FAIL until Task 4 on dev).
- [ ] **Step 6: Commit** `feat: add website theme rollout check script` on `development`.

### Task 2: Promote code to `main` and back up prod

**Files:** none (git + oec.sh only).

- [ ] **Step 1:** Confirm fast-forward is possible: `git fetch origin && git merge-base --is-ancestor origin/main origin/development` — expected exit 0 (verified 2026-10-26: `main` is 25 commits behind, no divergence). Record `git rev-parse origin/main` as the rollback sha.
- [ ] **Step 2:** Record prod's installed module set: `search_read('ir.module.module', [('state','=','installed')], ['name'])` → save names to `docs/superpowers/specs/migration-baseline/prod-1240-modules-before-website.txt` (expected 71 modules, `website` absent).
- [ ] **Step 3 (user go required):** `oecsh_create_backup` on env `8a0b0649-d366-4311-a3a3-b38b71880d49`; `oecsh_wait_for_task` until `completed`; note backup id in the commit message of Step 4.
- [ ] **Step 4 (user go required):** `git push origin development:main` (fast-forward only; never `--force`). Commit the baseline file from Step 2 on `development` first and include it in the push.

### Task 3: Deploy and install on prod

**Interfaces:** Consumes Task 1's CLI for verification.

- [ ] **Step 1 (user go required):** `oecsh_deploy_environment` on prod env id with no `update_modules`; `oecsh_wait_for_task` (≈4 min on dev) — expected `completed`, `health.http_ok == true`.
- [ ] **Step 2:** Over XML-RPC as admin on the prod DB: `ir.module.module.update_list()`, then search `name = 'website_adaminfo_theme'` — expected state `uninstalled` (module now visible).
- [ ] **Step 3 (user go required):** `execute('ir.module.module', 'button_immediate_install', [theme_id])`. Expected: returns without Fault; `website` and the Review Focus side modules now `installed`. The module's `post_init_hook` (`hooks.apply_site_defaults`) runs on this fresh install — the `18.0.1.1.0` migration does not.
- [ ] **Step 4:** Read Odoo log via `oecsh_get_runtime_logs` (≤ 6 calls/min; filter with `jq -r .log | grep -iE "ERROR|CRITICAL|Traceback|adaminfo_theme"`). Expected: no `ERROR`/`Traceback` apart from the known `GeoLite2-City.mmdb` noise.
- [ ] **Step 5:** Mark the configurator done: `search_read('ir.actions.todo', [('state','=','open')], ['name','action_id'])`; write `state='done'` on the website configurator todo only.
- [ ] **Step 6:** Delete cached assets: `ir.attachment` search `[('name','=like','%assets_%'), ('res_model','=','ir.ui.view')]` → `unlink`.
- [ ] **Step 7:** Diff installed modules against Task 2 Step 2's file; append the "after" list to the same file. Expected additions = exactly the Review Focus list plus `website`, `website_adaminfo_theme`. Anything else: stop and ask the user.
- [ ] **Step 8:** `python -m seed.verify_website_theme --env .env.prod --db adams-organization_adaminfo_adaminfo-prod-1240` — expected PASS for all keys except `form_recipient_set`.

### Task 4: Contact form recipient (dev, then prod)

**Files:** none in git — the Builder writes a website-specific copy of `website_adaminfo_theme.section_contact`, which is the point (signature hashed with each DB's own secret).

- [ ] **Step 1 (dev):** Log in at `https://adaminfo-dev-1869.apps.oec.sh/odoo/website`, Edit → click the contact form → Form options: Action `Send an E-mail`, Recipient Email `roland@adaminformatika.hu` → Save.
- [ ] **Step 2 (dev):** Submit the public form once (subject `rollout test dev`). Expected: `mail.mail` row with `email_to = roland@adaminformatika.hu`, `state` in `sent`/`outgoing`, browser redirected to `/contactus-thank-you`. Then Task 1 CLI on dev — all PASS.
- [ ] **Step 3 (prod, user go required):** Repeat Step 1 on `https://adaminfo-prod-1240.apps.oec.sh/odoo/website`.
- [ ] **Step 4 (prod):** Repeat Step 2 with subject `rollout test prod`; confirm the email actually arrives (prod outgoing mail server). Delete the test `mail.mail`/message afterwards. Task 1 CLI on prod — all PASS.

### Task 5: Visual verification and docs

**Files:**
- Modify: `README.md` (Theme deployment section: status line, prod DB name, install-vs-upgrade note)

- [ ] **Step 1:** Browser pass on `https://adaminfo-prod-1240.apps.oec.sh/` at 1440px and 390px: hero banner, alternating sections, two project cards linking to `https://www.linkedin.com/in/adaminformatika/details/projects/`, Minimalist footer with LinkedIn + globe icons, `Copyright © ADAM Roland E.V.`, tab title `Home | Adam Informatika`. Expected: matches dev screenshots of 2026-10-26; no console errors; no horizontal scroll.
- [ ] **Step 2:** Update README "Status" line: prod live on `adaminfo-prod-1240` (date), remaining = DNS cutover; document that first prod install uses `button_immediate_install` (hook), upgrades use the deploy `update_modules` path (migrations); record prod DB name. Remove the stale `adaminfo-prod-1139` reference there.
- [ ] **Step 3:** Commit on `development`, push, fast-forward `main` again (`git push origin development:main`, user go).

## Rollback

Any failure in Task 3 Steps 3–7 or Task 4 Step 4 that can't be fixed forward in minutes: restore the Task 2 backup through oec.sh (dashboard restore; the MCP tools here have no restore call), then `git push --force-with-lease origin <previous-main-sha>:main` only with the user's explicit approval. Do not uninstall `website` as a rollback — uninstall leaves orphaned COW views and menus.
