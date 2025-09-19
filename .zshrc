#--- environment setup ---#
eval "$(/opt/homebrew/bin/brew shellenv)"

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

#--- interactive tools ---#
eval "$(starship init zsh)"
eval "$(zoxide init zsh)"
export FZF_DEFAULT_OPTS='--height 40% --layout=reverse --border'
source <(fzf --zsh)

#--- aliases ---#
alias ll="ls -lh"
alias la="ls -lah"
alias y="yt-dlp"