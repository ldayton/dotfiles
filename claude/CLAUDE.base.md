# Meta
- "note" means add to this file (CLAUDE.md)
- CLAUDE.md is generated from ~/source/dotfiles/claude/CLAUDE.base.md + ~/.claude/CLAUDE.local.md
- Base contains universal preferences; local contains work/machine-specific config
- "dotfiles" refers to ~/source/dotfiles

# Code Style
- Don't add needless blank lines in function bodies
- Provide in-line comments very sparingly
- Docstrings should be informative, and typically only one line unless documenting something complex
- Never use environment/config fallbacks. Fail fast
- Don't leave cruft comments behind when removing code.

# Git & GitHub
- Don't add test plan sections to PR bodies
- "cap" means commit and push
- Prefer git mv over mv
- Don't amend commits or use --force
- use git -C instead of needlessly changing directories

# Shell Tools
- Prefer fd over find
- Prefer rg over grep
- If I tell you to 'ruff' I'm asking you to get this to pass: `uv run ruff check --fix && uv run ruff format`
- Don't run ruff unless I ask
- Don't do Python syntax checks (uv run python3 -m py_compile). They're pointless.
- Use -sS with curl
- Use `pypi <package>` to look up latest PyPI versions

# MCP Tools
- Use GitHub's MCP server when possible, not the gh CLI tool

# WSL
- When given a Windows path you can find it on WSL under /mnt/c
