-- nvim_settings: entry point.
--
-- Everything lives in lua/config (core editor setup, no plugins needed) and
-- lua/plugins (lazy.nvim specs). See README.md for the layout.

-- The leader has to be set before any mapping or plugin spec is evaluated.
vim.g.mapleader = ","
vim.g.maplocalleader = "\\"

require("config").setup()
