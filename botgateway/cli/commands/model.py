import json
import sys
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def cmd_model_list(args):
    url = f"{args.server}/admin/models"
    if args.provider_id:
        url += f"?provider_id={args.provider_id}"

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


def cmd_model_add(args):
    url = f"{args.server}/admin/models"
    headers = {"Authorization": f"Bearer {args.token}"} if args.token else {}
    headers["Content-Type"] = "application/json"

    body_data = {
        "provider_id": args.provider_id,
        "name": args.name,
    }
    if args.model_type:
        body_data["model_type"] = args.model_type
    if args.max_tokens:
        body_data["max_tokens"] = int(args.max_tokens)
    if args.temperature:
        body_data["temperature"] = float(args.temperature)
    if args.top_p:
        body_data["top_p"] = float(args.top_p)
    if args.timeout:
        body_data["timeout"] = int(args.timeout)

    body = json.dumps(body_data).encode("utf-8")

    try:
        req = Request(url, headers=headers, data=body, method="POST")
        with urlopen(req) as response:
            data = json.loads(response.read().decode("utf-8"))
            print("Model created successfully!")
            print(json.dumps(data, indent=2, ensure_ascii=False))
    except HTTPError as e:
        print(f"Error: {e.code}", file=sys.stderr)
        sys.exit(1)
    except URLError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_model_update(args):
    url = f"{args.server}/admin/models/{args.id}"
    headers = {"Authorization": f"Bearer {args.token}"} if args.token else {}
    headers["Content-Type"] = "application/json"

    update_data = {}
    if args.name:
        update_data["name"] = args.name
    if args.model_type:
        update_data["model_type"] = args.model_type
    if args.max_tokens:
        update_data["max_tokens"] = int(args.max_tokens)
    if args.temperature:
        update_data["temperature"] = float(args.temperature)
    if args.top_p:
        update_data["top_p"] = float(args.top_p)
    if args.timeout:
        update_data["timeout"] = int(args.timeout)

    if not update_data:
        print("Error: No update data provided", file=sys.stderr)
        sys.exit(1)

    body = json.dumps(update_data).encode("utf-8")

    try:
        req = Request(url, headers=headers, data=body, method="PUT")
        with urlopen(req) as response:
            data = json.loads(response.read().decode("utf-8"))
            print("Model updated successfully!")
            print(json.dumps(data, indent=2, ensure_ascii=False))
    except HTTPError as e:
        print(f"Error: {e.code}", file=sys.stderr)
        sys.exit(1)
    except URLError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_model_delete(args):
    url = f"{args.server}/admin/models/{args.id}"
    headers = {"Authorization": f"Bearer {args.token}"} if args.token else {}

    try:
        req = Request(url, headers=headers, method="DELETE")
        with urlopen(req):
            print("Model deleted successfully!")
    except HTTPError as e:
        print(f"Error: {e.code}", file=sys.stderr)
        sys.exit(1)
    except URLError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def register_model_commands(subparsers):
    parser = subparsers.add_parser(
        "model",
        help="Manage models",
        description="List, add, update, or delete models in the gateway."
    )
    model_subparsers = parser.add_subparsers(dest="command", help="Available model commands")

    list_parser = model_subparsers.add_parser(
        "list",
        help="List all models",
        description="List all models, optionally filtered by provider."
    )
    list_parser.add_argument(
        "--provider-id",
        help="Filter models by provider ID (optional)"
    )
    list_parser.set_defaults(func=cmd_model_list)

    add_parser = model_subparsers.add_parser(
        "add",
        help="Create a new model",
        description="Create a new model. Required: --provider-id and --name."
    )
    add_parser.add_argument(
        "--provider-id", required=True,
        help="Provider ID (required). Get from: botcli provider list"
    )
    add_parser.add_argument(
        "--name", required=True,
        help="Model name (required), e.g., gpt-4, claude-3"
    )
    add_parser.add_argument(
        "--model-type",
        default="chat",
        help="Model type (default: chat). Options: chat, embedding"
    )
    add_parser.add_argument(
        "--max-tokens",
        help="Maximum tokens in response (optional), e.g., 4096"
    )
    add_parser.add_argument(
        "--temperature",
        type=float,
        help="Temperature for randomness (optional, default: 0.7), range: 0-2"
    )
    add_parser.add_argument(
        "--top-p",
        type=float,
        help="Top-p sampling (optional, default: 1.0), range: 0-1"
    )
    add_parser.add_argument(
        "--timeout",
        type=int,
        help="Request timeout in seconds (optional, default: 60)"
    )
    add_parser.set_defaults(func=cmd_model_add)

    update_parser = model_subparsers.add_parser(
        "update",
        help="Update an existing model",
        description="Update model parameters. Required: model ID as positional argument."
    )
    update_parser.add_argument(
        "id",
        help="Model ID (required). Get from: botcli model list"
    )
    update_parser.add_argument("--name", help="Model name (optional)")
    update_parser.add_argument("--model-type", help="Model type (optional)")
    update_parser.add_argument("--max-tokens", help="Max tokens (optional)")
    update_parser.add_argument(
        "--temperature", type=float,
        help="Temperature (optional), range: 0-2"
    )
    update_parser.add_argument(
        "--top-p", type=float,
        help="Top-p (optional), range: 0-1"
    )
    update_parser.add_argument("--timeout", type=int, help="Timeout in seconds (optional)")
    update_parser.set_defaults(func=cmd_model_update)

    delete_parser = model_subparsers.add_parser(
        "delete",
        help="Delete a model",
        description="Delete a model by ID."
    )
    delete_parser.add_argument(
        "id",
        help="Model ID (required). Get from: botcli model list"
    )
    delete_parser.set_defaults(func=cmd_model_delete)
