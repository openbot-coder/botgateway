# 设计文档：create-v0-2-0

> 创建日期：2026-05-02
> 状态：待填充

## 设计状态

| 阶段 | 状态 | 日期 | 说明 |
|------|------|------|------|
| 设计编写 | ✅ | 2026-05-02 | |
| Agent 审查 | ⏳ | - | |
| 用户批准 | ⏳ | - | |

## 目标

创建v0.2.0版本：1)创建botgateway和botcli命令；2)提供管理token认证服务；3)提供health健康状态查询接口

## 背景

当前项目处于 v0.1.0 版本，仅有基本的项目结构。需要升级到 v0.2.0，添加 CLI 命令、管理 token 认证和健康检查功能。

### 需求要点

- [x] 创建 `botgateway` 命令：启动 FastAPI 服务
- [x] 创建 `botcli` 命令：管理 botgateway 服务
- [x] 管理 token 认证：所有管理接口必须验证 token
- [x] Health 健康状态查询接口：服务器时间、内存占用、CPU 占用、服务接口状态

### 确认的设计方案

#### 1. CLI 命令设计（使用 argparse 标准库）

**botgateway 命令**：
- 启动 FastAPI 服务
- 参数：`--host`、`--port`、`--config`（配置文件路径）
- 配置文件格式：JSON，包含 `management_token` 等配置

**botcli 命令**：
- 管理子命令：`health`、`status`、`config`
- 参数：`--server`（服务地址）、`--token`（管理 token，或通过环境变量 `BOTGATEWAY_TOKEN`）

#### 2. 管理 Token 认证

- **服务端**：通过 JSON 配置文件读取 `management_token`
- **客户端**：通过命令行参数 `--token` 或环境变量 `BOTGATEWAY_TOKEN` 传入
- **验证方式**：请求头 `Authorization: Bearer <token>`

#### 3. Health 接口设计

**GET /health**（需要认证）：
- 返回服务器时间、内存占用、CPU 占用、磁盘使用情况、网络连接数、进程信息、系统运行时间
- 包含所有注册的 API 接口及其状态
- 验证失败返回 404 Not Found

#### 4. 项目结构

```
botgateway/
├── __init__.py
├── main.py          # FastAPI 主应用
├── cli/
│   ├── __init__.py
│   ├── botgateway.py   # botgateway 命令实现
│   └── botcli.py       # botcli 命令实现
├── api/
│   ├── __init__.py
│   ├── health.py       # 健康检查接口
│   └── auth.py         # 认证中间件
└── config.py        # 配置管理
```

### 待确认事项

- [x] CLI 库选择：argparse
- [x] Token 存储：服务端 JSON 配置，客户端环境变量/命令行
- [x] Health 接口状态：列出所有注册的 API 接口

## 成功标准

- [x] 标准1：`botgateway` 命令能启动 FastAPI 服务 ✅
- [x] 标准2：`botcli` 命令能通过 token 认证查询健康状态 ✅
- [x] 标准3：管理接口正确验证 token，验证失败返回 404 ✅
- [x] 标准4：Health 接口返回服务器时间、内存、CPU 和接口状态信息 ✅

## 范围

### 包含

- 创建 `botgateway` 命令启动服务
- 创建 `botcli` 命令管理服务
- 实现管理 token 认证中间件
- 实现 Health 健康检查接口

### 不包含

- 不支持数据库存储 token
- 不支持多用户权限管理
- 不支持复杂的配置热更新

## 非功能性需求

- 性能：Health 接口响应时间 < 100ms
- 安全：token 验证使用 Bearer 认证方式
- 兼容性：支持 Python 3.10+

## 备注

- 配置文件默认路径：`~/.botgateway/config.json`
- 环境变量：`BOTGATEWAY_TOKEN` 用于 botcli 认证
