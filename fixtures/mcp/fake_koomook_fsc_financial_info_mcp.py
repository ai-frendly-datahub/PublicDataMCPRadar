#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from typing import Any


TOOLS = [
    {
        "name": "get_summary_financial_statement",
        "title": "Get FSC Summary Financial Statement",
        "description": "Return deterministic FSC summary financial statement fixture results.",
        "inputSchema": {"type": "object", "additionalProperties": True},
    },
    {
        "name": "get_balance_sheet",
        "title": "Get FSC Balance Sheet",
        "description": "Return deterministic FSC balance sheet fixture results.",
        "inputSchema": {"type": "object", "additionalProperties": True},
    },
    {
        "name": "get_income_statement",
        "title": "Get FSC Income Statement",
        "description": "Return deterministic FSC income statement fixture results.",
        "inputSchema": {"type": "object", "additionalProperties": True},
    },
    {
        "name": "search_company_financial_info",
        "title": "Search FSC Company Financial Info",
        "description": "Return deterministic FSC company financial info fixture results.",
        "inputSchema": {"type": "object", "additionalProperties": True},
    },
]


RESULTS: dict[str, dict[str, Any]] = {
    "get_summary_financial_statement": {
        "title": "FSC summary statement fixture",
        "url": "https://example.test/publicdata/fsc-financial/summary-fixture",
        "summary": "Fixture-only FSC summary financial statement for collector normalization.",
        "company_id": "fixture-fsc-summary-001",
        "source": "fixture",
    },
    "get_balance_sheet": {
        "title": "FSC balance sheet fixture",
        "url": "https://example.test/publicdata/fsc-financial/balance-fixture",
        "summary": "Fixture-only FSC balance sheet for collector normalization.",
        "company_id": "fixture-fsc-balance-001",
        "source": "fixture",
    },
    "get_income_statement": {
        "title": "FSC income statement fixture",
        "url": "https://example.test/publicdata/fsc-financial/income-fixture",
        "summary": "Fixture-only FSC income statement for collector normalization.",
        "company_id": "fixture-fsc-income-001",
        "source": "fixture",
    },
    "search_company_financial_info": {
        "title": "FSC company search fixture",
        "url": "https://example.test/publicdata/fsc-financial/search-fixture",
        "summary": "Fixture-only FSC company financial search for collector normalization.",
        "company_id": "fixture-fsc-search-001",
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
                "serverInfo": {"name": "fake-koomook-fsc-financial-info-mcp", "version": "0.0.0"},
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
