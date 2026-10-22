"""Full install from GitHub: bootstrap lazy.nvim, restore the lockfile, start for real.

Skipped by default; run with `pytest --run-network` (or NVIM_SETTINGS_NETWORK_TESTS=1).
"""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

import pytest

from conftest import REPO, Nvim

pytestmark = pytest.mark.network


@pytest.fixture(scope="module")
def installed(nvim_bin: str, tmp_path_factory: pytest.TempPathFactory) -> Nvim:
    nv = Nvim(nvim_bin, tmp_path_factory.mktemp("network"))
    env = nv.env(safe=False)
    gitconfig = Path(os.path.expanduser("~/.gitconfig"))
    if gitconfig.is_file():  # proxies/credentials for the clone; read-only
        env["GIT_CONFIG_GLOBAL"] = str(gitconfig)
    proc = subprocess.run(
        [nvim_bin, "--headless", "+Lazy! restore", "+qa"],
        env=env,
        cwd=nv.root,
        capture_output=True,
        text=True,
        timeout=900,
        stdin=subprocess.DEVNULL,
    )
    assert proc.returncode == 0, proc.stderr
    nv.git_env = env  # type: ignore[attr-defined]
    return nv


def test_plugins_match_lockfile(installed: Nvim) -> None:
    lock = json.loads((REPO / "lazy-lock.json").read_text())
    lazy_root = installed.data_dir / "lazy"
    assert sorted(p.name for p in lazy_root.iterdir()) == sorted(lock)
    for name, entry in lock.items():
        head = subprocess.run(
            ["git", "-C", str(lazy_root / name), "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
        assert head == entry["commit"], name


def test_starts_cleanly_with_real_plugins(installed: Nvim) -> None:
    res = installed.run(
        """
        vim.api.nvim_exec_autocmds("User", { pattern = "VeryLazy" })
        local mods = {}
        for _, m in ipairs({ "dap", "dapui", "dap-python", "telescope", "blink.cmp", "lualine",
                             "nvim-tree", "mason", "tree-sitter-manager", "osv" }) do
          mods[m] = (pcall(require, m))
        end
        local spec = require("lazy.core.config").spec
        return {
          colors = vim.g.colors_name,
          notifs = vim.tbl_map(function(n) return n.msg end, spec.notifs),
          mods = mods,
          cmds = { Mason = vim.fn.exists(":Mason"), Tools = vim.fn.exists(":MasonInstallTools"),
                   TSManager = vim.fn.exists(":TSManager"), Telescope = vim.fn.exists(":Telescope") },
        }
        """,
        safe=False,
        timeout=120,
    )
    res.assert_clean()
    r = res.result
    assert r["colors"] == "dracula"
    assert r["notifs"] in ([], {})
    assert all(r["mods"].values()), r["mods"]
    assert r["cmds"] == {"Mason": 2, "Tools": 2, "TSManager": 2, "Telescope": 2}


def test_lazy_health_finds_no_spec_problems(installed: Nvim) -> None:
    res = installed.run(
        """
        vim.cmd("checkhealth lazy")
        return table.concat(vim.api.nvim_buf_get_lines(0, 0, -1, false), "\\n")
        """,
        safe=False,
        timeout=120,
    )
    res.assert_clean()
    assert "unknown key" not in res.result
    assert "ERROR" not in res.result
    assert "Issues were reported" not in res.result


def test_lua_buffer_gets_treesitter_highlighting(installed: Nvim, tmp_path: Path) -> None:
    lua_file = tmp_path / "x.lua"
    lua_file.write_text("local x = 1\nreturn x\n")
    res = installed.run(
        f"""
        vim.cmd.edit({str(lua_file)!r})
        return vim.treesitter.highlighter.active[vim.api.nvim_get_current_buf()] ~= nil
        """,
        safe=False,
        timeout=120,
    )
    res.assert_clean()
    assert res.result is True


def test_dap_python_adapter_registered(installed: Nvim) -> None:
    res = installed.run(
        """
        require("lazy").load({ plugins = { "nvim-dap" } })
        local dap = require("dap")
        return {
          python = type(dap.adapters.python),
          nlua = type(dap.adapters.nlua),
          configs = #(dap.configurations.python or {}),
        }
        """,
        safe=False,
        timeout=120,
    )
    res.assert_clean()
    assert res.result["python"] == "function"
    assert res.result["nlua"] == "function"
    assert res.result["configs"] > 0
