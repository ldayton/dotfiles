# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "bashlex",
# ]
# ///
"""Hook to auto-approve read-only CLI commands using bash AST parsing."""

import json
import sys

import bashlex

# Simple commands that are always safe
SAFE_COMMANDS = {
    "ack", "basename", "cat", "cd", "cut", "date", "df", "diff",
    "dirname", "du", "echo", "env", "file", "grep", "groups",
    "head", "hostname", "id", "jq", "ls", "lsof", "mkdir",
    "printenv", "ps", "pwd", "readlink", "realpath", "rg", "ss",
    "stat", "tail", "tr", "tree", "type", "uname", "uniq",
    "uptime", "wc", "which", "whoami",
}

# Commands that are safe when they start with specific token sequences
PREFIX_COMMANDS = {
    "git config --get",
    "git config --list",
    "git stash list",
    "node --version",
    "python --version",
    "pre-commit",
}

# Wrapper commands that just modify how the inner command runs
WRAPPERS = {
    "time": 0,      # time <cmd>
    "nice": None,   # nice [-n N] <cmd> - skip until non-flag
    "timeout": 1,   # timeout <duration> <cmd>
    "env": None,    # env [VAR=val]... <cmd> - skip VAR=val pairs
}

# CLI tools with action-based checks
CLI_CONFIGS = {
    "aws": {
        "safe_actions": {"ls"},
        "safe_prefixes": ("describe-", "get-", "head-", "list-"),
        "parser": "aws",
    },
    "az": {
        "safe_actions": {"list", "show"},
        "safe_prefixes": ("get-", "list-"),
        "parser": "last_token",
    },
    "gcloud": {
        "safe_actions": {"list", "describe"},
        "safe_prefixes": ("get-", "list-"),
        "parser": "last_token",
    },
    "gh": {
        "safe_actions": {"checks", "diff", "list", "search", "status", "view"},
        "safe_prefixes": (),
        "parser": "second_token",
    },
    "docker": {
        "safe_actions": {"diff", "events", "history", "images", "inspect", "logs", "port", "ps", "stats", "top"},
        "safe_prefixes": (),
        "parser": "first_token",
    },
    "brew": {
        "safe_actions": {"config", "deps", "desc", "doctor", "info", "leaves", "list", "options", "outdated", "search", "uses"},
        "safe_prefixes": (),
        "parser": "first_token",
    },
    "git": {
        "safe_actions": {"blame", "cat-file", "check-ignore", "cherry", "describe", "diff", "fetch", "for-each-ref", "grep", "log", "ls-files", "ls-tree", "merge-base", "name-rev", "reflog", "rev-list", "rev-parse", "shortlog", "show", "status"},
        "safe_prefixes": (),
        "parser": "first_token",
    },
    "kubectl": {
        "safe_actions": {"api-resources", "api-versions", "cluster-info", "describe", "explain", "get", "logs", "top", "version"},
        "safe_prefixes": (),
        "parser": "first_token",
    },
}

CLI_ALIASES = {
    "kubeat": "kubectl",
    "kubeci": "kubectl",
    "kubeci2": "kubectl",
    "kubelab": "kubectl",
}


def check_find(tokens):
    """Approve find if no dangerous flags."""
    dangerous = {"-exec", "-execdir", "-ok", "-okdir", "-delete"}
    if dangerous & set(tokens):
        return False
    return True


def check_sort(tokens):
    """Approve sort if no -o flag."""
    if "-o" in tokens or any(t.startswith("-o") for t in tokens):
        return False
    return True


CUSTOM_CHECKS = {
    "find": check_find,
    "sort": check_sort,
}


def strip_wrappers(tokens):
    """Strip wrapper commands and return inner command tokens."""
    while tokens and tokens[0] in WRAPPERS:
        wrapper = tokens[0]
        skip = WRAPPERS[wrapper]
        tokens = tokens[1:]

        if skip is None:
            # Skip flags and VAR=val pairs until we hit a command
            while tokens:
                if tokens[0].startswith("-"):
                    tokens = tokens[1:]
                    # Handle -n 10 style (skip next arg too)
                    if wrapper == "nice" and tokens:
                        tokens = tokens[1:]
                elif "=" in tokens[0]:
                    # env VAR=val
                    tokens = tokens[1:]
                else:
                    break
        elif skip > 0:
            # Skip fixed number of args
            tokens = tokens[skip:]

    return tokens


def get_cli_action(tokens, parser):
    """Extract action from CLI command based on parser type."""
    if parser == "aws":
        # aws <service> <action>
        if len(tokens) >= 2:
            return tokens[1]
    elif parser == "first_token":
        # git <action>, docker <action>
        if tokens:
            return tokens[0]
    elif parser == "second_token":
        # gh <resource> <action>
        if len(tokens) >= 2:
            return tokens[1]
    elif parser == "last_token":
        # az <group> [subgroup...] <action>
        action = None
        for token in tokens:
            if token.startswith("-"):
                break
            action = token
        return action
    return None


def is_command_safe(tokens):
    """Check if a single command (as token list) is safe."""
    if not tokens:
        return False

    # Strip wrappers
    tokens = strip_wrappers(tokens)
    if not tokens:
        return False

    cmd = tokens[0]
    args = tokens[1:]

    # Check simple safe commands
    if cmd in SAFE_COMMANDS:
        return True

    # Check prefix commands
    for prefix in PREFIX_COMMANDS:
        prefix_tokens = prefix.split()
        if tokens[:len(prefix_tokens)] == prefix_tokens:
            return True

    # Check custom handlers
    if cmd in CUSTOM_CHECKS:
        return CUSTOM_CHECKS[cmd](tokens)

    # Resolve aliases
    cmd = CLI_ALIASES.get(cmd, cmd)

    # Check CLI configs
    if cmd in CLI_CONFIGS:
        config = CLI_CONFIGS[cmd]
        action = get_cli_action(args, config["parser"])

        if not action:
            return False

        if action in config["safe_actions"]:
            return True

        if config["safe_prefixes"] and action.startswith(config["safe_prefixes"]):
            return True

    return False


# Output redirect types that write to files
OUTPUT_REDIRECTS = {">", ">>", "&>", ">&"}


def has_output_redirect(node):
    """Check if a command node has any output redirects."""
    if node.kind == "command":
        for part in node.parts:
            if part.kind == "redirect" and part.type in OUTPUT_REDIRECTS:
                return True
    return False


def get_command_nodes(node):
    """Recursively extract command nodes from AST.

    Returns None if any command has output redirects (defer).
    Returns list of command token lists otherwise.
    """
    commands = []

    if node.kind == "command":
        # Check for output redirects first
        if has_output_redirect(node):
            return None
        parts = [p.word for p in node.parts if p.kind == "word"]
        if parts:
            commands.append(parts)
    elif node.kind == "compound":
        for child in node.list:
            result = get_command_nodes(child)
            if result is None:
                return None
            commands.extend(result)
    elif node.kind == "pipeline":
        for child in node.parts:
            result = get_command_nodes(child)
            if result is None:
                return None
            commands.extend(result)
    elif hasattr(node, "parts"):
        for child in node.parts:
            result = get_command_nodes(child)
            if result is None:
                return None
            commands.extend(result)
    elif hasattr(node, "list"):
        for child in node.list:
            result = get_command_nodes(child)
            if result is None:
                return None
            commands.extend(result)

    return commands


def preprocess_command(cmd_string):
    """Strip bash reserved words that bashlex doesn't handle."""
    import re
    # Remove 'time' prefix (bashlex doesn't support it)
    # Handle: time cmd, time -p cmd
    cmd_string = re.sub(r'\btime\s+(-p\s+)?', '', cmd_string)
    return cmd_string


def parse_commands(cmd_string):
    """Parse a bash command string and return list of commands.

    Returns None if parsing fails or output redirects detected.
    """
    try:
        cmd_string = preprocess_command(cmd_string)
        parts = bashlex.parse(cmd_string)
        commands = []
        for part in parts:
            result = get_command_nodes(part)
            if result is None:
                return None  # output redirect detected
            commands.extend(result)
        return commands
    except Exception:
        return None


def main():
    input_data = json.load(sys.stdin)
    command = input_data.get("tool_input", {}).get("command", "")

    if not command.strip():
        sys.exit(0)

    commands = parse_commands(command)

    if commands is None:
        # Parse error - defer
        sys.exit(0)

    if not commands:
        sys.exit(0)

    # ALL commands must be safe
    for cmd_tokens in commands:
        if not is_command_safe(cmd_tokens):
            sys.exit(0)  # defer

    # All safe - approve
    print(json.dumps({"decision": "approve", "reason": "all commands safe"}))
    sys.exit(0)


if __name__ == "__main__":
    main()
