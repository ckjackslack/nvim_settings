"""lua/config/python.lua: virtualenv detection, :PyRun command line, statusline label."""

from __future__ import annotations

import json
from pathlib import Path

from conftest import Nvim


def make_venv(path: Path) -> Path:
    python = path / "bin" / "python"
    python.parent.mkdir(parents=True)
    python.write_text("#!/bin/sh\n")
    python.chmod(0o755)
    return path


def call(nvim: Nvim, expr: str):
    res = nvim.run(f"local py = require('config.python')\nreturn {expr}")
    res.assert_clean()
    return res.result


def lua(value: object) -> str:
    """Python value -> Lua literal (strings and flat dicts are all we need)."""
    if isinstance(value, dict):
        return "{" + ", ".join(f"[{json.dumps(k)}] = {lua(v)}" for k, v in value.items()) + "}"
    return json.dumps(value)


def test_finds_dot_venv_in_project_root(nvim: Nvim, tmp_path: Path) -> None:
    project = tmp_path / "proj"
    venv = make_venv(project / ".venv")
    nested = project / "src" / "pkg"
    nested.mkdir(parents=True)
    (nested / "mod.py").write_text("")
    assert call(nvim, f"py.find_venv({lua(str(nested / 'mod.py'))}, {{}})") == str(venv)
    assert call(nvim, f"py.python_path({lua(str(nested))}, {{}})") == str(venv / "bin" / "python")


def test_prefers_nearest_venv_and_known_names(nvim: Nvim, tmp_path: Path) -> None:
    outer = make_venv(tmp_path / "proj" / "venv")
    inner = make_venv(tmp_path / "proj" / "sub" / "env")
    assert call(nvim, f"py.find_venv({lua(str(tmp_path / 'proj' / 'sub'))}, {{}})") == str(inner)
    assert call(nvim, f"py.find_venv({lua(str(tmp_path / 'proj'))}, {{}})") == str(outer)


def test_ignores_dirs_without_interpreter(nvim: Nvim, tmp_path: Path) -> None:
    (tmp_path / "proj" / ".venv").mkdir(parents=True)  # no bin/python inside
    assert call(nvim, f"py.find_venv({lua(str(tmp_path / 'proj'))}, {{}})") is None


def test_virtual_env_wins_and_conda_is_last(nvim: Nvim, tmp_path: Path) -> None:
    project = tmp_path / "proj"
    local = make_venv(project / ".venv")
    active = str(tmp_path / "active")
    conda = str(tmp_path / "conda")
    p = lua(str(project))
    assert call(nvim, f"py.find_venv({p}, {lua({'VIRTUAL_ENV': active})})") == active
    assert call(nvim, f"py.find_venv({p}, {lua({'CONDA_PREFIX': conda})})") == str(local)
    empty = tmp_path / "empty"
    empty.mkdir()
    assert call(nvim, f"py.find_venv({lua(str(empty))}, {lua({'CONDA_PREFIX': conda})})") == conda
    assert call(nvim, f"py.find_venv({lua(str(empty))}, {lua({'VIRTUAL_ENV': ''})})") is None


def test_falls_back_to_system_python(nvim: Nvim, tmp_path: Path) -> None:
    result = call(nvim, f"py.python_path({lua(str(tmp_path))}, {{}})")
    assert result.endswith("python3")


def test_run_cmd_uses_project_interpreter(nvim: Nvim, tmp_path: Path) -> None:
    venv = make_venv(tmp_path / "proj" / ".venv")
    script = tmp_path / "proj" / "main.py"
    script.write_text("print('hi')\n")
    assert call(nvim, f"py.run_cmd({lua(str(script))}, {{}})") == [str(venv / "bin" / "python"), str(script)]


def test_venv_label(nvim: Nvim) -> None:
    assert call(nvim, "py.venv_label('/work/myproject/.venv')") == "venv:myproject"
    assert call(nvim, "py.venv_label('/home/me/.virtualenvs/tools')") == "venv:tools"
    assert call(nvim, "py.venv_label(nil)") == ""


def test_statusline_only_for_python_buffers(nvim: Nvim, tmp_path: Path) -> None:
    make_venv(tmp_path / "proj" / ".venv")
    py_file = tmp_path / "proj" / "app.py"
    py_file.write_text("x = 1\n")
    txt_file = tmp_path / "proj" / "notes.txt"
    txt_file.write_text("notes\n")
    res = nvim.run(
        f"""
        local py = require("config.python")
        vim.cmd.edit({lua(str(py_file))})
        local on_python = py.statusline()
        vim.cmd.edit({lua(str(txt_file))})
        return {{ on_python, py.statusline() }}
        """
    )
    res.assert_clean()
    assert res.result == ["venv:proj", ""]


def test_pyrun_runs_file_in_terminal(nvim: Nvim, tmp_path: Path) -> None:
    out = tmp_path / "ran.txt"
    script = tmp_path / "proj" / "main.py"
    script.parent.mkdir()
    script.write_text(f"open({str(out)!r}, 'w').write('ok')\n")
    res = nvim.run(
        f"""
        vim.cmd.edit({lua(str(script))})
        vim.cmd("PyRun")
        vim.wait(10000, function() return vim.uv.fs_stat({lua(str(out))}) ~= nil end, 50)
        return {{ buftype = vim.bo.buftype, wins = #vim.api.nvim_list_wins() }}
        """
    )
    res.assert_clean()
    assert res.result == {"buftype": "terminal", "wins": 2}
    assert out.read_text() == "ok"


def test_pyrun_refuses_non_python(nvim: Nvim, tmp_path: Path) -> None:
    txt = tmp_path / "a.txt"
    txt.write_text("x\n")
    res = nvim.run(f"vim.cmd.edit({lua(str(txt))}); vim.cmd('PyRun'); return #vim.api.nvim_list_wins()")
    assert res.ok, res.error
    assert res.result == 1
    assert ":PyRun needs a saved Python file" in res.messages
