#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from typing import Any


TOOLS = [
    {
        "name": "list_speeches",
        "title": "List Presidential Speeches",
        "description": "Return deterministic presidential speech listing fixture results.",
        "inputSchema": {"type": "object", "additionalProperties": True},
    },
    {
        "name": "search_speeches",
        "title": "Search Presidential Speeches",
        "description": "Return deterministic presidential speech search fixture results.",
        "inputSchema": {"type": "object", "additionalProperties": True},
    },
    {
        "name": "get_recent_speeches",
        "title": "Recent Presidential Speeches",
        "description": "Return deterministic recent presidential speech fixture results.",
        "inputSchema": {"type": "object", "additionalProperties": True},
    },
]


SPEECH_RESULTS: dict[str, dict[str, Any]] = {
    "list_speeches": {
        "title": "Presidential speeches list fixture",
        "url": "https://example.test/publicdata/presidential-speeches/list-fixture",
        "summary": "Fixture-only presidential speech listing for collector normalization.",
        "speech_id": "fixture-list-001",
        "source": "fixture",
    },
    "search_speeches": {
        "title": "Presidential speeches search fixture",
        "url": "https://example.test/publicdata/presidential-speeches/search-fixture",
        "summary": "Fixture-only presidential speech search result for collector normalization.",
        "speech_id": "fixture-search-001",
        "source": "fixture",
    },
    "get_recent_speeches": {
        "title": "Presidential speeches recent fixture",
        "url": "https://example.test/publicdata/presidential-speeches/recent-fixture",
        "summary": "Fixture-only recent presidential speech for collector normalization.",
        "speech_id": "fixture-recent-001",
        "source": "fixture",
    },
}


def write_message(payload: dict[str, Any]) -> None:
    sys.stdout.write(json.dumps(payload, ensure_ascii=False) + "\n")
    sys.stdout.flush()


def response_for(message: dict[str, Any]) -> dict[str, Any] | None:
    request_id = message.get("id")
    method = message.get("method")
    if method == "notifications/initialized":
        return None
    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {
                    "name": "fake-koomook-presidential-speeches-mcp",
                    "version": "0.0.0",
                },
            },
        }
    if method == "tools/list":
        return {"jsonrpc": "2.0", "id": request_id, "result": {"tools": TOOLS}}
    if method == "tools/call":
        params = message.get("params") if isinstance(message.get("params"), dict) else {}
        tool_name = params.get("name")
        result = SPEECH_RESULTS.get(tool_name)
        if result is None:
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "isError": True,
                    "content": [{"type": "text", "text": f"Unsupported tool: {tool_name}"}],
                },
            }
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "content": [
                    {"type": "text", "text": json.dumps(result, ensure_ascii=False)}
                ],
                "structuredContent": result,
            },
        }
    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "error": {"code": -32601, "message": f"Unsupported method: {method}"},
    }


def main() -> int:
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            message = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(message, dict):
            continue
        response = response_for(message)
        if response is not None:
            write_message(response)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
