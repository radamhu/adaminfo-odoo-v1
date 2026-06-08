from unittest.mock import MagicMock, call
from seed.contacts import seed, wipe, COMPANIES, INDIVIDUALS


def test_seed_creates_all_when_none_exist():
    client = MagicMock()
    # search_read calls: existing seeds, then per company_name lookup for individuals (via country cache too)
    client.search_read.side_effect = lambda model, domain, fields, **kw: (
        [] if model == 'res.partner' and ('name', 'like', '[SEED]') in domain
        else [{'id': 99}] if model == 'res.country'
        else [{'id': 1, 'name': '[SEED] Kovács és Társai Kft.'}]
    )
    seed(client)
    # companies + individuals
    assert client.create.call_count == len(COMPANIES) + len(INDIVIDUALS)


def test_seed_skips_when_all_exist():
    client = MagicMock()
    all_names = [{'name': c['name']} for c in COMPANIES] + [{'name': i['name']} for i in INDIVIDUALS]

    def side_effect(model, domain, fields, **kw):
        if model == 'res.partner' and ('name', 'like', '[SEED]') in domain:
            return all_names
        if model == 'res.country':
            return [{'id': 99}]
        # lookup existing company by exact name
        return [{'id': 1}]

    client.search_read.side_effect = side_effect
    seed(client)
    client.create.assert_not_called()


def test_wipe_unlinks_all_seeded_partners():
    client = MagicMock()
    client.search_read.return_value = [{'id': 10}, {'id': 11}]
    wipe(client)
    client.unlink.assert_called_once_with('res.partner', [10, 11])


def test_wipe_does_nothing_when_empty():
    client = MagicMock()
    client.search_read.return_value = []
    wipe(client)
    client.unlink.assert_not_called()
