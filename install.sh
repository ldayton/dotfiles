#!/bin/bash

# Dotfiles installation script
set -e

DOTFILES="$(cd "$(dirname "$0")" && pwd)"

echo "Installing dotfiles from $DOTFILES"

link() {
    local src="$1"
    local dest="$2"

    # `ln -s` succeeds on a target that does not exist, so a source removed from the repo
    # installs as a dangling symlink that nothing reports until something reads through it.
    # That is how ~/.claude/statusline.py survived the statusline moving into dippy.
    if [ ! -e "$src" ]; then
        echo "  ✗ MISSING SOURCE: $src (not linking)"
        return 1
    fi

    # Create parent directory if needed
    mkdir -p "$(dirname "$dest")"

    # Handle existing file/link if it exists
    if [ -L "$dest" ]; then
        # It's a symlink - remove immutable flag if set, then unlink
        chattr -i "$dest" 2>/dev/null || chflags -h nouchg "$dest" 2>/dev/null || true
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
    # Make immutable where the filesystem allows it. Real on macOS (chflags -h acts on the
    # link itself); a no-op on WSL, where chattr cannot read or set flags on a symlink at
    # all -- so do not count on these links being write-protected on Linux.
    chattr +i "$dest" 2>/dev/null || chflags -h uchg "$dest" 2>/dev/null || true
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

if [ -f "$DOTFILES/starship/starship.toml" ]; then
    link "$DOTFILES/starship/starship.toml" "$HOME/.config/starship.toml"
fi

if [ -f "$DOTFILES/claude/settings.json" ]; then
    mkdir -p "$HOME/.claude"
    link "$DOTFILES/claude/settings.json" "$HOME/.claude/settings.json"
fi

# ~/.claude/settings.json is a symlink into this repo, and Claude Code writes the current
# model back into it every time you switch — which would leave the repo permanently dirty
# with a value that is per-machine anyway. There is no user-level settings.local.json to
# escape into (that file is project-scoped), so `model` is stripped at stage time instead:
# the working file keeps whatever you picked, git never sees the key. Filters are per-clone
# config, not committed, so this has to be set here rather than in .gitattributes alone.
if command -v jq >/dev/null 2>&1; then
    git -C "$DOTFILES" config filter.claude-settings.clean "jq --indent 2 'del(.model)'"
    git -C "$DOTFILES" config filter.claude-settings.smudge cat
    echo "  ✓ Configured claude-settings filter (keeps 'model' out of git)"
else
    echo "  ! jq not found — 'model' changes will show as repo modifications"
fi
# The filter keeps `model` out of every commit, but git cannot use its stat cache through
# a filter, so the file still reads as modified until something re-hashes it. skip-worktree
# silences that. Both are wanted: the filter is the guarantee (nothing bad is committable
# even if this flag is later cleared), skip-worktree is the quiet.
#
# The cost, and it is a real one: while this flag is set, git ignores the file entirely. To
# change settings.json deliberately, or if a pull reports it would be overwritten:
#     git update-index --no-skip-worktree claude/settings.json
#     ... edit / pull / commit ...
#     git update-index --skip-worktree claude/settings.json
git -C "$DOTFILES" update-index --skip-worktree claude/settings.json 2>/dev/null \
    && echo "  ✓ settings.json marked skip-worktree (model switches stay out of git status)"

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

echo ""
echo "Dotfiles installed successfully!"
