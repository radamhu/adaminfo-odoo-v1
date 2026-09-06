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
