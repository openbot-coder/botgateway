from __future__ import annotations

from .database import Database
from .models import ApiKey, Model, ModelGroup, ModelGroupMember, Provider


class ProviderRepository:
    def __init__(self, db: Database):
        self.db = db

    async def create(self, provider: Provider) -> Provider:
        await self.db.execute(
            """INSERT INTO providers
            (id, name, api_type, base_url, api_key_encrypted,
            key_nonce, is_active, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (provider.id, provider.name, provider.api_type, provider.base_url,
             provider.api_key_encrypted, provider.key_nonce,
             int(provider.is_active), provider.created_at, provider.updated_at)
        )
        await self.db.commit()
        return provider

    async def get_by_id(self, id: str) -> Provider | None:
        row = await self.db.fetchone(
            "SELECT * FROM providers WHERE id = ?", (id,)
        )
        return Provider.from_dict(row) if row else None

    async def get_all(self, active_only: bool = True) -> list[Provider]:
        sql = "SELECT * FROM providers"
        if active_only:
            sql += " WHERE is_active = 1"
        rows = await self.db.fetchall(sql)
        return [Provider.from_dict(row) for row in rows]

    async def update(self, provider: Provider) -> Provider:
        await self.db.execute(
            """UPDATE providers SET name = ?, api_type = ?, base_url = ?,
            api_key_encrypted = ?, key_nonce = ?,
            is_active = ?, updated_at = ? WHERE id = ?""",
            (provider.name, provider.api_type, provider.base_url,
             provider.api_key_encrypted, provider.key_nonce,
             int(provider.is_active), provider.updated_at, provider.id)
        )
        await self.db.commit()
        return provider

    async def delete(self, id: str) -> bool:
        await self.db.execute("DELETE FROM providers WHERE id = ?", (id,))
        await self.db.commit()
        return True


class ModelRepository:
    def __init__(self, db: Database):
        self.db = db

    async def create(self, model: Model) -> Model:
        await self.db.execute(
            """INSERT INTO models
            (id, provider_id, name, model_type, max_tokens, temperature,
            top_p, timeout, extra_params, is_active, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (model.id, model.provider_id, model.name, model.model_type,
             model.max_tokens, model.temperature, model.top_p,
             model.timeout, model.extra_params,
             int(model.is_active), model.created_at, model.updated_at)
        )
        await self.db.commit()
        return model

    async def get_by_id(self, id: str) -> Model | None:
        row = await self.db.fetchone(
            "SELECT * FROM models WHERE id = ?", (id,)
        )
        return Model.from_dict(row) if row else None

    async def get_all(
        self, provider_id: str | None = None, active_only: bool = True
    ) -> list[Model]:
        sql = "SELECT * FROM models WHERE 1=1"
        params = []
        if provider_id:
            sql += " AND provider_id = ?"
            params.append(provider_id)
        if active_only:
            sql += " AND is_active = 1"
        rows = await self.db.fetchall(sql, tuple(params))
        return [Model.from_dict(row) for row in rows]

    async def update(self, model: Model) -> Model:
        await self.db.execute(
            """UPDATE models SET provider_id = ?, name = ?, model_type = ?,
            max_tokens = ?, temperature = ?, top_p = ?, timeout = ?,
            extra_params = ?, is_active = ?, updated_at = ? WHERE id = ?""",
            (model.provider_id, model.name, model.model_type, model.max_tokens,
             model.temperature, model.top_p, model.timeout, model.extra_params,
             int(model.is_active), model.updated_at, model.id)
        )
        await self.db.commit()
        return model

    async def delete(self, id: str) -> bool:
        await self.db.execute("DELETE FROM models WHERE id = ?", (id,))
        await self.db.commit()
        return True


class ModelGroupRepository:
    def __init__(self, db: Database):
        self.db = db

    async def create(self, group: ModelGroup) -> ModelGroup:
        await self.db.execute(
            """INSERT INTO model_groups
            (id, name, description, routing_strategy, retry_count,
            retry_delay, cooldown_period, is_active, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (group.id, group.name, group.description, group.routing_strategy,
             group.retry_count, group.retry_delay, group.cooldown_period,
             int(group.is_active), group.created_at, group.updated_at)
        )
        await self.db.commit()
        return group

    async def get_by_id(self, id: str) -> ModelGroup | None:
        row = await self.db.fetchone(
            "SELECT * FROM model_groups WHERE id = ?", (id,)
        )
        return ModelGroup.from_dict(row) if row else None

    async def get_by_name(self, name: str) -> ModelGroup | None:
        row = await self.db.fetchone(
            "SELECT * FROM model_groups WHERE name = ?", (name,)
        )
        return ModelGroup.from_dict(row) if row else None

    async def get_all(self, active_only: bool = True) -> list[ModelGroup]:
        sql = "SELECT * FROM model_groups"
        if active_only:
            sql += " WHERE is_active = 1"
        rows = await self.db.fetchall(sql)
        return [ModelGroup.from_dict(row) for row in rows]

    async def update(self, group: ModelGroup) -> ModelGroup:
        await self.db.execute(
            """UPDATE model_groups SET name = ?, description = ?,
            routing_strategy = ?, retry_count = ?, retry_delay = ?,
            cooldown_period = ?, is_active = ?, updated_at = ? WHERE id = ?""",
            (group.name, group.description, group.routing_strategy,
             group.retry_count, group.retry_delay, group.cooldown_period,
             int(group.is_active), group.updated_at, group.id)
        )
        await self.db.commit()
        return group

    async def delete(self, id: str) -> bool:
        await self.db.execute("DELETE FROM model_groups WHERE id = ?", (id,))
        await self.db.commit()
        return True


class ModelGroupMemberRepository:
    def __init__(self, db: Database):
        self.db = db

    async def create(self, member: ModelGroupMember) -> ModelGroupMember:
        await self.db.execute(
            """INSERT INTO model_group_members
            (id, group_id, model_id, priority, weight, created_at)
            VALUES (?, ?, ?, ?, ?, ?)""",
            (member.id, member.group_id, member.model_id,
             member.priority, member.weight, member.created_at)
        )
        await self.db.commit()
        return member

    async def get_by_id(self, id: str) -> ModelGroupMember | None:
        row = await self.db.fetchone(
            "SELECT * FROM model_group_members WHERE id = ?", (id,)
        )
        return ModelGroupMember.from_dict(row) if row else None

    async def get_by_group_id(self, group_id: str) -> list[ModelGroupMember]:
        rows = await self.db.fetchall(
            "SELECT * FROM model_group_members WHERE group_id = ? ORDER BY priority",
            (group_id,)
        )
        return [ModelGroupMember.from_dict(row) for row in rows]

    async def delete(self, id: str) -> bool:
        await self.db.execute(
            "DELETE FROM model_group_members WHERE id = ?", (id,)
        )
        await self.db.commit()
        return True

    async def delete_by_group_id(self, group_id: str) -> bool:
        await self.db.execute(
            "DELETE FROM model_group_members WHERE group_id = ?", (group_id,)
        )
        await self.db.commit()
        return True


class ApiKeyRepository:
    def __init__(self, db: Database):
        self.db = db

    async def create(self, api_key: ApiKey) -> ApiKey:
        await self.db.execute(
            """INSERT INTO api_keys
            (id, name, api_key_hash, is_active, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)""",
            (api_key.id, api_key.name, api_key.api_key_hash,
             int(api_key.is_active), api_key.created_at, api_key.updated_at)
        )
        await self.db.commit()
        return api_key

    async def get_by_id(self, id: str) -> ApiKey | None:
        row = await self.db.fetchone(
            "SELECT * FROM api_keys WHERE id = ?", (id,)
        )
        return ApiKey.from_dict(row) if row else None

    async def get_by_hash(self, api_key_hash: str) -> ApiKey | None:
        row = await self.db.fetchone(
            "SELECT * FROM api_keys WHERE api_key_hash = ? AND is_active = 1",
            (api_key_hash,)
        )
        return ApiKey.from_dict(row) if row else None

    async def get_all(self, active_only: bool = True) -> list[ApiKey]:
        sql = "SELECT * FROM api_keys"
        if active_only:
            sql += " WHERE is_active = 1"
        rows = await self.db.fetchall(sql)
        return [ApiKey.from_dict(row) for row in rows]

    async def update(self, api_key: ApiKey) -> ApiKey:
        await self.db.execute(
            """UPDATE api_keys SET name = ?, api_key_hash = ?,
            is_active = ?, updated_at = ? WHERE id = ?""",
            (api_key.name, api_key.api_key_hash,
             int(api_key.is_active), api_key.updated_at, api_key.id)
        )
        await self.db.commit()
        return api_key

    async def delete(self, id: str) -> bool:
        await self.db.execute("DELETE FROM api_keys WHERE id = ?", (id,))
        await self.db.commit()
        return True

    async def count(self) -> int:
        row = await self.db.fetchone("SELECT COUNT(*) as count FROM api_keys")
        return row["count"] if row else 0
