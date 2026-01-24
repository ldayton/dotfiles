# Meta
- "note" means add to this file (CLAUDE.md)
- CLAUDE.md is generated from ~/source/dotfiles/claude/CLAUDE.base.md + ~/.claude/CLAUDE.local.md
- Base contains universal preferences; local contains work/machine-specific config
- "dotfiles" refers to ~/source/dotfiles
- If I ask for a table or chart, I want a minimum of 3 columns displayed to me. Total width of max 130 chars.

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
- Don't use gh --admin or try to bypass rulesets
- use git -C instead of needlessly changing directories

# Shell Tools
- Prefer fd over find
- Prefer rg over grep
- If I tell you to 'ruff' I'm asking you to get this to pass: `uv run ruff check --fix && uv run ruff format`
- Don't run ruff unless I ask
- Don't do Python syntax checks (uv run python3 -m py_compile). They're pointless.
- Use -sS with curl
- Use `pypi <package>` to look up latest PyPI versions
- Dippy audit log: ~/.claude/dippy-audit.log

# WSL
- When given a Windows path you can find it on WSL under /mnt/c

# MCP
- First preference is for direct access to MCP servers, but second preference using CLI tools like gh
