#!/usr/bin/env python3
"""Minimal LangChain test agent for a streamable HTTP MCP server.

Purpose
-------
Connect to your MCP server over streamable HTTP, load only the tools you want
(`web_search` and `current_time` by default), and run a simple prompt so you can
confirm the agent can reach and use the server.

Install
-------
pip install -U langchain langchain-openai langchain-mcp-adapters

Env
---
export OPENAI_API_KEY="your-openai-key"

Run
---
python mcp_test_agent.py \
  --server-url "http://localhost:8000/mcp" \
  --auth-token "your-server-token"

Optional
--------
python mcp_test_agent.py \
  --server-url "http://localhost:8000/mcp" \
  --auth-token "your-server-token" \
  --model "openai:gpt-5" \
  --tools web_search current_time \
  --prompt "Search for the latest news about MCP and tell me the current UTC time."
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from src.config.settings import settings
from langchain.agents import create_agent
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_google_genai import ChatGoogleGenerativeAI

DEFAULT_MODEL = "gemini-2.5-flash"
DEFAULT_TOOLS = ["search_web", "get_current_time"]
DEFAULT_PROMPT = (
    "Use the available tools to do two things: "
    "1) search the web for a very recent AI engineering headline, and "
    "2) check the current time in UTC. "
    "Then return a short answer showing both results and mention which tools you used."
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Simple LangChain MCP test agent for a streamable HTTP server."
    )
    parser.add_argument(
        "--token-prefix",
        default="Bearer",
        help='Prefix for Authorization header. Use "Bearer" for Bearer <token>, or "" for raw token.',
    )
    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help=f"LangChain model id (default: {DEFAULT_MODEL})",
    )
    parser.add_argument(
        "--tools",
        nargs="+",
        default=DEFAULT_TOOLS,
        help="Tool names to keep from the MCP server (default: web_search current_time)",
    )
    parser.add_argument(
        "--prompt",
        default=DEFAULT_PROMPT,
        help="Prompt to send to the agent.",
    )
    parser.add_argument(
        "--show-all-tools",
        action="store_true",
        help="Print all tools exposed by the server before filtering.",
    )
    return parser.parse_args()


def build_headers(token: str, token_prefix: str) -> dict[str, str]:
    headers: dict[str, str] = {}

    if token:
        if token_prefix:
            headers["Authorization"] = f"{token_prefix.strip()} {token}".strip()
        else:
            headers["Authorization"] = token

    return headers


def normalize_tool_name(tool) -> str:
    return getattr(tool, "name", str(tool))


async def main() -> int:
    args = parse_args()

    if not settings.GEMINI_API_KEY:
        print("ERROR: API_KEY is not set.", file=sys.stderr)
        return 1
        
    llm = ChatGoogleGenerativeAI(model=DEFAULT_MODEL, api_key=settings.GEMINI_API_KEY)

    wanted_tools = set(args.tools)
    headers = build_headers("a3f8c2d1e4b5a6f7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1", args.token_prefix)

    print("=" * 80)
    print("MCP test agent starting")
    print(f"Server URL : https://mcp-test-1v7t.onrender.com/mcp")
    print(f"Model      : {args.model}")
    print(f"Want tools : {sorted(wanted_tools)}")
    print(
        f"Headers    : {json.dumps({k: ('***' if k.lower() == 'authorization' else v) for k, v in headers.items()})}"
    )
    print("=" * 80)

    client = MultiServerMCPClient(
        {
            "test_server": {
                "transport": "http",
                "url": "https://mcp-test-1v7t.onrender.com/mcp",
                "headers": headers,
            }
        }
    )

    try:
        server_tools = await client.get_tools()
    except Exception as exc:
        print(f"Failed to connect to MCP server or load tools: {exc}", file=sys.stderr)
        return 2

    available_tool_names = [normalize_tool_name(tool) for tool in server_tools]

    if args.show_all_tools:
        print("Server exposed tools:")
        for name in available_tool_names:
            print(f"  - {name}")
        print("-" * 80)

    filtered_tools = [tool for tool in server_tools if normalize_tool_name(tool) in wanted_tools]
    filtered_tool_names = [normalize_tool_name(tool) for tool in filtered_tools]

    if not filtered_tools:
        print(
            "No matching tools were loaded after filtering.\n"
            f"Requested: {sorted(wanted_tools)}\n"
            f"Available: {available_tool_names}",
            file=sys.stderr,
        )
        return 3

    missing_tools = sorted(wanted_tools - set(filtered_tool_names))
    if missing_tools:
        print(f"Warning: these requested tools were not found on the server: {missing_tools}")

    print(f"Loaded tools for agent: {filtered_tool_names}")
    print("-" * 80)

    agent = create_agent(
        model= llm,
        tools=filtered_tools,
        system_prompt=("""uv 
                       You are a small MCP server test agent. 
                       Use the available MCP tools whenever they are relevant. 
                       Be concise and clearly mention the tools you used."""
        ),
    )

    try:
        result = await agent.ainvoke(
            {
                "messages": [
                    {
                        "role": "user",
                        "content": args.prompt,
                    }
                ]
            }
        )
    except Exception as exc:
        print(f"Agent execution failed: {exc}", file=sys.stderr)
        return 4

    print("Agent run completed")
    print("=" * 80)

    messages = result.get("messages", [])
    for message in messages:
        msg_type = getattr(message, "type", message.__class__.__name__)
        name = getattr(message, "name", None)
        content = getattr(message, "content", None)

        if msg_type == "tool":
            print(f"[TOOL] {name}")
            print(content)
            print("-" * 80)
        elif msg_type == "ai":
            print("[FINAL ANSWER]")
            print(content)
            print("-" * 80)

    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
