# 设计文档：fix-v0-3-1-code-review

> 创建日期：2026-05-03
> 状态：待审查

## 设计状态

| 阶段 | 状态 | 日期 | 说明 |
|------|------|------|------|
| 设计编写 | ✅ | 2026-05-03 | |
| Agent 审查 | ⏳ | - | |
| 用户批准 | ⏳ | - | |

## 目标

修复 v0.3.0 Code Review 发现的问题，发布 v0.3.1 版本。重点修复：
1. 异步端点中的同步阻塞 I/O（生产环境致命问题）
2. 数据库类型错误和布尔值处理 Bug
3. 异常处理改进（可观测性）
4. 测试和 lint 修复
5. 弃用 API 更新

## 背景

v0.3.0 Code Review 发现 15 个问题，其中 4 个严重、5 个中等、6 个轻微。主要集中在：
- **性能**：同步 HTTP 客户端阻塞 FastAPI 事件循环
- **数据正确性**：数据库列类型错误、布尔值反序列化 Bug
- **可观测性**：异常被静默吞掉，审计日志丢失不可知
- **测试**：缺少 pytest-asyncio 依赖，7 个测试失败

### 需求要点

- [ ] **异步 I/O**：OpenAI/Anthropic SDK 改用 Async 客户端，router 改用 httpx.AsyncClient
- [ ] **数据库类型修复**：use_count TEXT→INTEGER，enabled 的 bool 反序列化修复
- [ ] **datetime 修复**：utcnow()→now(timezone.utc)
- [ ] **异常处理改进**：关键路径添加日志，区分认证错误和内部错误
- [ ] **测试修复**：添加 pytest-asyncio，修复 lint 警告
- [ ] **版本升级**：0.3.0→0.3.1

## 范围

### 包含

1. `core/sdk_adapter.py` - OpenAI/Anthropic 客户端改为 Async 版本
2. `core/router.py` - `requests` 库替换为 `httpx`，同步改异步
3. `api/chat.py` - `chat_completions` 端点内调用改为 `await`
4. `db/models.py` - `use_count` TEXT→INTEGER，`_now_iso` 修复
5. `db/database.py` - 建表语句 `use_count` 类型修复
6. `db/repositories.py` - `enabled` 布尔值正确反序列化
7. `api/auth.py` - 异常处理添加日志
8. `api/chat.py` - 审计日志异常处理添加日志
9. `api/admin/providers.py` - 审计日志异常处理添加日志
10. `pyproject.toml` - 版本号升级、添加 pytest-asyncio 和 httpx 依赖
11. `tests/` - lint 修复、health 测试修复
12. `.github/workflows/ci.yml` - 矩阵添加 Python 3.12/3.13

### 不包含

1. CLI 改为通过 API 调用（架构变更，留到后续版本）
2. SSE token 安全改进（需要 SSE 协议变更，留到后续版本）
3. `__init__.py` 过度暴露清理（API 变更，留到后续版本）
4. `PydanticRequest.extra` 命名冲突（命名变更，留到后续版本）

## 成功标准

- [ ] `uv run ruff check .` 零错误
- [ ] `uv run --extra dev pytest tests/ -v` 全部通过（115+ 测试）
- [ ] `uv build` 成功构建 botgateway-0.3.1
- [ ] 异步端点不再阻塞事件循环
- [ ] enabled=False 能正确禁用模型
- [ ] use_count 能正确递增
- [ ] 无 DeprecationWarning

## 影响范围

| 文件 | 变更类型 | 风险 |
|------|---------|------|
| core/sdk_adapter.py | 重构（同步→异步） | 高 |
| core/router.py | 重构（同步→异步） | 高 |
| api/chat.py | 修改（await 调用） | 中 |
| db/models.py | 修复（类型+弃用） | 低 |
| db/database.py | 修复（建表语句） | 低 |
| db/repositories.py | 修复（bool 处理） | 低 |
| api/auth.py | 修改（日志） | 低 |
| api/admin/providers.py | 修改（日志） | 低 |
| pyproject.toml | 修改（版本+依赖） | 低 |
| tests/ | 修改（lint+async） | 低 |
| .github/workflows/ci.yml | 修改（矩阵） | 低 |

## 变更记录

| 日期 | 阶段 | 操作 | 说明 |
|------|------|------|------|
| 2026-05-03 | 设计 | 创建 | v0.3.1 Code Review 修复设计文档 |
