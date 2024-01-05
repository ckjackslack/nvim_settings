vim.opt.completeopt = {"menuone", "noselect", "noinsert", "preview"}

vim.opt.shortmess = vim.opt.shortmess + {c = true}

local cmp = require'cmp'
cmp.setup({
  mapping = {
    ['<S-Tab>'] = cmp.mapping.select_prev_item(),
    ['<Tab>'] = cmp.mapping.select_next_item(),
    ['<C-S-f>'] = cmp.mapping.scroll_docs(-4),
    ['<C-f>'] = cmp.mapping.scroll_docs(4),
    ['<C-Space>'] = cmp.mapping.complete(),
    ['<C-e>'] = cmp.mapping.close(),
    ['<CR>'] = cmp.mapping.confirm({
      behavior = cmp.ConfirmBehavior.Insert,
      select = true,
    }),
  },
  sources = {
    { name = "path" },
    { name = "nvim_lsp", keyword_length = 3 },
    { name = "nvim_lsp_signature_help" },
    { name = "nvim_lua", keyword_length = 2 },
    { name = "buffer", keyword_length = 2 },
    { name = "vsnip", keyword_length = 2 },
  },
  snippet = {
    expand = function(args)
      vim.fn["vsnip#anonymous"](args.body)
    end,
  },
  window = {
    completion = cmp.config.window.bordered(),
    documentation = cmp.config.window.bordered(),
  },
  formatting = {
    fields = {"menu", "abbr", "kind"},
    format = function(entry, item)
      local menu_icon = {
        nvim_lsp = 'λ',
	vsnip = '⋗',
	buffer = 'b',
	path = 'p'
      }
      item.menu = menu_icon[entry.source.name]
      return item
    end,
  },
})
