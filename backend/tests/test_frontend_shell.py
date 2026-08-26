"""S5: оболочка вкладок и вынесенные css/js на месте."""
from pathlib import Path

FRONTEND = Path(__file__).resolve().parents[2] / "frontend"

REQUIRED_IDS = [
    "login-screen",
    "project-screen",
    "main-screen",
    "tab-home",
    "tab-expenses",
    "tab-masters",
    "tab-payments",
    "tab-dashboard",
    "tab-report",
    "tab-tasks",
    "tab-profile",
    "nav-home",
    "nav-expenses",
    "nav-masters",
    "nav-tasks",
    "phone-input",
    "add-sheet",
    "toast",
]


def test_shell_keeps_screens_and_tabs():
    html = (FRONTEND / "index.html").read_text(encoding="utf-8")
    for i in REQUIRED_IDS:
        assert f'id="{i}"' in html, i
    assert 'href="/css/app.css"' in html
    assert 'src="/js/app.js"' in html
    assert "<style>" not in html
    assert "<script type=\"module\">" not in html


def test_extracted_assets_keep_behavior_hooks():
    css = (FRONTEND / "css" / "app.css").read_text(encoding="utf-8")
    js = (FRONTEND / "js" / "app.js").read_text(encoding="utf-8")
    assert "--blue:" in css
    assert "window.padPress" in js
    assert "window.showTab" in js
    assert "from '/api.js'" in js


async def test_static_css_js_served(client):
    css = await client.get("/css/app.css")
    assert css.status_code == 200
    assert "--blue" in css.text
    js = await client.get("/js/app.js")
    assert js.status_code == 200
    assert "padPress" in js.text
    page = await client.get("/index.html")
    assert page.status_code == 200
    assert 'id="tab-home"' in page.text
    assert 'href="/css/app.css"' in page.text


def test_sw_updates_without_incognito():
    sw = (FRONTEND / "sw.js").read_text(encoding="utf-8")
    js = (FRONTEND / "js" / "app.js").read_text(encoding="utf-8")
    assert "welldom-v22" in sw
    assert 'cache: "no-store"' in sw
    assert "_isAppShell" in sw
    assert "updateViaCache: 'none'" in js
    assert "controllerchange" in js


async def test_sw_js_not_http_cached(client):
    r = await client.get("/sw.js")
    assert r.status_code == 200
    assert "welldom-v22" in r.text
    cc = r.headers.get("cache-control", "").lower()
    assert "no-store" in cc or "no-cache" in cc
