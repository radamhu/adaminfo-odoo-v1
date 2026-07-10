## EXECUTION PLAN

> **Status:** DRAFT — awaiting approval
> **Target:** https://adaminfo-prod-1139.apps.oec.sh/
> **Approach:** No test prefix — these are real prospects (unlike `[SEED]` demo data).
> Skip if record already exists by exact name (idempotent).

### Summary

| Phase           | Type                                                      | Records        |
| --------------- | --------------------------------------------------------- | -------------- |
| 0               | Create tags in `res.partner.category` + `crm.tag`     | 3 tags each    |
| 1               | `res.partner` — Companies                              | ~107           |
| 2               | `res.partner` — Individual contacts (Fintech founders) | 8              |
| 3               | `crm.lead` — 1 lead per company, type=lead, stage=New  | ~107           |
| **Total** |                                                           | **~225** |

---

### Phase 0 — Tags (created first, then applied)

Tags are applied to **both** contacts and leads — two separate Odoo models:

| Tag name          | Contact model (`res.partner.category`) | Lead model (`crm.tag`)   |
| ----------------- | ---------------------------------------- | -------------------------- |
| `DevOps IT`     | ✓ applied via `category_id`           | ✓ applied via `tag_ids` |
| `ERP–Webshop`  | ✓ applied via `category_id`           | ✓ applied via `tag_ids` |
| `Fintech–Data` | ✓ applied via `category_id`           | ✓ applied via `tag_ids` |

Seeder will `search_or_create` each tag before processing companies.

---

### Phase 1 — Companies

#### A · DevOps / IT (Hungary) — 81 companies

| Company name                        | Website                                     | Note                  |
| ----------------------------------- | ------------------------------------------- | --------------------- |
| Vphone.hu                           | https://www.vphone.hu                       |                       |
| Arteries                            | https://arteries.hu                         |                       |
| Defense Innovation                  | https://defenseinnovation.hu                |                       |
| HM EI Zrt                           | https://hmei.hu                             |                       |
| HM Currus                           | https://www.currus.hu                       |                       |
| HM Arezenal Zrt                     | —                                          |                       |
| REMRED Zrt                          | —                                          |                       |
| 4iG Nyrt                            | https://www.4ig.hu                          |                       |
| OptiGroup Kft (SSC)                 | —                                          |                       |
| Roche SSC                           | https://www.roche.hu                        |                       |
| Allianz Technology                  | https://allianz-technology.com              |                       |
| Kuka SSC Taksony                    | https://www.kuka.com                        |                       |
| Fressnapf SSC                       | https://www.fressnapf.hu                    |                       |
| Nielsen IQ Budapest                 | https://nielseniq.com                       |                       |
| Agora Pay                           | —                                          |                       |
| Amrop Kohlmann & Young Kft          | https://amrop.com                           | merged entry          |
| ApPello Kft                         | —                                          |                       |
| Appello Asseco SEE S.A.             | —                                          |                       |
| Attrecto Zrt                        | https://attrecto.com                        |                       |
| AutSoft Zrt                         | https://autsoft.hu                          |                       |
| Aggreg8.io                          | http://aggreg8.io                           |                       |
| Cherrisk                            | https://www.cherrisk.com                    |                       |
| Cellum                              | https://www.cellum.com                      |                       |
| Commsignia                          | https://commsignia.com                      |                       |
| Complytron                          | https://complytron.com                      |                       |
| Ergománia                          | —                                          |                       |
| Erlang Solutions Hungary Kft        | https://www.erlang-solutions.com            |                       |
| EuroMACC Kft                        | https://euromacc.com                        |                       |
| FX Software Zrt                     | https://fx.hu                               |                       |
| GB & Partners Zrt                   | —                                          |                       |
| Facekom Kft                         | https://facekom.net                         |                       |
| Family Finances                     | https://www.familyfinances.hu               |                       |
| Fundastik                           | http://www.fundastik.com                    |                       |
| FestiPay                            | http://www.festipay.com                     |                       |
| FlexiBill                           | https://flexibill.hu                        |                       |
| INNODOX Technologies Zrt            | https://www.innodox.com                     |                       |
| INTREND Computing Kft               | https://www.intrend.hu                      |                       |
| IThelps Kft                         | —                                          |                       |
| Invitech ICT Services Kft           | https://www.invitech.hu                     |                       |
| Iron Mountain                       | https://www.ironmountain.com                |                       |
| InLock                              | https://inlock.io                           |                       |
| Insurwiz                            | https://insurwiz.io                         |                       |
| LocalTime PR                        | —                                          |                       |
| Loxon                               | https://www.loxon.eu                        |                       |
| Livlia                              | https://livlia.com                          |                       |
| Mastercard Hungary                  | https://www.mastercard.com                  |                       |
| Mindspire Consulting Zrt            | https://mindspire.hu                        |                       |
| Money.hu                            | https://www.money.hu                        |                       |
| MrCoin                              | https://www.mrcoin.eu                       |                       |
| MKB FinTech Lab                     | https://fintechlab.hu                       |                       |
| FintechBlocks                       | https://www.fintechblocks.com               |                       |
| ONLINET Group Zrt                   | https://onlinetgroup.com                    |                       |
| Omikron Magyarország Kft           | —                                          |                       |
| OTP Lab                             | https://www.otpbank.hu/portal/en/OTPLAB_ENG |                       |
| Qualco                              | https://qualco.eu                           |                       |
| Qualysoft Informatikai Zrt          | https://qualysoft.com                       |                       |
| Quattrosoft Kft                     | —                                          |                       |
| R-Szoft Kft                         | https://r-szoft.hu                          |                       |
| Recash Ltd                          | —                                          |                       |
| Rowan Hill                          | http://www.rowanhillglobal.hu               |                       |
| Rollet                              | https://rollet.hu                           |                       |
| Riport                              | https://riport.co.hu                        |                       |
| UpScale                             | —                                          |                       |
| Vialto Consulting Kft               | https://vialto.com                          |                       |
| Virgo Systems Kft                   | —                                          |                       |
| W.UP                                | https://wup.digital                         | rebranded as Finshape |
| VERN                                | http://www.vernhelps.com                    |                       |
| Virpay                              | https://virpay.hu                           |                       |
| IzzyPay                             | https://izzypay.hu                          |                       |
| Tesco Hungary                       | https://www.tesco.hu                        |                       |
| Bosch Innovation Center Budapest    | https://www.bosch.hu                        |                       |
| Bitrise                             | https://bitrise.io                          |                       |
| Greehill                            | https://www.greehill.com                    |                       |
| Tresorit                            | https://tresorit.com                        |                       |
| Squer                               | https://www.squer.io                        | AT/DE company         |
| Digital Thinkers                    | —                                          |                       |
| Supercharge                         | https://supercharge.io                      |                       |
| Big Fish Internet-Technológiai Kft | https://bigfish.hu                          |                       |
| Runiosit                            | https://runiosit.com                        |                       |

---

#### B · DevOps / IT (International) — 12 companies

| Company name                              | Country | Website                       |
| ----------------------------------------- | ------- | ----------------------------- |
| AboutYou                                  | DE      | https://corporate.aboutyou.de |
| Zalando                                   | DE      | https://jobs.zalando.com      |
| Flipper Devices                           | DE      | https://flipperdevices.com    |
| DISH (Digital Infrastructure & Solutions) | DE      | https://www.dish.co           |
| CEWE                                      | DE      | https://www.cewe.de           |
| Klarna                                    | SE      | https://klarna.com            |
| Affirm                                    | US      | https://affirm.com            |
| Afterpay                                  | AU      | https://afterpay.com          |
| Continental                               | DE      | https://www.continental.com   |
| Mergify                                   | FR      | https://mergify.com           |
| Tetrate                                   | US      | https://tetrate.io            |
| ClickUp                                   | US      | https://clickup.com           |

---

#### C · ERP / Webshop — 13 companies

| Company name  | Country | Website                   |
| ------------- | ------- | ------------------------- |
| Shoprenter    | HU      | https://www.shoprenter.hu |
| Shopify       | CA      | https://www.shopify.com   |
| Unas          | HU      | https://unas.hu           |
| Cargoson      | EE      | https://www.cargoson.com  |
| Valkuz        | HU      | https://valkuz.hu         |
| Wildom        | HU      | https://wildom.com        |
| VShosting     | CZ      | https://vshosting.hu      |
| Online-ERP.hu | HU      | https://www.online-erp.hu |
| Oregional     | HU      | https://oregional.hu      |
| Hungarodo     | HU      | https://hungarodo.hu      |
| Dotech        | HU      | https://www.dotech.hu     |
| BDSC          | HU      | https://www.bdsc.hu       |
| Eyssen        | HU      | https://www.eyssen.hu     |

---

#### D · Fintech / Data — 12 companies

| Company name                       | Country | Website                    |
| ---------------------------------- | ------- | -------------------------- |
| BerenyiSoft Kft                    | HU      | https://berenyisoft.com    |
| Datapao                            | HU      | https://datapao.com        |
| WorldQuant                         | US      | https://www.worldquant.com |
| SEON                               | HU      | https://seon.io            |
| Péntech / PastPay                 | HU      | https://pentech.hu         |
| Perfinal                           | HU      | https://perfinal.com       |
| FintechX                           | HU      | https://fintechx.digital   |
| Swipe Technologies (Salarify)      | HU      | https://salarify.me        |
| Acounto                            | HU      | —                         |
| Smartsurance Technologies (Cristo) | HU      | —                         |
| Fintrous Group                     | HU      | https://fintrous.com       |
| Erste BankSpiration                | HU      | https://www.erstebank.hu   |

> `Fintrous Group`, `PastPay`, and `Instacash` also appeared in the DevOps raw list — deduplicated here under Fintech.

---

### Phase 2 — Individual contacts (Fintech founders / CEOs)

Linked to their parent company. Tag: `Fintech–Data`.

| Name              | Company                            | Title           |
| ----------------- | ---------------------------------- | --------------- |
| Kádár Tamás    | SEON                               | CEO, co-founder |
| Berényi Benjamin | Péntech / PastPay                 | co-founder      |
| Brezovszki Máté | Perfinal                           | CEO             |
| Mudri György     | FintechX                           | CEO             |
| Radák Bence      | Swipe Technologies (Salarify)      | CEO, co-founder |
| Brachmann Ferenc  | Acounto                            | co-founder      |
| Szota Szabolcs    | Smartsurance Technologies (Cristo) | co-founder      |
| Bruzsa Géza      | Fintrous Group                     | CEO             |

---

### Phase 3 — CRM Leads

- **1 lead per company** (not per individual), type = `lead`, stage = first stage (New/Incoming)
- Lead name pattern: `{Company} — {Category} Outreach`
- Linked to the company partner from Phase 1 via `partner_id`
- Tag applied: `DevOps IT` / `ERP–Webshop` / `Fintech–Data` (same name as contact tag, separate `crm.tag` object)
- `expected_revenue`: 0 (filled manually)
- Idempotent: skip by lead name if already exists

---

### Skipped (ambiguous raw entries)

The following raw mentions have no clean company identity and will be skipped:
`Spar3d`, `Hearsay`, `Cégjelző`, `Capital Portal`, `Creative Selector`, `Riskaware`, `Metapay`, `forex brokerstars`, `frix.hu`, `Functional Finances`, `InfoCert`, `Infotér`, `InnovITech`, `Opmasys`, `Online Üzleti Informatika Zrt`, `Work Force Kft`, `e-Postoffice Kft`, `Világgazdasági Intézet`, `DevOps Excellence` (Kununu-only URL)

---

> **Status: DRAFT — awaiting approval. Reply "approved" or with corrections.**
