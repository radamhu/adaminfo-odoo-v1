from odoo import SUPERUSER_ID, api

from odoo.addons.website_adaminfo_theme.hooks import apply_site_defaults


def migrate(cr, version):
    apply_site_defaults(api.Environment(cr, SUPERUSER_ID, {}))
