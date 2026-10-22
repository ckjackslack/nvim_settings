-- Format on save through the LSP, with an allow-list of formatters per filetype.
--
-- Only the listed language servers ever format a buffer: Python files go through
-- ruff, which also sorts the imports first (replacing the original black + isort).
-- Other filetypes are left alone.
--
--   :FormatToggle    toggle format-on-save globally
--   :FormatToggle!   toggle it for the current buffer only
local M = {}

--- filetype -> names of LSP clients allowed to format it
---@type table<string, string[]>
M.formatters = {
  python = { "ruff" },
}

--- filetypes whose imports are organised (LSP "source.organizeImports") before formatting
---@type table<string, boolean>
M.organize_imports = {
  python = true,
}

--- Is format-on-save enabled for `buf`? A buffer-local setting wins over the global one.
---@param buf? integer
---@return boolean
function M.enabled(buf)
  buf = buf or vim.api.nvim_get_current_buf()
  local local_value = vim.b[buf].format_on_save
  if local_value ~= nil then
    return local_value
  end
  return vim.g.format_on_save ~= false
end

--- Toggle format-on-save, globally or for one buffer. Returns the new state.
---@param buffer_only? boolean
---@param buf? integer
---@return boolean
function M.toggle(buffer_only, buf)
  buf = buf or vim.api.nvim_get_current_buf()
  local new_state = not M.enabled(buf)
  if buffer_only then
    vim.b[buf].format_on_save = new_state
  else
    vim.g.format_on_save = new_state
    vim.b[buf].format_on_save = nil
  end
  return new_state
end

--- The LSP client names allowed to format a filetype (empty when none).
---@param filetype string
---@return string[]
function M.formatters_for(filetype)
  return M.formatters[filetype] or {}
end

--- Synchronously apply `client`'s "source.organizeImports" code action to `buf`.
---@param client vim.lsp.Client
---@param buf integer
local function organize_imports(client, buf)
  local params = {
    textDocument = vim.lsp.util.make_text_document_params(buf),
    range = {
      start = { line = 0, character = 0 },
      ["end"] = { line = vim.api.nvim_buf_line_count(buf), character = 0 },
    },
    context = { only = { "source.organizeImports" }, diagnostics = {} },
  }
  local response = client:request_sync("textDocument/codeAction", params, 2000, buf)
  for _, action in ipairs(response and response.result or {}) do
    if not action.edit and client:supports_method("codeAction/resolve") then
      local resolved = client:request_sync("codeAction/resolve", action, 2000, buf)
      action = resolved and resolved.result or action
    end
    if action.edit then
      vim.lsp.util.apply_workspace_edit(action.edit, client.offset_encoding)
    end
  end
end

--- Format `buf` with its allowed formatter, if one is attached. Returns true if it ran.
---@param buf? integer
---@return boolean
function M.format(buf)
  buf = buf or vim.api.nvim_get_current_buf()
  local allowed = M.formatters_for(vim.bo[buf].filetype)
  if #allowed == 0 then
    return false
  end
  local clients = vim.lsp.get_clients({ bufnr = buf, method = "textDocument/formatting" })
  for _, client in ipairs(clients) do
    if vim.list_contains(allowed, client.name) then
      if M.organize_imports[vim.bo[buf].filetype] then
        organize_imports(client, buf)
      end
      vim.lsp.buf.format({ bufnr = buf, id = client.id, timeout_ms = 2000 })
      return true
    end
  end
  return false
end

function M.setup()
  if vim.g.format_on_save == nil then
    vim.g.format_on_save = true
  end

  vim.api.nvim_create_autocmd("BufWritePre", {
    group = vim.api.nvim_create_augroup("nvim_settings_format", { clear = true }),
    desc = "Format on save with the allowed LSP formatter",
    callback = function(args)
      if M.enabled(args.buf) then
        M.format(args.buf)
      end
    end,
  })

  vim.api.nvim_create_user_command("FormatToggle", function(cmd)
    local state = M.toggle(cmd.bang)
    local scope = cmd.bang and "this buffer" or "all buffers"
    vim.notify(("Format on save %s for %s"):format(state and "enabled" or "disabled", scope))
  end, { bang = true, desc = "Toggle format on save (! = current buffer only)" })

  vim.api.nvim_create_user_command("Format", function()
    if not M.format() then
      vim.notify("No allowed formatter attached to this buffer", vim.log.levels.WARN)
    end
  end, { desc = "Format the current buffer with its allowed LSP formatter" })
end

return M
