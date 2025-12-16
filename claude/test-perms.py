#!/usr/bin/env python3
"""Test cases for custom-perms.py"""

import json
import subprocess
import sys

# (command, expected_approved_by_hook)
# Note: simple commands like ls, grep, cat are handled by settings.json, not the hook
TESTS = [
    # CLI tools - safe
    ("aws s3 ls", True),
    ("aws ec2 describe-instances", True),
    ("git status", True),
    ("git log", True),
    ("kubectl get pods", True),
    ("gh pr list", True),
    ("docker ps", True),
    ("brew list", True),

    # CLI tools - unsafe (should defer)
    ("aws s3 rm s3://bucket/key", False),
    ("aws ec2 terminate-instances --instance-ids i-123", False),
    ("git push", False),
    ("kubectl delete pod foo", False),
    ("gh pr create", False),
    ("docker run ubuntu", False),
    ("brew install foo", False),

    # Custom checks
    ("find . -name '*.py'", True),
    ("find . -exec rm {} \\;", False),
    ("find . -delete", False),
    ("sort file.txt", True),
    ("sort -o output.txt file.txt", False),

    # Chained commands (should defer)
    ("ls && rm -rf /", False),
    ("cat file || echo foo", False),
    ("ls; whoami", False),
    ("cat file | grep foo", False),

    # Wrappers (currently not handled - should defer)
    ("time ls", False),
    ("nice grep foo", False),
]


def test_command(cmd, expected_safe):
    """Run custom-perms.py with a command and check result."""
    input_data = json.dumps({"tool_input": {"command": cmd}})

    result = subprocess.run(
        ["python3", "custom-perms.py"],
        input=input_data,
        capture_output=True,
        text=True,
        cwd="/Users/lily/source/dotfiles/claude",
    )

    # If output contains "approve", it's safe
    is_safe = "approve" in result.stdout

    return is_safe == expected_safe


def main():
    passed = 0
    failed = 0

    for cmd, expected_safe in TESTS:
        ok = test_command(cmd, expected_safe)
        status = "✓" if ok else "✗"
        expected = "safe" if expected_safe else "defer"

        if ok:
            passed += 1
        else:
            failed += 1
            print(f"{status} {cmd!r} (expected {expected})")

    print(f"\n{passed} passed, {failed} failed")
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
