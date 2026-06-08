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
