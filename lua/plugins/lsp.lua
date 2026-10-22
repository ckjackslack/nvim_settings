-- Mason installs the language servers and debugpy; the servers themselves are
-- configured natively in lsp/*.lua and enabled from lua/config/lsp.lua.
---@type LazySpec
return {
  {
    "mason-org/mason.nvim", -- was williamboman/mason.nvim
    lazy = false, -- puts Mason's bin directory on $PATH before any server starts...
    priority = 100, -- ...and before tree-sitter-manager looks for the tree-sitter CLI
    opts = {},
    config = function(_, opts)
      require("mason").setup(opts)
      local tools = require("config.tools")
      vim.api.nvim_create_user_command("MasonInstallTools", tools.install_missing, {
        desc = "Install the language servers and debugpy this config uses",
      })
      -- Install on the first interactive start, never in headless/scripted runs.
      if #vim.api.nvim_list_uis() > 0 then
        vim.api.nvim_create_autocmd("VimEnter", { once = true, callback = tools.install_missing })
      end
    end,
  },

  {
    -- Neovim API + plugin types for lua_ls, only when editing Lua.
    "folke/lazydev.nvim",
    ft = "lua",
    opts = {
      library = {
        { path = "${3rd}/luv/library", words = { "vim%.uv" } },
      },
    },
  },
}
