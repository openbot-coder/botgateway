import json
import sys
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def cmd_provider_list(args):
    url = f"{args.server}/admin/providers"
    headers = {"Authorization": f"Bearer {args.token}"} if args.token else {}

    try:
        req = Request(url, headers=headers)
        with urlopen(req) as response:
            data = json.loads(response.read().decode("utf-8"))
            print(json.dumps(data, indent=2, ensure_ascii=False))
    except HTTPError as e:
        print(f"Error: {e.code}", file=sys.stderr)
        sys.exit(1)
    except URLError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_provider_add(args):
    url = f"{args.server}/admin/providers"
    headers = {"Authorization": f"Bearer {args.token}"} if args.token else {}
    headers["Content-Type"] = "application/json"

    body_data = {"name": args.name}
    if args.api_type:
        body_data["api_type"] = args.api_type
    if args.base_url:
        body_data["base_url"] = args.base_url
    if args.api_key:
        body_data["api_key"] = args.api_key

    body = json.dumps(body_data).encode("utf-8")

    try:
        req = Request(url, headers=headers, data=body, method="POST")
        with urlopen(req) as response:
            data = json.loads(response.read().decode("utf-8"))
            print("Provider created successfully!")
            print(json.dumps(data, indent=2, ensure_ascii=False))
    except HTTPError as e:
        print(f"Error: {e.code}", file=sys.stderr)
        sys.exit(1)
    except URLError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_provider_update(args):
    url = f"{args.server}/admin/providers/{args.id}"
    headers = {"Authorization": f"Bearer {args.token}"} if args.token else {}
    headers["Content-Type"] = "application/json"

    update_data = {}
    if args.name:
        update_data["name"] = args.name
    if args.api_type:
        update_data["api_type"] = args.api_type
    if args.base_url:
        update_data["base_url"] = args.base_url
    if args.api_key:
        update_data["api_key"] = args.api_key

    if not update_data:
        print("Error: No update data provided", file=sys.stderr)
        sys.exit(1)

    body = json.dumps(update_data).encode("utf-8")

    try:
        req = Request(url, headers=headers, data=body, method="PUT")
        with urlopen(req) as response:
            data = json.loads(response.read().decode("utf-8"))
            print("Provider updated successfully!")
            print(json.dumps(data, indent=2, ensure_ascii=False))
    except HTTPError as e:
        print(f"Error: {e.code}", file=sys.stderr)
        sys.exit(1)
    except URLError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_provider_delete(args):
    url = f"{args.server}/admin/providers/{args.id}"
    headers = {"Authorization": f"Bearer {args.token}"} if args.token else {}

    try:
        req = Request(url, headers=headers, method="DELETE")
        with urlopen(req):
            print("Provider deleted successfully!")
    except HTTPError as e:
        print(f"Error: {e.code}", file=sys.stderr)
        sys.exit(1)
    except URLError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def register_provider_commands(subparsers):
    parser = subparsers.add_parser("provider", help="Manage providers")
    provider_subparsers = parser.add_subparsers(dest="command", help="Provider commands")

    list_parser = provider_subparsers.add_parser("list", help="List all providers")
    list_parser.set_defaults(func=cmd_provider_list)

    add_parser = provider_subparsers.add_parser("add", help="Create a provider")
    add_parser.add_argument("--name", required=True, help="Provider name")
    add_parser.add_argument("--api-type", default="openai", help="API type (openai/anthropic)")
    add_parser.add_argument("--base-url", help="Base URL")
    add_parser.add_argument("--api-key", help="API key")
    add_parser.set_defaults(func=cmd_provider_add)

    update_parser = provider_subparsers.add_parser("update", help="Update a provider")
    update_parser.add_argument("id", help="Provider ID")
    update_parser.add_argument("--name", help="Provider name")
    update_parser.add_argument("--api-type", help="API type")
    update_parser.add_argument("--base-url", help="Base URL")
    update_parser.add_argument("--api-key", help="API key")
    update_parser.set_defaults(func=cmd_provider_update)

    delete_parser = provider_subparsers.add_parser("delete", help="Delete a provider")
    delete_parser.add_argument("id", help="Provider ID")
    delete_parser.set_defaults(func=cmd_provider_delete)
