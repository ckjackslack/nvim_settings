"""lua/config/format.lua: format-on-save toggles and the formatter allow-list."""

from __future__ import annotations

from conftest import Nvim


def test_enabled_by_default(nvim: Nvim) -> None:
    res = nvim.run("return { vim.g.format_on_save, require('config.format').enabled() }")
    res.assert_clean()
    assert res.result == [True, True]


def test_global_toggle(nvim: Nvim) -> None:
    res = nvim.run(
        """
        local f = require("config.format")
        local a = f.toggle(false)
        local b = f.enabled()
        local c = f.toggle(false)
        return { a, b, c, vim.g.format_on_save }
        """
    )
    res.assert_clean()
    assert res.result == [False, False, True, True]


def test_buffer_toggle_overrides_global(nvim: Nvim) -> None:
    res = nvim.run(
        """
        local f = require("config.format")
        local first = vim.api.nvim_get_current_buf()
        f.toggle(true)                 -- off for this buffer only
        local other = vim.api.nvim_create_buf(true, false)
        return { f.enabled(first), f.enabled(other), vim.g.format_on_save }
        """
    )
    res.assert_clean()
    assert res.result == [False, True, True]


def test_global_toggle_clears_buffer_override(nvim: Nvim) -> None:
    res = nvim.run(
        """
        local f = require("config.format")
        f.toggle(true)   -- buffer: off
        f.toggle(false)  -- global: from this buffer's view on -> ... recomputed
        return { vim.b.format_on_save == nil, vim.g.format_on_save }
        """
    )
    res.assert_clean()
    # buffer was off, so the global toggle turns things on everywhere and drops the override
    assert res.result == [True, True]


def test_format_toggle_command(nvim: Nvim) -> None:
    res = nvim.run(
        """
        vim.cmd("FormatToggle")
        local g = vim.g.format_on_save
        vim.cmd("FormatToggle!")
        return { g, vim.b.format_on_save }
        """
    )
    res.assert_clean()
    assert res.result == [False, True]
    assert "Format on save disabled for all buffers" in res.messages
    assert "Format on save enabled for this buffer" in res.messages


def test_allow_list(nvim: Nvim) -> None:
    res = nvim.run(
        """
        local f = require("config.format")
        return { f.formatters_for("python"), #f.formatters_for("lua"), f.organize_imports.python }
        """
    )
    res.assert_clean()
    assert res.result == [["ruff"], 0, True]


def test_format_without_client_is_noop(nvim: Nvim, tmp_path) -> None:
    script = tmp_path / "x.py"
    script.write_text("x  =  1\n")
    res = nvim.run(
        f"""
        vim.cmd.edit({str(script)!r})
        local ran = require("config.format").format()
        vim.cmd.write()
        return {{ ran = ran, lines = vim.api.nvim_buf_get_lines(0, 0, -1, false) }}
        """,
        env={"PATH": "/usr/bin:/bin"},
    )
    res.assert_clean()
    assert res.result == {"ran": False, "lines": ["x  =  1"]}
