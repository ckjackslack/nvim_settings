-- basedpyright: type checking, completion, hover, go-to-definition for Python.
-- Linting, import sorting and formatting are left to ruff (lsp/ruff.lua).
---@type vim.lsp.Config
return {
  cmd = { "basedpyright-langserver", "--stdio" },
  filetypes = { "python" },
  root_markers = {
    "pyproject.toml",
    "setup.py",
    "setup.cfg",
    "requirements.txt",
    "Pipfile",
    "pyrightconfig.json",
    ".git",
  },
  settings = {
    basedpyright = {
      disableOrganizeImports = true, -- ruff does this
      analysis = {
        typeCheckingMode = "standard",
        autoSearchPaths = true,
        useLibraryCodeForTypes = true,
        diagnosticMode = "openFilesOnly",
      },
    },
    python = {},
  },
  -- Point the server at the project's virtualenv (.venv, venv, $VIRTUAL_ENV, ...).
  before_init = function(_, config)
    local root = config.root_dir or vim.fn.getcwd()
    config.settings = config.settings or {}
    config.settings.python = config.settings.python or {}
    config.settings.python.pythonPath = require("config.python").python_path(root)
  end,
}
