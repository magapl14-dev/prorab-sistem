"""S6: mobile/www — копия frontend; сборка Capacitor зовёт sync-web."""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
FRONTEND = REPO / "frontend"
WWW = REPO / "mobile" / "www"
SYNC = REPO / "mobile" / "sync-web.js"
PACKAGE = REPO / "mobile" / "package.json"

CACHE_RE = re.compile(r'CACHE\s*=\s*"([^"]+)"')
BUILD_SCRIPTS = ("open:android", "open:ios", "build:android", "build:android:debug")


def _files(root: Path) -> dict[str, bytes]:
    out = {}
    for p in root.rglob("*"):
        if p.is_file():
            out[p.relative_to(root).as_posix()] = p.read_bytes()
    return out


def test_build_scripts_call_sync_web():
    scripts = json.loads(PACKAGE.read_text(encoding="utf-8"))["scripts"]
    assert scripts.get("sync-web") == "node sync-web.js"
    for name in BUILD_SCRIPTS:
        cmd = scripts[name]
        assert "sync-web" in cmd, name
        assert cmd.strip().startswith("npm run sync-web"), name


def test_sync_web_mirrors_frontend_and_sw_version():
    proc = subprocess.run(
        ["node", str(SYNC)],
        cwd=str(REPO / "mobile"),
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stderr or proc.stdout
    fe = _files(FRONTEND)
    www = _files(WWW)
    assert fe.keys() == www.keys()
    for rel in fe:
        assert fe[rel] == www[rel], rel
    fe_cache = CACHE_RE.search((FRONTEND / "sw.js").read_text(encoding="utf-8"))
    www_cache = CACHE_RE.search((WWW / "sw.js").read_text(encoding="utf-8"))
    assert fe_cache and www_cache
    assert fe_cache.group(1) == www_cache.group(1)
    assert fe_cache.group(1).startswith("welldom-v")
    assert "css/app.css" in fe
    assert "js/app.js" in fe
