-- Language servers via the native Neovim 0.11+ API.
--
-- Server definitions live in lsp/<name>.lua at the root of this config (picked
-- up automatically by `vim.lsp.config`); this module only enables them and adds
-- buffer-local keymaps when a server attaches. No nvim-lspconfig needed.
-- The executables come from Mason (see lua/plugins/lsp.lua) or from $PATH.
local M = {}

--- Servers enabled at startup. Each needs an lsp/<name>.lua definition.
M.servers = { "basedpyright", "ruff", "lua_ls" }

---@param client vim.lsp.Client
---@param buf integer
function M.on_attach(client, buf)
  local function map(lhs, rhs, desc)
    vim.keymap.set("n", lhs, rhs, { buffer = buf, desc = "LSP: " .. desc })
  end

  map("gd", vim.lsp.buf.definition, "Go to definition")
  map("gD", vim.lsp.buf.declaration, "Go to declaration")
  map("<leader>cf", function()
    if not require("config.format").format(buf) then
      vim.lsp.buf.format({ bufnr = buf })
    end
  end, "Format buffer")
  map("<leader>ci", function()
    vim.lsp.buf.code_action({ context = { only = { "source.organizeImports" }, diagnostics = {} }, apply = true })
  end, "Organize imports")

  if client.name == "ruff" then
    -- basedpyright gives far better hover docs; ruff's would only duplicate them.
    client.server_capabilities.hoverProvider = false
  end
end

function M.setup()
  vim.diagnostic.config({
    severity_sort = true,
    virtual_text = { spacing = 2, source = "if_many" },
    float = { source = "if_many" },
  })

  vim.api.nvim_create_autocmd("LspAttach", {
    group = vim.api.nvim_create_augroup("nvim_settings_lsp", { clear = true }),
    desc = "Buffer-local LSP keymaps",
    callback = function(args)
      local client = vim.lsp.get_client_by_id(args.data.client_id)
      if client then
        M.on_attach(client, args.buf)
      end
    end,
  })

  vim.lsp.enable(M.servers)
end

return M
