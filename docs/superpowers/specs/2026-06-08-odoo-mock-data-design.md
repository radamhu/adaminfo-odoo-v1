# Odoo Mock Data Seeder — Design Spec

**Date:** 2026-06-08
**Purpose:** Development/testing seed data for Odoo ERP Community Edition
**Scope:** CRM, Sale, Contacts, Project, Invoicing, Timesheet, Knowledge

---

## Context

The project connects to an Odoo Community instance via XML-RPC. Credentials and URL are stored in `.env.dev`. The seeder produces moderate-volume, realistic-looking data for local development and integration testing. All seeded records are tagged with a `[SEED]` name prefix so they can be identified and removed cleanly.

---

## Directory Structure

```
seed/
├── __init__.py
├── runner.py          # CLI entry point
├── connection.py      # XML-RPC client, loads .env.dev
├── products.py        # prerequisite: products needed by sale & invoicing
├── contacts.py        # res.partner (companies + individuals)
├── crm.py             # crm.lead (leads + opportunities)
├── sale.py            # sale.order + sale.order.line
├── project.py         # project.project + project.task
├── invoicing.py       # account.move (customer invoices)
├── timesheet.py       # account.analytic.line
└── knowledge.py       # knowledge.article
```

---

## Connection Layer (`connection.py`)

- Loads `.env.dev` via `python-dotenv` (`ODOO_ERP_URL`, `ODOO_LOGIN_USERNAME`, `ODOO_LOGIN_PASSWORD`)
- Authenticates once against `/xmlrpc/2/common` and caches `uid`
- Exposes `OdooClient` with methods:
  - `search_read(model, domain, fields, limit)`
  - `create(model, vals)` → returns new record id
  - `write(model, ids, vals)`
  - `unlink(model, ids)`
  - `execute(model, method, *args, **kwargs)` — for workflow calls (e.g. `action_confirm`)

---

## CLI Layer (`runner.py`)

### Usage

```bash
python seed/runner.py                      # seed everything (idempotent)
python seed/runner.py --only crm           # seed one module only
python seed/runner.py --wipe               # wipe all seeded data (no re-seed)
python seed/runner.py --wipe --only crm    # wipe one module's data only
# To wipe and re-seed: run --wipe then run without --wipe
```

### Execution order

Dependencies flow left to right:

```
products → contacts → crm → sale → project → invoicing → timesheet → knowledge
```

Each module file exports exactly two functions:

```python
def seed(client: OdooClient) -> None: ...
def wipe(client: OdooClient) -> None: ...
```

The runner calls them in the correct order, printing progress to stdout.

---

## Module Data Plan

### `products.py` — prerequisite, not user-facing

| Field | Values |
|---|---|
| Model | `product.template` |
| Count | 8 |
| Types | 5 service (`service`), 3 storable (`consu`) |
| Names | Mixed HU/EN: e.g. `[SEED] Consulting`, `[SEED] Tanácsadás`, `[SEED] Support`, `[SEED] Szoftver licensz`, … |

### `contacts.py` — `res.partner`

| Segment | Count |
|---|---|
| HU companies | 8 |
| EN companies | 5 |
| Individuals (linked to companies) | 12 |
| **Total** | **25** |

- Mix of `customer_rank=1` and `supplier_rank=1`
- HU contacts use Hungarian names, cities (Budapest, Debrecen, Pécs, Győr), and `country_id` = Hungary
- EN contacts use English names, cities (London, Berlin, Vienna), appropriate countries

### `crm.py` — `crm.lead`

| Type | Count | Stages |
|---|---|---|
| Leads | 10 | New, Qualified |
| Opportunities | 15 | New → Won/Lost spread |

- `partner_id` references seeded contacts
- `expected_revenue` range: 500–50 000
- Mix of HU and EN names/descriptions

### `sale.py` — `sale.order` + `sale.order.line`

| State | Count |
|---|---|
| Draft (`draft`) | 5 |
| Sent (`sent`) | 5 |
| Confirmed (`sale`) | 7 |
| Cancelled (`cancel`) | 3 |

- Each order has 2–4 lines using seeded products
- `partner_id` references seeded contacts
- Line quantities: 1–20; unit prices pulled from product list price

### `project.py` — `project.project` + `project.task`

| Model | Count |
|---|---|
| Projects | 6 |
| Tasks | 30 (~5 per project) |

- Task stages spread: To Do, In Progress, Done
- Projects linked to seeded contacts via `partner_id`
- Mix of HU and EN project/task names

### `invoicing.py` — `account.move`

| State | Count |
|---|---|
| Draft | 8 |
| Posted | 12 |

- Type: `out_invoice` (customer invoices)
- `partner_id` references seeded contacts
- 2–3 invoice lines per invoice using seeded products
- Posted invoices have a `invoice_date` spread over the last 90 days
- Where a confirmed sale order exists for the same contact, `invoice_origin` references it

### `timesheet.py` — `account.analytic.line`

| Field | Values |
|---|---|
| Count | 40 entries |
| Projects | All 6 seeded projects |
| Employee | Admin user's linked employee (fallback: first available employee) |
| Hours | 0.5–8 per entry |
| Dates | Spread over last 60 days |
| Descriptions | Mix of HU/EN task descriptions |

### `knowledge.py` — `knowledge.article`

| Type | Count |
|---|---|
| Top-level articles | 5 |
| Child articles | 10 |
| **Total** | **15** |

- Mix of HU and EN titles and body content (plain HTML)
- Topics: onboarding, processes, product docs, internal notes

---

## Idempotency & Wipe Strategy

### Check-before-create (idempotency)
Every `seed()` function searches for existing records matching `[('name', 'like', '[SEED]')]` (or equivalent identifying field) before creating. If found, the record is skipped.

### Wipe (`--wipe` flag)
Every `wipe()` function:
1. Searches for all records with `[SEED]` in the identifying field
2. For posted invoices: calls `button_cancel` before `unlink`
3. For confirmed sale orders: calls `action_cancel` before `unlink`
4. Calls `unlink()` on remaining records

Wipe runs in **reverse dependency order**:
```
knowledge → timesheet → invoicing → project → sale → crm → contacts → products
```

---

## Dependencies

- `python-dotenv` — loads `.env.dev`
- Standard library `xmlrpc.client` — no third-party Odoo client needed
- Python 3.9+

No ORM, no Odoo source code required. Pure XML-RPC over HTTPS.

---

## Out of Scope

- HR employees (timesheet uses the admin user's employee record)
- Inventory / stock moves
- Purchase orders
- Multi-company setup
- Attachments / binary fields
