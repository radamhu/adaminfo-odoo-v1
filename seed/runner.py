import argparse
import sys

from seed.connection import get_client
from seed import products, contacts, crm, sale, project, invoicing, timesheet, knowledge

SEED_ORDER = ['products', 'contacts', 'crm', 'sale', 'project', 'invoicing', 'timesheet', 'knowledge']
WIPE_ORDER = list(reversed(SEED_ORDER))


class _ModulesDict(dict):
    """A dict that looks up module values from the current globals() for testing compatibility."""
    def __getitem__(self, key):
        return globals()[key]

    def __contains__(self, key):
        return key in globals()


MODULES = _ModulesDict()


def main() -> None:
    parser = argparse.ArgumentParser(description='Seed or wipe Odoo mock data')
    parser.add_argument('--wipe', action='store_true',
                        help='Wipe seeded data only (no re-seed)')
    parser.add_argument('--only', metavar='MODULE',
                        help='Target a single module')
    args = parser.parse_args()

    if args.only and args.only not in MODULES:
        print(f'Unknown module: {args.only}. Available: {", ".join(SEED_ORDER)}',
              file=sys.stderr)
        sys.exit(1)

    client = get_client()

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
