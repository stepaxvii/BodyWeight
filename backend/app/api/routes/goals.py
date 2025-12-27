from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List

from app.api.deps import get_current_user
from app.db.database import get_session
from app.db.models import User, Goal, GoalType, Exercise

router = APIRouter(prefix="/goals", tags=["goals"])


class GoalCreate(BaseModel):
    goal_type: str
    title: str
    target_value: int
    exercise_id: Optional[int] = None
    deadline: Optional[datetime] = None


class GoalResponse(BaseModel):
    id: int
    goal_type: str
    title: str
    target_value: int
    current_value: int
    progress_percent: float
    exercise_id: Optional[int]
    exercise_name: Optional[str]
    deadline: Optional[datetime]
    created_at: datetime
    completed_at: Optional[datetime]
    is_active: bool


@router.post("/", response_model=GoalResponse)
async def create_goal(
    data: GoalCreate,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Create a new goal."""
    try:
        goal_type = GoalType(data.goal_type)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid goal type")

    exercise_name = None
    if data.exercise_id:
        result = await session.execute(
            select(Exercise).where(Exercise.id == data.exercise_id)
        )
        exercise = result.scalar_one_or_none()
        if not exercise:
            raise HTTPException(status_code=400, detail="Exercise not found")
        exercise_name = exercise.name

    goal = Goal(
        user_id=user.id,
        goal_type=goal_type,
        title=data.title,
        target_value=data.target_value,
        exercise_id=data.exercise_id,
        deadline=data.deadline,
    )
    session.add(goal)
    await session.commit()
    await session.refresh(goal)

    return GoalResponse(
        id=goal.id,
        goal_type=goal.goal_type.value,
        title=goal.title,
        target_value=goal.target_value,
        current_value=goal.current_value,
        progress_percent=0,
        exercise_id=goal.exercise_id,
        exercise_name=exercise_name,
        deadline=goal.deadline,
        created_at=goal.created_at,
        completed_at=goal.completed_at,
        is_active=goal.is_active,
    )


@router.get("/", response_model=List[GoalResponse])
async def get_goals(
    active_only: bool = True,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Get user's goals."""
    query = select(Goal).where(Goal.user_id == user.id)

    if active_only:
        query = query.where(Goal.is_active == True)

    query = query.order_by(Goal.created_at.desc())
    result = await session.execute(query)
    goals = result.scalars().all()

    response = []
    for goal in goals:
        exercise_name = None
        if goal.exercise_id:
            ex_result = await session.execute(
                select(Exercise).where(Exercise.id == goal.exercise_id)
            )
            exercise = ex_result.scalar_one_or_none()
            if exercise:
                exercise_name = exercise.name

        progress = (goal.current_value / goal.target_value * 100) if goal.target_value > 0 else 0

        response.append(GoalResponse(
            id=goal.id,
            goal_type=goal.goal_type.value,
            title=goal.title,
            target_value=goal.target_value,
            current_value=goal.current_value,
            progress_percent=min(progress, 100),
            exercise_id=goal.exercise_id,
            exercise_name=exercise_name,
            deadline=goal.deadline,
            created_at=goal.created_at,
            completed_at=goal.completed_at,
            is_active=goal.is_active,
        ))

    return response


@router.delete("/{goal_id}")
async def delete_goal(
    goal_id: int,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Delete a goal."""
    result = await session.execute(
        select(Goal)
        .where(Goal.id == goal_id)
        .where(Goal.user_id == user.id)
    )
    goal = result.scalar_one_or_none()

    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")

    await session.delete(goal)
    await session.commit()

    return {"message": "Goal deleted"}
