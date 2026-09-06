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
