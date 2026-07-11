## Customer Operations Dashboard

Odoo 18 custom addon plus a Python-based seeding/testing toolkit that drives an Odoo instance over XML-RPC.

Repository layout :

```
customer_operations_dashboard/   Odoo addon: per-customer financial & operational metrics
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
