from unittest.mock import MagicMock
from seed.timesheet import seed, wipe, ENTRY_COUNT


def _mock_client(existing_timesheets=None):
    client = MagicMock()
    entries = existing_timesheets if existing_timesheets is not None else []

    def search_read(model, domain, fields, **kw):
        if model == 'account.analytic.line':
            return entries
        if model == 'project.project':
            return [{'id': i + 1, 'name': f'[SEED] Project {i}'} for i in range(3)]
        if model == 'project.task':
            return [{'id': i + 10, 'project_id': (i % 3) + 1} for i in range(9)]
        if model == 'hr.employee':
            return [{'id': 5, 'name': 'Admin'}]
        return []

    client.search_read.side_effect = search_read
    return client


def test_seed_creates_entries_when_none_exist():
    client = _mock_client([])
    seed(client)
    assert client.create.call_count == ENTRY_COUNT


def test_seed_skips_when_already_seeded():
    client = _mock_client([{'id': 1}])
    seed(client)
    client.create.assert_not_called()


def test_seed_each_entry_targets_analytic_line_model():
    client = _mock_client([])
    seed(client)
    for c in client.create.call_args_list:
        assert c[0][0] == 'account.analytic.line'


def test_wipe_unlinks_all():
    client = MagicMock()
    client.search_read.return_value = [{'id': 1}, {'id': 2}]
    wipe(client)
    client.unlink.assert_called_once_with('account.analytic.line', [1, 2])


def test_wipe_does_nothing_when_empty():
    client = MagicMock()
    client.search_read.return_value = []
    wipe(client)
    client.unlink.assert_not_called()
