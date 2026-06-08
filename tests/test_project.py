from unittest.mock import MagicMock
from seed.project import seed, wipe, PROJECTS


def _mock_client(existing_projects=None):
    client = MagicMock()
    projects = existing_projects if existing_projects is not None else []

    def search_read(model, domain, fields, **kw):
        if model == 'project.project':
            return projects
        if model == 'res.partner':
            return [{'id': i + 1} for i in range(5)]
        if model == 'project.task.type':
            return [{'id': 1, 'name': 'In Progress'}, {'id': 2, 'name': 'Done'}]
        return []

    client.search_read.side_effect = search_read
    client.create.return_value = 50
    return client


def test_seed_creates_projects_and_tasks_when_none_exist():
    client = _mock_client([])
    seed(client)
    # projects + tasks per project
    total_tasks = sum(p['tasks'] for p in PROJECTS)
    assert client.create.call_count == len(PROJECTS) + total_tasks


def test_seed_skips_when_all_projects_exist():
    existing = [{'name': p['name']} for p in PROJECTS]
    client = _mock_client(existing)
    seed(client)
    client.create.assert_not_called()


def test_wipe_unlinks_tasks_then_projects():
    client = MagicMock()

    def search_read(model, domain, fields, **kw):
        if model == 'project.project':
            return [{'id': 10}, {'id': 11}]
        if model == 'project.task':
            return [{'id': 100}, {'id': 101}]
        return []

    client.search_read.side_effect = search_read
    wipe(client)
    calls = client.unlink.call_args_list
    assert calls[0][0] == ('project.task', [100, 101])
    assert calls[1][0] == ('project.project', [10, 11])


def test_wipe_does_nothing_when_empty():
    client = MagicMock()
    client.search_read.return_value = []
    wipe(client)
    client.unlink.assert_not_called()
