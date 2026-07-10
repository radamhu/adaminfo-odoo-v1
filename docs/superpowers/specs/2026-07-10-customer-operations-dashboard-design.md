# Customer Operations Dashboard — Design Spec

## Context

`README.md` lays out a set of MSP-oriented Odoo extension ideas (AWS Cost Import, Project Profitability, Cloud Resource Inventory, Kubernetes Inventory, MSP Dashboard) and argues that the two dashboard concepts — "Profitability Dashboard" (financial) and "Managed Service Dashboard" (operational) — should merge into a single **Customer Operations Dashboard**, surfaced as an "Operations" tab on the Contact/Partner form rather than a standalone top-level module (README Option 1).

This repo currently contains only XML-RPC seeder tooling (`seed/`) against an external Odoo instance — no addon source exists yet. This is the first real Odoo module built in this repo.

## Scope (v1)

Odoo-native metrics only. The infra-facing metrics from README's full vision (AWS Cost, Cluster Health, Certificate/Domain expiry) depend on Cloud/Kubernetes Inventory modules that don't exist yet (per README's own priority ordering, those come later). v1 covers:

- Revenue
- Margin / Margin %
- Hours Used
- Open Tickets
- SLA %
- Monthly historical snapshots of the above, with a trend graph

AWS Cost, Cluster Health, Certificates, and Domains are explicitly **out of scope** for this spec and will be added once their source modules exist.

## Module

- Path: `addons/customer_operations_dashboard/`
- Target: Odoo 18
- Depends: `contacts`, `sale`, `account`, `hr_timesheet`, `hr_employee_cost_history` (OCA timesheet repo), `helpdesk_mgmt` (OCA), `helpdesk_mgmt_sla` (OCA)
- New model: `customer.operations.report` (`_auto=False`, PostgreSQL-view-backed, monthly aggregation for trend graph — see below). All current-value fields remain compute fields on `res.partner` via inheritance.
- No local Odoo installation exists in this repo; dev/prod are remote cloud instances reachable only via XML-RPC (see `.env.dev`/`.env.prod`, `seed/connection.py`). Deployment = commit to this repo; ops triggers an environment-based redeploy that installs/upgrades the addon on the target instance. There is no local `odoo-bin --test-enable` run available — correctness is checked via static validation (syntax/XML well-formedness) locally, and functional verification happens against the dev instance after deploy (via the existing `OdooClient` XML-RPC wrapper in `seed/connection.py`, or manual UI check).

## Fields & Formulas

All fields below are added to `res.partner`, non-stored (`compute=`, no `store=True`) so values are always live/current — appropriate for a "look up the customer while they're on the phone" use case, not a reporting/history use case.

| Field | Formula | Source |
|---|---|---|
| `x_revenue_month` / `x_revenue_total` | Sum of posted customer invoice totals (`account.move`, `move_type='out_invoice'`, `state='posted'`, `partner_id=self`), scoped to current calendar month or all-time | `account.move` |
| `x_labor_cost_month` / `x_labor_cost_total` | Σ (timesheet hours × employee hourly cost rate in effect at the time of the entry) for `account.analytic.line` records linked to this partner's projects/tasks | `hr_timesheet` + `hr_employee_cost_history` |
| `x_margin_month` / `x_margin_total` | `revenue − labor_cost` | derived |
| `x_margin_pct` | `margin / revenue`, guarded to `0` when revenue is `0` | derived |
| `x_hours_month` / `x_hours_total` | Σ timesheet hours logged against the partner's projects/tasks | `hr_timesheet` |
| `x_open_tickets_count` | Count of `helpdesk.ticket` where `partner_id=self` and stage is not a "closed"-marked stage | `helpdesk_mgmt` |
| `x_sla_percent` | SLA compliance percentage for the partner's tickets, delegated to `helpdesk_mgmt_sla`'s own compliance computation | `helpdesk_mgmt_sla` |

**Partner → project/task linkage**: a project or task counts toward a partner if `project.project.partner_id == partner` or the task's own `partner_id == partner` (covers both project-per-customer and shared-project-with-per-task-customer setups).

**Edge cases**:
- Partner with no invoices/timesheets/tickets → all fields resolve to `0`, not an error.
- Division by zero in `x_margin_pct` → returns `0`.
- Individual contacts (non-company) with direct invoices/tickets are computed the same way as companies — no `is_company` restriction on the computation itself (only on tab visibility, see below).

## Historical Trend: SQL-View Reporting Model

Follows Odoo's standard reporting-model pattern (same technique as core `sale.report` / `account.invoice.report`): a model with `_auto=False` backed by a PostgreSQL `VIEW` defined in `init()`, instead of a stored/cron-populated table. Postgres computes the aggregation on every query, so the current in-progress month is always present and always fresh — no cron, no snapshot staleness, no "finalize last month" logic.

**Model**: `customer.operations.report` (`_auto=False`)
- Fields (one row per `partner_id` × calendar month): `partner_id`, `date` (first-of-month, the groupby key), `revenue`, `labor_cost`, `margin`, `margin_pct`, `hours`, `open_tickets`, `sla_percent`. All fields `readonly=True` (standard for `_auto=False` models).
- `init()` builds the view via `tools.drop_view_if_exists` + `CREATE VIEW ... AS SELECT`, joining/aggregating `account_move` (+ lines), `account_analytic_line` (timesheets, joined to `hr_employee_cost_history` for the rate), and `helpdesk_ticket` (+ `helpdesk_mgmt_sla` compliance data), grouped by `partner_id` and `date_trunc('month', ...)`.
- Retention: the view itself filters to `WHERE date >= (now() - interval '24 months')` — "retention" is just a `WHERE` clause, not a cleanup job.

**Graph placement**: embedded in the "Operations" tab on the partner form as an inline `<graph>` (and/or `<pivot>`) view on `customer.operations.report`, domain-filtered to the current partner, grouped by month. Since the view is computed live, the graph's last bar/point is always "this month so far" — no separate live-value injection needed. No separate menu item or standalone reporting action — stays inside the partner-centric surface per README's Option 1 rationale.

## View

- Inherit `view_partner_form` (from `contacts`/`base`).
- Add a new `<page string="Operations">` positioned after the existing standard tabs.
- Tab visibility: hidden by default, shown only when the partner has at least one related invoice, ticket, or project (avoids clutter on contacts with no commercial activity). Implemented via a domain/`invisible` check against existing related fields — no new visibility-tracking field needed.
- Layout inside the page:
  - **Financial group**: Revenue, Margin, Margin %, Labor Cost (secondary/muted display)
  - **Operations group**: Hours Used, Open Tickets, SLA %
  - A "This Month" / "All-Time" toggle (backed by a transient, non-stored `x_period_scope` selection field, default `month`) switches which of the paired fields are visible — implemented with `invisible` attrs, no page reload.
  - Below the stat groups: the trend graph described above.
- All fields in this tab are read-only (`readonly="1"`) — this is a reporting surface, not a data-entry form.
- No new menu items, no new top-level module surface — matches README's Option 1 reasoning explicitly.

## Testing

**Constraint**: no local Odoo installation is available in this repo/environment (confirmed — dev/prod are remote cloud instances, reachable only via XML-RPC per `.env.dev`/`.env.prod`). Standard Odoo `TransactionCase` tests (the idiomatic way to test `_auto=False` view models and compute fields) are written as part of the module, live under `addons/customer_operations_dashboard/tests/`, and are the correct long-term test suite — but they run under Odoo's own test runner (`-i customer_operations_dashboard --test-enable`), which requires an actual Odoo server. This repo cannot execute that locally.

Two-tier verification, both real, both used:
1. **Local static checks** (run in this repo, no Odoo needed): `python -m py_compile` on every `.py` file, and `xmllint --noout` on every `.xml` file. Catches syntax errors and malformed XML before anything is committed.
2. **Post-deploy functional verification** (after commit triggers ops redeploy to the dev instance): a verification script using the existing `seed/connection.py` `OdooClient` XML-RPC wrapper reads back computed field values (and, once the view exists, `customer.operations.report` rows) for a known seeded partner and asserts expected numbers. This is the actual pass/fail signal for correctness, since it exercises the real installed module against real data.

The `TransactionCase` test files are still written (correct practice, will run whenever the module is installed/upgraded with `--test-enable` on any Odoo instance, including future CI if ops adds it) — they are just not exercised by this repo's own tooling today.

Cases to cover (as `TransactionCase` tests in the module, and mirrored by the XML-RPC verification script's assertions where practical):
1. Partner with zero invoices/timesheets/tickets → all computed fields are `0`.
2. Partner with invoices in the current month vs. a prior month → month vs. all-time totals split correctly.
3. Margin % divide-by-zero guard when revenue is `0`.
4. Partner linked via multiple projects → hours and labor cost aggregate across all of them.
5. Open ticket count excludes tickets in a closed-marked stage.
6. SLA % reflects `helpdesk_mgmt_sla`'s compliance computation for the partner's tickets (not reimplemented locally).
7. `customer.operations.report` has exactly one row per partner per month with activity, aggregating revenue/labor_cost/hours/tickets correctly for that month.
8. The current (in-progress) month appears in `customer.operations.report` with partial-month figures (proves the view is live, not cron-populated).
9. Rows older than 24 months are excluded from `customer.operations.report`.

## Out of Scope (v1)

- AWS Cost, Cluster Health, Certificate/Domain expiry (blocked on Cloud/Kubernetes Inventory modules not yet built).
- Any new top-level "Operations" menu or standalone reporting view (deferred per README until customer count/operator count justifies it — see README Option 2). The trend graph is surfaced only embedded in the partner form's Operations tab.
- Any cron jobs — the SQL-view architecture makes them unnecessary for this feature.
