import argparse
import sys

from seed.connection import get_client
from seed import products, contacts, crm, sale, project, invoicing, timesheet, knowledge

SEED_ORDER = ['products', 'contacts', 'crm', 'sale', 'project', 'invoicing', 'timesheet', 'knowledge']
WIPE_ORDER = list(reversed(SEED_ORDER))

# All available module names for validation
ALL_MODULES = set(SEED_ORDER)


def main() -> None:
    parser = argparse.ArgumentParser(description='Seed or wipe Odoo mock data')
    parser.add_argument('--wipe', action='store_true',
                        help='Wipe seeded data only (no re-seed)')
    parser.add_argument('--only', metavar='MODULE',
                        help='Target a single module')
    args = parser.parse_args()

    if args.only and args.only not in ALL_MODULES:
        print(f'Unknown module: {args.only}. Available: {", ".join(SEED_ORDER)}',
              file=sys.stderr)
        sys.exit(1)

    client = get_client()

    if args.wipe:
        order = [args.only] if args.only else WIPE_ORDER
        for name in order:
            print(f'  Wiping {name}...')
            module = globals()[name]
            module.wipe(client)
    else:
        order = [args.only] if args.only else SEED_ORDER
        for name in order:
            print(f'  Seeding {name}...')
            module = globals()[name]
            module.seed(client)


if __name__ == '__main__':
    main()
