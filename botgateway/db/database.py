from __future__ import annotations

import os
from pathlib import Path

import aiosqlite


class Database:
    _instance: Database | None = None
    _db_path: str

    def __init__(self, db_path: str | None = None):
        if db_path is None:
            db_path = os.environ.get(
                "BOTGATEWAY_DB_PATH",
                str(Path.home() / ".botgateway" / "botgateway.db")
            )
        self._db_path = db_path
        self._conn: aiosqlite.Connection | None = None

    @classmethod
    def get_instance(cls, db_path: str | None = None) -> Database:
        if cls._instance is None:
            cls._instance = cls(db_path)
        return cls._instance

    @classmethod
    def get_database(cls, db_path: str | None = None) -> Database:
        return cls.get_instance(db_path)

    async def connect(self) -> aiosqlite.Connection:
        if self._conn is None:
            Path(self._db_path).parent.mkdir(parents=True, exist_ok=True)
            self._conn = await aiosqlite.connect(self._db_path)
            self._conn.row_factory = aiosqlite.Row
            await self._conn.execute("PRAGMA foreign_keys = ON")
        return self._conn

    async def close(self) -> None:
        if self._conn:
            await self._conn.close()
            self._conn = None

    async def execute(self, sql: str, parameters: tuple = ()) -> aiosqlite.Cursor:
        conn = await self.connect()
        return await conn.execute(sql, parameters)

    async def executemany(self, sql: str, parameters: list) -> aiosqlite.Cursor:
        conn = await self.connect()
        return await conn.executemany(sql, parameters)

    async def commit(self) -> None:
        if self._conn:
            await self._conn.commit()

    async def rollback(self) -> None:
        if self._conn:
            await self._conn.rollback()

    async def fetchone(self, sql: str, parameters: tuple = ()) -> dict | None:
        cursor = await self.execute(sql, parameters)
        row = await cursor.fetchone()
        return dict(row) if row else None

    async def fetchall(self, sql: str, parameters: tuple = ()) -> list[dict]:
        cursor = await self.execute(sql, parameters)
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]

    async def init_schema(self) -> None:
        schema = """
        CREATE TABLE IF NOT EXISTS providers (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            api_type TEXT NOT NULL DEFAULT 'openai',
            base_url TEXT,
            api_key_encrypted TEXT,
            key_nonce TEXT,
            is_active INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS models (
            id TEXT PRIMARY KEY,
            provider_id TEXT NOT NULL,
            name TEXT NOT NULL,
            model_type TEXT NOT NULL DEFAULT 'chat',
            max_tokens INTEGER,
            temperature REAL DEFAULT 0.7,
            top_p REAL DEFAULT 1.0,
            timeout INTEGER DEFAULT 60,
            extra_params TEXT,
            is_active INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY (provider_id) REFERENCES providers(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS model_groups (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL UNIQUE,
            description TEXT,
            routing_strategy TEXT NOT NULL DEFAULT 'fallback',
            retry_count INTEGER NOT NULL DEFAULT 3,
            retry_delay INTEGER NOT NULL DEFAULT 1,
            cooldown_period INTEGER NOT NULL DEFAULT 60,
            use_count INTEGER NOT NULL DEFAULT 0,
            is_active INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS model_group_members (
            id TEXT PRIMARY KEY,
            group_id TEXT NOT NULL,
            model_id TEXT NOT NULL,
            priority INTEGER NOT NULL DEFAULT 0,
            weight INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL,
            FOREIGN KEY (group_id) REFERENCES model_groups(id) ON DELETE CASCADE,
            FOREIGN KEY (model_id) REFERENCES models(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS api_keys (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            api_key_hash TEXT NOT NULL UNIQUE,
            is_active INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS mcp_tools (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT,
            endpoint_url TEXT,
            tool_schema TEXT,
            is_active INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS mcp_servers (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            transport TEXT NOT NULL DEFAULT 'stdio',
            command TEXT,
            args TEXT,
            url TEXT,
            env TEXT,
            description TEXT,
            is_active INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );

        CREATE INDEX IF NOT EXISTS idx_models_provider ON models(provider_id);
        CREATE INDEX IF NOT EXISTS idx_model_group_members_group ON model_group_members(group_id);
        CREATE INDEX IF NOT EXISTS idx_model_group_members_model ON model_group_members(model_id);
        CREATE INDEX IF NOT EXISTS idx_api_keys_hash ON api_keys(api_key_hash);
        CREATE INDEX IF NOT EXISTS idx_mcp_tools_name ON mcp_tools(name);
        CREATE INDEX IF NOT EXISTS idx_mcp_servers_name ON mcp_servers(name);

        CREATE TABLE IF NOT EXISTS operation_logs (
            id TEXT PRIMARY KEY,
            table_name TEXT NOT NULL,
            operation_type TEXT NOT NULL,
            record_id TEXT,
            details TEXT,
            created_at TEXT NOT NULL
        );

        CREATE INDEX IF NOT EXISTS idx_operation_logs_table ON operation_logs(table_name);
        CREATE INDEX IF NOT EXISTS idx_operation_logs_record ON operation_logs(record_id);
        """
        conn = await self.connect()
        await conn.executescript(schema)
        await self.commit()
