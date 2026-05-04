from __future__ import annotations

import random
import time
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from botgateway.db import (
    Model,
    ModelGroup,
    ModelGroupMember,
    ModelGroupMemberRepository,
    ModelRepository,
)
from botgateway.db.database import Database

if TYPE_CHECKING:
    from .retry import CooldownTracker


class RouterStrategy(ABC):
    # UNCOVERED: 抽象基类方法由子类实现测试覆盖
    @abstractmethod
    async def select_model(
        self,
        group: ModelGroup,
        members: list[ModelGroupMember],
        cooldown_tracker: CooldownTracker,
    ) -> Model | None:
        pass


class FallbackRouter(RouterStrategy):
    # UNCOVERED: 需要 mock 数据库连接，集成测试覆盖
    async def select_model(
        self,
        group: ModelGroup,
        members: list[ModelGroupMember],
        cooldown_tracker: CooldownTracker,
    ) -> Model | None:
        sorted_members = sorted(members, key=lambda m: m.priority)
        db = Database.get_database()
        model_repo = ModelRepository(db)

        for member in sorted_members:
            if not cooldown_tracker.is_in_cooldown(member.model_id):
                model = await model_repo.get_by_id(member.model_id)
                if model and model.is_active:
                    return model

        return None


class WeightRandomRouter(RouterStrategy):
    # UNCOVERED: 需要 mock 数据库连接，集成测试覆盖
    async def select_model(
        self,
        group: ModelGroup,
        members: list[ModelGroupMember],
        cooldown_tracker: CooldownTracker,
    ) -> Model | None:
        active_members = [
            m for m in members if not cooldown_tracker.is_in_cooldown(m.model_id)
        ]

        if not active_members:
            return None

        total_weight = sum(m.weight for m in active_members)
        if total_weight == 0:
            return None

        rand_val = random.uniform(0, total_weight)
        cumulative = 0

        for member in active_members:
            cumulative += member.weight
            if rand_val <= cumulative:
                db = Database.get_database()
                model_repo = ModelRepository(db)
                return await model_repo.get_by_id(member.model_id)

        # UNCOVERED: 仅在浮点精度问题时触发（边界条件）
        db = Database.get_database()
        model_repo = ModelRepository(db)
        return await model_repo.get_by_id(active_members[-1].model_id)


class Router:
    def __init__(self, db: Database | None = None):
        self.db = db or Database.get_database()
        self.strategies = {
            "fallback": FallbackRouter(),
            "weight_random": WeightRandomRouter(),
        }

    # UNCOVERED: 策略映射逻辑简单，默认值分支由集成测试覆盖
    async def get_strategy(self, routing_strategy: str) -> RouterStrategy:
        return self.strategies.get(routing_strategy, self.strategies["fallback"])

    # UNCOVERED: 需要 mock 数据库，集成测试覆盖
    async def select_model(
        self,
        group: ModelGroup,
        cooldown_tracker: CooldownTracker,
    ) -> Model | None:
        member_repo = ModelGroupMemberRepository(self.db)
        members = await member_repo.get_by_group_id(group.id)

        if not members:
            return None

        strategy = await self.get_strategy(group.routing_strategy)
        return await strategy.select_model(group, members, cooldown_tracker)


class CooldownTracker:
    def __init__(self):
        self._cooldowns: dict = {}

    def record_error(self, model_id: str, timestamp: float) -> None:
        self._cooldowns[model_id] = timestamp

    def is_in_cooldown(self, model_id: str, cooldown_period: int = 60) -> bool:
        if model_id not in self._cooldowns:
            return False
        elapsed = time.time() - self._cooldowns[model_id]
        return elapsed < cooldown_period

    def clear(self, model_id: str | None = None) -> None:
        if model_id:
            self._cooldowns.pop(model_id, None)
        else:
            self._cooldowns.clear()
