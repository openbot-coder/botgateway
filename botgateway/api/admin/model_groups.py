from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from botgateway.db import (
    Database,
    ModelGroup,
    ModelGroupMember,
    ModelGroupMemberRepository,
    ModelGroupRepository,
    ModelRepository,
)

router = APIRouter(prefix="/model-groups", tags=["model-groups"])


class ModelGroupCreate(BaseModel):
    name: str
    description: str | None = None
    routing_strategy: str = "fallback"
    retry_count: int = 3
    retry_delay: int = 1
    cooldown_period: int = 60


class ModelGroupUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    routing_strategy: str | None = None
    retry_count: int | None = None
    retry_delay: int | None = None
    cooldown_period: int | None = None


class MemberCreate(BaseModel):
    model_id: str
    priority: int = 0
    weight: int = 1


class ModelGroupMemberResponse(BaseModel):
    id: str
    group_id: str
    model_id: str
    priority: int
    weight: int
    created_at: str


class ModelGroupResponse(BaseModel):
    id: str
    name: str
    description: str | None
    routing_strategy: str
    retry_count: int
    retry_delay: int
    cooldown_period: int
    is_active: bool
    created_at: str
    updated_at: str
    members: list[ModelGroupMemberResponse] | None = None


def get_db() -> Database:
    return Database.get_database()


@router.post("", response_model=ModelGroupResponse, status_code=status.HTTP_201_CREATED)
async def create_model_group(
    group_data: ModelGroupCreate,
    db: Database = Depends(get_db),
):
    repo = ModelGroupRepository(db)
    existing = await repo.get_by_name(group_data.name)
    if existing:
        raise HTTPException(status_code=400, detail="Model group name already exists")

    group = ModelGroup.create(
        name=group_data.name,
        description=group_data.description,
        routing_strategy=group_data.routing_strategy,
        retry_count=group_data.retry_count,
        retry_delay=group_data.retry_delay,
        cooldown_period=group_data.cooldown_period,
    )

    await repo.create(group)
    return ModelGroupResponse(**group.to_dict(), members=[])


@router.get("", response_model=list[ModelGroupResponse])
async def list_model_groups(
    active_only: bool = True,
    db: Database = Depends(get_db),
):
    repo = ModelGroupRepository(db)
    groups = await repo.get_all(active_only=active_only)

    member_repo = ModelGroupMemberRepository(db)
    result = []
    for group in groups:
        members = await member_repo.get_by_group_id(group.id)
        member_responses = [ModelGroupMemberResponse(**m.to_dict()) for m in members]
        result.append(ModelGroupResponse(**group.to_dict(), members=member_responses))

    return result


@router.get("/{group_id}", response_model=ModelGroupResponse)
async def get_model_group(
    group_id: str,
    db: Database = Depends(get_db),
):
    repo = ModelGroupRepository(db)
    group = await repo.get_by_id(group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Model group not found")

    member_repo = ModelGroupMemberRepository(db)
    members = await member_repo.get_by_group_id(group_id)
    member_responses = [ModelGroupMemberResponse(**m.to_dict()) for m in members]

    return ModelGroupResponse(**group.to_dict(), members=member_responses)


@router.put("/{group_id}", response_model=ModelGroupResponse)
async def update_model_group(
    group_id: str,
    group_data: ModelGroupUpdate,
    db: Database = Depends(get_db),
):
    repo = ModelGroupRepository(db)
    group = await repo.get_by_id(group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Model group not found")

    if group_data.name is not None:
        existing = await repo.get_by_name(group_data.name)
        if existing and existing.id != group_id:
            raise HTTPException(status_code=400, detail="Model group name already exists")
        group.name = group_data.name

    if group_data.description is not None:
        group.description = group_data.description
    if group_data.routing_strategy is not None:
        group.routing_strategy = group_data.routing_strategy
    if group_data.retry_count is not None:
        group.retry_count = group_data.retry_count
    if group_data.retry_delay is not None:
        group.retry_delay = group_data.retry_delay
    if group_data.cooldown_period is not None:
        group.cooldown_period = group_data.cooldown_period

    group.updated_at = datetime.utcnow().isoformat()
    await repo.update(group)

    member_repo = ModelGroupMemberRepository(db)
    members = await member_repo.get_by_group_id(group_id)
    member_responses = [ModelGroupMemberResponse(**m.to_dict()) for m in members]

    return ModelGroupResponse(**group.to_dict(), members=member_responses)


@router.delete("/{group_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_model_group(
    group_id: str,
    db: Database = Depends(get_db),
):
    repo = ModelGroupRepository(db)
    group = await repo.get_by_id(group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Model group not found")
    await repo.delete(group_id)


@router.post(
    "/{group_id}/members",
    response_model=ModelGroupMemberResponse,
    status_code=status.HTTP_201_CREATED
)
async def add_member(
    group_id: str,
    member_data: MemberCreate,
    db: Database = Depends(get_db),
):
    group_repo = ModelGroupRepository(db)
    group = await group_repo.get_by_id(group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Model group not found")

    model_repo = ModelRepository(db)
    model = await model_repo.get_by_id(member_data.model_id)
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")

    member = ModelGroupMember.create(
        group_id=group_id,
        model_id=member_data.model_id,
        priority=member_data.priority,
        weight=member_data.weight,
    )

    member_repo = ModelGroupMemberRepository(db)
    await member_repo.create(member)
    return ModelGroupMemberResponse(**member.to_dict())


@router.delete("/{group_id}/members/{member_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_member(
    group_id: str,
    member_id: str,
    db: Database = Depends(get_db),
):
    member_repo = ModelGroupMemberRepository(db)
    member = await member_repo.get_by_id(member_id)
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    if member.group_id != group_id:
        raise HTTPException(status_code=404, detail="Member not found in this group")
    await member_repo.delete(member_id)
