#!/bin/bash

# Dotfiles installation script
#
# Usage: ./install.sh [--dry-run]
#
# Re-running after a pull is the normal case, so the common outcome should read as "already
# correct" rather than as a pile of churn -- and --dry-run has to be able to say what would
# change without changing it.
set -e

DOTFILES="$(CDPATH='' cd -P -- "$(dirname -- "$0")" && pwd)"
DRY_RUN=false
[ "${1:-}" = "--dry-run" ] && DRY_RUN=true

echo "Installing dotfiles from $DOTFILES"
$DRY_RUN && echo "(dry run -- nothing will be changed)"

# Refuse to install out of a linked worktree. $DOTFILES would be the worktree path, so every
# link in $HOME would point into it and dangle as soon as it is removed -- and the
# skip-worktree flag below is per-worktree, so it would not carry to the main checkout either.
if git_dir="$(git -C "$DOTFILES" rev-parse --git-dir 2>/dev/null)" \
   && common_dir="$(git -C "$DOTFILES" rev-parse --git-common-dir 2>/dev/null)" \
   && [ "$(cd "$DOTFILES" && cd "$git_dir" && pwd)" != "$(cd "$DOTFILES" && cd "$common_dir" && pwd)" ]; then
    echo "  ✗ $DOTFILES is a linked worktree; run install.sh from the main checkout" >&2
    exit 1
fi

link_failures=0

# Immutability is best-effort: chflags on macOS, where it genuinely protects the link; on
# Linux chattr opens with O_NOFOLLOW and the flags ioctl is unsupported on symlink inodes, so
# both calls are no-ops there. Never fatal -- a mutable link still works.
set_immutable()   { chattr +i "$1" 2>/dev/null || chflags -h uchg "$1" 2>/dev/null || true; }
clear_immutable() { chattr -i "$1" 2>/dev/null || chflags -h nouchg "$1" 2>/dev/null || true; }

link() {
    local src="$1"
    local dest="$2"

    # `ln -s` succeeds on a target that does not exist, so a source removed from the repo
    # installs as a dangling symlink that nothing reports until something reads through it.
    # That is how ~/.claude/statusline.py outlived the statusline it was pointing at.
    if [ ! -e "$src" ]; then
        echo "  ✗ MISSING SOURCE: $src -- refusing to create a dangling link"
        link_failures=$((link_failures + 1))
        return 0
    fi

    # Already correct: say so and touch nothing. Comparing the raw link target rather than
    # readlink -f keeps this working on macOS, where -f is not available on stock readlink --
    # and every link here is created with an absolute src, so the comparison is exact.
    if [ -L "$dest" ] && [ "$(readlink "$dest")" = "$src" ]; then
        echo "  = Already linked: $dest"
        return 0
    fi

    if $DRY_RUN; then
        echo "  → Would link: $dest -> $src"
        return 0
    fi

    mkdir -p "$(dirname "$dest")"

    if [ -L "$dest" ]; then
        clear_immutable "$dest"
        unlink "$dest"
    elif [ -d "$dest" ]; then
        echo "  ✗ $dest is a directory -- not replacing"
        link_failures=$((link_failures + 1))
        return 0
    elif [ -e "$dest" ]; then
        # Timestamped: a plain .backup silently overwrote the previous one, so the second run
        # through a path destroyed whatever the first run had saved.
        local backup
        backup="$dest.backup.$(date +%Y%m%d%H%M%S)"
        clear_immutable "$dest"
        mv "$dest" "$backup"
        echo "  ⤴ Backed up existing file -> $backup"
    fi

    ln -s "$src" "$dest"
    set_immutable "$dest"

    # Prove it, rather than trusting that ln did what was asked.
    if [ ! -e "$dest" ]; then
        echo "  ✗ Link created but does not resolve: $dest"
        link_failures=$((link_failures + 1))
        return 0
    fi
    echo "  ✓ Linked $dest -> $src"
}

link "$DOTFILES/zsh/zshrc" "$HOME/.zshrc"

# Copied, not linked, and never overwritten: user.email is per-account and the tracked copy
# deliberately carries none, so a rerun must not reset an identity set by hand.
if [ -e "$HOME/.gitconfig" ]; then
    echo "  = Left alone: $HOME/.gitconfig (already exists)"
elif $DRY_RUN; then
    echo "  → Would copy: $HOME/.gitconfig <- $DOTFILES/git/gitconfig"
else
    cp "$DOTFILES/git/gitconfig" "$HOME/.gitconfig"
    echo "  ✓ Copied $HOME/.gitconfig"
fi
link "$DOTFILES/ripgrep/ripgreprc" "$HOME/.ripgreprc"

link "$DOTFILES/atuin/config.toml" "$HOME/.config/atuin/config.toml"

link "$DOTFILES/starship/starship.toml" "$HOME/.config/starship.toml"

# settings.json is generated, not linked. Claude Code writes into it, and a tracked file it
# writes to needed a clean filter to keep `model` out of commits plus skip-worktree to silence
# what the filter could not -- and skip-worktree makes git ignore the file outright, which is
# how a block of hooks stayed in the committed config for months after leaving the disk.
# Generating means the file the app writes to is simply not a file git tracks.
if $DRY_RUN; then
    echo "  → Would generate: $HOME/.claude/settings.json (from $DOTFILES/claude/settings.base.json)"
elif settings_result="$(CLAUDE_SETTINGS_BASE="$DOTFILES/claude/settings.base.json" "$DOTFILES/claude/build-settings")"; then
    if [ "$settings_result" = "unchanged" ]; then
        echo "  = Already current: $HOME/.claude/settings.json"
    else
        echo "  ✓ Generated $HOME/.claude/settings.json"
    fi
else
    echo "  ✗ Could not generate $HOME/.claude/settings.json"
    link_failures=$((link_failures + 1))
fi

if [[ "$OSTYPE" == "darwin"* ]]; then
    VSCODE_DIR="$HOME/Library/Application Support/Code/User"
else
    VSCODE_DIR="$HOME/.config/Code/User"
fi
link "$DOTFILES/vscode/settings.json" "$VSCODE_DIR/settings.json"

link "$DOTFILES/zed/settings.json" "$HOME/.config/zed/settings.json"
link "$DOTFILES/zed/keymap.json" "$HOME/.config/zed/keymap.json"

echo ""
if [ "$link_failures" -gt 0 ]; then
    echo "Dotfiles installed with $link_failures problem(s) above."
    exit 1
fi
echo "Dotfiles installed successfully!"
