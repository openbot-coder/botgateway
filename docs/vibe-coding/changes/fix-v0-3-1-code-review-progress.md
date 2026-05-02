# 进度：fix-v0-3-1-code-review

> 版本：0.3.1
> 分支：develop
> 创建日期：2026-05-03

## 阶段状态

| 阶段 | 状态 | 日期 | 说明 |
|------|------|------|------|
| 阶段1：需求分析 | ✅ | 2026-05-03 | 设计文档已批准 |
| 阶段2：任务拆解 | 🔄 | 2026-05-03 | 进行中 |
| 阶段3：代码执行 | ⏳ | - | |
| 阶段4：测试验证 | ⏳ | - | |
| 阶段5：需求归档 | ⏳ | - | |

## 任务清单

| 序号 | 任务名称 | 功能点数 | 状态 |
|------|---------|---------|------|
| 1 | 异步化 SDK 适配器 | 4 | ⏳ |
| 2 | 异步化路由器 | 4 | ⏳ |
| 3 | 异步化 chat 端点 | 2 | ⏳ |
| 4 | 数据库类型修复 | 4 | ⏳ |
| 5 | 异常处理改进 | 3 | ⏳ |
| 6 | 测试和 CI 修复 | 4 | ⏳ |
| 7 | 版本升级 | 2 | ⏳ |

---

### Task 1：异步化 SDK 适配器（core/sdk_adapter.py）
- [ ] 将 OpenAI 客户端从 `OpenAI` 改为 `AsyncOpenAI`
- [ ] 将 Anthropic 客户端从 `Anthropic` 改为 `AsyncAnthropic`
- [ ] 将 `send_request` 方法改为 `async def`
- [ ] 更新相关测试

### Task 2：异步化路由器（core/router.py）
- [ ] 将 `requests` 替换为 `httpx.AsyncClient`
- [ ] 将 `_do_send_request` 和 `send_request` 改为 `async def`
- [ ] 添加 httpx 依赖到 pyproject.toml
- [ ] 更新相关测试

### Task 3：异步化 chat 端点（api/chat.py）
- [ ] `chat_completions` 中的路由调用改为 `await`
- [ ] 更新 `model_extra_params` 和 `build_body_with_extra_params` 的调用链

### Task 4：数据库类型修复（db/）
- [ ] `models.py`：`use_count TEXT` → `use_count INTEGER DEFAULT 0`
- [ ] `database.py`：建表语句同步修改
- [ ] `models.py`：`_now_iso` 使用 `datetime.now(timezone.utc)` 替代 `utcnow()`
- [ ] `repositories.py`：修复 `enabled` 布尔值反序列化

### Task 5：异常处理改进（api/）
- [ ] `auth.py`：添加 logger，认证异常记录日志
- [ ] `chat.py`：审计日志失败记录日志
- [ ] `admin/providers.py`：审计日志失败记录日志

### Task 6：测试和 CI 修复
- [ ] 添加 `pytest-asyncio` 到 dev 依赖
- [ ] 修复 lint 警告（import 排序、未使用导入、换行）
- [ ] 修复 `test_health.py` 的异步测试
- [ ] CI 矩阵添加 Python 3.12/3.13

### Task 7：版本升级
- [ ] `pyproject.toml`：版本号 0.3.0 → 0.3.1
- [ ] `__init__.py`：版本号 0.3.0 → 0.3.1
