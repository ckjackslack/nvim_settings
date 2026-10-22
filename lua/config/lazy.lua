-- Bootstrap lazy.nvim and load every spec in lua/plugins/.
-- Plugin versions are pinned in lazy-lock.json (commit it; `:Lazy restore` installs exactly those).
local M = {}

M.repo = "https://github.com/folke/lazy.nvim.git"

---@return string
function M.path()
  return vim.fs.joinpath(vim.fn.stdpath("data"), "lazy", "lazy.nvim")
end

--- Clone lazy.nvim if it is missing. Returns false (with a message) if that fails.
---@return boolean ok
function M.bootstrap()
  local path = M.path()
  if vim.uv.fs_stat(path) then
    return true
  end
  local out = vim.fn.system({ "git", "clone", "--filter=blob:none", "--branch=stable", M.repo, path })
  if vim.v.shell_error ~= 0 then
    vim.api.nvim_echo({
      { "Failed to clone lazy.nvim; starting without plugins.\n", "ErrorMsg" },
      { out, "WarningMsg" },
    }, true, {})
    return false
  end
  return true
end

M.opts = {
  spec = { { import = "plugins" } },
  install = { colorscheme = { "dracula", "habamax" } },
  checker = { enabled = false }, -- update deliberately with :Lazy update, then commit the lockfile
  change_detection = { notify = false },
  rocks = { enabled = false }, -- no plugin here needs luarocks
  performance = {
    rtp = {
      disabled_plugins = { "gzip", "tarPlugin", "tohtml", "tutor", "zipPlugin" },
    },
  },
}

function M.setup()
  if not M.bootstrap() then
    return
  end
  vim.opt.rtp:prepend(M.path())
  require("lazy").setup(M.opts)
end

return M
