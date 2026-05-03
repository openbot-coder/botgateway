import json
import sys
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def cmd_api_key_list(args):
    url = f"{args.server}/admin/api-keys"
    headers = {"Authorization": f"Bearer {args.token}"} if args.token else {}

    try:
        req = Request(url, headers=headers)
        with urlopen(req) as response:
            data = json.loads(response.read().decode("utf-8"))
            print(json.dumps(data, indent=2, ensure_ascii=False))
    except HTTPError as e:
        print(f"Error: {e.code}", file=sys.stderr)
        if e.code == 401:
            print("Authentication required", file=sys.stderr)
        sys.exit(1)
    except URLError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_api_key_create(args):
    url = f"{args.server}/admin/api-keys"
    headers = {"Authorization": f"Bearer {args.token}"} if args.token else {}
    headers["Content-Type"] = "application/json"

    body = json.dumps({"name": args.name}).encode("utf-8")

    try:
        req = Request(url, headers=headers, data=body, method="POST")
        with urlopen(req) as response:
            data = json.loads(response.read().decode("utf-8"))
            print("API Key created successfully!")
            print(f"ID: {data['id']}")
            print(f"Name: {data['name']}")
            print(f"API Key: {data['api_key']}")
            print(f"\n{data['message']}")
    except HTTPError as e:
        print(f"Error: {e.code}", file=sys.stderr)
        sys.exit(1)
    except URLError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_api_key_update(args):
    url = f"{args.server}/admin/api-keys/{args.id}"
    headers = {"Authorization": f"Bearer {args.token}"} if args.token else {}
    headers["Content-Type"] = "application/json"

    update_data = {}
    if args.name:
        update_data["name"] = args.name

    if not update_data:
        print("Error: No update data provided", file=sys.stderr)
        sys.exit(1)

    body = json.dumps(update_data).encode("utf-8")

    try:
        req = Request(url, headers=headers, data=body, method="PUT")
        with urlopen(req) as response:
            data = json.loads(response.read().decode("utf-8"))
            print("API Key updated successfully!")
            print(json.dumps(data, indent=2, ensure_ascii=False))
    except HTTPError as e:
        print(f"Error: {e.code}", file=sys.stderr)
        sys.exit(1)
    except URLError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_api_key_delete(args):
    url = f"{args.server}/admin/api-keys/{args.id}"
    headers = {"Authorization": f"Bearer {args.token}"} if args.token else {}

    try:
        req = Request(url, headers=headers, method="DELETE")
        with urlopen(req):
            print("API Key deleted successfully!")
    except HTTPError as e:
        print(f"Error: {e.code}", file=sys.stderr)
        sys.exit(1)
    except URLError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def register_api_key_commands(subparsers):
    parser = subparsers.add_parser(
        "api-key",
        help="Manage API keys",
        description="List, create, update, or delete API keys for client authentication."
    )
    api_key_subparsers = parser.add_subparsers(dest="command", help="Available API key commands")

    list_parser = api_key_subparsers.add_parser(
        "list",
        help="List all API keys",
        description="List all configured API keys. "
                 "Note: API key values are only shown once at creation."
    )
    list_parser.set_defaults(func=cmd_api_key_list)

    create_parser = api_key_subparsers.add_parser(
        "create",
        help="Create a new API key",
        description="Create a new API key for client authentication. "
                 "The key value is only shown once - save it securely!"
    )
    create_parser.add_argument(
        "--name", required=True,
        help="API key name/label (required), e.g., prod-key, test-key, mobile-app"
    )
    create_parser.set_defaults(func=cmd_api_key_create)

    update_parser = api_key_subparsers.add_parser(
        "update",
        help="Update an API key",
        description="Update API key name. Required: API key ID as positional argument."
    )
    update_parser.add_argument(
        "id",
        help="API key ID (required). Get from: botcli api-key list"
    )
    update_parser.add_argument(
        "--name",
        help="New API key name/label (optional)"
    )
    update_parser.set_defaults(func=cmd_api_key_update)

    delete_parser = api_key_subparsers.add_parser(
        "delete",
        help="Delete an API key",
        description="Delete an API key. This will revoke access for clients using this key."
    )
    delete_parser.add_argument(
        "id",
        help="API key ID (required). Get from: botcli api-key list"
    )
    delete_parser.set_defaults(func=cmd_api_key_delete)
