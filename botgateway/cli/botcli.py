import argparse
import json
import os
import sys
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError


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
    parser = argparse.ArgumentParser(
        prog="botcli",
        description="管理 BotGateway 服务的命令行工具"
    )
    
    parser.add_argument(
        "--server",
        type=str,
        default="http://localhost:8000",
        help="BotGateway 服务地址"
    )
    
    parser.add_argument(
        "--token",
        type=str,
        help="管理 token（也可通过环境变量 BOTGATEWAY_TOKEN 设置）"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="可用命令")
    
    subparsers.add_parser("health", help="查询健康状态（需要认证）")
    subparsers.add_parser("status", help="检查服务状态（需要认证）")
    
    args = parser.parse_args()
    
    if args.command == "health":
        cmd_health(args)
    elif args.command == "status":
        cmd_status(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()