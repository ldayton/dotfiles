#!/bin/sh

set -e

#--- Where is DOT_DIR? ---#
if [ -e "${CODESPACE}" ]; then
  DOT_DIR='/workspaces/.codespaces/.persistedshare/dotfiles'
else
  DOT_DIR="${HOME}/source/dotfiles"
fi

#--- Backup and link dot files ---#
safelink() {
  if [ -e "${HOME}/${1}" ]; then
    if diff "${DOT_DIR}/${1}" "${HOME}/${1}" >/dev/null; then
      return
    else
      cp "${HOME}/${1}" "${HOME}/${1}.${date +%s}.bak"
      echo "backed up ${HOME}/${1}" to "${HOME}/${1}.${date +%s}.bak"
    fi
    rm "${HOME}/${1}"
  fi
  ln -s "${DOT_DIR}/${1}" "${HOME}/${1}"
}

safelink ".zshrc"
safelink ".gitconfig"
safelink ".ackrc"
safelink ".hyper.js"

#--- Homebrew bundle ---#
brew bundle --file "${DOT_DIR}/brewfile" -q
brew update -q
brew upgrade -q

#--- NPM global installs ---#
# export PNPM_HOME="${HOME}/.pnpm"
# export PATH="${PATH}:${PNPM_HOME}"
# pnpm install -g \
#   cypress \
#   eslint \
#   jest \
#   lighthouse \
#   netlify-cli \
#   npm-check-updates \
#   npm-run-all \
#   playwright \
#   prettier \
#   vite \
#   vitest \
#   @types/node \
#   typescript

#--- Update oh-my-zsh ---#
/bin/zsh -c ". ${HOME}/.oh-my-zsh/oh-my-zsh.sh && omz update"
