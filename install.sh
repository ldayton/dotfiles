#!/bin/bash

# Dotfiles installation script
set -e

DOTFILES="$(cd "$(dirname "$0")" && pwd)"

echo "Installing dotfiles from $DOTFILES"

link() {
    local src="$1"
    local dest="$2"

    # Create parent directory if needed
    mkdir -p "$(dirname "$dest")"

    # Handle existing file/link if it exists
    if [ -L "$dest" ]; then
        # It's a symlink, safe to remove
        unlink "$dest"
    elif [ -f "$dest" ]; then
        # It's a regular file, back it up first
        echo "  Backing up existing file: $dest -> $dest.backup"
        mv "$dest" "$dest.backup"
    elif [ -d "$dest" ]; then
        # It's a directory, don't remove it
        echo "  ERROR: $dest is a directory, not replacing"
        return 1
    fi

    # Create symlink
    ln -s "$src" "$dest"
    echo "  ✓ Linked $dest"
}

link "$DOTFILES/zsh/zshrc" "$HOME/.zshrc"

if [ -f "$DOTFILES/git/gitconfig" ]; then
    if [ -e "$HOME/.gitconfig" ]; then
        echo "  ✗ Skipped $HOME/.gitconfig (already exists)"
    else
        cp "$DOTFILES/git/gitconfig" "$HOME/.gitconfig"
        echo "  ✓ Copied $HOME/.gitconfig"
    fi
fi
if [ -f "$DOTFILES/ripgrep/ripgreprc" ]; then
    link "$DOTFILES/ripgrep/ripgreprc" "$HOME/.ripgreprc"
fi

if [ -f "$DOTFILES/atuin/config.toml" ]; then
    link "$DOTFILES/atuin/config.toml" "$HOME/.config/atuin/config.toml"
fi

if [ -f "$DOTFILES/claude/settings.json" ]; then
    mkdir -p "$HOME/.claude"
    link "$DOTFILES/claude/settings.json" "$HOME/.claude/settings.json"
    link "$DOTFILES/claude/statusline.py" "$HOME/.claude/statusline.py"
fi

if [ -f "$DOTFILES/vscode/settings.json" ]; then
    if [[ "$OSTYPE" == "darwin"* ]]; then
        VSCODE_DIR="$HOME/Library/Application Support/Code/User"
    else
        VSCODE_DIR="$HOME/.config/Code/User"
    fi
    link "$DOTFILES/vscode/settings.json" "$VSCODE_DIR/settings.json"
fi

if [ -f "$DOTFILES/zed/settings.json" ]; then
    link "$DOTFILES/zed/settings.json" "$HOME/.config/zed/settings.json"
fi
if [ -f "$DOTFILES/zed/keymap.json" ]; then
    link "$DOTFILES/zed/keymap.json" "$HOME/.config/zed/keymap.json"
fi

if [ -f "$DOTFILES/dippy/config" ]; then
    link "$DOTFILES/dippy/config" "$HOME/.dippy/config"
fi

echo ""
echo "Dotfiles installed successfully!"
