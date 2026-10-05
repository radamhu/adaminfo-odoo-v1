## Customer Operations Dashboard

Odoo 18 custom addon plus a Python-based seeding/testing toolkit that drives an Odoo instance over XML-RPC.

Repository layout :

```
customer_operations_dashboard/   Odoo addon: per-customer financial & operational metrics
website_adaminfo_theme/          Odoo addon: adaminformatika.hu custom website theme
seed/                            XML-RPC seed scripts (demo/test data generation)
tests/                           pytest suite — exercises the live Odoo API via XML-RPC
docs/                            project docs
```

Adds a read-only SQL view (`customer.operations.report`) and partner-form widgets showing, per customer per month:

- Revenue, labor cost, margin, margin %
- Timesheet hours
- Helpdesk tickets created, SLA %

Depends on: `contacts`, `sale`, `account`, `hr_timesheet`, `hr_employee_cost_history`, `helpdesk_mgmt`, `helpdesk_mgmt_sla`.

Install by placing the addon on your Odoo instance's addons path and enabling it from Apps.

### Operations tab "Revenue" vs core "Invoiced" button — not the same number

The partner form's **Operations tab → Revenue** and the standard **Invoiced** smart button (from Odoo's `account`/`sale` core, not this addon) are computed by two independent code paths and will diverge:

| | Operations tab `revenue_total`/`revenue_month` | Core `total_invoiced` (Invoiced button) |
|---|---|---|
| Source | `res_partner.py: _compute_operations_financials` | Odoo core (not in this addon) |
| Tax | **Tax-included** (`amount_total`) | **Tax-excluded** (untaxed amount) |
| Credit notes | Ignored — invoices only | Netted against invoices |
| Contacts | Exact `partner_id` match only | Rolls up child contacts too |
| Company | No `company_id` filter | Scoped to allowed companies |
| Currency | Raw sum, no conversion | Converted to company currency |
| Period | Month bucket + all-time | All-time only |

In practice the tax difference is usually the biggest driver — e.g. a customer with one $73,907.05 invoice (15% tax) shows `revenue_total = 73,907.05` on the Operations tab but `total_invoiced = 64,267.00` on the Invoiced button. Before treating a mismatch as a bug, check whether the customer also has credit notes, child contacts with their own invoices, or invoices across multiple companies/currencies — any of those compound the gap further.

## Website Adaminfo Theme

Odoo 18 theme addon rebuilding adaminformatika.hu (personal portfolio
site) as a single Website-Builder-editable page, replacing the old
static HTML5-UP template. Design spec:
`docs/superpowers/specs/2026-10-05-adaminfo-website-design.md`.

```
website_adaminfo_theme/
├── models/theme_website_adaminfo_theme.py   theme.utils post_copy hook
├── static/src/scss/
│   ├── primary_variables.scss   PREPENDED — fonts + $o-website-values-palettes only
│   ├── colors.scss              NOT prepended — $o-color-palettes merge
│   └── theme.scss               anchor-scroll offset for sticky header
├── static/src/img/              real logo (adaminformatika_logo.png)
├── views/snippets/sections.xml  Hero/About/Projects/Contact, incl. real
│                                 s_website_form (not hand-authored — pulled
│                                 live from this env's own /contactus page)
└── data/                        menu.xml (anchor nav), website_logo.xml
```

Brand (navy `#001323` / gold `#D9A74A`) wired through Odoo's **real**
`$o-color-palettes` + `o_cc` system — selectable in Website Builder's
own Theme → color picker, not hardcoded CSS. Took 4 deploy iterations
to get right; worth knowing before touching this file again:

1. **Don't replace `$o-color-palettes`, map-merge it.** A plain
   `$o-color-palettes: (...)` assignment wipes out `base-1`/`base-2`
   entries core's own SCSS depends on via `map-get()` — crashes with
   `argument $map1 ... must be a map`.
2. **Don't prepend the file with the `$o-color-palettes` merge.**
   `prepend` means "before literally everything," including website
   module's own foundational palette definition — `Undefined variable`.
   Split into two files: `primary_variables.scss` stays prepended (only
   for `$o-website-values-palettes`), `colors.scss` is NOT prepended
   (normal dependency order, loads after website's own scss).
3. **`'menu'`/`'footer'`/`'copyright'` are `o_cc` index numbers (1-5),
   not `o-color-N` indices.** `o_cc4` → `o-color-1`, not `o-color-4`.
   Confirmed from core's own `$o-base-color-palette` comment
   (`'menu': 1, // o_cc1`).
4. Register the palette name via
   `$o-selected-color-palettes-names: append(...)` so it actually shows
   up in the Builder's picker — same mechanism the official
   `odoo/addons/theme_test_custo` reference module uses.

When stuck on an SCSS compile error, read Odoo core's actual source
rather than guessing — `docker exec <env_id>_odoo find /usr/lib/python3/dist-packages/odoo/addons -name primary_variables.scss`
on the oec.sh host finds every shipped theme module plus core's own
2000+-line `website/static/src/scss/primary_variables.scss`. A "css
error occured, using an old style" banner in the Website Builder
backend (not the plain frontend) is the signal a compile actually
failed — the plain frontend silently falls back to an old cached style
instead of showing anything.

**Deploying this addon** (same oec.sh flow as below, with one addition):
after `git push` + oec.sh redeploy, the module needs an explicit
install/upgrade — `ir.module.module.button_immediate_install` (first
install) or `button_immediate_upgrade` (subsequent changes) over
XML-RPC, **and** clear cached asset bundles
(`ir.attachment` where `name like 'assets_%'`, `unlink`) so the SCSS
actually recompiles. Verify by checking the Website Builder backend
(`/odoo/website`) for the css-error banner before trusting any
screenshot of the plain frontend.

**Status (2026-10-05):** verified working on `adaminfo-dev-1869`
(navy/gold render correctly, real contact form submits to `mail.mail`,
no compile errors). **Not yet done:** end-to-end form-submission
verification (confirm it actually lands in Odoo), install on
`adaminfo-prod-1139`, DNS cutover. One known cosmetic bug left
unfixed by request: Projects section card headings render in a broken
fallback font.

## Demo

<video src="operations_dashboard_demo.mp4" controls width="600"></video>

[operations_dashboard_demo.mp4](operations_dashboard_demo.mp4) — Operations tab: revenue/margin/hours/tickets/SLA, All-Time toggle, monthly trend table.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env.dev   # fill in ODOO_ERP_URL, ODOO_LOGIN_USERNAME, ODOO_LOGIN_PASSWORD, ODOO_DB
```

`.envrc` (direnv) auto-activates `.venv` and loads `.env.dev` on `cd` into the repo.

## Seeding data

```bash
python -m seed.runner                    # seed all modules, in order
python -m seed.runner --only crm         # seed a single module
python -m seed.runner --wipe             # wipe all seeded data
python -m seed.runner --wipe --only crm  # wipe a single module
python -m seed.runner --env .env.prod    # target a different environment
```

Seed order: `products → contacts → crm → sale → project → invoicing → timesheet → knowledge`. `prod_sales` is available via `--only prod_sales` but not part of the default order.

## Tests

```bash
pytest
```

Tests hit the Odoo instance configured in `.env.dev` over XML-RPC — no mocking of Odoo itself, only of `seed.runner`'s module dispatch in `test_runner.py`.

## Environment variables

See `.env.example`. Never commit `.env.dev` / `.env.prod` (already gitignored).

## Deploying a ticket

Use Claude Code skill `odoo-oecsh-ticket-deploy` (`~/.claude/skills/odoo-oecsh-ticket-deploy/SKILL.md`) for end-to-end ticket → deploy → verify runbook, this repo included:

1. Read ticket (Jira/Linear/GitHub Issues)
2. Code change, commit, push to branch target env tracks
3. Redeploy target env via oec.sh API (`api.oec.sh/api/public/v1`, not SSH+git pull)
4. Poll deploy status till done (~180s)
5. Playwright: activate dev mode, upgrade module (search technical name first — don't click Upgrade off unfiltered Apps list, silently misfires)
6. Verify live (real field value in accessibility snapshot, not just "no error")
7. Screenshot (`fullPage: true`)
8. Comment on ticket: commit hash, env, what got verified

Needs oec.sh `full_access` API key + `env_id` per target env (from per-env `.env.*` file). Ask which repo/project/env/module if ambiguous — never deploy to prod-looking env without confirm.
