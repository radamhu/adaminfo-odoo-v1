import itertools
import random
from datetime import date, timedelta

# Each entry: (description_suffix, state, num_lines, days_ago)
INVOICES = [
    {'suffix': 'Consulting Q1',           'state': 'draft',  'lines': 2, 'days_ago': 0},
    {'suffix': 'Szoftver licensz csomag', 'state': 'draft',  'lines': 3, 'days_ago': 0},
    {'suffix': 'Training workshop',       'state': 'draft',  'lines': 2, 'days_ago': 0},
    {'suffix': 'Hardware eszközök',       'state': 'draft',  'lines': 4, 'days_ago': 0},
    {'suffix': 'Support Package Q2',      'state': 'draft',  'lines': 2, 'days_ago': 0},
    {'suffix': 'IT tanácsadás Feb',       'state': 'draft',  'lines': 3, 'days_ago': 0},
    {'suffix': 'Annual license 2026',     'state': 'draft',  'lines': 2, 'days_ago': 0},
    {'suffix': 'Onboarding services',     'state': 'draft',  'lines': 2, 'days_ago': 0},
    {'suffix': 'ERP setup March',         'state': 'posted', 'lines': 3, 'days_ago': 85},
    {'suffix': 'Cloud migration phase 1', 'state': 'posted', 'lines': 2, 'days_ago': 72},
    {'suffix': 'Security audit Jan',      'state': 'posted', 'lines': 2, 'days_ago': 60},
    {'suffix': 'Adatmigrálás sprint 1',   'state': 'posted', 'lines': 4, 'days_ago': 55},
    {'suffix': 'Helpdesk SLA Feb',        'state': 'posted', 'lines': 2, 'days_ago': 45},
    {'suffix': 'Custom dev sprint 1',     'state': 'posted', 'lines': 3, 'days_ago': 38},
    {'suffix': 'Training batch Q1',       'state': 'posted', 'lines': 2, 'days_ago': 30},
    {'suffix': 'Rendszer integráció',     'state': 'posted', 'lines': 3, 'days_ago': 22},
    {'suffix': 'Licensing bundle Apr',    'state': 'posted', 'lines': 2, 'days_ago': 15},
    {'suffix': 'Consulting April',        'state': 'posted', 'lines': 2, 'days_ago': 10},
    {'suffix': 'Mobile app sprint',       'state': 'posted', 'lines': 3, 'days_ago': 7},
    {'suffix': 'Support renewal May',     'state': 'posted', 'lines': 2, 'days_ago': 3},
]

_QUANTITIES = [1, 2, 3, 5]


def seed(client) -> None:
    existing = client.search_read(
        'account.move',
        [('narration', 'like', '[SEED]'), ('move_type', '=', 'out_invoice')],
        ['id'],
    )
    if existing:
        print(f'  invoicing: already seeded ({len(existing)} invoices), skipping')
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
        print('  invoicing: missing seeded partners or products, skipping')
        return

    partner_cycle = itertools.cycle([p['id'] for p in partners])
    product_cycle = itertools.cycle(products)
    today = date.today()

    for inv in INVOICES:
        lines = []
        for _ in range(inv['lines']):
            p = next(product_cycle)
            lines.append((0, 0, {
                'product_id': p['id'],
                'quantity': random.choice(_QUANTITIES),
                'price_unit': p['lst_price'],
                'name': f'[SEED] {inv["suffix"]}',
            }))
        invoice_date = (today - timedelta(days=inv['days_ago'])) if inv['days_ago'] else False
        invoice_id = client.create('account.move', {
            'move_type': 'out_invoice',
            'partner_id': next(partner_cycle),
            'narration': '[SEED]',
            'invoice_date': str(invoice_date) if invoice_date else False,
            'invoice_line_ids': lines,
        })
        if inv['state'] == 'posted':
            client.execute('account.move', 'action_post', [invoice_id])

    print(f'  invoicing: {len(INVOICES)} invoices created')


def wipe(client) -> None:
    invoices = client.search_read(
        'account.move',
        [('narration', 'like', '[SEED]'), ('move_type', '=', 'out_invoice')],
        ['id', 'state'],
    )
    if not invoices:
        print('  invoicing: nothing to wipe')
        return
    posted_ids = [i['id'] for i in invoices if i['state'] == 'posted']
    if posted_ids:
        client.execute('account.move', 'button_draft', posted_ids)
    ids = [i['id'] for i in invoices]
    client.unlink('account.move', ids)
    print(f'  invoicing: {len(ids)} invoices deleted')
