from unittest.mock import patch, MagicMock
import pytest


def _make_client(uid=7):
    with patch('xmlrpc.client.ServerProxy') as mock_proxy:
        mock_common = MagicMock()
        mock_common.authenticate.return_value = uid
        mock_models = MagicMock()
        mock_proxy.side_effect = [mock_common, mock_models]
        from seed.connection import OdooClient
        client = OdooClient('http://localhost:8069', 'testdb', 'admin', 'pass')
    return client, mock_common, mock_models


def test_authenticate_sets_uid():
    client, _, _ = _make_client(uid=7)
    assert client.uid == 7


def test_authenticate_raises_on_failure():
    with patch('xmlrpc.client.ServerProxy') as mock_proxy:
        mock_common = MagicMock()
        mock_common.authenticate.return_value = 0
        mock_models = MagicMock()
        mock_proxy.side_effect = [mock_common, mock_models]
        from seed.connection import OdooClient
        with pytest.raises(ValueError, match='Authentication failed'):
            OdooClient('http://localhost:8069', 'testdb', 'admin', 'wrong')


def test_search_read_calls_execute_kw():
    client, _, mock_models = _make_client()
    mock_models.execute_kw.return_value = [{'id': 1, 'name': 'Test'}]
    result = client.search_read('res.partner', [('name', '=', 'Test')], ['id', 'name'])
    assert result == [{'id': 1, 'name': 'Test'}]
    mock_models.execute_kw.assert_called_once_with(
        'testdb', 7, 'pass', 'res.partner', 'search_read',
        [[('name', '=', 'Test')]], {'fields': ['id', 'name'], 'limit': 100}
    )


def test_create_returns_new_id():
    client, _, mock_models = _make_client()
    mock_models.execute_kw.return_value = 42
    new_id = client.create('res.partner', {'name': 'New Partner'})
    assert new_id == 42
    mock_models.execute_kw.assert_called_once_with(
        'testdb', 7, 'pass', 'res.partner', 'create', [{'name': 'New Partner'}], {}
    )


def test_unlink_calls_execute_kw():
    client, _, mock_models = _make_client()
    mock_models.execute_kw.return_value = True
    result = client.unlink('res.partner', [1, 2, 3])
    assert result is True
    mock_models.execute_kw.assert_called_once_with(
        'testdb', 7, 'pass', 'res.partner', 'unlink', [[1, 2, 3]], {}
    )


def test_execute_calls_method_with_ids():
    client, _, mock_models = _make_client()
    mock_models.execute_kw.return_value = True
    client.execute('sale.order', 'action_confirm', [5, 6])
    mock_models.execute_kw.assert_called_once_with(
        'testdb', 7, 'pass', 'sale.order', 'action_confirm', [[5, 6]], {}
    )
