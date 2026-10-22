"""The core config (no plugins) loads cleanly and sets what it promises."""

from __future__ import annotations

import pytest

from conftest import Nvim


def test_safe_mode_starts_without_errors(nvim: Nvim) -> None:
    res = nvim.run(
        """
        return {
          safe = require("config").safe_mode(),
          lazy_loaded = package.loaded["lazy"] ~= nil,
          errmsg = vim.v.errmsg,
        }
        """
    )
    res.assert_clean()
    assert res.result == {"safe": True, "lazy_loaded": False, "errmsg": ""}


def test_leader_and_options(nvim: Nvim) -> None:
    res = nvim.run(
        """
        local o = vim.o
        return {
          leader = vim.g.mapleader,
          localleader = vim.g.maplocalleader,
          number = o.number, expandtab = o.expandtab, shiftwidth = o.shiftwidth,
          tabstop = o.tabstop, ignorecase = o.ignorecase, smartcase = o.smartcase,
          signcolumn = o.signcolumn, undofile = o.undofile, termguicolors = o.termguicolors,
          colorcolumn = o.colorcolumn, splitright = o.splitright, winborder = o.winborder,
          completeopt = o.completeopt, shortmess_c = o.shortmess:find("c", 1, true) ~= nil,
        }
        """
    )
    res.assert_clean()
    assert res.result == {
        "leader": ",",
        "localleader": "\\",
        "number": True,
        "expandtab": True,
        "shiftwidth": 4,
        "tabstop": 4,
        "ignorecase": True,
        "smartcase": True,
        "signcolumn": "yes",
        "undofile": True,
        "termguicolors": True,
        "colorcolumn": "88",
        "splitright": True,
        "winborder": "rounded",
        "completeopt": "menuone,noselect,noinsert",
        "shortmess_c": True,
    }


@pytest.mark.parametrize(
    ("mode", "lhs", "desc"),
    [
        ("n", "<Esc>", "Clear search highlight"),
        ("n", "<C-h>", "Go to left window"),
        ("n", "<C-l>", "Go to right window"),
        ("v", "<", "Indent left"),
        ("n", "<leader>q", "Diagnostics to location list"),
        ("n", "<leader>tf", "Toggle format on save"),
        ("n", "<leader>pr", "Run current Python file"),
        ("t", "<Esc><Esc>", "Exit terminal mode"),
    ],
)
def test_core_keymaps(nvim: Nvim, mode: str, lhs: str, desc: str) -> None:
    res = nvim.run(f'return vim.fn.maparg({lhs!r}, {mode!r}, false, true).desc or ""')
    res.assert_clean()
    assert res.result == desc


def test_leader_is_comma_in_mappings(nvim: Nvim) -> None:
    res = nvim.run('return vim.fn.maparg(",tf", "n")')
    res.assert_clean()
    assert res.result == "<Cmd>FormatToggle<CR>"


def test_user_commands_and_autocmds(nvim: Nvim) -> None:
    res = nvim.run(
        """
        local cmds = vim.api.nvim_get_commands({})
        local function has_au(group, event)
          return #vim.api.nvim_get_autocmds({ group = group, event = event }) > 0
        end
        return {
          commands = vim.tbl_map(function(n) return cmds[n] ~= nil end,
            { FormatToggle = "FormatToggle", Format = "Format", PyRun = "PyRun", PyVenv = "PyVenv" }),
          yank = has_au("nvim_settings", "TextYankPost"),
          restore = has_au("nvim_settings", "BufReadPost"),
          format = has_au("nvim_settings_format", "BufWritePre"),
          lsp_attach = has_au("nvim_settings_lsp", "LspAttach"),
        }
        """
    )
    res.assert_clean()
    assert res.result == {
        "commands": {"FormatToggle": True, "Format": True, "PyRun": True, "PyVenv": True},
        "yank": True,
        "restore": True,
        "format": True,
        "lsp_attach": True,
    }


def test_native_lsp_configs_are_enabled(nvim: Nvim) -> None:
    res = nvim.run(
        """
        local out = {}
        for _, name in ipairs(require("config.lsp").servers) do
          local cfg = vim.lsp.config[name]
          out[name] = {
            enabled = vim.lsp.is_enabled(name),
            cmd = cfg.cmd,
            filetypes = cfg.filetypes,
            has_root_markers = cfg.root_markers ~= nil,
          }
        end
        out.ruff_isort = vim.lsp.config.ruff.init_options.settings.lint.extendSelect
        out.pyright_mode = vim.lsp.config.basedpyright.settings.basedpyright.analysis.typeCheckingMode
        out.pyright_before_init = type(vim.lsp.config.basedpyright.before_init)
        out.lspconfig = package.loaded["lspconfig"] ~= nil
        return out
        """
    )
    res.assert_clean()
    r = res.result
    assert r["basedpyright"] == {
        "enabled": True,
        "cmd": ["basedpyright-langserver", "--stdio"],
        "filetypes": ["python"],
        "has_root_markers": True,
    }
    assert r["ruff"]["cmd"] == ["ruff", "server"]
    assert r["ruff"]["enabled"]
    assert r["lua_ls"]["filetypes"] == ["lua"]
    assert r["lua_ls"]["enabled"]
    assert r["ruff_isort"] == ["I"]
    assert r["pyright_mode"] == "standard"
    assert r["pyright_before_init"] == "function"
    assert r["lspconfig"] is False


def test_missing_language_server_is_harmless(nvim: Nvim, tmp_path) -> None:
    """Opening a Python file without basedpyright/ruff installed must not raise errors."""
    script = tmp_path / "x.py"
    script.write_text("print('hi')\n")
    res = nvim.run(
        f"""
        vim.cmd.edit({str(script)!r})
        vim.wait(200)
        return {{ ft = vim.bo.filetype, clients = #vim.lsp.get_clients({{ bufnr = 0 }}) }}
        """,
        env={"PATH": "/usr/bin:/bin"},
    )
    res.assert_clean()
    assert res.result == {"ft": "python", "clients": 0}


def test_diagnostics_config(nvim: Nvim) -> None:
    res = nvim.run(
        "local c = vim.diagnostic.config(); return { sort = c.severity_sort, vt = type(c.virtual_text) }"
    )
    res.assert_clean()
    assert res.result == {"sort": True, "vt": "table"}


def test_old_neovim_gets_a_clear_message(nvim: Nvim) -> None:
    """Pretend to be Neovim 0.10: only options load, plus an error message, no crash."""
    fake_old = (
        "lua local has = vim.fn.has; "
        "vim.fn.has = function(f) if f == 'nvim-0.11' then return 0 end return has(f) end"
    )
    res = nvim.run(
        """
        return {
          number = vim.o.number,
          lsp_loaded = package.loaded["config.lsp"] ~= nil,
          keymaps_loaded = package.loaded["config.keymaps"] ~= nil,
        }
        """,
        pre_args=["--cmd", fake_old],
    )
    assert res.ok, res.error
    assert res.result == {"number": True, "lsp_loaded": False, "keymaps_loaded": False}
    assert "needs Neovim >= 0.11" in res.messages + res.stderr


def test_truthy_env_parsing(nvim: Nvim) -> None:
    res = nvim.run(
        """
        local t = require("config").truthy
        return { t("1"), t("TRUE"), t("yes"), t("on"), t("0"), t(""), t(nil), t("no") }
        """
    )
    res.assert_clean()
    assert res.result == [True, True, True, True, False, False, False, False]


def test_plugins_are_skipped_only_in_safe_mode(nvim: Nvim) -> None:
    """Without NVIM_NO_PLUGINS the bootstrap runs; with an unreachable git it fails softly."""
    res = nvim.run(
        "return { lazy = package.loaded['lazy'] ~= nil }",
        safe=False,
        env={"PATH": "/nonexistent"},  # no git -> clone fails -> config keeps working
    )
    assert res.ok, res.error
    assert res.result == {"lazy": False}
    assert "Failed to clone lazy.nvim" in res.messages + res.stderr
