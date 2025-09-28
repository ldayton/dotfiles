#!/bin/bash

# Dotfiles installation script
set -e

DOTFILES="$(cd "$(dirname "$0")" && pwd)"

echo "Installing dotfiles from $DOTFILES"

# Function to create symlink
link() {
    local src="$1"
    local dest="$2"

    # Create parent directory if needed
    mkdir -p "$(dirname "$dest")"

    # Remove existing file/link if it exists
    if [ -e "$dest" ] || [ -L "$dest" ]; then
        rm -rf "$dest"
    fi

    # Create symlink
    ln -s "$src" "$dest"
    echo "  ✓ Linked $dest"
}

# Basic dotfiles
link "$DOTFILES/git/gitconfig" "$HOME/.gitconfig"
link "$DOTFILES/zsh/zshrc" "$HOME/.zshrc"
link "$DOTFILES/ripgrep/ripgreprc" "$HOME/.ripgreprc"

# Claude config
if [ -f "$DOTFILES/claude/settings.json" ]; then
    mkdir -p "$HOME/.claude"
    link "$DOTFILES/claude/settings.json" "$HOME/.claude/settings.local.json"
fi

# VS Code
if [ -f "$DOTFILES/vscode/settings.json" ]; then
    if [[ "$OSTYPE" == "darwin"* ]]; then
        VSCODE_DIR="$HOME/Library/Application Support/Code/User"
    else
        VSCODE_DIR="$HOME/.config/Code/User"
    fi
    link "$DOTFILES/vscode/settings.json" "$VSCODE_DIR/settings.json"
fi

# Zed config (same path for macOS and Linux)
if [ -f "$DOTFILES/zed/settings.json" ]; then
    link "$DOTFILES/zed/settings.json" "$HOME/.config/zed/settings.json"
fi
if [ -f "$DOTFILES/zed/keymap.json" ]; then
    link "$DOTFILES/zed/keymap.json" "$HOME/.config/zed/keymap.json"
fi

echo ""
echo "Dotfiles installed successfully!"
