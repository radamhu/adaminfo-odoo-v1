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
