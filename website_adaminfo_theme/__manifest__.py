{
    "name": "Website Adaminfo Theme",
    "version": "18.0.1.1.0",
    "summary": "Personal portfolio theme for adaminformatika.hu",
    "category": "Theme/Creative",
    "author": "Adaminfo",
    "license": "LGPL-3",
    "depends": ["website"],
    "data": [
        "data/menu.xml",
        "data/website_logo.xml",
        "views/snippets/sections.xml",
        "views/footer.xml",
        "data/website_page_data.xml",
    ],
    "assets": {
        "web._assets_primary_variables": [
            ("prepend", "website_adaminfo_theme/static/src/scss/primary_variables.scss"),
            "website_adaminfo_theme/static/src/scss/colors.scss",
        ],
        "web.assets_frontend": [
            "website_adaminfo_theme/static/src/scss/theme.scss",
        ],
    },
    "post_init_hook": "post_init_hook",
    "installable": True,
    "auto_install": False,
    "application": False,
}
