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
