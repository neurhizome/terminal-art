#!/usr/bin/env zsh
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DOT="$ROOT/dotfiles"
ln -sf "$DOT/.zshrc" ~/.zshrc
ln -sf "$DOT/.vimrc" ~/.vimrc
mkdir -p ~/.ipython/profile_default/startup
cp "$DOT/ipython/profile_default/"* ~/.ipython/profile_default/ 2>/dev/null || true
cp "$DOT/ipython/profile_default/startup/"* ~/.ipython/profile_default/startup/
echo "dotfiles installed. restart shell."
