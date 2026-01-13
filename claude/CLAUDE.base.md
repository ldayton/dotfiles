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

## MCP Servers

You have access to MCP (Model Context Protocol) servers via the `mcp-cli` cli.
MCP provides tools for interacting with external systems like GitHub, databases, and APIs.

Available Commands:

```bash
mcp-cli                              # List all servers and tool names
mcp-cli <server>                     # Show server tools and parameters
mcp-cli <server>/<tool>              # Get tool JSON schema and descriptions
mcp-cli <server>/<tool> '<json>'     # Call tool with JSON arguments
mcp-cli grep "<pattern>"             # Search tools by name (glob pattern)
```

**Add `-d` to include tool descriptions** (e.g., `mcp-cli <server> -d`)

Workflow:

1. **Discover**: Run `mcp-cli` to see available servers and tools or `mcp-cli grep "<pattern>"` to search for tools by name (glob pattern)
2. **Inspect**: Run `mcp-cli <server> -d` or `mcp-cli <server>/<tool>` to get the full JSON input schema if required context is missing. If there are more than 5 mcp servers defined don't use -d as it will print all tool descriptions and might exceed the context window.  
3. **Execute**: Run `mcp-cli <server>/<tool> '<json>'` with correct arguments

### Examples

```bash
# With inline JSON
$ mcp-cli github/search_repositories '{"query": "mcp server", "per_page": 5}'

# From stdin (use '-' to indicate stdin input)
$ echo '{"query": "mcp"}' | mcp-cli github/search_repositories -

# Using a heredoc with '-' for stdin (recommended for complex JSON)
mcp-cli server/tool - <<EOF
{"content": "Text with 'single quotes' and \"double quotes\""}
EOF

# Complex Command chaining with xargs and jq
mcp-cli filesystem/search_files '{"path": "src/", "pattern": "*.ts"}' --json | jq -r '.content[0].text' | head -1 | xargs -I {} sh -c 'mcp-cli filesystem/read_file "{\"path\": \"{}\"}"'
```

### Rules

1. **Always check schema first**: Run `mcp-cli <server> -d or `mcp-cli <server>/<tool>` before calling any tool
3. **Quote JSON arguments**: Wrap JSON in single quotes to prevent shell interpretation

