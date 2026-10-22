-- Bootstrap lazy.nvim and load every spec in lua/plugins/.
-- Plugin versions are pinned in lazy-lock.json (commit it; `:Lazy restore` installs exactly those).
local M = {}

M.repo = "https://github.com/folke/lazy.nvim.git"

---@return string
function M.path()
  return vim.fs.joinpath(vim.fn.stdpath("data"), "lazy", "lazy.nvim")
end

--- The lazy.nvim commit pinned in lazy-lock.json, if any.
---@return string|nil
function M.locked_commit()
  local lockfile = vim.fs.joinpath(vim.fn.stdpath("config"), "lazy-lock.json")
  local ok, lock = pcall(function()
    return vim.json.decode(table.concat(vim.fn.readfile(lockfile), "\n"))
  end)
  local entry = ok and type(lock) == "table" and lock["lazy.nvim"] or nil
  return type(entry) == "table" and entry.commit or nil
end

--- Clone lazy.nvim (at the locked commit) if it is missing. Returns false (with a message) if that fails.
---@return boolean ok
function M.bootstrap()
  local path = M.path()
  if vim.uv.fs_stat(path) then
    return true
  end
  local ok, out = false, "git is not installed"
  if vim.fn.executable("git") == 1 then
    out = vim.fn.system({ "git", "clone", "--filter=blob:none", "--branch=stable", M.repo, path })
    ok = vim.v.shell_error == 0
    local commit = ok and M.locked_commit()
    if commit then
      vim.fn.system({ "git", "-C", path, "checkout", "--quiet", commit })
    end
  end
  if not ok then
    vim.api.nvim_echo({
      { "Failed to clone lazy.nvim; starting without plugins.\n", "ErrorMsg" },
      { out, "WarningMsg" },
    }, true, {})
  end
  return ok
end

M.opts = {
  spec = {
    { "folke/lazy.nvim", version = "*" }, -- lazy itself follows releases, like the bootstrap's stable branch
    { import = "plugins" },
  },
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
