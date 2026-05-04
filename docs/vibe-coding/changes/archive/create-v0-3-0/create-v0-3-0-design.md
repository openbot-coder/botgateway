# 设计文档：create-v0-3-0

> 创建日期：2026-05-03
> 状态：待审查

## 设计状态

| 阶段 | 状态 | 日期 | 说明 |
|------|------|------|------|
| 设计编写 | ✅ | 2026-05-03 | |
| Agent 审查 | ⏳ | - | |
| 用户批准 | ⏳ | - | |

## 目标

实现 botgateway v0.3.0 版本，支持：
1. 下游客户使用 OpenAI 兼容接口连接 botgateway，转接到上游 OpenAI 兼容接口或 Anthropic 兼容接口
2. 上游采用 OpenAI 和 Anthropic 官方 SDK 请求
3. botcli 管理接口：provider、model、model group、router
4. fallback 路由（按优先级）和 weight-random 路由（按权重随机）
5. 错误重试与冷却控制
6. SQLite 存储，API Key 加密存储

## 背景

当前 botgateway v0.2.0 仅提供基础健康检查和状态接口，需要扩展为完整的 AI 网关，支持多模型供应商和多路由策略。

### 需求要点

- [x] **API-Key 认证**：OpenAI 兼容接口支持 API-Key 验证，无配置时允许匿名访问
- [x] **OpenAI 兼容接口**：支持 v1/chat/completions, v1/completions, v1/embeddings 等端点
- [x] **双协议支持**：转发到 OpenAI 兼容 API 和 Anthropic 兼容 API
- [x] **官方 SDK**：使用 openai-python 和 anthropic-python 官方 SDK
- [x] **管理接口**：botcli 支持 api-key、provider、model、model group 的增删改查
- [x] **模型参数配置**：Model 支持 temperature、top_p、timeout 等参数配置
- [x] **fallback 路由**：按优先级依次调用模型
- [x] **weight-random 路由**：按权重随机选择模型
- [x] **错误重试**：支持冷却控制和重新路由（路由配置合并到 ModelGroup）
- [x] **数据持久化**：SQLite 存储模型/路由配置
- [x] **安全存储**：API Key 使用 AES-256-GCM 加密

### 确认的设计方案

#### 1. 架构设计

```
                    ┌─────────────────────────────────────────────┐
                    │                  botgateway                 │
                    │                                             │
┌──────────┐        │  ┌─────────────────────────────────────┐  │
│  Client  │───────▶│  │         Auth Middleware              │  │
│          │        │  │  (API-Key Validation)                 │  │
└──────────┘        │  └───────────────┬─────────────────────┘  │
                   │                  │                        │
                   │  ┌───────────────▼─────────────────────┐  │
                   │  │       OpenAI API Proxy               │  │
                   │  │  /v1/chat/completions                │  │
                   │  │  /v1/completions                     │  │
                   │  │  /v1/embeddings                      │  │
                   │  └───────────────┬─────────────────────┘  │
                   │                  │                        │
                   │  ┌───────────────▼─────────────────────┐  │
                   │  │           Router                     │  │
                   │  │  (fallback / weight-random)          │  │
                   │  │  (from ModelGroup config)            │  │
                   │  └───────────────┬─────────────────────┘  │
                   │                  │                        │
                   │  ┌───────────────▼─────────────────────┐  │
                   │  │         Request Handler              │  │
                   │  │  - 错误处理  - 重试逻辑  - 冷却控制  │  │
                   │  └───────────────┬─────────────────────┘  │
                   │                  │                        │
                   │  ┌───────────────▼─────────────────────┐  │
                   │  │         SDK Adapter Layer           │  │
                   │  │  ┌─────────────┐  ┌─────────────┐  │  │
                   │  │  │ OpenAI SDK  │  │Anthropic SDK│  │  │
                   │  │  └─────────────┘  └─────────────┘  │  │
                   │  └───────────────────────────────────┘  │
                   │                                              │
                   │  ┌─────────────────────────────────────────┐  │
                   │  │           SQLite Database               │  │
                   │  │  ApiKey / Provider / Model / ModelGroup  │  │
                   │  │  - API Key (SHA-256)                    │  │
                   │  │  - Provider API Key (AES-256-GCM)       │  │
                   │  └─────────────────────────────────────────┘  │
                   │                                              │
                   │  ┌─────────────────────────────────────────┐  │
                   │  │         botcli Management CLI            │  │
                   │  │  api-key / provider / model / model-group │  │
                   │  └─────────────────────────────────────────┘  │
                   └─────────────────────────────────────────────┘
                                    │                    │
                                    ▼                    ▼
                          ┌─────────────────┐    ┌─────────────────┐
                          │  OpenAI API     │    │  Anthropic API  │
                          │  Compatible    │    │  Compatible    │
                          └─────────────────┘    └─────────────────┘
```

#### 2. 数据模型设计

**Provider（供应商）**
| 字段 | 类型 | 说明 |
|------|------|------|
| id | TEXT (UUID) | 主键 |
| name | TEXT | 供应商名称 (openai/anthropic/custom) |
| api_type | TEXT | api_type (openai/anthropic/azure) |
| base_url | TEXT | API 基础地址 |
| api_key_encrypted | TEXT | 加密后的 API Key |
| is_active | INTEGER | 是否启用 |
| created_at | TEXT | 创建时间 |
| updated_at | TEXT | 更新时间 |

**Model（模型）**
| 字段 | 类型 | 说明 |
|------|------|------|
| id | TEXT (UUID) | 主键 |
| provider_id | TEXT | 关联供应商 ID |
| name | TEXT | 模型名称 (gpt-4/claude-3-opus等) |
| model_type | TEXT | 模型类型 (chat/completion/embedding) |
| max_tokens | INTEGER | 最大 token 数 |
| temperature | REAL | 默认温度 |
| top_p | REAL | Top-p 采样参数 |
| timeout | INTEGER | 超时时间（秒） |
| extra_params | TEXT | JSON 格式额外参数 |
| is_active | INTEGER | 是否启用 |
| created_at | TEXT | 创建时间 |
| updated_at | TEXT | 更新时间 |

**ModelGroup（模型组）**
| 字段 | 类型 | 说明 |
|------|------|------|
| id | TEXT (UUID) | 主键 |
| name | TEXT | 组名称（作为路由标识） |
| description | TEXT | 描述 |
| routing_strategy | TEXT | 路由策略 (fallback/weight_random) |
| retry_count | INTEGER | 重试次数 |
| retry_delay | INTEGER | 重试延迟（秒） |
| cooldown_period | INTEGER | 冷却时间（秒） |
| is_active | INTEGER | 是否启用 |
| created_at | TEXT | 创建时间 |
| updated_at | TEXT | 更新时间 |

**ModelGroupMember（模型组成员）**
| 字段 | 类型 | 说明 |
|------|------|------|
| id | TEXT (UUID) | 主键 |
| group_id | TEXT | 模型组 ID |
| model_id | TEXT | 模型 ID |
| priority | INTEGER | 优先级 (fallback 用，数值越小优先级越高) |
| weight | INTEGER | 权重 (weight_random 用) |
| created_at | TEXT | 创建时间 |

**Router（路由配置）** → 已合并到 ModelGroup

**ApiKey（API Key 加密存储）**
| 字段 | 类型 | 说明 |
|------|------|------|
| provider_id | TEXT | 供应商 ID |
| api_key_encrypted | TEXT | AES-256-GCM 加密的 Key |
| key_nonce | TEXT | 加密 nonce |
| updated_at | TEXT | 更新时间 |

#### 3. API 端点设计

**OpenAI 兼容接口（Chat Completions）**

```
POST /v1/chat/completions        # Chat 对话
POST /v1/completions             # 文本补全（可选支持）
POST /v1/embeddings              # 向量嵌入（可选支持）
GET  /v1/models                  # 模型列表（可选支持）
```

**管理接口（需认证）**

```
# API-Key 管理
GET    /admin/api-keys            - 列出所有 API-Key
POST   /admin/api-keys            - 创建 API-Key（返回明文，仅显示一次）
GET    /admin/api-keys/{id}      - 获取 API-Key 详情
PUT    /admin/api-keys/{id}      - 更新 API-Key
DELETE /admin/api-keys/{id}      - 删除 API-Key

# Provider 管理
GET    /admin/providers           - 列出所有供应商
POST   /admin/providers           - 创建供应商
GET    /admin/providers/{id}      - 获取供应商详情
PUT    /admin/providers/{id}      - 更新供应商
DELETE /admin/providers/{id}      - 删除供应商

# Model 管理
GET    /admin/models              - 列出所有模型
POST   /admin/models              - 创建模型
GET    /admin/models/{id}         - 获取模型详情
PUT    /admin/models/{id}          - 更新模型
DELETE /admin/models/{id}          - 删除模型

# ModelGroup 管理（包含路由配置）
GET    /admin/model-groups        - 列出所有模型组
POST   /admin/model-groups        - 创建模型组（包含路由配置）
GET    /admin/model-groups/{id}   - 获取模型组详情
PUT    /admin/model-groups/{id}   - 更新模型组
DELETE /admin/model-groups/{id}   - 删除模型组
POST   /admin/model-groups/{id}/members - 添加模型组成员
DELETE /admin/model-groups/{id}/members/{member_id} - 删除模型组成员
```

**botcli 命令设计**

```
botcli api-key list
botcli api-key create --name <name>
botcli api-key update <id> --name <name>
botcli api-key delete <id>

botcli provider list
botcli provider add --name <name> --api-key <key> [--base-url <url>]
botcli provider update <id> [--name <name>] [--api-key <key>] [--base-url <url>]
botcli provider delete <id>

botcli model list [--provider-id <id>]
botcli model add --provider-id <id> --name <name> [--max-tokens <n>] [--temperature <t>] [--top-p <p>]
botcli model update <id> [--name <name>] [--max-tokens <n>] [--temperature <t>] [--top-p <p>]
botcli model delete <id>

botcli model-group list
botcli model-group add --name <name> --strategy <fallback|weight_random> [--retry-count <n>] [--retry-delay <n>] [--cooldown <n>]
botcli model-group update <id> [--name <name>] [--strategy <strategy>] [--retry-count <n>] [--retry-delay <n>] [--cooldown <n>]
botcli model-group add-member <group-id> --model-id <id> [--priority <n>] [--weight <n>]
botcli model-group remove-member <group-id> <member-id>
botcli model-group delete <id>
```

#### 4. 路由策略实现

**Fallback 路由**
```python
def fallback_route(group_members: list[ModelGroupMember]) -> Model:
    # 按 priority 升序排列（priority 越小优先级越高）
    sorted_members = sorted(group_members, key=lambda m: m.priority)
    for member in sorted_members:
        if not is_in_cooldown(member.model_id):
            return get_model(member.model_id)
    raise NoAvailableModelError("All models in cooldown")
```

**Weight-Random 路由**
```python
import random

def weight_random_route(group_members: list[ModelGroupMember]) -> Model:
    active_members = [m for m in group_members if not is_in_cooldown(m.model_id)]
    if not active_members:
        raise NoAvailableModelError("All models in cooldown")

    total_weight = sum(m.weight for m in active_members)
    rand = random.uniform(0, total_weight)
    cumulative = 0
    for member in active_members:
        cumulative += member.weight
        if rand <= cumulative:
            return get_model(member.model_id)
    return get_model(active_members[-1].model_id)
```

#### 5. 错误重试与冷却控制

```python
class ErrorRetryHandler:
    def __init__(self, model_group: ModelGroup):
        self.retry_count = model_group.retry_count
        self.retry_delay = model_group.retry_delay
        self.cooldown_period = model_group.cooldown_period
        self.cooldown_tracker: dict[str, datetime] = {}

    def handle_error(self, model_id: str, error: Exception):
        self.cooldown_tracker[model_id] = datetime.now()
        return len(self.cooldown_tracker) < self.retry_count

    def is_in_cooldown(self, model_id: str) -> bool:
        if model_id not in self.cooldown_tracker:
            return False
        elapsed = (datetime.now() - self.cooldown_tracker[model_id]).seconds
        return elapsed < self.cooldown_period
```

#### 6. API Key 加密

使用 AES-256-GCM 加密 API Key：
```python
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import hashlib
import os

class ApiKeyEncryptor:
    def __init__(self, master_key: bytes):  # 32 bytes for AES-256
        self.aesgcm = AESGCM(master_key)

    def encrypt(self, api_key: str) -> tuple[bytes, bytes]:
        nonce = os.urandom(12)  # 96-bit nonce for GCM
        ciphertext = self.aesgcm.encrypt(nonce, api_key.encode(), None)
        return ciphertext, nonce

    def decrypt(self, ciphertext: bytes, nonce: bytes) -> str:
        return self.aesgcm.decrypt(nonce, ciphertext, None).decode()


class ClientApiKeyValidator:
    """客户端 API-Key 验证（使用 SHA-256 哈希）"""

    @staticmethod
    def hash_key(api_key: str) -> str:
        return hashlib.sha256(api_key.encode()).hexdigest()

    def verify(self, api_key: str, stored_hash: str) -> bool:
        return self.hash_key(api_key) == stored_hash
```

#### 7. 目录结构

```
botgateway/
├── __init__.py
├── main.py
├── config.py
├── api/
│   ├── __init__.py
│   ├── auth.py              # 管理接口认证
│   ├── health.py
│   ├── chat.py              # OpenAI 兼容接口 + API-Key 验证
│   └── admin/               # 管理接口
│       ├── __init__.py
│       ├── api_keys.py      # 客户端 API-Key 管理
│       ├── providers.py
│       ├── models.py
│       └── model_groups.py
├── cli/
│   ├── __init__.py
│   ├── botcli.py
│   ├── botgateway.py
│   └── commands/            # botcli 子命令
│       ├── __init__.py
│       ├── api_key.py       # API-Key 管理
│       ├── provider.py
│       ├── model.py
│       └── model_group.py
├── core/
│   ├── __init__.py
│   ├── auth.py              # API-Key 认证中间件
│   ├── router.py            # 路由策略
│   ├── retry.py             # 重试与冷却
│   ├── sdk_adapter.py       # SDK 适配器
│   └── encryptor.py         # API Key 加密
├── db/
│   ├── __init__.py
│   ├── database.py          # SQLite 连接
│   ├── models.py            # 数据模型
│   └── migrations/          # 数据库迁移
└── tests/
    ├── ...
```

#### 8. 依赖变更

新增依赖：
```toml
[project.dependencies]
# 已有
fastapi = ">=0.100.0"
uvicorn = ">=0.20.0"
psutil = ">=5.9.0"
requests = ">=2.31.0"

# 新增
openai = ">=1.0.0"           # OpenAI 官方 SDK
anthropic = ">=0.20.0"       # Anthropic 官方 SDK
aiosqlite = ">=0.19.0"      # 异步 SQLite
cryptography = ">=41.0.0"   # 加密库
pydantic = ">=2.0.0"         # 数据验证
```

## 成功标准

- [ ] **API-Key 认证**：OpenAI 兼容接口支持 API-Key 验证，无配置时允许匿名访问
- [ ] **OpenAI 兼容接口**：支持所有 OpenAI API v1 端点（/v1/chat/completions, /v1/completions, /v1/embeddings 等）
- [ ] **双协议转发**：请求能正确转发到 OpenAI 和 Anthropic 兼容 API
- [ ] **SDK 集成**：使用官方 SDK 发起请求
- [ ] **CRUD 操作**：botcli 和管理 API 能完整操作 api-key、provider、model、model group
- [ ] **模型参数配置**：Model 支持 temperature、top_p、timeout 等参数配置
- [ ] **fallback 路由**：按优先级顺序尝试可用模型
- [ ] **weight-random 路由**：按权重随机选择模型
- [ ] **错误重试**：上游错误时自动重试，支持冷却控制
- [ ] **数据持久化**：SQLite 正确存储所有配置
- [ ] **API Key 加密**：API Key 以 AES-256-GCM 加密存储，客户端 API-Key 以 SHA-256 哈希存储
- [ ] **单元测试覆盖率**：核心模块覆盖率 ≥80%

## 范围

### 包含

1. **API-Key 认证机制**：客户端 API-Key 验证，支持匿名访问（无配置时）
2. **OpenAI 兼容接口**：支持 v1/chat/completions, v1/completions, v1/embeddings 等端点
3. OpenAI SDK 和 Anthropic SDK 集成
4. SQLite 数据库设计与实现
5. Provider/Model/ModelGroup CRUD API
6. botcli 命令行管理工具
7. Model 参数配置支持（temperature, top_p, timeout 等）
8. Fallback 和 Weight-Random 路由策略（路由配置合并到 ModelGroup）
9. 错误重试与冷却控制机制
10. API Key AES-256-GCM 加密

### 不包含

1. ~~用户认证和授权~~ → 已实现简单的 API-Key 认证
2. API Key 管理和计费（后续版本）
3. 模型调用监控和日志（后续版本）
4. Azure OpenAI 特定功能
5. 流式输出（Stream）支持（后续版本）

## 非功能性需求

| 需求 | 说明 |
|------|------|
| **性能** | 单次请求延迟增加 < 100ms |
| **可靠性** | 错误重试机制确保可用性 |
| **安全性** | API Key 必须加密存储 |
| **兼容性** | OpenAI API v1 兼容 |
| **可扩展性** | 支持添加新的路由策略 |

#### 9. API-Key 认证设计

**场景说明**
- 下游客户通过 OpenAI 兼容接口访问时，需要验证 API-Key
- API-Key 通过管理接口进行添加、修改、删除
- 如果未配置 API-Key 验证策略（即没有添加任何 API-Key），则允许匿名访问

**数据模型：ApiKey（客户端密钥）**

| 字段 | 类型 | 说明 |
|------|------|------|
| id | TEXT (UUID) | 主键 |
| name | TEXT | 密钥名称/标识 |
| api_key_hash | TEXT | SHA-256 哈希后的 API Key |
| is_active | INTEGER | 是否启用 |
| created_at | TEXT | 创建时间 |
| updated_at | TEXT | 更新时间 |

**认证流程**

```
请求 → 提取 API-Key → 检查是否配置了 API-Key
                               ↓
                    ┌──────────┴──────────┐
                    ↓                      ↓
            未配置（无密钥）          已配置（有密钥列表）
                    ↓                      ↓
                允许访问           在数据库中查找匹配
                                         ↓
                               ┌──────────┴──────────┐
                               ↓                      ↓
                          找到且启用               未找到或禁用
                               ↓                      ↓
                          允许访问              返回 401 Unauthorized
```

**OpenAI 兼容接口认证**

```
Authorization: Bearer <api-key>
```
或
```
X-API-Key: <api-key>
```

**管理接口扩展**

```
# API-Key 管理
GET    /admin/api-keys            - 列出所有 API-Key
POST   /admin/api-keys            - 创建 API-Key（返回明文，仅显示一次）
GET    /admin/api-keys/{id}      - 获取 API-Key 详情
PUT    /admin/api-keys/{id}      - 更新 API-Key
DELETE /admin/api-keys/{id}      - 删除 API-Key
```

**botcli 命令扩展**

```
botcli api-key list
botcli api-key create --name <name>        # 创建并显示 API-Key
botcli api-key update <id> --name <name>
botcli api-key delete <id>
```

## 备注

1. Master Key（用于加密 API Key）建议通过环境变量 `BOTGATEWAY_MASTER_KEY` 配置
2. 数据库默认路径：`~/.botgateway/botgateway.db`
3. 初始版本不实现复杂的模型映射和请求转换，直接透传标准字段
4. Anthropic API 需将 OpenAI 格式转换为 Anthropic 格式（system/user/messages）
5. 客户端 API-Key 使用 SHA-256 哈希存储，而非加密存储（用于验证）

## 变更记录

| 日期 | 阶段 | 操作 | 说明 |
|------|------|------|------|
| 2026-05-03 | 设计 | 创建 | v0.3.0 设计文档 |
| 2026-05-03 | 设计 | 修改 | 新增 API-Key 认证机制设计 |
| 2026-05-03 | 设计 | 修改 | Model 增加参数配置；Router 合并到 ModelGroup |
