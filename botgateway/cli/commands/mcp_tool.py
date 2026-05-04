import json
import sys
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def cmd_mcp_tool_list(args):
    url = f"{args.server}/admin/mcp-tools"
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


def cmd_mcp_tool_create(args):
    if args.file:
        return _import_from_file(args)

    url = f"{args.server}/admin/mcp-tools"
    headers = {"Authorization": f"Bearer {args.token}"} if args.token else {}
    headers["Content-Type"] = "application/json"

    tool_data = {"name": args.name}
    if args.description:
        tool_data["description"] = args.description
    if args.endpoint_url:
        tool_data["endpoint_url"] = args.endpoint_url
    if args.tool_schema:
        try:
            tool_data["tool_schema"] = json.loads(args.tool_schema)
        except json.JSONDecodeError as e:
            print(f"Error: Invalid JSON schema: {e}", file=sys.stderr)
            sys.exit(1)

    body = json.dumps(tool_data).encode("utf-8")

    try:
        req = Request(url, headers=headers, data=body, method="POST")
        with urlopen(req) as response:
            data = json.loads(response.read().decode("utf-8"))
            print("MCP Tool created successfully!")
            print(json.dumps(data, indent=2, ensure_ascii=False))
    except HTTPError as e:
        print(f"Error: {e.code}", file=sys.stderr)
        sys.exit(1)
    except URLError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def _import_from_file(args):
    import os

    file_path = args.file
    if not os.path.exists(file_path):
        print(f"Error: File not found: {file_path}", file=sys.stderr)
        sys.exit(1)

    if not file_path.endswith(".json"):
        print("Error: Only .json files are supported", file=sys.stderr)
        sys.exit(1)

    url = f"{args.server}/admin/mcp-tools/import-servers"
    headers = {"Authorization": f"Bearer {args.token}"} if args.token else {}

    boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
    headers["Content-Type"] = f"multipart/form-data; boundary={boundary}"

    try:
        with open(file_path, "rb") as f:
            file_content = f.read()
    except Exception as e:
        print(f"Error: Failed to read file: {e}", file=sys.stderr)
        sys.exit(1)

    filename = os.path.basename(file_path)
    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'
        f"Content-Type: application/json\r\n\r\n"
    ).encode() + file_content + f"\r\n--{boundary}--\r\n".encode()

    try:
        req = Request(url, headers=headers, data=body, method="POST")
        with urlopen(req) as response:
            data = json.loads(response.read().decode("utf-8"))
            print("Import completed!")
            print(f"Success: {len(data.get('success', []))}")
            print(f"Errors: {len(data.get('errors', []))}")
            if data.get("success"):
                print("\nImported servers:")
                for server in data["success"]:
                    print(f"  - {server['name']} (ID: {server['id']})")
            if data.get("errors"):
                print("\nErrors:")
                for error in data["errors"]:
                    print(f"  - Index {error['index']}: {error['error']}")
    except HTTPError as e:
        error_body = ""
        try:
            error_body = e.read().decode("utf-8")
        except Exception:
            pass
        print(f"Error: {e.code}", file=sys.stderr)
        if error_body:
            print(f"Details: {error_body}", file=sys.stderr)
        sys.exit(1)
    except URLError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_mcp_tool_update(args):
    url = f"{args.server}/admin/mcp-tools/{args.id}"
    headers = {"Authorization": f"Bearer {args.token}"} if args.token else {}
    headers["Content-Type"] = "application/json"

    update_data = {}
    if args.name:
        update_data["name"] = args.name
    if args.description:
        update_data["description"] = args.description
    if args.endpoint_url:
        update_data["endpoint_url"] = args.endpoint_url
    if args.tool_schema:
        try:
            update_data["tool_schema"] = json.loads(args.tool_schema)
        except json.JSONDecodeError as e:
            print(f"Error: Invalid JSON schema: {e}", file=sys.stderr)
            sys.exit(1)
    if args.is_active is not None:
        update_data["is_active"] = args.is_active

    if not update_data:
        print("Error: No update data provided", file=sys.stderr)
        sys.exit(1)

    body = json.dumps(update_data).encode("utf-8")

    try:
        req = Request(url, headers=headers, data=body, method="PUT")
        with urlopen(req) as response:
            data = json.loads(response.read().decode("utf-8"))
            print("MCP Tool updated successfully!")
            print(json.dumps(data, indent=2, ensure_ascii=False))
    except HTTPError as e:
        print(f"Error: {e.code}", file=sys.stderr)
        sys.exit(1)
    except URLError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_mcp_tool_delete(args):
    url = f"{args.server}/admin/mcp-tools/{args.id}"
    headers = {"Authorization": f"Bearer {args.token}"} if args.token else {}

    try:
        req = Request(url, headers=headers, method="DELETE")
        with urlopen(req):
            print("MCP Tool deleted successfully!")
    except HTTPError as e:
        print(f"Error: {e.code}", file=sys.stderr)
        sys.exit(1)
    except URLError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_mcp_server_list(args):
    url = f"{args.server}/admin/mcp-tools/servers"
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


def cmd_mcp_server_create(args):
    url = f"{args.server}/admin/mcp-tools/servers"
    headers = {"Authorization": f"Bearer {args.token}"} if args.token else {}
    headers["Content-Type"] = "application/json"

    server_data = {"name": args.name, "transport": args.transport}
    if args.command:
        server_data["command"] = args.command
    if args.args:
        try:
            server_data["args"] = json.loads(args.args)
        except json.JSONDecodeError as e:
            print(f"Error: Invalid JSON args: {e}", file=sys.stderr)
            sys.exit(1)
    if args.url:
        server_data["url"] = args.url
    if args.env:
        try:
            server_data["env"] = json.loads(args.env)
        except json.JSONDecodeError as e:
            print(f"Error: Invalid JSON env: {e}", file=sys.stderr)
            sys.exit(1)
    if args.description:
        server_data["description"] = args.description

    body = json.dumps(server_data).encode("utf-8")

    try:
        req = Request(url, headers=headers, data=body, method="POST")
        with urlopen(req) as response:
            data = json.loads(response.read().decode("utf-8"))
            print("MCP Server created successfully!")
            print(json.dumps(data, indent=2, ensure_ascii=False))
    except HTTPError as e:
        print(f"Error: {e.code}", file=sys.stderr)
        sys.exit(1)
    except URLError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_mcp_server_import(args):
    import os

    file_path = args.file
    if not os.path.exists(file_path):
        print(f"Error: File not found: {file_path}", file=sys.stderr)
        sys.exit(1)

    if not file_path.endswith(".json"):
        print("Error: Only .json files are supported", file=sys.stderr)
        sys.exit(1)

    url = f"{args.server}/admin/mcp-tools/import-servers"
    headers = {"Authorization": f"Bearer {args.token}"} if args.token else {}

    boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
    headers["Content-Type"] = f"multipart/form-data; boundary={boundary}"

    try:
        with open(file_path, "rb") as f:
            file_content = f.read()
    except Exception as e:
        print(f"Error: Failed to read file: {e}", file=sys.stderr)
        sys.exit(1)

    filename = os.path.basename(file_path)
    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'
        f"Content-Type: application/json\r\n\r\n"
    ).encode() + file_content + f"\r\n--{boundary}--\r\n".encode()

    try:
        req = Request(url, headers=headers, data=body, method="POST")
        with urlopen(req) as response:
            data = json.loads(response.read().decode("utf-8"))
            print("Import completed!")
            print(f"Success: {len(data.get('success', []))}")
            print(f"Errors: {len(data.get('errors', []))}")
            if data.get("success"):
                print("\nImported servers:")
                for server in data["success"]:
                    print(f"  - {server['name']} (ID: {server['id']})")
            if data.get("errors"):
                print("\nErrors:")
                for error in data["errors"]:
                    print(f"  - Index {error['index']}: {error['error']}")
    except HTTPError as e:
        error_body = ""
        try:
            error_body = e.read().decode("utf-8")
        except Exception:
            pass
        print(f"Error: {e.code}", file=sys.stderr)
        if error_body:
            print(f"Details: {error_body}", file=sys.stderr)
        sys.exit(1)
    except URLError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_mcp_server_delete(args):
    url = f"{args.server}/admin/mcp-tools/servers/{args.id}"
    headers = {"Authorization": f"Bearer {args.token}"} if args.token else {}

    try:
        req = Request(url, headers=headers, method="DELETE")
        with urlopen(req):
            print("MCP Server deleted successfully!")
    except HTTPError as e:
        print(f"Error: {e.code}", file=sys.stderr)
        sys.exit(1)
    except URLError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_mcp_server_sync(args):
    url = f"{args.server}/admin/mcp-tools/servers/{args.server_id}/sync-tools"
    headers = {"Authorization": f"Bearer {args.token}"} if args.token else {}

    try:
        req = Request(url, headers=headers, method="POST")
        with urlopen(req) as response:
            data = json.loads(response.read().decode("utf-8"))
            print("Sync completed!")
            print(f"Success: {len(data.get('success', []))}")
            print(f"Errors: {len(data.get('errors', []))}")
            if data.get("success"):
                print("\nSynced tools:")
                for tool in data["success"]:
                    print(f"  - {tool['name']} (ID: {tool['id']})")
            if data.get("errors"):
                print("\nErrors:")
                for error in data["errors"]:
                    print(f"  - Index {error['index']}: {error['error']}")
    except HTTPError as e:
        print(f"Error: {e.code}", file=sys.stderr)
        sys.exit(1)
    except URLError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def register_mcp_tool_commands(subparsers):
    parser = subparsers.add_parser(
        "mcp-tool",
        help="Manage MCP tools",
        description="List, create, update, or delete MCP tools in the gateway."
    )
    mcp_tool_subparsers = parser.add_subparsers(dest="command", help="Available MCP tool commands")

    list_parser = mcp_tool_subparsers.add_parser(
        "list",
        help="List all MCP tools",
        description="List all configured MCP tools."
    )
    list_parser.set_defaults(func=cmd_mcp_tool_list)

    create_parser = mcp_tool_subparsers.add_parser(
        "create",
        help="Create a new MCP tool",
        description="Create a new MCP tool. Use --file to import from mcp.json."
    )
    create_parser.add_argument("--name", help="MCP tool name (optional)")
    create_parser.add_argument("--description", help="MCP tool description (optional)")
    create_parser.add_argument("--endpoint-url", help="MCP tool endpoint URL (optional)")
    create_parser.add_argument(
        "--tool-schema",
        help="MCP tool schema as JSON string (optional), e.g., '{\"type\":\"function\",...}'"
    )
    create_parser.add_argument(
        "--file", "-f",
        help="Import from mcp.json file (required for bulk import). "
             "Format: {tool_name: {url:..., cmd:[...]}}"
    )
    create_parser.set_defaults(func=cmd_mcp_tool_create)

    update_parser = mcp_tool_subparsers.add_parser(
        "update",
        help="Update an MCP tool",
        description="Update MCP tool parameters. Required: tool ID as positional argument."
    )
    update_parser.add_argument("id", help="MCP tool ID (required). Get from: botcli mcp-tool list")
    update_parser.add_argument("--name", help="MCP tool name (optional)")
    update_parser.add_argument("--description", help="MCP tool description (optional)")
    update_parser.add_argument("--endpoint-url", help="MCP tool endpoint URL (optional)")
    update_parser.add_argument("--tool-schema", help="MCP tool schema JSON string (optional)")
    update_parser.add_argument(
        "--is-active", type=lambda x: x.lower() == "true",
        help="Active status (optional). Use: true or false"
    )
    update_parser.set_defaults(func=cmd_mcp_tool_update)

    delete_parser = mcp_tool_subparsers.add_parser(
        "delete",
        help="Delete an MCP tool",
        description="Delete an MCP tool by ID."
    )
    delete_parser.add_argument("id", help="MCP tool ID (required). Get from: botcli mcp-tool list")
    delete_parser.set_defaults(func=cmd_mcp_tool_delete)

    server_parser = subparsers.add_parser(
        "mcp-server",
        help="Manage MCP servers",
        description="List, create, import, or delete MCP servers."
    )
    mcp_server_subparsers = server_parser.add_subparsers(
        dest="command",
        help="Available MCP server commands"
    )

    server_list_parser = mcp_server_subparsers.add_parser(
        "list",
        help="List all MCP servers",
        description="List all configured MCP servers."
    )
    server_list_parser.set_defaults(func=cmd_mcp_server_list)

    server_create_parser = mcp_server_subparsers.add_parser(
        "create",
        help="Create a new MCP server",
        description="Create a new MCP server. Required: --name."
    )
    server_create_parser.add_argument(
        "--name", required=True,
        help="MCP server name (required), e.g., weather-server, calculator"
    )
    server_create_parser.add_argument(
        "--transport", default="stdio",
        help="Transport type (default: stdio). Options: stdio, sse, http"
    )
    server_create_parser.add_argument(
        "--command",
        help="Command to run (required for stdio transport), e.g., uv, python"
    )
    server_create_parser.add_argument(
        "--args",
        help="Command arguments as JSON array (optional), e.g., '[\"run\", \"weather\"]'"
    )
    server_create_parser.add_argument(
        "--url",
        help="Server URL (required for sse/http transport), e.g., http://localhost:8080/sse"
    )
    server_create_parser.add_argument(
        "--env",
        help="Environment variables as JSON object (optional), e.g., '{\"API_KEY\": \"xxx\"}'"
    )
    server_create_parser.add_argument("--description", help="Server description (optional)")
    server_create_parser.set_defaults(func=cmd_mcp_server_create)

    server_import_parser = mcp_server_subparsers.add_parser(
        "import",
        help="Import MCP servers from mcp.json",
        description="Import MCP servers from a mcp.json file. Required: --file."
    )
    server_import_parser.add_argument(
        "--file", "-f", required=True,
        help="Path to mcp.json file (required)"
    )
    server_import_parser.set_defaults(func=cmd_mcp_server_import)

    server_delete_parser = mcp_server_subparsers.add_parser(
        "delete",
        help="Delete an MCP server",
        description="Delete an MCP server by ID."
    )
    server_delete_parser.add_argument(
        "id",
        help="MCP server ID (required). Get from: botcli mcp-server list"
    )
    server_delete_parser.set_defaults(func=cmd_mcp_server_delete)

    server_sync_parser = mcp_server_subparsers.add_parser(
        "sync",
        help="Sync tools from MCP server",
        description="Sync tools from an MCP server. Creates/updates tools in the gateway."
    )
    server_sync_parser.add_argument(
        "server_id",
        help="MCP server ID (required). Get from: botcli mcp-server list"
    )
    server_sync_parser.set_defaults(func=cmd_mcp_server_sync)
