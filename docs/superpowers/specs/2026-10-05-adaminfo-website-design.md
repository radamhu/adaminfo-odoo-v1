# adaminformatika.hu — Odoo Website Rebuild

## Context

The live site at https://www.adaminformatika.hu/ is a static one-page personal
portfolio built on an HTML5-UP template: a hero line ("IT PM • Devops •
Coding"), social links (LinkedIn, GitHub, Twitter→LinkedIn), and an
obfuscated email contact. No CMS, no form, no content management.

This project rebuilds that site as a page inside this repo's Odoo 18
instance, using the Website module, so it's editable through Odoo's
Website Builder going forward and lives alongside the other work already
tracked here (the `customer_operations_dashboard` addon, the oec.sh
migration tooling).

## Goal

A personal portfolio site — not a business/lead-gen site. Same spirit as
the current site (individual brand, not a company), rebuilt with a fresh
visual design and real content instead of a template default, running on
Odoo Website.

## Scope

**In scope:**
- One scrollable page: Hero → About/Skills → Projects → Contact
- Fresh brand pass (palette, type, layout) — not a copy of the old
  HTML5-UP look
- English only
- Custom Odoo theme addon (`website_adaminfo_theme`) with editable
  Website Builder snippets
- Odoo's built-in Website contact form (submissions into Odoo)
- Deploy to this repo's existing oec.sh environment and verify live
- DNS cutover for adaminformatika.hu once the env is verified

**Out of scope:**
- Blog, multi-page nav, e-commerce
- Multi-language (HU/EN) — single language for now, revisit later if needed
- New business/consulting content — this is a personal site, not a
  services site

## Content & Information Architecture

One page, anchor-nav between four sections:

1. **Hero** — name, refreshed tagline (successor to "IT PM • DevOps •
   Coding"), CTA scrolling to Contact.
2. **About / Skills** — short bio, skill-category tags/badges.
3. **Projects** — cards sourced from this repo's actual work:
   - Customer Operations Dashboard (Odoo addon: per-customer financial &
     operational metrics)
   - Odoo migration tooling (`migration/`: oec.sh API client, preflight,
     cutover-check, lifecycle, log-watch CLIs)
   Each card: short description + link to the relevant GitHub repo.
4. **Contact** — Odoo Website contact form, plus LinkedIn/GitHub links.

Sticky header with anchor links to each section (Odoo's built-in
anchor-nav pattern).

## Visual Design Phase (Figma) — blocked on external setup

This phase is **not runnable in the current session** and is a hard
prerequisite before the addon's SCSS/snippets are built. The user owns
setting this up; resume the plan here once done.

**Prerequisites (user-side, outside this session):**
1. A Figma account, with the
   [Odoo Website v18 Wireframes](https://www.figma.com/community/file/1531671606285288070/odoo-website-v18-wireframes-figma-community)
   community file duplicated into the user's own Figma.
2. Claude in Chrome extension connected and active (this repo's Claude
   Code session already has the `chrome-browser` skill available — it
   just needs the extension running and a reachable Figma tab). The
   `figma-to-odoo-theme-designer` skill uses Chrome MCP for real-time
   browser-based design reading, not a dedicated Figma API integration.
3. The `figma-to-odoo-theme-designer` skill
   (mcpmarket.com/tools/skills/figma-to-odoo-theme-designer) downloaded
   and installed under `~/.claude/skills/` so it's invocable by name in
   a future session.

**Once set up, the phase does:**
- Pick/duplicate the wireframe(s) matching a one-pager
  hero/about/projects/contact layout from the community file.
- Apply the fresh brand pass (palette, type) — explicitly not the old
  HTML5-UP look.
- Run the `figma-to-odoo-theme-designer` skill to extract colors,
  typography, and layout, and map them onto Odoo's snippet/template
  structure (the skill ships a reference library of headers/footers/
  layouts for exactly this mapping).
- Output: a Figma file link/export plus extracted design tokens, handed
  to the addon-build phase below.

## Odoo Addon Architecture

New addon, `website_adaminfo_theme`, depending on `website`:

```
website_adaminfo_theme/
├── __manifest__.py          depends: website
├── static/src/scss/         brand vars + section styles (from Figma tokens)
├── static/src/img/          exported assets from Figma
├── views/
│   ├── snippets/            hero, skills, project-card, contact section templates
│   └── layout.xml           page assembly / anchor nav
└── data/
    └── website_page_data.xml  pre-populates the one page with the sections above
```

Snippets are built as draggable Website Builder blocks (not locked-down
templates), so future content edits can happen in the Odoo UI without
touching code — consistent with how Odoo theme addons are normally built.

## Deploy & Verify

Reuses the `odoo-oecsh-ticket-deploy` skill's existing runbook — no new
deploy mechanism.

- **Target env:** `adaminfo-prod-1139`, resolved by **ID**
  `c0672b12-b1b6-43c9-8414-7917246d0136`, **not by name**. The old
  environment shares the exact same `name` field
  (`docs/migration-log-2026-09-04-adaminfo-prod-1139.md` — "HAZARD:
  Environment name collision"), so `find_environment('adaminfo-prod-1139')`
  is non-deterministic until the old env is deleted or renamed. Use
  `find_environment_by_id()` or match on URL instead.
- Push branch → redeploy via oec.sh API → poll until done.
- Activate dev mode, install `website_adaminfo_theme` via Apps (search
  technical name first, don't click Upgrade off an unfiltered Apps list).
- Playwright: full-page screenshot, verify each of the four sections
  renders, submit the contact form and confirm it lands in Odoo.
- Once verified, point adaminformatika.hu's DNS at the environment.

## Testing

- No automated test suite is practical for a marketing/portfolio page's
  visual design — verification is the Playwright pass above (render +
  form submission), matching how this repo already verifies Odoo-side
  changes (see `tests/test_verify_customer_operations_dashboard.py` for
  the pattern used elsewhere in this repo, adapted for an addon with no
  backend logic to unit-test).

## Open Items / Risks

- Figma + Chrome MCP + the mcpmarket skill are **not available in the
  current session** — Phase 2 (Visual Design) cannot start until the
  user sets these up, as detailed above.
- DNS cutover timing/registrar access not yet confirmed — flagged as
  in-scope but final step depends on user's domain registrar access.
