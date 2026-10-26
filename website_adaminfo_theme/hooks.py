import base64

from odoo.tools.misc import file_open

LINKEDIN_URL = "https://www.linkedin.com/in/adaminformatika"
META_DESCRIPTION = (
    "Adam Informatika — freelance IT PM, DevOps engineer and Python/Odoo "
    "developer. Build, automate, deploy, scale."
)


def apply_site_defaults(env):
    """One-time site content defaults, written the same way the Website
    Builder would (website-specific COW views), so they stay editable there.

    Runs on install and from the 18.0.1.1.0 migration — not on every update,
    so later Builder choices (e.g. switching footer template) aren't reverted.
    theme.utils' _post_copy hook never fires here: it only runs for theme_*
    modules applied through the theme picker.
    """
    website = env.ref("website.default_website")
    with file_open("website_adaminfo_theme/static/src/img/adaminformatika_logo.png", "rb") as f:
        logo = base64.b64encode(f.read())
    website.write({
        "name": "Adam Informatika",
        "social_linkedin": LINKEDIN_URL,
        "logo": logo,
    })
    env["theme.utils"].with_context(website_id=website.id).enable_view(
        "website.template_footer_minimalist"
    )
    env["website.page"].search([
        ("url", "=", "/"),
        ("website_id", "in", [False, website.id]),
    ]).write({"website_meta_description": META_DESCRIPTION})


def post_init_hook(env):
    apply_site_defaults(env)
