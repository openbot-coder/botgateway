import argparse
import json
import os
import sys
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from botgateway.cli.commands import (
    register_api_key_commands,
    register_mcp_tool_commands,
    register_model_commands,
    register_model_group_commands,
    register_provider_commands,
)

GLOBAL_FLAGS = {"--server", "-s", "--token", "-t"}
EQUAL_FLAGS = {"--server=", "-s=", "--token=", "-t="}
TWO_ARG_FLAGS = {"--server", "-s", "--token", "-t"}


def _is_global_flag(arg):
    if arg in GLOBAL_FLAGS:
        return True
    return any(arg.startswith(p) for p in EQUAL_FLAGS)


def _reorder_argv(argv):
    """将 --server/-s、--token/-t 移到子命令之前，使全局参数支持后置写法

    支持的写法:
        botcli status -t TOKEN --server URL
        botcli -t TOKEN status --server URL
        botcli -t TOKEN --server URL status
        botcli --server URL status -t TOKEN
    """
    if len(argv) <= 1:
        return argv

    subcmd_idx = None
    i = 1
    while i < len(argv):
        arg = argv[i]
        if _is_global_flag(arg):
            i += 2 if arg in TWO_ARG_FLAGS else 1
            continue
        subcmd_idx = i
        break

    if subcmd_idx is None:
        return argv

    pre_flags = argv[1:subcmd_idx]
    subcmd = argv[subcmd_idx]
    post = argv[subcmd_idx + 1:]

    relocated = []
    remaining = []
    i = 0
    while i < len(post):
        arg = post[i]
        if _is_global_flag(arg):
            relocated.append(arg)
            if arg in TWO_ARG_FLAGS:
                if i + 1 < len(post):
                    relocated.append(post[i + 1])
                    i += 2
                else:
                    i += 1
            else:
                i += 1
            continue
        remaining = post[i:]
        break

    return [argv[0]] + pre_flags + relocated + [subcmd] + remaining


def cmd_health(args):
    url = f"{args.server}/health"
    token = args.token or os.environ.get("BOTGATEWAY_TOKEN")

    if not token:
        print("Error: Token is required", file=sys.stderr)
        sys.exit(1)

    headers = {"Authorization": f"Bearer {token}"}

    try:
        req = Request(url, headers=headers)
        with urlopen(req) as response:
            data = response.read().decode("utf-8")
            print(json.dumps(json.loads(data), indent=2))
    except HTTPError as e:
        if e.code == 404:
            print("Error: Not Found", file=sys.stderr)
        else:
            print(f"Error: {e.code}", file=sys.stderr)
        sys.exit(1)
    except URLError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_status(args):
    url = f"{args.server}/health"
    token = args.token or os.environ.get("BOTGATEWAY_TOKEN")

    if not token:
        print("Error: Token is required", file=sys.stderr)
        sys.exit(1)

    headers = {"Authorization": f"Bearer {token}"}

    try:
        req = Request(url, headers=headers)
        with urlopen(req, timeout=5) as response:
            if response.status == 200:
                data = json.loads(response.read().decode("utf-8"))
                print(f"Status: {data.get('status', 'unknown')}")
                print(f"Server Time: {data.get('server_time', 'unknown')}")
            else:
                print(f"Status: Error ({response.status})")
    except HTTPError as e:
        if e.code == 404:
            print("Status: Not Found", file=sys.stderr)
        else:
            print(f"Status: Error ({e.code})", file=sys.stderr)
        sys.exit(1)
    except URLError as e:
        print(f"Status: Unreachable - {e}", file=sys.stderr)
        sys.exit(1)


def main():
    reordered = _reorder_argv(sys.argv)

    parser = argparse.ArgumentParser(
        prog="botcli",
        description="BotGateway CLI - Manage AI Gateway"
    )

    parser.add_argument(
        "--server", "-s",
        type=str,
        default=os.environ.get("BOTGATEWAY_SERVER", "http://localhost:8000"),
        help="BotGateway server address"
    )

    parser.add_argument(
        "--token", "-t",
        type=str,
        help="Management token (can also be set via BOTGATEWAY_TOKEN env var)"
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    subparsers.add_parser("health", help="Query health status (requires auth)")
    subparsers.add_parser("status", help="Check server status (requires auth)")

    register_api_key_commands(subparsers)
    register_provider_commands(subparsers)
    register_model_commands(subparsers)
    register_model_group_commands(subparsers)
    register_mcp_tool_commands(subparsers)

    args = parser.parse_args(reordered[1:])

    if args.command == "health":
        cmd_health(args)
    elif args.command == "status":
        cmd_status(args)
    elif args.command and hasattr(args, 'func'):
        args.func(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
