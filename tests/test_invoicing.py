from unittest.mock import MagicMock
from seed.invoicing import seed, wipe, INVOICES


def _mock_client(existing_invoices=None):
    client = MagicMock()
    invoices = existing_invoices if existing_invoices is not None else []

    def search_read(model, domain, fields, **kw):
        if model == 'account.move':
            return invoices
        if model == 'res.partner':
            return [{'id': i + 1} for i in range(5)]
        if model == 'product.product':
            return [{'id': i + 10, 'lst_price': 150.0} for i in range(4)]
        return []

    client.search_read.side_effect = search_read
    client.create.return_value = 77
    return client


def test_seed_creates_all_invoices_when_none_exist():
    client = _mock_client([])
    seed(client)
    assert client.create.call_count == len(INVOICES)


def test_seed_skips_when_already_seeded():
    client = _mock_client([{'id': 1}])
    seed(client)
    client.create.assert_not_called()


def test_seed_posts_invoices_with_posted_state():
    client = _mock_client([])
    seed(client)
    posted_count = sum(1 for inv in INVOICES if inv['state'] == 'posted')
    post_calls = [c for c in client.execute.call_args_list if c[0][1] == 'action_post']
    assert len(post_calls) == posted_count


def test_wipe_resets_posted_invoices_before_unlink():
    client = MagicMock()
    client.search_read.return_value = [
        {'id': 1, 'state': 'posted'},
        {'id': 2, 'state': 'draft'},
    ]
    wipe(client)
    client.execute.assert_called_once_with('account.move', 'button_draft', [1])
    client.unlink.assert_called_once_with('account.move', [1, 2])


def test_wipe_does_nothing_when_empty():
    client = MagicMock()
    client.search_read.return_value = []
    wipe(client)
    client.unlink.assert_not_called()
