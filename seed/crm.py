import itertools

LEADS = [
    {'name': '[SEED] Weboldal fejlesztés igény',   'type': 'lead', 'stage_key': 0,
     'expected_revenue': 2500.0,  'probability': 10,
     'description': 'Az ügyfél egyedi weboldalt szeretne.'},
    {'name': '[SEED] ERP bevezetési érdeklődés',   'type': 'lead', 'stage_key': 0,
     'expected_revenue': 15000.0, 'probability': 20,
     'description': 'ERP rendszer bevezetése 50 fős cégnek.'},
    {'name': '[SEED] IT infrastruktúra felmérés',  'type': 'lead', 'stage_key': 0,
     'expected_revenue': 4500.0,  'probability': 15,
     'description': 'Hálózati infrastruktúra audit igény.'},
    {'name': '[SEED] Software audit request',      'type': 'lead', 'stage_key': 0,
     'expected_revenue': 3200.0,  'probability': 25,
     'description': 'Client wants a full software stack review.'},
    {'name': '[SEED] Cloud migration inquiry',     'type': 'lead', 'stage_key': 0,
     'expected_revenue': 8000.0,  'probability': 20,
     'description': 'Interested in migrating on-premise to cloud.'},
    {'name': '[SEED] Mobilalkalmazás fejlesztés',  'type': 'lead', 'stage_key': 1,
     'expected_revenue': 6500.0,  'probability': 35,
     'description': 'iOS és Android alkalmazás fejlesztési igény.'},
    {'name': '[SEED] CRM integration project',    'type': 'lead', 'stage_key': 1,
     'expected_revenue': 5000.0,  'probability': 30,
     'description': 'Integrate existing CRM with new platform.'},
    {'name': '[SEED] Adatelemzési megoldás',       'type': 'lead', 'stage_key': 1,
     'expected_revenue': 12000.0, 'probability': 40,
     'description': 'BI dashboard és adatelemzési rendszer.'},
    {'name': '[SEED] E-commerce platform build',  'type': 'lead', 'stage_key': 1,
     'expected_revenue': 18000.0, 'probability': 30,
     'description': 'Full e-commerce solution with payment gateway.'},
    {'name': '[SEED] Képzési program tervezés',   'type': 'lead', 'stage_key': 1,
     'expected_revenue': 3000.0,  'probability': 45,
     'description': 'Vállalati képzési program összeállítása.'},
]

OPPORTUNITIES = [
    {'name': '[SEED] Éves IT support szerződés',     'type': 'opportunity', 'stage_key': 0,
     'expected_revenue': 24000.0, 'probability': 50,
     'description': 'Éves szintű support és karbantartási szerződés.'},
    {'name': '[SEED] Odoo implementation Q3',        'type': 'opportunity', 'stage_key': 0,
     'expected_revenue': 35000.0, 'probability': 55,
     'description': 'Full Odoo Community setup for 30 users.'},
    {'name': '[SEED] Security hardening contract',   'type': 'opportunity', 'stage_key': 1,
     'expected_revenue': 9500.0,  'probability': 60,
     'description': 'Penetration testing and security audit.'},
    {'name': '[SEED] Rendszer integráció projekt',   'type': 'opportunity', 'stage_key': 1,
     'expected_revenue': 28000.0, 'probability': 65,
     'description': 'SAP és Odoo integráció tervezés és kivitelezés.'},
    {'name': '[SEED] Annual license bundle',         'type': 'opportunity', 'stage_key': 1,
     'expected_revenue': 5800.0,  'probability': 70,
     'description': 'Multi-seat software license renewal package.'},
    {'name': '[SEED] Logisztikai szoftver fejlesztés','type': 'opportunity', 'stage_key': 2,
     'expected_revenue': 42000.0, 'probability': 75,
     'description': 'Egyedi raktárkezelő szoftver fejlesztése.'},
    {'name': '[SEED] Training programme 2026',       'type': 'opportunity', 'stage_key': 2,
     'expected_revenue': 7200.0,  'probability': 80,
     'description': 'Six-month developer upskilling programme.'},
    {'name': '[SEED] Felhő migráció projekt',        'type': 'opportunity', 'stage_key': 2,
     'expected_revenue': 19500.0, 'probability': 85,
     'description': 'Azure felhő átállás tervezés és végrehajtás.'},
    {'name': '[SEED] Custom dashboard development',  'type': 'opportunity', 'stage_key': 2,
     'expected_revenue': 6000.0,  'probability': 80,
     'description': 'Real-time KPI dashboard for management.'},
    {'name': '[SEED] Helpdesk rendszer kiépítés',    'type': 'opportunity', 'stage_key': 2,
     'expected_revenue': 11000.0, 'probability': 85,
     'description': 'Ticketing és helpdesk rendszer bevezetése.'},
    {'name': '[SEED] ERP Q4 go-live',                'type': 'opportunity', 'stage_key': 3,
     'expected_revenue': 50000.0, 'probability': 90,
     'description': 'ERP production rollout scheduled Q4 2026.'},
    {'name': '[SEED] Data warehouse project — WON',  'type': 'opportunity', 'stage_key': 3,
     'expected_revenue': 32000.0, 'probability': 100,
     'description': 'Data warehouse build — deal closed.'},
    {'name': '[SEED] Cancelled security audit',      'type': 'opportunity', 'stage_key': 3,
     'expected_revenue': 4500.0,  'probability': 0,
     'description': 'Security audit — cancelled by client.'},
    {'name': '[SEED] Partnership portal',            'type': 'opportunity', 'stage_key': 3,
     'expected_revenue': 14000.0, 'probability': 95,
     'description': 'B2B partner self-service portal.'},
    {'name': '[SEED] Mobilapp pilot — closed',       'type': 'opportunity', 'stage_key': 3,
     'expected_revenue': 8500.0,  'probability': 100,
     'description': 'Mobile app pilot — completed and invoiced.'},
]


def seed(client) -> None:
    existing = client.search_read('crm.lead', [('name', 'like', '[SEED]')], ['name'])
    existing_names = {r['name'] for r in existing}

    partners = client.search_read('res.partner', [('name', 'like', '[SEED]'), ('is_company', '=', True)], ['id'])
    stages = client.search_read('crm.stage', [], ['id', 'name'])
    stage_ids = [s['id'] for s in stages] or [False]
    partner_cycle = itertools.cycle([p['id'] for p in partners]) if partners else itertools.cycle([False])

    created = 0
    for record in LEADS + OPPORTUNITIES:
        if record['name'] in existing_names:
            continue
        stage_idx = min(record['stage_key'], len(stage_ids) - 1)
        vals = {
            'name': record['name'],
            'type': record['type'],
            'stage_id': stage_ids[stage_idx],
            'expected_revenue': record['expected_revenue'],
            'probability': record['probability'],
            'description': record['description'],
            'partner_id': next(partner_cycle),
        }
        client.create('crm.lead', vals)
        created += 1

    total = len(LEADS) + len(OPPORTUNITIES)
    print(f'  crm: {created} created, {total - created} skipped')


def wipe(client) -> None:
    records = client.search_read('crm.lead', [('name', 'like', '[SEED]')], ['id'])
    if not records:
        print('  crm: nothing to wipe')
        return
    ids = [r['id'] for r in records]
    client.unlink('crm.lead', ids)
    print(f'  crm: {len(ids)} deleted')
