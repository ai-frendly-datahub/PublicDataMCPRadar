#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from typing import Any


TOOLS = [
    {"name": "search_chemicals", "title": "Search Chemicals", "description": "Return deterministic chemical search fixture results.", "inputSchema": {"type": "object", "additionalProperties": True}},
    {"name": "get_chemical_safety_summary", "title": "Get Chemical Safety Summary", "description": "Return deterministic chemical safety summary fixture results.", "inputSchema": {"type": "object", "additionalProperties": True}},
    {"name": "get_chemical_handling_info", "title": "Get Chemical Handling Info", "description": "Return deterministic chemical handling fixture results.", "inputSchema": {"type": "object", "additionalProperties": True}},
    {"name": "get_chemical_properties", "title": "Get Chemical Properties", "description": "Return deterministic chemical properties fixture results.", "inputSchema": {"type": "object", "additionalProperties": True}},
    {"name": "get_chemical_regulatory_info", "title": "Get Chemical Regulatory Info", "description": "Return deterministic chemical regulatory fixture results.", "inputSchema": {"type": "object", "additionalProperties": True}},
    {"name": "get_chemical_section", "title": "Get Chemical Section", "description": "Return deterministic chemical section fixture results.", "inputSchema": {"type": "object", "additionalProperties": True}},
    {"name": "get_complete_msds", "title": "Get Complete MSDS", "description": "Return deterministic complete MSDS fixture results.", "inputSchema": {"type": "object", "additionalProperties": True}},
]


def _make_result(tool: str) -> dict[str, Any]:
    slug = tool.replace("_", "-")
    return {
        "title": f"MSDS {slug} fixture",
        "url": f"https://example.test/publicdata/msds-chemical/{slug}-fixture",
        "summary": f"Fixture-only MSDS {slug} result for collector normalization.",
        "chemical_id": f"fixture-msds-{slug}",
        "source": "fixture",
    }


RESULTS: dict[str, dict[str, Any]] = {tool["name"]: _make_result(tool["name"]) for tool in TOOLS}


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
                "serverInfo": {"name": "fake-koomook-msds-chemical-info-mcp", "version": "0.0.0"},
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
