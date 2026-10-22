#!/usr/bin/env sh
# Download an official Neovim release into .cache/nvim (used by the tests when
# no NVIM_BIN is set). Usage: scripts/fetch-nvim.sh [version]   e.g. v0.12.6
set -eu

version="${1:-v0.12.6}"
case "$(uname -s)-$(uname -m)" in
  Linux-x86_64) asset="nvim-linux-x86_64" ;;
  Linux-aarch64 | Linux-arm64) asset="nvim-linux-arm64" ;;
  Darwin-arm64) asset="nvim-macos-arm64" ;;
  Darwin-x86_64) asset="nvim-macos-x86_64" ;;
  *) echo "unsupported platform: $(uname -s)-$(uname -m)" >&2; exit 1 ;;
esac

root="$(cd "$(dirname "$0")/.." && pwd)"
dest="$root/.cache/nvim"
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT

url="https://github.com/neovim/neovim/releases/download/$version/$asset.tar.gz"
echo "Downloading $url"
curl -fsSL -o "$tmp/nvim.tar.gz" "$url"
tar -xzf "$tmp/nvim.tar.gz" -C "$tmp"
rm -rf "$dest"
mkdir -p "$root/.cache"
mv "$tmp/$asset" "$dest"
"$dest/bin/nvim" --version | head -1
