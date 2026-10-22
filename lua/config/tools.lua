-- External tools this config uses: what Mason installs and what :checkhealth looks for.
local M = {}

--- Mason packages installed by :MasonInstallTools (and automatically on the first interactive start).
M.mason_packages = { "basedpyright", "ruff", "lua-language-server", "debugpy", "tree-sitter-cli" }

---@class ToolCheck
---@field cmd string executable name
---@field purpose string
---@field required? boolean missing required tools are errors, others warnings
---@field advice string how to get it

---@type ToolCheck[]
M.executables = {
  { cmd = "git", purpose = "lazy.nvim plugin installs", required = true, advice = "Install git" },
  { cmd = "rg", purpose = "Telescope live grep (<leader>fg)", advice = "Install ripgrep" },
  { cmd = "tree-sitter", purpose = "building tree-sitter parsers", advice = "Run :MasonInstallTools" },
  { cmd = "cc", purpose = "compiling tree-sitter parsers", advice = "Install gcc or clang" },
  { cmd = "python3", purpose = "Python LSP and debugging", advice = "Install Python 3" },
  {
    cmd = "basedpyright-langserver",
    purpose = "Python language server (basedpyright)",
    advice = "Run :MasonInstallTools (or pip install basedpyright)",
  },
  { cmd = "ruff", purpose = "Python lint/format server (ruff)", advice = "Run :MasonInstallTools (or pip install ruff)" },
  { cmd = "lua-language-server", purpose = "Lua language server", advice = "Run :MasonInstallTools" },
}

--- Mason packages that are not installed yet. `is_installed` is injectable for tests.
---@param is_installed fun(name: string): boolean
---@return string[]
function M.missing_packages(is_installed)
  return vim.tbl_filter(function(name)
    return not is_installed(name)
  end, M.mason_packages)
end

--- Install missing Mason packages (needs mason.nvim to be loaded).
function M.install_missing()
  local registry = require("mason-registry")
  registry.refresh(function()
    local missing = M.missing_packages(registry.is_installed)
    for _, name in ipairs(missing) do
      if registry.has_package(name) then
        vim.notify("Mason: installing " .. name)
        registry.get_package(name):install()
      end
    end
  end)
end

return M
