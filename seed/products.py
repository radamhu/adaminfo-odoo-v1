PRODUCTS = [
    {'name': '[SEED] Consulting',         'type': 'service', 'list_price': 150.0},
    {'name': '[SEED] Tanácsadás',         'type': 'service', 'list_price': 45000.0},
    {'name': '[SEED] Support Package',    'type': 'service', 'list_price': 500.0},
    {'name': '[SEED] Támogatási csomag',  'type': 'service', 'list_price': 150000.0},
    {'name': '[SEED] Training',           'type': 'service', 'list_price': 1200.0},
    {'name': '[SEED] Szoftver licensz',   'type': 'consu',   'list_price': 299.0},
    {'name': '[SEED] Hardware Module',    'type': 'consu',   'list_price': 89.0},
    {'name': '[SEED] Irodaszer csomag',   'type': 'consu',   'list_price': 12500.0},
]


def seed(client) -> None:
    existing = client.search_read('product.template', [('name', 'like', '[SEED]')], ['name'])
    existing_names = {r['name'] for r in existing}
    created = 0
    for p in PRODUCTS:
        if p['name'] not in existing_names:
            client.create('product.template', p)
            created += 1
    print(f'  products: {created} created, {len(PRODUCTS) - created} skipped')


def wipe(client) -> None:
    records = client.search_read('product.template', [('name', 'like', '[SEED]')], ['id'])
    if not records:
        print('  products: nothing to wipe')
        return
    ids = [r['id'] for r in records]
    client.unlink('product.template', ids)
    print(f'  products: {len(ids)} deleted')
