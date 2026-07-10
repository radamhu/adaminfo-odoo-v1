# Customer Operations Dashboard Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the `customer_operations_dashboard` Odoo 18 addon: an "Operations" tab on the partner form showing live Revenue/Margin/Hours/Tickets/SLA (this-month and all-time), plus a live trend graph backed by a PostgreSQL-view reporting model.

**Architecture:** Compute fields added to `res.partner` via inheritance for live current-value stats. A separate `_auto=False` model (`customer.operations.report`, same pattern as core `sale.report`) backed by a `CREATE VIEW` aggregates revenue/labor cost/hours/tickets/SLA per partner per month directly from Postgres — always live, no cron. The view is embedded as an inline `<graph>` on a `One2many` field in the partner form.

**Tech Stack:** Odoo 18, PostgreSQL (raw SQL view via `init()`), OCA `hr_employee_cost_history`, OCA `helpdesk_mgmt` + `helpdesk_mgmt_sla`, Python `pytest` (repo-level static checks only — no local Odoo), `xmlrpc` (`seed/connection.py`) for post-deploy verification.

## Global Constraints

- Module path: `addons/customer_operations_dashboard/`. Target Odoo version: 18.0.
- Depends: `contacts`, `sale`, `account`, `hr_timesheet`, `hr_employee_cost_history` (OCA `timesheet` repo), `helpdesk_mgmt` (OCA `helpdesk` repo), `helpdesk_mgmt_sla` (OCA `helpdesk` repo).
- **No local Odoo installation exists in this repo/environment.** Dev/prod are remote cloud instances reachable only via XML-RPC (`.env.dev`/`.env.prod`, `seed/connection.py`). Deployment = commit to this repo; ops triggers an environment redeploy. There is no way to run `odoo-bin --test-enable` here.
- Consequence for every task below: addon-internal `TransactionCase` test files are still written (correct practice, will run under Odoo's own test runner whenever the module is installed/upgraded with `--test-enable`), but **cannot be executed from this repo**. Each such step is marked accordingly — the executable local verification is `python -m py_compile` (syntax) and XML well-formedness parsing, run via a repo-level pytest test (Task 1). Real functional pass/fail happens post-deploy (Task 6/7) via XML-RPC against the dev instance.
- Custom fields on `res.partner` use **no `x_` prefix** — that prefix is only required for fields not defined in Python code (e.g. Studio-added). These are proper addon-defined fields.
- Two spec ambiguities resolved here (documented so nobody re-derives them mid-task): `margin_pct` and `sla_percent` each get a `_month` and `_total` variant (matching every other paired metric, so the "This Month"/"All-Time" toggle actually changes their values). `open_tickets_count` has no period variant — it is inherently a live, current-moment count and is shown unchanged regardless of toggle state.
- The monthly SQL-view report renames the spec's "open tickets" column to **`tickets_created`** (ticket volume opened that month) — "open tickets" has no coherent per-month-in-the-past meaning (a past month can't have "currently open" tickets); volume is the meaningful trend metric. The live, current "open right now" count stays on `res.partner` as `open_tickets_count`.
- Verified against actual OCA source (not guessed): `hr.employee.timesheet.cost.history` (fields: `employee_id`, `currency_id`, `hourly_cost`, `starting_date`, `comment`) from `OCA/timesheet` 18.0; `helpdesk.ticket` (`partner_id`, `stage_id`, `create_date`) and `helpdesk.ticket.stage` (`closed` boolean) and `helpdesk.ticket.sla` (`ticket_id`, `state` — stored, values `accomplished`/`in_progress`/`expired`/`on_hold`) from `OCA/helpdesk` 18.0.

---

### Task 1: Module Scaffold + Local Static-Check Harness

**Files:**
- Create: `addons/customer_operations_dashboard/__init__.py`
- Create: `addons/customer_operations_dashboard/__manifest__.py`
- Create: `addons/customer_operations_dashboard/models/__init__.py`
- Create: `tests/test_customer_operations_dashboard_addon.py`

**Interfaces:**
- Produces: a valid, empty-but-loadable addon skeleton that every later task adds files into. Produces the repo-level static-check test that every later task's Python/XML files must keep passing.

- [ ] **Step 1: Write the failing static-check test**

```python
# tests/test_customer_operations_dashboard_addon.py
import ast
import py_compile
import xml.dom.minidom
from pathlib import Path

ADDON_DIR = Path(__file__).resolve().parent.parent / "addons" / "customer_operations_dashboard"


def _python_files():
    return sorted(ADDON_DIR.rglob("*.py"))


def _xml_files():
    return sorted(ADDON_DIR.rglob("*.xml"))


def test_addon_directory_exists():
    assert ADDON_DIR.is_dir(), f"expected addon at {ADDON_DIR}"


def test_manifest_is_valid_dict_with_required_keys():
    manifest_path = ADDON_DIR / "__manifest__.py"
    assert manifest_path.is_file()
    manifest = ast.literal_eval(manifest_path.read_text())
    assert isinstance(manifest, dict)
    for key in ("name", "version", "depends", "data"):
        assert key in manifest, f"manifest missing required key: {key}"


def test_all_python_files_compile():
    files = _python_files()
    assert files, "expected at least one .py file in the addon"
    for f in files:
        py_compile.compile(str(f), doraise=True)


def test_all_xml_files_are_well_formed():
    for f in _xml_files():
        xml.dom.minidom.parse(str(f))
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_customer_operations_dashboard_addon.py -v`
Expected: FAIL — `test_addon_directory_exists` fails with `AssertionError: expected addon at .../addons/customer_operations_dashboard` (directory doesn't exist yet).

- [ ] **Step 3: Create the module skeleton**

```python
# addons/customer_operations_dashboard/__init__.py
from . import models
```

```python
# addons/customer_operations_dashboard/__manifest__.py
{
    "name": "Customer Operations Dashboard",
    "version": "18.0.1.0.0",
    "summary": "Per-customer financial and operational metrics on the partner form",
    "category": "Customer Relationship Management",
    "author": "Adaminfo",
    "license": "LGPL-3",
    "depends": [
        "contacts",
        "sale",
        "account",
        "hr_timesheet",
        "hr_employee_cost_history",
        "helpdesk_mgmt",
        "helpdesk_mgmt_sla",
    ],
    "data": [],
    "installable": True,
    "application": False,
}
```

```python
# addons/customer_operations_dashboard/models/__init__.py
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_customer_operations_dashboard_addon.py -v`
Expected: PASS (4 passed)

- [ ] **Step 5: Commit**

```bash
git add addons/customer_operations_dashboard/__init__.py \
        addons/customer_operations_dashboard/__manifest__.py \
        addons/customer_operations_dashboard/models/__init__.py \
        tests/test_customer_operations_dashboard_addon.py
git commit -m "feat: scaffold customer_operations_dashboard addon"
```

---

### Task 2: res.partner — Financial Compute Fields (Revenue/Labor Cost/Margin)

**Files:**
- Create: `addons/customer_operations_dashboard/models/res_partner.py`
- Modify: `addons/customer_operations_dashboard/models/__init__.py`
- Create: `addons/customer_operations_dashboard/tests/__init__.py`
- Create: `addons/customer_operations_dashboard/tests/test_res_partner_financials.py`

**Interfaces:**
- Consumes: nothing beyond stock `res.partner`, `account.move`, `account.analytic.line`, `hr.employee.timesheet.cost.history`.
- Produces: on `res.partner` — `revenue_month`, `revenue_total`, `labor_cost_month`, `labor_cost_total`, `margin_month`, `margin_total`, `margin_pct_month`, `margin_pct_total`, `hours_month`, `hours_total` (all `Monetary`/`Float`, non-stored, compute-only). Later tasks (3, 4) add more fields to this same file/class.

- [ ] **Step 1: Write the TransactionCase test (cannot run locally — no Odoo install; see Global Constraints)**

```python
# addons/customer_operations_dashboard/tests/__init__.py
from . import test_res_partner_financials
```

```python
# addons/customer_operations_dashboard/tests/test_res_partner_financials.py
from datetime import date

from odoo.tests.common import TransactionCase


class TestResPartnerFinancials(TransactionCase):
    def setUp(self):
        super().setUp()
        self.partner = self.env["res.partner"].create({"name": "Test Customer"})

    def test_zero_activity_partner_has_zero_financials(self):
        self.assertEqual(self.partner.revenue_total, 0)
        self.assertEqual(self.partner.revenue_month, 0)
        self.assertEqual(self.partner.labor_cost_total, 0)
        self.assertEqual(self.partner.margin_total, 0)
        self.assertEqual(self.partner.margin_pct_total, 0)
        self.assertEqual(self.partner.hours_total, 0)

    def test_revenue_splits_current_month_vs_prior_month(self):
        today = date.today()
        prior_month = (today.replace(day=1) - date.resolution).replace(day=1)
        self.env["account.move"].create({
            "partner_id": self.partner.id,
            "move_type": "out_invoice",
            "invoice_date": today,
            "state": "draft",
            "invoice_line_ids": [(0, 0, {"name": "Service", "price_unit": 1000, "quantity": 1})],
        }).action_post()
        self.env["account.move"].create({
            "partner_id": self.partner.id,
            "move_type": "out_invoice",
            "invoice_date": prior_month,
            "state": "draft",
            "invoice_line_ids": [(0, 0, {"name": "Service", "price_unit": 500, "quantity": 1})],
        }).action_post()
        self.assertEqual(self.partner.revenue_month, 1000)
        self.assertEqual(self.partner.revenue_total, 1500)

    def test_margin_pct_guards_divide_by_zero(self):
        self.assertEqual(self.partner.margin_pct_total, 0)
        self.assertEqual(self.partner.margin_pct_month, 0)

    def test_labor_cost_uses_rate_in_effect_at_line_date(self):
        employee = self.env["hr.employee"].create({"name": "Test Employee"})
        project = self.env["project.project"].create({
            "name": "Test Project", "partner_id": self.partner.id,
        })
        self.env["hr.employee.timesheet.cost.history"].create({
            "employee_id": employee.id, "hourly_cost": 10.0, "starting_date": "2020-01-01",
        })
        self.env["hr.employee.timesheet.cost.history"].create({
            "employee_id": employee.id, "hourly_cost": 20.0, "starting_date": date.today(),
        })
        self.env["account.analytic.line"].create({
            "name": "/", "project_id": project.id, "employee_id": employee.id,
            "unit_amount": 5, "date": date.today(),
        })
        self.assertEqual(self.partner.labor_cost_month, 100.0)  # 5h * 20 (current rate)
        self.assertEqual(self.partner.hours_month, 5)
```

- [ ] **Step 2: Run local syntax check (the only executable verification available)**

Run: `python -m py_compile addons/customer_operations_dashboard/tests/test_res_partner_financials.py`
Expected: no output, exit code 0 (valid syntax). This does NOT prove the test logic passes against a real Odoo ORM — that requires the dev instance (Task 6/7).

- [ ] **Step 3: Write the implementation**

```python
# addons/customer_operations_dashboard/models/res_partner.py
from datetime import date

from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    revenue_month = fields.Monetary(
        string="Revenue (This Month)", compute="_compute_operations_financials",
        currency_field="currency_id",
    )
    revenue_total = fields.Monetary(
        string="Revenue (All-Time)", compute="_compute_operations_financials",
        currency_field="currency_id",
    )
    labor_cost_month = fields.Monetary(
        string="Labor Cost (This Month)", compute="_compute_operations_financials",
        currency_field="currency_id",
    )
    labor_cost_total = fields.Monetary(
        string="Labor Cost (All-Time)", compute="_compute_operations_financials",
        currency_field="currency_id",
    )
    margin_month = fields.Monetary(
        string="Margin (This Month)", compute="_compute_operations_financials",
        currency_field="currency_id",
    )
    margin_total = fields.Monetary(
        string="Margin (All-Time)", compute="_compute_operations_financials",
        currency_field="currency_id",
    )
    margin_pct_month = fields.Float(
        string="Margin % (This Month)", compute="_compute_operations_financials",
    )
    margin_pct_total = fields.Float(
        string="Margin % (All-Time)", compute="_compute_operations_financials",
    )
    hours_month = fields.Float(
        string="Hours Used (This Month)", compute="_compute_operations_financials",
    )
    hours_total = fields.Float(
        string="Hours Used (All-Time)", compute="_compute_operations_financials",
    )

    def _operations_timesheet_domain(self, partner):
        return [
            "|",
            ("project_id.partner_id", "=", partner.id),
            ("task_id.partner_id", "=", partner.id),
        ]

    def _operations_labor_cost(self, lines):
        # N+1 lookups here are intentional for v1: correctness over
        # premature optimization at small-MSP data volumes.
        cost_history = self.env["hr.employee.timesheet.cost.history"]
        total = 0.0
        for line in lines:
            if not line.employee_id:
                continue
            history = cost_history.search(
                [
                    ("employee_id", "=", line.employee_id.id),
                    ("starting_date", "<=", line.date),
                ],
                order="starting_date desc",
                limit=1,
            )
            total += line.unit_amount * (history.hourly_cost if history else 0.0)
        return total

    @api.depends()
    def _compute_operations_financials(self):
        move_model = self.env["account.move"]
        analytic_model = self.env["account.analytic.line"]
        month_start = date.today().replace(day=1)
        for partner in self:
            invoice_domain = [
                ("partner_id", "=", partner.id),
                ("move_type", "=", "out_invoice"),
                ("state", "=", "posted"),
            ]
            all_invoices = move_model.search(invoice_domain)
            month_invoices = all_invoices.filtered(
                lambda m: m.invoice_date and m.invoice_date >= month_start
            )
            revenue_total = sum(all_invoices.mapped("amount_total"))
            revenue_month = sum(month_invoices.mapped("amount_total"))

            all_lines = analytic_model.search(self._operations_timesheet_domain(partner))
            month_lines = all_lines.filtered(
                lambda l: l.date and l.date >= month_start
            )
            labor_cost_total = self._operations_labor_cost(all_lines)
            labor_cost_month = self._operations_labor_cost(month_lines)

            partner.revenue_total = revenue_total
            partner.revenue_month = revenue_month
            partner.labor_cost_total = labor_cost_total
            partner.labor_cost_month = labor_cost_month
            partner.margin_total = revenue_total - labor_cost_total
            partner.margin_month = revenue_month - labor_cost_month
            partner.margin_pct_total = (
                partner.margin_total / revenue_total * 100 if revenue_total else 0.0
            )
            partner.margin_pct_month = (
                partner.margin_month / revenue_month * 100 if revenue_month else 0.0
            )
            partner.hours_total = sum(all_lines.mapped("unit_amount"))
            partner.hours_month = sum(month_lines.mapped("unit_amount"))
```

```python
# addons/customer_operations_dashboard/models/__init__.py
from . import res_partner
```

- [ ] **Step 4: Run local syntax check again**

Run: `python -m py_compile addons/customer_operations_dashboard/models/res_partner.py addons/customer_operations_dashboard/models/__init__.py addons/customer_operations_dashboard/tests/test_res_partner_financials.py`
Expected: no output, exit code 0.

- [ ] **Step 5: Run the repo-level static-check suite**

Run: `pytest tests/test_customer_operations_dashboard_addon.py -v`
Expected: PASS (all tests, now covering the new files too).

- [ ] **Step 6: Commit**

```bash
git add addons/customer_operations_dashboard/models/res_partner.py \
        addons/customer_operations_dashboard/models/__init__.py \
        addons/customer_operations_dashboard/tests/__init__.py \
        addons/customer_operations_dashboard/tests/test_res_partner_financials.py
git commit -m "feat: add revenue/labor-cost/margin/hours compute fields to res.partner"
```

---

### Task 3: res.partner — Tickets/SLA Fields + Period Toggle

**Files:**
- Modify: `addons/customer_operations_dashboard/models/res_partner.py`
- Modify: `addons/customer_operations_dashboard/tests/__init__.py`
- Create: `addons/customer_operations_dashboard/tests/test_res_partner_operations.py`

**Interfaces:**
- Consumes: `helpdesk.ticket`, `helpdesk.ticket.stage` (`closed` field), `helpdesk.ticket.sla` (`state` field) from Task 2's file.
- Produces: `open_tickets_count`, `sla_percent_month`, `sla_percent_total`, `period_scope` (Selection: `month`/`all_time`, default `month`) on `res.partner`.

- [ ] **Step 1: Write the TransactionCase test**

```python
# addons/customer_operations_dashboard/tests/test_res_partner_operations.py
from datetime import date, timedelta

from odoo.tests.common import TransactionCase


class TestResPartnerOperations(TransactionCase):
    def setUp(self):
        super().setUp()
        self.partner = self.env["res.partner"].create({"name": "Test Customer"})

    def test_zero_activity_partner_has_zero_ticket_stats(self):
        self.assertEqual(self.partner.open_tickets_count, 0)
        self.assertEqual(self.partner.sla_percent_month, 0)
        self.assertEqual(self.partner.sla_percent_total, 0)

    def test_open_tickets_excludes_closed_stage(self):
        open_stage = self.env["helpdesk.ticket.stage"].create({"name": "Open", "closed": False})
        closed_stage = self.env["helpdesk.ticket.stage"].create({"name": "Closed", "closed": True})
        self.env["helpdesk.ticket"].create({
            "name": "Open ticket", "partner_id": self.partner.id, "stage_id": open_stage.id,
        })
        self.env["helpdesk.ticket"].create({
            "name": "Closed ticket", "partner_id": self.partner.id, "stage_id": closed_stage.id,
        })
        self.assertEqual(self.partner.open_tickets_count, 1)

    def test_period_scope_defaults_to_month(self):
        self.assertEqual(self.partner.period_scope, "month")
```

- [ ] **Step 2: Run local syntax check**

Run: `python -m py_compile addons/customer_operations_dashboard/tests/test_res_partner_operations.py`
Expected: no output, exit code 0.

- [ ] **Step 3: Add the fields and compute method to res_partner.py**

Append to `addons/customer_operations_dashboard/models/res_partner.py` (inside the existing `ResPartner` class, after the fields added in Task 2):

```python
    open_tickets_count = fields.Integer(
        string="Open Tickets", compute="_compute_operations_tickets",
    )
    sla_percent_month = fields.Float(
        string="SLA % (This Month)", compute="_compute_operations_tickets",
    )
    sla_percent_total = fields.Float(
        string="SLA % (All-Time)", compute="_compute_operations_tickets",
    )
    period_scope = fields.Selection(
        [("month", "This Month"), ("all_time", "All-Time")],
        string="Period", default="month",
    )
```

And add the compute method (below `_compute_operations_financials`):

```python
    def _operations_sla_percent(self, partner, extra_domain):
        sla_model = self.env["helpdesk.ticket.sla"]
        slas = sla_model.search(
            [
                ("ticket_id.partner_id", "=", partner.id),
                ("state", "in", ["accomplished", "expired"]),
            ]
            + extra_domain
        )
        total = len(slas)
        if not total:
            return 0.0
        accomplished = len(slas.filtered(lambda s: s.state == "accomplished"))
        return accomplished / total * 100

    @api.depends()
    def _compute_operations_tickets(self):
        ticket_model = self.env["helpdesk.ticket"]
        month_start = date.today().replace(day=1)
        for partner in self:
            partner.open_tickets_count = ticket_model.search_count(
                [
                    ("partner_id", "=", partner.id),
                    ("stage_id.closed", "=", False),
                ]
            )
            partner.sla_percent_total = self._operations_sla_percent(partner, [])
            partner.sla_percent_month = self._operations_sla_percent(
                partner, [("ticket_id.create_date", ">=", month_start)]
            )
```

- [ ] **Step 4: Update tests/__init__.py**

```python
# addons/customer_operations_dashboard/tests/__init__.py
from . import test_res_partner_financials
from . import test_res_partner_operations
```

- [ ] **Step 5: Run local syntax check on the modified files**

Run: `python -m py_compile addons/customer_operations_dashboard/models/res_partner.py addons/customer_operations_dashboard/tests/test_res_partner_operations.py addons/customer_operations_dashboard/tests/__init__.py`
Expected: no output, exit code 0.

- [ ] **Step 6: Run the repo-level static-check suite**

Run: `pytest tests/test_customer_operations_dashboard_addon.py -v`
Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add addons/customer_operations_dashboard/models/res_partner.py \
        addons/customer_operations_dashboard/tests/__init__.py \
        addons/customer_operations_dashboard/tests/test_res_partner_operations.py
git commit -m "feat: add ticket/SLA compute fields and period toggle to res.partner"
```

---

### Task 4: SQL-View Reporting Model (`customer.operations.report`)

**Files:**
- Create: `addons/customer_operations_dashboard/models/customer_operations_report.py`
- Modify: `addons/customer_operations_dashboard/models/__init__.py`
- Modify: `addons/customer_operations_dashboard/models/res_partner.py` (adds the inverse `One2many`)
- Create: `addons/customer_operations_dashboard/security/ir.model.access.csv`
- Modify: `addons/customer_operations_dashboard/__manifest__.py` (adds `data` entry)
- Modify: `addons/customer_operations_dashboard/tests/__init__.py`
- Create: `addons/customer_operations_dashboard/tests/test_customer_operations_report.py`

**Interfaces:**
- Consumes: `account.move`, `account.analytic.line`, `hr.employee.timesheet.cost.history`, `helpdesk.ticket`, `helpdesk.ticket.sla` (all read-only, via raw SQL in `init()`).
- Produces: model `customer.operations.report` with fields `partner_id`, `date`, `revenue`, `labor_cost`, `margin`, `margin_pct`, `hours`, `tickets_created`, `sla_percent`, `currency_id`. Produces `res.partner.operations_report_ids` (`One2many`) consumed by Task 5's view.

- [ ] **Step 1: Write the TransactionCase test**

```python
# addons/customer_operations_dashboard/tests/test_customer_operations_report.py
from datetime import date

from odoo.tests.common import TransactionCase


class TestCustomerOperationsReport(TransactionCase):
    def setUp(self):
        super().setUp()
        self.partner = self.env["res.partner"].create({"name": "Test Customer"})

    def test_no_activity_produces_no_rows(self):
        rows = self.env["customer.operations.report"].search(
            [("partner_id", "=", self.partner.id)]
        )
        self.assertFalse(rows)

    def test_current_month_row_reflects_partial_month_invoice(self):
        self.env["account.move"].create({
            "partner_id": self.partner.id,
            "move_type": "out_invoice",
            "invoice_date": date.today(),
            "state": "draft",
            "invoice_line_ids": [(0, 0, {"name": "Service", "price_unit": 700, "quantity": 1})],
        }).action_post()
        row = self.env["customer.operations.report"].search(
            [("partner_id", "=", self.partner.id)]
        )
        self.assertEqual(len(row), 1)
        self.assertEqual(row.revenue, 700)
        self.assertEqual(row.date.replace(day=1), date.today().replace(day=1))

    def test_one_row_per_partner_per_month(self):
        for day_offset in range(3):
            self.env["account.move"].create({
                "partner_id": self.partner.id,
                "move_type": "out_invoice",
                "invoice_date": date.today(),
                "state": "draft",
                "invoice_line_ids": [(0, 0, {"name": "Service", "price_unit": 100, "quantity": 1})],
            }).action_post()
        rows = self.env["customer.operations.report"].search(
            [("partner_id", "=", self.partner.id)]
        )
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows.revenue, 300)
```

- [ ] **Step 2: Run local syntax check**

Run: `python -m py_compile addons/customer_operations_dashboard/tests/test_customer_operations_report.py`
Expected: no output, exit code 0.

- [ ] **Step 3: Write the SQL-view model**

```python
# addons/customer_operations_dashboard/models/customer_operations_report.py
from odoo import fields, models, tools


class CustomerOperationsReport(models.Model):
    _name = "customer.operations.report"
    _description = "Customer Operations Monthly Report"
    _auto = False
    _order = "date desc"

    partner_id = fields.Many2one("res.partner", string="Customer", readonly=True)
    date = fields.Date(string="Month", readonly=True)
    currency_id = fields.Many2one("res.currency", string="Currency", readonly=True)
    revenue = fields.Monetary(string="Revenue", currency_field="currency_id", readonly=True)
    labor_cost = fields.Monetary(string="Labor Cost", currency_field="currency_id", readonly=True)
    margin = fields.Monetary(string="Margin", currency_field="currency_id", readonly=True)
    margin_pct = fields.Float(string="Margin %", readonly=True)
    hours = fields.Float(string="Hours", readonly=True)
    tickets_created = fields.Integer(string="Tickets Created", readonly=True)
    sla_percent = fields.Float(string="SLA %", readonly=True)

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute(
            f"""
            CREATE VIEW {self._table} AS (
                WITH revenue_cte AS (
                    SELECT
                        partner_id,
                        date_trunc('month', invoice_date)::date AS month,
                        SUM(amount_total) AS revenue
                    FROM account_move
                    WHERE move_type = 'out_invoice'
                      AND state = 'posted'
                      AND partner_id IS NOT NULL
                    GROUP BY partner_id, date_trunc('month', invoice_date)
                ),
                labor_cte AS (
                    SELECT
                        COALESCE(proj.partner_id, task.partner_id) AS partner_id,
                        date_trunc('month', a.date)::date AS month,
                        SUM(a.unit_amount) AS hours,
                        SUM(a.unit_amount * COALESCE(cost.hourly_cost, 0)) AS labor_cost
                    FROM account_analytic_line a
                    LEFT JOIN project_project proj ON proj.id = a.project_id
                    LEFT JOIN project_task task ON task.id = a.task_id
                    LEFT JOIN LATERAL (
                        SELECT h.hourly_cost
                        FROM hr_employee_timesheet_cost_history h
                        WHERE h.employee_id = a.employee_id
                          AND h.starting_date <= a.date
                        ORDER BY h.starting_date DESC
                        LIMIT 1
                    ) cost ON true
                    WHERE COALESCE(proj.partner_id, task.partner_id) IS NOT NULL
                    GROUP BY COALESCE(proj.partner_id, task.partner_id), date_trunc('month', a.date)
                ),
                tickets_cte AS (
                    SELECT
                        t.partner_id AS partner_id,
                        date_trunc('month', t.create_date)::date AS month,
                        COUNT(DISTINCT t.id) AS tickets_created,
                        COUNT(*) FILTER (WHERE s.state = 'accomplished') AS sla_accomplished,
                        COUNT(*) FILTER (WHERE s.state IN ('accomplished', 'expired')) AS sla_finished
                    FROM helpdesk_ticket t
                    LEFT JOIN helpdesk_ticket_sla s ON s.ticket_id = t.id
                    WHERE t.partner_id IS NOT NULL
                    GROUP BY t.partner_id, date_trunc('month', t.create_date)
                ),
                months AS (
                    SELECT partner_id, month FROM revenue_cte
                    UNION
                    SELECT partner_id, month FROM labor_cte
                    UNION
                    SELECT partner_id, month FROM tickets_cte
                )
                SELECT
                    (m.partner_id::bigint * 1000000 +
                     (EXTRACT(YEAR FROM m.month)::bigint * 100 + EXTRACT(MONTH FROM m.month)::bigint)
                    ) AS id,
                    m.partner_id AS partner_id,
                    m.month AS date,
                    (SELECT currency_id FROM res_company ORDER BY id LIMIT 1) AS currency_id,
                    COALESCE(r.revenue, 0) AS revenue,
                    COALESCE(l.labor_cost, 0) AS labor_cost,
                    COALESCE(r.revenue, 0) - COALESCE(l.labor_cost, 0) AS margin,
                    CASE WHEN COALESCE(r.revenue, 0) = 0 THEN 0
                         ELSE (COALESCE(r.revenue, 0) - COALESCE(l.labor_cost, 0)) / r.revenue * 100
                    END AS margin_pct,
                    COALESCE(l.hours, 0) AS hours,
                    COALESCE(tk.tickets_created, 0) AS tickets_created,
                    CASE WHEN COALESCE(tk.sla_finished, 0) = 0 THEN 0
                         ELSE tk.sla_accomplished::float / tk.sla_finished * 100
                    END AS sla_percent
                FROM months m
                LEFT JOIN revenue_cte r ON r.partner_id = m.partner_id AND r.month = m.month
                LEFT JOIN labor_cte l ON l.partner_id = m.partner_id AND l.month = m.month
                LEFT JOIN tickets_cte tk ON tk.partner_id = m.partner_id AND tk.month = m.month
                WHERE m.month >= date_trunc('month', now() - interval '24 months')
            )
            """
        )
```

Note: this view assumes a single-company instance (currency is taken from the first `res_company` row) — matches the freelancer/small-MSP context in `README.md`; multi-company currency handling is explicitly out of scope (YAGNI).

- [ ] **Step 4: Add the inverse One2many to res_partner.py**

Append to the `ResPartner` class in `addons/customer_operations_dashboard/models/res_partner.py` (after the `period_scope` field added in Task 3):

```python
    operations_report_ids = fields.One2many(
        "customer.operations.report", "partner_id",
        string="Operations Monthly Report", readonly=True,
    )
```

- [ ] **Step 5: Update models/__init__.py**

```python
# addons/customer_operations_dashboard/models/__init__.py
from . import res_partner
from . import customer_operations_report
```

- [ ] **Step 6: Write the security access file**

```csv
# addons/customer_operations_dashboard/security/ir.model.access.csv
id,name,model_id:id,group_id:id,perm_read,perm_write,perm_create,perm_unlink
access_customer_operations_report,customer.operations.report,model_customer_operations_report,base.group_user,1,0,0,0
```

- [ ] **Step 7: Register the security file in the manifest**

```python
# addons/customer_operations_dashboard/__manifest__.py, change the "data" line
    "data": [
        "security/ir.model.access.csv",
    ],
```

- [ ] **Step 8: Update tests/__init__.py**

```python
# addons/customer_operations_dashboard/tests/__init__.py
from . import test_res_partner_financials
from . import test_res_partner_operations
from . import test_customer_operations_report
```

- [ ] **Step 9: Run local syntax + XML checks on everything touched**

Run: `python -m py_compile addons/customer_operations_dashboard/models/customer_operations_report.py addons/customer_operations_dashboard/models/res_partner.py addons/customer_operations_dashboard/models/__init__.py addons/customer_operations_dashboard/tests/__init__.py addons/customer_operations_dashboard/tests/test_customer_operations_report.py addons/customer_operations_dashboard/__manifest__.py`
Expected: no output, exit code 0.

- [ ] **Step 10: Run the repo-level static-check suite**

Run: `pytest tests/test_customer_operations_dashboard_addon.py -v`
Expected: PASS.

- [ ] **Step 11: Commit**

```bash
git add addons/customer_operations_dashboard/models/customer_operations_report.py \
        addons/customer_operations_dashboard/models/res_partner.py \
        addons/customer_operations_dashboard/models/__init__.py \
        addons/customer_operations_dashboard/security/ir.model.access.csv \
        addons/customer_operations_dashboard/__manifest__.py \
        addons/customer_operations_dashboard/tests/__init__.py \
        addons/customer_operations_dashboard/tests/test_customer_operations_report.py
git commit -m "feat: add SQL-view reporting model customer.operations.report"
```

---

### Task 5: Partner Form View — Operations Tab

**Files:**
- Create: `addons/customer_operations_dashboard/views/res_partner_views.xml`
- Modify: `addons/customer_operations_dashboard/__manifest__.py`

**Interfaces:**
- Consumes: all fields from Tasks 2–4 (`revenue_month/total`, `labor_cost_month/total`, `margin_month/total`, `margin_pct_month/total`, `hours_month/total`, `open_tickets_count`, `sla_percent_month/total`, `period_scope`, `operations_report_ids`).
- Produces: the "Operations" tab on `base.view_partner_form`, the deliverable end-users interact with.

- [ ] **Step 1: Write the view XML**

```xml
<!-- addons/customer_operations_dashboard/views/res_partner_views.xml -->
<odoo>
    <record id="view_partner_form_operations" model="ir.ui.view">
        <field name="name">res.partner.form.operations</field>
        <field name="model">res.partner</field>
        <field name="inherit_id" ref="base.view_partner_form"/>
        <field name="arch" type="xml">
            <notebook position="inside">
                <page string="Operations" name="operations"
                      invisible="revenue_total == 0 and hours_total == 0 and open_tickets_count == 0">
                    <field name="period_scope" widget="radio" options="{'horizontal': true}"/>
                    <group>
                        <group string="Financial" invisible="period_scope != 'month'">
                            <field name="revenue_month" readonly="1"/>
                            <field name="margin_month" readonly="1"/>
                            <field name="margin_pct_month" readonly="1"/>
                            <field name="labor_cost_month" readonly="1"/>
                        </group>
                        <group string="Financial" invisible="period_scope != 'all_time'">
                            <field name="revenue_total" readonly="1"/>
                            <field name="margin_total" readonly="1"/>
                            <field name="margin_pct_total" readonly="1"/>
                            <field name="labor_cost_total" readonly="1"/>
                        </group>
                        <group string="Operations" invisible="period_scope != 'month'">
                            <field name="hours_month" readonly="1"/>
                            <field name="open_tickets_count" readonly="1"/>
                            <field name="sla_percent_month" readonly="1"/>
                        </group>
                        <group string="Operations" invisible="period_scope != 'all_time'">
                            <field name="hours_total" readonly="1"/>
                            <field name="open_tickets_count" readonly="1"/>
                            <field name="sla_percent_total" readonly="1"/>
                        </group>
                    </group>
                    <field name="operations_report_ids" nolabel="1">
                        <graph type="line" string="Trend">
                            <field name="date" interval="month"/>
                            <field name="revenue" type="measure"/>
                            <field name="margin" type="measure"/>
                            <field name="hours" type="measure"/>
                            <field name="tickets_created" type="measure"/>
                            <field name="sla_percent" type="measure"/>
                        </graph>
                    </field>
                </page>
            </notebook>
        </field>
    </record>
</odoo>
```

- [ ] **Step 2: Register the view in the manifest**

```python
# addons/customer_operations_dashboard/__manifest__.py, change the "data" list
    "data": [
        "security/ir.model.access.csv",
        "views/res_partner_views.xml",
    ],
```

- [ ] **Step 3: Run XML well-formedness check**

Run: `python -c "import xml.dom.minidom; xml.dom.minidom.parse('addons/customer_operations_dashboard/views/res_partner_views.xml')"`
Expected: no output, exit code 0.

- [ ] **Step 4: Run the repo-level static-check suite**

Run: `pytest tests/test_customer_operations_dashboard_addon.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add addons/customer_operations_dashboard/views/res_partner_views.xml \
        addons/customer_operations_dashboard/__manifest__.py
git commit -m "feat: add Operations tab to partner form"
```

---

### Task 6: Post-Deploy Verification Script

**Files:**
- Create: `seed/verify_customer_operations_dashboard.py`
- Create: `tests/test_verify_customer_operations_dashboard.py`

**Interfaces:**
- Consumes: `seed.connection.OdooClient` (existing — constructor `OdooClient(url, db, username, password)`, methods `search_read(model, domain, fields, limit=100)`, `create`, `unlink`, `execute`).
- Produces: a standalone script runnable against the dev instance after deploy, printing a known partner's computed Operations fields for manual/automated sanity-check. This is the real functional verification given no local Odoo (see Global Constraints).

- [ ] **Step 1: Write the failing unit test (mocks XML-RPC, same pattern as tests/test_connection.py)**

```python
# tests/test_verify_customer_operations_dashboard.py
from unittest.mock import MagicMock, patch


def test_fetch_operations_fields_calls_search_read_with_expected_fields():
    with patch("xmlrpc.client.ServerProxy") as mock_proxy:
        mock_common = MagicMock()
        mock_common.authenticate.return_value = 7
        mock_models = MagicMock()
        mock_models.execute_kw.return_value = [{
            "id": 42, "name": "ACME Kft",
            "revenue_month": 500000, "margin_month": 280000,
            "hours_month": 15, "open_tickets_count": 2, "sla_percent_month": 99.0,
        }]
        mock_proxy.side_effect = [mock_common, mock_models]

        from seed.verify_customer_operations_dashboard import fetch_operations_fields
        result = fetch_operations_fields(
            "http://localhost:8069", "testdb", "admin", "pass", partner_id=42,
        )

        assert result["name"] == "ACME Kft"
        assert result["revenue_month"] == 500000
        mock_models.execute_kw.assert_called_once_with(
            "testdb", 7, "pass", "res.partner", "search_read",
            [[("id", "=", 42)]],
            {
                "fields": [
                    "name", "revenue_month", "revenue_total",
                    "margin_month", "margin_total",
                    "margin_pct_month", "margin_pct_total",
                    "hours_month", "hours_total",
                    "open_tickets_count", "sla_percent_month", "sla_percent_total",
                ],
                "limit": 1,
            },
        )
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_verify_customer_operations_dashboard.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'seed.verify_customer_operations_dashboard'`

- [ ] **Step 3: Write the implementation**

```python
# seed/verify_customer_operations_dashboard.py
from seed.connection import OdooClient

OPERATIONS_FIELDS = [
    "name",
    "revenue_month", "revenue_total",
    "margin_month", "margin_total",
    "margin_pct_month", "margin_pct_total",
    "hours_month", "hours_total",
    "open_tickets_count", "sla_percent_month", "sla_percent_total",
]


def fetch_operations_fields(url, db, username, password, partner_id):
    client = OdooClient(url, db, username, password)
    results = client.search_read(
        "res.partner", [("id", "=", partner_id)], OPERATIONS_FIELDS, limit=1
    )
    if not results:
        raise ValueError(f"No partner found with id={partner_id}")
    return results[0]


if __name__ == "__main__":
    import argparse
    import os

    parser = argparse.ArgumentParser(
        description="Print Customer Operations Dashboard fields for a partner on a live instance."
    )
    parser.add_argument("partner_id", type=int)
    args = parser.parse_args()

    result = fetch_operations_fields(
        os.environ["ODOO_ERP_URL"],
        os.environ["ODOO_DB"],
        os.environ["ODOO_LOGIN_USERNAME"],
        os.environ["ODOO_LOGIN_PASSWORD"],
        args.partner_id,
    )
    for key, value in result.items():
        print(f"{key}: {value}")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_verify_customer_operations_dashboard.py -v`
Expected: PASS (1 passed)

- [ ] **Step 5: Commit**

```bash
git add seed/verify_customer_operations_dashboard.py tests/test_verify_customer_operations_dashboard.py
git commit -m "feat: add post-deploy verification script for operations dashboard fields"
```

---

### Task 7: Final Static-Check Pass, Manifest Review, and Deployment Handoff

**Files:**
- No new files — verification and handoff only.

**Interfaces:**
- Consumes: everything from Tasks 1–6.
- Produces: a addon ready to commit/push for ops' redeploy pipeline to pick up, plus the exact post-deploy verification steps to run.

- [ ] **Step 1: Run the full repo test suite**

Run: `pytest -v`
Expected: all tests PASS, including every test added in Tasks 1–6 and every pre-existing test in `tests/`.

- [ ] **Step 2: Manually review the final manifest**

Read `addons/customer_operations_dashboard/__manifest__.py` and confirm `data` lists exactly `security/ir.model.access.csv` then `views/res_partner_views.xml`, and `depends` lists exactly `contacts`, `sale`, `account`, `hr_timesheet`, `hr_employee_cost_history`, `helpdesk_mgmt`, `helpdesk_mgmt_sla`.

- [ ] **Step 3: Confirm no stray files**

Run: `git status`
Expected: working tree clean (everything from Tasks 1–6 already committed) — only untracked files, if any, should be things you intentionally haven't added yet.

- [ ] **Step 4: Push and hand off to ops for redeploy**

```bash
git push
```

Notify ops (per the confirmed deployment flow: "git commit to adaminfo-odoo-v1 repo and ops will trigger environment-based Odoo instance redeploy process") that `customer_operations_dashboard` is ready to install on the dev instance.

- [ ] **Step 5: Post-deploy functional verification (manual, once ops confirms the dev instance has the module installed)**

Find or create a test partner with at least one posted invoice, one timesheet entry, and one helpdesk ticket on the dev instance (e.g. via the existing `seed/` scripts or the Odoo UI), note its partner `id`, then run:

```bash
python -m seed.verify_customer_operations_dashboard <partner_id>
```

Expected: prints `revenue_month`, `margin_month`, `hours_month`, `open_tickets_count`, `sla_percent_month`, etc. with non-error, plausible values matching what you seeded. Also open that partner's form in the Odoo UI and confirm the "Operations" tab renders with the same figures and the trend graph shows the current month.
