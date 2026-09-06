import os
import requests
from dotenv import load_dotenv

BASE_URL = 'https://api.oec.sh/api/public/v1'


class OecshClient:
    """Thin wrapper around the oec.sh public API (platform-level env/server ops).

    Covers what the public API exposes: server/project/environment discovery,
    backup listing, health status, logs, and env lifecycle (stop/start/restart/
    delete). Backup *creation* and restore-to-different-server have no public
    endpoint as of 2026-09 — those stay manual, dashboard-only.
    """

    def __init__(self, api_key: str):
        self._session = requests.Session()
        self._session.headers['Authorization'] = f'Bearer {api_key}'

    def _get(self, path: str, params: dict = None) -> dict:
        resp = self._session.get(f'{BASE_URL}{path}', params=params or {})
        resp.raise_for_status()
        return resp.json()

    def list_servers(self) -> list:
        return self._get('/servers')['data']

    def list_projects(self) -> list:
        return self._get('/projects')['data']

    def list_environments(self, project_id: str) -> list:
        return self._get(f'/projects/{project_id}/environments')

    def find_environment(self, name: str) -> dict:
        """Search every project on this account for an environment by exact name."""
        for project in self.list_projects():
            for env in self.list_environments(project['id']):
                if env['name'] == name:
                    return env
        raise ValueError(f'No environment named {name!r} found on this account')

    def find_environment_by_id(self, env_id: str) -> dict:
        for project in self.list_projects():
            for env in self.list_environments(project['id']):
                if env['id'] == env_id:
                    return env
        raise ValueError(f'No environment with id {env_id!r} found on this account')

    def list_backups(self, env_id: str, status: str = None) -> list:
        params = {'status': status} if status else {}
        return self._get(f'/environments/{env_id}/backups', params=params)['items']

    def status(self, env_id: str) -> dict:
        return self._get(f'/environments/{env_id}/status')

    def logs(self, env_id: str) -> dict:
        return self._get(f'/environments/{env_id}/logs')

    def stop(self, env_id: str) -> None:
        resp = self._session.post(f'{BASE_URL}/environments/{env_id}/stop')
        resp.raise_for_status()

    def start(self, env_id: str) -> None:
        resp = self._session.post(f'{BASE_URL}/environments/{env_id}/start')
        resp.raise_for_status()

    def restart(self, env_id: str) -> None:
        resp = self._session.post(f'{BASE_URL}/environments/{env_id}/restart')
        resp.raise_for_status()

    def delete(self, env_id: str) -> None:
        resp = self._session.delete(f'{BASE_URL}/environments/{env_id}')
        resp.raise_for_status()


def get_client(env_file: str = '.env.dev') -> OecshClient:
    load_dotenv(env_file, override=True)
    return OecshClient(os.environ['ODOO_PUBLIC_API_KEY'])
