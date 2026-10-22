-- File explorer and fuzzy finder.
---@type LazySpec
return {
  {
    "nvim-tree/nvim-tree.lua",
    version = "*",
    lazy = false, -- needed so `nvim <directory>` opens the tree instead of netrw
    dependencies = { "nvim-tree/nvim-web-devicons" },
    init = function()
      -- nvim-tree replaces netrw; this must happen before netrw loads.
      vim.g.loaded_netrw = 1
      vim.g.loaded_netrwPlugin = 1
    end,
    keys = {
      { "<leader>n", "<cmd>NvimTreeToggle<CR>", desc = "File explorer: toggle" },
      { "<leader>N", "<cmd>NvimTreeFindFile<CR>", desc = "File explorer: reveal current file" },
    },
    opts = {
      view = { width = 32 },
      renderer = { group_empty = true },
      update_focused_file = { enable = true },
      filters = { custom = { "^.git$", "__pycache__" } },
    },
  },

  {
    "nvim-telescope/telescope.nvim",
    version = "*",
    cmd = "Telescope",
    dependencies = { "nvim-lua/plenary.nvim" },
    keys = {
      {
        "<leader>ff",
        function()
          require("telescope.builtin").find_files({ hidden = true, no_ignore = true })
        end,
        desc = "Find files (incl. hidden and git-ignored)",
      },
      {
        "<leader>fg",
        function()
          require("telescope.builtin").live_grep()
        end,
        desc = "Live grep (ripgrep, respects .gitignore)",
      },
      {
        "<leader>fb",
        function()
          require("telescope.builtin").buffers()
        end,
        desc = "Find buffers",
      },
      {
        "<leader>fh",
        function()
          require("telescope.builtin").help_tags()
        end,
        desc = "Find help tags",
      },
      {
        "<leader>fd",
        function()
          require("telescope.builtin").diagnostics()
        end,
        desc = "Find diagnostics",
      },
    },
    opts = {
      defaults = {
        -- <leader>ff searches ignored files too, but never these.
        file_ignore_patterns = { "^%.git/", "/%.git/", "%.venv/", "__pycache__/", "node_modules/" },
      },
    },
  },
}
