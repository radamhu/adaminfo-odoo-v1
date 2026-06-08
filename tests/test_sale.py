from unittest.mock import MagicMock
from seed.sale import seed, wipe, ORDERS


def _mock_client(existing_orders=None):
    client = MagicMock()
    orders = existing_orders if existing_orders is not None else []

    def search_read(model, domain, fields, **kw):
        if model == 'sale.order':
            return orders
        if model == 'res.partner':
            return [{'id': i + 1, 'name': f'[SEED] Company {i}'} for i in range(5)]
        if model == 'product.product':
            return [{'id': i + 10, 'name': f'[SEED] Product {i}', 'lst_price': 100.0}
                    for i in range(4)]
        return []

    client.search_read.side_effect = search_read
    client.create.return_value = 99
    return client


def test_seed_creates_orders_when_none_exist():
    client = _mock_client([])
    seed(client)
    # Each order = 1 create (with inline lines via Command)
    assert client.create.call_count == len(ORDERS)


def test_seed_skips_when_already_seeded():
    client = _mock_client([{'id': 1}])
    seed(client)
    client.create.assert_not_called()


def test_seed_confirms_sale_state_orders():
    client = _mock_client([])
    seed(client)
    confirmed = [o for o in ORDERS if o['state'] == 'sale']
    confirm_calls = [c for c in client.execute.call_args_list
                     if c[0][1] == 'action_confirm']
    assert len(confirm_calls) == len(confirmed)


def test_seed_cancels_cancel_state_orders():
    client = _mock_client([])
    seed(client)
    cancelled = [o for o in ORDERS if o['state'] == 'cancel']
    cancel_calls = [c for c in client.execute.call_args_list
                    if c[0][1] == 'action_cancel']
    assert len(cancel_calls) == len(cancelled)


def test_wipe_cancels_confirmed_then_unlinks():
    client = MagicMock()
    client.search_read.return_value = [
        {'id': 1, 'state': 'sale'},
        {'id': 2, 'state': 'draft'},
    ]
    wipe(client)
    client.execute.assert_called_once_with('sale.order', 'action_cancel', [1])
    client.unlink.assert_called_once_with('sale.order', [1, 2])


def test_wipe_does_nothing_when_empty():
    client = MagicMock()
    client.search_read.return_value = []
    wipe(client)
    client.unlink.assert_not_called()
