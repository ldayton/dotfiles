#--- homebrew setup ---#
if [[ -f /opt/homebrew/bin/brew ]]; then
    eval "$(/opt/homebrew/bin/brew shellenv)"
else
    eval "$(/home/linuxbrew/.linuxbrew/bin/brew shellenv)"
fi

#--- history ---#
HISTFILE=~/.zsh_history    # where to save history
HISTSIZE=1000000000        # number of commands to keep in memory during session
SAVEHIST=1000000000        # number of commands to save to disk
HISTORY_IGNORE="(ll|ls|cd|pwd|exit|history|..|...|....)" # patterns to exclude from history
setopt INC_APPEND_HISTORY  # add commands to history immediately, not on shell exit
setopt EXTENDED_HISTORY    # save timestamp and duration with each command
setopt HIST_IGNORE_DUPS    # don't save command if it's same as the previous one
setopt HIST_IGNORE_SPACE   # don't save commands that start with a space
setopt SHARE_HISTORY       # share history between all terminal sessions in real-time

#--- completions ---#
autoload -Uz compinit && compinit

#--- rustup environment ---#
if [[ -d "$HOME/.cargo/bin" ]]; then
    export PATH="$HOME/.cargo/bin:$PATH"
fi

#--- interactive tools ---#
if [[ -x "$HOME/.local/bin/starship" ]]; then
    eval "$($HOME/.local/bin/starship init zsh)"
elif command -v starship &> /dev/null; then
    eval "$(starship init zsh)"
fi

if command -v zoxide &> /dev/null; then
    eval "$(zoxide init zsh)"
fi

export FZF_DEFAULT_OPTS='--height 40% --layout=reverse --border'
if command -v fzf &> /dev/null; then
    if fzf --zsh &> /dev/null 2>&1; then
        eval "$(fzf --zsh)"
    else
        [ -f ~/.fzf.zsh ] && source ~/.fzf.zsh
    fi
fi

#--- aliases ---#
if command -v eza &> /dev/null; then
    alias ls="eza"
    alias ll="eza -lh"
    alias la="eza -lah"
else
    alias ll="ls -lh"
    alias la="ls -lah"
fi
alias ..="cd .."
alias y="yt-dlp"
alias lg="lazygit"
alias claude='npx @anthropic-ai/claude-code'

#--- fix key bindings ---#
bindkey "^[[H" beginning-of-line     # Home key
bindkey "^[[F" end-of-line           # End key
bindkey "^[OH" beginning-of-line     # Home key (alternative)
bindkey "^[OF" end-of-line           # End key (alternative)
bindkey "^[[1~" beginning-of-line    # Home key (another variant)
bindkey "^[[4~" end-of-line          # End key (another variant)
bindkey "^[[3~" delete-char          # Delete key

#--- local configuration ---#
[[ -f ~/.zshrc.local ]] && . ~/.zshrc.local
