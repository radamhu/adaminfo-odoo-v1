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
