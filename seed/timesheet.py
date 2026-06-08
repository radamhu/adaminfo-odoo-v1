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
