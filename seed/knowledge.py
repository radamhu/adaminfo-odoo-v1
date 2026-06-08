TOP_ARTICLES = [
    {
        'name': '[SEED] Onboarding Guide',
        'body': '<h1>Welcome</h1><p>This guide helps new team members get started with our systems and processes. Follow each section to complete your onboarding.</p>',
    },
    {
        'name': '[SEED] Fejlesztői Kézikönyv',
        'body': '<h1>Fejlesztői Kézikönyv</h1><p>Ez a dokumentum tartalmazza a fejlesztési folyamatokat, kódolási szabványokat és a CI/CD pipeline leírását.</p>',
    },
    {
        'name': '[SEED] Sales Playbook',
        'body': '<h1>Sales Playbook</h1><p>This document covers our sales process from lead qualification to contract signing. It includes objection handling scripts and pricing guidelines.</p>',
    },
    {
        'name': '[SEED] Belső Folyamatok',
        'body': '<h1>Belső Folyamatok</h1><p>A vállalat belső folyamatainak leírása: jóváhagyási rendszer, kommunikációs protokollok és projekt kezelési szabályok.</p>',
    },
    {
        'name': '[SEED] Product Documentation',
        'body': '<h1>Product Documentation</h1><p>Technical documentation for our main product suite. Covers installation, configuration, and API reference.</p>',
    },
]

CHILD_ARTICLES = [
    {
        'name': '[SEED] IT Setup Checklist',
        'parent_name': '[SEED] Onboarding Guide',
        'body': '<h2>IT Setup</h2><ul><li>Request laptop from IT</li><li>Set up VPN access</li><li>Configure email client</li><li>Join Slack workspace</li></ul>',
    },
    {
        'name': '[SEED] HR & Benefits Overview',
        'parent_name': '[SEED] Onboarding Guide',
        'body': '<h2>HR &amp; Benefits</h2><p>Review your employment contract, sign up for health insurance, and schedule your 30-day check-in with your manager.</p>',
    },
    {
        'name': '[SEED] Git Workflow',
        'parent_name': '[SEED] Fejlesztői Kézikönyv',
        'body': '<h2>Git Workflow</h2><p>Feature branches → Pull Request → Code review (min. 1 approval) → Merge to main. Never force-push to main.</p>',
    },
    {
        'name': '[SEED] Kód Review Szabályok',
        'parent_name': '[SEED] Fejlesztői Kézikönyv',
        'body': '<h2>Kód Review</h2><p>Minden PR-t legalább egy kolléga kell jóváhagyja. A review-k során fókuszálj a logikára, biztonságra és a tesztek lefedettségére.</p>',
    },
    {
        'name': '[SEED] Lead Qualification',
        'parent_name': '[SEED] Sales Playbook',
        'body': '<h2>Lead Qualification</h2><p>Use the BANT framework: Budget, Authority, Need, Timeline. A lead must score at least 3/4 before moving to Opportunity.</p>',
    },
    {
        'name': '[SEED] Pricing Guidelines',
        'parent_name': '[SEED] Sales Playbook',
        'body': '<h2>Pricing</h2><p>Standard rates apply. Discounts above 15% require manager approval. Volume discounts kick in at 10+ seats.</p>',
    },
    {
        'name': '[SEED] Jóváhagyási Folyamat',
        'parent_name': '[SEED] Belső Folyamatok',
        'body': '<h2>Jóváhagyások</h2><p>5000 EUR feletti kiadásokhoz pénzügyi igazgatói jóváhagyás szükséges. Az igényléseket a CRM rendszerben kell rögzíteni.</p>',
    },
    {
        'name': '[SEED] Communication Protocols',
        'parent_name': '[SEED] Belső Folyamatok',
        'body': '<h2>Communication</h2><p>Use Slack for async communication. Email for external parties. Weekly standups on Monday 9am. Urgent issues: call directly.</p>',
    },
    {
        'name': '[SEED] API Reference',
        'parent_name': '[SEED] Product Documentation',
        'body': '<h2>API Reference</h2><p>Base URL: <code>https://api.example.com/v1</code>. Authentication: Bearer token. Rate limit: 1000 req/min. Full spec in Swagger.</p>',
    },
    {
        'name': '[SEED] Telepítési Útmutató',
        'parent_name': '[SEED] Product Documentation',
        'body': '<h2>Telepítés</h2><p>Követelmények: Python 3.9+, PostgreSQL 14+, 4GB RAM. Telepítési lépések: clone, pip install, adatbázis inicializálás, szerver indítás.</p>',
    },
]


def seed(client) -> None:
    existing = client.search_read('knowledge.article', [('name', 'like', '[SEED]')], ['name'])
    existing_names = {r['name'] for r in existing}
    parent_ids: dict = {}
    created = 0

    for art in TOP_ARTICLES:
        if art['name'] not in existing_names:
            new_id = client.create('knowledge.article', {
                'name': art['name'],
                'body': art['body'],
            })
            created += 1
        else:
            rec = client.search_read('knowledge.article', [('name', '=', art['name'])], ['id'])
            new_id = rec[0]['id'] if rec else None
        parent_ids[art['name']] = new_id

    for art in CHILD_ARTICLES:
        if art['name'] not in existing_names:
            vals = {'name': art['name'], 'body': art['body']}
            parent_id = parent_ids.get(art['parent_name'])
            if parent_id:
                vals['parent_id'] = parent_id
            client.create('knowledge.article', vals)
            created += 1

    total = len(TOP_ARTICLES) + len(CHILD_ARTICLES)
    print(f'  knowledge: {created} created, {total - created} skipped')


def wipe(client) -> None:
    records = client.search_read('knowledge.article', [('name', 'like', '[SEED]')], ['id'])
    if not records:
        print('  knowledge: nothing to wipe')
        return
    ids = [r['id'] for r in records]
    client.unlink('knowledge.article', ids)
    print(f'  knowledge: {len(ids)} articles deleted')
