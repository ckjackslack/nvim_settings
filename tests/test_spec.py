"""The lazy.nvim spec, checked offline through a stub lazy.nvim (tests/lua/lazy_stub)."""

from __future__ import annotations

import json
from typing import Any

import pytest

from conftest import REPO, Nvim

COLLECT = """
local lazy = require("lazy")
local plugins = {}
for name, spec in pairs(lazy.plugins) do
  plugins[name] = {
    source = spec[1],
    lazy = spec.lazy,
    version = spec.version,
    has_keys = spec.keys ~= nil,
    event = spec.event,
    cmd = spec.cmd,
    ft = spec.ft,
  }
end
return {
  errors = lazy.errors,
  plugins = plugins,
  order = lazy.order,
  opts = { rocks = lazy.options.rocks.enabled, checker = lazy.options.checker.enabled },
  netrw = vim.g.loaded_netrw,
}
"""


@pytest.fixture
def spec(nvim: Nvim) -> dict[str, Any]:
    nvim.install_lazy_stub()
    res = nvim.run(COLLECT, safe=False)
    res.assert_clean()
    return res.result


def test_full_init_runs_with_stubbed_lazy(spec: dict[str, Any]) -> None:
    assert spec["errors"] == []


def test_expected_plugins(spec: dict[str, Any]) -> None:
    sources = {p["source"] for p in spec["plugins"].values()}
    assert sources == {
        "folke/lazy.nvim",
        "Mofiqul/dracula.nvim",
        "nvim-tree/nvim-web-devicons",
        "nvim-lualine/lualine.nvim",
        "nvim-tree/nvim-tree.lua",
        "nvim-telescope/telescope.nvim",
        "nvim-lua/plenary.nvim",
        "saghen/blink.cmp",
        "rafamadriz/friendly-snippets",
        "mason-org/mason.nvim",
        "folke/lazydev.nvim",
        "romus204/tree-sitter-manager.nvim",
        "mfussenegger/nvim-dap",
        "rcarriga/nvim-dap-ui",
        "nvim-neotest/nvim-nio",
        "theHamsta/nvim-dap-virtual-text",
        "mfussenegger/nvim-dap-python",
        "nvim-telescope/telescope-dap.nvim",
        "jbyuki/one-small-step-for-vimkind",
    }


@pytest.mark.parametrize(
    "stale",
    [
        "wbthomason/packer.nvim",  # archived 2023
        "williamboman/mason.nvim",  # moved to mason-org
        "williamboman/mason-lspconfig.nvim",
        "kyazdani42/nvim-web-devicons",  # moved to nvim-tree
        "nvim-treesitter/nvim-treesitter",  # archived 2026
        "neovim/nvim-lspconfig",  # replaced by native vim.lsp.config + lsp/*.lua
        "hrsh7th/nvim-cmp",  # replaced by blink.cmp
        "hrsh7th/vim-vsnip",
    ],
)
def test_no_stale_plugins(spec: dict[str, Any], stale: str) -> None:
    assert stale not in {p["source"] for p in spec["plugins"].values()}


def test_lockfile_matches_spec(spec: dict[str, Any]) -> None:
    lock = json.loads((REPO / "lazy-lock.json").read_text())
    assert set(lock) == set(spec["plugins"])
    for name, entry in lock.items():
        assert len(entry["commit"]) == 40, name
        assert entry["branch"], name


def test_lazy_options(spec: dict[str, Any]) -> None:
    assert spec["opts"] == {"rocks": False, "checker": False}


def test_init_hooks_ran(spec: dict[str, Any]) -> None:
    # nvim-tree's init disables netrw before it can load
    assert spec["netrw"] == 1


def test_eager_plugins_are_intentional(spec: dict[str, Any]) -> None:
    """Everything is lazy-loaded except a known list of plugins that must start eagerly."""
    eager = {name for name, p in spec["plugins"].items() if p.get("lazy") is False}
    assert eager == {
        "dracula.nvim",
        "nvim-tree.lua",
        "blink.cmp",
        "mason.nvim",
        "tree-sitter-manager.nvim",
    }


def test_pinned_versions(spec: dict[str, Any]) -> None:
    plugins = spec["plugins"]
    assert plugins["blink.cmp"]["version"] == "1.*"  # prebuilt fuzzy binaries come with release tags
    assert plugins["telescope.nvim"]["version"] == "*"


@pytest.mark.parametrize(
    ("mode", "lhs", "desc"),
    [
        ("n", ",ff", "Find files (incl. hidden and git-ignored)"),
        ("n", ",fg", "Live grep (ripgrep, respects .gitignore)"),
        ("n", ",fb", "Find buffers"),
        ("n", ",fh", "Find help tags"),
        ("n", ",fd", "Find diagnostics"),
        ("n", ",n", "File explorer: toggle"),
        ("n", ",N", "File explorer: reveal current file"),
        ("n", "<F5>", "Debug: start / continue"),
        ("n", "<F10>", "Debug: step over"),
        ("n", "<F11>", "Debug: step into"),
        ("n", "<F12>", "Debug: step out"),
        ("n", ",b", "Debug: toggle breakpoint"),
        ("n", ",B", "Debug: conditional breakpoint"),
        ("n", ",du", "Debug: toggle UI"),
        ("n", ",dt", "Debug: Python test method"),
        ("x", ",ds", "Debug: Python selection"),
        ("n", ",dl", "Debug: start Lua debug server in this Neovim"),
    ],
)
def test_plugin_keymaps(nvim: Nvim, mode: str, lhs: str, desc: str) -> None:
    nvim.install_lazy_stub()
    res = nvim.run(f'return vim.fn.maparg({lhs!r}, {mode!r}, false, true).desc or ""', safe=False)
    res.assert_clean()
    assert res.result == desc


def test_no_keymap_collisions(nvim: Nvim) -> None:
    """Plugin keys must not silently overwrite each other or the core keymaps."""
    nvim.install_lazy_stub()
    res = nvim.run(
        """
        local seen, dupes = {}, {}
        for _, k in ipairs(require("lazy").keymaps) do
          local modes = type(k.mode) == "table" and k.mode or { k.mode }
          for _, m in ipairs(modes) do
            local id = m .. " " .. k.lhs
            if seen[id] then dupes[#dupes + 1] = id end
            seen[id] = true
          end
        end
        return dupes
        """,
        safe=False,
    )
    res.assert_clean()
    assert res.result in ([], {})


def test_spec_validator_catches_mistakes(nvim: Nvim) -> None:
    """Sanity check of the stub itself: a bad spec is reported, not accepted."""
    nvim.install_lazy_stub()
    bad = nvim.config_dir / "lua" / "plugins" / "zz_bad.lua"
    bad.write_text(
        'return { { "not a repo" }, { "a/b", lazzy = true }, { "c/d", keys = { { "x", "y" } } } }\n'
    )
    res = nvim.run("return require('lazy').errors", safe=False)
    assert res.ok, res.error
    errors = "\n".join(res.result)
    assert "not an owner/repo" in errors
    assert "unknown key <lazzy>" in errors
    assert "has no desc" in errors
