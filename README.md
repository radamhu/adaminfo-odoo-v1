# Customer Operations Dashboard

Odoo 18 addons with Python tools for seeding and testing Odoo over XML-RPC.

## Repository layout

```text
customer_operations_dashboard/  Customer financial and operational metrics
website_adaminfo_theme/          adaminformatika.hu website theme
seed/                            Demo/test data generators
tests/                           Live XML-RPC integration tests
docs/                            Project documentation
```

## Customer operations addon

Adds a read-only SQL view (`customer.operations.report`) and partner-form widgets with monthly customer metrics:

- Revenue, labor cost, margin, and margin percentage
- Timesheet hours
- Helpdesk tickets and SLA percentage

Dependencies: `contacts`, `sale`, `account`, `hr_timesheet`, `hr_employee_cost_history`, `helpdesk_mgmt`, and `helpdesk_mgmt_sla`.

Install the addon from Apps after adding it to the Odoo addons path.

### Revenue vs. Invoiced

The Operations tab's Revenue value and Odoo's Invoiced smart button use different calculations.

|              | Operations Revenue                                       | Core Invoiced           |
| ------------ | -------------------------------------------------------- | ----------------------- |
| Source       | `_compute_operations_financials` in `res_partner.py` | Odoo core               |
| Tax          | Included (`amount_total`)                              | Excluded                |
| Credit notes | Ignored                                                  | Netted against invoices |
| Contacts     | Exact`partner_id`                                      | Includes child contacts |
| Company      | No`company_id` filter                                  | Allowed companies only  |
| Currency     | No conversion                                            | Company currency        |
| Period       | Monthly and all-time                                     | All-time                |

Check these differences before reporting a mismatch. Tax is usually the main cause.

## Website theme addon

`website_adaminfo_theme` rebuilds adaminformatika.hu as a Website Builder-editable page. See the [design specification](docs/superpowers/specs/2026-10-05-adaminfo-website-design.md).

```text
website_adaminfo_theme/
├── models/theme_website_adaminfo_theme.py  Theme post-copy hook
├── static/src/scss/
│   ├── primary_variables.scss              Fonts and website palette selection
│   ├── colors.scss                         Color palette merge
│   └── theme.scss                          Sticky-header scroll offset
├── static/src/img/                         Logo
├── views/snippets/sections.xml             Hero, About, Projects, and Contact
└── data/                                   Menu and website logo records
```

The navy (`#001323`) and gold (`#D9A74A`) brand colors use Odoo's `$o-color-palettes` and `o_cc` system.

### SCSS requirements

- Merge into `$o-color-palettes`; replacing it removes core palettes and breaks compilation.
- Keep the palette merge in non-prepended `colors.scss`. Prepending it runs before Odoo defines the base palette.
- Treat `menu`, `footer`, and `copyright` values as `o_cc` indexes (1–5), not `o-color-N` indexes.
- Append the palette name to `$o-selected-color-palettes-names` so it appears in Website Builder.

For compile errors, inspect Odoo's shipped `primary_variables.scss` files. Website Builder (`/odoo/website`) shows CSS compilation errors; the public page may silently use cached assets.

### Theme deployment

After pushing and redeploying through oec.sh:

1. Install or upgrade the module through `ir.module.module` XML-RPC (`button_immediate_install` or `button_immediate_upgrade`).
2. Delete cached `ir.attachment` records whose names match `assets_%`.
3. Check `/odoo/website` for CSS errors.

Status as of 2026-10-05: working on `adaminfo-dev-1869`. Remaining work: verify end-to-end contact form delivery, deploy to `adaminfo-prod-1139`, and cut over DNS. The Projects headings have a known fallback-font issue.

### Guidelines for the web designer

Once this is live on prod, a designer can do real day-to-day editing through the Website Builder UI alone — no dev, no code, no redeploy. Enter edit mode via the "Edit" button on the live site (admin login required).

**Self-serve, no dev needed:**

- **Page content** — Hero/About/Projects/Contact text and images: click into any section and edit inline (plain `oe_structure` blocks, that's what they're for)
- **Colors** — Website Builder → Customize → Theme → color palette picker. The "adaminfo" navy/gold palette is a real, selectable entry (not hardcoded CSS) — pick it, tweak it, or switch to a different stock palette entirely
- **Menu / nav items** — Website → Configuration → Menu, or drag-reorder inline
- **Header/footer template** — Builder's header/footer customize panel (switch layout variant)
- **Logo** — Builder's logo upload, under site settings
- **Contact form fields** — Builder's own form editor (add/remove/relabel fields). Use the Builder's editor, not hand-edited XML — it recomputes the hidden signature hash itself; a manual XML edit won't

**Still needs a dev:**

- Adding a brand-new font not already registered in `$o-theme-font-configs` (currently Inter + Playfair Display)
- New homepage sections, new pages, or structural layout changes beyond what a snippet/section supports
- Anything touching `primary_variables.scss` / `colors.scss` directly — see the SCSS gotchas above before anyone goes near these files again
- Redeploys, module upgrades, DNS/infra

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env.dev
```

Set `ODOO_ERP_URL`, `ODOO_LOGIN_USERNAME`, `ODOO_LOGIN_PASSWORD`, and `ODOO_DB` in `.env.dev`.

With direnv, `.envrc` activates `.venv` and loads `.env.dev` when entering the repository.

## Seeding data

```bash
python -m seed.runner                    # Seed all modules
python -m seed.runner --only crm         # Seed one module
python -m seed.runner --wipe             # Wipe all seeded data
python -m seed.runner --wipe --only crm  # Wipe one module
python -m seed.runner --env .env.prod    # Use another environment
```

Default order: `products → contacts → crm → sale → project → invoicing → timesheet → knowledge`.

`prod_sales` is available through `--only prod_sales` but is not included by default.

## Tests

```bash
pytest
```

Tests call the Odoo instance configured in `.env.dev`. Odoo is not mocked; only `seed.runner` module dispatch is mocked in `test_runner.py`.

## Environment variables

See `.env.example`. Do not commit `.env.dev` or `.env.prod`; both are gitignored.

## Deploying a ticket

Use the `odoo-oecsh-ticket-deploy` Claude Code skill at `~/.claude/skills/odoo-oecsh-ticket-deploy/SKILL.md`:

1. Read the ticket.
2. Implement, commit, and push the change to the target environment's branch.
3. Redeploy through `api.oec.sh/api/public/v1`.
4. Wait for deployment to finish.
5. Enable developer mode and upgrade the module by technical name.
6. Verify the live field value with Playwright.
7. Capture a full-page screenshot.
8. Comment on the ticket with the commit, environment, and verification result.

Requires an oec.sh `full_access` API key and target `env_id` from the environment file. Confirm before deploying to production.
