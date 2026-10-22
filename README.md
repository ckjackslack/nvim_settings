# nvim_settings

> **Draft: initial assessment.** This README is unfinished on purpose. See the TODO section.

## What this seems to be

The author's personal Neovim configuration (early 2024): a Lua `init.lua` that `require`s
one module per concern from `lua/`:

| Module | Purpose |
| --- | --- |
| `plugins.lua` | packer.nvim plugin list (mason, lspconfig, nvim-cmp + vsnip, nvim-tree, telescope, nvim-dap + dap-ui, dracula, treesitter, lualine) |
| `mason-config.lua` | `mason` + `mason-lspconfig` setup |
| `pylsp.lua` | Python LSP (`pylsp`) via `lspconfig.pylsp.setup{}` |
| `code-completion.lua` | nvim-cmp with Tab/S-Tab/CR mappings and a few sources |
| `debugging.lua` | nvim-dap-ui opening and closing automatically with debug sessions |
| `file-finder.lua` / `telescope.lua` | Telescope find-files / live-grep keymaps |
| `file-explorer.lua` | nvim-tree |
| `syntax-highlight.lua` | nvim-treesitter for go, lua, rust, python |
| `statusbar.lua`, `styling.lua`, `custom-keys.lua` | lualine, the dracula colorscheme, `,` as leader |

The focus is clearly **Python development**: LSP, completion, debugging, fuzzy finding.

## Current state (honest assessment)

Partly works on a machine that already has packer installed. Problems:

- **packer.nvim was archived in 2023.** It is not bootstrapped either, so on a fresh machine
  `require("packer")` fails straight away.
- **Several modules are commented out of `init.lua`**: completion, debugging, file explorer and
  styling. `telescope.lua` is never required; it duplicates `file-finder.lua`.
- `file-explorer.lua` uses `open_on_setup` / `ignore_buffer_on_setup`, which nvim-tree removed in
  2023. Re-enabling it would raise an error.
- `pylsp.lua` uses the old `require("lspconfig").X.setup{}` pattern, which Neovim 0.11+ replaces
  with `vim.lsp.config()` / `vim.lsp.enable()`. It also leaks globals (`lspconfig`, `util`),
  passes `vim.fn.getcwd()` as a root *pattern*, and uses settings keys that pylsp doesn't
  recognise (`pylsp.analyses.*`, `staticchek`). The flake8, isort and black toggles do nothing.
- `mason-lspconfig.setup()` has no `ensure_installed`, so nothing installs `pylsp`.
- lualine depends on `kyazdani42/nvim-web-devicons` (renamed to `nvim-tree/nvim-web-devicons`).
- `require('nvim-treesitter.configs')` is the API of the old `master` branch. That branch is
  gone from the default, and nvim-treesitter itself was archived in 2026.
- The debugger has no Python adapter, so `nvim-dap` can't debug anything. `telescope-dap` and
  `one-small-step-for-vimkind` are installed but never configured.
- `<leader>` is set *after* plugins load. There are no editor options at all (numbers, indent and
  so on), and no tests.
- There are no secrets or personal paths in the repo.

## TODO / to be finished

- [ ] Redesign for the 2026 ecosystem: lazy.nvim + lockfile, `lua/config` + `lua/plugins`
      layout, native `vim.lsp.config`, basedpyright + ruff
- [ ] Fix or replace the broken plugin setups; enable completion, debugging and the explorer
- [ ] Headless pytest suite against a real Neovim binary
- [ ] Usage docs
