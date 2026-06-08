from unittest.mock import MagicMock, patch
import pytest


_MODULE_NAMES = ['products', 'contacts', 'crm', 'sale', 'project', 'invoicing', 'timesheet', 'knowledge']


def _run(args: list):
    ctx = {name: patch(f'seed.runner.{name}') for name in _MODULE_NAMES}
    ctx['get_client'] = patch('seed.runner.get_client', return_value=MagicMock())
    mocks = {k: patcher.start() for k, patcher in ctx.items()}
    try:
        with patch('sys.argv', ['runner.py'] + args):
            from seed.runner import main
            main()
    finally:
        for patcher in ctx.values():
            patcher.stop()
    ctx.pop('get_client')
    return mocks


def test_default_seeds_all_in_order():
    mocks = _run([])
    for name in _MODULE_NAMES:
        mocks[name].seed.assert_called_once()
        mocks[name].wipe.assert_not_called()


def test_wipe_flag_wipes_all_no_seed():
    mocks = _run(['--wipe'])
    for name in _MODULE_NAMES:
        mocks[name].wipe.assert_called_once()
        mocks[name].seed.assert_not_called()


def test_only_flag_seeds_single_module():
    mocks = _run(['--only', 'crm'])
    mocks['crm'].seed.assert_called_once()
    mocks['contacts'].seed.assert_not_called()
    mocks['sale'].seed.assert_not_called()


def test_wipe_only_flag_wipes_single_module():
    mocks = _run(['--wipe', '--only', 'crm'])
    mocks['crm'].wipe.assert_called_once()
    mocks['contacts'].wipe.assert_not_called()
    mocks['crm'].seed.assert_not_called()


def test_unknown_module_exits_with_error():
    with patch('sys.argv', ['runner.py', '--only', 'nonexistent']), \
         patch('seed.runner.get_client', return_value=MagicMock()):
        from seed.runner import main
        with pytest.raises(SystemExit) as exc:
            main()
        assert exc.value.code == 1
