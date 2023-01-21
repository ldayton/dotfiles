# oh-my-zsh
export ZSH="$HOME/.oh-my-zsh"
ZSH_THEME="jonathan"
HYPHEN_INSENSITIVE="true"
zstyle ':omz:update' mode auto      # update automatically without asking
zstyle ':omz:update' frequency 13 # how often to auto-update (in days)
COMPLETION_WAITING_DOTS="true"
plugins=(
    git
    z
)
source $ZSH/oh-my-zsh.sh

# text editors
export EDITOR=vim

# history settings
HISTFILE=~/.zsh_history
HISTSIZE=1000000000
SAVEHIST=1000000000
HISTORY_IGNORE="(ll|ls|cd|pwd|exit|exit:history|..|...|....)"
setopt INC_APPEND_HISTORY  # immediately append to history
setopt EXTENDED_HISTORY  # add timestamp
setopt HIST_IGNORE_DUPS  # don't add consecutive dups
