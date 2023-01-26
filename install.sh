#!/bin/sh

set -ex

#--- Where is DOT_DIR? ---#
if [ -e "${CODESPACE}" ]; then
    DOT_DIR='/workspaces/.codespaces/.persistedshare/dotfiles'
fi

if [ "$(uname)" = 'Darwin' ]; then
    DOT_DIR="${HOME}/source/dotfiles"
fi

#--- Backup and link dot files ---#
if [ -f "${HOME}/.zshrc" ]; then
  cp "${HOME}/.zshrc" "${HOME}/.zshrc.bak"
  rm -rf "${HOME}/.zshrc";
fi
ln -s "${DOT_DIR}/zshrc" "${HOME}/.zshrc"

if [ -f "${HOME}/.gitconfig" ]; then
  cp "${HOME}/.gitconfig" "${HOME}/.gitconfig.bak";
  rm -rf "${HOME}/.gitconfig";
fi
ln -s "${DOT_DIR}/gitconfig" "${HOME}/.gitconfig";

if [ -f "${HOME}/.ackrc" ]; then
  cp "${HOME}/.ackrc" "${HOME}/.ackrc.bak";
  rm -rf "${HOME}/.ackrc";
fi
ln -s "${DOT_DIR}/ackrc" "${HOME}/.ackrc"

#--- Homebrew bundle ---#
if [ -e "${CODESPACE}" ]; then
  brew bundle --file="${DOT_DIR}/brewfile.codespaces"
fi

if [ "$(uname)" = 'Darwin' ]; then
  brew bundle --file="${DOT_DIR}/brewfile.darwin"
fi

brew update;
brew upgrade;

