#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "bashlex",
# ]
# ///
"""Hook to auto-approve read-only CLI commands using bash AST parsing."""

from collections.abc import Callable
from typing import Any

import json
import os
import re
import sys

import bashlex

# === Data: What commands are safe ===

SAFE_COMMANDS = {
    "ack", "arch", "base32", "base64", "basenc", "basename", "cat", "cd",
    "cloc", "comm", "cut", "date", "df", "diff", "dig", "dir", "dirname",
    "du", "echo", "env", "false", "fd", "file", "free", "getent", "grep",
    "groups", "head", "host", "hostid", "hostname", "id", "join", "jq",
    "logname", "ls", "lsof", "mkdir", "netstat", "nproc", "nslookup", "paste",
    "ping", "pinky", "printenv", "printf", "ps", "pwd", "readlink", "realpath",
    "rg", "sleep", "ss", "stat", "tail", "traceroute", "tr", "tree", "true",
    "tsort", "tty", "type", "uname", "uniq", "uptime", "users", "vdir",
    "wc", "which", "who", "whoami", "yes",
}

SAFE_SCRIPTS = {
    "bashlex-debug.py",
    "custom-perms.py",
    "post-dashboard.sh",
    "test-perms.py",
}

# Scripts that wrap curl and should be checked as curl
CURL_WRAPPERS = {
    "grafana.py",
    "prometheus.py",
    "pushgateway.py",
}

PREFIX_COMMANDS = {
    "git config --get",
    "git config --list",
    "git stash list",
    "node --version",
    "python --version",
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

# === Data: CLI configurations ===

# CLI tools with action-based checks
# parser types:
#   "aws": action is second token (aws <service> <action>)
#   "first_token": action is first non-flag token
#   "second_token": action is second non-flag token
#   "variable_depth": action depth varies by service (see action_depth, service_depths)
CLI_CONFIGS = {
    "aws": {
        "safe_actions": {"filter-log-events", "lookup-events", "ls", "tail", "wait"},
        "safe_prefixes": ("batch-get-", "describe-", "get-", "head-", "list-"),
        "parser": "aws",
    },
    "az": {
        "safe_actions": {"list", "show", "get", "export"},
        "safe_prefixes": ("get-", "list-"),
        "parser": "variable_depth",
        "action_depth": 1,
        "service_depths": {"storage": 2, "keyvault": 2, "network": 2},
        "flags_with_arg": {"-g", "-o", "--output", "--query", "--resource-group", "--subscription"},
    },
    "gcloud": {
        "safe_actions": {"list", "describe", "get", "get-iam-policy", "export"},
        "safe_prefixes": ("get-", "list-", "describe-"),
        "parser": "variable_depth",
        "action_depth": 2,
        "service_depths": {"auth": 1, "config": 1, "projects": 1, "components": 1, "topic": 1},
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
        "flags_with_arg": {"-C", "-c", "--git-dir", "--work-tree"},
    },
    "kubectl": {
        "safe_actions": {"api-resources", "api-versions", "cluster-info", "describe", "explain", "get", "logs", "top", "version"},
        "safe_prefixes": (),
        "parser": "first_token",
        "flags_with_arg": {"-n", "--namespace", "--context", "--cluster", "--kubeconfig", "-o", "--output"},
    },
    "cdk": {
        "safe_actions": {"diff", "doctor", "docs", "list", "ls", "metadata", "notices", "synth"},
        "safe_prefixes": (),
        "parser": "first_token",
    },
    "pre-commit": {
        "safe_actions": {"help", "run", "sample-config", "validate-config", "validate-manifest"},
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

# === Custom validators ===


def check_awk(tokens: list[str]) -> bool:
    """Approve awk if no -f flag and no dangerous patterns in script."""
    for t in tokens:
        if t == "-f" or t.startswith("-f") or t == "--file":
            return False
        if not t.startswith("-"):
            if ">" in t or "|" in t or "system" in t:
                return False
    return True


def check_dmesg(tokens: list[str]) -> bool:
    """Approve dmesg if no clear flags."""
    for t in tokens:
        if t in {"-c", "-C", "--clear"}:
            return False
    return True


def check_find(tokens: list[str]) -> bool:
    """Approve find if no dangerous flags."""
    dangerous = {"-exec", "-execdir", "-ok", "-okdir", "-delete"}
    if dangerous & set(tokens):
        return False
    return True


def check_ifconfig(tokens: list[str]) -> bool:
    """Approve ifconfig if no modifying arguments (up/down/address changes)."""
    dangerous = {"up", "down", "add", "del", "delete", "tunnel", "promisc"}
    if dangerous & set(tokens):
        return False
    for t in tokens:
        if t.startswith("netmask") or t.startswith("broadcast"):
            return False
    return True


def check_ip(tokens: list[str]) -> bool:
    """Approve ip if using read-only subcommands."""
    if len(tokens) < 2:
        return False
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
    dangerous = {"add", "del", "delete", "change", "replace", "set", "flush", "exec"}
    if dangerous & set(tokens):
        return False
    return True


def check_journalctl(tokens: list[str]) -> bool:
    """Approve journalctl if no modifying flags."""
    for t in tokens:
        if t in {"--rotate", "--flush", "--sync", "--relinquish-var"} or t.startswith("--vacuum"):
            return False
    return True


def check_openssl(tokens: list[str]) -> bool:
    """Approve openssl x509 if -noout is present (read-only display)."""
    if len(tokens) < 2:
        return False
    subcommand = tokens[1]
    if subcommand == "x509" and "-noout" in tokens:
        return True
    return False


def check_sed(tokens: list[str]) -> bool:
    """Approve sed if no -i flag (in-place editing)."""
    for t in tokens:
        if t == "-i" or t.startswith("-i") or t.startswith("--in-place"):
            return False
    return True


def check_sort(tokens: list[str]) -> bool:
    """Approve sort if no -o flag."""
    return not any(t.startswith("-o") for t in tokens)


# Curl flags that send data (imply POST or upload)
CURL_DATA_FLAGS = {
    "-d", "--data", "--data-binary", "--data-raw", "--data-ascii",
    "--data-urlencode", "-F", "--form", "--form-string", "-T", "--upload-file",
}


def check_curl(tokens: list[str]) -> bool:
    """Approve curl if GET/HEAD only (no data-sending or method-changing flags)."""
    for i, t in enumerate(tokens):
        # Block data/upload flags (and --flag=value variants)
        if t in CURL_DATA_FLAGS:
            return False
        for flag in CURL_DATA_FLAGS:
            if t.startswith(flag + "="):
                return False
        # Check -X/--request for non-safe methods
        if t in {"-X", "--request"}:
            if i + 1 < len(tokens):
                method = tokens[i + 1].upper()
                if method not in {"GET", "HEAD", "OPTIONS", "TRACE"}:
                    return False
        # Also catch --request=METHOD
        if t.startswith("-X=") or t.startswith("--request="):
            method = t.split("=", 1)[1].upper()
            if method not in {"GET", "HEAD"}:
                return False
    return True


CUSTOM_CHECKS: dict[str, Callable[[list[str]], bool]] = {
    "awk": check_awk,
    "curl": check_curl,
    "dmesg": check_dmesg,
    "find": check_find,
    "ifconfig": check_ifconfig,
    "ip": check_ip,
    "journalctl": check_journalctl,
    "openssl": check_openssl,
    "sed": check_sed,
    "sort": check_sort,
}

# === Wrapper stripping ===


def strip_wrappers(tokens: list[str]) -> list[str]:
    """Strip wrapper commands and return inner command tokens."""
    while tokens and tokens[0] in WRAPPERS:
        prefix, skip = WRAPPERS[tokens[0]]
        if tokens[:len(prefix)] != prefix:
            break
        tokens = tokens[len(prefix):]

        if skip is None:
            while tokens:
                if tokens[0].startswith("-"):
                    tokens = tokens[1:]
                elif "=" in tokens[0]:
                    tokens = tokens[1:]
                else:
                    break
        elif skip == "nice":
            while tokens and tokens[0].startswith("-"):
                tokens = tokens[1:]
                if tokens:
                    tokens = tokens[1:]
        elif skip > 0:
            tokens = tokens[skip:]

    return tokens


# === CLI action extraction ===

AWS_FLAGS_WITH_ARG = {
    "--ca-bundle", "--cli-connect-timeout", "--cli-read-timeout", "--color",
    "--endpoint-url", "--output", "--profile", "--region",
}


def skip_flags(tokens: list[str], flags_with_arg: set[str]) -> int:
    """Return index of first non-flag token, skipping flags and their arguments."""
    i = 0
    while i < len(tokens):
        if tokens[i] in flags_with_arg:
            i += 2
        elif tokens[i].startswith("-"):
            i += 1
        else:
            break
    return i


def _get_aws_action(tokens: list[str]) -> str | None:
    """Extract action from aws <service> <action> command."""
    i = 0
    while i < len(tokens):
        if tokens[i] in AWS_FLAGS_WITH_ARG:
            i += 2
        elif tokens[i].startswith("--"):
            i += 1
        else:
            break
    if i + 1 < len(tokens):
        return tokens[i + 1]
    return None


def _get_nth_token(tokens: list[str], n: int, flags_with_arg: set[str]) -> str | None:
    """Extract nth non-flag token (0-indexed)."""
    i = skip_flags(tokens, flags_with_arg)
    if i + n < len(tokens):
        return tokens[i + n]
    return None


def _get_variable_depth_action(tokens: list[str], config: dict[str, Any]) -> str | None:
    """Get action at variable depth based on first token (service/group)."""
    flags_with_arg = config.get("flags_with_arg", set())
    default_depth = config.get("action_depth", 1)
    service_depths = config.get("service_depths", {})

    i = skip_flags(tokens, flags_with_arg)
    if i >= len(tokens):
        return None

    service = tokens[i]
    depth = service_depths.get(service, default_depth)

    target_idx = i + depth
    if target_idx < len(tokens):
        return tokens[target_idx]
    return None


PARSERS: dict[str, Callable[[list[str], dict[str, Any]], str | None]] = {
    "aws": lambda tokens, config: _get_aws_action(tokens),
    "first_token": lambda tokens, config: _get_nth_token(tokens, 0, config.get("flags_with_arg", set())),
    "second_token": lambda tokens, config: _get_nth_token(tokens, 1, config.get("flags_with_arg", set())),
    "variable_depth": _get_variable_depth_action,
}


def get_cli_action(tokens: list[str], parser: str, config: dict[str, Any] | None = None) -> str | None:
    """Extract action from CLI command based on parser type."""
    return PARSERS[parser](tokens, config)


# === Core safety check ===


def is_command_safe(tokens: list[str]) -> bool:
    """Check if a single command (as token list) is safe."""
    if not tokens:
        return False

    tokens = strip_wrappers(tokens)
    if not tokens:
        return False

    cmd = tokens[0]
    args = tokens[1:]

    if cmd in SAFE_COMMANDS:
        return True

    if os.path.basename(cmd) in SAFE_SCRIPTS:
        return True

    # Curl wrappers should be checked as curl
    if os.path.basename(cmd) in CURL_WRAPPERS:
        return check_curl(tokens)

    for prefix in PREFIX_COMMANDS:
        prefix_tokens = prefix.split()
        if tokens[:len(prefix_tokens)] == prefix_tokens:
            return True

    if cmd in CUSTOM_CHECKS:
        return CUSTOM_CHECKS[cmd](tokens)

    cmd = CLI_ALIASES.get(cmd, cmd)

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


# === AST parsing ===

OUTPUT_REDIRECTS = {">", ">>", "&>", ">&"}
SAFE_REDIRECT_TARGETS = {"/dev/null"}


def has_unsafe_output_redirect(node: Any) -> bool:
    """Check if a command node has any unsafe output redirects."""
    if node.kind == "command":
        for part in node.parts:
            if part.kind == "redirect" and part.type in OUTPUT_REDIRECTS:
                if isinstance(part.output, int):
                    continue
                target = getattr(part.output, "word", None) if hasattr(part, "output") else None
                if target in SAFE_REDIRECT_TARGETS:
                    continue
                return True
    return False


def get_command_nodes(node: Any) -> list[list[str]] | None:
    """Recursively extract command nodes from AST.

    Returns None if any command has output redirects (defer).
    Returns list of command token lists otherwise.
    """
    if node.kind == "command":
        if has_unsafe_output_redirect(node):
            return None
        parts = [p.word for p in node.parts if p.kind == "word"]
        return [parts] if parts else []

    children = getattr(node, "list", None) or getattr(node, "parts", None) or []
    commands = []
    for child in children:
        result = get_command_nodes(child)
        if result is None:
            return None
        commands.extend(result)
    return commands


def preprocess_command(cmd_string: str) -> str:
    """Strip bash reserved words that bashlex doesn't handle."""
    return re.sub(r'\btime\s+(-p\s+)?', '', cmd_string)


def parse_commands(cmd_string: str) -> list[list[str]] | None:
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
                return None
            commands.extend(result)
        return commands
    except Exception:
        return None


# === Entry point ===


def main() -> None:
    input_data = json.load(sys.stdin)
    command = input_data.get("tool_input", {}).get("command", "")

    if not command.strip():
        sys.exit(0)

    commands = parse_commands(command)

    if commands is None:
        sys.exit(0)

    if not commands:
        sys.exit(0)

    for cmd_tokens in commands:
        if not is_command_safe(cmd_tokens):
            sys.exit(0)

    print(json.dumps({"decision": "approve", "reason": "all commands safe"}))
    sys.exit(0)


if __name__ == "__main__":
    main()
