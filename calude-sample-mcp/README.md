# calude-sample-mcp

A minimal, local sample MCP (Model Context Protocol) server that answers
generic analytics questions over a synthetic dataset of user accounts
(e.g. "How many Samsung accounts are there?").

No Node.js and no third-party packages required — it's a single
dependency-free Python script (stdlib only) that speaks MCP over stdio.

## Contents

- `data/accounts.json` — 1,200 synthetic accounts across brands (Samsung,
  Apple, Google, Xiaomi, OnePlus), each with `id`, `name`, `email`, `brand`,
  `country`, `plan`, `status`, `created_at`.
- `scripts/generate_data.py` — regenerates `data/accounts.json` (seeded, so
  output is reproducible).
- `server.py` — the MCP server itself.
- `scripts/test_client.py` — a tiny standalone MCP client that spawns
  `server.py` and exercises every tool, for smoke-testing without a real
  MCP host.

## Tools exposed

| Tool | Purpose |
|---|---|
| `count_accounts` | Count accounts matching optional filters (`brand`, `country`, `plan`, `status`). Answers "How many Samsung accounts are there?" |
| `list_accounts` | List up to `limit` accounts matching optional filters. |
| `group_by_stats` | Group counts by `brand`, `country`, `plan`, or `status`, optionally scoped by filters. Answers "break down accounts by brand". |
| `get_account` | Fetch one account by `id`. |

## Try it standalone

```bash
python3 scripts/test_client.py
```

This spawns the server and runs a handful of sample questions end-to-end,
including "How many Samsung accounts are there?".

## Use it as a real MCP server

Register it with Claude Code:

```bash
claude mcp add sample-analytics -- python3 /Users/adityakiran/Developer/github/data-akiran/calude-sample-mcp/server.py
```

Or add it manually to an MCP client config (e.g. Claude Desktop's
`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "sample-analytics": {
      "command": "python3",
      "args": [
        "/Users/adityakiran/Developer/github/data-akiran/calude-sample-mcp/server.py"
      ]
    }
  }
}
```

Then ask things like:
- "How many Samsung accounts are there?"
- "Break down accounts by plan"
- "List 5 suspended accounts in India"

## Regenerate the dataset

```bash
python3 scripts/generate_data.py
```

## Extending

Add a new tool by writing a handler function in `server.py` and adding an
entry to the `TOOLS` dict with its `description` and `inputSchema` — the
JSON-RPC plumbing (`initialize`, `tools/list`, `tools/call`) is generic and
needs no changes.
