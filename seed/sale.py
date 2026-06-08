import itertools
import random

# (description in note, state, number_of_lines)
ORDERS = [
    {'note': '[SEED] Webfejlesztési projekt',     'state': 'draft',  'lines': 2},
    {'note': '[SEED] IT tanácsadás Q3',           'state': 'draft',  'lines': 3},
    {'note': '[SEED] Szoftver licensz csomag',    'state': 'draft',  'lines': 2},
    {'note': '[SEED] Hardver eszközök rendelés',  'state': 'draft',  'lines': 4},
    {'note': '[SEED] Képzési program tervezés',   'state': 'draft',  'lines': 2},
    {'note': '[SEED] Support contract Q1',        'state': 'sent',   'lines': 3},
    {'note': '[SEED] Annual license renewal',     'state': 'sent',   'lines': 2},
    {'note': '[SEED] Consulting services pkg',    'state': 'sent',   'lines': 4},
    {'note': '[SEED] Irodaszerek rendelés',       'state': 'sent',   'lines': 3},
    {'note': '[SEED] Training workshop bundle',   'state': 'sent',   'lines': 2},
    {'note': '[SEED] ERP bevezetési projekt',     'state': 'sale',   'lines': 3},
    {'note': '[SEED] Cloud migration phase 1',   'state': 'sale',   'lines': 2},
    {'note': '[SEED] Security audit contract',   'state': 'sale',   'lines': 2},
    {'note': '[SEED] Adatmigrálás projekt',       'state': 'sale',   'lines': 4},
    {'note': '[SEED] Rendszer integráció',        'state': 'sale',   'lines': 3},
    {'note': '[SEED] Helpdesk support SLA',      'state': 'sale',   'lines': 2},
    {'note': '[SEED] Custom dev sprint 1',       'state': 'sale',   'lines': 3},
    {'note': '[SEED] Tesztelési projekt',         'state': 'cancel', 'lines': 2},
    {'note': '[SEED] Pilot program cancelled',   'state': 'cancel', 'lines': 3},
    {'note': '[SEED] Infrastructure cancelled',  'state': 'cancel', 'lines': 2},
]

_QUANTITIES = [1, 2, 3, 5, 10]


def seed(client) -> None:
    existing = client.search_read('sale.order', [('client_order_ref', '=', '[SEED]')], ['id'])
    if existing:
        print(f'  sale: already seeded ({len(existing)} orders), skipping')
        return

    partners = client.search_read(
        'res.partner', [('name', 'like', '[SEED]'), ('is_company', '=', True)], ['id']
    )
    products = client.search_read(
        'product.product',
        [('product_tmpl_id.name', 'like', '[SEED]')],
        ['id', 'lst_price'],
    )
    if not partners or not products:
        print('  sale: missing seeded partners or products, skipping')
        return

    partner_cycle = itertools.cycle([p['id'] for p in partners])
    product_cycle = itertools.cycle(products)

    for order in ORDERS:
        lines = []
        for _ in range(order['lines']):
            p = next(product_cycle)
            lines.append((0, 0, {
                'product_id': p['id'],
                'product_uom_qty': random.choice(_QUANTITIES),
                'price_unit': p['lst_price'],
            }))
        order_id = client.create('sale.order', {
            'partner_id': next(partner_cycle),
            'client_order_ref': '[SEED]',
            'note': order['note'],
            'order_line': lines,
        })
        if order['state'] == 'sale':
            client.execute('sale.order', 'action_confirm', [order_id])
        elif order['state'] == 'sent':
            client.write('sale.order', [order_id], {'state': 'sent'})
        elif order['state'] == 'cancel':
            client.execute('sale.order', 'action_cancel', [order_id])

    print(f'  sale: {len(ORDERS)} orders created')


def wipe(client) -> None:
    orders = client.search_read(
        'sale.order', [('client_order_ref', '=', '[SEED]')], ['id', 'state']
    )
    if not orders:
        print('  sale: nothing to wipe')
        return
    to_cancel = [o['id'] for o in orders if o['state'] in ('sale', 'done')]
    if to_cancel:
        client.execute('sale.order', 'action_cancel', to_cancel)
    ids = [o['id'] for o in orders]
    client.unlink('sale.order', ids)
    print(f'  sale: {len(ids)} orders deleted')
