# adaminfo-odoo-v1

Odoo 18 addons plus Python XML-RPC tools for seeding and testing. Global rules (`~/.claude/AGENTS-rules.md`) apply on top; this file is repo-specific only. Details: `README.md`.

## Layout

- `customer_operations_dashboard/`: partner financial/operational metrics addon
- `website_adaminfo_theme/`: adaminformatika.hu website theme (not a `theme_*` module)
- `seed/`: demo/test data generators (`python -m seed.runner`)
- `tests/`: live XML-RPC integration tests
- `docs/`: specs, plans, migration logs

## Commands

- Setup: `python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt && cp .env.example .env.dev`
- Test: `pytest` (hits the live Odoo in `.env.dev`; only `seed.runner` dispatch is mocked)
- Seed: `python -m seed.runner [--only <module>] [--wipe] [--env .env.prod]`
- Theme rollout check: `seed/verify_website_theme.py`

## Don'ts

- Never commit `.env.dev` or `.env.prod`.
- Do not seed or wipe against `.env.prod` without explicit confirmation.
- Confirm before any production deploy or module upgrade.
- Theme SCSS: merge into `$o-color-palettes` (never replace), keep the merge in non-prepended `colors.scss`, treat `menu`/`footer`/`copyright` as `o_cc` indexes (1-5). Read the SCSS section in `README.md` before touching `primary_variables.scss` or `colors.scss`.
- Site defaults in `hooks.py` run once (install + migration). Do not make them run on every upgrade.

## Deploy

- Ticket deploys: `odoo-oecsh-ticket-deploy` skill (oec.sh API, env branch push, redeploy, module upgrade, verify).
- Theme: after redeploy, upgrade via `ir.module.module` XML-RPC, delete `ir.attachment` named `assets_%`, check `/odoo/website` for CSS errors.

## Memory

Shared notes in `.agent-notes.md` (gitignored). A Stop hook (`.claude/hooks/notes-reminder.sh`) reminds Claude Code to update it.
