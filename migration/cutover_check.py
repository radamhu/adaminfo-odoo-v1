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
