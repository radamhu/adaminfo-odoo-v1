import os
import xmlrpc.client
from urllib.parse import urlparse
from dotenv import load_dotenv


class OdooClient:
    def __init__(self, url: str, db: str, username: str, password: str):
        self.url = url.rstrip('/')
        self.db = db
        self.password = password
        self._common = xmlrpc.client.ServerProxy(f'{self.url}/xmlrpc/2/common', allow_none=True)
        self._models = xmlrpc.client.ServerProxy(f'{self.url}/xmlrpc/2/object', allow_none=True)
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
    except (xmlrpc.client.Fault, OSError):
        pass
    hostname = urlparse(url).hostname or ''
    if not hostname:
        raise ValueError(f'Invalid Odoo URL: {url} — could not extract hostname')
    return hostname.split('.')[0]


def get_client(env_file: str = '.env.dev') -> OdooClient:
    load_dotenv(env_file, override=True)
    url = os.environ['ODOO_ERP_URL']
    username = os.environ['ODOO_LOGIN_USERNAME']
    password = os.environ['ODOO_LOGIN_PASSWORD']
    db = os.environ.get('ODOO_DB') or _detect_db(url)
    return OdooClient(url, db, username, password)
