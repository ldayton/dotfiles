#!/usr/bin/env -S uv run
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
    ("aws --profile prod ec2 describe-instances", True),
    ("aws --region us-east-1 ec2 describe-instances", True),
    ("aws --output json s3 ls", True),
    ("aws --profile prod --region us-west-2 lambda list-functions", True),
    ("aws --endpoint-url http://localhost:4566 s3 ls", True),
    ("aws --no-cli-pager ec2 describe-instances", True),
    ("aws logs filter-log-events --log-group-name test", True),
    ("aws cloudtrail lookup-events", True),
    ("aws dynamodb batch-get-item --request-items file://items.json", True),
    ("git status", True),
    ("git log", True),
    ("kubectl get pods", True),
    ("gh pr list", True),
    ("gh pr view 123 --repo foo/bar", True),
    ("gh --repo foo/bar pr list", True),
    ("gh -R foo/bar pr view 123", True),
    ("docker ps", True),
    ("docker --host tcp://localhost:2375 ps", True),
    ("docker -H unix:///var/run/docker.sock images", True),
    ("brew list", True),

    # CLI tools - unsafe (should defer)
    ("aws s3 rm s3://bucket/key", False),
    ("aws ec2 terminate-instances --instance-ids i-123", False),
    ("aws --profile prod ec2 terminate-instances --instance-ids i-123", False),
    ("aws --region us-east-1 s3 rm s3://bucket/file", False),
    ("git push", False),
    ("git branch -D feature", False),
    ("git stash drop", False),
    ("git config --unset user.name", False),
    ("git tag -d v1.0", False),
    ("kubectl delete pod foo", False),
    ("gh pr create", False),
    ("gh -R foo/bar pr create", False),
    ("docker run ubuntu", False),
    ("docker --host tcp://localhost run ubuntu", False),
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

    # Curl - safe (GET/HEAD only)
    ("curl https://example.com", True),
    ("curl -I https://example.com", True),
    ("curl --head https://example.com", True),
    ("curl -X GET https://example.com", True),
    ("curl -X HEAD https://example.com", True),
    ("curl -X OPTIONS https://example.com", True),
    ("curl -X TRACE https://example.com", True),
    ("curl -s -o /dev/null -w '%{http_code}' https://example.com", True),

    # Curl - unsafe (POST/PUT/DELETE or data-sending)
    ("curl -X POST https://example.com", False),
    ("curl -X PUT https://example.com", False),
    ("curl -X DELETE https://example.com", False),
    ("curl --request=DELETE https://example.com", False),
    ("curl -d 'data' https://example.com", False),
    ("curl --data='foo=bar' https://example.com", False),
    ("curl -F 'file=@test.txt' https://example.com", False),
    ("curl --form 'file=@test.txt' https://example.com", False),
    ("curl -T file.txt ftp://example.com", False),
    ("curl --upload-file file.txt ftp://example.com", False),

    # Curl wrappers (scripts that wrap curl)
    ("grafana.sh query foo", True),
    ("/path/to/prometheus.sh get metrics", True),
    ("pushgateway.sh --help", True),
    ("grafana.sh -X POST data", False),
    ("prometheus.sh -d 'data' https://example.com", False),
    ("pushgateway.sh --data=foo", False),

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

    # Scripts with paths (basename matching)
    ("./test-perms.py", True),
    ("/path/to/test-perms.py", True),
    ("./unknown-script.py", False),

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

    # --help makes any command safe
    ("gh api --help", True),
    ("gh api repos --help", True),
    ("aws s3 rm --help", True),
    ("kubectl delete --help", True),
    ("docker run --help", True),
    ("git push --help", True),
    ("unknown-command --help", True),
    ("./mystery-script.sh --help", True),

    # gh api - safe (GET requests)
    ("gh api repos/owner/repo", True),
    ("gh api repos/{owner}/{repo}/pulls", True),
    ("gh api /user", True),
    ("gh api -X GET repos/owner/repo", True),
    ("gh api --method GET repos/owner/repo", True),
    ("gh api --method=GET repos/owner/repo", True),
    ("gh api -XGET repos/owner/repo", True),
    ("gh api -X GET search/issues -f q='repo:cli/cli'", True),  # -f ok with explicit GET
    ("gh api -f q='repo:cli/cli' -X GET search/issues", True),  # -X GET after -f is still safe
    ("gh api --paginate repos/owner/repo/issues", True),
    ("gh api -q '.[] | .name' repos/owner/repo", True),

    # gh api - unsafe (mutations)
    ("gh api repos/owner/repo --raw-field=foo=bar", False),  # --flag=value form
    ("gh api repos/owner/repo --field=foo=bar", False),
    ("gh api repos/owner/repo/issues -f title='bug'", False),  # -f implies POST
    ("gh api repos/owner/repo/issues -F body=@file.txt", False),  # -F implies POST
    ("gh api repos/owner/repo/issues --field title=bug", False),
    ("gh api -X POST repos/owner/repo/issues", False),
    ("gh api -X DELETE repos/owner/repo/issues/1", False),
    ("gh api --method POST repos/owner/repo/hooks", False),
    ("gh api --method=PATCH repos/owner/repo", False),
    ("gh api -XPOST repos/owner/repo/issues", False),
    ("gh api repos/owner/repo --input payload.json", False),
    ("gh api graphql -f query='mutation { ... }'", False),

    # Git with -C flag
    ("git -C /some/path status", True),
    ("git -C /some/path log --oneline -5", True),
    ("git -C /tmp push --force", False),
    ("git --git-dir=/some/.git status", True),
    ("git -c core.editor=vim log", True),

    # Gcloud with global flags (values could match action names)
    ("gcloud --project delete compute instances list", True),
    ("gcloud --format delete compute instances list", True),
    ("gcloud --project myproj compute instances delete foo", False),

    # Gcloud with --flag value patterns
    ("gcloud compute instances list", True),
    ("gcloud compute instances list --project foo", True),
    ("gcloud compute backend-services describe k8s-be --global --project foo", True),
    ("gcloud iap settings get --project foo --resource-type=compute", True),
    ("gcloud auth list", True),
    ("gcloud compute instances delete foo", False),
    ("gcloud compute instances delete list", False),  # deleting instance named "list"
    ("gcloud compute instances create foo", False),
    ("gcloud container clusters get-credentials foo", True),  # get- prefix

    # Az with global flags (values could match action names)
    ("az --subscription delete vm list", True),
    ("az --query delete vm show", True),
    ("az -o delete vm list", True),
    ("az --subscription mysub vm delete foo", False),

    # Az with positional args before flags
    ("az vm list --resource-group mygroup", True),
    ("az vm show myvm --resource-group mygroup", True),
    ("az storage account list", True),
    ("az keyvault secret show --name mysecret --vault-name myvault", True),
    ("az vm delete myvm --resource-group mygroup", False),
    ("az vm delete list", False),  # deleting vm named "list"
    ("az vm create myvm --resource-group mygroup", False),
    ("az vm start myvm", False),

    # Kubectl with global flags (values could match action names)
    ("kubectl --context delete get pods", True),
    ("kubectl -n delete get pods", True),
    ("kubectl --namespace exec get pods", True),
    ("kubectl --context mycluster delete pod foo", False),

    # Kubectl with flags before action
    ("kubectl --context=foo get pods", True),
    ("kubectl --context=foo get managedcertificate ci-api -o jsonpath='{}'", True),
    ("kubectl -n kube-system describe pod foo", True),
    ("kubectl delete pod foo", False),
    ("kubectl --context=foo delete pod list", False),  # deleting pod named "list"
    ("kubectl apply -f foo.yaml", False),
    ("kubectl exec -it foo -- bash", False),

    # Openssl x509 with -noout (read-only)
    ("openssl x509 -noout -text", True),
    ("openssl x509 -noout -text -in cert.pem", True),
    ("openssl x509 -noout -subject -issuer", True),
    ("openssl x509 -text", False),  # no -noout, could write encoded output
    ("openssl x509 -in cert.pem -out cert.der", False),
    ("openssl req -new -key key.pem", False),

    # Network diagnostic tools with checks
    ("ip addr", True),
    ("ip addr show", True),
    ("ip route", True),
    ("ip link show", True),
    ("ip -4 addr show", True),
    ("ip addr add 192.168.1.1/24 dev eth0", False),
    ("ip link set eth0 up", False),
    ("ip route del default", False),
    ("ip netns exec myns ip addr", False),  # runs commands in namespace
    ("ifconfig", True),
    ("ifconfig eth0", True),
    ("ifconfig eth0 up", False),
    ("ifconfig eth0 down", False),
    ("ifconfig eth0 192.168.1.1", True),  # viewing, not setting without netmask
    ("ifconfig eth0 192.168.1.1 netmask 255.255.255.0", False),
    ("journalctl", True),
    ("journalctl -f", True),
    ("journalctl -u sshd", True),
    ("journalctl --rotate", False),
    ("journalctl --vacuum-time=1d", False),
    ("journalctl --flush", False),
    ("dmesg", True),
    ("dmesg -T", True),
    ("dmesg -c", False),
    ("dmesg --clear", False),
    ("ping google.com", True),
    ("ping -c 4 google.com", True),
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
