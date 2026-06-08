COMPANIES = [
    {'name': '[SEED] Kovács és Társai Kft.',    'is_company': True, 'customer_rank': 1,
     'city': 'Budapest',   'country_code': 'HU', 'phone': '+36 1 234 5678',
     'email': 'info@kovacs-tarsai.hu'},
    {'name': '[SEED] Magyar Fejlesztő Zrt.',    'is_company': True, 'customer_rank': 1,
     'city': 'Debrecen',   'country_code': 'HU', 'phone': '+36 52 345 678',
     'email': 'office@magyar-fejleszto.hu'},
    {'name': '[SEED] Budai Logisztika Kft.',    'is_company': True, 'supplier_rank': 1,
     'city': 'Budapest',   'country_code': 'HU', 'phone': '+36 1 456 7890',
     'email': 'kapcsolat@budai-logisztika.hu'},
    {'name': '[SEED] Pécs-Tech Bt.',            'is_company': True, 'customer_rank': 1,
     'city': 'Pécs',       'country_code': 'HU', 'phone': '+36 72 234 567',
     'email': 'info@pecstech.hu'},
    {'name': '[SEED] Győri Nyomda Kft.',        'is_company': True, 'supplier_rank': 1,
     'city': 'Győr',       'country_code': 'HU', 'phone': '+36 96 345 678',
     'email': 'rendeles@gyorinyomda.hu'},
    {'name': '[SEED] Debreceni Consulting Kft.','is_company': True, 'customer_rank': 1,
     'city': 'Debrecen',   'country_code': 'HU', 'phone': '+36 52 456 789',
     'email': 'hello@debconsulting.hu'},
    {'name': '[SEED] Alföldi Agro Zrt.',        'is_company': True, 'customer_rank': 1,
     'city': 'Kecskemét',  'country_code': 'HU', 'phone': '+36 76 234 567',
     'email': 'info@alfoldiagro.hu'},
    {'name': '[SEED] Balaton Turisztika Kft.',  'is_company': True, 'customer_rank': 1,
     'city': 'Siófok',     'country_code': 'HU', 'phone': '+36 84 345 678',
     'email': 'foglalas@balatonturisztika.hu'},
    {'name': '[SEED] Acme Corp Ltd.',           'is_company': True, 'customer_rank': 1,
     'city': 'London',     'country_code': 'GB', 'phone': '+44 20 1234 5678',
     'email': 'contact@acmecorp.co.uk'},
    {'name': '[SEED] Nexus Solutions GmbH',     'is_company': True, 'customer_rank': 1,
     'city': 'Berlin',     'country_code': 'DE', 'phone': '+49 30 123 4567',
     'email': 'info@nexussolutions.de'},
    {'name': '[SEED] Alpine Ventures AG',       'is_company': True, 'supplier_rank': 1,
     'city': 'Vienna',     'country_code': 'AT', 'phone': '+43 1 234 5678',
     'email': 'office@alpineventures.at'},
    {'name': '[SEED] Nordic Systems AS',        'is_company': True, 'customer_rank': 1,
     'city': 'Oslo',       'country_code': 'NO', 'phone': '+47 21 234 567',
     'email': 'contact@nordicsystems.no'},
    {'name': '[SEED] Eastern Bridge Ltd.',      'is_company': True, 'customer_rank': 1,
     'city': 'Warsaw',     'country_code': 'PL', 'phone': '+48 22 234 5678',
     'email': 'info@easternbridge.pl'},
]

INDIVIDUALS = [
    {'name': '[SEED] Kovács Péter',    'company_name': '[SEED] Kovács és Társai Kft.',
     'email': 'peter.kovacs@kovacs-tarsai.hu',    'phone': '+36 30 123 4567', 'function': 'Ügyvezető'},
    {'name': '[SEED] Nagy Anna',       'company_name': '[SEED] Magyar Fejlesztő Zrt.',
     'email': 'anna.nagy@magyar-fejleszto.hu',     'phone': '+36 70 234 5678', 'function': 'Projektvezető'},
    {'name': '[SEED] Horváth Gábor',   'company_name': '[SEED] Budai Logisztika Kft.',
     'email': 'gabor.horvath@budai-logisztika.hu', 'phone': '+36 20 345 6789', 'function': 'Logisztikai vezető'},
    {'name': '[SEED] Szabó Éva',       'company_name': '[SEED] Pécs-Tech Bt.',
     'email': 'eva.szabo@pecstech.hu',             'phone': '+36 30 456 7890', 'function': 'Fejlesztő'},
    {'name': '[SEED] Tóth István',     'company_name': '[SEED] Győri Nyomda Kft.',
     'email': 'istvan.toth@gyorinyomda.hu',        'phone': '+36 20 567 8901', 'function': 'Értékesítési vezető'},
    {'name': '[SEED] Fekete Zsuzsanna','company_name': '[SEED] Debreceni Consulting Kft.',
     'email': 'zsuzsanna.fekete@debconsulting.hu', 'phone': '+36 70 678 9012', 'function': 'Tanácsadó'},
    {'name': '[SEED] Varga László',    'company_name': '[SEED] Alföldi Agro Zrt.',
     'email': 'laszlo.varga@alfoldiagro.hu',       'phone': '+36 30 789 0123', 'function': 'Értékesítő'},
    {'name': '[SEED] Kiss Mária',      'company_name': '[SEED] Balaton Turisztika Kft.',
     'email': 'maria.kiss@balatonturisztika.hu',   'phone': '+36 20 890 1234', 'function': 'Recepciós'},
    {'name': '[SEED] John Smith',      'company_name': '[SEED] Acme Corp Ltd.',
     'email': 'john.smith@acmecorp.co.uk',         'phone': '+44 7700 900001', 'function': 'Sales Manager'},
    {'name': '[SEED] Sarah Johnson',   'company_name': '[SEED] Nexus Solutions GmbH',
     'email': 'sarah.johnson@nexussolutions.de',   'phone': '+49 170 234 5678', 'function': 'Account Manager'},
    {'name': '[SEED] Hans Mueller',    'company_name': '[SEED] Alpine Ventures AG',
     'email': 'hans.mueller@alpineventures.at',    'phone': '+43 650 234 5678', 'function': 'Director'},
    {'name': '[SEED] Erik Larsson',    'company_name': '[SEED] Nordic Systems AS',
     'email': 'erik.larsson@nordicsystems.no',     'phone': '+47 900 12 345',  'function': 'CTO'},
]


def _country_id(client, cache: dict, code: str) -> int:
    if code not in cache:
        res = client.search_read('res.country', [('code', '=', code)], ['id'])
        cache[code] = res[0]['id'] if res else False
    return cache[code]


def seed(client) -> None:
    existing = client.search_read('res.partner', [('name', 'like', '[SEED]')], ['name'])
    existing_names = {r['name'] for r in existing}
    country_cache: dict = {}
    company_ids: dict = {}
    created = 0

    for c in COMPANIES:
        cid = _country_id(client, country_cache, c['country_code'])
        vals = {k: v for k, v in c.items() if k != 'country_code'}
        vals['country_id'] = cid
        if c['name'] not in existing_names:
            new_id = client.create('res.partner', vals)
            created += 1
        else:
            rec = client.search_read('res.partner', [('name', '=', c['name'])], ['id'])
            new_id = rec[0]['id']
        company_ids[c['name']] = new_id

    for ind in INDIVIDUALS:
        if ind['name'] not in existing_names:
            vals = {k: v for k, v in ind.items() if k != 'company_name'}
            parent_id = company_ids.get(ind['company_name'])
            if parent_id:
                vals['parent_id'] = parent_id
            client.create('res.partner', vals)
            created += 1

    total = len(COMPANIES) + len(INDIVIDUALS)
    print(f'  contacts: {created} created, {total - created} skipped')


def wipe(client) -> None:
    records = client.search_read('res.partner', [('name', 'like', '[SEED]')], ['id'])
    if not records:
        print('  contacts: nothing to wipe')
        return
    ids = [r['id'] for r in records]
    client.unlink('res.partner', ids)
    print(f'  contacts: {len(ids)} deleted')
