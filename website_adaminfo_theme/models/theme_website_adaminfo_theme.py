from odoo import models


class ThemeWebsiteAdaminfoTheme(models.AbstractModel):
    _inherit = "theme.utils"

    def _theme_website_adaminfo_theme_post_copy(self, mod):
        # No logo asset yet — keep the default text brand name, don't force option_header_brand_logo.
        self.enable_view("website.template_header_default")
        self.enable_view("website.template_footer_minimalist")
