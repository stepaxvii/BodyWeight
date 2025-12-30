from datetime import date, datetime, timedelta
from typing import List
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select

from app.api.deps import AsyncSessionDep, CurrentUser
from app.db.models import UserGoal

router = APIRouter()


class CreateGoalRequest(BaseModel):
    goal_type: str  # weekly_workouts, daily_xp, weekly_xp
    target_value: int
    duration_days: int = 7  # Default to weekly


class GoalResponse(BaseModel):
    id: int
    goal_type: str
    target_value: int
    current_value: int
    start_date: date
    end_date: date
    completed: bool
    completed_at: datetime | None
    progress_percent: float

    class Config:
        from_attributes = True


@router.get("", response_model=List[GoalResponse])
async def get_goals(
    session: AsyncSessionDep,
    user: CurrentUser,
    active_only: bool = True,
):
    """Get user's goals."""
    query = select(UserGoal).where(UserGoal.user_id == user.id)

    if active_only:
        today = date.today()
        query = query.where(UserGoal.end_date >= today)

    query = query.order_by(UserGoal.end_date.asc())

    result = await session.execute(query)
    goals = result.scalars().all()

    return [
        GoalResponse(
            id=g.id,
            goal_type=g.goal_type,
            target_value=g.target_value,
            current_value=g.current_value,
            start_date=g.start_date,
            end_date=g.end_date,
            completed=g.completed,
            completed_at=g.completed_at,
            progress_percent=min((g.current_value / g.target_value) * 100, 100) if g.target_value > 0 else 0,
        )
        for g in goals
    ]


@router.post("", response_model=GoalResponse, status_code=status.HTTP_201_CREATED)
async def create_goal(
    request: CreateGoalRequest,
    session: AsyncSessionDep,
    user: CurrentUser,
):
    """Create a new goal."""
    # Validate goal type
    valid_types = ["weekly_workouts", "daily_xp", "weekly_xp", "streak_days"]
    if request.goal_type not in valid_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid goal type. Must be one of: {valid_types}",
        )

    if request.target_value <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Target value must be positive",
        )

    today = date.today()
    end_date = today + timedelta(days=request.duration_days)

    goal = UserGoal(
        user_id=user.id,
        goal_type=request.goal_type,
        target_value=request.target_value,
        current_value=0,
        start_date=today,
        end_date=end_date,
    )
    session.add(goal)
    await session.flush()

    return GoalResponse(
        id=goal.id,
        goal_type=goal.goal_type,
        target_value=goal.target_value,
        current_value=goal.current_value,
        start_date=goal.start_date,
        end_date=goal.end_date,
        completed=goal.completed,
        completed_at=goal.completed_at,
        progress_percent=0,
    )


@router.put("/{goal_id}", response_model=GoalResponse)
async def update_goal_progress(
    goal_id: int,
    session: AsyncSessionDep,
    user: CurrentUser,
    add_value: int = 1,
):
    """Update goal progress (typically called after workout completion)."""
    result = await session.execute(
        select(UserGoal)
        .where(UserGoal.id == goal_id)
        .where(UserGoal.user_id == user.id)
    )
    goal = result.scalar_one_or_none()

    if not goal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Goal not found",
        )

    if goal.completed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Goal already completed",
        )

    if goal.end_date < date.today():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Goal has expired",
        )

    goal.current_value += add_value

    if goal.current_value >= goal.target_value:
        goal.completed = True
        goal.completed_at = datetime.utcnow()

    await session.flush()

    return GoalResponse(
        id=goal.id,
        goal_type=goal.goal_type,
        target_value=goal.target_value,
        current_value=goal.current_value,
        start_date=goal.start_date,
        end_date=goal.end_date,
        completed=goal.completed,
        completed_at=goal.completed_at,
        progress_percent=min((goal.current_value / goal.target_value) * 100, 100) if goal.target_value > 0 else 0,
    )


@router.get("/progress", response_model=List[GoalResponse])
async def get_goals_progress(
    session: AsyncSessionDep,
    user: CurrentUser,
):
    """
    Get detailed progress for all active goals.
    Includes completed and incomplete goals.
    """
    today = date.today()

    # Get all active goals (not expired)
    query = (
        select(UserGoal)
        .where(UserGoal.user_id == user.id)
        .where(UserGoal.end_date >= today)
        .order_by(UserGoal.completed.asc(), UserGoal.end_date.asc())
    )

    result = await session.execute(query)
    goals = result.scalars().all()

    return [
        GoalResponse(
            id=g.id,
            goal_type=g.goal_type,
            target_value=g.target_value,
            current_value=g.current_value,
            start_date=g.start_date,
            end_date=g.end_date,
            completed=g.completed,
            completed_at=g.completed_at,
            progress_percent=min((g.current_value / g.target_value) * 100, 100) if g.target_value > 0 else 0,
        )
        for g in goals
    ]


@router.delete("/{goal_id}")
async def delete_goal(
    goal_id: int,
    session: AsyncSessionDep,
    user: CurrentUser,
):
    """Delete a goal."""
    result = await session.execute(
        select(UserGoal)
        .where(UserGoal.id == goal_id)
        .where(UserGoal.user_id == user.id)
    )
    goal = result.scalar_one_or_none()

    if not goal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Goal not found",
        )

    await session.delete(goal)

    return {"message": "Goal deleted"}
