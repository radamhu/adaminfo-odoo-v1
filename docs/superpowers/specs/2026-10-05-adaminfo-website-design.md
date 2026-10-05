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

## Visual Design Phase (Figma) — tooling ready

Setup done:
1. **Figma remote MCP server** installed via
   `claude mcp add --scope user --transport http figma https://mcp.figma.com/mcp`
   (user scope, global — available in any session). OAuth completed and
   verified connected (checked 2026-10-05, `claude mcp list` → `figma:
   ✔ Connected`).
2. **`odoo-frontend` plugin** (cloud-market marketplace,
   `ahmed-lakosha/odoo-plugins`) installed user-scope via
   `claude plugin marketplace add ahmed-lakosha/odoo-plugins` +
   `claude plugin install odoo-frontend@cloud-market`. This is the real
   identity behind the mcpmarket.com "figma-to-odoo-theme-designer"
   listing — it ships a `theme-design` skill (Figma extraction pipeline,
   color→`o-color-N` mapping, header/footer template decision
   flowcharts) alongside `theme-create`/`theme-scss`/`theme-snippets`.

**User-side, confirmed done (2026-10-05):** Figma account verified
(handle `Adam`, team "Adam's team", starter plan) and the
[Odoo Website v18 Wireframes](https://www.figma.com/design/UBokxzL9ECAS35LPY7kUJX/Odoo-Website-v18---Wireframes---Figma-Community--Community-)
community file is already editable in the user's own space (has a
`Drafts` link, full edit toolbar — no further duplication needed). Full
page list: `COVER`; `FOUNDATIONS` (Colors, Typography, Media,
in-file-components); `COMPONENTS` (Buttons, Controls, Breadcrumbs,
Accordions, Carousel indicators, Inputs, Progress Bar, Pagination,
Calendar); `ODOO BLOCKS` (Header & Footer, Categories Blocks, Inner
content); `DEFAULT PAGES` (Contact & 404, Shop, Blog, Events, Job,
Appointment). Attached libraries are all Figma Community kits (Material
3, Simple Design System, Apple OS kits) — none need subscribing to, the
wireframe content itself is native frames.

**Important clarification (2026-10-05, raised by ops):** this file is
Odoo's generic, off-the-shelf wireframe **component kit** (header/footer
variants, buttons, sample page types like Shop/Blog/Events) — nobody has
designed an actual adaminformatika.hu mockup. "Pick a header/footer
variant + hand-write content in code" (the original plan below) was a
code-first shortcut. **Decision: go design-first instead** — see
"Mockup Phase" below, inserted before the addon build.

**Browser access note:** for any browser-driven step in this phase
(reading Figma pages, later Playwright verification), use the
`browser-skill` skill, **not** the built-in browser or Claude in Chrome —
despite the mcpmarket listing's Chrome MCP description, this repo's
convention is `browser-skill` for all browser automation.

### Tooling — when to use what

Two layers, don't conflate them: the **figma MCP + skills** read/write
raw Figma (generic, no Odoo knowledge); the **`odoo-frontend` plugin**
turns extracted design into an installable Odoo theme module (Odoo
knowledge, no Figma access of its own). Flow is always figma-layer →
odoo-layer, never the reverse.

| Tool | Layer | Use for | Don't use for |
|---|---|---|---|
| `mcp__figma__whoami` | figma MCP | Verify account/plan/seat before anything else | Reading design content |
| `mcp__figma__get_metadata` | figma MCP | Cheap page/node tree overview (names, ids, bbox) before deciding what to pull in full | Implementing a design — it has no styles/content, only structure |
| `mcp__figma__get_design_context` | figma MCP | Pull full node detail (styles, text, layout) once a target page/frame is picked — required before implementing anything | First-pass exploration of an unfamiliar file (too heavy; use `get_metadata` first) |
| `mcp__figma__get_screenshot` | figma MCP | Visual reference/sanity check alongside `get_design_context` | Source of truth for exact values — always cross-check against design context |
| `mcp__figma__get_libraries` / `search_design_system` | figma MCP | Find which community/org component libraries a file uses and search their components/variables/styles | Odoo-side token mapping — that's `theme-design`'s job once values are extracted |
| `mcp__figma__use_figma` (needs `/figma-use` skill loaded first) | figma MCP | **Mockup Phase build step** — creates the actual adaminformatika.hu frames (Hero/About/Projects/Contact) in a new Figma page, reusing wireframe-kit header/footer symbols as a base | Reading/exploring — that's `get_metadata`/`get_design_context` |
| `odoo-frontend:figma-generate-design` skill (loads before `use_figma` alongside `/figma-use`) | figma MCP | Turns the brainstormed brand brief (palette/type/tone) into actual layout instructions for `use_figma` | Skipping straight to `use_figma` without a brief first — produces generic/default-looking output |
| `mcp__figma__generate_figma_design` | figma MCP | Capturing an existing *web page* into Figma (reverse direction) | Not used here — greenfield mockup, no existing page worth capturing (old HTML5-UP site is explicitly not the look we want) |
| **`browser-skill`** | browser automation | Any browser-driven step: checking file access/page list when MCP metadata lazy-loads incompletely (happened once this session), later Playwright verification of the deployed addon | Reading/extracting Figma design data — that's the figma MCP's job, browser-skill is for navigation/screenshots/form-submit only |
| `odoo-frontend:theme-design` skill | odoo-frontend plugin | Once a wireframe page's design context is extracted: map colors→`o-color-1..5`, pick header/footer XML ID via its decision flowcharts, decide typography mapping | Reading Figma directly — it consumes already-extracted tokens, doesn't call the Figma MCP itself |
| `odoo-frontend:theme-create` / `create-theme` skill | odoo-frontend plugin | Scaffold the actual `website_adaminfo_theme` addon structure (manifest, SCSS, views, snippets) from the mapped tokens | Design extraction or brand decisions — those happen in `theme-design` first |
| `odoo-frontend:theme-scss` skill | odoo-frontend plugin | Reference lookup for exact SCSS variable names/load order while writing the addon's SCSS | Anything before the addon-build phase |

**Phase does (wireframe-kit reading, done 2026-10-05):**
- Pulled `Header & Footer` page from the kit, compared 4 header variants
  (default/Stretch/Vertical) + footer Minimalist — picked **Header
  default** + **Footer Minimalist** as the structural base (simplest,
  no ecommerce chrome; names match Odoo's own
  `template_header_default`/`template_footer_minimalist` XML IDs).
- These are base *structure* only — not a finished mockup. Real design
  (brand pass) happens in the Mockup Phase below.

### Mockup Phase — design-first (added 2026-10-05, supersedes code-first shortcut)

Before writing any more addon code, produce an actual
adaminformatika.hu mockup in Figma:

1. **Brainstorm brand direction first** (`superpowers:brainstorming`
   skill — mandatory before creative work, not skippable). Pins down
   palette, type, tone/vibe, logo/wordmark treatment. Needs user input
   — the agent can propose but not decide this alone.
2. **New Figma page** in the same file (e.g. "Adaminfo Site"), separate
   from the generic wireframe-kit pages — keeps the kit as reference,
   real design lives on its own.
3. **Agent builds via `mcp__figma__use_figma`** (loads `/figma-use` +
   `odoo-frontend:figma-generate-design` skills first): reuses the
   picked Header-default/Footer-minimalist symbols as a base, lays out
   Hero/About/Projects/Contact frames per the Content & Information
   Architecture section above, applies the brainstormed palette/type/copy.
4. **Review loop**: `mcp__figma__get_screenshot` after each pass → user
   feedback → agent adjusts. Repeat until approved — cheaper to iterate
   in Figma than in code.
5. **Hand-off to code**: once approved, re-run `get_design_context` —
   now against *our* frames, not the generic kit — then
   `odoo-frontend:theme-design` to extract real tokens
   (color→`o-color-1..5`, etc.) for the addon build.

**Status:** addon scaffold (`website_adaminfo_theme`, see below) was
already built code-first, ahead of this phase, using Odoo's `default-1`
placeholder palette and placeholder copy — it will need a re-sync pass
(real palette into `primary_variables.scss`, real copy into
`sections.xml`) once the mockup is approved. Not wasted work: manifest,
theme.utils wiring, menu/anchor-nav plumbing, and section template
structure stay as-is regardless of final visual design.

### Brand direction — locked (2026-10-05, brainstorm approved)

Real brand assets found in `~/Downloads` (`adaminformatika_banner_v1.2.png`,
`adaminformatika_logo_v2.png`) — not generic placeholders. Colors sampled
directly from the files (histogram, not eyeballed):

- **Logo**: `adaminformatika_logo_v2.png` — Roman centurion badge
  (navy + gold, laurel wreaths, "ADAMINFORMATIKA" circular text). Used
  as-is in header (~40px) and footer, cropped/transparent.
- **Palette**: navy bg `#001323` (page-wide, not just header/footer),
  gold accent `#D9A74A` (flattened from the logo/banner's metallic
  gradient range `#C9962C`–`#ECB860`), off-white `#F5F5F5` for headings
  and body text.
- **Type**: two-font system — serif display (Playfair Display or
  similar) for the name/H1 only, matching the badge's classical feel;
  Inter for nav/body/buttons.
- **Hero copy**: "Adam Informatika" wordmark, "Freelancer" subtitle,
  tagline **"Reliable solutions. Real impact."** (from banner, not the
  old site's "IT PM • DevOps • Coding"), gold CTA to `#contact`. Thin
  "Build · Automate · Deploy · Scale" strip under it, echoing the
  banner's layout.
- **Skills (About section)**: verbatim from banner — AWS Cloud
  Solutions, Python Developer, Odoo Developer, DevOps Automate & Scale.
- **Projects/Contact sections**: content unchanged from the original
  Content & Information Architecture section above, gold-accented
  styling.

This fully replaces the scaffold's `default-1`/Inter-only placeholder
— real custom `o-color` palette, not a stock Odoo one. Next: build this
as an actual Figma mockup (new page in the wireframe file) via
`mcp__figma__use_figma`, then re-sync the addon from it.

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

- **Target env (dev/build target):** `adaminfo-dev-1869`, resolved by
  **ID** `11e4aa83-45a8-492f-a0c9-b88aa1347ca2` (project
  `d58c356f-385d-4575-b781-e73ffe92a9cc`), branch `development`, url
  `https://adaminfo-dev-1869.apps.oec.sh`. Checked 2026-10-05: status
  already `running`, no start needed. As with `adaminfo-prod-1139`,
  resolve by ID, not name, given this account's prior name-collision
  hazard (`docs/migration-log-2026-09-04-adaminfo-prod-1139.md`).
- **Prod target (unchanged, for final cutover):** `adaminfo-prod-1139`,
  resolved by **ID** `c0672b12-b1b6-43c9-8414-7917246d0136`, **not by
  name** — same collision hazard applies.
- Build/verify the addon against `adaminfo-dev-1869` first; push branch
  → redeploy via oec.sh API → poll until done.
- Activate dev mode, install `website_adaminfo_theme` via Apps (search
  technical name first, don't click Upgrade off an unfiltered Apps list).
- Playwright (via `browser-skill`, not the built-in browser): full-page
  screenshot, verify each of the four sections renders, submit the
  contact form and confirm it lands in Odoo.
- Once verified on `adaminfo-dev-1869`, promote/redeploy to
  `adaminfo-prod-1139` and point adaminformatika.hu's DNS at it.

## Testing

- No automated test suite is practical for a marketing/portfolio page's
  visual design — verification is the Playwright pass above (render +
  form submission), matching how this repo already verifies Odoo-side
  changes (see `tests/test_verify_customer_operations_dashboard.py` for
  the pattern used elsewhere in this repo, adapted for an addon with no
  backend logic to unit-test).

## Open Items / Risks

- Figma MCP server (user scope, OAuth'd) + `odoo-frontend` plugin are
  installed and verified connected (2026-10-05) — tooling blocker
  cleared.
- Figma account + wireframes file access confirmed (2026-10-05) —
  no remaining gate on Figma access.
- **Mockup Phase complete (2026-10-05):** brainstorm approved, mockup
  built and approved in Figma
  ([Adaminfo Website Mockup](https://www.figma.com/design/3QAM2X6wAc7ZiZohAKUyja)
  — separate file from the wireframe kit, created fresh since the
  Starter plan caps the kit file at 3 pages). Real logo
  (`adaminformatika_logo_v2.png`) embedded, Name/Email/Message form
  fields mocked.
- **Addon re-synced from the mockup (2026-10-05):** `primary_variables.scss`
  now defines a real `adaminfo` color palette (gold `#D9A74A` /
  navy `#001323` / navy-light `#091C30`) instead of `default-1`, plus
  Playfair Display for H1 only (h2-h6 reset to Inter). Real logo
  copied to `static/src/img/adaminformatika_logo.png` (resized
  2.1MB→131KB) and wired via `data/website_logo.xml`. Hero/About copy
  in `sections.xml` updated to match mockup content verbatim.
  **Still open:** Projects/Contact section copy was already accurate
  pre-mockup (unchanged); the Contact form itself is still the
  pre-existing TODO (real `s_website_form` snippet not yet verified
  against this Odoo version — see Odoo Addon Architecture section).
- **Next step:** install `website_adaminfo_theme` on `adaminfo-dev-1869`
  to catch SCSS/XML errors early, then resolve the Contact form TODO.
- DNS cutover timing/registrar access not yet confirmed — flagged as
  in-scope but final step depends on user's domain registrar access.
