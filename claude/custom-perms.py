#!/usr/bin/env python3
"""Hook to auto-approve read-only CLI commands."""

import json
import re
import sys


def check_find(command, tokens):
    """Approve find if no -exec/-execdir/-ok/-okdir/-delete."""
    dangerous = {"-exec", "-execdir", "-ok", "-okdir", "-delete"}
    if dangerous & set(tokens):
        return None  # defer
    return {"decision": "approve", "reason": "safe: find (no exec)"}


def check_sort(command, tokens):
    """Approve sort if no -o (output file)."""
    if "-o" in tokens or any(t.startswith("-o") for t in tokens):
        return None  # defer
    return {"decision": "approve", "reason": "safe: sort (no -o)"}


# Custom checkers for commands that don't fit the standard pattern
CUSTOM_CHECKS = {
    "find": check_find,
    "sort": check_sort,
}

# Per-CLI configuration
CONFIGS = {
    "aws": {
        "safe_actions": {"ls"},
        "safe_prefixes": ("describe-", "get-", "head-", "list-"),
        "parser": "aws",  # aws <service> <action>
    },
    "az": {
        "safe_actions": {"list", "show"},
        "safe_prefixes": ("get-", "list-"),
        "parser": "last_token",  # az <group> [subgroup...] <action>
    },
    "gcloud": {
        "safe_actions": {"list", "describe"},
        "safe_prefixes": ("get-", "list-"),
        "parser": "last_token",  # gcloud <group> [subgroup...] <action>
    },
    "gh": {
        "safe_actions": {"checks", "diff", "list", "search", "status", "view"},
        "safe_prefixes": (),
        "parser": "last_token",  # gh <group> <action>
    },
    "docker": {
        "safe_actions": {"diff", "events", "history", "images", "inspect", "logs", "port", "ps", "stats", "top"},
        "safe_prefixes": (),
        "parser": "first_token",  # docker <command> [args]
    },
    "brew": {
        "safe_actions": {"config", "deps", "desc", "doctor", "info", "leaves", "list", "options", "outdated", "search", "uses"},
        "safe_prefixes": (),
        "parser": "first_token",  # brew <command> [args]
    },
    "git": {
        "safe_actions": {"blame", "branch", "cat-file", "check-ignore", "cherry", "describe", "diff", "fetch", "for-each-ref", "grep", "log", "ls-files", "ls-tree", "merge-base", "name-rev", "reflog", "rev-list", "rev-parse", "shortlog", "show", "status", "tag"},
        "safe_prefixes": (),
        "parser": "first_token",  # git <command> [args]
    },
    "kubectl": {
        "safe_actions": {"api-resources", "api-versions", "cluster-info", "describe", "explain", "get", "logs", "top", "version"},
        "safe_prefixes": (),
        "parser": "first_token",  # kubectl <command> [args]
    },
}

# Aliases that share config with another CLI
ALIASES = {
    "kubeat": "kubectl",
    "kubeci": "kubectl",
    "kubeci2": "kubectl",
    "kubelab": "kubectl",
}


def parse_aws(tokens):
    """Parse: aws <service> <action> → return (service, action)"""
    if len(tokens) < 2:
        return None, None
    match = re.match(r"^[\w-]+$", tokens[0]) and re.match(r"^[\w-]+$", tokens[1])
    if match:
        return tokens[0], tokens[1]
    return None, None


def parse_last_token(tokens):
    """Parse: <cli> <group> [subgroup...] <action> → return action (last non-flag token)"""
    action = None
    for token in tokens:
        if token.startswith("-"):
            break
        action = token
    return None, action


def parse_first_token(tokens):
    """Parse: <cli> <command> [args] → return action (first non-flag token)"""
    if not tokens or tokens[0].startswith("-"):
        return None, None
    return None, tokens[0]


PARSERS = {
    "aws": parse_aws,
    "first_token": parse_first_token,
    "last_token": parse_last_token,
}


def main():
    input_data = json.load(sys.stdin)
    command = input_data.get("tool_input", {}).get("command", "")

    # Reject chained commands - defer to default permissions
    if any(op in command for op in ("&&", "||", ";", "|")):
        sys.exit(0)

    tokens = command.split()
    if not tokens:
        sys.exit(0)

    cli = tokens[0]

    # Check custom handlers first
    if cli in CUSTOM_CHECKS:
        result = CUSTOM_CHECKS[cli](command, tokens)
        if result:
            print(json.dumps(result))
        sys.exit(0)

    # Resolve aliases
    cli = ALIASES.get(cli, cli)

    if cli not in CONFIGS:
        sys.exit(0)

    config = CONFIGS[cli]
    parser = PARSERS[config["parser"]]
    service, action = parser(tokens[1:])

    if not action:
        sys.exit(0)

    # Check safe actions
    if action in config["safe_actions"]:
        print(json.dumps({"decision": "approve", "reason": f"safe: {action}"}))
        sys.exit(0)

    # Check safe prefixes
    if action.startswith(config["safe_prefixes"]):
        print(json.dumps({"decision": "approve", "reason": f"safe: {action}"}))
        sys.exit(0)

    # Unknown or dangerous - defer
    sys.exit(0)


if __name__ == "__main__":
    main()
