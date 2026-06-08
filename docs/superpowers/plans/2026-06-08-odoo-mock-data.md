# Odoo Mock Data Seeder — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a CLI-driven XML-RPC seeder that creates 20–50 realistic mock records per Odoo module across 7 modules (+ 1 prerequisite) for development/testing.

**Architecture:** Module-per-file: each Odoo module has a seeder file exposing `seed(client)` and `wipe(client)`. A shared `OdooClient` wraps all XML-RPC calls. A CLI runner in `seed/runner.py` handles `--wipe` and `--only` flags with explicit dependency ordering.

**Tech Stack:** Python 3.9+, `xmlrpc.client` (stdlib), `python-dotenv`, `pytest`

---

## File Map

| File | Responsibility |
|---|---|
| `requirements.txt` | runtime + dev dependencies |
| `seed/__init__.py` | package marker |
| `seed/connection.py` | `OdooClient` class + `get_client()` factory |
| `seed/products.py` | `product.template` — prerequisite for sale & invoicing |
| `seed/contacts.py` | `res.partner` — foundation for all other seeders |
| `seed/crm.py` | `crm.lead` — leads + opportunities |
| `seed/sale.py` | `sale.order` + `sale.order.line` |
| `seed/project.py` | `project.project` + `project.task` |
| `seed/invoicing.py` | `account.move` — customer invoices |
| `seed/timesheet.py` | `account.analytic.line` |
| `seed/knowledge.py` | `knowledge.article` |
| `seed/runner.py` | CLI entry point |
| `tests/__init__.py` | package marker |
| `tests/test_connection.py` | `OdooClient` unit tests |
| `tests/test_products.py` | products seeder tests |
| `tests/test_contacts.py` | contacts seeder tests |
| `tests/test_crm.py` | CRM seeder tests |
| `tests/test_sale.py` | sale seeder tests |
| `tests/test_project.py` | project seeder tests |
| `tests/test_invoicing.py` | invoicing seeder tests |
| `tests/test_timesheet.py` | timesheet seeder tests |
| `tests/test_knowledge.py` | knowledge seeder tests |
| `tests/test_runner.py` | runner CLI tests |

---

## Task 1: Project scaffolding

**Files:**
- Create: `requirements.txt`
- Create: `seed/__init__.py`
- Create: `tests/__init__.py`

- [ ] **Step 1: Create `requirements.txt`**

```
python-dotenv>=1.0.0
pytest>=7.0.0
```

- [ ] **Step 2: Create `seed/__init__.py`**

```python
```
(empty file)

- [ ] **Step 3: Create `tests/__init__.py`**

```python
```
(empty file)

- [ ] **Step 4: Install dependencies**

```bash
pip install -r requirements.txt
```

Expected: packages install without error.

- [ ] **Step 5: Commit**

```bash
git add requirements.txt seed/__init__.py tests/__init__.py
git commit -m "chore: scaffold seed package and test directory"
```

---

## Task 2: OdooClient (`seed/connection.py`)

**Files:**
- Create: `tests/test_connection.py`
- Create: `seed/connection.py`

- [ ] **Step 1: Write `tests/test_connection.py`**

```python
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
```

- [ ] **Step 2: Run tests — verify they all fail**

```bash
pytest tests/test_connection.py -v
```

Expected: `ImportError` or `ModuleNotFoundError` for `seed.connection`.

- [ ] **Step 3: Write `seed/connection.py`**

```python
import os
import xmlrpc.client
from urllib.parse import urlparse
from dotenv import load_dotenv


class OdooClient:
    def __init__(self, url: str, db: str, username: str, password: str):
        self.url = url.rstrip('/')
        self.db = db
        self.password = password
        self._common = xmlrpc.client.ServerProxy(f'{self.url}/xmlrpc/2/common')
        self._models = xmlrpc.client.ServerProxy(f'{self.url}/xmlrpc/2/object')
        self.uid = self._common.authenticate(db, username, password, {})
        if not self.uid:
            raise ValueError(f'Authentication failed for user {username}')

    def search_read(self, model: str, domain: list, fields: list, limit: int = 100) -> list:
        return self._models.execute_kw(
            self.db, self.uid, self.password, model, 'search_read',
            [domain], {'fields': fields, 'limit': limit}
        )

    def create(self, model: str, vals: dict) -> int:
        return self._models.execute_kw(
            self.db, self.uid, self.password, model, 'create', [vals], {}
        )

    def write(self, model: str, ids: list, vals: dict) -> bool:
        return self._models.execute_kw(
            self.db, self.uid, self.password, model, 'write', [ids, vals], {}
        )

    def unlink(self, model: str, ids: list) -> bool:
        return self._models.execute_kw(
            self.db, self.uid, self.password, model, 'unlink', [ids], {}
        )

    def execute(self, model: str, method: str, ids: list, **kwargs) -> object:
        return self._models.execute_kw(
            self.db, self.uid, self.password, model, method, [ids], kwargs
        )


def _detect_db(url: str) -> str:
    base = url.rstrip('/')
    try:
        dbs = xmlrpc.client.ServerProxy(f'{base}/xmlrpc/2/db').list()
        if dbs:
            return dbs[0]
    except Exception:
        pass
    hostname = urlparse(url).hostname or ''
    return hostname.split('.')[0]


def get_client() -> OdooClient:
    load_dotenv('.env.dev')
    url = os.environ['ODOO_ERP_URL']
    username = os.environ['ODOO_LOGIN_USERNAME']
    password = os.environ['ODOO_LOGIN_PASSWORD']
    db = os.environ.get('ODOO_DB') or _detect_db(url)
    return OdooClient(url, db, username, password)
```

- [ ] **Step 4: Run tests — verify they all pass**

```bash
pytest tests/test_connection.py -v
```

Expected: 6 tests pass.

- [ ] **Step 5: Commit**

```bash
git add seed/connection.py tests/test_connection.py
git commit -m "feat: add OdooClient XML-RPC wrapper"
```

---

## Task 3: Products seeder (`seed/products.py`)

**Files:**
- Create: `tests/test_products.py`
- Create: `seed/products.py`

- [ ] **Step 1: Write `tests/test_products.py`**

```python
from unittest.mock import MagicMock, call
from seed.products import seed, wipe, PRODUCTS


def test_seed_creates_all_when_none_exist():
    client = MagicMock()
    client.search_read.return_value = []
    seed(client)
    client.search_read.assert_called_once_with(
        'product.template', [('name', 'like', '[SEED]')], ['name']
    )
    assert client.create.call_count == len(PRODUCTS)
    first_call = client.create.call_args_list[0]
    assert first_call[0][0] == 'product.template'
    assert first_call[0][1]['name'] == '[SEED] Consulting'


def test_seed_skips_existing_products():
    client = MagicMock()
    client.search_read.return_value = [{'name': p['name']} for p in PRODUCTS]
    seed(client)
    client.create.assert_not_called()


def test_seed_creates_only_missing():
    client = MagicMock()
    client.search_read.return_value = [{'name': '[SEED] Consulting'}]
    seed(client)
    assert client.create.call_count == len(PRODUCTS) - 1


def test_wipe_unlinks_found_records():
    client = MagicMock()
    client.search_read.return_value = [{'id': 1}, {'id': 2}, {'id': 3}]
    wipe(client)
    client.search_read.assert_called_once_with(
        'product.template', [('name', 'like', '[SEED]')], ['id']
    )
    client.unlink.assert_called_once_with('product.template', [1, 2, 3])


def test_wipe_does_nothing_when_empty():
    client = MagicMock()
    client.search_read.return_value = []
    wipe(client)
    client.unlink.assert_not_called()
```

- [ ] **Step 2: Run tests — verify they fail**

```bash
pytest tests/test_products.py -v
```

Expected: `ImportError` for `seed.products`.

- [ ] **Step 3: Write `seed/products.py`**

```python
PRODUCTS = [
    {'name': '[SEED] Consulting',         'type': 'service', 'list_price': 150.0},
    {'name': '[SEED] Tanácsadás',         'type': 'service', 'list_price': 45000.0},
    {'name': '[SEED] Support Package',    'type': 'service', 'list_price': 500.0},
    {'name': '[SEED] Támogatási csomag',  'type': 'service', 'list_price': 150000.0},
    {'name': '[SEED] Training',           'type': 'service', 'list_price': 1200.0},
    {'name': '[SEED] Szoftver licensz',   'type': 'consu',   'list_price': 299.0},
    {'name': '[SEED] Hardware Module',    'type': 'consu',   'list_price': 89.0},
    {'name': '[SEED] Irodaszer csomag',   'type': 'consu',   'list_price': 12500.0},
]


def seed(client) -> None:
    existing = client.search_read('product.template', [('name', 'like', '[SEED]')], ['name'])
    existing_names = {r['name'] for r in existing}
    created = 0
    for p in PRODUCTS:
        if p['name'] not in existing_names:
            client.create('product.template', p)
            created += 1
    print(f'  products: {created} created, {len(PRODUCTS) - created} skipped')


def wipe(client) -> None:
    records = client.search_read('product.template', [('name', 'like', '[SEED]')], ['id'])
    if not records:
        print('  products: nothing to wipe')
        return
    ids = [r['id'] for r in records]
    client.unlink('product.template', ids)
    print(f'  products: {len(ids)} deleted')
```

- [ ] **Step 4: Run tests — verify they pass**

```bash
pytest tests/test_products.py -v
```

Expected: 5 tests pass.

- [ ] **Step 5: Commit**

```bash
git add seed/products.py tests/test_products.py
git commit -m "feat: add products seeder"
```

---

## Task 4: Contacts seeder (`seed/contacts.py`)

**Files:**
- Create: `tests/test_contacts.py`
- Create: `seed/contacts.py`

- [ ] **Step 1: Write `tests/test_contacts.py`**

```python
from unittest.mock import MagicMock, call
from seed.contacts import seed, wipe, COMPANIES, INDIVIDUALS


def test_seed_creates_all_when_none_exist():
    client = MagicMock()
    # search_read calls: existing seeds, then per company_name lookup for individuals (via country cache too)
    client.search_read.side_effect = lambda model, domain, fields, **kw: (
        [] if model == 'res.partner' and ('name', 'like', '[SEED]') in domain
        else [{'id': 99}] if model == 'res.country'
        else [{'id': 1, 'name': '[SEED] Kovács és Társai Kft.'}]
    )
    seed(client)
    # companies + individuals
    assert client.create.call_count == len(COMPANIES) + len(INDIVIDUALS)


def test_seed_skips_when_all_exist():
    client = MagicMock()
    all_names = [{'name': c['name']} for c in COMPANIES] + [{'name': i['name']} for i in INDIVIDUALS]

    def side_effect(model, domain, fields, **kw):
        if model == 'res.partner' and ('name', 'like', '[SEED]') in domain:
            return all_names
        if model == 'res.country':
            return [{'id': 99}]
        # lookup existing company by exact name
        return [{'id': 1}]

    client.search_read.side_effect = side_effect
    seed(client)
    client.create.assert_not_called()


def test_wipe_unlinks_all_seeded_partners():
    client = MagicMock()
    client.search_read.return_value = [{'id': 10}, {'id': 11}]
    wipe(client)
    client.unlink.assert_called_once_with('res.partner', [10, 11])


def test_wipe_does_nothing_when_empty():
    client = MagicMock()
    client.search_read.return_value = []
    wipe(client)
    client.unlink.assert_not_called()
```

- [ ] **Step 2: Run tests — verify they fail**

```bash
pytest tests/test_contacts.py -v
```

Expected: `ImportError` for `seed.contacts`.

- [ ] **Step 3: Write `seed/contacts.py`**

```python
COMPANIES = [
    {'name': '[SEED] Kovács és Társai Kft.',    'is_company': True, 'customer_rank': 1,
     'city': 'Budapest',   'country_code': 'HU', 'phone': '+36 1 234 5678',
     'email': 'info@kovacs-tarsai.hu'},
    {'name': '[SEED] Magyar Fejlesztő Zrt.',    'is_company': True, 'customer_rank': 1,
     'city': 'Debrecen',   'country_code': 'HU', 'phone': '+36 52 345 678',
     'email': 'office@magyar-fejleszto.hu'},
    {'name': '[SEED] Budai Logisztika Kft.',    'is_company': True, 'supplier_rank': 1,
     'city': 'Budapest',   'country_code': 'HU', 'phone': '+36 1 456 7890',
     'email': 'kapcsolat@budai-logisztika.hu'},
    {'name': '[SEED] Pécs-Tech Bt.',            'is_company': True, 'customer_rank': 1,
     'city': 'Pécs',       'country_code': 'HU', 'phone': '+36 72 234 567',
     'email': 'info@pecstech.hu'},
    {'name': '[SEED] Győri Nyomda Kft.',        'is_company': True, 'supplier_rank': 1,
     'city': 'Győr',       'country_code': 'HU', 'phone': '+36 96 345 678',
     'email': 'rendeles@gyorinyomda.hu'},
    {'name': '[SEED] Debreceni Consulting Kft.','is_company': True, 'customer_rank': 1,
     'city': 'Debrecen',   'country_code': 'HU', 'phone': '+36 52 456 789',
     'email': 'hello@debconsulting.hu'},
    {'name': '[SEED] Alföldi Agro Zrt.',        'is_company': True, 'customer_rank': 1,
     'city': 'Kecskemét',  'country_code': 'HU', 'phone': '+36 76 234 567',
     'email': 'info@alfoldiagro.hu'},
    {'name': '[SEED] Balaton Turisztika Kft.',  'is_company': True, 'customer_rank': 1,
     'city': 'Siófok',     'country_code': 'HU', 'phone': '+36 84 345 678',
     'email': 'foglalas@balatonturisztika.hu'},
    {'name': '[SEED] Acme Corp Ltd.',           'is_company': True, 'customer_rank': 1,
     'city': 'London',     'country_code': 'GB', 'phone': '+44 20 1234 5678',
     'email': 'contact@acmecorp.co.uk'},
    {'name': '[SEED] Nexus Solutions GmbH',     'is_company': True, 'customer_rank': 1,
     'city': 'Berlin',     'country_code': 'DE', 'phone': '+49 30 123 4567',
     'email': 'info@nexussolutions.de'},
    {'name': '[SEED] Alpine Ventures AG',       'is_company': True, 'supplier_rank': 1,
     'city': 'Vienna',     'country_code': 'AT', 'phone': '+43 1 234 5678',
     'email': 'office@alpineventures.at'},
    {'name': '[SEED] Nordic Systems AS',        'is_company': True, 'customer_rank': 1,
     'city': 'Oslo',       'country_code': 'NO', 'phone': '+47 21 234 567',
     'email': 'contact@nordicsystems.no'},
    {'name': '[SEED] Eastern Bridge Ltd.',      'is_company': True, 'customer_rank': 1,
     'city': 'Warsaw',     'country_code': 'PL', 'phone': '+48 22 234 5678',
     'email': 'info@easternbridge.pl'},
]

INDIVIDUALS = [
    {'name': '[SEED] Kovács Péter',    'company_name': '[SEED] Kovács és Társai Kft.',
     'email': 'peter.kovacs@kovacs-tarsai.hu',    'phone': '+36 30 123 4567', 'function': 'Ügyvezető'},
    {'name': '[SEED] Nagy Anna',       'company_name': '[SEED] Magyar Fejlesztő Zrt.',
     'email': 'anna.nagy@magyar-fejleszto.hu',     'phone': '+36 70 234 5678', 'function': 'Projektvezető'},
    {'name': '[SEED] Horváth Gábor',   'company_name': '[SEED] Budai Logisztika Kft.',
     'email': 'gabor.horvath@budai-logisztika.hu', 'phone': '+36 20 345 6789', 'function': 'Logisztikai vezető'},
    {'name': '[SEED] Szabó Éva',       'company_name': '[SEED] Pécs-Tech Bt.',
     'email': 'eva.szabo@pecstech.hu',             'phone': '+36 30 456 7890', 'function': 'Fejlesztő'},
    {'name': '[SEED] Tóth István',     'company_name': '[SEED] Győri Nyomda Kft.',
     'email': 'istvan.toth@gyorinyomda.hu',        'phone': '+36 20 567 8901', 'function': 'Értékesítési vezető'},
    {'name': '[SEED] Fekete Zsuzsanna','company_name': '[SEED] Debreceni Consulting Kft.',
     'email': 'zsuzsanna.fekete@debconsulting.hu', 'phone': '+36 70 678 9012', 'function': 'Tanácsadó'},
    {'name': '[SEED] Varga László',    'company_name': '[SEED] Alföldi Agro Zrt.',
     'email': 'laszlo.varga@alfoldiagro.hu',       'phone': '+36 30 789 0123', 'function': 'Értékesítő'},
    {'name': '[SEED] Kiss Mária',      'company_name': '[SEED] Balaton Turisztika Kft.',
     'email': 'maria.kiss@balatonturisztika.hu',   'phone': '+36 20 890 1234', 'function': 'Recepciós'},
    {'name': '[SEED] John Smith',      'company_name': '[SEED] Acme Corp Ltd.',
     'email': 'john.smith@acmecorp.co.uk',         'phone': '+44 7700 900001', 'function': 'Sales Manager'},
    {'name': '[SEED] Sarah Johnson',   'company_name': '[SEED] Nexus Solutions GmbH',
     'email': 'sarah.johnson@nexussolutions.de',   'phone': '+49 170 234 5678', 'function': 'Account Manager'},
    {'name': '[SEED] Hans Mueller',    'company_name': '[SEED] Alpine Ventures AG',
     'email': 'hans.mueller@alpineventures.at',    'phone': '+43 650 234 5678', 'function': 'Director'},
    {'name': '[SEED] Erik Larsson',    'company_name': '[SEED] Nordic Systems AS',
     'email': 'erik.larsson@nordicsystems.no',     'phone': '+47 900 12 345',  'function': 'CTO'},
]


def _country_id(client, cache: dict, code: str) -> int:
    if code not in cache:
        res = client.search_read('res.country', [('code', '=', code)], ['id'])
        cache[code] = res[0]['id'] if res else False
    return cache[code]


def seed(client) -> None:
    existing = client.search_read('res.partner', [('name', 'like', '[SEED]')], ['name'])
    existing_names = {r['name'] for r in existing}
    country_cache: dict = {}
    company_ids: dict = {}
    created = 0

    for c in COMPANIES:
        cid = _country_id(client, country_cache, c['country_code'])
        vals = {k: v for k, v in c.items() if k != 'country_code'}
        vals['country_id'] = cid
        if c['name'] not in existing_names:
            new_id = client.create('res.partner', vals)
            created += 1
        else:
            rec = client.search_read('res.partner', [('name', '=', c['name'])], ['id'])
            new_id = rec[0]['id']
        company_ids[c['name']] = new_id

    for ind in INDIVIDUALS:
        if ind['name'] not in existing_names:
            vals = {k: v for k, v in ind.items() if k != 'company_name'}
            parent_id = company_ids.get(ind['company_name'])
            if parent_id:
                vals['parent_id'] = parent_id
            client.create('res.partner', vals)
            created += 1

    total = len(COMPANIES) + len(INDIVIDUALS)
    print(f'  contacts: {created} created, {total - created} skipped')


def wipe(client) -> None:
    records = client.search_read('res.partner', [('name', 'like', '[SEED]')], ['id'])
    if not records:
        print('  contacts: nothing to wipe')
        return
    ids = [r['id'] for r in records]
    client.unlink('res.partner', ids)
    print(f'  contacts: {len(ids)} deleted')
```

- [ ] **Step 4: Run tests — verify they pass**

```bash
pytest tests/test_contacts.py -v
```

Expected: 4 tests pass.

- [ ] **Step 5: Commit**

```bash
git add seed/contacts.py tests/test_contacts.py
git commit -m "feat: add contacts seeder (HU/EN companies and individuals)"
```

---

## Task 5: CRM seeder (`seed/crm.py`)

**Files:**
- Create: `tests/test_crm.py`
- Create: `seed/crm.py`

- [ ] **Step 1: Write `tests/test_crm.py`**

```python
from unittest.mock import MagicMock
from seed.crm import seed, wipe, LEADS, OPPORTUNITIES


def _mock_client_for_seed(existing_crm=None):
    client = MagicMock()
    all_data = existing_crm if existing_crm is not None else []

    def search_read(model, domain, fields, **kw):
        if model == 'crm.lead':
            return all_data
        if model == 'res.partner':
            return [{'id': i + 1, 'name': f'Partner {i}'} for i in range(5)]
        if model == 'crm.stage':
            return [{'id': 1, 'name': 'New'}, {'id': 2, 'name': 'Qualified'},
                    {'id': 3, 'name': 'Proposition'}, {'id': 4, 'name': 'Won'}]
        return []

    client.search_read.side_effect = search_read
    return client


def test_seed_creates_all_when_none_exist():
    client = _mock_client_for_seed([])
    seed(client)
    assert client.create.call_count == len(LEADS) + len(OPPORTUNITIES)


def test_seed_skips_when_all_exist():
    existing = [{'name': r['name']} for r in LEADS + OPPORTUNITIES]
    client = _mock_client_for_seed(existing)
    seed(client)
    client.create.assert_not_called()


def test_seed_each_lead_uses_crm_lead_model():
    client = _mock_client_for_seed([])
    seed(client)
    for c in client.create.call_args_list:
        assert c[0][0] == 'crm.lead'


def test_wipe_unlinks_all():
    client = MagicMock()
    client.search_read.return_value = [{'id': 1}, {'id': 2}]
    wipe(client)
    client.unlink.assert_called_once_with('crm.lead', [1, 2])


def test_wipe_does_nothing_when_empty():
    client = MagicMock()
    client.search_read.return_value = []
    wipe(client)
    client.unlink.assert_not_called()
```

- [ ] **Step 2: Run tests — verify they fail**

```bash
pytest tests/test_crm.py -v
```

Expected: `ImportError` for `seed.crm`.

- [ ] **Step 3: Write `seed/crm.py`**

```python
import itertools

LEADS = [
    {'name': '[SEED] Weboldal fejlesztés igény',   'type': 'lead', 'stage_key': 0,
     'expected_revenue': 2500.0,  'probability': 10,
     'description': 'Az ügyfél egyedi weboldalt szeretne.'},
    {'name': '[SEED] ERP bevezetési érdeklődés',   'type': 'lead', 'stage_key': 0,
     'expected_revenue': 15000.0, 'probability': 20,
     'description': 'ERP rendszer bevezetése 50 fős cégnek.'},
    {'name': '[SEED] IT infrastruktúra felmérés',  'type': 'lead', 'stage_key': 0,
     'expected_revenue': 4500.0,  'probability': 15,
     'description': 'Hálózati infrastruktúra audit igény.'},
    {'name': '[SEED] Software audit request',      'type': 'lead', 'stage_key': 0,
     'expected_revenue': 3200.0,  'probability': 25,
     'description': 'Client wants a full software stack review.'},
    {'name': '[SEED] Cloud migration inquiry',     'type': 'lead', 'stage_key': 0,
     'expected_revenue': 8000.0,  'probability': 20,
     'description': 'Interested in migrating on-premise to cloud.'},
    {'name': '[SEED] Mobilalkalmazás fejlesztés',  'type': 'lead', 'stage_key': 1,
     'expected_revenue': 6500.0,  'probability': 35,
     'description': 'iOS és Android alkalmazás fejlesztési igény.'},
    {'name': '[SEED] CRM integration project',    'type': 'lead', 'stage_key': 1,
     'expected_revenue': 5000.0,  'probability': 30,
     'description': 'Integrate existing CRM with new platform.'},
    {'name': '[SEED] Adatelemzési megoldás',       'type': 'lead', 'stage_key': 1,
     'expected_revenue': 12000.0, 'probability': 40,
     'description': 'BI dashboard és adatelemzési rendszer.'},
    {'name': '[SEED] E-commerce platform build',  'type': 'lead', 'stage_key': 1,
     'expected_revenue': 18000.0, 'probability': 30,
     'description': 'Full e-commerce solution with payment gateway.'},
    {'name': '[SEED] Képzési program tervezés',   'type': 'lead', 'stage_key': 1,
     'expected_revenue': 3000.0,  'probability': 45,
     'description': 'Vállalati képzési program összeállítása.'},
]

OPPORTUNITIES = [
    {'name': '[SEED] Éves IT support szerződés',     'type': 'opportunity', 'stage_key': 0,
     'expected_revenue': 24000.0, 'probability': 50,
     'description': 'Éves szintű support és karbantartási szerződés.'},
    {'name': '[SEED] Odoo implementation Q3',        'type': 'opportunity', 'stage_key': 0,
     'expected_revenue': 35000.0, 'probability': 55,
     'description': 'Full Odoo Community setup for 30 users.'},
    {'name': '[SEED] Security hardening contract',   'type': 'opportunity', 'stage_key': 1,
     'expected_revenue': 9500.0,  'probability': 60,
     'description': 'Penetration testing and security audit.'},
    {'name': '[SEED] Rendszer integráció projekt',   'type': 'opportunity', 'stage_key': 1,
     'expected_revenue': 28000.0, 'probability': 65,
     'description': 'SAP és Odoo integráció tervezés és kivitelezés.'},
    {'name': '[SEED] Annual license bundle',         'type': 'opportunity', 'stage_key': 1,
     'expected_revenue': 5800.0,  'probability': 70,
     'description': 'Multi-seat software license renewal package.'},
    {'name': '[SEED] Logisztikai szoftver fejlesztés','type': 'opportunity', 'stage_key': 2,
     'expected_revenue': 42000.0, 'probability': 75,
     'description': 'Egyedi raktárkezelő szoftver fejlesztése.'},
    {'name': '[SEED] Training programme 2026',       'type': 'opportunity', 'stage_key': 2,
     'expected_revenue': 7200.0,  'probability': 80,
     'description': 'Six-month developer upskilling programme.'},
    {'name': '[SEED] Felhő migráció projekt',        'type': 'opportunity', 'stage_key': 2,
     'expected_revenue': 19500.0, 'probability': 85,
     'description': 'Azure felhő átállás tervezés és végrehajtás.'},
    {'name': '[SEED] Custom dashboard development',  'type': 'opportunity', 'stage_key': 2,
     'expected_revenue': 6000.0,  'probability': 80,
     'description': 'Real-time KPI dashboard for management.'},
    {'name': '[SEED] Helpdesk rendszer kiépítés',    'type': 'opportunity', 'stage_key': 2,
     'expected_revenue': 11000.0, 'probability': 85,
     'description': 'Ticketing és helpdesk rendszer bevezetése.'},
    {'name': '[SEED] ERP Q4 go-live',                'type': 'opportunity', 'stage_key': 3,
     'expected_revenue': 50000.0, 'probability': 90,
     'description': 'ERP production rollout scheduled Q4 2026.'},
    {'name': '[SEED] Data warehouse project — WON',  'type': 'opportunity', 'stage_key': 3,
     'expected_revenue': 32000.0, 'probability': 100,
     'description': 'Data warehouse build — deal closed.'},
    {'name': '[SEED] Cancelled security audit',      'type': 'opportunity', 'stage_key': 3,
     'expected_revenue': 4500.0,  'probability': 0,
     'description': 'Security audit — cancelled by client.'},
    {'name': '[SEED] Partnership portal',            'type': 'opportunity', 'stage_key': 3,
     'expected_revenue': 14000.0, 'probability': 95,
     'description': 'B2B partner self-service portal.'},
    {'name': '[SEED] Mobilapp pilot — closed',       'type': 'opportunity', 'stage_key': 3,
     'expected_revenue': 8500.0,  'probability': 100,
     'description': 'Mobile app pilot — completed and invoiced.'},
]


def seed(client) -> None:
    existing = client.search_read('crm.lead', [('name', 'like', '[SEED]')], ['name'])
    existing_names = {r['name'] for r in existing}

    partners = client.search_read('res.partner', [('name', 'like', '[SEED]'), ('is_company', '=', True)], ['id'])
    stages = client.search_read('crm.stage', [], ['id', 'name'])
    stage_ids = [s['id'] for s in stages] or [False]
    partner_cycle = itertools.cycle([p['id'] for p in partners]) if partners else itertools.cycle([False])

    created = 0
    for record in LEADS + OPPORTUNITIES:
        if record['name'] in existing_names:
            continue
        stage_idx = min(record['stage_key'], len(stage_ids) - 1)
        vals = {
            'name': record['name'],
            'type': record['type'],
            'stage_id': stage_ids[stage_idx],
            'expected_revenue': record['expected_revenue'],
            'probability': record['probability'],
            'description': record['description'],
            'partner_id': next(partner_cycle),
        }
        client.create('crm.lead', vals)
        created += 1

    total = len(LEADS) + len(OPPORTUNITIES)
    print(f'  crm: {created} created, {total - created} skipped')


def wipe(client) -> None:
    records = client.search_read('crm.lead', [('name', 'like', '[SEED]')], ['id'])
    if not records:
        print('  crm: nothing to wipe')
        return
    ids = [r['id'] for r in records]
    client.unlink('crm.lead', ids)
    print(f'  crm: {len(ids)} deleted')
```

- [ ] **Step 4: Run tests — verify they pass**

```bash
pytest tests/test_crm.py -v
```

Expected: 5 tests pass.

- [ ] **Step 5: Commit**

```bash
git add seed/crm.py tests/test_crm.py
git commit -m "feat: add CRM seeder (10 leads + 15 opportunities)"
```

---

## Task 6: Sale seeder (`seed/sale.py`)

**Notes:** Sale orders use `client_order_ref='[SEED]'` as the identifier (order `name` is auto-generated by Odoo). Order lines reference `product.product` (variants), not `product.template`.

**Files:**
- Create: `tests/test_sale.py`
- Create: `seed/sale.py`

- [ ] **Step 1: Write `tests/test_sale.py`**

```python
from unittest.mock import MagicMock
from seed.sale import seed, wipe, ORDERS


def _mock_client(existing_orders=None):
    client = MagicMock()
    orders = existing_orders if existing_orders is not None else []

    def search_read(model, domain, fields, **kw):
        if model == 'sale.order':
            return orders
        if model == 'res.partner':
            return [{'id': i + 1, 'name': f'[SEED] Company {i}'} for i in range(5)]
        if model == 'product.product':
            return [{'id': i + 10, 'name': f'[SEED] Product {i}', 'lst_price': 100.0}
                    for i in range(4)]
        return []

    client.search_read.side_effect = search_read
    client.create.return_value = 99
    return client


def test_seed_creates_orders_when_none_exist():
    client = _mock_client([])
    seed(client)
    # Each order = 1 create (with inline lines via Command)
    assert client.create.call_count == len(ORDERS)


def test_seed_skips_when_already_seeded():
    client = _mock_client([{'id': 1}])
    seed(client)
    client.create.assert_not_called()


def test_seed_confirms_sale_state_orders():
    client = _mock_client([])
    seed(client)
    confirmed = [o for o in ORDERS if o['state'] == 'sale']
    confirm_calls = [c for c in client.execute.call_args_list
                     if c[0][1] == 'action_confirm']
    assert len(confirm_calls) == len(confirmed)


def test_seed_cancels_cancel_state_orders():
    client = _mock_client([])
    seed(client)
    cancelled = [o for o in ORDERS if o['state'] == 'cancel']
    cancel_calls = [c for c in client.execute.call_args_list
                    if c[0][1] == 'action_cancel']
    assert len(cancel_calls) == len(cancelled)


def test_wipe_cancels_confirmed_then_unlinks():
    client = MagicMock()
    client.search_read.return_value = [
        {'id': 1, 'state': 'sale'},
        {'id': 2, 'state': 'draft'},
    ]
    wipe(client)
    client.execute.assert_called_once_with('sale.order', 'action_cancel', [1])
    client.unlink.assert_called_once_with('sale.order', [1, 2])


def test_wipe_does_nothing_when_empty():
    client = MagicMock()
    client.search_read.return_value = []
    wipe(client)
    client.unlink.assert_not_called()
```

- [ ] **Step 2: Run tests — verify they fail**

```bash
pytest tests/test_sale.py -v
```

Expected: `ImportError` for `seed.sale`.

- [ ] **Step 3: Write `seed/sale.py`**

```python
import itertools
import random

# (description in note, state, number_of_lines)
ORDERS = [
    {'note': '[SEED] Webfejlesztési projekt',     'state': 'draft',  'lines': 2},
    {'note': '[SEED] IT tanácsadás Q3',           'state': 'draft',  'lines': 3},
    {'note': '[SEED] Szoftver licensz csomag',    'state': 'draft',  'lines': 2},
    {'note': '[SEED] Hardver eszközök rendelés',  'state': 'draft',  'lines': 4},
    {'note': '[SEED] Képzési program tervezés',   'state': 'draft',  'lines': 2},
    {'note': '[SEED] Support contract Q1',        'state': 'sent',   'lines': 3},
    {'note': '[SEED] Annual license renewal',     'state': 'sent',   'lines': 2},
    {'note': '[SEED] Consulting services pkg',    'state': 'sent',   'lines': 4},
    {'note': '[SEED] Irodaszerek rendelés',       'state': 'sent',   'lines': 3},
    {'note': '[SEED] Training workshop bundle',   'state': 'sent',   'lines': 2},
    {'note': '[SEED] ERP bevezetési projekt',     'state': 'sale',   'lines': 3},
    {'note': '[SEED] Cloud migration phase 1',   'state': 'sale',   'lines': 2},
    {'note': '[SEED] Security audit contract',   'state': 'sale',   'lines': 2},
    {'note': '[SEED] Adatmigrálás projekt',       'state': 'sale',   'lines': 4},
    {'note': '[SEED] Rendszer integráció',        'state': 'sale',   'lines': 3},
    {'note': '[SEED] Helpdesk support SLA',      'state': 'sale',   'lines': 2},
    {'note': '[SEED] Custom dev sprint 1',       'state': 'sale',   'lines': 3},
    {'note': '[SEED] Tesztelési projekt',         'state': 'cancel', 'lines': 2},
    {'note': '[SEED] Pilot program cancelled',   'state': 'cancel', 'lines': 3},
    {'note': '[SEED] Infrastructure cancelled',  'state': 'cancel', 'lines': 2},
]

_QUANTITIES = [1, 2, 3, 5, 10]


def seed(client) -> None:
    existing = client.search_read('sale.order', [('client_order_ref', '=', '[SEED]')], ['id'])
    if existing:
        print(f'  sale: already seeded ({len(existing)} orders), skipping')
        return

    partners = client.search_read(
        'res.partner', [('name', 'like', '[SEED]'), ('is_company', '=', True)], ['id']
    )
    products = client.search_read(
        'product.product',
        [('product_tmpl_id.name', 'like', '[SEED]')],
        ['id', 'lst_price'],
    )
    if not partners or not products:
        print('  sale: missing seeded partners or products, skipping')
        return

    partner_cycle = itertools.cycle([p['id'] for p in partners])
    product_cycle = itertools.cycle(products)

    for order in ORDERS:
        lines = []
        for _ in range(order['lines']):
            p = next(product_cycle)
            lines.append((0, 0, {
                'product_id': p['id'],
                'product_uom_qty': random.choice(_QUANTITIES),
                'price_unit': p['lst_price'],
            }))
        order_id = client.create('sale.order', {
            'partner_id': next(partner_cycle),
            'client_order_ref': '[SEED]',
            'note': order['note'],
            'order_line': lines,
        })
        if order['state'] == 'sale':
            client.execute('sale.order', 'action_confirm', [order_id])
        elif order['state'] == 'sent':
            client.write('sale.order', [order_id], {'state': 'sent'})
        elif order['state'] == 'cancel':
            client.execute('sale.order', 'action_cancel', [order_id])

    print(f'  sale: {len(ORDERS)} orders created')


def wipe(client) -> None:
    orders = client.search_read(
        'sale.order', [('client_order_ref', '=', '[SEED]')], ['id', 'state']
    )
    if not orders:
        print('  sale: nothing to wipe')
        return
    to_cancel = [o['id'] for o in orders if o['state'] in ('sale', 'done')]
    if to_cancel:
        client.execute('sale.order', 'action_cancel', to_cancel)
    ids = [o['id'] for o in orders]
    client.unlink('sale.order', ids)
    print(f'  sale: {len(ids)} orders deleted')
```

- [ ] **Step 4: Run tests — verify they pass**

```bash
pytest tests/test_sale.py -v
```

Expected: 6 tests pass.

- [ ] **Step 5: Commit**

```bash
git add seed/sale.py tests/test_sale.py
git commit -m "feat: add sale order seeder (20 orders across draft/sent/confirmed/cancelled)"
```

---

## Task 7: Project seeder (`seed/project.py`)

**Files:**
- Create: `tests/test_project.py`
- Create: `seed/project.py`

- [ ] **Step 1: Write `tests/test_project.py`**

```python
from unittest.mock import MagicMock
from seed.project import seed, wipe, PROJECTS


def _mock_client(existing_projects=None):
    client = MagicMock()
    projects = existing_projects if existing_projects is not None else []

    def search_read(model, domain, fields, **kw):
        if model == 'project.project':
            return projects
        if model == 'res.partner':
            return [{'id': i + 1} for i in range(5)]
        if model == 'project.task.type':
            return [{'id': 1, 'name': 'In Progress'}, {'id': 2, 'name': 'Done'}]
        return []

    client.search_read.side_effect = search_read
    client.create.return_value = 50
    return client


def test_seed_creates_projects_and_tasks_when_none_exist():
    client = _mock_client([])
    seed(client)
    # projects + tasks per project
    total_tasks = sum(p['tasks'] for p in PROJECTS)
    assert client.create.call_count == len(PROJECTS) + total_tasks


def test_seed_skips_when_all_projects_exist():
    existing = [{'name': p['name']} for p in PROJECTS]
    client = _mock_client(existing)
    seed(client)
    client.create.assert_not_called()


def test_wipe_unlinks_tasks_then_projects():
    client = MagicMock()

    def search_read(model, domain, fields, **kw):
        if model == 'project.project':
            return [{'id': 10}, {'id': 11}]
        if model == 'project.task':
            return [{'id': 100}, {'id': 101}]
        return []

    client.search_read.side_effect = search_read
    wipe(client)
    calls = client.unlink.call_args_list
    assert calls[0][0] == ('project.task', [100, 101])
    assert calls[1][0] == ('project.project', [10, 11])


def test_wipe_does_nothing_when_empty():
    client = MagicMock()
    client.search_read.return_value = []
    wipe(client)
    client.unlink.assert_not_called()
```

- [ ] **Step 2: Run tests — verify they fail**

```bash
pytest tests/test_project.py -v
```

Expected: `ImportError` for `seed.project`.

- [ ] **Step 3: Write `seed/project.py`**

```python
import itertools

PROJECTS = [
    {'name': '[SEED] ERP Bevezetési Projekt',    'tasks': 5,
     'description': 'Odoo Community bevezetése és testreszabása.'},
    {'name': '[SEED] Webfejlesztés 2026',        'tasks': 5,
     'description': 'Vállalati weboldal újratervezése és fejlesztése.'},
    {'name': '[SEED] Cloud Migration',           'tasks': 5,
     'description': 'On-premise infrastructure migration to cloud.'},
    {'name': '[SEED] Security Audit',            'tasks': 5,
     'description': 'Annual penetration testing and hardening.'},
    {'name': '[SEED] Mobilalkalmazás Fejlesztés','tasks': 5,
     'description': 'iOS és Android app prototípus készítése.'},
    {'name': '[SEED] Data Warehouse Build',      'tasks': 5,
     'description': 'Central data warehouse design and implementation.'},
]

_TASK_NAMES = [
    ['[SEED] Követelmény felmérés',    '[SEED] Rendszerterv készítés',
     '[SEED] Fejlesztés sprint 1',     '[SEED] Tesztelés',          '[SEED] Go-live'],
    ['[SEED] Design mockups',          '[SEED] Frontend development',
     '[SEED] Backend API',             '[SEED] Integration testing', '[SEED] Deploy'],
    ['[SEED] Infrastructure audit',    '[SEED] Migration plan',
     '[SEED] Data migration',          '[SEED] Cutover testing',    '[SEED] Sign-off'],
    ['[SEED] Scope definition',        '[SEED] Vulnerability scan',
     '[SEED] Penetration test',        '[SEED] Report writing',     '[SEED] Remediation'],
    ['[SEED] UX kutatás',              '[SEED] Prototípus tervezés',
     '[SEED] iOS fejlesztés',          '[SEED] Android fejlesztés', '[SEED] Tesztelés'],
    ['[SEED] Schema design',           '[SEED] ETL pipeline setup',
     '[SEED] Dashboard build',         '[SEED] Data validation',    '[SEED] Handover'],
]


def seed(client) -> None:
    existing = client.search_read('project.project', [('name', 'like', '[SEED]')], ['name'])
    existing_names = {r['name'] for r in existing}

    partners = client.search_read('res.partner', [('name', 'like', '[SEED]'), ('is_company', '=', True)], ['id'])
    task_types = client.search_read('project.task.type', [], ['id', 'name'])
    stage_ids = [t['id'] for t in task_types] or [False]
    partner_cycle = itertools.cycle([p['id'] for p in partners]) if partners else itertools.cycle([False])

    created_projects = 0
    created_tasks = 0
    for idx, proj in enumerate(PROJECTS):
        if proj['name'] in existing_names:
            continue
        project_id = client.create('project.project', {
            'name': proj['name'],
            'description': proj['description'],
            'partner_id': next(partner_cycle),
        })
        created_projects += 1
        task_names = _TASK_NAMES[idx % len(_TASK_NAMES)]
        for t_idx, task_name in enumerate(task_names[:proj['tasks']]):
            stage_idx = min(t_idx * len(stage_ids) // proj['tasks'], len(stage_ids) - 1)
            client.create('project.task', {
                'name': task_name,
                'project_id': project_id,
                'stage_id': stage_ids[stage_idx],
            })
            created_tasks += 1

    print(f'  project: {created_projects} projects, {created_tasks} tasks created')


def wipe(client) -> None:
    projects = client.search_read('project.project', [('name', 'like', '[SEED]')], ['id'])
    if not projects:
        print('  project: nothing to wipe')
        return
    project_ids = [r['id'] for r in projects]
    tasks = client.search_read('project.task', [('project_id', 'in', project_ids)], ['id'])
    if tasks:
        client.unlink('project.task', [t['id'] for t in tasks])
    client.unlink('project.project', project_ids)
    print(f'  project: {len(project_ids)} projects and {len(tasks)} tasks deleted')
```

- [ ] **Step 4: Run tests — verify they pass**

```bash
pytest tests/test_project.py -v
```

Expected: 4 tests pass.

- [ ] **Step 5: Commit**

```bash
git add seed/project.py tests/test_project.py
git commit -m "feat: add project seeder (6 projects, 30 tasks)"
```

---

## Task 8: Invoicing seeder (`seed/invoicing.py`)

**Notes:** Invoices use `narration='[SEED]'` as the identifier. Posted invoices must be reset to draft (`button_draft`) before deletion. Invoice lines are created inline via `(0, 0, vals)` Command syntax.

**Files:**
- Create: `tests/test_invoicing.py`
- Create: `seed/invoicing.py`

- [ ] **Step 1: Write `tests/test_invoicing.py`**

```python
from unittest.mock import MagicMock
from seed.invoicing import seed, wipe, INVOICES


def _mock_client(existing_invoices=None):
    client = MagicMock()
    invoices = existing_invoices if existing_invoices is not None else []

    def search_read(model, domain, fields, **kw):
        if model == 'account.move':
            return invoices
        if model == 'res.partner':
            return [{'id': i + 1} for i in range(5)]
        if model == 'product.product':
            return [{'id': i + 10, 'lst_price': 150.0} for i in range(4)]
        return []

    client.search_read.side_effect = search_read
    client.create.return_value = 77
    return client


def test_seed_creates_all_invoices_when_none_exist():
    client = _mock_client([])
    seed(client)
    assert client.create.call_count == len(INVOICES)


def test_seed_skips_when_already_seeded():
    client = _mock_client([{'id': 1}])
    seed(client)
    client.create.assert_not_called()


def test_seed_posts_invoices_with_posted_state():
    client = _mock_client([])
    seed(client)
    posted_count = sum(1 for inv in INVOICES if inv['state'] == 'posted')
    post_calls = [c for c in client.execute.call_args_list if c[0][1] == 'action_post']
    assert len(post_calls) == posted_count


def test_wipe_resets_posted_invoices_before_unlink():
    client = MagicMock()
    client.search_read.return_value = [
        {'id': 1, 'state': 'posted'},
        {'id': 2, 'state': 'draft'},
    ]
    wipe(client)
    client.execute.assert_called_once_with('account.move', 'button_draft', [1])
    client.unlink.assert_called_once_with('account.move', [1, 2])


def test_wipe_does_nothing_when_empty():
    client = MagicMock()
    client.search_read.return_value = []
    wipe(client)
    client.unlink.assert_not_called()
```

- [ ] **Step 2: Run tests — verify they fail**

```bash
pytest tests/test_invoicing.py -v
```

Expected: `ImportError` for `seed.invoicing`.

- [ ] **Step 3: Write `seed/invoicing.py`**

```python
import itertools
import random
from datetime import date, timedelta

# Each entry: (description_suffix, state, num_lines, days_ago)
INVOICES = [
    {'suffix': 'Consulting Q1',           'state': 'draft',  'lines': 2, 'days_ago': 0},
    {'suffix': 'Szoftver licensz csomag', 'state': 'draft',  'lines': 3, 'days_ago': 0},
    {'suffix': 'Training workshop',       'state': 'draft',  'lines': 2, 'days_ago': 0},
    {'suffix': 'Hardware eszközök',       'state': 'draft',  'lines': 4, 'days_ago': 0},
    {'suffix': 'Support Package Q2',      'state': 'draft',  'lines': 2, 'days_ago': 0},
    {'suffix': 'IT tanácsadás Feb',       'state': 'draft',  'lines': 3, 'days_ago': 0},
    {'suffix': 'Annual license 2026',     'state': 'draft',  'lines': 2, 'days_ago': 0},
    {'suffix': 'Onboarding services',     'state': 'draft',  'lines': 2, 'days_ago': 0},
    {'suffix': 'ERP setup March',         'state': 'posted', 'lines': 3, 'days_ago': 85},
    {'suffix': 'Cloud migration phase 1', 'state': 'posted', 'lines': 2, 'days_ago': 72},
    {'suffix': 'Security audit Jan',      'state': 'posted', 'lines': 2, 'days_ago': 60},
    {'suffix': 'Adatmigrálás sprint 1',   'state': 'posted', 'lines': 4, 'days_ago': 55},
    {'suffix': 'Helpdesk SLA Feb',        'state': 'posted', 'lines': 2, 'days_ago': 45},
    {'suffix': 'Custom dev sprint 1',     'state': 'posted', 'lines': 3, 'days_ago': 38},
    {'suffix': 'Training batch Q1',       'state': 'posted', 'lines': 2, 'days_ago': 30},
    {'suffix': 'Rendszer integráció',     'state': 'posted', 'lines': 3, 'days_ago': 22},
    {'suffix': 'Licensing bundle Apr',    'state': 'posted', 'lines': 2, 'days_ago': 15},
    {'suffix': 'Consulting April',        'state': 'posted', 'lines': 2, 'days_ago': 10},
    {'suffix': 'Mobile app sprint',       'state': 'posted', 'lines': 3, 'days_ago': 7},
    {'suffix': 'Support renewal May',     'state': 'posted', 'lines': 2, 'days_ago': 3},
]

_QUANTITIES = [1, 2, 3, 5]


def seed(client) -> None:
    existing = client.search_read(
        'account.move',
        [('narration', 'like', '[SEED]'), ('move_type', '=', 'out_invoice')],
        ['id'],
    )
    if existing:
        print(f'  invoicing: already seeded ({len(existing)} invoices), skipping')
        return

    partners = client.search_read(
        'res.partner', [('name', 'like', '[SEED]'), ('is_company', '=', True)], ['id']
    )
    products = client.search_read(
        'product.product',
        [('product_tmpl_id.name', 'like', '[SEED]')],
        ['id', 'lst_price'],
    )
    if not partners or not products:
        print('  invoicing: missing seeded partners or products, skipping')
        return

    partner_cycle = itertools.cycle([p['id'] for p in partners])
    product_cycle = itertools.cycle(products)
    today = date.today()

    for inv in INVOICES:
        lines = []
        for _ in range(inv['lines']):
            p = next(product_cycle)
            lines.append((0, 0, {
                'product_id': p['id'],
                'quantity': random.choice(_QUANTITIES),
                'price_unit': p['lst_price'],
                'name': f'[SEED] {inv["suffix"]}',
            }))
        invoice_date = (today - timedelta(days=inv['days_ago'])) if inv['days_ago'] else False
        invoice_id = client.create('account.move', {
            'move_type': 'out_invoice',
            'partner_id': next(partner_cycle),
            'narration': '[SEED]',
            'invoice_date': str(invoice_date) if invoice_date else False,
            'invoice_line_ids': lines,
        })
        if inv['state'] == 'posted':
            client.execute('account.move', 'action_post', [invoice_id])

    print(f'  invoicing: {len(INVOICES)} invoices created')


def wipe(client) -> None:
    invoices = client.search_read(
        'account.move',
        [('narration', 'like', '[SEED]'), ('move_type', '=', 'out_invoice')],
        ['id', 'state'],
    )
    if not invoices:
        print('  invoicing: nothing to wipe')
        return
    posted_ids = [i['id'] for i in invoices if i['state'] == 'posted']
    if posted_ids:
        client.execute('account.move', 'button_draft', posted_ids)
    ids = [i['id'] for i in invoices]
    client.unlink('account.move', ids)
    print(f'  invoicing: {len(ids)} invoices deleted')
```

- [ ] **Step 4: Run tests — verify they pass**

```bash
pytest tests/test_invoicing.py -v
```

Expected: 5 tests pass.

- [ ] **Step 5: Commit**

```bash
git add seed/invoicing.py tests/test_invoicing.py
git commit -m "feat: add invoicing seeder (8 draft + 12 posted customer invoices)"
```

---

## Task 9: Timesheet seeder (`seed/timesheet.py`)

**Files:**
- Create: `tests/test_timesheet.py`
- Create: `seed/timesheet.py`

- [ ] **Step 1: Write `tests/test_timesheet.py`**

```python
from unittest.mock import MagicMock
from seed.timesheet import seed, wipe, ENTRY_COUNT


def _mock_client(existing_timesheets=None):
    client = MagicMock()
    entries = existing_timesheets if existing_timesheets is not None else []

    def search_read(model, domain, fields, **kw):
        if model == 'account.analytic.line':
            return entries
        if model == 'project.project':
            return [{'id': i + 1, 'name': f'[SEED] Project {i}'} for i in range(3)]
        if model == 'project.task':
            return [{'id': i + 10, 'project_id': (i % 3) + 1} for i in range(9)]
        if model == 'hr.employee':
            return [{'id': 5, 'name': 'Admin'}]
        return []

    client.search_read.side_effect = search_read
    return client


def test_seed_creates_entries_when_none_exist():
    client = _mock_client([])
    seed(client)
    assert client.create.call_count == ENTRY_COUNT


def test_seed_skips_when_already_seeded():
    client = _mock_client([{'id': 1}])
    seed(client)
    client.create.assert_not_called()


def test_seed_each_entry_targets_analytic_line_model():
    client = _mock_client([])
    seed(client)
    for c in client.create.call_args_list:
        assert c[0][0] == 'account.analytic.line'


def test_wipe_unlinks_all():
    client = MagicMock()
    client.search_read.return_value = [{'id': 1}, {'id': 2}]
    wipe(client)
    client.unlink.assert_called_once_with('account.analytic.line', [1, 2])


def test_wipe_does_nothing_when_empty():
    client = MagicMock()
    client.search_read.return_value = []
    wipe(client)
    client.unlink.assert_not_called()
```

- [ ] **Step 2: Run tests — verify they fail**

```bash
pytest tests/test_timesheet.py -v
```

Expected: `ImportError` for `seed.timesheet`.

- [ ] **Step 3: Write `seed/timesheet.py`**

```python
import itertools
import random
from datetime import date, timedelta

ENTRY_COUNT = 40

_HU_DESCRIPTIONS = [
    '[SEED] Követelmény elemzés', '[SEED] Fejlesztés', '[SEED] Kód review',
    '[SEED] Tesztelés', '[SEED] Dokumentálás', '[SEED] Megbeszélés',
    '[SEED] Hibajavítás', '[SEED] Deploy előkészítés',
]
_EN_DESCRIPTIONS = [
    '[SEED] Requirements analysis', '[SEED] Development work', '[SEED] Code review',
    '[SEED] Testing & QA', '[SEED] Documentation', '[SEED] Client meeting',
    '[SEED] Bug fixing', '[SEED] Sprint planning',
]
_ALL_DESCRIPTIONS = _HU_DESCRIPTIONS + _EN_DESCRIPTIONS
_DURATIONS = [0.5, 1.0, 1.5, 2.0, 3.0, 4.0, 6.0, 8.0]


def seed(client) -> None:
    existing = client.search_read(
        'account.analytic.line', [('name', 'like', '[SEED]')], ['id']
    )
    if existing:
        print(f'  timesheet: already seeded ({len(existing)} entries), skipping')
        return

    projects = client.search_read('project.project', [('name', 'like', '[SEED]')], ['id'])
    if not projects:
        print('  timesheet: no seeded projects found, skipping')
        return

    project_ids = [p['id'] for p in projects]
    tasks = client.search_read(
        'project.task', [('project_id', 'in', project_ids)], ['id', 'project_id']
    )

    employees = client.search_read('hr.employee', [('user_id.name', 'ilike', 'admin')], ['id'])
    if not employees:
        employees = client.search_read('hr.employee', [], ['id'], limit=1)
    employee_id = employees[0]['id'] if employees else False

    if not employee_id:
        print('  timesheet: no employee found, skipping')
        return

    today = date.today()
    project_cycle = itertools.cycle(project_ids)
    task_cycle = itertools.cycle(tasks) if tasks else itertools.cycle([None])
    desc_cycle = itertools.cycle(_ALL_DESCRIPTIONS)

    for i in range(ENTRY_COUNT):
        project_id = next(project_cycle)
        task = next(task_cycle)
        task_id = task['id'] if task else False
        entry_date = today - timedelta(days=random.randint(0, 59))
        client.create('account.analytic.line', {
            'name': next(desc_cycle),
            'project_id': project_id,
            'task_id': task_id,
            'employee_id': employee_id,
            'date': str(entry_date),
            'unit_amount': random.choice(_DURATIONS),
        })

    print(f'  timesheet: {ENTRY_COUNT} entries created')


def wipe(client) -> None:
    records = client.search_read(
        'account.analytic.line', [('name', 'like', '[SEED]')], ['id']
    )
    if not records:
        print('  timesheet: nothing to wipe')
        return
    ids = [r['id'] for r in records]
    client.unlink('account.analytic.line', ids)
    print(f'  timesheet: {len(ids)} entries deleted')
```

- [ ] **Step 4: Run tests — verify they pass**

```bash
pytest tests/test_timesheet.py -v
```

Expected: 5 tests pass.

- [ ] **Step 5: Commit**

```bash
git add seed/timesheet.py tests/test_timesheet.py
git commit -m "feat: add timesheet seeder (40 entries over last 60 days)"
```

---

## Task 10: Knowledge seeder (`seed/knowledge.py`)

**Files:**
- Create: `tests/test_knowledge.py`
- Create: `seed/knowledge.py`

- [ ] **Step 1: Write `tests/test_knowledge.py`**

```python
from unittest.mock import MagicMock
from seed.knowledge import seed, wipe, TOP_ARTICLES, CHILD_ARTICLES


def _mock_client(existing=None):
    client = MagicMock()
    records = existing if existing is not None else []
    client.search_read.return_value = records
    client.create.return_value = 200
    return client


def test_seed_creates_all_when_none_exist():
    client = _mock_client([])
    seed(client)
    assert client.create.call_count == len(TOP_ARTICLES) + len(CHILD_ARTICLES)


def test_seed_skips_when_all_exist():
    all_names = ([{'name': a['name']} for a in TOP_ARTICLES] +
                 [{'name': a['name']} for a in CHILD_ARTICLES])
    client = _mock_client(all_names)
    seed(client)
    client.create.assert_not_called()


def test_seed_creates_top_articles_before_children():
    client = _mock_client([])
    seed(client)
    top_count = len(TOP_ARTICLES)
    child_count = len(CHILD_ARTICLES)
    assert client.create.call_count == top_count + child_count
    # First N creates should be top-level (no parent_id)
    for i, c in enumerate(client.create.call_args_list[:top_count]):
        assert 'parent_id' not in c[0][1] or c[0][1].get('parent_id') is None


def test_wipe_unlinks_all():
    client = MagicMock()
    client.search_read.return_value = [{'id': 1}, {'id': 2}]
    wipe(client)
    client.unlink.assert_called_once_with('knowledge.article', [1, 2])


def test_wipe_does_nothing_when_empty():
    client = MagicMock()
    client.search_read.return_value = []
    wipe(client)
    client.unlink.assert_not_called()
```

- [ ] **Step 2: Run tests — verify they fail**

```bash
pytest tests/test_knowledge.py -v
```

Expected: `ImportError` for `seed.knowledge`.

- [ ] **Step 3: Write `seed/knowledge.py`**

```python
TOP_ARTICLES = [
    {
        'name': '[SEED] Onboarding Guide',
        'body': '<h1>Welcome</h1><p>This guide helps new team members get started with our systems and processes. Follow each section to complete your onboarding.</p>',
    },
    {
        'name': '[SEED] Fejlesztői Kézikönyv',
        'body': '<h1>Fejlesztői Kézikönyv</h1><p>Ez a dokumentum tartalmazza a fejlesztési folyamatokat, kódolási szabványokat és a CI/CD pipeline leírását.</p>',
    },
    {
        'name': '[SEED] Sales Playbook',
        'body': '<h1>Sales Playbook</h1><p>This document covers our sales process from lead qualification to contract signing. It includes objection handling scripts and pricing guidelines.</p>',
    },
    {
        'name': '[SEED] Belső Folyamatok',
        'body': '<h1>Belső Folyamatok</h1><p>A vállalat belső folyamatainak leírása: jóváhagyási rendszer, kommunikációs protokollok és projekt kezelési szabályok.</p>',
    },
    {
        'name': '[SEED] Product Documentation',
        'body': '<h1>Product Documentation</h1><p>Technical documentation for our main product suite. Covers installation, configuration, and API reference.</p>',
    },
]

CHILD_ARTICLES = [
    {
        'name': '[SEED] IT Setup Checklist',
        'parent_name': '[SEED] Onboarding Guide',
        'body': '<h2>IT Setup</h2><ul><li>Request laptop from IT</li><li>Set up VPN access</li><li>Configure email client</li><li>Join Slack workspace</li></ul>',
    },
    {
        'name': '[SEED] HR & Benefits Overview',
        'parent_name': '[SEED] Onboarding Guide',
        'body': '<h2>HR &amp; Benefits</h2><p>Review your employment contract, sign up for health insurance, and schedule your 30-day check-in with your manager.</p>',
    },
    {
        'name': '[SEED] Git Workflow',
        'parent_name': '[SEED] Fejlesztői Kézikönyv',
        'body': '<h2>Git Workflow</h2><p>Feature branches → Pull Request → Code review (min. 1 approval) → Merge to main. Never force-push to main.</p>',
    },
    {
        'name': '[SEED] Kód Review Szabályok',
        'parent_name': '[SEED] Fejlesztői Kézikönyv',
        'body': '<h2>Kód Review</h2><p>Minden PR-t legalább egy kolléga kell jóváhagyja. A review-k során fókuszálj a logikára, biztonságra és a tesztek lefedettségére.</p>',
    },
    {
        'name': '[SEED] Lead Qualification',
        'parent_name': '[SEED] Sales Playbook',
        'body': '<h2>Lead Qualification</h2><p>Use the BANT framework: Budget, Authority, Need, Timeline. A lead must score at least 3/4 before moving to Opportunity.</p>',
    },
    {
        'name': '[SEED] Pricing Guidelines',
        'parent_name': '[SEED] Sales Playbook',
        'body': '<h2>Pricing</h2><p>Standard rates apply. Discounts above 15% require manager approval. Volume discounts kick in at 10+ seats.</p>',
    },
    {
        'name': '[SEED] Jóváhagyási Folyamat',
        'parent_name': '[SEED] Belső Folyamatok',
        'body': '<h2>Jóváhagyások</h2><p>5000 EUR feletti kiadásokhoz pénzügyi igazgatói jóváhagyás szükséges. Az igényléseket a CRM rendszerben kell rögzíteni.</p>',
    },
    {
        'name': '[SEED] Communication Protocols',
        'parent_name': '[SEED] Belső Folyamatok',
        'body': '<h2>Communication</h2><p>Use Slack for async communication. Email for external parties. Weekly standups on Monday 9am. Urgent issues: call directly.</p>',
    },
    {
        'name': '[SEED] API Reference',
        'parent_name': '[SEED] Product Documentation',
        'body': '<h2>API Reference</h2><p>Base URL: <code>https://api.example.com/v1</code>. Authentication: Bearer token. Rate limit: 1000 req/min. Full spec in Swagger.</p>',
    },
    {
        'name': '[SEED] Telepítési Útmutató',
        'parent_name': '[SEED] Product Documentation',
        'body': '<h2>Telepítés</h2><p>Követelmények: Python 3.9+, PostgreSQL 14+, 4GB RAM. Telepítési lépések: clone, pip install, adatbázis inicializálás, szerver indítás.</p>',
    },
]


def seed(client) -> None:
    existing = client.search_read('knowledge.article', [('name', 'like', '[SEED]')], ['name'])
    existing_names = {r['name'] for r in existing}
    parent_ids: dict = {}
    created = 0

    for art in TOP_ARTICLES:
        if art['name'] not in existing_names:
            new_id = client.create('knowledge.article', {
                'name': art['name'],
                'body': art['body'],
            })
            created += 1
        else:
            rec = client.search_read('knowledge.article', [('name', '=', art['name'])], ['id'])
            new_id = rec[0]['id'] if rec else None
        parent_ids[art['name']] = new_id

    for art in CHILD_ARTICLES:
        if art['name'] not in existing_names:
            vals = {'name': art['name'], 'body': art['body']}
            parent_id = parent_ids.get(art['parent_name'])
            if parent_id:
                vals['parent_id'] = parent_id
            client.create('knowledge.article', vals)
            created += 1

    total = len(TOP_ARTICLES) + len(CHILD_ARTICLES)
    print(f'  knowledge: {created} created, {total - created} skipped')


def wipe(client) -> None:
    records = client.search_read('knowledge.article', [('name', 'like', '[SEED]')], ['id'])
    if not records:
        print('  knowledge: nothing to wipe')
        return
    ids = [r['id'] for r in records]
    client.unlink('knowledge.article', ids)
    print(f'  knowledge: {len(ids)} articles deleted')
```

- [ ] **Step 4: Run tests — verify they pass**

```bash
pytest tests/test_knowledge.py -v
```

Expected: 5 tests pass.

- [ ] **Step 5: Commit**

```bash
git add seed/knowledge.py tests/test_knowledge.py
git commit -m "feat: add knowledge seeder (5 top-level + 10 child articles, HU/EN)"
```

---

## Task 11: Runner CLI (`seed/runner.py`)

**Files:**
- Create: `tests/test_runner.py`
- Create: `seed/runner.py`

- [ ] **Step 1: Write `tests/test_runner.py`**

```python
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
```

- [ ] **Step 2: Run tests — verify they fail**

```bash
pytest tests/test_runner.py -v
```

Expected: `ImportError` for `seed.runner`.

- [ ] **Step 3: Write `seed/runner.py`**

```python
import argparse
import sys

from seed.connection import get_client
from seed import products, contacts, crm, sale, project, invoicing, timesheet, knowledge

MODULES = {
    'products':   products,
    'contacts':   contacts,
    'crm':        crm,
    'sale':       sale,
    'project':    project,
    'invoicing':  invoicing,
    'timesheet':  timesheet,
    'knowledge':  knowledge,
}

SEED_ORDER = ['products', 'contacts', 'crm', 'sale', 'project', 'invoicing', 'timesheet', 'knowledge']
WIPE_ORDER = list(reversed(SEED_ORDER))


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
            MODULES[name].wipe(client)
    else:
        order = [args.only] if args.only else SEED_ORDER
        for name in order:
            print(f'  Seeding {name}...')
            MODULES[name].seed(client)


if __name__ == '__main__':
    main()
```

- [ ] **Step 4: Run tests — verify they pass**

```bash
pytest tests/test_runner.py -v
```

Expected: 5 tests pass.

- [ ] **Step 5: Run full test suite — all green**

```bash
pytest -v
```

Expected: All tests pass (39 total across all modules).

- [ ] **Step 6: Commit**

```bash
git add seed/runner.py tests/test_runner.py
git commit -m "feat: add CLI runner with --wipe and --only flags"
```

---

## Task 12: End-to-end smoke test against dev instance

**Prerequisites:** Dev Odoo instance running at URL in `.env.dev`, modules installed: `crm`, `sale_management`, `account`, `project`, `hr_timesheet`, `knowledge`.

- [ ] **Step 1: Verify connectivity**

```bash
python -c "from seed.connection import get_client; c = get_client(); print('UID:', c.uid)"
```

Expected output: `UID: <integer>` (e.g. `UID: 2`). If this fails with `Authentication failed`, check `.env.dev` credentials. If it fails with a connection error, verify the URL and that the instance is running.

- [ ] **Step 2: Run full seed**

```bash
python seed/runner.py
```

Expected: Lines like:
```
  Seeding products...
  products: 8 created, 0 skipped
  Seeding contacts...
  contacts: 25 created, 0 skipped
  Seeding crm...
  crm: 25 created, 0 skipped
  Seeding sale...
  sale: 20 orders created
  Seeding project...
  project: 6 projects, 30 tasks created
  Seeding invoicing...
  invoicing: 20 invoices created
  Seeding timesheet...
  timesheet: 40 entries created
  Seeding knowledge...
  knowledge: 15 created, 0 skipped
```

- [ ] **Step 3: Verify idempotency — run seed again**

```bash
python seed/runner.py
```

Expected: All modules print `skipped` or `already seeded` — zero creates.

- [ ] **Step 4: Test `--only` flag**

```bash
python seed/runner.py --wipe --only crm
python seed/runner.py --only crm
```

Expected: First run deletes 25 CRM records. Second run re-creates 25.

- [ ] **Step 5: Test full wipe**

```bash
python seed/runner.py --wipe
```

Expected: All modules report deleted counts. Wipe runs in reverse order (knowledge → … → products).

- [ ] **Step 6: Final commit**

```bash
git add .
git commit -m "chore: verify end-to-end seed/wipe against dev Odoo instance"
```
