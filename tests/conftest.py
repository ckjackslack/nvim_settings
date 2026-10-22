"""Pytest harness: run the config in a real, headless Neovim with isolated XDG dirs.

Every test gets its own XDG_CONFIG_HOME / XDG_DATA_HOME / XDG_STATE_HOME /
XDG_CACHE_HOME and HOME under ``tmp_path``. The repository is copied in as
``$XDG_CONFIG_HOME/nvim``, so nothing outside the temp dir is read or written.

The Neovim binary comes from ``$NVIM_BIN``, ``.cache/nvim/bin/nvim`` (see
``scripts/fetch-nvim.sh``) or ``nvim`` on ``$PATH``; without one the tests are
skipped.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest

REPO = Path(__file__).resolve().parent.parent
STUB_LAZY = Path(__file__).resolve().parent / "lua" / "lazy_stub"
MIN_NVIM = (0, 11, 0)
NETWORK_ENV = "NVIM_SETTINGS_NETWORK_TESTS"

# What gets copied into the isolated config dir (everything the config consists of).
CONFIG_ITEMS = ("init.lua", "lua", "lsp", "lazy-lock.json")

PROBE_TEMPLATE = """\
local __out = assert(os.getenv("NVIM_TEST_OUT"))
local __ok, __res = xpcall(function()
{body}
end, debug.traceback)
local __messages = vim.api.nvim_exec2("messages", {{ output = true }}).output
local __f = assert(io.open(__out, "w"))
__f:write(vim.json.encode({{
  ok = __ok,
  result = __ok and (__res == nil and vim.NIL or __res) or vim.NIL,
  error = (not __ok) and tostring(__res) or vim.NIL,
  messages = __messages,
}}))
__f:close()
vim.cmd("qa!")
"""

ERROR_PATTERNS = re.compile(r"(Error detected|E\d{1,4}:|stack traceback|Error executing)")


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--run-network",
        action="store_true",
        default=False,
        help=f"run tests that clone plugins from GitHub (or set {NETWORK_ENV}=1)",
    )


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    enabled = config.getoption("--run-network") or os.environ.get(NETWORK_ENV) == "1"
    if enabled:
        return
    skip = pytest.mark.skip(reason=f"network test: use --run-network or {NETWORK_ENV}=1")
    for item in items:
        if "network" in item.keywords:
            item.add_marker(skip)


def parse_version(output: str) -> tuple[int, int, int] | None:
    match = re.search(r"NVIM v(\d+)\.(\d+)\.(\d+)", output)
    return tuple(int(part) for part in match.groups()) if match else None  # type: ignore[return-value]


def find_nvim() -> str | None:
    candidates = [os.environ.get("NVIM_BIN"), str(REPO / ".cache" / "nvim" / "bin" / "nvim")]
    candidates.append(shutil.which("nvim"))
    for candidate in candidates:
        if candidate and Path(candidate).is_file() and os.access(candidate, os.X_OK):
            return candidate
    return None


@pytest.fixture(scope="session")
def nvim_bin() -> str:
    binary = find_nvim()
    if binary is None:
        pytest.skip("no Neovim binary (set NVIM_BIN or run scripts/fetch-nvim.sh)")
    out = subprocess.run([binary, "--version"], capture_output=True, text=True, check=True).stdout
    version = parse_version(out)
    if version is None or version < MIN_NVIM:
        pytest.skip(f"Neovim {version} is older than {MIN_NVIM}")
    return binary


def find_tool(name: str) -> str | None:
    """An executable from $PATH or from the venv running pytest."""
    found = shutil.which(name)
    if found:
        return found
    local = Path(sys.executable).parent / name
    return str(local) if local.is_file() else None


@dataclass
class Result:
    returncode: int
    stdout: str
    stderr: str
    ok: bool
    result: Any
    error: str | None
    messages: str

    def assert_clean(self) -> None:
        """No Lua error, nothing on stderr and no error in :messages."""
        assert self.ok, self.error
        assert self.returncode == 0, self.stderr
        assert not ERROR_PATTERNS.search(self.stderr), self.stderr
        assert not ERROR_PATTERNS.search(self.messages), self.messages


class Nvim:
    """A Neovim sandbox: isolated XDG dirs plus a copy of this config."""

    def __init__(self, binary: str, root: Path) -> None:
        self.binary = binary
        self.root = root
        self.config_home = root / "xdg" / "config"
        self.data_home = root / "xdg" / "data"
        self.config_dir = self.config_home / "nvim"
        self.data_dir = self.data_home / "nvim"
        self.home = root / "home"
        self.state_home = root / "xdg" / "state"
        self.cache_home = root / "xdg" / "cache"
        for path in (self.config_home, self.data_home, self.state_home, self.cache_home, self.home):
            path.mkdir(parents=True, exist_ok=True)
        self.config_dir.mkdir()
        for item in CONFIG_ITEMS:
            src = REPO / item
            if src.is_dir():
                shutil.copytree(src, self.config_dir / item)
            elif src.exists():
                shutil.copy2(src, self.config_dir / item)
        self._probe_count = 0

    def env(self, extra: Mapping[str, str] | None = None, *, safe: bool = True) -> dict[str, str]:
        env = {
            key: value
            for key, value in os.environ.items()
            if not key.startswith(("NVIM", "VIM", "XDG_", "VIRTUAL_ENV", "CONDA_"))
        }
        env.update(
            HOME=str(self.home),
            XDG_CONFIG_HOME=str(self.config_home),
            XDG_DATA_HOME=str(self.data_home),
            XDG_STATE_HOME=str(self.state_home),
            XDG_CACHE_HOME=str(self.cache_home),
        )
        if safe:
            env["NVIM_NO_PLUGINS"] = "1"
        env.update(extra or {})
        return env

    def install_lazy_stub(self) -> None:
        """Put a fake lazy.nvim where the bootstrap looks, so no clone happens."""
        shutil.copytree(STUB_LAZY, self.data_dir / "lazy" / "lazy.nvim")

    def run(
        self,
        body: str,
        *,
        safe: bool = True,
        env: Mapping[str, str] | None = None,
        args: Sequence[str] = (),
        pre_args: Sequence[str] = (),
        cwd: Path | None = None,
        timeout: float = 60,
    ) -> Result:
        """Start Neovim with this config, run Lua `body` (which may `return` a value), quit."""
        self._probe_count += 1
        probe = self.root / f"probe{self._probe_count}.lua"
        out = self.root / f"probe{self._probe_count}.json"
        indented = "\n".join("  " + line for line in body.strip("\n").splitlines())
        probe.write_text(PROBE_TEMPLATE.format(body=indented))
        cmd = [self.binary, *pre_args, "--headless", *args, "+luafile " + str(probe)]
        proc = subprocess.run(
            cmd,
            env=self.env({**(env or {}), "NVIM_TEST_OUT": str(out)}, safe=safe),
            cwd=cwd or self.root,
            capture_output=True,
            text=True,
            timeout=timeout,
            stdin=subprocess.DEVNULL,
        )
        if not out.exists():
            raise AssertionError(f"probe did not run (rc={proc.returncode})\n{proc.stderr}\n{proc.stdout}")
        data = json.loads(out.read_text())
        return Result(
            returncode=proc.returncode,
            stdout=proc.stdout,
            stderr=proc.stderr,
            ok=data["ok"],
            result=data["result"],
            error=data["error"],
            messages=data["messages"],
        )


@pytest.fixture
def nvim(nvim_bin: str, tmp_path: Path) -> Nvim:
    return Nvim(nvim_bin, tmp_path)
