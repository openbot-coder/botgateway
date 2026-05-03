from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone


def generate_id() -> str:
    return str(uuid.uuid4())


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _parse_bool(value) -> bool:
    """Parse a boolean value from various input types.

    Handles integers (0/1), strings ("true"/"false"/"0"/"1"), and actual bools.
    Fixes the bug where bool("false") returns True.
    """
    if isinstance(value, bool):
        return value
    if isinstance(value, int):
        return bool(value)
    if isinstance(value, str):
        return value.lower() in ("true", "1", "yes")
    return bool(value)


@dataclass
class Provider:
    id: str
    name: str
    api_type: str = "openai"
    base_url: str | None = None
    api_key_encrypted: str | None = None
    key_nonce: str | None = None
    is_active: bool = True
    created_at: str = field(default_factory=now_iso)
    updated_at: str = field(default_factory=now_iso)

    @classmethod
    def create(cls, name: str, api_type: str = "openai",
               base_url: str | None = None) -> Provider:
        return cls(id=generate_id(), name=name, api_type=api_type, base_url=base_url)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "api_type": self.api_type,
            "base_url": self.base_url,
            "is_active": self.is_active,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> Provider:
        return cls(
            id=data["id"],
            name=data["name"],
            api_type=data.get("api_type", "openai"),
            base_url=data.get("base_url"),
            api_key_encrypted=data.get("api_key_encrypted"),
            key_nonce=data.get("key_nonce"),
            is_active=_parse_bool(data.get("is_active", 1)),
            created_at=data["created_at"],
            updated_at=data["updated_at"],
        )


@dataclass
class Model:
    id: str
    provider_id: str
    name: str
    model_type: str = "chat"
    max_tokens: int | None = None
    temperature: float = 0.7
    top_p: float = 1.0
    timeout: int = 60
    extra_params: str | None = None
    is_active: bool = True
    created_at: str = field(default_factory=now_iso)
    updated_at: str = field(default_factory=now_iso)

    @classmethod
    def create(cls, provider_id: str, name: str, model_type: str = "chat",
               max_tokens: int | None = None, temperature: float = 0.7,
               top_p: float = 1.0, timeout: int = 60,
               extra_params: dict | None = None) -> Model:
        return cls(
            id=generate_id(),
            provider_id=provider_id,
            name=name,
            model_type=model_type,
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p,
            timeout=timeout,
            extra_params=json.dumps(extra_params) if extra_params else None,
        )

    def get_extra_params(self) -> dict | None:
        if self.extra_params:
            return json.loads(self.extra_params)
        return None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "provider_id": self.provider_id,
            "name": self.name,
            "model_type": self.model_type,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "top_p": self.top_p,
            "timeout": self.timeout,
            "extra_params": self.get_extra_params(),
            "is_active": self.is_active,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> Model:
        return cls(
            id=data["id"],
            provider_id=data["provider_id"],
            name=data["name"],
            model_type=data.get("model_type", "chat"),
            max_tokens=data.get("max_tokens"),
            temperature=data.get("temperature", 0.7),
            top_p=data.get("top_p", 1.0),
            timeout=data.get("timeout", 60),
            extra_params=data.get("extra_params"),
            is_active=_parse_bool(data.get("is_active", 1)),
            created_at=data["created_at"],
            updated_at=data["updated_at"],
        )


@dataclass
class ModelGroup:
    id: str
    name: str
    description: str | None = None
    routing_strategy: str = "fallback"
    retry_count: int = 3
    retry_delay: int = 1
    cooldown_period: int = 60
    use_count: int = 0
    is_active: bool = True
    created_at: str = field(default_factory=now_iso)
    updated_at: str = field(default_factory=now_iso)

    @classmethod
    def create(cls, name: str, description: str | None = None,
               routing_strategy: str = "fallback", retry_count: int = 3,
               retry_delay: int = 1, cooldown_period: int = 60) -> ModelGroup:
        return cls(
            id=generate_id(),
            name=name,
            description=description,
            routing_strategy=routing_strategy,
            retry_count=retry_count,
            retry_delay=retry_delay,
            cooldown_period=cooldown_period,
        )

    def increment_use_count(self) -> None:
        """Increment the use_count by 1."""
        self.use_count += 1

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "routing_strategy": self.routing_strategy,
            "retry_count": self.retry_count,
            "retry_delay": self.retry_delay,
            "cooldown_period": self.cooldown_period,
            "use_count": self.use_count,
            "is_active": self.is_active,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> ModelGroup:
        return cls(
            id=data["id"],
            name=data["name"],
            description=data.get("description"),
            routing_strategy=data.get("routing_strategy", "fallback"),
            retry_count=data.get("retry_count", 3),
            retry_delay=data.get("retry_delay", 1),
            cooldown_period=data.get("cooldown_period", 60),
            use_count=int(data.get("use_count", 0)),
            is_active=_parse_bool(data.get("is_active", 1)),
            created_at=data["created_at"],
            updated_at=data["updated_at"],
        )


@dataclass
class ModelGroupMember:
    id: str
    group_id: str
    model_id: str
    priority: int = 0
    weight: int = 1
    created_at: str = field(default_factory=now_iso)

    @classmethod
    def create(cls, group_id: str, model_id: str,
               priority: int = 0, weight: int = 1) -> ModelGroupMember:
        return cls(
            id=generate_id(),
            group_id=group_id,
            model_id=model_id,
            priority=priority,
            weight=weight,
        )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "group_id": self.group_id,
            "model_id": self.model_id,
            "priority": self.priority,
            "weight": self.weight,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> ModelGroupMember:
        return cls(
            id=data["id"],
            group_id=data["group_id"],
            model_id=data["model_id"],
            priority=data.get("priority", 0),
            weight=data.get("weight", 1),
            created_at=data["created_at"],
        )


@dataclass
class ApiKey:
    id: str
    name: str
    api_key_hash: str
    is_active: bool = True
    created_at: str = field(default_factory=now_iso)
    updated_at: str = field(default_factory=now_iso)

    @classmethod
    def create(cls, name: str, api_key_hash: str) -> ApiKey:
        return cls(id=generate_id(), name=name, api_key_hash=api_key_hash)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "api_key_hash": self.api_key_hash,
            "is_active": self.is_active,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> ApiKey:
        return cls(
            id=data["id"],
            name=data["name"],
            api_key_hash=data["api_key_hash"],
            is_active=_parse_bool(data.get("is_active", 1)),
            created_at=data["created_at"],
            updated_at=data["updated_at"],
        )


@dataclass
class McpTool:
    id: str
    name: str
    description: str | None = None
    endpoint_url: str | None = None
    tool_schema: str | None = None
    is_active: bool = True
    created_at: str = field(default_factory=now_iso)
    updated_at: str = field(default_factory=now_iso)

    @classmethod
    def create(cls, name: str, description: str | None = None,
               endpoint_url: str | None = None,
               tool_schema: dict | None = None) -> McpTool:
        return cls(
            id=generate_id(),
            name=name,
            description=description,
            endpoint_url=endpoint_url,
            tool_schema=json.dumps(tool_schema) if tool_schema else None,
        )

    def get_tool_schema(self) -> dict | None:
        if self.tool_schema:
            return json.loads(self.tool_schema)
        return None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "endpoint_url": self.endpoint_url,
            "tool_schema": self.get_tool_schema(),
            "is_active": self.is_active,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> McpTool:
        return cls(
            id=data["id"],
            name=data["name"],
            description=data.get("description"),
            endpoint_url=data.get("endpoint_url"),
            tool_schema=data.get("tool_schema"),
            is_active=_parse_bool(data.get("is_active", 1)),
            created_at=data["created_at"],
            updated_at=data["updated_at"],
        )


@dataclass
class McpServer:
    id: str
    name: str
    transport: str = "stdio"  # stdio, sse, http
    command: str | None = None
    args: str | None = None  # JSON array of arguments
    url: str | None = None
    env: str | None = None  # JSON object of environment variables
    description: str | None = None
    is_active: bool = True
    created_at: str = field(default_factory=now_iso)
    updated_at: str = field(default_factory=now_iso)

    @classmethod
    def create(cls, name: str, transport: str = "stdio",
               command: str | None = None, args: list[str] | None = None,
               url: str | None = None, env: dict | None = None,
               description: str | None = None) -> McpServer:
        return cls(
            id=generate_id(),
            name=name,
            transport=transport,
            command=command,
            args=json.dumps(args) if args else None,
            url=url,
            env=json.dumps(env) if env else None,
            description=description,
        )

    def get_args(self) -> list[str] | None:
        if self.args:
            return json.loads(self.args)
        return None

    def get_env(self) -> dict | None:
        if self.env:
            return json.loads(self.env)
        return None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "transport": self.transport,
            "command": self.command,
            "args": self.get_args(),
            "url": self.url,
            "env": self.get_env(),
            "description": self.description,
            "is_active": self.is_active,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> McpServer:
        return cls(
            id=data["id"],
            name=data["name"],
            transport=data.get("transport", "stdio"),
            command=data.get("command"),
            args=data.get("args"),
            url=data.get("url"),
            env=data.get("env"),
            description=data.get("description"),
            is_active=_parse_bool(data.get("is_active", 1)),
            created_at=data["created_at"],
            updated_at=data["updated_at"],
        )
