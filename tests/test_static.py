"""Static checks: every Lua file compiles, no deprecated APIs, sane layout."""

from __future__ import annotations

import json
import re

import pytest

from conftest import REPO, Nvim

LUA_FILES = sorted(
    p for p in REPO.rglob("*.lua") if not ({".venv", ".git", ".cache"} & set(p.relative_to(REPO).parts))
)

# pattern -> what to use instead
DEPRECATED = {
    r"require\s*\(?\s*[\"']lspconfig": "vim.lsp.config / vim.lsp.enable (lsp/*.lua)",
    r"\bpacker\b": "lazy.nvim",
    r"nvim-treesitter\.configs": "vim.treesitter.start + a parser manager",
    r"\bvim\.loop\b": "vim.uv",
    r"get_active_clients|buf_get_clients": "vim.lsp.get_clients",
    r"\btermopen\b": "vim.fn.jobstart(cmd, { term = true })",
    r"\bvim\.highlight\.": "vim.hl",
    r"nvim_buf_set_option|nvim_win_set_option": "vim.bo / vim.wo",
    r"vim\.tbl_flatten|vim\.tbl_islist": "vim.iter(...):flatten() / vim.islist",
    r"diagnostic\.goto_(next|prev)": "vim.diagnostic.jump",
    r"williamboman/|kyazdani42/": "the renamed repositories (mason-org/, nvim-tree/)",
    r"\bnvim_set_keymap\b": "vim.keymap.set",
}


def strip_comments(source: str) -> str:
    return re.sub(r"--.*", "", source)


def test_lua_files_found() -> None:
    names = {p.relative_to(REPO).as_posix() for p in LUA_FILES}
    assert {"init.lua", "lua/config/init.lua", "lsp/basedpyright.lua", "lua/plugins/lsp.lua"} <= names


@pytest.mark.parametrize(("pattern", "instead"), DEPRECATED.items(), ids=list(DEPRECATED))
def test_no_deprecated_api(pattern: str, instead: str) -> None:
    offenders = [
        p.relative_to(REPO).as_posix() for p in LUA_FILES if re.search(pattern, strip_comments(p.read_text()))
    ]
    assert offenders == [], f"use {instead}"


def test_all_lua_files_compile(nvim: Nvim) -> None:
    files = [str(p) for p in LUA_FILES]
    res = nvim.run(
        f"""
        local errors = {{}}
        for _, file in ipairs(vim.json.decode({json.dumps(json.dumps(files))})) do
          local _, err = loadfile(file)
          if err then errors[#errors + 1] = err end
        end
        return errors
        """,
        args=["--clean"],
    )
    res.assert_clean()
    assert res.result in ([], {})


def test_no_globals_leak(nvim: Nvim) -> None:
    """The old pylsp.lua leaked `lspconfig` and `util` as globals; nothing should now."""
    res = nvim.run(
        """
        local before = vim.json.decode(os.getenv("GLOBALS_BEFORE"))
        local leaked = {}
        for k in pairs(_G) do
          if type(k) == "string" and not before[k] then leaked[#leaked + 1] = k end
        end
        table.sort(leaked)
        return leaked
        """,
        pre_args=[
            "--cmd",
            "lua local g = {} for k in pairs(_G) do g[k] = true end "
            "g.__ok = true g.__res = true g.__out = true g.__f = true g.__messages = true "
            "vim.env.GLOBALS_BEFORE = vim.json.encode(g)",
        ],
    )
    res.assert_clean()
    assert res.result in ([], {})


def test_lsp_dir_matches_enabled_servers(nvim: Nvim) -> None:
    res = nvim.run("return require('config.lsp').servers")
    res.assert_clean()
    on_disk = sorted(p.stem for p in (REPO / "lsp").glob("*.lua"))
    assert sorted(res.result) == on_disk


def test_lockfile_is_valid_json_and_sorted() -> None:
    raw = (REPO / "lazy-lock.json").read_text()
    lock = json.loads(raw)
    assert list(lock) == sorted(lock)
    assert all(set(v) == {"branch", "commit"} for v in lock.values())
