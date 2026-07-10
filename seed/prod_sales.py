"""
Production sales prospects — contacts (res.partner) + CRM leads (crm.lead).
Idempotent: skips records that already exist by exact name.
Run:  python -m seed.runner --env .env.prod --only prod_sales
"""

TAG_DEVOPS  = 'DevOps IT'
TAG_ERP     = 'ERP–Webshop'    # ERP–Webshop
TAG_FINTECH = 'Fintech–Data'   # Fintech–Data

# (name, country_code, website_or_None, tag)
COMPANIES = [
    # ── DevOps / IT — Hungary ──────────────────────────────────────────
    ('Vphone.hu',                        'HU', 'https://www.vphone.hu',              TAG_DEVOPS),
    ('Arteries',                         'HU', 'https://arteries.hu',                TAG_DEVOPS),
    ('Defense Innovation',               'HU', 'https://defenseinnovation.hu',       TAG_DEVOPS),
    ('HM EI Zrt',                        'HU', 'https://hmei.hu',                    TAG_DEVOPS),
    ('HM Currus',                        'HU', 'https://www.currus.hu',              TAG_DEVOPS),
    ('HM Arezenal Zrt',                  'HU', None,                                 TAG_DEVOPS),
    ('REMRED Zrt',                       'HU', None,                                 TAG_DEVOPS),
    ('4iG Nyrt',                         'HU', 'https://www.4ig.hu',                 TAG_DEVOPS),
    ('OptiGroup Kft (SSC)',              'HU', None,                                 TAG_DEVOPS),
    ('Roche SSC',                        'HU', 'https://www.roche.hu',               TAG_DEVOPS),
    ('Allianz Technology',               'HU', 'https://allianz-technology.com',     TAG_DEVOPS),
    ('Kuka SSC Taksony',                 'HU', 'https://www.kuka.com',               TAG_DEVOPS),
    ('Fressnapf SSC',                    'HU', 'https://www.fressnapf.hu',           TAG_DEVOPS),
    ('Nielsen IQ Budapest',              'HU', 'https://nielseniq.com',              TAG_DEVOPS),
    ('Agora Pay',                        'HU', None,                                 TAG_DEVOPS),
    ('Amrop Kohlmann & Young Kft',       'HU', 'https://amrop.com',                  TAG_DEVOPS),
    ('ApPello Kft',                      'HU', None,                                 TAG_DEVOPS),
    ('Appello Asseco SEE S.A.',          'HU', None,                                 TAG_DEVOPS),
    ('Attrecto Zrt',                     'HU', 'https://attrecto.com',               TAG_DEVOPS),
    ('AutSoft Zrt',                      'HU', 'https://autsoft.hu',                 TAG_DEVOPS),
    ('Aggreg8.io',                       'HU', 'http://aggreg8.io',                  TAG_DEVOPS),
    ('Cherrisk',                         'HU', 'https://www.cherrisk.com',           TAG_DEVOPS),
    ('Cellum',                           'HU', 'https://www.cellum.com',             TAG_DEVOPS),
    ('Commsignia',                       'HU', 'https://commsignia.com',             TAG_DEVOPS),
    ('Complytron',                       'HU', 'https://complytron.com',             TAG_DEVOPS),
    ('Ergománia',                   'HU', None,                                 TAG_DEVOPS),
    ('Erlang Solutions Hungary Kft',     'HU', 'https://www.erlang-solutions.com',   TAG_DEVOPS),
    ('EuroMACC Kft',                     'HU', 'https://euromacc.com',               TAG_DEVOPS),
    ('FX Software Zrt',                  'HU', 'https://fx.hu',                      TAG_DEVOPS),
    ('GB & Partners Zrt',                'HU', None,                                 TAG_DEVOPS),
    ('Facekom Kft',                      'HU', 'https://facekom.net',                TAG_DEVOPS),
    ('Family Finances',                  'HU', 'https://www.familyfinances.hu',      TAG_DEVOPS),
    ('Fundastik',                        'HU', 'http://www.fundastik.com',           TAG_DEVOPS),
    ('FestiPay',                         'HU', 'http://www.festipay.com',            TAG_DEVOPS),
    ('FlexiBill',                        'HU', 'https://flexibill.hu',               TAG_DEVOPS),
    ('INNODOX Technologies Zrt',         'HU', 'https://www.innodox.com',            TAG_DEVOPS),
    ('INTREND Computing Kft',            'HU', 'https://www.intrend.hu',             TAG_DEVOPS),
    ('IThelps Kft',                      'HU', None,                                 TAG_DEVOPS),
    ('Invitech ICT Services Kft',        'HU', 'https://www.invitech.hu',            TAG_DEVOPS),
    ('Iron Mountain',                    'HU', 'https://www.ironmountain.com',       TAG_DEVOPS),
    ('InLock',                           'HU', 'https://inlock.io',                  TAG_DEVOPS),
    ('Insurwiz',                         'HU', 'https://insurwiz.io',                TAG_DEVOPS),
    ('LocalTime PR',                     'HU', None,                                 TAG_DEVOPS),
    ('Loxon',                            'HU', 'https://www.loxon.eu',               TAG_DEVOPS),
    ('Livlia',                           'HU', 'https://livlia.com',                 TAG_DEVOPS),
    ('Mastercard Hungary',               'HU', 'https://www.mastercard.com',         TAG_DEVOPS),
    ('Mindspire Consulting Zrt',         'HU', 'https://mindspire.hu',               TAG_DEVOPS),
    ('Money.hu',                         'HU', 'https://www.money.hu',               TAG_DEVOPS),
    ('MrCoin',                           'HU', 'https://www.mrcoin.eu',              TAG_DEVOPS),
    ('MKB FinTech Lab',                  'HU', 'https://fintechlab.hu',              TAG_DEVOPS),
    ('FintechBlocks',                    'HU', 'https://www.fintechblocks.com',      TAG_DEVOPS),
    ('ONLINET Group Zrt',                'HU', 'https://onlinetgroup.com',           TAG_DEVOPS),
    ('Omikron Magyarország Kft',   'HU', None,                                 TAG_DEVOPS),
    ('OTP Lab',                          'HU', 'https://www.otpbank.hu/portal/en/OTPLAB_ENG', TAG_DEVOPS),
    ('Qualco',                           'HU', 'https://qualco.eu',                  TAG_DEVOPS),
    ('Qualysoft Informatikai Zrt',       'HU', 'https://qualysoft.com',              TAG_DEVOPS),
    ('Quattrosoft Kft',                  'HU', None,                                 TAG_DEVOPS),
    ('R-Szoft Kft',                      'HU', 'https://r-szoft.hu',                 TAG_DEVOPS),
    ('Recash Ltd',                       'HU', None,                                 TAG_DEVOPS),
    ('Rowan Hill',                       'HU', 'http://www.rowanhillglobal.hu',      TAG_DEVOPS),
    ('Rollet',                           'HU', 'https://rollet.hu',                  TAG_DEVOPS),
    ('Riport',                           'HU', 'https://riport.co.hu',               TAG_DEVOPS),
    ('UpScale',                          'HU', None,                                 TAG_DEVOPS),
    ('Vialto Consulting Kft',            'HU', 'https://vialto.com',                 TAG_DEVOPS),
    ('Virgo Systems Kft',                'HU', None,                                 TAG_DEVOPS),
    ('W.UP',                             'HU', 'https://wup.digital',                TAG_DEVOPS),
    ('VERN',                             'HU', 'http://www.vernhelps.com',           TAG_DEVOPS),
    ('Virpay',                           'HU', 'https://virpay.hu',                  TAG_DEVOPS),
    ('IzzyPay',                          'HU', 'https://izzypay.hu',                 TAG_DEVOPS),
    ('Tesco Hungary',                    'HU', 'https://www.tesco.hu',               TAG_DEVOPS),
    ('Bosch Innovation Center Budapest', 'HU', 'https://www.bosch.hu',               TAG_DEVOPS),
    ('Bitrise',                          'HU', 'https://bitrise.io',                 TAG_DEVOPS),
    ('Greehill',                         'HU', 'https://www.greehill.com',           TAG_DEVOPS),
    ('Tresorit',                         'HU', 'https://tresorit.com',               TAG_DEVOPS),
    ('Digital Thinkers',                 'HU', None,                                 TAG_DEVOPS),
    ('Supercharge',                      'HU', 'https://supercharge.io',             TAG_DEVOPS),
    ('Big Fish Internet-Technológiai Kft', 'HU', 'https://bigfish.hu',          TAG_DEVOPS),
    ('Runiosit',                         'HU', 'https://runiosit.com',               TAG_DEVOPS),
    # ── DevOps / IT — International ────────────────────────────────────
    ('AboutYou',                         'DE', 'https://corporate.aboutyou.de',      TAG_DEVOPS),
    ('Zalando',                          'DE', 'https://jobs.zalando.com',           TAG_DEVOPS),
    ('Flipper Devices',                  'DE', 'https://flipperdevices.com',         TAG_DEVOPS),
    ('DISH',                             'DE', 'https://www.dish.co',                TAG_DEVOPS),
    ('CEWE',                             'DE', 'https://www.cewe.de',                TAG_DEVOPS),
    ('Klarna',                           'SE', 'https://klarna.com',                 TAG_DEVOPS),
    ('Affirm',                           'US', 'https://affirm.com',                 TAG_DEVOPS),
    ('Afterpay',                         'AU', 'https://afterpay.com',               TAG_DEVOPS),
    ('Continental',                      'DE', 'https://www.continental.com',        TAG_DEVOPS),
    ('Mergify',                          'FR', 'https://mergify.com',                TAG_DEVOPS),
    ('Tetrate',                          'US', 'https://tetrate.io',                 TAG_DEVOPS),
    ('ClickUp',                          'US', 'https://clickup.com',                TAG_DEVOPS),
    ('Squer',                            'AT', 'https://www.squer.io',               TAG_DEVOPS),
    # ── ERP / Webshop ───────────────────────────────────────────────────
    ('Shoprenter',                       'HU', 'https://www.shoprenter.hu',          TAG_ERP),
    ('Shopify',                          'CA', 'https://www.shopify.com',            TAG_ERP),
    ('Unas',                             'HU', 'https://unas.hu',                    TAG_ERP),
    ('Cargoson',                         'EE', 'https://www.cargoson.com',           TAG_ERP),
    ('Valkuz',                           'HU', 'https://valkuz.hu',                  TAG_ERP),
    ('Wildom',                           'HU', 'https://wildom.com',                 TAG_ERP),
    ('VShosting',                        'CZ', 'https://vshosting.hu',               TAG_ERP),
    ('Online-ERP.hu',                    'HU', 'https://www.online-erp.hu',          TAG_ERP),
    ('Oregional',                        'HU', 'https://oregional.hu',               TAG_ERP),
    ('Hungarodo',                        'HU', 'https://hungarodo.hu',               TAG_ERP),
    ('Dotech',                           'HU', 'https://www.dotech.hu',              TAG_ERP),
    ('BDSC',                             'HU', 'https://www.bdsc.hu',                TAG_ERP),
    ('Eyssen',                           'HU', 'https://www.eyssen.hu',              TAG_ERP),
    # ── Fintech / Data ──────────────────────────────────────────────────
    ('BerenyiSoft Kft',                  'HU', 'https://berenyisoft.com',            TAG_FINTECH),
    ('Datapao',                          'HU', 'https://datapao.com',                TAG_FINTECH),
    ('WorldQuant',                       'US', 'https://www.worldquant.com',         TAG_FINTECH),
    ('SEON',                             'HU', 'https://seon.io',                    TAG_FINTECH),
    ('Péntech / PastPay',           'HU', 'https://pentech.hu',                 TAG_FINTECH),
    ('Perfinal',                         'HU', 'https://perfinal.com',               TAG_FINTECH),
    ('FintechX',                         'HU', 'https://fintechx.digital',           TAG_FINTECH),
    ('Swipe Technologies (Salarify)',    'HU', 'https://salarify.me',                TAG_FINTECH),
    ('Acounto',                          'HU', None,                                 TAG_FINTECH),
    ('Smartsurance Technologies (Cristo)', 'HU', None,                               TAG_FINTECH),
    ('Fintrous Group',                   'HU', 'https://fintrous.com',               TAG_FINTECH),
    ('Erste BankSpiration',              'HU', 'https://www.erstebank.hu',           TAG_FINTECH),
]

INDIVIDUALS = [
    {'name': 'Kádár Tamás',    'company': 'SEON',                               'function': 'CEO, co-founder'},
    {'name': 'Berényi Benjamin',           'company': 'Péntech / PastPay',            'function': 'co-founder'},
    {'name': 'Brezovszki Máté',      'company': 'Perfinal',                           'function': 'CEO'},
    {'name': 'Mudri György',              'company': 'FintechX',                           'function': 'CEO'},
    {'name': 'Radák Bence',               'company': 'Swipe Technologies (Salarify)',       'function': 'CEO, co-founder'},
    {'name': 'Brachmann Ferenc',               'company': 'Acounto',                            'function': 'co-founder'},
    {'name': 'Szota Szabolcs',                 'company': 'Smartsurance Technologies (Cristo)',  'function': 'co-founder'},
    {'name': 'Bruzsa Géza',               'company': 'Fintrous Group',                     'function': 'CEO'},
]


def _country_id(client, cache: dict, code: str) -> int:
    if code not in cache:
        res = client.search_read('res.country', [('code', '=', code)], ['id'])
        cache[code] = res[0]['id'] if res else False
    return cache[code]


def _get_or_create(client, model: str, name: str) -> int:
    res = client.search_read(model, [('name', '=', name)], ['id'])
    if res:
        return res[0]['id']
    return client.create(model, {'name': name})


def seed(client) -> None:
    # Phase 0 — tags
    partner_tags: dict = {}
    crm_tags: dict = {}
    for t in (TAG_DEVOPS, TAG_ERP, TAG_FINTECH):
        partner_tags[t] = _get_or_create(client, 'res.partner.category', t)
        crm_tags[t]     = _get_or_create(client, 'crm.tag', t)

    # Phase 1 — companies
    existing_co = {
        r['name'] for r in
        client.search_read('res.partner', [('is_company', '=', True)], ['name'], limit=5000)
    }
    country_cache: dict = {}
    company_ids: dict = {}
    c_created = 0

    for name, cc, website, tag in COMPANIES:
        cid = _country_id(client, country_cache, cc)
        vals: dict = {
            'name': name,
            'is_company': True,
            'customer_rank': 1,
            'country_id': cid,
            'category_id': [[6, 0, [partner_tags[tag]]]],
        }
        if website:
            vals['website'] = website
        if name not in existing_co:
            company_ids[name] = client.create('res.partner', vals)
            c_created += 1
        else:
            rec = client.search_read('res.partner',
                                     [('name', '=', name), ('is_company', '=', True)], ['id'])
            if rec:
                company_ids[name] = rec[0]['id']

    # Phase 2 — individual contacts
    existing_ind = {
        r['name'] for r in
        client.search_read('res.partner', [('is_company', '=', False)], ['name'], limit=5000)
    }
    p_created = 0
    for ind in INDIVIDUALS:
        if ind['name'] in existing_ind:
            continue
        vals = {
            'name': ind['name'],
            'is_company': False,
            'function': ind['function'],
            'category_id': [[6, 0, [partner_tags[TAG_FINTECH]]]],
        }
        parent = company_ids.get(ind['company'])
        if parent:
            vals['parent_id'] = parent
        client.create('res.partner', vals)
        p_created += 1

    # Phase 3 — CRM leads
    existing_leads = {
        r['name'] for r in
        client.search_read('crm.lead', [], ['name'], limit=5000)
    }
    stages = client.search_read('crm.stage', [], ['id', 'sequence'], limit=20)
    stages.sort(key=lambda s: s.get('sequence', 0))
    first_stage = stages[0]['id'] if stages else False

    l_created = 0
    for name, _cc, _url, tag in COMPANIES:
        lead_name = f'{name} — {tag} Outreach'
        if lead_name in existing_leads:
            continue
        client.create('crm.lead', {
            'name': lead_name,
            'type': 'opportunity',
            'stage_id': first_stage,
            'partner_id': company_ids.get(name, False),
            'tag_ids': [[6, 0, [crm_tags[tag]]]],
        })
        l_created += 1

    n = len(COMPANIES)
    print(f'  prod_sales: {c_created}/{n} companies, '
          f'{p_created}/{len(INDIVIDUALS)} contacts, '
          f'{l_created}/{n} leads created')


def wipe(client) -> None:
    print('  prod_sales: wipe not supported — delete records manually in Odoo if needed.')
