import argparse
import json
import os
import sys
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def get_api_key(args):
    api_key = args.api_key or os.environ.get("OPENBOT_API_KEY")
    if not api_key:
        print(
            "Error: API key is required. "
            "Use --api-key or set OPENBOT_API_KEY environment variable",
            file=sys.stderr,
        )
        sys.exit(1)
    return api_key


def cmd_tool_list(args):
    url = f"{args.server}/v1/mcp/tools"
    api_key = get_api_key(args)
    headers = {"Authorization": f"Bearer {api_key}"}

    try:
        req = Request(url, headers=headers)
        with urlopen(req) as response:
            data = json.loads(response.read().decode("utf-8"))
            print(json.dumps(data, indent=2, ensure_ascii=False))
    except HTTPError as e:
        if e.code == 401:
            print("Error: Invalid API key", file=sys.stderr)
        else:
            print(f"Error: {e.code}", file=sys.stderr)
        sys.exit(1)
    except URLError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_tool_call(args):
    url = f"{args.server}/v1/mcp/tools/{args.tool_name}/call"
    api_key = get_api_key(args)
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    tool_args = {}
    if args.arguments:
        try:
            tool_args = json.loads(args.arguments)
        except json.JSONDecodeError as e:
            print(f"Error: Invalid JSON arguments: {e}", file=sys.stderr)
            sys.exit(1)

    body = json.dumps({"arguments": tool_args}).encode("utf-8")

    try:
        req = Request(url, headers=headers, data=body, method="POST")
        with urlopen(req) as response:
            data = json.loads(response.read().decode("utf-8"))
            print(json.dumps(data, indent=2, ensure_ascii=False))
    except HTTPError as e:
        if e.code == 401:
            print("Error: Invalid API key", file=sys.stderr)
        elif e.code == 404:
            print(f"Error: Tool '{args.tool_name}' not found", file=sys.stderr)
        else:
            error_body = e.read().decode("utf-8") if e.read() else ""
            print(f"Error: {e.code} - {error_body}", file=sys.stderr)
        sys.exit(1)
    except URLError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_tool_info(args):
    url = f"{args.server}/v1/mcp/tools/{args.tool_name}"
    api_key = get_api_key(args)
    headers = {"Authorization": f"Bearer {api_key}"}

    try:
        req = Request(url, headers=headers)
        with urlopen(req) as response:
            data = json.loads(response.read().decode("utf-8"))
            print(json.dumps(data, indent=2, ensure_ascii=False))
    except HTTPError as e:
        if e.code == 401:
            print("Error: Invalid API key", file=sys.stderr)
        elif e.code == 404:
            print(f"Error: Tool '{args.tool_name}' not found", file=sys.stderr)
        else:
            print(f"Error: {e.code}", file=sys.stderr)
        sys.exit(1)
    except URLError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        prog="openbot",
        description="OpenBot CLI - Call MCP tools via BotGateway"
    )

    parser.add_argument(
        "--server",
        type=str,
        default=os.environ.get("OPENBOT_SERVER", "http://localhost:8000"),
        help="BotGateway server address"
    )

    parser.add_argument(
        "--api-key",
        type=str,
        help="API key for authentication (can also be set via OPENBOT_API_KEY env var)"
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    tool_parser = subparsers.add_parser("tool", help="MCP tool operations")
    tool_subparsers = tool_parser.add_subparsers(dest="tool_command", help="Tool commands")

    list_parser = tool_subparsers.add_parser("list", help="List available MCP tools")
    list_parser.set_defaults(func=cmd_tool_list)

    info_parser = tool_subparsers.add_parser("info", help="Get info about an MCP tool")
    info_parser.add_argument("tool_name", help="Name of the MCP tool")
    info_parser.set_defaults(func=cmd_tool_info)

    call_parser = tool_subparsers.add_parser("call", help="Call an MCP tool")
    call_parser.add_argument("tool_name", help="Name of the MCP tool")
    call_parser.add_argument("--arguments", "-a", help="Tool arguments as JSON string")
    call_parser.set_defaults(func=cmd_tool_call)

    args = parser.parse_args()

    if hasattr(args, 'func'):
        args.func(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
