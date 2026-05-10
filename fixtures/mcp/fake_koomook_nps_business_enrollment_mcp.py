#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from typing import Any


TOOLS = [
    {
        "name": "search_business",
        "title": "Search NPS Business",
        "description": "Return deterministic NPS business search fixture results.",
        "inputSchema": {"type": "object", "additionalProperties": True},
    },
    {
        "name": "get_business_detail",
        "title": "Get NPS Business Detail",
        "description": "Return deterministic NPS business detail fixture results.",
        "inputSchema": {"type": "object", "additionalProperties": True},
    },
    {
        "name": "get_period_status",
        "title": "Get NPS Period Status",
        "description": "Return deterministic NPS period status fixture results.",
        "inputSchema": {"type": "object", "additionalProperties": True},
    },
]


RESULTS: dict[str, dict[str, Any]] = {
    "search_business": {
        "title": "NPS business search fixture",
        "url": "https://example.test/publicdata/nps-business/search-fixture",
        "summary": "Fixture-only NPS business search result for collector normalization.",
        "business_id": "fixture-nps-search-001",
        "source": "fixture",
    },
    "get_business_detail": {
        "title": "NPS business detail fixture",
        "url": "https://example.test/publicdata/nps-business/detail-fixture",
        "summary": "Fixture-only NPS business detail for collector normalization.",
        "business_id": "fixture-nps-detail-001",
        "source": "fixture",
    },
    "get_period_status": {
        "title": "NPS period status fixture",
        "url": "https://example.test/publicdata/nps-business/period-fixture",
        "summary": "Fixture-only NPS period status for collector normalization.",
        "business_id": "fixture-nps-period-001",
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
                "serverInfo": {"name": "fake-koomook-nps-business-enrollment-mcp", "version": "0.0.0"},
            },
        }
    if method == "tools/list":
        return {"jsonrpc": "2.0", "id": request_id, "result": {"tools": TOOLS}}
    if method == "tools/call":
        params = message.get("params") if isinstance(message.get("params"), dict) else {}
        tool_name = params.get("name")
        result = RESULTS.get(tool_name)
        if result is None:
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {"isError": True, "content": [{"type": "text", "text": f"Unsupported tool: {tool_name}"}]},
            }
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "content": [{"type": "text", "text": json.dumps(result, ensure_ascii=False)}],
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
