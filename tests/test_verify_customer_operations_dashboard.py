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
