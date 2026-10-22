"""Real language servers (basedpyright + ruff) attached through the native LSP config.

These run offline in safe mode, but need the servers installed. They are skipped
without them; `pip install --group lsp` (or Mason) provides both.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from conftest import Nvim, find_tool

pytestmark = pytest.mark.lsp

PYRIGHT = find_tool("basedpyright-langserver")
RUFF = find_tool("ruff")
needs_servers = pytest.mark.skipif(
    not (PYRIGHT and RUFF), reason="basedpyright-langserver and ruff are not installed"
)

ATTACH = """
vim.cmd.edit("main.py")
vim.wait(30000, function() return #vim.lsp.get_clients({ bufnr = 0 }) >= 2 end, 100)
"""


@pytest.fixture
def project(tmp_path: Path) -> Path:
    proj = tmp_path / "proj"
    (proj / ".venv" / "bin").mkdir(parents=True)
    fake_python = proj / ".venv" / "bin" / "python"
    fake_python.write_text('#!/bin/sh\nexec python3 "$@"\n')
    fake_python.chmod(0o755)
    (proj / "pyproject.toml").write_text('[project]\nname = "demo"\nversion = "0"\n')
    (proj / "main.py").write_text("import sys\nimport os\nx  =  1\nprint( os.sep,sys.argv )\n")
    return proj


def server_path() -> dict[str, str]:
    dirs = {str(Path(PYRIGHT).parent), str(Path(RUFF).parent)}  # type: ignore[arg-type]
    return {"PATH": os.pathsep.join([*dirs, os.environ.get("PATH", "")])}


@needs_servers
def test_servers_attach_with_project_venv(nvim: Nvim, project: Path) -> None:
    res = nvim.run(
        ATTACH
        + """
        local out = { clients = {} }
        for _, c in ipairs(vim.lsp.get_clients({ bufnr = 0 })) do
          out.clients[#out.clients + 1] = c.name
          if c.name == "basedpyright" then
            out.python = c.settings.python.pythonPath
            out.root = c.root_dir
          elseif c.name == "ruff" then
            out.ruff_hover = c.server_capabilities.hoverProvider
          end
        end
        table.sort(out.clients)
        out.gd = vim.fn.maparg("gd", "n", false, true).desc
        out.cf = vim.fn.maparg(",cf", "n", false, true).desc
        return out
        """,
        cwd=project,
        env=server_path(),
    )
    res.assert_clean()
    assert res.result == {
        "clients": ["basedpyright", "ruff"],
        "python": str(project / ".venv" / "bin" / "python"),
        "root": str(project),
        "ruff_hover": False,
        "gd": "LSP: Go to definition",
        "cf": "LSP: Format buffer",
    }


@needs_servers
def test_ruff_reports_unsorted_imports(nvim: Nvim, project: Path) -> None:
    res = nvim.run(
        ATTACH
        + """
        vim.wait(15000, function() return #vim.diagnostic.get(0) > 0 end, 100)
        return vim.tbl_map(function(d) return d.code end, vim.diagnostic.get(0))
        """,
        cwd=project,
        env=server_path(),
    )
    res.assert_clean()
    assert "I001" in res.result


@needs_servers
def test_format_on_save_sorts_imports_and_formats(nvim: Nvim, project: Path) -> None:
    res = nvim.run(ATTACH + "vim.cmd.write()", cwd=project, env=server_path())
    res.assert_clean()
    assert (project / "main.py").read_text() == ("import os\nimport sys\n\nx = 1\nprint(os.sep, sys.argv)\n")


@needs_servers
def test_format_on_save_can_be_disabled(nvim: Nvim, project: Path) -> None:
    original = (project / "main.py").read_text()
    res = nvim.run(ATTACH + "vim.cmd('FormatToggle!')\nvim.cmd.write()", cwd=project, env=server_path())
    res.assert_clean()
    assert (project / "main.py").read_text() == original
