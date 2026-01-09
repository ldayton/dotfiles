#!/usr/bin/env python3
"""Claude Code statusline: model | pwd | git branch"""
import json
import os
import subprocess
import sys
import time

CACHE_DIR = os.path.join(
    os.environ.get("XDG_CACHE_HOME", os.path.expanduser("~/.cache")),
    "claude-statusline",
)
CACHE_TTL = 3
MCP_CACHE_TTL = 10


def get_cache_path(session_id: str) -> str:
    safe_id = session_id.replace("/", "_") if session_id else "default"
    return os.path.join(CACHE_DIR, f"{safe_id}.cache")


def get_cached(session_id: str) -> str | None:
    try:
        path = get_cache_path(session_id)
        if time.time() - os.path.getmtime(path) > CACHE_TTL:
            return None
        with open(path) as f:
            return f.read()
    except Exception:
        return None


def set_cache(session_id: str, output: str):
    try:
        os.makedirs(CACHE_DIR, exist_ok=True)
        path = get_cache_path(session_id)
        tmp = f"{path}.tmp.{os.getpid()}"
        with open(tmp, "w") as f:
            f.write(output)
        os.rename(tmp, path)
    except Exception:
        pass


MCP_CACHE_PATH = os.path.join(CACHE_DIR, "mcp.cache")


def get_mcp_servers() -> str | None:
    """Read cached MCP servers, spawn refresh if stale."""
    try:
        mtime = os.path.getmtime(MCP_CACHE_PATH)
        age = time.time() - mtime
        with open(MCP_CACHE_PATH) as f:
            cached = f.read().strip()
    except Exception:
        age = MCP_CACHE_TTL + 1
        cached = ""
    if age >= MCP_CACHE_TTL:
        try:
            os.makedirs(CACHE_DIR, exist_ok=True)
            tmp = f"{MCP_CACHE_PATH}.tmp.{os.getpid()}"
            cmd = f"timeout 10 claude mcp list 2>/dev/null | awk -F: 'NF>1 {{if (/Connected/) print $1; else print \"!\" $1}}' | paste -sd, | sed 's/,/, /g' > {tmp} && mv {tmp} {MCP_CACHE_PATH}"
            subprocess.Popen(
                cmd,
                shell=True,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
            )
        except Exception:
            pass
    return f"MCP: {cached}" if cached else None


def get_context_from_transcript(transcript_path: str) -> int | None:
    """Read transcript JSONL and get actual context length from most recent message."""
    if not transcript_path:
        return None
    try:
        with open(transcript_path, "rb") as f:
            f.seek(0, 2)
            size = f.tell()
            chunk_size = min(size, 64 * 1024)
            f.seek(max(0, size - chunk_size))
            lines = f.read().decode("utf-8", errors="ignore").strip().split("\n")
        for line in reversed(lines):
            try:
                entry = json.loads(line)
                usage = entry.get("message", {}).get("usage")
                if usage:
                    return (
                        usage.get("input_tokens", 0)
                        + usage.get("cache_read_input_tokens", 0)
                        + usage.get("cache_creation_input_tokens", 0)
                    )
            except json.JSONDecodeError:
                continue
    except Exception:
        pass
    return None


def get_context_remaining(data: dict) -> str | None:
    try:
        ctx = data.get("context_window", {})
        size = ctx.get("context_window_size", 0)
        if not size:
            return None
        used = get_context_from_transcript(data.get("transcript_path", ""))
        if used is None:
            return "ctx: 100% free"
        remaining = max(0, 100 - (used * 100 // size))
        return f"ctx: {remaining}% free"
    except Exception:
        return None


def get_git_changes(cwd: str) -> str | None:
    if not cwd:
        return None
    try:
        result = subprocess.run(
            ["git", "-C", cwd, "diff", "--shortstat", "HEAD"],
            capture_output=True,
            text=True,
            timeout=1,
        )
        if result.returncode != 0:
            return None
        stat = result.stdout.strip()
        if not stat:
            return "clean"
        added = removed = 0
        for part in stat.split(","):
            part = part.strip()
            if "insertion" in part:
                added = int(part.split()[0])
            elif "deletion" in part:
                removed = int(part.split()[0])
        return f"Δ +{added},-{removed}"
    except Exception:
        pass
    return None


def get_git_branch(cwd: str) -> str | None:
    if not cwd:
        return None
    try:
        result = subprocess.run(
            ["git", "-C", cwd, "branch", "--show-current"],
            capture_output=True,
            text=True,
            timeout=1,
        )
        if result.returncode == 0:
            branch = result.stdout.strip()
            if branch:
                return f"⎇ {branch}"
            return "⎇ [detached head]"
    except Exception:
        pass
    return None


def build_statusline(data: dict) -> str:
    model = "?"
    cwd = ""
    try:
        model = data.get("model", {}).get("display_name") or "?"
    except Exception:
        pass
    try:
        cwd = data.get("workspace", {}).get("current_dir") or ""
    except Exception:
        pass
    display_cwd = cwd
    try:
        home = os.path.expanduser("~")
        if cwd.startswith(home):
            display_cwd = "~" + cwd[len(home):]
    except Exception:
        pass
    parts = [model, display_cwd] if display_cwd else [model]
    branch = get_git_branch(cwd)
    if branch:
        parts.append(branch)
    changes = get_git_changes(cwd)
    if changes:
        parts.append(changes)
    ctx_remaining = get_context_remaining(data)
    if ctx_remaining:
        parts.append(ctx_remaining)
    mcp = get_mcp_servers()
    if mcp:
        parts.append(mcp)
    return " | ".join(parts)


def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        data = {}
    session_id = data.get("session_id", "")
    cached = get_cached(session_id)
    if cached:
        print(cached)
        return
    output = build_statusline(data)
    set_cache(session_id, output)
    print(output)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        print("?")
