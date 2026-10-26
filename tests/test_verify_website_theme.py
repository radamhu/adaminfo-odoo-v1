from unittest.mock import MagicMock, patch

from seed.verify_website_theme import KEYS, check_theme_rollout

LINKEDIN = "https://www.linkedin.com/in/adaminformatika"
FORM_OK = (
    '<form id="contactus_form"><input type="hidden" class="form-control s_website_form_input" '
    'name="email_to" value="roland@adaminformatika.hu"/></form>'
)
FORM_EMPTY = '<form id="contactus_form"><input type="hidden" name="email_to"/></form>'
FORM_BLANK = '<form id="contactus_form"><input type="hidden" name="email_to" value=""/></form>'


def _state(**over):
    state = {
        "module": [{"state": "installed", "installed_version": "18.0.1.1.0"}],
        "website": [{"id": 1, "name": "Adam Informatika", "social_linkedin": LINKEDIN}],
        "footer_minimalist": [{"id": 10, "website_id": [1, "Adam Informatika"], "active": True}],
        "footer_override": [{"id": 11, "website_id": [1, "Adam Informatika"], "active": True}],
        "contact": [{"id": 12, "website_id": [1, "Adam Informatika"], "arch_db": FORM_OK}],
    }
    state.update(over)
    return state


def _run(state):
    """Run check_theme_rollout against a mocked XML-RPC server."""
    def execute_kw(db, uid, pw, model, method, args, kwargs):
        domain = args[0]
        if model == "ir.module.module":
            return state["module"]
        if model == "website":
            return state["website"]
        assert model == "ir.ui.view"
        assert kwargs.get("context") == {"active_test": False}
        key = next(v for f, _, v in domain if f == "key")
        name = {
            "website.template_footer_minimalist": "footer_minimalist",
            "website_adaminfo_theme.footer_minimalist_content": "footer_override",
            "website_adaminfo_theme.section_contact": "contact",
        }[key]
        rows = state[name]
        # emulate server-side website_id/active filtering when present in the domain
        for f, _, v in domain:
            if f == "website_id":
                rows = [r for r in rows if (r["website_id"] or [False])[0] == v]
            if f == "active":
                rows = [r for r in rows if r.get("active", True) == v]
        return rows

    with patch("xmlrpc.client.ServerProxy") as mock_proxy:
        common = MagicMock()
        common.authenticate.return_value = 7
        models = MagicMock()
        models.execute_kw.side_effect = execute_kw
        mock_proxy.side_effect = [common, models]
        from seed.connection import OdooClient
        client = OdooClient("http://x", "db", "admin", "pw")
        return check_theme_rollout(client)


def test_all_checks_pass_on_dev_like_state():
    assert _run(_state()) == dict.fromkeys(KEYS, True)


def test_empty_email_to_fails_form_recipient_check():
    for arch in (FORM_EMPTY, FORM_BLANK):
        state = _state(contact=[{"id": 12, "website_id": [1, "x"], "arch_db": arch}])
        assert _run(state)["form_recipient_set"] is False


def test_generic_only_minimalist_view_fails():
    state = _state(footer_minimalist=[{"id": 10, "website_id": False, "active": True}])
    assert _run(state)["footer_minimalist"] is False


def test_keys_are_exact():
    assert set(_run(_state())) == {
        "theme_installed", "website_named", "linkedin_set",
        "footer_minimalist", "footer_override", "form_recipient_set",
    }


def test_theme_wrong_version_or_state_fails():
    for row in ({"state": "installed", "installed_version": "18.0.1.0.0"},
                {"state": "to upgrade", "installed_version": "18.0.1.1.0"}):
        assert _run(_state(module=[row]))["theme_installed"] is False
    assert _run(_state(module=[]))["theme_installed"] is False


def test_website_name_and_linkedin_failures():
    state = _state(website=[{"id": 1, "name": "My Website", "social_linkedin": False}])
    result = _run(state)
    assert result["website_named"] is False
    assert result["linkedin_set"] is False


def test_footer_override_missing_or_inactive_fails():
    assert _run(_state(footer_override=[]))["footer_override"] is False
    inactive = [{"id": 11, "website_id": [1, "x"], "active": False}]
    assert _run(_state(footer_override=inactive))["footer_override"] is False


def test_website_specific_contact_copy_preferred_over_generic():
    state = _state(contact=[
        {"id": 1, "website_id": False, "arch_db": FORM_OK},
        {"id": 2, "website_id": [1, "x"], "arch_db": FORM_EMPTY},
    ])
    assert _run(state)["form_recipient_set"] is False


def test_generic_contact_used_when_no_website_copy():
    state = _state(contact=[{"id": 1, "website_id": False, "arch_db": FORM_OK}])
    assert _run(state)["form_recipient_set"] is True


def test_contact_view_missing_fails():
    assert _run(_state(contact=[]))["form_recipient_set"] is False


def test_search_read_context_only_sent_when_given():
    with patch("xmlrpc.client.ServerProxy") as mock_proxy:
        common = MagicMock(); common.authenticate.return_value = 7
        models = MagicMock(); models.execute_kw.return_value = []
        mock_proxy.side_effect = [common, models]
        from seed.connection import OdooClient
        c = OdooClient("http://x", "db", "a", "p")
        c.search_read("m", [], ["f"])
        assert "context" not in models.execute_kw.call_args[0][6]
        c.search_read("m", [], ["f"], context={"active_test": False})
        assert models.execute_kw.call_args[0][6]["context"] == {"active_test": False}
