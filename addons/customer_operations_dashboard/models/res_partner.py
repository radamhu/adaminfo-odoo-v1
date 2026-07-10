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
        if month_start.month == 12:
            next_month_start = month_start.replace(year=month_start.year + 1, month=1)
        else:
            next_month_start = month_start.replace(month=month_start.month + 1)
        for partner in self:
            invoice_domain = [
                ("partner_id", "=", partner.id),
                ("move_type", "=", "out_invoice"),
                ("state", "=", "posted"),
            ]
            all_invoices = move_model.search(invoice_domain)
            month_invoices = all_invoices.filtered(
                lambda m: m.invoice_date and m.invoice_date >= month_start and m.invoice_date < next_month_start
            )
            revenue_total = sum(all_invoices.mapped("amount_total"))
            revenue_month = sum(month_invoices.mapped("amount_total"))

            all_lines = analytic_model.search(self._operations_timesheet_domain(partner))
            month_lines = all_lines.filtered(
                lambda l: l.date and l.date >= month_start and l.date < next_month_start
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
