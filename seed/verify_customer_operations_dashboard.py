from dotenv import load_dotenv

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

    load_dotenv()

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
