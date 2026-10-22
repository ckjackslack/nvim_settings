-- Completion: blink.cmp replaces nvim-cmp + its six source plugins + vim-vsnip.
-- Keys follow the original nvim-cmp setup: <Tab>/<S-Tab> move through the menu,
-- <CR> accepts, <C-Space> opens it, <C-e> closes it, <C-f>/<C-b> scroll docs.
-- It also registers its LSP capabilities via vim.lsp.config("*"), so it is not lazy-loaded.
---@type LazySpec
return {
  {
    "saghen/blink.cmp",
    version = "1.*", -- release tags ship prebuilt fuzzy-matcher binaries
    lazy = false,
    dependencies = { "rafamadriz/friendly-snippets" },
    opts = {
      keymap = {
        preset = "enter",
        ["<Tab>"] = { "select_next", "snippet_forward", "fallback" },
        ["<S-Tab>"] = { "select_prev", "snippet_backward", "fallback" },
      },
      completion = {
        list = { selection = { preselect = false, auto_insert = true } },
        menu = { border = "rounded" },
        documentation = { auto_show = true, auto_show_delay_ms = 300, window = { border = "rounded" } },
      },
      signature = { enabled = true, window = { border = "rounded" } },
      sources = {
        default = { "lsp", "path", "snippets", "buffer" },
      },
      fuzzy = { implementation = "prefer_rust_with_warning" },
    },
  },
}
