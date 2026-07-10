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
