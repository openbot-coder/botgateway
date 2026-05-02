import argparse
import json
import sys
from pathlib import Path

# UNCOVERED: 启动服务器的代码 - 需要 uvicorn 运行，无法在单元测试中测试
# 这是可接受的未覆盖原因，因为 main() 函数启动 uvicorn 服务器

from botgateway.config import load_config, save_config, generate_token
from botgateway.main import create_app


def main():
    parser = argparse.ArgumentParser(
        prog="botgateway",
        description="启动 BotGateway FastAPI 服务"
    )
    
    parser.add_argument(
        "--host",
        type=str,
        help="服务绑定地址"
    )
    
    parser.add_argument(
        "--port",
        type=int,
        help="服务端口"
    )
    
    parser.add_argument(
        "--config",
        type=str,
        help="配置文件路径"
    )
    
    parser.add_argument(
        "--token",
        type=str,
        help="管理 token（优先使用命令行参数）"
    )
    
    parser.add_argument(
        "--generate-token",
        action="store_true",
        help="生成一个新的管理 token"
    )
    
    parser.add_argument(
        "--save-config",
        action="store_true",
        help="保存配置到配置文件"
    )
    
    args = parser.parse_args()
    
    if args.generate_token:
        token = generate_token()
        print(f"Generated token: {token}")
        return
    
    config = load_config(args.config)
    
    host = args.host if args.host else config.get("host", "127.0.0.1")
    port = args.port if args.port else config.get("port", 8000)
    token = args.token if args.token else config.get("management_token", "")
    
    if args.save_config:
        config["host"] = host
        config["port"] = port
        config["management_token"] = token
        save_config(config, args.config)
        print(f"Config saved to {args.config or 'default path'}")
        return
    
    print(f"Starting BotGateway on {host}:{port}")
    if token:
        print("Management token is configured")
    else:
        print("Warning: No management token configured")
    
    try:
        import uvicorn
        app = create_app(management_token=token)
        uvicorn.run(app, host=host, port=port)
    except ImportError:
        print("Error: uvicorn not installed", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()