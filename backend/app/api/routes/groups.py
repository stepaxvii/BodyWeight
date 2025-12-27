from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from app.api.deps import get_current_user
from app.db.database import get_session
from app.db.models import User, Group, GroupMember, GroupRole

router = APIRouter(prefix="/groups", tags=["groups"])


class GroupCreate(BaseModel):
    name: str
    description: Optional[str] = None


class GroupResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    invite_code: str
    member_count: int
    is_owner: bool
    role: str


class GroupMemberResponse(BaseModel):
    id: int
    user_id: int
    username: Optional[str]
    first_name: Optional[str]
    level: int
    experience: int
    streak_days: int
    total_workouts: int
    role: str
    joined_at: datetime


@router.get("/", response_model=List[GroupResponse])
async def get_my_groups(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Get groups user is member of."""
    result = await session.execute(
        select(Group, GroupMember)
        .join(GroupMember, GroupMember.group_id == Group.id)
        .where(GroupMember.user_id == user.id)
    )
    rows = result.all()

    groups = []
    for group, member in rows:
        # Get member count
        count_result = await session.execute(
            select(func.count(GroupMember.id))
            .where(GroupMember.group_id == group.id)
        )
        member_count = count_result.scalar() or 0

        groups.append(
            GroupResponse(
                id=group.id,
                name=group.name,
                description=group.description,
                invite_code=group.invite_code,
                member_count=member_count,
                is_owner=group.owner_id == user.id,
                role=member.role.value,
            )
        )

    return groups


@router.post("/", response_model=GroupResponse)
async def create_group(
    data: GroupCreate,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Create new group."""
    import secrets

    # Generate unique invite code
    invite_code = secrets.token_urlsafe(6)

    group = Group(
        name=data.name,
        description=data.description,
        owner_id=user.id,
        invite_code=invite_code,
    )
    session.add(group)
    await session.flush()

    # Add owner as admin
    member = GroupMember(
        group_id=group.id,
        user_id=user.id,
        role=GroupRole.ADMIN,
    )
    session.add(member)
    await session.commit()

    return GroupResponse(
        id=group.id,
        name=group.name,
        description=group.description,
        invite_code=group.invite_code,
        member_count=1,
        is_owner=True,
        role=GroupRole.ADMIN.value,
    )


@router.get("/{group_id}", response_model=GroupResponse)
async def get_group(
    group_id: int,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Get group details."""
    result = await session.execute(
        select(Group, GroupMember)
        .join(GroupMember, GroupMember.group_id == Group.id)
        .where(Group.id == group_id)
        .where(GroupMember.user_id == user.id)
    )
    row = result.first()

    if not row:
        raise HTTPException(status_code=404, detail="Группа не найдена")

    group, member = row

    count_result = await session.execute(
        select(func.count(GroupMember.id))
        .where(GroupMember.group_id == group.id)
    )
    member_count = count_result.scalar() or 0

    return GroupResponse(
        id=group.id,
        name=group.name,
        description=group.description,
        invite_code=group.invite_code,
        member_count=member_count,
        is_owner=group.owner_id == user.id,
        role=member.role.value,
    )


@router.get("/{group_id}/members", response_model=List[GroupMemberResponse])
async def get_group_members(
    group_id: int,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Get group members."""
    # Check if user is member
    member_check = await session.execute(
        select(GroupMember)
        .where(GroupMember.group_id == group_id)
        .where(GroupMember.user_id == user.id)
    )
    if not member_check.scalar_one_or_none():
        raise HTTPException(status_code=403, detail="Вы не участник группы")

    result = await session.execute(
        select(GroupMember, User)
        .join(User, User.id == GroupMember.user_id)
        .where(GroupMember.group_id == group_id)
        .order_by(User.experience.desc())
    )
    rows = result.all()

    return [
        GroupMemberResponse(
            id=m.id,
            user_id=u.id,
            username=u.username,
            first_name=u.first_name,
            level=u.level,
            experience=u.experience,
            streak_days=u.streak_days,
            total_workouts=u.total_workouts,
            role=m.role.value,
            joined_at=m.joined_at,
        )
        for m, u in rows
    ]


@router.post("/join/{invite_code}")
async def join_group(
    invite_code: str,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Join group by invite code."""
    result = await session.execute(
        select(Group).where(Group.invite_code == invite_code)
    )
    group = result.scalar_one_or_none()

    if not group:
        raise HTTPException(status_code=404, detail="Группа не найдена")

    # Check if already member
    member_check = await session.execute(
        select(GroupMember)
        .where(GroupMember.group_id == group.id)
        .where(GroupMember.user_id == user.id)
    )
    if member_check.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Вы уже участник группы")

    member = GroupMember(
        group_id=group.id,
        user_id=user.id,
        role=GroupRole.MEMBER,
    )
    session.add(member)
    await session.commit()

    return {"message": "Вы присоединились к группе", "group_name": group.name}


@router.delete("/{group_id}/leave")
async def leave_group(
    group_id: int,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Leave group."""
    result = await session.execute(
        select(Group).where(Group.id == group_id)
    )
    group = result.scalar_one_or_none()

    if not group:
        raise HTTPException(status_code=404, detail="Группа не найдена")

    if group.owner_id == user.id:
        raise HTTPException(status_code=400, detail="Владелец не может покинуть группу")

    member_result = await session.execute(
        select(GroupMember)
        .where(GroupMember.group_id == group_id)
        .where(GroupMember.user_id == user.id)
    )
    member = member_result.scalar_one_or_none()

    if not member:
        raise HTTPException(status_code=404, detail="Вы не участник группы")

    await session.delete(member)
    await session.commit()

    return {"message": "Вы покинули группу"}


@router.delete("/{group_id}")
async def delete_group(
    group_id: int,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Delete group (owner only)."""
    result = await session.execute(
        select(Group).where(Group.id == group_id)
    )
    group = result.scalar_one_or_none()

    if not group:
        raise HTTPException(status_code=404, detail="Группа не найдена")

    if group.owner_id != user.id:
        raise HTTPException(status_code=403, detail="Только владелец может удалить группу")

    # Delete all members
    members_result = await session.execute(
        select(GroupMember).where(GroupMember.group_id == group_id)
    )
    for member in members_result.scalars().all():
        await session.delete(member)

    await session.delete(group)
    await session.commit()

    return {"message": "Группа удалена"}
