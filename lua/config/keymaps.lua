-- Core keymaps that need no plugins. Plugin keymaps live next to their plugin
-- spec in lua/plugins/*.lua (lazy.nvim `keys`), LSP keymaps in config/lsp.lua.
--
-- Neovim 0.11+ already provides LSP defaults: K (hover), grn (rename),
-- gra (code action), grr (references), gri (implementation), gO (symbols),
-- [d / ]d (diagnostics), <C-w>d (diagnostic float).
local map = vim.keymap.set

map("n", "<Esc>", "<cmd>nohlsearch<CR>", { desc = "Clear search highlight" })

-- Window navigation
map("n", "<C-h>", "<C-w>h", { desc = "Go to left window" })
map("n", "<C-j>", "<C-w>j", { desc = "Go to lower window" })
map("n", "<C-k>", "<C-w>k", { desc = "Go to upper window" })
map("n", "<C-l>", "<C-w>l", { desc = "Go to right window" })

-- Keep the selection when indenting in visual mode
map("v", "<", "<gv", { desc = "Indent left" })
map("v", ">", ">gv", { desc = "Indent right" })

map("n", "<leader>q", vim.diagnostic.setloclist, { desc = "Diagnostics to location list" })
map("n", "<leader>tf", "<cmd>FormatToggle<CR>", { desc = "Toggle format on save" })
map("n", "<leader>pr", "<cmd>PyRun<CR>", { desc = "Run current Python file" })

-- Leave terminal mode with a double <Esc> (useful with :PyRun)
map("t", "<Esc><Esc>", "<C-\\><C-n>", { desc = "Exit terminal mode" })
