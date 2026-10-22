-- Colorscheme, icons and statusline.
---@type LazySpec
return {
  {
    "Mofiqul/dracula.nvim",
    lazy = false,
    priority = 1000, -- load before everything else so highlights are right from the start
    config = function()
      vim.cmd.colorscheme("dracula")
    end,
  },

  { "nvim-tree/nvim-web-devicons", lazy = true }, -- was kyazdani42/nvim-web-devicons

  {
    "nvim-lualine/lualine.nvim",
    event = "VeryLazy",
    dependencies = { "nvim-tree/nvim-web-devicons" },
    opts = function()
      local python = require("config.python")
      return {
        options = { theme = "auto", globalstatus = true },
        sections = {
          lualine_x = {
            {
              function()
                return python.statusline()
              end,
              cond = function()
                return vim.bo.filetype == "python"
              end,
            },
            "encoding",
            "fileformat",
            "filetype",
          },
        },
      }
    end,
  },
}
