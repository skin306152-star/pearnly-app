from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_cowork_integration_uses_the_identity_panel_without_bot_copy():
    page = read("src/home/page-integrations.ts")
    assert 'id="cowork-line-integration-row"' in page
    assert 'data-cowork-line-copy="productName"' in page
    assert 'data-cowork-line-copy="productDescription"' in page
    assert "initCoworkLineSummary(sec)" in page
    assert "erpLineBindingMarkup" in page
    assert "/api/line/erp/binding-code" in page


def test_cowork_identity_panel_calls_only_the_new_contract():
    source = read("src/home/cowork-line/identity-panel.ts")
    assert source.count("'/api/cowork-line/identity'") == 3
    assert "'/api/cowork-line/binding-code'" in source
    assert "method: 'POST'" in source
    assert "method: 'DELETE'" in source
    assert "/api/line/binding" not in source
    assert "/api/cowork-line/connect/start" not in source
    assert "subscribeI18n?.('cowork-line-identity'" in source
    assert "friendship_ready" in source
    assert "https://line.me/R/ti/p/@pearnly" in source
    assert 'class="linebot-steps"' in source
    assert source.count('class="linebot-step-no"') == 3
    assert "添加 Pearnly Cowork 为好友" in source
    assert "把这组 6 位数字发给 Bot" in source
    assert "等待绑定完成" in source
    assert "在 LINE 打开" in source


def test_drawer_mounts_cowork_identity_instead_of_the_legacy_bot_panel():
    source = read("src/home/integration-drawer.ts")
    assert "mountCoworkLineIdentity(body)" in source
    assert "window._loadLineBotPanel" not in source
    assert "line: 'linebot'" not in source
    assert not (ROOT / "src/home/line-panel.ts").exists()


def test_console_invites_by_email_and_keeps_the_copy_link_result():
    source = read("static/console/console.js")
    assert 'data-ch="line"' not in source
    assert "inv_target_line" not in source
    assert "channel: 'email'" in source
    assert "j.invite_url" in source
    assert "navigator.clipboard.writeText(j.invite_url)" in source


def test_console_invite_copy_has_no_line_contact_keys_in_any_language():
    source = read("static/console/console-i18n.js")
    for key in ("inv_channel", "inv_line", "inv_target_line", "inv_line_tip"):
        assert key + ":" not in source
    assert source.count("inv_target_email:") == 4
