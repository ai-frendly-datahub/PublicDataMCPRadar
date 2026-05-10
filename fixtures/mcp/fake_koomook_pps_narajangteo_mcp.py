#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from typing import Any


TOOLS = [
    {
        "name": "search_bid_announcements",
        "title": "Search PPS Bid Announcements",
        "description": "Return deterministic PPS bid announcement fixture results.",
        "inputSchema": {"type": "object", "additionalProperties": True},
    },
    {
        "name": "search_successful_bids",
        "title": "Search PPS Successful Bids",
        "description": "Return deterministic PPS successful bid fixture results.",
        "inputSchema": {"type": "object", "additionalProperties": True},
    },
    {
        "name": "search_contracts",
        "title": "Search PPS Contracts",
        "description": "Return deterministic PPS contract fixture results.",
        "inputSchema": {"type": "object", "additionalProperties": True},
    },
    {
        "name": "get_bid_detail",
        "title": "Get PPS Bid Detail",
        "description": "Return deterministic PPS bid detail fixture results.",
        "inputSchema": {"type": "object", "additionalProperties": True},
    },
]


RESULTS: dict[str, dict[str, Any]] = {
    "search_bid_announcements": {
        "title": "PPS bid announcements fixture",
        "url": "https://example.test/publicdata/pps-narajangteo/announcements-fixture",
        "summary": "Fixture-only PPS bid announcements for collector normalization.",
        "bid_id": "fixture-pps-announce-001",
        "source": "fixture",
    },
    "search_successful_bids": {
        "title": "PPS successful bids fixture",
        "url": "https://example.test/publicdata/pps-narajangteo/successful-fixture",
        "summary": "Fixture-only PPS successful bids for collector normalization.",
        "bid_id": "fixture-pps-success-001",
        "source": "fixture",
    },
    "search_contracts": {
        "title": "PPS contracts fixture",
        "url": "https://example.test/publicdata/pps-narajangteo/contracts-fixture",
        "summary": "Fixture-only PPS contracts for collector normalization.",
        "bid_id": "fixture-pps-contract-001",
        "source": "fixture",
    },
    "get_bid_detail": {
        "title": "PPS bid detail fixture",
        "url": "https://example.test/publicdata/pps-narajangteo/detail-fixture",
        "summary": "Fixture-only PPS bid detail for collector normalization.",
        "bid_id": "fixture-pps-detail-001",
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
                "serverInfo": {"name": "fake-koomook-pps-narajangteo-mcp", "version": "0.0.0"},
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
