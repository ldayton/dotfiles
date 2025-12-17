#!/usr/bin/env -S uv run
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
    "ack", "arch", "base32", "base64", "basenc", "basename",
    "bashlex-debug.py", "cat", "cd", "cloc", "comm", "custom-perms.py",
    "cut", "date", "df", "diff", "dig", "dir", "dirname", "du", "echo",
    "env", "false", "fd", "file", "free", "getent", "grep", "groups", "head", "host",
    "hostid", "hostname", "id", "join", "jq", "logname", "ls", "lsof",
    "mkdir", "netstat", "nproc", "nslookup", "paste", "pinky", "printenv",
    "printf", "ps", "pwd", "readlink", "realpath", "rg", "sleep", "ss",
    "stat", "tail", "test-perms.py", "traceroute", "tr", "tree", "true",
    "tsort", "tty", "type", "uname", "uniq", "uptime", "users", "vdir",
    "wc", "which", "who", "whoami", "yes",
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
# Value is (prefix_tokens, skip_count) where skip_count can be:
#   int: skip that many args after prefix
#   None: skip flags and VAR=val pairs
#   "nice": skip -n N style flags
WRAPPERS = {
    "time": (["time"], 0),
    "nice": (["nice"], "nice"),
    "timeout": (["timeout"], 1),
    "env": (["env"], None),
    "uv": (["uv", "run"], None),
}

# Known unsafe actions for CLIs using "scan" parser
UNSAFE_ACTIONS = {
    "create", "delete", "update", "set", "remove", "add", "import", "patch",
    "start", "stop", "reset", "restart", "ssh", "scp", "deploy", "rollback",
    "invoke", "attach", "detach", "deallocate", "redeploy",
    "set-iam-policy", "add-iam-policy-binding", "remove-iam-policy-binding",
    "activate-service-account", "revoke", "login", "apply", "edit", "replace",
    "run", "exec", "scale", "cordon", "uncordon", "drain", "taint", "label",
    "annotate", "patch", "rollout",
}

# CLI tools with action-based checks
# parser types:
#   "aws": action is second token (aws <service> <action>)
#   "first_token": action is first non-flag token
#   "second_token": action is second non-flag token
#   "scan": scan first 4 non-flag tokens for safe/unsafe action
CLI_CONFIGS = {
    "aws": {
        "safe_actions": {"filter-log-events", "lookup-events", "ls", "tail", "wait"},
        "safe_prefixes": ("batch-get-", "describe-", "get-", "head-", "list-"),
        "parser": "aws",
    },
    "az": {
        "safe_actions": {"list", "show", "get", "export"},
        "safe_prefixes": ("get-", "list-"),
        "parser": "scan",
        "flags_with_arg": {"-g", "-o", "--output", "--query", "--resource-group", "--subscription"},
    },
    "gcloud": {
        "safe_actions": {"list", "describe", "get", "get-iam-policy", "export"},
        "safe_prefixes": ("get-", "list-", "describe-"),
        "parser": "scan",
        "flags_with_arg": {"--account", "--configuration", "--format", "--project", "--region", "--zone"},
    },
    "gh": {
        "safe_actions": {"checks", "diff", "list", "search", "status", "view"},
        "safe_prefixes": (),
        "parser": "second_token",
        "flags_with_arg": {"-R", "--repo"},
    },
    "docker": {
        "safe_actions": {"diff", "events", "history", "images", "inspect", "logs", "port", "ps", "stats", "top"},
        "safe_prefixes": (),
        "parser": "first_token",
        "flags_with_arg": {"-c", "--config", "--context", "-H", "--host", "-l", "--log-level"},
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
        "parser": "scan",
        "flags_with_arg": {"-n", "--namespace", "--context", "--cluster", "--kubeconfig", "-o", "--output"},
    },
    "cdk": {
        "safe_actions": {"diff", "doctor", "docs", "list", "ls", "metadata", "notices", "synth"},
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


def check_dmesg(tokens):
    """Approve dmesg if no clear flags."""
    for t in tokens:
        if t in {"-c", "-C", "--clear"}:
            return False
    return True


def check_find(tokens):
    """Approve find if no dangerous flags."""
    dangerous = {"-exec", "-execdir", "-ok", "-okdir", "-delete"}
    if dangerous & set(tokens):
        return False
    return True


def check_ifconfig(tokens):
    """Approve ifconfig if no modifying arguments (up/down/address changes)."""
    dangerous = {"up", "down", "add", "del", "delete", "tunnel", "promisc"}
    if dangerous & set(tokens):
        return False
    # Block if setting address (any token that looks like IP or netmask assignment)
    for t in tokens:
        if t.startswith("netmask") or t.startswith("broadcast"):
            return False
    return True


def check_ip(tokens):
    """Approve ip if using read-only subcommands."""
    if len(tokens) < 2:
        return False
    # ip [options] OBJECT { COMMAND }
    # Find the object (first non-flag token after 'ip')
    obj = None
    for t in tokens[1:]:
        if t.startswith("-"):
            continue
        obj = t
        break
    if not obj:
        return False
    safe_objects = {"addr", "address", "link", "route", "neigh", "neighbor", "rule", "maddr", "mroute", "tunnel"}
    if obj not in safe_objects:
        return False
    # Block modifying commands
    dangerous = {"add", "del", "delete", "change", "replace", "set", "flush", "exec"}
    if dangerous & set(tokens):
        return False
    return True


def check_journalctl(tokens):
    """Approve journalctl if no modifying flags."""
    for t in tokens:
        if t in {"--rotate", "--flush", "--sync", "--relinquish-var"} or t.startswith("--vacuum"):
            return False
    return True


def check_ping(tokens):
    """Approve ping if no flood flag."""
    if "-f" in tokens:
        return False
    return True


def check_sort(tokens):
    """Approve sort if no -o flag."""
    if "-o" in tokens or any(t.startswith("-o") for t in tokens):
        return False
    return True


def check_sed(tokens):
    """Approve sed if no -i flag (in-place editing)."""
    for t in tokens:
        if t == "-i" or t.startswith("-i") or t.startswith("--in-place"):
            return False
    return True


def check_awk(tokens):
    """Approve awk if no -f flag and no dangerous patterns in script."""
    for t in tokens:
        if t == "-f" or t.startswith("-f") or t == "--file":
            return False
        if not t.startswith("-"):
            if ">" in t or "|" in t or "system" in t:
                return False
    return True


# Git flags that take an argument
GIT_FLAGS_WITH_ARG = {"-C", "-c", "--git-dir", "--work-tree"}


def check_git(tokens):
    """Approve git if action is safe, stripping -C and similar flags."""
    # tokens[0] is 'git', work with the rest
    args = tokens[1:]
    # Strip flags that take arguments
    while args:
        if args[0] in GIT_FLAGS_WITH_ARG and len(args) >= 2:
            args = args[2:]
        elif args[0].startswith("-"):
            args = args[1:]
        else:
            break
    if not args:
        return False
    action = args[0]
    config = CLI_CONFIGS["git"]
    return action in config["safe_actions"]


def check_openssl(tokens):
    """Approve openssl x509 if -noout is present (read-only display)."""
    if len(tokens) < 2:
        return False
    subcommand = tokens[1]
    if subcommand == "x509" and "-noout" in tokens:
        return True
    return False


CUSTOM_CHECKS = {
    "awk": check_awk,
    "dmesg": check_dmesg,
    "find": check_find,
    "git": check_git,
    "ifconfig": check_ifconfig,
    "ip": check_ip,
    "journalctl": check_journalctl,
    "openssl": check_openssl,
    "ping": check_ping,
    "sed": check_sed,
    "sort": check_sort,
}


def strip_wrappers(tokens):
    """Strip wrapper commands and return inner command tokens."""
    while tokens and tokens[0] in WRAPPERS:
        prefix, skip = WRAPPERS[tokens[0]]
        # Check if tokens start with the full prefix
        if tokens[:len(prefix)] != prefix:
            break
        tokens = tokens[len(prefix):]

        if skip is None:
            # Skip flags and VAR=val pairs until we hit a command
            while tokens:
                if tokens[0].startswith("-"):
                    tokens = tokens[1:]
                elif "=" in tokens[0]:
                    tokens = tokens[1:]
                else:
                    break
        elif skip == "nice":
            # Skip -n N style flags
            while tokens and tokens[0].startswith("-"):
                tokens = tokens[1:]
                if tokens:
                    tokens = tokens[1:]
        elif skip > 0:
            tokens = tokens[skip:]

    return tokens


# AWS CLI global flags that take an argument
AWS_FLAGS_WITH_ARG = {
    "--ca-bundle", "--cli-connect-timeout", "--cli-read-timeout", "--color",
    "--endpoint-url", "--output", "--profile", "--region",
}


def get_cli_action(tokens, parser, config=None):
    """Extract action from CLI command based on parser type."""
    if parser == "aws":
        # aws [global-flags] <service> <action>
        i = 0
        while i < len(tokens):
            if tokens[i] in AWS_FLAGS_WITH_ARG:
                i += 2
            elif tokens[i].startswith("--"):
                i += 1
            else:
                break
        # tokens[i] is service, tokens[i+1] is action
        if i + 1 < len(tokens):
            return tokens[i + 1]
        return None
    elif parser == "first_token":
        # docker <action>, brew <action>
        # Skip global flags and their values
        flags_with_arg = config.get("flags_with_arg", set()) if config else set()
        i = 0
        while i < len(tokens):
            if tokens[i] in flags_with_arg:
                i += 2
            elif tokens[i].startswith("-"):
                i += 1
            else:
                break
        if i < len(tokens):
            return tokens[i]
        return None
    elif parser == "second_token":
        # gh <resource> <action>
        # Skip global flags and their values
        flags_with_arg = config.get("flags_with_arg", set()) if config else set()
        i = 0
        while i < len(tokens):
            if tokens[i] in flags_with_arg:
                i += 2
            elif tokens[i].startswith("-"):
                i += 1
            else:
                break
        if i + 1 < len(tokens):
            return tokens[i + 1]
        return None
    elif parser == "scan":
        # Scan first 4 non-flag tokens for a known action
        safe_actions = config["safe_actions"] if config else set()
        safe_prefixes = config["safe_prefixes"] if config else ()
        flags_with_arg = config.get("flags_with_arg", set()) if config else set()
        non_flag_count = 0
        skip_next = False
        for token in tokens:
            if skip_next:
                skip_next = False
                continue
            if token in flags_with_arg:
                skip_next = True
                continue
            if token.startswith("-"):
                continue
            non_flag_count += 1
            if non_flag_count > 4:
                return None
            if token in safe_actions:
                return token
            if safe_prefixes and token.startswith(safe_prefixes):
                return token
            if token in UNSAFE_ACTIONS:
                return token
        return None
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
        action = get_cli_action(args, config["parser"], config)
        if not action:
            return False
        if action in config["safe_actions"]:
            return True
        if config["safe_prefixes"] and action.startswith(config["safe_prefixes"]):
            return True
    return False


# Output redirect types that write to files
OUTPUT_REDIRECTS = {">", ">>", "&>", ">&"}

# Safe redirect destinations
SAFE_REDIRECT_TARGETS = {"/dev/null"}


def has_unsafe_output_redirect(node):
    """Check if a command node has any unsafe output redirects."""
    if node.kind == "command":
        for part in node.parts:
            if part.kind == "redirect" and part.type in OUTPUT_REDIRECTS:
                # 2>&1 style redirects have int output (fd), not a file - safe
                if isinstance(part.output, int):
                    continue
                # Check if redirecting to a safe target
                target = getattr(part.output, "word", None) if hasattr(part, "output") else None
                if target in SAFE_REDIRECT_TARGETS:
                    continue
                return True
    return False


def get_command_nodes(node):
    """Recursively extract command nodes from AST.

    Returns None if any command has output redirects (defer).
    Returns list of command token lists otherwise.
    """
    commands = []

    if node.kind == "command":
        # Check for unsafe output redirects first
        if has_unsafe_output_redirect(node):
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
