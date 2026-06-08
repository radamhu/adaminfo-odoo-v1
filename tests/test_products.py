from unittest.mock import MagicMock, call
from seed.products import seed, wipe, PRODUCTS


def test_seed_creates_all_when_none_exist():
    client = MagicMock()
    client.search_read.return_value = []
    seed(client)
    client.search_read.assert_called_once_with(
        'product.template', [('name', 'like', '[SEED]')], ['name']
    )
    assert client.create.call_count == len(PRODUCTS)
    first_call = client.create.call_args_list[0]
    assert first_call[0][0] == 'product.template'
    assert first_call[0][1]['name'] == '[SEED] Consulting'


def test_seed_skips_existing_products():
    client = MagicMock()
    client.search_read.return_value = [{'name': p['name']} for p in PRODUCTS]
    seed(client)
    client.create.assert_not_called()


def test_seed_creates_only_missing():
    client = MagicMock()
    client.search_read.return_value = [{'name': '[SEED] Consulting'}]
    seed(client)
    assert client.create.call_count == len(PRODUCTS) - 1


def test_wipe_unlinks_found_records():
    client = MagicMock()
    client.search_read.return_value = [{'id': 1}, {'id': 2}, {'id': 3}]
    wipe(client)
    client.search_read.assert_called_once_with(
        'product.template', [('name', 'like', '[SEED]')], ['id']
    )
    client.unlink.assert_called_once_with('product.template', [1, 2, 3])


def test_wipe_does_nothing_when_empty():
    client = MagicMock()
    client.search_read.return_value = []
    wipe(client)
    client.unlink.assert_not_called()
