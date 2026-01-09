#!/usr/bin/env python3
"""Claude Code statusline: model | pwd | git branch"""
import json
import os
import subprocess
import sys
import time

# Terminal color palette (Molokai)
# Foreground: "#rrggbb"
# Background: ("#fg", "#bg")
MOLOKAI = {
    "black": "#121212",
    "red": "#fa2573",
    "green": "#98e123",
    "yellow": "#dfd460",
    "blue": "#1080d0",
    "magenta": "#8700ff",
    "cyan": "#43a8d0",
    "white": "#bbbbbb",
    "brightBlack": "#555555",
    "brightRed": "#f6669d",
    "brightGreen": "#b1e05f",
    "brightYellow": "#fff26d",
    "brightBlue": "#00afff",
    "brightMagenta": "#af87ff",
    "brightCyan": "#51ceff",
    "brightWhite": "#ffffff",
    "bgBlack": ("#ffffff", "#121212"),
    "bgRed": ("#ffffff", "#fa2573"),
    "bgGreen": ("#000000", "#98e123"),
    "bgYellow": ("#000000", "#dfd460"),
    "bgBlue": ("#ffffff", "#1080d0"),
    "bgMagenta": ("#ffffff", "#8700ff"),
    "bgCyan": ("#ffffff", "#43a8d0"),
    "bgWhite": ("#000000", "#bbbbbb"),
    "bgBrightBlack": ("#ffffff", "#555555"),
    "bgBrightRed": ("#ffffff", "#f6669d"),
    "bgBrightGreen": ("#000000", "#b1e05f"),
    "bgBrightYellow": ("#000000", "#fff26d"),
    "bgBrightBlue": ("#ffffff", "#00afff"),
    "bgBrightMagenta": ("#ffffff", "#af87ff"),
    "bgBrightCyan": ("#ffffff", "#51ceff"),
    "bgBrightWhite": ("#000000", "#ffffff"),
}

# Element styling: element -> condition -> (fg_color, bg_color)
STYLES = {
    "model": ("white", None),
    "directory": ("white", None),
    "branch": ("white", None),
    "branch_detached": ("bgYellow", None),
    "changes_clean": ("white", None),
    "changes_dirty": ("yellow", None),
    "context": ("white", None),
    "mcp_title": ("white", None),
    "mcp_connected": ("green", None),
    "mcp_disconnected": ("red", None),
}


def hex_to_rgb(h: str) -> tuple[int, int, int]:
    """Convert '#rrggbb' to (r, g, b)."""
    h = h.lstrip("#")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def style(text: str, fg_color: str | None, bg_color: str | None = None) -> str:
    """Apply foreground and/or background color to text."""
    if not fg_color and not bg_color:
        return text
    prefix = ""
    color = MOLOKAI.get(fg_color) if fg_color else None
    if color and isinstance(color, tuple):
        # bgX color: ("#fg", "#bg")
        fg_r, fg_g, fg_b = hex_to_rgb(color[0])
        bg_r, bg_g, bg_b = hex_to_rgb(color[1])
        prefix = f"\033[38;2;{fg_r};{fg_g};{fg_b}m\033[48;2;{bg_r};{bg_g};{bg_b}m"
    elif color:
        r, g, b = hex_to_rgb(color)
        prefix = f"\033[38;2;{r};{g};{b}m"
        if bg_color:
            bg_hex = MOLOKAI.get(bg_color)
            if bg_hex and isinstance(bg_hex, str):
                r, g, b = hex_to_rgb(bg_hex)
                prefix += f"\033[48;2;{r};{g};{b}m"
    return f"{prefix}{text}\033[0m"

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
            conn_r, conn_g, conn_b = hex_to_rgb(MOLOKAI[STYLES["mcp_connected"][0]])
            disc_r, disc_g, disc_b = hex_to_rgb(MOLOKAI[STYLES["mcp_disconnected"][0]])
            cmd = f"timeout 10 claude mcp list 2>/dev/null | awk -F: 'NF>1 {{if (/Connected/) print \"\\033[38;2;{conn_r};{conn_g};{conn_b}m\" $1 \"\\033[0m\"; else print \"\\033[38;2;{disc_r};{disc_g};{disc_b}m!\" $1 \"\\033[0m\"}}' | paste -sd, | sed 's/,/, /g' > {tmp} && mv {tmp} {MCP_CACHE_PATH}"
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
    if not cached:
        return None
    fg_c, bg_c = STYLES["mcp_title"]
    title = style("MCP:", fg_c, bg_c)
    return f"{title} {cached}"


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
                        + usage.get("output_tokens", 0)
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
            fg_c, bg_c = STYLES["context"]
            return style("ctx: 80% left", fg_c, bg_c)
        used_pct = used * 100 // size
        until_compact = max(0, 80 - used_pct)
        fg_c, bg_c = STYLES["context"]
        return style(f"ctx: {until_compact}% left", fg_c, bg_c)
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
            fg_c, bg_c = STYLES["changes_clean"]
            return style("clean", fg_c, bg_c)
        added = removed = 0
        for part in stat.split(","):
            part = part.strip()
            if "insertion" in part:
                added = int(part.split()[0])
            elif "deletion" in part:
                removed = int(part.split()[0])
        fg_c, bg_c = STYLES["changes_dirty"]
        return style(f"Δ +{added},-{removed}", fg_c, bg_c)
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
                fg_c, bg_c = STYLES["branch"]
                return style(f"⎇ {branch}", fg_c, bg_c)
            fg_c, bg_c = STYLES["branch_detached"]
            return style("⎇ [detached head]", fg_c, bg_c)
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
    fg_c, bg_c = STYLES["model"]
    model = style(model, fg_c, bg_c)
    display_cwd = os.path.basename(cwd) if cwd else ""
    if display_cwd:
        fg_c, bg_c = STYLES["directory"]
        display_cwd = style(display_cwd, fg_c, bg_c)
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
