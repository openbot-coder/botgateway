# UX Improvements

## 1. health endpoint 返回内容优化

1.memory 输出内容 显示为 MB
2、disk 输出内容 显示为 MB
3、endpoints 输出内容 显示为 path 和 methods 字段

输出样例如下：
PS C:\Users\shale\Documents\src\botgateway> botcli.exe --server http://127.0.0.1:8000 -t iH60kBgg5egN8lCWNQAUL3WGZkmIiPlx status
Status: healthy
Server Time: 2026-05-03T09:21:23.197745Z
PS C:\Users\shale\Documents\src\botgateway> botcli.exe --server http://127.0.0.1:8000 -t iH60kBgg5egN8lCWNQAUL3WGZkmIiPlx health
{
  "status": "healthy",
  "server_time": "2026-05-03T09:21:33.487639Z",
  "memory": {
    "total": 16996933632,
    "available": 3311857664,
    "used": 13685075968,
    "percent": 80.5
  },
  "cpu": {
    "percent": 19.6,
    "count": 8,
    "freq": {
      "current": 2419.0,
      "min": 0.0,
      "max": 2419.0
    }
  },
  "disk": {
    "total": 254752583680,
    "used": 216002080768,
    "free": 38750502912,
    "percent": 84.8
  },
  "network": {
    "connections": 248
  },
  "process": {
    "pid": 14244,
    "name": "python.exe",
    "memory_percent": 0.42733806916355677,
    "cpu_percent": 0.0
  },
  "uptime": 139456.94160485268,
  "endpoints": [
    {
      "path": "/openapi.json",
      "methods": [
        "GET",
        "HEAD"
      ]
    },
    {
      "path": "/docs",
      "methods": [
        "GET",
        "HEAD"
      ]
    },
    {
      "path": "/docs/oauth2-redirect",
      "methods": [
        "GET",
        "HEAD"
      ]
    },
    {
      "path": "/redoc",
      "methods": [
        "GET",
        "HEAD"
      ]
    },
    {
      "path": "/health",
      "methods": [
        "GET"
      ]
    },
    {
      "path": "/v1/chat/completions",
      "methods": [
        "POST"
      ]
    },
    {
      "path": "/v1/models",
      "methods": [
        "GET"
      ]
    },
    {
      "path": "/admin/providers",
      "methods": [
        "POST"
      ]
    },
    {
      "path": "/admin/providers",
      "methods": [
        "GET"
      ]
    },
    {
      "path": "/admin/providers/{provider_id}",
      "methods": [
        "GET"
      ]
    },
    {
      "path": "/admin/providers/{provider_id}",
      "methods": [
        "PUT"
      ]
    },
    {
      "path": "/admin/providers/{provider_id}",
      "methods": [
        "DELETE"
      ]
    },
    {
      "path": "/admin/models",
      "methods": [
        "POST"
      ]
    },
    {
      "path": "/admin/models",
      "methods": [
        "GET"
      ]
    },
    {
      "path": "/admin/models/{model_id}",
      "methods": [
        "GET"
      ]
    },
    {
      "path": "/admin/models/{model_id}",
      "methods": [
        "PUT"
      ]
    },
    {
      "path": "/admin/models/{model_id}",
      "methods": [
        "DELETE"
      ]
    },
    {
      "path": "/admin/model-groups",
      "methods": [
        "POST"
      ]
    },
    {
      "path": "/admin/model-groups",
      "methods": [
        "GET"
      ]
    },
    {
      "path": "/admin/model-groups/{group_id}",
      "methods": [
        "GET"
      ]
    },
    {
      "path": "/admin/model-groups/{group_id}",
      "methods": [
        "PUT"
      ]
    },
    {
      "path": "/admin/model-groups/{group_id}",
      "methods": [
        "DELETE"
      ]
    },
    {
      "path": "/admin/model-groups/{group_id}/members",
      "methods": [
        "POST"
      ]
    },
    {
      "path": "/admin/model-groups/{group_id}/members/{member_id}",      
      "methods": [
        "DELETE"
      ]
    },
    {
      "path": "/admin/api-keys",
      "methods": [
        "POST"
      ]
    },
    {
      "path": "/admin/api-keys",
      "methods": [
        "GET"
      ]
    },
    {
      "path": "/admin/api-keys/{api_key_id}",
      "methods": [
        "GET"
      ]
    },
    {
      "path": "/admin/api-keys/{api_key_id}",
      "methods": [
        "PUT"
      ]
    },
    {
      "path": "/admin/api-keys/{api_key_id}",
      "methods": [
        "DELETE"
      ]
    },
    {
      "path": "/admin/mcp-tools",
      "methods": [
        "POST"
      ]
    },
    {
      "path": "/admin/mcp-tools",
      "methods": [
        "GET"
      ]
    },
    {
      "path": "/admin/mcp-tools/import",
      "methods": [
        "POST"
      ]
    },
    {
      "path": "/admin/mcp-tools/import-servers",
      "methods": [
        "POST"
      ]
    },
    {
      "path": "/admin/mcp-tools/servers",
      "methods": [
        "POST"
      ]
    },
    {
      "path": "/admin/mcp-tools/servers",
      "methods": [
        "GET"
      ]
    },
    {
      "path": "/admin/mcp-tools/servers/{server_id}",
      "methods": [
        "GET"
      ]
    },
    {
      "path": "/admin/mcp-tools/servers/{server_id}",
      "methods": [
        "PUT"
      ]
    },
    {
      "path": "/admin/mcp-tools/servers/{server_id}",
      "methods": [
        "DELETE"
      ]
    },
    {
      "path": "/admin/mcp-tools/servers/{server_id}/sync-tools",
      "methods": [
        "POST"
      ]
    },
    {
      "path": "/admin/mcp-tools/{tool_id}",
      "methods": [
        "GET"
      ]
    },
    {
      "path": "/admin/mcp-tools/{tool_id}",
      "methods": [
        "PUT"
      ]
    },
    {
      "path": "/admin/mcp-tools/{tool_id}",
      "methods": [
        "DELETE"
      ]
    },
    {
      "path": "/v1/mcp/tools",
      "methods": [
        "GET"
      ]
    },
    {
      "path": "/v1/mcp/tools/{tool_name}",
      "methods": [
        "GET"
      ]
    },
    {
      "path": "/v1/mcp/tools/{tool_name}/call",
      "methods": [
        "POST"
      ]
    },
    {
      "path": "/",
      "methods": [
        "GET"
      ]
    }
  ]
}

## 2. 命令行help提示优化


提示不足，需要给一些示例说明，或者默认值如何设置等等。
所有的help信息都要优化，确保用户能够快速理解每个命令的使用方法。

PS C:\Users\shale\Documents\src\botgateway> botcli.exe --server http://127.0.0.1:8000 -t iH60kBgg5egN8lCWNQAUL3WGZkmIiPlx model add -h    
usage: botcli model add [-h] --provider-id PROVIDER_ID --name NAME
                        [--model-type MODEL_TYPE]
                        [--max-tokens MAX_TOKENS]
                        [--temperature TEMPERATURE] [--top-p TOP_P]      
                        [--timeout TIMEOUT]

options:
  -h, --help            show this help message and exit
  --provider-id PROVIDER_ID
                        Provider ID
  --name NAME           Model name
  --model-type MODEL_TYPE
                        Model type
  --max-tokens MAX_TOKENS
                        Max tokens
  --temperature TEMPERATURE
                        Temperature
  --top-p TOP_P         Top p
  --timeout TIMEOUT     Timeout in seconds

  ## 3.


  [                                                                        
  {
    "id": "58f34d51-669f-4743-9bb8-ae57360a2de4",
    "provider_id": "17d9e1f9-df1d-454d-912c-bc97b2e03131",
    "name": "mimo-v2.5-pro",
    "model_type": "chat",
    "max_tokens": null,
    "temperature": 0.7,
    "top_p": 1.0,
    "timeout": 60,
    "extra_params": null,
    "is_active": true,
    "created_at": "2026-05-03T10:00:56.359884+00:00",
    "updated_at": "2026-05-03T10:00:56.359900+00:00"
  },
  {
    "id": "27acbc99-5208-4452-931b-d2b0df0dd5a9",
    "provider_id": "17d9e1f9-df1d-454d-912c-bc97b2e03131",
    "name": "mimo-v2.5",
    "model_type": "chat",
    "max_tokens": null,
    "temperature": 0.7,
    "top_p": 1.0,
    "timeout": 60,
    "extra_params": null,
    "is_active": true,
    "created_at": "2026-05-03T10:01:03.270803+00:00",
    "updated_at": "2026-05-03T10:01:03.270837+00:00"
  },
  {
    "id": "a0bd49ab-a67a-41b2-881d-1913decc5226",
    "provider_id": "78ce8b69-a5dd-42c8-bb61-3ffa5416c9d1",
    "name": "ark-code-latest",
    "model_type": "chat",
    "max_tokens": null,
    "temperature": 0.7,
    "top_p": 1.0,
    "timeout": 60,
    "extra_params": null,
    "is_active": true,
    "created_at": "2026-05-03T10:03:15.045927+00:00",
    "updated_at": "2026-05-03T10:03:15.045945+00:00"
  },
  {
    "id": "31b45dfd-53db-4209-9d52-31430478c3cc",
    "provider_id": "78ce8b69-a5dd-42c8-bb61-3ffa5416c9d1",
    "name": "kimi-k2.6",
    "model_type": "chat",
    "max_tokens": null,
    "temperature": 0.7,
    "top_p": 1.0,
    "timeout": 60,
    "extra_params": null,
    "is_active": true,
    "created_at": "2026-05-03T10:03:42.657849+00:00",
    "updated_at": "2026-05-03T10:03:42.657866+00:00"
  },
  {
    "id": "9e0b895a-00a8-42da-9e46-b4b5958e6126",
    "provider_id": "78ce8b69-a5dd-42c8-bb61-3ffa5416c9d1",
    "name": "glm-5.1",
    "model_type": "chat",
    "max_tokens": null,
    "temperature": 0.7,
    "top_p": 1.0,
    "timeout": 60,
    "extra_params": null,
    "is_active": true,
    "created_at": "2026-05-03T10:03:53.633583+00:00",
    "updated_at": "2026-05-03T10:03:53.633608+00:00"
  },
  {
    "id": "54040cb7-8b11-4c9b-9412-5f5caafbc410",
    "provider_id": "78ce8b69-a5dd-42c8-bb61-3ffa5416c9d1",
    "name": "minimax-m2.7",
    "model_type": "chat",
    "max_tokens": null,
    "temperature": 0.7,
    "top_p": 1.0,
    "timeout": 60,
    "extra_params": null,
    "is_active": true,
    "created_at": "2026-05-03T10:04:12.965313+00:00",
    "updated_at": "2026-05-03T10:04:12.965331+00:00"
  },
  {
    "id": "b1d783f4-219f-43f6-940a-dce7c08c7fda",
    "provider_id": "78ce8b69-a5dd-42c8-bb61-3ffa5416c9d1",
    "name": "doubao-seed-2.0-pro",
    "model_type": "chat",
    "max_tokens": null,
    "temperature": 0.7,
    "top_p": 1.0,
    "timeout": 60,
    "extra_params": null,
    "is_active": true,
    "created_at": "2026-05-03T10:04:24.365036+00:00",
    "updated_at": "2026-05-03T10:04:24.365049+00:00"
  },
  {
    "id": "1deca6a4-3f0a-4071-b509-dc0ae4ac3620",
    "provider_id": "78ce8b69-a5dd-42c8-bb61-3ffa5416c9d1",
    "name": "doubao-seed-2.0-code",
    "model_type": "chat",
    "max_tokens": null,
    "temperature": 0.7,
    "top_p": 1.0,
    "timeout": 60,
    "extra_params": null,
    "is_active": true,
    "created_at": "2026-05-03T10:04:44.397770+00:00",
    "updated_at": "2026-05-03T10:04:44.397788+00:00"
  },
  {
    "id": "17069841-9e41-4d59-b248-b8c6f6729747",
    "provider_id": "01e2474f-472d-4687-8bd9-3cb53df06c77",
    "name": "minimax-m2.7-highspeed",
    "model_type": "chat",
    "max_tokens": null,
    "temperature": 0.7,
    "top_p": 1.0,
    "timeout": 60,
    "extra_params": null,
    "is_active": true,
    "created_at": "2026-05-03T10:05:40.556016+00:00",
    "updated_at": "2026-05-03T10:05:40.556028+00:00"
  },
  {
    "id": "ffa9aa13-b18f-4184-b790-1322e5cec78f",
    "provider_id": "01e2474f-472d-4687-8bd9-3cb53df06c77",
    "name": "minimax-m2.5-highspeed",
    "model_type": "chat",
    "max_tokens": null,
    "temperature": 0.7,
    "top_p": 1.0,
    "timeout": 60,
    "extra_params": null,
    "is_active": true,
    "created_at": "2026-05-03T10:05:44.908409+00:00",
    "updated_at": "2026-05-03T10:05:44.908429+00:00"
  }
]


## 4. 命令行无法执行

PS C:\Users\shale\.botgateway> botcli.exe --server http://127.0.0.1:8000 --token iH60kBgg5egN8lCWNQAUL3WGZkmIiPlx provider update --api-key 44dafe87-e3d5-43e9-ac82-5f0c16d28983 78ce8b69-a5dd-42c8-bb61-3ffa5416c9d1      
Provider updated successfully!
{
  "id": "78ce8b69-a5dd-42c8-bb61-3ffa5416c9d1",
  "name": "doubao",
  "api_type": "openai",
  "base_url": "https://ark.cn-beijing.volces.com/api/coding/v3",
  "is_active": true,
  "created_at": "2026-05-03T09:57:18.211125+00:00",
  "updated_at": "2026-05-03T11:03:08.937486"
}

实际上并没有保存就到数据库当中。

所有的命令行都要核查一下，确保没有错误。
