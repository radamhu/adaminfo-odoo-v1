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
