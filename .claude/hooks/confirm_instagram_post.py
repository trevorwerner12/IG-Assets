#!/usr/bin/env python3
"""PreToolUse hook: ask before any Composio call that could publish to Instagram.

Everything else from Composio / Google Drive is allowed by settings.json.
"""
import json
import re
import sys

READ_PREFIX = re.compile(r"^INSTAGRAM_(GET|LIST|FETCH|SEARCH|RETRIEVE)", re.I)
PUBLISH_WORDS = re.compile(r"PUBLISH|POST|COMMENT|REPLY|MESSAGE|SEND|DELETE|STORY|REEL", re.I)


def ask(reason):
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "ask",
            "permissionDecisionReason": reason,
        }
    }))
    sys.exit(0)


try:
    data = json.load(sys.stdin)
except Exception:
    sys.exit(0)

tool = data.get("tool_name", "")
inp = data.get("tool_input", {}) or {}

if tool.endswith("COMPOSIO_MULTI_EXECUTE_TOOL"):
    for item in inp.get("tools", []) or []:
        slug = str(item.get("tool_slug", ""))
        if slug.upper().startswith("INSTAGRAM_") and not READ_PREFIX.match(slug) \
                and PUBLISH_WORDS.search(slug):
            ask(f"Instagram action {slug} may post publicly. Approve?")

elif tool.endswith("COMPOSIO_PROXY_EXECUTE"):
    toolkit = str(inp.get("toolkit_slug", "")).lower()
    method = str(inp.get("method", "GET")).upper()
    if toolkit in ("instagram", "facebook") and method not in ("GET", "HEAD"):
        ask(f"Raw {method} to the Instagram API may post publicly. Approve?")

elif tool.endswith(("COMPOSIO_REMOTE_WORKBENCH", "COMPOSIO_REMOTE_BASH_TOOL")):
    if "instagram" in json.dumps(inp).lower():
        ask("Workbench code touches Instagram and may post publicly. Approve?")

sys.exit(0)
