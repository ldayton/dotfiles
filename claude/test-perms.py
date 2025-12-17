#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "bashlex",
# ]
# ///
"""Test cases for custom-perms.py"""

import sys

# Import the module directly
import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "custom_perms", Path(__file__).parent / "custom-perms.py"
)
custom_perms = importlib.util.module_from_spec(spec)
spec.loader.exec_module(custom_perms)

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
    ("sed 's/foo/bar/' file.txt", True),
    ("sed -n '1,10p' file.txt", True),
    ("sed -i 's/foo/bar/' file.txt", False),
    ("sed -i.bak 's/foo/bar/' file.txt", False),
    ("sed --in-place 's/foo/bar/' file.txt", False),
    ("awk '{print $1}' file.txt", True),
    ("awk -F: '{print $1}' /etc/passwd", True),
    ("awk -f script.awk file.txt", False),
    ("awk '{print > \"out.txt\"}' file.txt", False),
    ("awk '{system(\"rm file\")}'", False),

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

    # uv run wrapper
    ("uv run cdk synth", True),
    ("uv run cdk synth --quiet", True),
    ("uv run --quiet cdk diff", True),
    ("uv run cdk deploy", False),
    ("uv run rm foo", False),
    ("uv sync", False),  # not 'uv run', don't unwrap

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

    # fd redirects (2>&1 style) - safe
    ("ls 2>&1", True),
    ("uv run cdk synth 2>&1 | head -10", True),

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

    # Git with -C flag
    ("git -C /some/path status", True),
    ("git -C /some/path log --oneline -5", True),
    ("git -C /tmp push --force", False),
    ("git --git-dir=/some/.git status", True),
    ("git -c core.editor=vim log", True),
]


def test_command(cmd, expected_safe):
    """Test a command directly using the module's functions."""
    commands = custom_perms.parse_commands(cmd)
    if commands is None:
        is_safe = False
    elif not commands:
        is_safe = False
    else:
        is_safe = all(custom_perms.is_command_safe(tokens) for tokens in commands)
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
