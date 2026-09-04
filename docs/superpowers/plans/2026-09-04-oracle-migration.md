# adaminfo-prod-1139 Oracle Cloud Migration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Migrate the `adaminfo-prod-1139` oec.sh environment to the new Oracle Cloud server (`1bf4ace1-9eea-4da9-a6b0-8497f6877c9a`) using oec.sh's native backup-restore-to-different-server feature, with pre/post verification automated as far as the platform allows.

**Architecture:** Two automatable surfaces. A small Python client package (`migration/`) wraps the oec.sh public REST API (`api.oec.sh/api/public/v1`) for everything the API exposes — server/project/environment discovery, backup listing, health status, logs, stop/start/delete. Playwright (MCP tools, driven live during execution, not scripted into the repo) covers what only exists inside the running Odoo app — login, module list, scheduled actions, a generic create/save smoke test, PDF rendering, attachments, email UI trigger. Two sub-steps (creating the backup, triggering the restore itself) have no API endpoint and stay dashboard-only, confirmed against the live `openapi.json`.

**Tech Stack:** Python 3.13, `requests`, `python-dotenv`, `pytest` (existing repo conventions — see `seed/connection.py` / `tests/test_connection.py` for the established client + test style this follows), Playwright MCP tools for in-app verification.

**Spec:** `docs/superpowers/specs/2026-09-04-oracle-migration-design.md`

## Global Constraints

- oec.sh API base URL: `https://api.oec.sh/api/public/v1`; auth header `Authorization: Bearer $ODOO_PUBLIC_API_KEY` (key already in `.env.prod`/`.env.dev`, same key works across all projects/environments on this account).
- No public API for backup creation or restore-to-different-server — those two actions stay manual, dashboard-only (`platform.oec.sh`). Every other platform action goes through the API.
- Downtime is not a hard constraint (confirmed flexible) — old env keeps serving until explicitly stopped.
- URL is oec.sh subdomain only (`adaminfo-prod-1139.apps.oec.sh`), no custom DNS in play.
- Old environment id: `cca3f63b-f16d-4b42-85f0-fb11827aa263`. Target server id: `1bf4ace1-9eea-4da9-a6b0-8497f6877c9a`. Project id: `d58c356f-385d-4575-b781-e73ffe92a9cc`.
- Rollback hold period before decommissioning the old environment: 3–7 days.
- Post-restore application-level verification uses a generic smoke test (create+save one `res.partner` record), not project-specific workflows — confirmed with the user, no specific flows to script.

---

### Task 1: oec.sh API client

**Files:**
- Modify: `requirements.txt` (add `requests>=2.31.0`)
- Create: `migration/__init__.py`
- Create: `migration/oecsh_client.py`
- Test: `tests/test_oecsh_client.py`

**Interfaces:**
- Produces: `migration.oecsh_client.OecshClient` with methods `list_servers() -> list`, `list_projects() -> list`, `list_environments(project_id: str) -> list`, `find_environment(name: str) -> dict`, `find_environment_by_id(env_id: str) -> dict`, `list_backups(env_id: str, status: str = None) -> list`, `status(env_id: str) -> dict`, `logs(env_id: str) -> dict`, `stop(env_id: str) -> None`, `start(env_id: str) -> None`, `restart(env_id: str) -> None`, `delete(env_id: str) -> None`. And `migration.oecsh_client.get_client(env_file: str = '.env.dev') -> OecshClient`, mirroring `seed.connection.get_client`.

- [ ] **Step 1: Add the `requests` dependency**

```bash
echo 'requests>=2.31.0' >> requirements.txt
pip install -r requirements.txt
```

- [ ] **Step 2: Write failing tests for discovery methods (servers/projects/environments)**

Create `tests/test_oecsh_client.py`:

```python
from unittest.mock import patch, MagicMock
import pytest
import requests

from migration.oecsh_client import OecshClient


def _resp(json_body):
    m = MagicMock()
    m.json.return_value = json_body
    m.raise_for_status.return_value = None
    return m


def test_list_servers_returns_data_list():
    client = OecshClient('testkey')
    body = {'data': [{'id': 's1', 'name': 'instance-1'}],
            'pagination': {'has_more': False, 'next_cursor': None, 'total': 1}}
    with patch.object(client._session, 'get', return_value=_resp(body)) as mock_get:
        servers = client.list_servers()
    assert servers == [{'id': 's1', 'name': 'instance-1'}]
    mock_get.assert_called_once_with('https://api.oec.sh/api/public/v1/servers', params={})


def test_list_projects_returns_data_list():
    client = OecshClient('testkey')
    body = {'data': [{'id': 'p1', 'name': 'adaminfo'}], 'pagination': {'total': 1}}
    with patch.object(client._session, 'get', return_value=_resp(body)):
        projects = client.list_projects()
    assert projects == [{'id': 'p1', 'name': 'adaminfo'}]


def test_list_environments_returns_plain_list():
    client = OecshClient('testkey')
    with patch.object(client._session, 'get', return_value=_resp([{'id': 'e1', 'name': 'env-1'}])):
        envs = client.list_environments('p1')
    assert envs == [{'id': 'e1', 'name': 'env-1'}]
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `pytest tests/test_oecsh_client.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'migration'` (or `ImportError`).

- [ ] **Step 4: Implement `OecshClient` discovery methods**

Create `migration/__init__.py` (empty file).

Create `migration/oecsh_client.py`:

```python
import os
import requests
from dotenv import load_dotenv

BASE_URL = 'https://api.oec.sh/api/public/v1'


class OecshClient:
    """Thin wrapper around the oec.sh public API (platform-level env/server ops).

    Covers what the public API exposes: server/project/environment discovery,
    backup listing, health status, logs, and env lifecycle (stop/start/restart/
    delete). Backup *creation* and restore-to-different-server have no public
    endpoint as of 2026-09 — those stay manual, dashboard-only.
    """

    def __init__(self, api_key: str):
        self._session = requests.Session()
        self._session.headers['Authorization'] = f'Bearer {api_key}'

    def _get(self, path: str, params: dict = None) -> dict:
        resp = self._session.get(f'{BASE_URL}{path}', params=params or {})
        resp.raise_for_status()
        return resp.json()

    def list_servers(self) -> list:
        return self._get('/servers')['data']

    def list_projects(self) -> list:
        return self._get('/projects')['data']

    def list_environments(self, project_id: str) -> list:
        return self._get(f'/projects/{project_id}/environments')

    def find_environment(self, name: str) -> dict:
        """Search every project on this account for an environment by exact name."""
        for project in self.list_projects():
            for env in self.list_environments(project['id']):
                if env['name'] == name:
                    return env
        raise ValueError(f'No environment named {name!r} found on this account')

    def find_environment_by_id(self, env_id: str) -> dict:
        for project in self.list_projects():
            for env in self.list_environments(project['id']):
                if env['id'] == env_id:
                    return env
        raise ValueError(f'No environment with id {env_id!r} found on this account')


def get_client(env_file: str = '.env.dev') -> OecshClient:
    load_dotenv(env_file, override=True)
    return OecshClient(os.environ['ODOO_PUBLIC_API_KEY'])
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `pytest tests/test_oecsh_client.py -v`
Expected: 3 passed.

- [ ] **Step 6: Write failing tests for `find_environment`, backups, status, logs**

Append to `tests/test_oecsh_client.py`:

```python
def test_find_environment_matches_by_name_across_projects():
    client = OecshClient('testkey')
    projects_resp = _resp({'data': [{'id': 'p1'}, {'id': 'p2'}], 'pagination': {}})
    envs_p1 = _resp([{'id': 'e1', 'name': 'other-env'}])
    envs_p2 = _resp([{'id': 'e2', 'name': 'target-env'}])
    with patch.object(client._session, 'get', side_effect=[projects_resp, envs_p1, envs_p2]):
        env = client.find_environment('target-env')
    assert env == {'id': 'e2', 'name': 'target-env'}


def test_find_environment_raises_when_not_found():
    client = OecshClient('testkey')
    with patch.object(client._session, 'get', return_value=_resp({'data': [], 'pagination': {}})):
        with pytest.raises(ValueError, match='No environment named'):
            client.find_environment('missing')


def test_find_environment_by_id_matches_across_projects():
    client = OecshClient('testkey')
    projects_resp = _resp({'data': [{'id': 'p1'}], 'pagination': {}})
    envs_p1 = _resp([{'id': 'e1', 'name': 'env-1'}])
    with patch.object(client._session, 'get', side_effect=[projects_resp, envs_p1]):
        env = client.find_environment_by_id('e1')
    assert env == {'id': 'e1', 'name': 'env-1'}


def test_list_backups_returns_items_list_and_passes_status_param():
    client = OecshClient('testkey')
    body = {'items': [{'id': 'b1', 'status': 'completed', 'completed_at': '2026-09-04T06:08:34Z'}]}
    with patch.object(client._session, 'get', return_value=_resp(body)) as mock_get:
        backups = client.list_backups('e1', status='completed')
    assert backups == [{'id': 'b1', 'status': 'completed', 'completed_at': '2026-09-04T06:08:34Z'}]
    mock_get.assert_called_once_with(
        'https://api.oec.sh/api/public/v1/environments/e1/backups', params={'status': 'completed'}
    )


def test_status_returns_flat_dict():
    client = OecshClient('testkey')
    body = {'environment_id': 'e1', 'status': 'running', 'container_running': True,
            'db_ready': True, 'http_ok': True}
    with patch.object(client._session, 'get', return_value=_resp(body)):
        result = client.status('e1')
    assert result == body


def test_logs_returns_flat_dict():
    client = OecshClient('testkey')
    body = {'task_id': None, 'log': 'INFO ok', 'lines': 1, 'truncated': False}
    with patch.object(client._session, 'get', return_value=_resp(body)):
        result = client.logs('e1')
    assert result == body
```

- [ ] **Step 7: Run tests to verify they fail**

Run: `pytest tests/test_oecsh_client.py -v`
Expected: 6 new tests FAIL with `AttributeError: 'OecshClient' object has no attribute 'list_backups'` (etc).

- [ ] **Step 8: Implement `list_backups`, `status`, `logs`**

Add to `migration/oecsh_client.py`, inside `OecshClient`:

```python
    def list_backups(self, env_id: str, status: str = None) -> list:
        params = {'status': status} if status else {}
        return self._get(f'/environments/{env_id}/backups', params=params)['items']

    def status(self, env_id: str) -> dict:
        return self._get(f'/environments/{env_id}/status')

    def logs(self, env_id: str) -> dict:
        return self._get(f'/environments/{env_id}/logs')
```

- [ ] **Step 9: Run tests to verify they pass**

Run: `pytest tests/test_oecsh_client.py -v`
Expected: 9 passed.

- [ ] **Step 10: Write failing tests for lifecycle methods (stop/start/restart/delete)**

Append to `tests/test_oecsh_client.py`:

```python
def test_stop_posts_and_raises_on_http_error():
    client = OecshClient('testkey')
    mock_resp = MagicMock()
    mock_resp.raise_for_status.side_effect = requests.HTTPError('500')
    with patch.object(client._session, 'post', return_value=mock_resp) as mock_post:
        with pytest.raises(requests.HTTPError):
            client.stop('e1')
    mock_post.assert_called_once_with('https://api.oec.sh/api/public/v1/environments/e1/stop')


def test_start_posts_to_start_endpoint():
    client = OecshClient('testkey')
    mock_resp = MagicMock()
    mock_resp.raise_for_status.return_value = None
    with patch.object(client._session, 'post', return_value=mock_resp) as mock_post:
        client.start('e1')
    mock_post.assert_called_once_with('https://api.oec.sh/api/public/v1/environments/e1/start')


def test_restart_posts_to_restart_endpoint():
    client = OecshClient('testkey')
    mock_resp = MagicMock()
    mock_resp.raise_for_status.return_value = None
    with patch.object(client._session, 'post', return_value=mock_resp) as mock_post:
        client.restart('e1')
    mock_post.assert_called_once_with('https://api.oec.sh/api/public/v1/environments/e1/restart')


def test_delete_calls_delete_endpoint():
    client = OecshClient('testkey')
    mock_resp = MagicMock()
    mock_resp.raise_for_status.return_value = None
    with patch.object(client._session, 'delete', return_value=mock_resp) as mock_delete:
        client.delete('e1')
    mock_delete.assert_called_once_with('https://api.oec.sh/api/public/v1/environments/e1')
```

- [ ] **Step 11: Run tests to verify they fail**

Run: `pytest tests/test_oecsh_client.py -v`
Expected: 4 new tests FAIL with `AttributeError`.

- [ ] **Step 12: Implement lifecycle methods**

Add to `migration/oecsh_client.py`, inside `OecshClient`:

```python
    def stop(self, env_id: str) -> None:
        resp = self._session.post(f'{BASE_URL}/environments/{env_id}/stop')
        resp.raise_for_status()

    def start(self, env_id: str) -> None:
        resp = self._session.post(f'{BASE_URL}/environments/{env_id}/start')
        resp.raise_for_status()

    def restart(self, env_id: str) -> None:
        resp = self._session.post(f'{BASE_URL}/environments/{env_id}/restart')
        resp.raise_for_status()

    def delete(self, env_id: str) -> None:
        resp = self._session.delete(f'{BASE_URL}/environments/{env_id}')
        resp.raise_for_status()
```

- [ ] **Step 13: Run full test file to verify all pass**

Run: `pytest tests/test_oecsh_client.py -v`
Expected: 13 passed.

- [ ] **Step 14: Live smoke-test against the real API (read-only, safe)**

```bash
python -c "from migration.oecsh_client import get_client; import json; c = get_client('.env.prod'); print(json.dumps(c.list_servers(), indent=2))"
```

Expected: real JSON list including a server with `"id": "1bf4ace1-9eea-4da9-a6b0-8497f6877c9a"`.

- [ ] **Step 15: Commit**

```bash
git add requirements.txt migration/ tests/test_oecsh_client.py
git commit -m "feat: add oec.sh API client (migration/oecsh_client.py)"
```

---

### Task 2: Migration CLI scripts (preflight, cutover check, lifecycle, log watch)

**Files:**
- Create: `migration/preflight.py`
- Create: `migration/cutover_check.py`
- Create: `migration/lifecycle.py`
- Create: `migration/watch_logs.py`
- Test: `tests/test_migration_cli.py`

**Interfaces:**
- Consumes: `migration.oecsh_client.get_client`, `OecshClient` methods from Task 1.
- Produces: `migration.preflight.run(env_name: str, target_server_id: str, env_file: str = '.env.prod') -> dict` (keys `target_server`, `environment`, `latest_backup`); `migration.cutover_check.run(old_env_id: str, new_env_id: str, env_file: str = '.env.prod') -> dict` (keys `old`, `new`, `url_matches`, `servers_differ`); `migration.lifecycle.run(action: str, env_id: str, confirm_name: str = None, env_file: str = '.env.prod') -> None`; `migration.watch_logs.run(env_id: str, env_file: str = '.env.prod') -> list[str]`. Each module also has a `main()` CLI entrypoint.

- [ ] **Step 1: Write failing tests for `preflight.run`**

Create `tests/test_migration_cli.py`:

```python
from unittest.mock import MagicMock, patch
import pytest


def test_preflight_reports_target_server_env_and_latest_backup():
    from migration import preflight
    mock_client = MagicMock()
    mock_client.list_servers.return_value = [
        {'id': 'srv1', 'name': 'instance-1', 'provider': 'custom', 'region': 'custom'},
    ]
    mock_client.find_environment.return_value = {
        'id': 'env1', 'name': 'adaminfo-prod-1139', 'server_id': 'srv-old', 'url': 'https://x',
    }
    mock_client.list_backups.return_value = [
        {'id': 'b1', 'completed_at': '2026-09-04T06:08:34Z', 'total_size': 5413180, 'is_verified': False},
        {'id': 'b2', 'completed_at': '2026-09-03T06:08:34Z', 'total_size': 5000000, 'is_verified': True},
    ]
    with patch('migration.preflight.get_client', return_value=mock_client):
        result = preflight.run('adaminfo-prod-1139', 'srv1')
    assert result['target_server']['id'] == 'srv1'
    assert result['latest_backup']['id'] == 'b1'  # most recent completed_at wins


def test_preflight_raises_when_target_server_unknown():
    from migration import preflight
    mock_client = MagicMock()
    mock_client.list_servers.return_value = []
    with patch('migration.preflight.get_client', return_value=mock_client):
        with pytest.raises(ValueError, match='not found'):
            preflight.run('adaminfo-prod-1139', 'missing-server')


def test_preflight_raises_when_no_completed_backups():
    from migration import preflight
    mock_client = MagicMock()
    mock_client.list_servers.return_value = [{'id': 'srv1', 'name': 'x', 'provider': 'p', 'region': 'r'}]
    mock_client.find_environment.return_value = {'id': 'env1', 'name': 'x', 'server_id': 's', 'url': 'u'}
    mock_client.list_backups.return_value = []
    with patch('migration.preflight.get_client', return_value=mock_client):
        with pytest.raises(ValueError, match='No completed backups'):
            preflight.run('x', 'srv1')
```

- [ ] **Step 2: Run to verify failure**

Run: `pytest tests/test_migration_cli.py -v`
Expected: FAIL, `ModuleNotFoundError: No module named 'migration.preflight'`.

- [ ] **Step 3: Implement `migration/preflight.py`**

```python
"""Pre-migration API preflight: confirm target server, find the env to migrate,
and report its most recent completed backup. Read-only — safe to run anytime.

Usage: python -m migration.preflight <env_name> <target_server_id>
"""
import sys
from migration.oecsh_client import get_client


def run(env_name: str, target_server_id: str, env_file: str = '.env.prod') -> dict:
    client = get_client(env_file)
    servers = {s['id']: s for s in client.list_servers()}
    if target_server_id not in servers:
        raise ValueError(f'Target server {target_server_id!r} not found on this account')
    target = servers[target_server_id]

    env = client.find_environment(env_name)
    backups = client.list_backups(env['id'], status='completed')
    if not backups:
        raise ValueError(f'No completed backups found for {env_name!r} — create one before restoring')
    latest = max(backups, key=lambda b: b['completed_at'])

    return {'target_server': target, 'environment': env, 'latest_backup': latest}


def main():
    if len(sys.argv) != 3:
        print('Usage: python -m migration.preflight <env_name> <target_server_id>')
        sys.exit(1)
    result = run(sys.argv[1], sys.argv[2])
    target, env, backup = result['target_server'], result['environment'], result['latest_backup']
    print(f"Target server OK: {target['name']} ({target['id']}, {target['provider']}/{target['region']})")
    print(f"Environment: {env['name']} ({env['id']}) on server {env['server_id']}, url {env['url']}")
    print(f"Latest completed backup: {backup['id']}, completed_at={backup['completed_at']}, "
          f"total_size={backup['total_size']} bytes, is_verified={backup['is_verified']}")


if __name__ == '__main__':
    main()
```

- [ ] **Step 4: Run to verify pass**

Run: `pytest tests/test_migration_cli.py -v`
Expected: 3 passed.

- [ ] **Step 5: Write failing tests for `cutover_check.run`**

Append to `tests/test_migration_cli.py`:

```python
def test_cutover_check_reports_url_match_and_server_diff():
    from migration import cutover_check
    mock_client = MagicMock()
    mock_client.find_environment_by_id.side_effect = [
        {'id': 'old', 'server_id': 's-old', 'url': 'https://adaminfo-prod-1139.apps.oec.sh'},
        {'id': 'new', 'server_id': 's-new', 'url': 'https://adaminfo-prod-1139.apps.oec.sh'},
    ]
    with patch('migration.cutover_check.get_client', return_value=mock_client):
        result = cutover_check.run('old', 'new')
    assert result['url_matches'] is True
    assert result['servers_differ'] is True
```

- [ ] **Step 6: Run to verify failure, then implement `migration/cutover_check.py`**

Run: `pytest tests/test_migration_cli.py -v` → expect `ModuleNotFoundError`.

```python
"""Compares two environments' server_id/url to confirm which server is actually
serving traffic — settles the URL/server takeover question after a restore.

Usage: python -m migration.cutover_check <old_env_id> <new_env_id>
"""
import sys
from migration.oecsh_client import get_client


def run(old_env_id: str, new_env_id: str, env_file: str = '.env.prod') -> dict:
    client = get_client(env_file)
    old_env = client.find_environment_by_id(old_env_id)
    new_env = client.find_environment_by_id(new_env_id)
    return {
        'old': old_env,
        'new': new_env,
        'url_matches': old_env['url'] == new_env['url'],
        'servers_differ': old_env['server_id'] != new_env['server_id'],
    }


def main():
    if len(sys.argv) != 3:
        print('Usage: python -m migration.cutover_check <old_env_id> <new_env_id>')
        sys.exit(1)
    result = run(sys.argv[1], sys.argv[2])
    print(f"Old env server_id={result['old']['server_id']} url={result['old']['url']}")
    print(f"New env server_id={result['new']['server_id']} url={result['new']['url']}")
    print(f"URLs match: {result['url_matches']}  Servers differ: {result['servers_differ']}")


if __name__ == '__main__':
    main()
```

Run: `pytest tests/test_migration_cli.py -v`
Expected: 4 passed.

- [ ] **Step 7: Write failing tests for `lifecycle.run`**

Append to `tests/test_migration_cli.py`:

```python
def test_lifecycle_delete_requires_matching_confirm_name():
    from migration import lifecycle
    mock_client = MagicMock()
    mock_client.find_environment_by_id.return_value = {'id': 'e1', 'name': 'adaminfo-prod-1139'}
    with patch('migration.lifecycle.get_client', return_value=mock_client):
        with pytest.raises(ValueError, match='to match exactly'):
            lifecycle.run('delete', 'e1', confirm_name='wrong-name')
    mock_client.delete.assert_not_called()


def test_lifecycle_delete_proceeds_when_confirm_name_matches():
    from migration import lifecycle
    mock_client = MagicMock()
    mock_client.find_environment_by_id.return_value = {'id': 'e1', 'name': 'adaminfo-prod-1139'}
    with patch('migration.lifecycle.get_client', return_value=mock_client):
        lifecycle.run('delete', 'e1', confirm_name='adaminfo-prod-1139')
    mock_client.delete.assert_called_once_with('e1')


def test_lifecycle_stop_calls_client_stop():
    from migration import lifecycle
    mock_client = MagicMock()
    with patch('migration.lifecycle.get_client', return_value=mock_client):
        lifecycle.run('stop', 'e1')
    mock_client.stop.assert_called_once_with('e1')


def test_lifecycle_rejects_unknown_action():
    from migration import lifecycle
    mock_client = MagicMock()
    with patch('migration.lifecycle.get_client', return_value=mock_client):
        with pytest.raises(ValueError, match='Unknown action'):
            lifecycle.run('destroy', 'e1')
```

- [ ] **Step 8: Run to verify failure, then implement `migration/lifecycle.py`**

Run: `pytest tests/test_migration_cli.py -v` → expect `ModuleNotFoundError`.

```python
"""Guarded stop/start/delete for an oec.sh environment. Delete requires the
environment's real name passed back as --confirm — destructive, no undo via
the public API.

Usage: python -m migration.lifecycle <stop|start|delete> <env_id> [--confirm <name>]
"""
import sys
from migration.oecsh_client import get_client


def run(action: str, env_id: str, confirm_name: str = None, env_file: str = '.env.prod') -> None:
    client = get_client(env_file)
    if action == 'stop':
        client.stop(env_id)
    elif action == 'start':
        client.start(env_id)
    elif action == 'delete':
        env = client.find_environment_by_id(env_id)
        if confirm_name != env['name']:
            raise ValueError(
                f"delete requires --confirm {env['name']!r} to match exactly (got {confirm_name!r})"
            )
        client.delete(env_id)
    else:
        raise ValueError(f'Unknown action {action!r} — expected stop, start, or delete')


def main():
    if len(sys.argv) < 3:
        print('Usage: python -m migration.lifecycle <stop|start|delete> <env_id> [--confirm <name>]')
        sys.exit(1)
    action, env_id = sys.argv[1], sys.argv[2]
    confirm_name = sys.argv[4] if len(sys.argv) > 4 and sys.argv[3] == '--confirm' else None
    run(action, env_id, confirm_name)
    print(f'{action} completed for {env_id}')


if __name__ == '__main__':
    main()
```

Run: `pytest tests/test_migration_cli.py -v`
Expected: 8 passed.

- [ ] **Step 9: Write failing test for `watch_logs.run`**

Append to `tests/test_migration_cli.py`:

```python
def test_watch_logs_flags_error_and_critical_lines():
    from migration import watch_logs
    mock_client = MagicMock()
    mock_client.logs.return_value = {'log': 'INFO ok\nERROR boom\nCRITICAL fire\nINFO fine'}
    with patch('migration.watch_logs.get_client', return_value=mock_client):
        flagged = watch_logs.run('e1')
    assert flagged == ['ERROR boom', 'CRITICAL fire']


def test_watch_logs_returns_empty_when_clean():
    from migration import watch_logs
    mock_client = MagicMock()
    mock_client.logs.return_value = {'log': 'INFO ok\nINFO fine'}
    with patch('migration.watch_logs.get_client', return_value=mock_client):
        flagged = watch_logs.run('e1')
    assert flagged == []
```

- [ ] **Step 10: Run to verify failure, then implement `migration/watch_logs.py`**

Run: `pytest tests/test_migration_cli.py -v` → expect `ModuleNotFoundError`.

```python
"""Polls an environment's logs for ERROR/CRITICAL lines. Intended to be run
periodically during the post-restore hold window (manually invoked, or on a
loop) rather than block synchronously for 24-48h.

Usage: python -m migration.watch_logs <env_id>
"""
import sys
from migration.oecsh_client import get_client

_FLAGS = ('ERROR', 'CRITICAL')


def run(env_id: str, env_file: str = '.env.prod') -> list:
    client = get_client(env_file)
    log_text = client.logs(env_id)['log']
    return [line for line in log_text.splitlines() if any(flag in line for flag in _FLAGS)]


def main():
    if len(sys.argv) != 2:
        print('Usage: python -m migration.watch_logs <env_id>')
        sys.exit(1)
    flagged = run(sys.argv[1])
    if flagged:
        print(f'{len(flagged)} flagged line(s):')
        for line in flagged:
            print(f'  {line}')
        sys.exit(1)
    print('No ERROR/CRITICAL lines found.')


if __name__ == '__main__':
    main()
```

Run: `pytest tests/test_migration_cli.py -v`
Expected: 10 passed.

- [ ] **Step 11: Commit**

```bash
git add migration/preflight.py migration/cutover_check.py migration/lifecycle.py migration/watch_logs.py tests/test_migration_cli.py
git commit -m "feat: add migration CLI scripts (preflight, cutover check, lifecycle, log watch)"
```

---

### Task 3: Pre-migration prep — API preflight + Playwright baseline

**Files:**
- Create: `docs/migration-log-2026-09-04-adaminfo-prod-1139.md`
- Create: `docs/superpowers/specs/migration-baseline/baseline.md`
- Create: `docs/superpowers/specs/migration-baseline/apps-installed-old.png`
- Create: `docs/superpowers/specs/migration-baseline/scheduled-actions-old.png`

**Interfaces:**
- Consumes: `migration.preflight.main` (Task 2) via `python -m migration.preflight`.

- [ ] **Step 1: Run preflight against the live account**

```bash
python -m migration.preflight adaminfo-prod-1139 1bf4ace1-9eea-4da9-a6b0-8497f6877c9a
```

Expected: prints target server OK, the environment's current `server_id`/`url`, and a completed backup with today's `completed_at`. If the newest completed backup is stale (not from today), create a fresh one first via oec.sh dashboard → `adaminfo-prod-1139` → Backup Management tab → Create Backup, then re-run this command until it reports a fresh one.

- [ ] **Step 2: Start the migration log**

Create `docs/migration-log-2026-09-04-adaminfo-prod-1139.md` with a `## Preflight` section pasting the exact output of Step 1 (server, environment, backup id/timestamp/size).

- [ ] **Step 3: Playwright — capture installed module list on the old env**

Using the Playwright MCP tools:
1. `browser_navigate` to `https://adaminfo-prod-1139.apps.oec.sh/web/login`.
2. Log in with `ODOO_LOGIN_USERNAME` / `ODOO_LOGIN_PASSWORD` from `.env.prod`.
3. `browser_navigate` to `https://adaminfo-prod-1139.apps.oec.sh/odoo/apps`, filter to "Installed".
4. `browser_snapshot` — read off every installed module's name and version from the accessibility tree.
5. `browser_take_screenshot` (`fullPage: true`), save to `docs/superpowers/specs/migration-baseline/apps-installed-old.png`.

- [ ] **Step 4: Playwright — capture Scheduled Actions on the old env**

1. Append `?debug=1` to the current URL (or use the General Settings "Activate the developer mode" link) to enable dev mode.
2. Navigate to Settings → Technical → Automation → Scheduled Actions.
3. `browser_snapshot` — read off every job's name and active/inactive state.
4. `browser_take_screenshot` (`fullPage: true`), save to `docs/superpowers/specs/migration-baseline/scheduled-actions-old.png`.

- [ ] **Step 5: Write the baseline record**

Create `docs/superpowers/specs/migration-baseline/baseline.md` listing, as plain text extracted from the two snapshots above: every installed module name + version, and every scheduled action name + active state. This is what Task 5's post-restore diff compares against.

- [ ] **Step 6: Commit**

```bash
git add docs/migration-log-2026-09-04-adaminfo-prod-1139.md docs/superpowers/specs/migration-baseline/
git commit -m "docs: capture pre-migration preflight + baseline for adaminfo-prod-1139"
```

---

### Task 4: Execute restore (manual) and record the new environment

If the native restore errors out or doesn't support this server pair, fall back to the manual
`pg_dump`/`rsync` path documented in the spec's Approach section — not built here, since it's a
contingency, not the primary path.

**Files:**
- Modify: `docs/migration-log-2026-09-04-adaminfo-prod-1139.md`

- [ ] **Step 1: Restore to the new server** *(manual, oec.sh dashboard — no API for this)*

1. Open `adaminfo-prod-1139` in the oec.sh dashboard → Backup Management tab.
2. Select the backup recorded in Task 3's preflight output.
3. Click Restore → target **"Different Server"** → select `instance-20260822-0943` (`1bf4ace1-9eea-4da9-a6b0-8497f6877c9a`).
4. Name the new environment `adaminfo-prod-1139-oracle` (distinct from the still-live old env's name).
5. Confirm and wait for the dashboard to show the restore complete. Watch the dashboard's
   deploy/restore log for `ModuleNotFoundError: No module named 'OpenSSL'` (`GEN_EMAIL/skew`) —
   a known oec.sh Odoo 18 platform gap (dep-check pins `cryptography` but not `pyOpenSSL`) that
   can surface if the restore triggers a fresh container build. If it appears: add a root
   `requirements.txt` entry pinning `pyOpenSSL>=24.0.0` to the `adaminfo-odoo-v1` repo, commit,
   push to `main`, and retry.
6. Leave `adaminfo-prod-1139` (old) running untouched — it's the rollback point until Task 7.

- [ ] **Step 2: Resolve the new environment's id/url/server via the API**

```bash
python -c "from migration.oecsh_client import get_client; import json; print(json.dumps(get_client('.env.prod').find_environment('adaminfo-prod-1139-oracle'), indent=2))"
```

Expected: JSON with the new environment's `id`, `server_id` (should equal `1bf4ace1-9eea-4da9-a6b0-8497f6877c9a`), and `url`.

- [ ] **Step 3: Record it in the migration log**

Append a `## Restore` section to `docs/migration-log-2026-09-04-adaminfo-prod-1139.md` with: backup id used, new environment name/id/server_id/url, restore completion time.

- [ ] **Step 4: Commit**

```bash
git add docs/migration-log-2026-09-04-adaminfo-prod-1139.md
git commit -m "docs: record adaminfo-prod-1139-oracle restore result"
```

---

### Task 5: Post-restore verification

**Files:**
- Modify: `docs/migration-log-2026-09-04-adaminfo-prod-1139.md`
- Create: `docs/superpowers/specs/migration-baseline/apps-installed-new.png`
- Create: `docs/superpowers/specs/migration-baseline/scheduled-actions-new.png`
- Create: `docs/superpowers/specs/migration-baseline/smoke-test-new.png`

**Interfaces:**
- Consumes: new environment id from Task 4 Step 2 (referred to below as `<new_env_id>`), baseline from Task 3.

- [ ] **Step 1: API health check**

```bash
python -c "from migration.oecsh_client import get_client; import json; print(json.dumps(get_client('.env.prod').status('<new_env_id>'), indent=2))"
```

Expected: `container_running`, `db_ready`, `http_ok` all `true`.

- [ ] **Step 2: Playwright — login proof**

`browser_navigate` to the new env's `/web/login` (URL from Task 4), log in as admin (`ODOO_LOGIN_USERNAME`/`PASSWORD`). If a non-admin user exists on this instance, log in as that user too (new browser context/logout-login). `browser_snapshot` to confirm the logged-in home screen, not an error page.

- [ ] **Step 3: Playwright — module list diff**

Repeat Task 3 Step 3 against the new env, screenshot to `apps-installed-new.png`. Diff the module name/version list against `baseline.md`. Record any difference in the migration log — expected result is no differences.

- [ ] **Step 4: Playwright — Scheduled Actions diff**

Repeat Task 3 Step 4 against the new env, screenshot to `scheduled-actions-new.png`. Diff against `baseline.md`, specifically checking that nothing flipped from active to inactive during the restore. Record the result.

- [ ] **Step 5: Playwright — generic smoke test (create + save)**

1. Navigate to the Contacts app on the new env.
2. Create a new contact named `[MIGRATION-TEST] verify-2026-09-04`, save it.
3. Reload the page, `browser_snapshot` to confirm the record persisted (not just an in-memory save).
4. Delete the test contact afterward so it doesn't linger as junk data.
5. Screenshot the saved-record state (before deleting) to `smoke-test-new.png`.

- [ ] **Step 6: Playwright — PDF report check**

Look for any record with a working Print action reachable from the record's action menu (check a Contact, or whatever is available on this instance via `browser_snapshot`). If one exists: trigger it, use `browser_network_requests` to confirm a `200` response with `content-type: application/pdf`. If none is reachable in a quick check, record "no printable report available on this instance" in the migration log instead of forcing one.

- [ ] **Step 7: Playwright — attachment check**

Open a record already known (from the baseline pass) to carry an attachment or image, confirm it renders correctly in a screenshot (a broken attachment shows a broken-image icon — easy to catch visually).

- [ ] **Step 8: Playwright — email UI check (partial)**

Navigate to Settings → Technical → Email → Outgoing Mail Servers, select the configured server, click "Test Connection". Confirm a success message, no error banner. Record explicitly in the log that this does **not** verify actual delivery — that would require a manual inbox check.

- [ ] **Step 9: Record results**

Append a `## Post-restore verification` section to the migration log with pass/fail for each of Steps 1–8 and links to the three new screenshots.

- [ ] **Step 10: Commit**

```bash
git add docs/migration-log-2026-09-04-adaminfo-prod-1139.md docs/superpowers/specs/migration-baseline/
git commit -m "docs: record post-restore verification for adaminfo-prod-1139-oracle"
```

---

### Task 6: Cutover check and rollback hold period

**Files:**
- Modify: `docs/migration-log-2026-09-04-adaminfo-prod-1139.md`

**Interfaces:**
- Consumes: `migration.cutover_check.main`, `migration.watch_logs.main` (Task 2).

- [ ] **Step 1: Run the cutover check**

```bash
python -m migration.cutover_check cca3f63b-f16d-4b42-85f0-fb11827aa263 <new_env_id>
```

Expected output shows both envs' `server_id` and `url`. Interpret: if `url_matches` is `True`, the new env is already reachable under the expected slug; if `False`, the old env's slug won't free up until it's stopped in Task 7 — either way this settles the previously-open cutover-timing question from the spec.

- [ ] **Step 2: Record the cutover result and set the hold window**

Append a `## Cutover check` section to the migration log with the command output and its interpretation. Set a hold-period end date 3–7 days out and write it down.

- [ ] **Step 3: Poll logs during the hold window**

Run periodically (at least once a day) during the hold window:

```bash
python -m migration.watch_logs <new_env_id>
```

Expected: `No ERROR/CRITICAL lines found.` (exit 0). If it exits non-zero, investigate before proceeding — do not move to Task 7 with unresolved flagged lines.

- [ ] **Step 4: Decision gate**

If Task 5's checklist found a real defect, or `watch_logs` surfaces unresolved errors during the hold window: **stop here** — do not proceed to Task 7. The old environment is still running untouched; that's the rollback. Record what failed in the migration log and treat this plan as paused pending a fix, not complete.

If the hold window passes clean, proceed to Task 7.

- [ ] **Step 5: Commit**

```bash
git add docs/migration-log-2026-09-04-adaminfo-prod-1139.md
git commit -m "docs: record cutover check and hold-window log watch for adaminfo-prod-1139-oracle"
```

---

### Task 7: Decommission the old environment

**Files:**
- Modify: `docs/migration-log-2026-09-04-adaminfo-prod-1139.md`
- Modify: `.env.prod` (not committed — gitignored; update locally so future tooling points at the new environment)

**Interfaces:**
- Consumes: `migration.lifecycle.main` (Task 2).

- [ ] **Step 1: Stop the old environment**

```bash
python -m migration.lifecycle stop cca3f63b-f16d-4b42-85f0-fb11827aa263
```

- [ ] **Step 2: Re-verify the new environment is unaffected**

```bash
python -c "from migration.oecsh_client import get_client; import json; print(json.dumps(get_client('.env.prod').status('<new_env_id>'), indent=2))"
```

Expected: still `container_running`, `db_ready`, `http_ok` all `true` — confirms the new env doesn't depend on the old one still running.

- [ ] **Step 3: Delete the old environment**

Only once fully confident (past the hold window, Step 2 clean):

```bash
python -m migration.lifecycle delete cca3f63b-f16d-4b42-85f0-fb11827aa263 --confirm adaminfo-prod-1139
```

- [ ] **Step 4: Update local `.env.prod`**

In `/Users/ferko/development/adaminfo-odoo-v1/.env.prod`, update `ODOO_DB` to the new environment's id, `SSH_HOST`/`ODOO_ADDON_PATH` to the new server's values (from the oec.sh dashboard's environment settings — SSH details aren't in the public API), and update the comment noting the target URL if it changed. This file is gitignored — edit locally, do not commit it.

- [ ] **Step 5: Close out the migration log**

Append a final `## Decommission` section: stop/delete timestamps, confirmation the new env is the sole live environment for this project, and a one-line summary of the whole migration (start date, end date, any issues hit).

- [ ] **Step 6: Commit**

```bash
git add docs/migration-log-2026-09-04-adaminfo-prod-1139.md
git commit -m "docs: close out adaminfo-prod-1139 Oracle Cloud migration"
```

---

## Reuse note

This plan's `migration/` package is written generically (env name/id/server id are all parameters, nothing hardcoded past Task 1/2's default `.env.prod`) — the same scripts apply directly to migrating `dentari-prod-2031` or `dentari-dev-8780` later, swapping only the ids/names used in Tasks 3–7's commands.
