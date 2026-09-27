#!/usr/bin/env python3
"""PreToolUse hook: auto-approve Composio MCP calls that only touch Instagram.

Anything else (other apps, raw proxy calls, connection changes) falls through
to the normal permission prompt.
"""
import json
import re
import sys

READ_ONLY_META = {
    "mcp__Composio__COMPOSIO_SEARCH_TOOLS",
    "mcp__Composio__COMPOSIO_GET_TOOL_SCHEMAS",
}
SLUG_CALL = re.compile(r"""run_composio_tool\(\s*(?:tool_slug\s*=\s*)?["']([A-Z0-9_]+)["']""")


def instagram_only(tool, args):
    if tool in READ_ONLY_META:
        return True
    if tool == "mcp__Composio__COMPOSIO_MULTI_EXECUTE_TOOL":
        slugs = [t.get("tool_slug", "") for t in args.get("tools") or []]
        return bool(slugs) and all(s.startswith("INSTAGRAM_") for s in slugs)
    if tool == "mcp__Composio__COMPOSIO_REMOTE_WORKBENCH":
        code = args.get("code_to_execute", "")
        if "proxy_execute" in code:
            return False
        # Calls through a variable slug can't be verified; leave those to the prompt.
        if code.count("run_composio_tool(") != len(SLUG_CALL.findall(code)):
            return False
        return all(s.startswith("INSTAGRAM_") for s in SLUG_CALL.findall(code))
    if tool == "mcp__Composio__COMPOSIO_MANAGE_CONNECTIONS":
        kits = args.get("toolkits") or []
        return bool(kits) and all(
            k.get("name") == "instagram" and k.get("action", "add") == "list" for k in kits
        )
    return False


def main():
    data = json.load(sys.stdin)
    if instagram_only(data.get("tool_name", ""), data.get("tool_input") or {}):
        print(json.dumps({
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "allow",
                "permissionDecisionReason": "Composio call limited to Instagram (auto-approved)",
            }
        }))


if __name__ == "__main__":
    main()
