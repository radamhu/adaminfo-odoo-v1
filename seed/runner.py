import argparse
import sys

from seed.connection import get_client
from seed import products, contacts, crm, sale, project, invoicing, timesheet, knowledge
from seed import prod_sales

SEED_ORDER = ['products', 'contacts', 'crm', 'sale', 'project', 'invoicing', 'timesheet', 'knowledge']
WIPE_ORDER = list(reversed(SEED_ORDER))

_EXTRA = {'prod_sales': prod_sales}


class _ModulesDict(dict):
    """Proxies __getitem__ to globals() so test patches on module-level names are visible."""
    def __getitem__(self, key):
        if key in _EXTRA:
            return _EXTRA[key]
        return globals()[key]

    def __contains__(self, key):
        return key in SEED_ORDER or key in _EXTRA


MODULES = _ModulesDict()


def main() -> None:
    parser = argparse.ArgumentParser(description='Seed or wipe Odoo mock data')
    parser.add_argument('--wipe', action='store_true',
                        help='Wipe seeded data only (no re-seed)')
    parser.add_argument('--only', metavar='MODULE',
                        help='Target a single module')
    parser.add_argument('--env', default='.env.dev', metavar='ENV_FILE',
                        help='dotenv file to load (default: .env.dev)')
    args = parser.parse_args()

    available = ', '.join(SEED_ORDER + list(_EXTRA))
    if args.only and args.only not in MODULES:
        print(f'Unknown module: {args.only}. Available: {available}', file=sys.stderr)
        sys.exit(1)

    client = get_client(env_file=args.env)

    if args.wipe:
        order = [args.only] if args.only else WIPE_ORDER
        for name in order:
            print(f'  Wiping {name}...')
            module = MODULES[name]
            module.wipe(client)
    else:
        order = [args.only] if args.only else SEED_ORDER
        for name in order:
            print(f'  Seeding {name}...')
            module = MODULES[name]
            module.seed(client)


if __name__ == '__main__':
    main()
