#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from typing import Any


TOOLS = [
    {
        "name": "validate_business",
        "title": "Validate NTS Business",
        "description": "Return deterministic NTS business validation fixture results.",
        "inputSchema": {"type": "object", "additionalProperties": True},
    },
    {
        "name": "check_business_status",
        "title": "Check NTS Business Status",
        "description": "Return deterministic NTS business status fixture results.",
        "inputSchema": {"type": "object", "additionalProperties": True},
    },
    {
        "name": "batch_validate_businesses",
        "title": "Batch Validate NTS Businesses",
        "description": "Return deterministic NTS batch validation fixture results.",
        "inputSchema": {"type": "object", "additionalProperties": True},
    },
]


RESULTS: dict[str, dict[str, Any]] = {
    "validate_business": {
        "title": "NTS business validate fixture",
        "url": "https://example.test/publicdata/nts-business/validate-fixture",
        "summary": "Fixture-only NTS business validation result for collector normalization.",
        "business_id": "fixture-nts-validate-001",
        "source": "fixture",
    },
    "check_business_status": {
        "title": "NTS business status fixture",
        "url": "https://example.test/publicdata/nts-business/status-fixture",
        "summary": "Fixture-only NTS business status for collector normalization.",
        "business_id": "fixture-nts-status-001",
        "source": "fixture",
    },
    "batch_validate_businesses": {
        "title": "NTS batch validate fixture",
        "url": "https://example.test/publicdata/nts-business/batch-fixture",
        "summary": "Fixture-only NTS batch validation for collector normalization.",
        "business_id": "fixture-nts-batch-001",
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
                "serverInfo": {"name": "fake-koomook-nts-business-verification-mcp", "version": "0.0.0"},
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
