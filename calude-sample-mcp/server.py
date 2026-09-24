#!/usr/bin/env python3
"""
A minimal, dependency-free MCP (Model Context Protocol) server.

Speaks MCP over stdio using newline-delimited JSON-RPC 2.0 messages, so it
works with any MCP client (Claude Code, Claude Desktop, etc.) without
installing the official SDK. Exposes a small set of analytics tools over a
local sample dataset of user accounts (data/accounts.json).

Run directly for manual testing, or point an MCP client at:
    python3 server.py
"""
import json
import sys
from pathlib import Path

DATA_PATH = Path(__file__).resolve().parent / "data" / "accounts.json"

SERVER_NAME = "sample-analytics-mcp"
SERVER_VERSION = "0.1.0"
PROTOCOL_VERSION = "2024-11-05"

FILTERABLE_FIELDS = ("brand", "country", "plan", "status")


def load_accounts():
    with DATA_PATH.open() as f:
        return json.load(f)


def apply_filters(accounts, filters: dict):
    filters = {k: v for k, v in (filters or {}).items() if v}
    result = accounts
    for field, value in filters.items():
        if field not in FILTERABLE_FIELDS:
            continue
        value_lower = str(value).lower()
        result = [a for a in result if str(a.get(field, "")).lower() == value_lower]
    return result


# ---------------------------------------------------------------------------
# Tool implementations
# ---------------------------------------------------------------------------

def tool_count_accounts(args: dict) -> dict:
    accounts = load_accounts()
    matched = apply_filters(accounts, args.get("filters", {}))
    return {"count": len(matched), "filters_applied": args.get("filters", {})}


def tool_list_accounts(args: dict) -> dict:
    accounts = load_accounts()
    matched = apply_filters(accounts, args.get("filters", {}))
    limit = int(args.get("limit", 20))
    limit = max(1, min(limit, 200))
    return {
        "total_matching": len(matched),
        "returned": min(limit, len(matched)),
        "accounts": matched[:limit],
    }


def tool_group_by_stats(args: dict) -> dict:
    group_by = args.get("group_by")
    if group_by not in FILTERABLE_FIELDS:
        raise ValueError(
            f"group_by must be one of {FILTERABLE_FIELDS}, got {group_by!r}"
        )
    accounts = load_accounts()
    matched = apply_filters(accounts, args.get("filters", {}))
    counts: dict = {}
    for a in matched:
        key = a.get(group_by, "unknown")
        counts[key] = counts.get(key, 0) + 1
    ordered = dict(sorted(counts.items(), key=lambda kv: kv[1], reverse=True))
    return {
        "group_by": group_by,
        "total_matching": len(matched),
        "counts": ordered,
    }


def tool_get_account(args: dict) -> dict:
    account_id = args.get("account_id")
    accounts = load_accounts()
    for a in accounts:
        if a.get("id") == account_id:
            return a
    raise ValueError(f"No account found with id {account_id!r}")


TOOLS = {
    "count_accounts": {
        "description": (
            "Count accounts matching optional filters. Use this to answer "
            "questions like 'How many Samsung accounts are there?' "
            "(filters={'brand': 'Samsung'})."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "filters": {
                    "type": "object",
                    "description": "Optional equality filters.",
                    "properties": {
                        "brand": {"type": "string", "description": "e.g. Samsung, Apple, Google, Xiaomi, OnePlus"},
                        "country": {"type": "string", "description": "2-letter country code, e.g. US, IN, KR"},
                        "plan": {"type": "string", "description": "free, premium, or business"},
                        "status": {"type": "string", "description": "active, inactive, or suspended"},
                    },
                    "additionalProperties": False,
                },
            },
        },
        "handler": tool_count_accounts,
    },
    "list_accounts": {
        "description": "List accounts matching optional filters, up to `limit` results.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "filters": {
                    "type": "object",
                    "properties": {
                        "brand": {"type": "string"},
                        "country": {"type": "string"},
                        "plan": {"type": "string"},
                        "status": {"type": "string"},
                    },
                    "additionalProperties": False,
                },
                "limit": {"type": "integer", "description": "Max rows to return (default 20, max 200)"},
            },
        },
        "handler": tool_list_accounts,
    },
    "group_by_stats": {
        "description": (
            "Aggregate account counts grouped by a field (brand, country, plan, "
            "or status), optionally scoped by filters. Use this for questions "
            "like 'break down accounts by brand' or 'accounts per country for "
            "Samsung'."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "group_by": {
                    "type": "string",
                    "enum": list(FILTERABLE_FIELDS),
                },
                "filters": {
                    "type": "object",
                    "properties": {
                        "brand": {"type": "string"},
                        "country": {"type": "string"},
                        "plan": {"type": "string"},
                        "status": {"type": "string"},
                    },
                    "additionalProperties": False,
                },
            },
            "required": ["group_by"],
        },
        "handler": tool_group_by_stats,
    },
    "get_account": {
        "description": "Fetch a single account record by its id.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "account_id": {"type": "string", "description": "e.g. acct_00001"},
            },
            "required": ["account_id"],
        },
        "handler": tool_get_account,
    },
}


# ---------------------------------------------------------------------------
# JSON-RPC / MCP protocol plumbing
# ---------------------------------------------------------------------------

def send(message: dict) -> None:
    sys.stdout.write(json.dumps(message) + "\n")
    sys.stdout.flush()


def make_result(msg_id, result):
    return {"jsonrpc": "2.0", "id": msg_id, "result": result}


def make_error(msg_id, code, message):
    return {"jsonrpc": "2.0", "id": msg_id, "error": {"code": code, "message": message}}


def handle_initialize(msg_id, params):
    send(make_result(msg_id, {
        "protocolVersion": PROTOCOL_VERSION,
        "capabilities": {"tools": {}},
        "serverInfo": {"name": SERVER_NAME, "version": SERVER_VERSION},
    }))


def handle_tools_list(msg_id, params):
    tools = [
        {
            "name": name,
            "description": spec["description"],
            "inputSchema": spec["inputSchema"],
        }
        for name, spec in TOOLS.items()
    ]
    send(make_result(msg_id, {"tools": tools}))


def handle_tools_call(msg_id, params):
    name = params.get("name")
    args = params.get("arguments") or {}
    spec = TOOLS.get(name)
    if spec is None:
        send(make_error(msg_id, -32602, f"Unknown tool: {name}"))
        return
    try:
        result = spec["handler"](args)
        send(make_result(msg_id, {
            "content": [{"type": "text", "text": json.dumps(result, indent=2)}],
            "isError": False,
        }))
    except Exception as exc:  # surfaced to the model as a tool error, not a crash
        send(make_result(msg_id, {
            "content": [{"type": "text", "text": f"Error: {exc}"}],
            "isError": True,
        }))


def handle_ping(msg_id, params):
    send(make_result(msg_id, {}))


METHODS = {
    "initialize": handle_initialize,
    "tools/list": handle_tools_list,
    "tools/call": handle_tools_call,
    "ping": handle_ping,
}


def main():
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except json.JSONDecodeError:
            continue

        method = msg.get("method")
        msg_id = msg.get("id")

        if method == "notifications/initialized":
            continue  # notification, no response expected

        handler = METHODS.get(method)
        if handler is None:
            if msg_id is not None:
                send(make_error(msg_id, -32601, f"Method not found: {method}"))
            continue

        handler(msg_id, msg.get("params") or {})


if __name__ == "__main__":
    main()
