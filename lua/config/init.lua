-- Top-level orchestration: load the plugin-free core, then (unless disabled)
-- bootstrap lazy.nvim and the plugin specs.
local M = {}

--- Oldest Neovim this config supports (native `vim.lsp.config` / `vim.lsp.enable`).
M.min_version = "0.11"

--- Truthy values accepted for boolean environment switches.
local TRUTHY = { ["1"] = true, ["true"] = true, ["yes"] = true, ["on"] = true }

--- Parse an environment-style boolean ("1", "true", "yes", "on"; case-insensitive).
---@param value string|nil
---@return boolean
function M.truthy(value)
  return value ~= nil and TRUTHY[value:lower()] == true
end

--- Safe mode: start with the core config only and no plugins at all.
--- Enabled with `NVIM_NO_PLUGINS=1 nvim` (handy for troubleshooting and for tests).
---@return boolean
function M.safe_mode()
  return M.truthy(vim.env.NVIM_NO_PLUGINS)
end

---@return boolean
function M.version_ok()
  return vim.fn.has("nvim-" .. M.min_version) == 1
end

function M.setup()
  require("config.options")

  if not M.version_ok() then
    vim.api.nvim_echo({
      {
        ("nvim_settings needs Neovim >= %s (found %s); only basic options were loaded."):format(
          M.min_version,
          tostring(vim.version())
        ),
        "ErrorMsg",
      },
    }, true, {})
    return
  end

  require("config.keymaps")
  require("config.autocmds")
  require("config.format").setup()
  require("config.python").setup()
  require("config.lsp").setup()

  if not M.safe_mode() then
    require("config.lazy").setup()
  end
end

return M
