# nvim_settings

A personal Neovim configuration focused on Python development, rebuilt for the 2026 ecosystem:
[lazy.nvim](https://github.com/folke/lazy.nvim) with a committed lockfile, the native
`vim.lsp` configuration API, and basedpyright + ruff for Python. It ships with a **headless
pytest harness** that loads the config in a real, isolated Neovim and checks that it actually
works.

## Layout

```
init.lua                 entry point: sets <leader> then require("config").setup()
lua/config/              editor setup that needs no plugins
  options · keymaps · autocmds · lsp · python · format · tools · health · lazy
lua/plugins/             lazy.nvim specs, one file per concern
  editor · ui · completion · lsp · treesitter · debug
lsp/                     per-server settings (basedpyright, ruff, lua_ls) for vim.lsp.config
lazy-lock.json           pinned plugin revisions
scripts/fetch-nvim.sh    download a pinned Neovim for the test harness
tests/                   headless pytest suite
```

Core editor behaviour lives in `lua/config` and loads even with every plugin disabled; plugins
are additive specs in `lua/plugins`.

## Requirements

- **Neovim ≥ 0.11** (0.12.x recommended — the native `vim.lsp.config`/`vim.lsp.enable` API and
  `vim.pack`-era defaults are assumed). `scripts/fetch-nvim.sh` pins `v0.12.6`.
- `git` (lazy.nvim clones plugins on first start).
- For the Python tooling: `basedpyright` and `ruff` on `PATH` (or installed via `mason`), and a
  debugpy-capable Python for `nvim-dap-python`.

## Install

This is a Neovim config, so "install" means putting it where Neovim looks for it:

```bash
git clone https://github.com/ckjackslack/nvim_settings ~/.config/nvim
nvim            # first launch: lazy.nvim bootstraps itself and installs the pinned plugins
```

To try it without touching your own config:

```bash
git clone https://github.com/ckjackslack/nvim_settings /tmp/nvim_settings
NVIM_APPNAME=nvim_settings XDG_CONFIG_HOME=/tmp nvim   # reads /tmp/nvim_settings
```

Plugin versions come from `lazy-lock.json`; run `:Lazy sync` to install exactly those, or
`:Lazy update` to move the lockfile forward.

## What's inside

- **Editor** (`options`/`keymaps`/`autocmds`): sensible defaults (numbers, relative-free,
  `expandtab`, `smartindent`, `termguicolors`, `undofile`, `ignorecase`+`smartcase`,
  `inccommand=split`, split-right/below, a visible `colorcolumn`/`listchars`), `,` as leader,
  window-navigation and visual-mode indent mappings, `<leader>q` for diagnostics,
  `<Esc>` to clear search highlight.
- **LSP** via the native API: servers are declared as files under `lsp/` and enabled with
  `vim.lsp.enable`; attach-time keymaps are set in `lua/config/lsp.lua`.
- **Python** (`lua/config/python.lua`): basedpyright + ruff, `<leader>pr` to run the current
  file, `<leader>tf` to toggle format-on-save.
- **Plugins**: lualine + nvim-tree + telescope + web-devicons (UI/navigation), blink.cmp +
  friendly-snippets (completion), nvim-dap + dap-ui + nvim-dap-python (debugging), and a
  treesitter manager current for 2026.
- **`:checkhealth`** support through `lua/config/health.lua`.

## Tests

The suite loads this config in a throwaway `XDG_CONFIG_HOME`/`XDG_DATA_HOME` under `tmp_path`, so
it never reads or writes your real Neovim state.

```bash
pip install -e '.[dev]'          # or: uv sync
scripts/fetch-nvim.sh            # downloads Neovim to .cache/nvim/bin (or set NVIM_BIN / use PATH)
pytest
```

```
98 passed, 5 skipped
```

Offline tests (the default) check that the config starts without errors, that options and keymaps
are applied, that the lazy spec is valid, that the Python helpers and formatter logic behave, and
that `:checkhealth` runs. The 5 skipped tests actually install plugins over the network; enable
them with `pytest --run-network` or `NVIM_SETTINGS_NETWORK_TESTS=1`. If no Neovim binary is found,
the suite skips rather than fails.

## Modernised from the original

| Original (early 2024) | Now |
| --- | --- |
| packer.nvim (archived 2023), not bootstrapped | lazy.nvim with a committed `lazy-lock.json` and safe bootstrap |
| flat `lua/` with modules commented out of `init.lua` | `lua/config` + `lua/plugins`, everything wired up |
| `lspconfig.pylsp.setup{}` old pattern, leaking globals | native `vim.lsp.config`/`vim.lsp.enable`, settings under `lsp/` |
| pylsp with unrecognised keys; no `ensure_installed` | basedpyright + ruff, installed via mason |
| nvim-cmp + vsnip | blink.cmp + friendly-snippets |
| `kyazdani42/nvim-web-devicons` (renamed) | `nvim-tree/nvim-web-devicons` |
| `nvim-treesitter.configs` (archived 2026) | a current treesitter manager |
| nvim-dap with no Python adapter | nvim-dap + nvim-dap-python |
| leader set after plugins; no editor options; no tests | leader first, full options, headless pytest suite |

## Goodies added

- A headless **pytest harness** that proves the config loads and behaves, isolated from your real
  setup — rare for a dotfiles repo.
- `scripts/fetch-nvim.sh` to grab a pinned Neovim for CI or a clean test.
- `<leader>pr` run-current-Python-file and `<leader>tf` toggle-format-on-save.
- A `:checkhealth nvim_settings` report.
- A committed lockfile for reproducible plugin installs.

## Known limitations

- Targets Neovim ≥ 0.11; it will not load on older versions (the native LSP API is required).
- First launch needs network access for lazy.nvim to clone plugins.
- Tuned for Python; other languages get treesitter + generic LSP keymaps but no dedicated setup.
- The GUI experience isn't automatically tested — the harness drives a headless Neovim.
