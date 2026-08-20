#!/bin/bash

# Dotfiles installation script
set -e

DOTFILES="$(cd "$(dirname "$0")" && pwd)"

echo "Installing dotfiles from $DOTFILES"

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

link() {
    local src="$1"
    local dest="$2"

    # `ln -s` succeeds on a target that does not exist, so a source removed from the repo
    # installs as a dangling symlink that nothing reports until something reads through it.
    # That is how ~/.claude/statusline.py outlived the statusline it was pointing at.
    if [ ! -e "$src" ]; then
        echo "  ✗ MISSING SOURCE: $src (not linking)"
        link_failures=$((link_failures + 1))
        return 0
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
        # Timestamped: a plain .backup silently overwrote the previous one, so the second
        # run through a path destroyed whatever the first run had saved.
        local backup
        backup="$dest.backup.$(date +%Y%m%d%H%M%S)"
        echo "  Backing up existing file: $dest -> $backup"
        mv "$dest" "$backup"
    elif [ -d "$dest" ]; then
        # It's a directory, don't remove it
        echo "  ERROR: $dest is a directory, not replacing"
        link_failures=$((link_failures + 1))
        return 0
    fi

    # Create symlink
    ln -s "$src" "$dest"
    # Make immutable where the OS allows it. Real on macOS, where chflags -h acts on the link
    # itself. Dead on Linux generally, not just WSL: chattr opens with O_NOFOLLOW and the
    # flags ioctl is unsupported on symlink inodes, so both lines are no-ops there. Do not
    # rely on these links being write-protected anywhere but macOS.
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
link "$DOTFILES/ripgrep/ripgreprc" "$HOME/.ripgreprc"

link "$DOTFILES/atuin/config.toml" "$HOME/.config/atuin/config.toml"

link "$DOTFILES/starship/starship.toml" "$HOME/.config/starship.toml"

mkdir -p "$HOME/.claude"
link "$DOTFILES/claude/settings.json" "$HOME/.claude/settings.json"

# ~/.claude/settings.json is a symlink into this repo, and Claude Code writes the current
# model back into it every time you switch — which would leave the repo permanently dirty
# with a value that is per-machine anyway. There is no user-level settings.local.json to
# escape into (that file is project-scoped), so `model` is stripped at stage time instead:
# the working file keeps whatever you picked, git never sees the key. Filters are per-clone
# config, not committed, so this has to be set here rather than in .gitattributes alone.
if command -v jq >/dev/null 2>&1; then
    git -C "$DOTFILES" config filter.claude-settings.clean "jq --indent 2 'del(.model)'"
    git -C "$DOTFILES" config filter.claude-settings.smudge cat
    git -C "$DOTFILES" config filter.claude-settings.required true
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
