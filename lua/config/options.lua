-- Editor options. Plain Neovim, no plugins required.
local opt = vim.opt

-- UI
opt.number = true
opt.cursorline = true
opt.signcolumn = "yes" -- no jumping text when diagnostics appear
opt.termguicolors = true
opt.colorcolumn = "88" -- ruff/black default line length
opt.scrolloff = 8
opt.list = true
opt.listchars = { tab = "» ", trail = "·", nbsp = "␣" }
opt.splitright = true
opt.splitbelow = true
opt.mouse = "a"
opt.showmode = false -- lualine shows the mode
opt.winborder = "rounded" -- floating windows (hover, signature help, ...)

-- Editing
opt.expandtab = true
opt.shiftwidth = 4
opt.tabstop = 4
opt.softtabstop = 4
opt.smartindent = true
opt.ignorecase = true
opt.smartcase = true
opt.inccommand = "split"
opt.confirm = true
opt.undofile = true

-- Responsiveness
opt.updatetime = 250
opt.timeoutlen = 400

-- Completion menu behaviour (kept from the original config)
opt.completeopt = { "menuone", "noselect", "noinsert" }
opt.shortmess:append("c")
