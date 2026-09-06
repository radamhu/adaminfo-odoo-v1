# Migration Baseline — adaminfo-prod-1139 (old environment)

Captured 2026-09-06 via Playwright against `https://adaminfo-prod-1139.apps.oec.sh`, logged in as `admin`
(credentials from `.env.prod`). This is the "before" snapshot Task 5's post-restore diff compares against.

## Installed modules (71)

Source: Settings → Apps, Filters → Installed (with the default "Apps" category filter removed to show the
full technical module list, not just top-level application modules). Screenshot: `apps-installed-old.png`.
Name + version were confirmed via the same authenticated session against `ir.module.module`
(`state = installed`, fields `name` / `shortdesc` / `installed_version`) since the Apps kanban cards show
technical name but not version.

| Technical Name | Display Name | Installed Version |
|---|---|---|
| account | Invoicing | 18.0.1.3 |
| account_add_gln | Add Partner GLN | 18.0.1.0 |
| account_edi_ubl_cii | Import/Export electronic invoices with UBL/CII | 18.0.1.0 |
| account_payment | Payment - Account | 18.0.2.0 |
| analytic | Analytic Accounting | 18.0.1.2 |
| auth_signup | Signup | 18.0.1.0 |
| auth_totp | Two-Factor Authentication (TOTP) | 18.0.1.0 |
| auth_totp_mail | 2FA Invite mail | 18.0.1.0 |
| auth_totp_portal | TOTPortal | 18.0.1.0 |
| base | Base | 18.0.1.3 |
| base_import | Base import | 18.0.2.0 |
| base_import_module | Base import module | 18.0.1.0 |
| base_install_request | Base - Module Install Request | 18.0.1.0 |
| base_setup | Initial Setup Tools | 18.0.1.0 |
| bus | IM Bus | 18.0.1.0 |
| calendar | Calendar | 18.0.1.1 |
| calendar_sms | Calendar - SMS | 18.0.1.1 |
| contacts | Contacts | 18.0.1.0 |
| crm | CRM | 18.0.1.8 |
| crm_iap_enrich | Lead Enrichment | 18.0.1.1 |
| crm_iap_mine | Lead Generation | 18.0.1.2 |
| crm_sms | SMS in CRM | 18.0.1.1 |
| digest | KPI Digests | 18.0.1.1 |
| document_knowledge | Documents Knowledge | 18.0.1.0.2 |
| google_gmail | Google Gmail | 18.0.1.2 |
| html_editor | HTML Editor | 18.0.1.0 |
| http_routing | Web Routing | 18.0.1.0 |
| iap | In-App Purchases | 18.0.1.1 |
| iap_crm | IAP / CRM | 18.0.1.0 |
| iap_mail | IAP / Mail | 18.0.1.0 |
| mail | Discuss | 18.0.1.18 |
| mail_bot | OdooBot | 18.0.1.2 |
| onboarding | Onboarding Toolbox | 18.0.1.2 |
| partner_autocomplete | Partner Autocomplete | 18.0.1.1 |
| payment | Payment Engine | 18.0.2.0 |
| phone_validation | Phone Numbers Validation | 18.0.2.1 |
| portal | Customer Portal | 18.0.1.0 |
| portal_rating | Portal Rating | 18.0.1.0 |
| privacy_lookup | Privacy | 18.0.1.0 |
| product | Products & Pricelists | 18.0.1.2 |
| project | Project | 18.0.1.3 |
| project_account | Project - Account | 18.0.1.0 |
| project_sms | Project - SMS | 18.0.1.1 |
| project_todo | To-Do | 18.0.1.0 |
| rating | Customer Rating | 18.0.1.1 |
| resource | Resource | 18.0.1.1 |
| resource_mail | Resource Mail | 18.0.1.0 |
| sale | Sales | 18.0.1.2 |
| sale_async_emails | Sales - Async Emails | 18.0.1.0 |
| sale_crm | Opportunity to Quotation | 18.0.1.0 |
| sale_edi_ubl | Import electronic orders with UBL | 18.0.1.0 |
| sale_management | Sales | 18.0.1.0 |
| sale_pdf_quote_builder | Sales PDF Quotation Builder | 18.0.1.0 |
| sale_project | Sales - Project | 18.0.1.0 |
| sale_service | Sales - Service | 18.0.1.0 |
| sale_sms | Sale - SMS | 18.0.1.0 |
| sales_team | Sales Teams | 18.0.1.1 |
| sms | SMS gateway | 18.0.3.0 |
| snailmail | Snail Mail | 18.0.0.4 |
| snailmail_account | Snail Mail - Account | 18.0.0.1 |
| spreadsheet | Spreadsheet | 18.0.1.0 |
| spreadsheet_account | Spreadsheet Accounting Formulas | 18.0.1.0 |
| spreadsheet_dashboard | Spreadsheet dashboard | 18.0.1.0 |
| spreadsheet_dashboard_account | Spreadsheet dashboard for accounting | 18.0.1.0 |
| spreadsheet_dashboard_sale | Spreadsheet dashboard for sales | 18.0.1.0 |
| uom | Units of measure | 18.0.1.0 |
| utm | UTM Trackers | 18.0.1.1 |
| web | Web | 18.0.1.0 |
| web_editor | Web Editor | 18.0.1.0 |
| web_tour | Tours | 18.0.1.0 |
| web_unsplash | Unsplash Image Library | 18.0.1.1 |

## Scheduled Actions (26)

Source: Settings → Technical → Automation → Scheduled Actions (dev mode via `?debug=1`). Screenshot:
`scheduled-actions-old.png`.

| Action Name | Model | Active |
|---|---|---|
| Account: Post draft entries with auto_post enabled and accounting date up to today | Journal Entry | Yes |
| automatic invoicing: send ready invoice | Payment Transaction | No |
| Base: Auto-vacuum internal data | Automatic Vacuum | Yes |
| Base: Portal Users Deletion | Users Deletion Request | Yes |
| Calendar: Event Reminder | Event Alarm Manager | Yes |
| CRM: enrich leads (IAP) | Lead/Opportunity | Yes |
| CRM: Lead Assignment | Sales Team | No |
| Digest Emails | Digest | Yes |
| Discuss: channel member unmute | Channel Member | Yes |
| Discuss: users settings unmute | User Settings | Yes |
| Mail: Email Queue Manager | Outgoing Mails | Yes |
| Mail: Fetchmail Service | Incoming Mail Server | No |
| Mail: Post scheduled messages | Scheduled Message | Yes |
| Mail: send web push notification | Push Notifications | Yes |
| Notification: Delete Notifications older than 6 Month | Message Notifications | Yes |
| Notification: Notify scheduled messages | Scheduled Messages | Yes |
| Partner Autocomplete: Sync with remote DB | Partner Autocomplete Sync | Yes |
| Payment: Post-process transactions | Payment Transaction | No |
| Predictive Lead Scoring: Recompute Automated Probabilities | Lead/Opportunity | No |
| Project: Send rating | Project | Yes |
| Sale Pdf Quote Builder: assign form fields to documents post upgrade | Form fields of inside quotation documents. | Yes |
| Sales: Send pending emails | Sales Order | Yes |
| Send invoices automatically | Journal Entry | Yes |
| SMS: SMS Queue Manager | Outgoing SMS | Yes |
| Snailmail: process letters queue | Snailmail Letter | Yes |
| Users: Notify About Unregistered Users | User | Yes |

Active count: 21 active, 5 inactive (automatic invoicing: send ready invoice; CRM: Lead Assignment;
Mail: Fetchmail Service; Payment: Post-process transactions; Predictive Lead Scoring: Recompute Automated
Probabilities).
