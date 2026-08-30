from pathlib import Path


ROOT = Path(__file__).parents[2]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_console_exposes_all_four_erp_permissions():
    source = read("static/console/console.js")
    for code in ("erp.endpoint.view", "erp.push.operate", "erp.log.view"):
        assert source.count(f"'{code}'") == 1
    assert source.count("'erp.endpoint.manage'") == 2
    assert "'erp.endpoint.manage'" in source.split("var FORBIDDEN_CODES", 1)[1]


def test_console_erp_permission_copy_exists_in_all_languages():
    source = read("static/console/console-i18n.js")
    for key in (
        "mod_erp",
        "pc_erp_endpoint_view",
        "pc_erp_endpoint_manage",
        "pc_erp_push_operate",
        "pc_erp_log_view",
    ):
        assert source.count(key + ":") == 4
