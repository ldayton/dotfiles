# Meta

- "amh" means "answer me here", as in don't do anything, but write your response in the chat so I can give feedback
- "yon" = answer yes or no: lead with Yes/No, then at most one short clarifying sentence
- "iafs" = answer in a few sentences
- "iass" = answer in a single sentence
- CLAUDE.md is generated from ~/source/dotfiles/claude/CLAUDE.base.md + ~/.claude/CLAUDE.local.md
- Base contains universal preferences; local contains work/machine-specific config
- "dotfiles" refers to ~/source/dotfiles
- If I ask for a table or chart, I want a minimum of 3 columns displayed to me. Total width of max 100 chars.

# Approvals

- Never merge a PR without explicit instruction for that PR

# Code Style

- Don't add needless blank lines in function bodies
- Provide in-line comments very sparingly
- Docstrings should be informative, and typically only one line unless documenting something complex
- Never use environment/config fallbacks. Fail fast
- Don't leave cruft comments behind when removing code.
- Don't add comments narrating a change
- Bug fixes: write the test, watch it fail, then fix
- Pin to current latest stable; document any older pick

# Git & GitHub

- Do your work in a git worktree, not the main checkout; leave the main checkout at latest origin/main
- Don't add test plan sections to PR bodies
- "cap" means commit and push
- Prefer git mv over mv
- Don't amend commits or use --force
- Don't use gh --admin or try to bypass rulesets
- use git -C instead of needlessly changing directories
- Don't use git stash/pop, there may be other Claude sessions running
- Squash-merge with a big-picture summary, not stitched commit msgs
- Don't hard-wrap commit bodies or markdown prose

# Shell Tools

- Don't run ruff unless I ask
- Don't do Python syntax checks (uv run python3 -m py_compile). They're pointless.
- Use -sS with curl
- Use `pypi <package>` to look up latest PyPI versions
- Dippy audit log: ~/.claude/dippy-audit.log
- After editing markdown, run `prettier --prose-wrap never --write` on touched files

# WSL

- When given a Windows path you can find it on WSL under /mnt/c

# MCP

- First preference is for direct access to MCP servers, but second preference using CLI tools like gh
