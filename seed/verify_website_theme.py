"""Repeatable check that the Adam Informatika website theme rollout is in place."""
import re

from seed.connection import OdooClient

THEME_MODULE = "website_adaminfo_theme"
THEME_VERSION = "18.0.1.1.0"
WEBSITE_NAME = "Adam Informatika"
LINKEDIN_URL = "https://www.linkedin.com/in/adaminformatika"
CONTACT_VIEW_KEY = "website_adaminfo_theme.section_contact"
ALL_VIEWS = {"active_test": False}

KEYS = [
    "theme_installed",
    "website_named",
    "linkedin_set",
    "footer_minimalist",
    "footer_override",
    "form_recipient_set",
]

_INPUT_TAG = re.compile(r"<input\b[^>]*>", re.I | re.S)
_EMAIL_TO = re.compile(r"""\bname\s*=\s*["']email_to["']""", re.I)
_NONEMPTY_VALUE = re.compile(r"""\bvalue\s*=\s*(?:"[^"]+"|'[^']+')""", re.I)


def _website_view_active(client: OdooClient, key: str) -> bool:
    rows = client.search_read(
        "ir.ui.view",
        [("key", "=", key), ("website_id", "=", 1), ("active", "=", True)],
        ["id"], limit=1, context=ALL_VIEWS,
    )
    return bool(rows)


def _form_recipient_set(client: OdooClient) -> bool:
    rows = client.search_read(
        "ir.ui.view", [("key", "=", CONTACT_VIEW_KEY)],
        ["website_id", "arch_db"], limit=10, context=ALL_VIEWS,
    )
    if not rows:
        return False

    def website_id(row):
        w = row.get("website_id")
        return w[0] if isinstance(w, (list, tuple)) else w

    view = next((r for r in rows if website_id(r) == 1), None) or next(
        (r for r in rows if not website_id(r)), rows[0]
    )
    arch = view.get("arch_db") or ""
    if "contactus_form" not in arch:
        return False
    return any(
        _EMAIL_TO.search(tag) and _NONEMPTY_VALUE.search(tag)
        for tag in _INPUT_TAG.findall(arch)
    )


def check_theme_rollout(client: OdooClient) -> dict[str, bool]:
    modules = client.search_read(
        "ir.module.module", [("name", "=", THEME_MODULE)],
        ["state", "installed_version"], limit=1,
    )
    websites = client.search_read(
        "website", [("id", "=", 1)], ["name", "social_linkedin"], limit=1,
        context=ALL_VIEWS,
    )
    module = modules[0] if modules else {}
    website = websites[0] if websites else {}
    return {
        "theme_installed": module.get("state") == "installed"
        and module.get("installed_version") == THEME_VERSION,
        "website_named": website.get("name") == WEBSITE_NAME,
        "linkedin_set": website.get("social_linkedin") == LINKEDIN_URL,
        "footer_minimalist": _website_view_active(client, "website.template_footer_minimalist"),
        "footer_override": _website_view_active(
            client, "website_adaminfo_theme.footer_minimalist_content"
        ),
        "form_recipient_set": _form_recipient_set(client),
    }


def main(argv=None) -> int:
    import argparse
    import os

    from dotenv import load_dotenv

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--env", required=True, help="path to env file with credentials")
    parser.add_argument("--db", required=True, help="Odoo database name (overrides ODOO_DB)")
    args = parser.parse_args(argv)

    load_dotenv(args.env, override=True)
    client = OdooClient(
        os.environ["ODOO_ERP_URL"], args.db,
        os.environ["ODOO_LOGIN_USERNAME"], os.environ["ODOO_LOGIN_PASSWORD"],
    )
    results = check_theme_rollout(client)
    for key in KEYS:
        print(f"{'PASS' if results[key] else 'FAIL'} {key}")
    return 0 if all(results.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
