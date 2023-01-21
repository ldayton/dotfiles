#!/bin/sh

if [ -e ${CODESPACE} ]; then
    DOT_DIR='/workspaces/.codespaces/.persistedshare/dotfiles'
fi

if [ `uname` == 'Darwin' ]; then
    DOT_DIR="${HOME}/source/dotfiles"
fi

rm -rf "${HOME}/.zshrc"; ln -s "${DOT_DIR}/zshrc" "${HOME}/.zshrc"
rm -rf "${HOME}/.gitconfig"; ln -s "${DOT_DIR}/gitconfig" "${HOME}/.gitconfig"
rm -rf "${HOME}/.ackrc"; ln -s "${DOT_DIR}/ackrc" "${HOME}/.ackrc"

if [ -e ${CODESPACE} ]; then
  brew bundle --file="${DOT_DIR}/brewfile.codespaces"
fi

if [ `uname` == 'Darwin' ]; then
  brew bundle --file="${DOT_DIR}/brewfile.darwin"
fi

