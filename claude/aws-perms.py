#!/usr/bin/env python3
"""Hook to auto-approve read-only AWS CLI commands."""

import json
import re
import sys

SAFE_PREFIXES = (
    "describe-",
    "get-",
    "head-",
    "list-",
)

SAFE_COMMANDS = {
    ("s3", "ls"),
}


def main():
    input_data = json.load(sys.stdin)
    command = input_data.get("tool_input", {}).get("command", "")

    # Not an aws command - defer to default permissions
    if not command.startswith("aws "):
        sys.exit(0)

    # Parse: aws <service> <action> ...
    match = re.match(r"^aws\s+([\w-]+)\s+([\w-]+)", command)
    if not match:
        # Can't parse - defer to default permissions
        sys.exit(0)

    service = match.group(1)
    action = match.group(2)

    # Check special safe commands
    if (service, action) in SAFE_COMMANDS:
        print(json.dumps({"decision": "approve", "reason": f"safe: {service} {action}"}))
        sys.exit(0)

    # Known safe - approve
    if action.startswith(SAFE_PREFIXES):
        print(json.dumps({"decision": "approve", "reason": f"safe: {action}"}))
        sys.exit(0)

    # Known dangerous or unknown - defer to default permissions
    sys.exit(0)


if __name__ == "__main__":
    main()
