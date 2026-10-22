""":checkhealth config and the Mason tool list."""

from __future__ import annotations

from pathlib import Path

from conftest import Nvim

HEALTH = """
vim.cmd("checkhealth config")
return table.concat(vim.api.nvim_buf_get_lines(0, 0, -1, false), "\\n")
"""


def test_checkhealth_config_runs(nvim: Nvim) -> None:
    res = nvim.run(HEALTH)
    res.assert_clean()
    report = res.result
    for section in ("Neovim ~", "Plugins ~", "External tools ~", "Python ~"):
        assert section in report
    assert "(>= 0.11 required)" in report
    assert "Safe mode (NVIM_NO_PLUGINS) is on" in report
    assert "lazy-lock.json found" in report
    assert "format on save: on" in report


def test_checkhealth_reports_missing_tools(nvim: Nvim) -> None:
    res = nvim.run(HEALTH, env={"PATH": "/nonexistent"})
    res.assert_clean()
    assert "ERROR git not found" in res.result
    assert "WARNING basedpyright-langserver not found" in res.result
    assert "Run :MasonInstallTools (or pip install basedpyright)" in res.result


def test_checkhealth_reports_venv(nvim: Nvim, tmp_path: Path) -> None:
    python = tmp_path / "proj" / ".venv" / "bin" / "python"
    python.parent.mkdir(parents=True)
    python.write_text("")
    res = nvim.run(HEALTH, cwd=tmp_path / "proj")
    res.assert_clean()
    assert f"virtualenv: {tmp_path / 'proj' / '.venv'}" in res.result


def test_checkhealth_without_lockfile(nvim: Nvim) -> None:
    (nvim.config_dir / "lazy-lock.json").unlink()
    res = nvim.run(HEALTH)
    res.assert_clean()
    assert "lazy-lock.json missing" in res.result


def test_missing_packages(nvim: Nvim) -> None:
    res = nvim.run(
        """
        local tools = require("config.tools")
        local installed = { ruff = true, debugpy = true }
        return {
          all = tools.mason_packages,
          missing = tools.missing_packages(function(name) return installed[name] == true end),
        }
        """
    )
    res.assert_clean()
    assert res.result["all"] == ["basedpyright", "ruff", "lua-language-server", "debugpy", "tree-sitter-cli"]
    assert res.result["missing"] == ["basedpyright", "lua-language-server", "tree-sitter-cli"]
