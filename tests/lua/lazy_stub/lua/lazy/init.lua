-- Offline stand-in for lazy.nvim used by the test-suite.
--
-- It resolves `{ import = "plugins" }` like lazy.nvim does, validates every
-- spec (unknown keys, types, source names, keymap entries), runs `init`
-- functions and registers `keys` mappings, but never loads or clones a plugin.
-- Results end up in the module table for the tests to inspect.
local M = {
  options = nil,
  plugins = {}, ---@type table<string, table>
  order = {}, ---@type string[]
  errors = {}, ---@type string[]
  keymaps = {}, ---@type table[]
}

-- Mirrors lazy.nvim's own list of valid plugin spec keys (lua/lazy/health.lua).
local VALID = {}
for _, key in ipairs({
  1, "_", "branch", "build", "cmd", "commit", "cond", "config", "deactivate", "dependencies",
  "dev", "dir", "enabled", "event", "ft", "import", "init", "keys", "lazy", "main", "module",
  "name", "optional", "opts", "pin", "priority", "submodules", "tag", "url", "version",
}) do
  VALID[key] = true
end

local TYPES = {
  build = { "string", "function", "table", "boolean" },
  cmd = { "string", "table" },
  cond = { "boolean", "function" },
  config = { "function", "boolean", "table" },
  dependencies = { "string", "table" },
  enabled = { "boolean", "function" },
  event = { "string", "table", "function" },
  ft = { "string", "table", "function" },
  init = { "function" },
  keys = { "string", "table", "function" },
  lazy = { "boolean" },
  main = { "string" },
  name = { "string" },
  opts = { "table", "function" },
  priority = { "number" },
  version = { "string", "boolean" },
}

local function err(msg)
  M.errors[#M.errors + 1] = msg
end

local function source_of(spec)
  return spec[1] or spec.url or spec.dir
end

local function name_of(spec)
  if spec.name then
    return spec.name
  end
  local source = source_of(spec)
  return source and source:gsub("%.git$", ""):match("[^/]+$") or nil
end

local add

local function import(modname)
  local files = vim.api.nvim_get_runtime_file("lua/" .. modname:gsub("%.", "/") .. "/*.lua", true)
  if #files == 0 then
    err("import '" .. modname .. "' matched no files")
  end
  table.sort(files)
  for _, file in ipairs(files) do
    local mod = modname .. "." .. vim.fn.fnamemodify(file, ":t:r")
    local ok, spec = pcall(require, mod)
    if not ok then
      err(mod .. ": " .. tostring(spec))
    elseif type(spec) ~= "table" then
      err(mod .. ": must return a spec table, got " .. type(spec))
    else
      add(spec, mod)
    end
  end
end

local function check_keys(name, keys)
  if type(keys) ~= "table" then
    return
  end
  for i, key in ipairs(keys) do
    if type(key) == "string" then
      key = { key }
    end
    if type(key[1]) ~= "string" then
      err(("%s: keys[%d] has no lhs"):format(name, i))
    elseif type(key.desc) ~= "string" or key.desc == "" then
      err(("%s: keys[%d] (%s) has no desc"):format(name, i, key[1]))
    else
      local rhs = key[2]
      if rhs ~= nil and type(rhs) ~= "string" and type(rhs) ~= "function" then
        err(("%s: keys[%d] (%s) rhs must be a string or function"):format(name, i, key[1]))
      end
      M.keymaps[#M.keymaps + 1] = { plugin = name, lhs = key[1], rhs = rhs, mode = key.mode or "n", desc = key.desc }
    end
  end
end

local function add_plugin(spec, from)
  local source = source_of(spec)
  if type(source) ~= "string" then
    err(from .. ": plugin spec without a source")
    return
  end
  if not spec.dir and not spec.url and not source:match("^[%w_.-]+/[%w_.-]+$") then
    err(from .. ": '" .. source .. "' is not an owner/repo short URL")
  end
  local name = name_of(spec)
  for key, value in pairs(spec) do
    if not VALID[key] then
      err(("%s: unknown key <%s>"):format(name, tostring(key)))
    elseif TYPES[key] and not vim.list_contains(TYPES[key], type(value)) then
      err(("%s: <%s> must be %s, got %s"):format(name, key, table.concat(TYPES[key], "|"), type(value)))
    end
  end
  check_keys(name, spec.keys)

  local existing = M.plugins[name]
  if existing then
    -- lazy.nvim merges repeated specs; only a conflicting source is an error.
    if source_of(existing) ~= source then
      err(("%s: declared with two sources (%s, %s)"):format(name, source_of(existing), source))
    end
    M.plugins[name] = vim.tbl_extend("keep", existing, spec)
  else
    M.plugins[name] = spec
    M.order[#M.order + 1] = name
  end

  if spec.dependencies then
    local deps = type(spec.dependencies) == "string" and { spec.dependencies } or spec.dependencies
    for _, dep in ipairs(deps) do
      add(dep, name .. ".dependencies")
    end
  end
end

function add(spec, from)
  if type(spec) == "string" then
    return add_plugin({ spec }, from)
  end
  if type(spec) ~= "table" then
    return err(from .. ": invalid spec of type " .. type(spec))
  end
  if spec.import then
    return import(spec.import)
  end
  if type(spec[1]) == "string" or spec.dir or spec.url then
    return add_plugin(spec, from)
  end
  if #spec == 0 then
    return err(from .. ": empty spec")
  end
  for _, item in ipairs(spec) do
    add(item, from)
  end
end

function M.setup(opts)
  M.options = opts
  if type(opts) ~= "table" or opts.spec == nil then
    err("setup() needs an options table with a `spec`")
    return
  end
  -- lazy.nvim manages itself as a plugin (it appears in lazy-lock.json too).
  M.plugins["lazy.nvim"] = { "folke/lazy.nvim" }
  M.order[#M.order + 1] = "lazy.nvim"
  add(opts.spec, "setup.spec")

  for _, name in ipairs(M.order) do
    local spec = M.plugins[name]
    if type(spec.init) == "function" then
      local ok, e = pcall(spec.init, spec)
      if not ok then
        err(name .. ": init() failed: " .. tostring(e))
      end
    end
  end
  for _, key in ipairs(M.keymaps) do
    vim.keymap.set(key.mode, key.lhs, key.rhs or "<Nop>", { desc = key.desc })
  end
end

function M.stats()
  return { count = #M.order, loaded = 0 }
end

return M
