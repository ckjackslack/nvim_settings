-- Python project helpers: virtualenv detection (shared by basedpyright, the
-- debugger and :PyRun) and a statusline component.
--
-- Lookup order for the interpreter of a project:
--   1. $VIRTUAL_ENV (an explicitly activated venv)
--   2. .venv / venv / env next to the file or in any parent directory
--   3. $CONDA_PREFIX
--   4. python3 from $PATH
local M = {}

local is_windows = vim.fn.has("win32") == 1

--- Directory names that are treated as a project virtualenv.
M.venv_names = { ".venv", "venv", "env" }

---@param path string
---@return boolean
local function is_file(path)
  local stat = vim.uv.fs_stat(path)
  return stat ~= nil and stat.type ~= "directory"
end

--- Path of the interpreter inside a virtualenv (or conda env) directory.
---@param venv string
---@return string
function M.venv_python(venv)
  if is_windows then
    return vim.fs.joinpath(venv, "Scripts", "python.exe")
  end
  return vim.fs.joinpath(venv, "bin", "python")
end

---@param env table|nil
---@param key string
---@return string|nil
local function getenv(env, key)
  local value = (env or vim.env)[key]
  if value == nil or value == "" then
    return nil
  end
  return value
end

--- Find the virtualenv that applies to `start` (a file or directory).
---@param start? string defaults to the current working directory
---@param env? table environment to read VIRTUAL_ENV / CONDA_PREFIX from (default: vim.env)
---@return string|nil venv directory
function M.find_venv(start, env)
  local active = getenv(env, "VIRTUAL_ENV")
  if active then
    return vim.fs.normalize(active)
  end

  local dir = vim.fs.normalize(start or vim.fn.getcwd())
  if is_file(dir) then
    dir = vim.fs.dirname(dir)
  end
  local candidates = { dir }
  for parent in vim.fs.parents(dir) do
    candidates[#candidates + 1] = parent
  end
  for _, candidate in ipairs(candidates) do
    for _, name in ipairs(M.venv_names) do
      local venv = vim.fs.joinpath(candidate, name)
      if is_file(M.venv_python(venv)) then
        return venv
      end
    end
  end

  local conda = getenv(env, "CONDA_PREFIX")
  if conda then
    return vim.fs.normalize(conda)
  end
  return nil
end

--- The Python interpreter to use for `start`.
---@param start? string
---@param env? table
---@return string
function M.python_path(start, env)
  local venv = M.find_venv(start, env)
  if venv then
    return M.venv_python(venv)
  end
  local system = vim.fn.exepath("python3")
  return system ~= "" and system or "python3"
end

--- Interpreter that has debugpy available for the debug adapter.
--- Prefers Mason's debugpy package, then a `debugpy-adapter` on $PATH, then the project python.
---@return string
function M.debugpy_python()
  local mason = M.venv_python(vim.fs.joinpath(vim.fn.stdpath("data"), "mason", "packages", "debugpy", "venv"))
  if is_file(mason) then
    return mason
  end
  if vim.fn.executable("debugpy-adapter") == 1 then
    return "debugpy-adapter"
  end
  return M.python_path()
end

--- Short label for the statusline: the project that owns the venv, e.g. "venv:myproject".
---@param venv string|nil
---@return string
function M.venv_label(venv)
  if not venv then
    return ""
  end
  local name = vim.fs.basename(venv)
  if vim.list_contains(M.venv_names, name) then
    name = vim.fs.basename(vim.fs.dirname(venv))
  end
  return "venv:" .. name
end

local label_cache = {} ---@type table<string, string>

--- Statusline component (used by lualine): venv label for Python buffers, "" otherwise.
---@param buf? integer
---@return string
function M.statusline(buf)
  buf = buf or vim.api.nvim_get_current_buf()
  if vim.bo[buf].filetype ~= "python" then
    return ""
  end
  local name = vim.api.nvim_buf_get_name(buf)
  local dir = name ~= "" and vim.fs.dirname(name) or vim.fn.getcwd()
  local key = dir .. "\0" .. (vim.env.VIRTUAL_ENV or "")
  if label_cache[key] == nil then
    label_cache[key] = M.venv_label(M.find_venv(dir))
  end
  return label_cache[key]
end

function M.clear_cache()
  label_cache = {}
end

--- Command line used by :PyRun for `file`.
---@param file string
---@param env? table
---@return string[]
function M.run_cmd(file, env)
  return { M.python_path(file, env), file }
end

function M.setup()
  vim.api.nvim_create_user_command("PyRun", function()
    local file = vim.api.nvim_buf_get_name(0)
    if file == "" or vim.bo.filetype ~= "python" then
      vim.notify(":PyRun needs a saved Python file", vim.log.levels.WARN)
      return
    end
    vim.cmd("silent update")
    local cmd = M.run_cmd(file)
    vim.cmd("botright 12split")
    vim.cmd("enew")
    vim.fn.jobstart(cmd, { term = true, cwd = vim.fs.dirname(file) })
    vim.cmd("startinsert")
  end, { desc = "Run the current Python file with the project's interpreter" })

  vim.api.nvim_create_user_command("PyVenv", function()
    local name = vim.api.nvim_buf_get_name(0)
    local start = name ~= "" and name or nil
    vim.notify(("venv: %s\npython: %s"):format(M.find_venv(start) or "(none)", M.python_path(start)))
  end, { desc = "Show the detected virtualenv and interpreter" })

  vim.api.nvim_create_autocmd("DirChanged", {
    group = vim.api.nvim_create_augroup("nvim_settings_python", { clear = true }),
    callback = M.clear_cache,
  })
end

return M
