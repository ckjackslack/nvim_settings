-- Tree-sitter parsers. nvim-treesitter was archived in 2026; Neovim 0.12 does the
-- highlighting itself (vim.treesitter.start) and tree-sitter-manager.nvim only
-- installs the parsers. Building parsers needs the `tree-sitter` CLI and a C compiler.
---@type LazySpec
return {
  {
    "romus204/tree-sitter-manager.nvim",
    lazy = false, -- registers the FileType autocmd that turns highlighting on
    main = "tree-sitter-manager",
    opts = function()
      -- Evaluated at load time, after Mason has put its tree-sitter CLI on $PATH.
      local can_build = vim.fn.executable("tree-sitter") == 1
      return {
        -- Same languages as the original config; Lua's parser ships with Neovim.
        ensure_installed = can_build and { "go", "python", "rust" } or {},
        auto_install = can_build,
        noauto_install = { "c", "lua", "markdown", "markdown_inline", "query", "vim", "vimdoc" },
        highlight = true,
      }
    end,
  },
}
