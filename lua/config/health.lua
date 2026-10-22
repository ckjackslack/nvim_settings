-- :checkhealth config — is this machine ready for the config?
local M = {}

function M.check()
  local health = vim.health
  local config = require("config")

  health.start("Neovim")
  if config.version_ok() then
    health.ok(("Neovim %s (>= %s required)"):format(tostring(vim.version()), config.min_version))
  else
    health.error(("Neovim %s is too old; %s+ is required"):format(tostring(vim.version()), config.min_version))
  end

  health.start("Plugins")
  if config.safe_mode() then
    health.info("Safe mode (NVIM_NO_PLUGINS) is on: plugins are not loaded")
  elseif package.loaded["lazy"] then
    local stats = require("lazy").stats()
    health.ok(("lazy.nvim loaded %d/%d plugins"):format(stats.loaded, stats.count))
  else
    health.warn("lazy.nvim is not loaded", { "Check that git works and run :Lazy restore" })
  end
  local lockfile = vim.fs.joinpath(vim.fn.stdpath("config"), "lazy-lock.json")
  if vim.uv.fs_stat(lockfile) then
    health.ok("lazy-lock.json found: plugin versions are pinned")
  else
    health.warn("lazy-lock.json missing: plugins will track their latest versions")
  end

  health.start("External tools")
  for _, tool in ipairs(require("config.tools").executables) do
    local path = vim.fn.exepath(tool.cmd)
    if path ~= "" then
      health.ok(("%s: %s"):format(tool.cmd, path))
    elseif tool.required then
      health.error(("%s not found (%s)"):format(tool.cmd, tool.purpose), { tool.advice })
    else
      health.warn(("%s not found (%s)"):format(tool.cmd, tool.purpose), { tool.advice })
    end
  end

  health.start("Python")
  local python = require("config.python")
  local venv = python.find_venv()
  if venv then
    health.ok("virtualenv: " .. venv)
  else
    health.info("no virtualenv found for " .. vim.fn.getcwd() .. " (using " .. python.python_path() .. ")")
  end
  health.info("debug adapter python: " .. python.debugpy_python())
  health.info(("format on save: %s"):format(require("config.format").enabled() and "on" or "off"))
end

return M
