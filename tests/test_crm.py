from unittest.mock import MagicMock
from seed.crm import seed, wipe, LEADS, OPPORTUNITIES


def _mock_client_for_seed(existing_crm=None):
    client = MagicMock()
    all_data = existing_crm if existing_crm is not None else []

    def search_read(model, domain, fields, **kw):
        if model == 'crm.lead':
            return all_data
        if model == 'res.partner':
            return [{'id': i + 1, 'name': f'Partner {i}'} for i in range(5)]
        if model == 'crm.stage':
            return [{'id': 1, 'name': 'New'}, {'id': 2, 'name': 'Qualified'},
                    {'id': 3, 'name': 'Proposition'}, {'id': 4, 'name': 'Won'}]
        return []

    client.search_read.side_effect = search_read
    return client


def test_seed_creates_all_when_none_exist():
    client = _mock_client_for_seed([])
    seed(client)
    assert client.create.call_count == len(LEADS) + len(OPPORTUNITIES)


def test_seed_skips_when_all_exist():
    existing = [{'name': r['name']} for r in LEADS + OPPORTUNITIES]
    client = _mock_client_for_seed(existing)
    seed(client)
    client.create.assert_not_called()


def test_seed_each_lead_uses_crm_lead_model():
    client = _mock_client_for_seed([])
    seed(client)
    for c in client.create.call_args_list:
        assert c[0][0] == 'crm.lead'


def test_wipe_unlinks_all():
    client = MagicMock()
    client.search_read.return_value = [{'id': 1}, {'id': 2}]
    wipe(client)
    client.unlink.assert_called_once_with('crm.lead', [1, 2])


def test_wipe_does_nothing_when_empty():
    client = MagicMock()
    client.search_read.return_value = []
    wipe(client)
    client.unlink.assert_not_called()
