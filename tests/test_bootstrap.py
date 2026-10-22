"""lua/config/lazy.lua: bootstrapping lazy.nvim at the commit pinned in lazy-lock.json (offline)."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

from conftest import Nvim

GIT = ["git", "-c", "user.name=t", "-c", "user.email=t@example.com", "-c", "commit.gpgsign=false"]


def make_repo(path: Path) -> list[str]:
    """A local stand-in for github.com/folke/lazy.nvim with two commits on `stable`."""
    path.mkdir()
    subprocess.run([*GIT, "init", "-q", "-b", "stable", str(path)], check=True)
    commits = []
    for n in (1, 2):
        (path / "lua").mkdir(exist_ok=True)
        (path / "lua" / f"v{n}.lua").write_text(f"return {n}\n")
        subprocess.run([*GIT, "-C", str(path), "add", "."], check=True)
        subprocess.run([*GIT, "-C", str(path), "commit", "-q", "-m", f"v{n}"], check=True)
        head = subprocess.run(
            ["git", "-C", str(path), "rev-parse", "HEAD"], capture_output=True, text=True, check=True
        )
        commits.append(head.stdout.strip())
    return commits


BOOTSTRAP = """
local lazy = require("config.lazy")
lazy.repo = {repo}
local ok = lazy.bootstrap()
local head = vim.trim(vim.fn.system({{ "git", "-C", lazy.path(), "rev-parse", "HEAD" }}))
return {{ ok = ok, head = head, locked = lazy.locked_commit() or vim.NIL }}
"""


def test_bootstrap_checks_out_locked_commit(nvim: Nvim, tmp_path: Path) -> None:
    first, _second = make_repo(tmp_path / "lazy-src")
    lock_path = nvim.config_dir / "lazy-lock.json"
    lock = json.loads(lock_path.read_text())
    lock["lazy.nvim"]["commit"] = first
    lock_path.write_text(json.dumps(lock))
    res = nvim.run(BOOTSTRAP.format(repo=json.dumps(str(tmp_path / "lazy-src"))))
    res.assert_clean()
    assert res.result == {"ok": True, "head": first, "locked": first}


def test_bootstrap_without_lockfile_uses_stable(nvim: Nvim, tmp_path: Path) -> None:
    _first, second = make_repo(tmp_path / "lazy-src")
    (nvim.config_dir / "lazy-lock.json").unlink()
    res = nvim.run(BOOTSTRAP.format(repo=json.dumps(str(tmp_path / "lazy-src"))))
    res.assert_clean()
    assert res.result == {"ok": True, "head": second, "locked": None}


def test_bootstrap_failure_is_reported_not_raised(nvim: Nvim, tmp_path: Path) -> None:
    res = nvim.run(BOOTSTRAP.format(repo=json.dumps(str(tmp_path / "does-not-exist"))))
    assert res.ok, res.error
    assert res.result["ok"] is False
    assert "Failed to clone lazy.nvim" in res.messages
