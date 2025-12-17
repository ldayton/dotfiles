#!/usr/bin/env python3
"""Test cases for custom-perms-v2.py"""

import json
import subprocess
import sys
from pathlib import Path

# (command, expected_approved_by_hook)
TESTS = [
    # CLI tools - safe
    ("aws s3 ls", True),
    ("aws ec2 describe-instances", True),
    ("git status", True),
    ("git log", True),
    ("kubectl get pods", True),
    ("gh pr list", True),
    ("gh pr view 123 --repo foo/bar", True),
    ("docker ps", True),
    ("brew list", True),

    # CLI tools - unsafe (should defer)
    ("aws s3 rm s3://bucket/key", False),
    ("aws ec2 terminate-instances --instance-ids i-123", False),
    ("git push", False),
    ("git branch -D feature", False),
    ("git stash drop", False),
    ("git config --unset user.name", False),
    ("git tag -d v1.0", False),
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

    # Chained commands - should check ALL commands
    ("aws s3 ls && aws s3 ls", True),  # both safe
    ("aws s3 ls && aws s3 rm foo", False),  # second unsafe
    ("aws s3 rm foo && aws s3 ls", False),  # first unsafe
    ("git status || git push", False),  # second unsafe

    # Pipes - should check ALL commands
    ("git log | grep foo", True),  # both safe (grep handled separately?)
    ("docker ps | grep foo", True),

    # Wrappers - should unwrap and check inner command
    ("time git status", True),
    ("time aws s3 ls", True),
    ("time aws s3 rm foo", False),
    ("nice git log", True),
    ("nice -n 10 git status", True),
    ("timeout 5 kubectl get pods", True),

    # Nested wrappers
    ("time nice git status", True),

    # Complex chains with wrappers
    ("time git status && git log", True),
    ("time git status && git push", False),

    # Simple commands (now handled by hook too)
    ("ls", True),
    ("ls -la", True),
    ("grep foo bar.txt", True),
    ("cat file.txt", True),

    # Simple commands chained
    ("ls && cat foo", True),
    ("ls && rm foo", False),

    # Output redirects - should defer (write to files)
    ("ls > file.txt", False),
    ("cat foo >> bar.txt", False),
    ("ls 2> err.txt", False),
    ("cmd &> all.txt", False),
    ("git log > changes.txt", False),

    # Safe redirects to /dev/null
    ("grep foo bar 2>/dev/null", True),
    ("ls 2>/dev/null", True),
    ("ls &>/dev/null", True),
    ("grep -r pattern /dir 2>/dev/null | head -10", True),

    # Input redirects - safe (read only)
    ("cat < input.txt", True),
    ("grep foo < file.txt", True),

    # Mixed chains with redirects
    ("ls && cat foo > out.txt", False),
    ("cat < in.txt && ls", True),

    # Variable assignment prefix
    ("FOO=BAR ls -l", True),
    ("FOO=BAR rm file", False),

    # Prefix commands
    ("git config --get user.name", True),
    ("git config --list", True),
    ("git stash list", True),
    ("node --version", True),
    ("python --version", True),
    ("pre-commit", True),
    ("pre-commit run", True),
    ("pre-commit run --all-files", True),

    # Prefix commands - unsafe variants
    ("git config user.name foo", False),
    ("git config --unset user.name", False),
    ("git stash pop", False),
    ("git stash drop", False),
    ("node script.js", False),
    ("python script.py", False),

    # Prefix commands in pipelines
    ("git config --get user.name | cat", True),
    ("node --version && ls", True),
    ("python --version | grep 3", True),

    # Prefix commands - partial token matches should NOT match
    ("python --version-info", False),
    ("pre-commit-hook", False),
]


def test_command(cmd, expected_safe):
    """Run custom-perms.py with a command and check result."""
    input_data = json.dumps({"tool_input": {"command": cmd}})

    result = subprocess.run(
        ["uv", "run", "custom-perms.py"],
        input=input_data,
        capture_output=True,
        text=True,
        cwd=Path(__file__).parent,
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
