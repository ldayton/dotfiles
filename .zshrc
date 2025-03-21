#--- oh-my-zsh ---#
export ZSH="$HOME/.oh-my-zsh"
# ZSH_THEME="jonathan"
ZSH_THEME="robbyrussell"
HYPHEN_INSENSITIVE="true"
zstyle ':omz:update' mode auto    # update automatically without asking
zstyle ':omz:update' frequency 13 # how often to auto-update (in days)
COMPLETION_WAITING_DOTS="true"
plugins=(
    git
    fzf
    zoxide
)
DISABLE_MAGIC_FUNCTIONS=true  # disable url escaping on paste
source $ZSH/oh-my-zsh.sh

#--- history settings ---#
HISTFILE=~/.zsh_history
HISTSIZE=1000000000
SAVEHIST=1000000000
HISTORY_IGNORE="(ll|ls|cd|pwd|exit|exit:history|..|...|....)"
setopt INC_APPEND_HISTORY # immediately append to history
setopt EXTENDED_HISTORY   # add timestamp
setopt HIST_IGNORE_DUPS   # don't add consecutive dups

#--- text editor ---#
export EDITOR=vi

#--- fzf history ---#
export FZF_DEFAULT_OPTS='--height 40% --layout=reverse --border'


#--- nvm ---#

export NVM_DIR="$HOME/.nvm"
[ -s "/usr/local/opt/nvm/nvm.sh" ] && \. "/usr/local/opt/nvm/nvm.sh"
[ -s "/usr/local/opt/nvm/etc/bash_completion.d/nvm" ] && \. "/usr/local/opt/nvm/etc/bash_completion.d/nvm"

#--- pnpm ---#
export PNPM_HOME="${HOME}/.pnpm"
export PATH="${PATH}:${PNPM_HOME}"
alias p="pnpm"

#--- add setup.sh to PATH ---#
if [ -e "${CODESPACE}" ]; then
    DOT_DIR='/workspaces/.codespaces/.persistedshare/dotfiles'
else
    DOT_DIR="${HOME}/ldayton/dotfiles"
fi
export PATH="${PATH}:${DOT_DIR}"

#-- shortcuts --#
alias y="yt-dlp"

#-- python --#
# source virtualenvwrapper.sh
