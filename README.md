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
