-- ruff: linting, import sorting and formatting for Python (the 2026 replacement
-- for the flake8 + isort + black trio the original pylsp setup asked for).
-- A project's own pyproject.toml / ruff.toml takes precedence over these defaults.
---@type vim.lsp.Config
return {
  cmd = { "ruff", "server" },
  filetypes = { "python" },
  root_markers = { "pyproject.toml", "ruff.toml", ".ruff.toml", ".git" },
  init_options = {
    settings = {
      configurationPreference = "filesystemFirst",
      lint = {
        extendSelect = { "I" }, -- isort rules
      },
    },
  },
}
