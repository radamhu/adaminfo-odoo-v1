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
