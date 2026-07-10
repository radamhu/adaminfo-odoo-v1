from datetime import date

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
