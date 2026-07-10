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

AWS Cost, Cluster Health, Certificates, and Domains are explicitly **out of scope** for this spec and will be added once their source modules exist.

## Module

- Path: `addons/customer_operations_dashboard/`
- Target: Odoo 18
- Depends: `contacts`, `sale`, `account`, `hr_timesheet`, `hr_employee_cost_history` (OCA timesheet repo), `helpdesk_mgmt` (OCA), `helpdesk_mgmt_sla` (OCA)
- No new persistent models. All new fields are compute fields added to `res.partner` via inheritance.

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

## View

- Inherit `view_partner_form` (from `contacts`/`base`).
- Add a new `<page string="Operations">` positioned after the existing standard tabs.
- Tab visibility: hidden by default, shown only when the partner has at least one related invoice, ticket, or project (avoids clutter on contacts with no commercial activity). Implemented via a domain/`invisible` check against existing related fields — no new visibility-tracking field needed.
- Layout inside the page:
  - **Financial group**: Revenue, Margin, Margin %, Labor Cost (secondary/muted display)
  - **Operations group**: Hours Used, Open Tickets, SLA %
  - A "This Month" / "All-Time" toggle (backed by a transient, non-stored `x_period_scope` selection field, default `month`) switches which of the paired fields are visible — implemented with `invisible` attrs, no page reload.
- All fields in this tab are read-only (`readonly="1"`) — this is a reporting surface, not a data-entry form.
- No new menu items, no new top-level module surface — matches README's Option 1 reasoning explicitly.

## Testing

Standard Odoo `TransactionCase` tests (not the live XML-RPC seeder in `seed/` — that tooling targets a real running instance; tests here use `Model.create`/`env.ref` fixtures created directly in the test transaction).

Cases to cover:
1. Partner with zero invoices/timesheets/tickets → all computed fields are `0`.
2. Partner with invoices in the current month vs. a prior month → month vs. all-time totals split correctly.
3. Margin % divide-by-zero guard when revenue is `0`.
4. Partner linked via multiple projects → hours and labor cost aggregate across all of them.
5. Open ticket count excludes tickets in a closed-marked stage.
6. SLA % reflects `helpdesk_mgmt_sla`'s compliance computation for the partner's tickets (not reimplemented locally).

## Out of Scope (v1)

- AWS Cost, Cluster Health, Certificate/Domain expiry (blocked on Cloud/Kubernetes Inventory modules not yet built).
- Stored/historical snapshots — all values are computed live, so there is no trend/graph view in v1.
- Any new top-level "Operations" menu (deferred per README until customer count/operator count justifies it — see README Option 2).
