lspconfig = require "lspconfig"
util = require "lspconfig/util"

lspconfig.pylsp.setup {
  cmd = { "pylsp" },
  filetypes = { "python" },
  root_dir = util.root_pattern(".git", vim.fn.getcwd()),
  settings = {
    pylsp = {
      analyses = {
	use_flake8 = true,
	use_pylint = false,
	use_isort = true,
	use_black = true,
      },
      staticchek = true,
    },
  },
}
