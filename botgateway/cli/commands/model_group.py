import json
import sys
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def cmd_model_group_list(args):
    url = f"{args.server}/admin/model-groups"
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


def cmd_model_group_add(args):
    url = f"{args.server}/admin/model-groups"
    headers = {"Authorization": f"Bearer {args.token}"} if args.token else {}
    headers["Content-Type"] = "application/json"

    body_data = {
        "name": args.name,
        "routing_strategy": args.strategy,
    }
    if args.description:
        body_data["description"] = args.description
    if args.retry_count:
        body_data["retry_count"] = int(args.retry_count)
    if args.retry_delay:
        body_data["retry_delay"] = int(args.retry_delay)
    if args.cooldown:
        body_data["cooldown_period"] = int(args.cooldown)

    body = json.dumps(body_data).encode("utf-8")

    try:
        req = Request(url, headers=headers, data=body, method="POST")
        with urlopen(req) as response:
            data = json.loads(response.read().decode("utf-8"))
            print("Model group created successfully!")
            print(json.dumps(data, indent=2, ensure_ascii=False))
    except HTTPError as e:
        print(f"Error: {e.code}", file=sys.stderr)
        sys.exit(1)
    except URLError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_model_group_update(args):
    url = f"{args.server}/admin/model-groups/{args.id}"
    headers = {"Authorization": f"Bearer {args.token}"} if args.token else {}
    headers["Content-Type"] = "application/json"

    update_data = {}
    if args.name:
        update_data["name"] = args.name
    if args.description:
        update_data["description"] = args.description
    if args.strategy:
        update_data["routing_strategy"] = args.strategy
    if args.retry_count:
        update_data["retry_count"] = int(args.retry_count)
    if args.retry_delay:
        update_data["retry_delay"] = int(args.retry_delay)
    if args.cooldown:
        update_data["cooldown_period"] = int(args.cooldown)

    if not update_data:
        print("Error: No update data provided", file=sys.stderr)
        sys.exit(1)

    body = json.dumps(update_data).encode("utf-8")

    try:
        req = Request(url, headers=headers, data=body, method="PUT")
        with urlopen(req) as response:
            data = json.loads(response.read().decode("utf-8"))
            print("Model group updated successfully!")
            print(json.dumps(data, indent=2, ensure_ascii=False))
    except HTTPError as e:
        print(f"Error: {e.code}", file=sys.stderr)
        sys.exit(1)
    except URLError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_model_group_add_member(args):
    url = f"{args.server}/admin/model-groups/{args.group_id}/members"
    headers = {"Authorization": f"Bearer {args.token}"} if args.token else {}
    headers["Content-Type"] = "application/json"

    body_data = {
        "model_id": args.model_id,
    }
    if args.priority:
        body_data["priority"] = int(args.priority)
    if args.weight:
        body_data["weight"] = int(args.weight)

    body = json.dumps(body_data).encode("utf-8")

    try:
        req = Request(url, headers=headers, data=body, method="POST")
        with urlopen(req) as response:
            data = json.loads(response.read().decode("utf-8"))
            print("Member added successfully!")
            print(json.dumps(data, indent=2, ensure_ascii=False))
    except HTTPError as e:
        print(f"Error: {e.code}", file=sys.stderr)
        sys.exit(1)
    except URLError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_model_group_remove_member(args):
    url = f"{args.server}/admin/model-groups/{args.group_id}/members/{args.member_id}"
    headers = {"Authorization": f"Bearer {args.token}"} if args.token else {}

    try:
        req = Request(url, headers=headers, method="DELETE")
        with urlopen(req):
            print("Member removed successfully!")
    except HTTPError as e:
        print(f"Error: {e.code}", file=sys.stderr)
        sys.exit(1)
    except URLError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_model_group_delete(args):
    url = f"{args.server}/admin/model-groups/{args.id}"
    headers = {"Authorization": f"Bearer {args.token}"} if args.token else {}

    try:
        req = Request(url, headers=headers, method="DELETE")
        with urlopen(req):
            print("Model group deleted successfully!")
    except HTTPError as e:
        print(f"Error: {e.code}", file=sys.stderr)
        sys.exit(1)
    except URLError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def register_model_group_commands(subparsers):
    parser = subparsers.add_parser("model-group", help="Manage model groups")
    group_subparsers = parser.add_subparsers(dest="command", help="Model group commands")

    list_parser = group_subparsers.add_parser("list", help="List all model groups")
    list_parser.set_defaults(func=cmd_model_group_list)

    add_parser = group_subparsers.add_parser("add", help="Create a model group")
    add_parser.add_argument("--name", required=True, help="Model group name")
    add_parser.add_argument("--strategy", required=True, choices=["fallback", "weight_random"],
                            help="Routing strategy")
    add_parser.add_argument("--description", help="Description")
    add_parser.add_argument("--retry-count", help="Retry count")
    add_parser.add_argument("--retry-delay", help="Retry delay in seconds")
    add_parser.add_argument("--cooldown", help="Cooldown period in seconds")
    add_parser.set_defaults(func=cmd_model_group_add)

    update_parser = group_subparsers.add_parser("update", help="Update a model group")
    update_parser.add_argument("id", help="Model group ID")
    update_parser.add_argument("--name", help="Model group name")
    update_parser.add_argument("--strategy", choices=["fallback", "weight_random"],
                               help="Routing strategy")
    update_parser.add_argument("--description", help="Description")
    update_parser.add_argument("--retry-count", help="Retry count")
    update_parser.add_argument("--retry-delay", help="Retry delay in seconds")
    update_parser.add_argument("--cooldown", help="Cooldown period in seconds")
    update_parser.set_defaults(func=cmd_model_group_update)

    add_member_parser = group_subparsers.add_parser("add-member", help="Add member to model group")
    add_member_parser.add_argument("group_id", help="Model group ID")
    add_member_parser.add_argument("--model-id", required=True, help="Model ID")
    add_member_parser.add_argument("--priority", help="Priority")
    add_member_parser.add_argument("--weight", help="Weight")
    add_member_parser.set_defaults(func=cmd_model_group_add_member)

    remove_member_parser = group_subparsers.add_parser(
        "remove-member", help="Remove member from model group"
    )
    remove_member_parser.add_argument("group_id", help="Model group ID")
    remove_member_parser.add_argument("member_id", help="Member ID")
    remove_member_parser.set_defaults(func=cmd_model_group_remove_member)

    delete_parser = group_subparsers.add_parser("delete", help="Delete a model group")
    delete_parser.add_argument("id", help="Model group ID")
    delete_parser.set_defaults(func=cmd_model_group_delete)
