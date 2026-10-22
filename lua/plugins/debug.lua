-- Debugging: nvim-dap + UI, with Python (debugpy) and Lua (debug Neovim itself) adapters.
local function dap(fn, ...)
  local args = { ... }
  return function()
    require("dap")[fn](unpack(args))
  end
end

---@type LazySpec
return {
  {
    "mfussenegger/nvim-dap",
    dependencies = {
      "rcarriga/nvim-dap-ui",
      "nvim-neotest/nvim-nio", -- required by nvim-dap-ui
      "theHamsta/nvim-dap-virtual-text",
      "mfussenegger/nvim-dap-python",
      "nvim-telescope/telescope-dap.nvim",
      "jbyuki/one-small-step-for-vimkind",
    },
    keys = {
      { "<F5>", dap("continue"), desc = "Debug: start / continue" },
      { "<S-F5>", dap("terminate"), desc = "Debug: stop" },
      { "<F10>", dap("step_over"), desc = "Debug: step over" },
      { "<F11>", dap("step_into"), desc = "Debug: step into" },
      { "<F12>", dap("step_out"), desc = "Debug: step out" },
      { "<leader>b", dap("toggle_breakpoint"), desc = "Debug: toggle breakpoint" },
      {
        "<leader>B",
        function()
          require("dap").set_breakpoint(vim.fn.input("Breakpoint condition: "))
        end,
        desc = "Debug: conditional breakpoint",
      },
      {
        "<leader>du",
        function()
          require("dapui").toggle()
        end,
        desc = "Debug: toggle UI",
      },
      {
        "<leader>dt",
        function()
          require("dap-python").test_method()
        end,
        desc = "Debug: Python test method",
      },
      {
        "<leader>dc",
        function()
          require("dap-python").test_class()
        end,
        desc = "Debug: Python test class",
      },
      {
        "<leader>ds",
        function()
          require("dap-python").debug_selection()
        end,
        mode = "x",
        desc = "Debug: Python selection",
      },
      {
        "<leader>dl",
        function()
          require("osv").launch({ port = 8086 })
        end,
        desc = "Debug: start Lua debug server in this Neovim",
      },
      {
        "<leader>df",
        function()
          require("telescope").extensions.dap.frames()
        end,
        desc = "Debug: find frames",
      },
    },
    config = function()
      local dap_ = require("dap")
      local dapui = require("dapui")
      dapui.setup()
      require("nvim-dap-virtual-text").setup({})

      -- Open/close the UI with the debug session (as in the original config).
      dap_.listeners.before.attach.nvim_settings = dapui.open
      dap_.listeners.before.launch.nvim_settings = dapui.open
      dap_.listeners.before.event_terminated.nvim_settings = dapui.close
      dap_.listeners.before.event_exited.nvim_settings = dapui.close

      -- Python: debugpy from Mason, debuggee runs in the project's virtualenv.
      local python = require("config.python")
      local dap_python = require("dap-python")
      dap_python.resolve_python = function()
        return python.python_path()
      end
      dap_python.setup(python.debugpy_python())
      dap_python.test_runner = "pytest"

      -- Lua: attach to a Neovim instance started with <leader>dl (one-small-step-for-vimkind).
      dap_.adapters.nlua = function(callback, config)
        callback({ type = "server", host = config.host or "127.0.0.1", port = config.port or 8086 })
      end
      dap_.configurations.lua = {
        { type = "nlua", request = "attach", name = "Attach to running Neovim instance" },
      }

      pcall(function()
        require("telescope").load_extension("dap")
      end)
    end,
  },
}
