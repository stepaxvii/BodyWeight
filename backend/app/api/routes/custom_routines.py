from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.api.deps import AsyncSessionDep, CurrentUser
from app.db.models import Exercise, UserCustomRoutine, UserCustomRoutineExercise

router = APIRouter()


# ============== Request/Response Models ==============

class RoutineExerciseCreate(BaseModel):
    exercise_id: int
    target_reps: int | None = None
    target_duration: int | None = None
    rest_seconds: int = 30


class RoutineExerciseResponse(BaseModel):
    id: int
    exercise_id: int
    exercise_slug: str
    exercise_name_ru: str
    is_timed: bool
    sort_order: int
    target_reps: int | None
    target_duration: int | None
    rest_seconds: int

    class Config:
        from_attributes = True


class CustomRoutineCreate(BaseModel):
    name: str
    description: str | None = None
    routine_type: str = "workout"  # morning, workout, stretch
    exercises: list[RoutineExerciseCreate] = []


class CustomRoutineUpdate(BaseModel):
    name: str | None= None
    description: str | None = None
    routine_type: str | None = None
    exercises: list[RoutineExerciseCreate] | None = None


class CustomRoutineResponse(BaseModel):
    id: int
    name: str
    description: str | None
    routine_type: str
    duration_minutes: int
    is_active: bool
    exercises: list[RoutineExerciseResponse]

    class Config:
        from_attributes = True


class CustomRoutineListItem(BaseModel):
    id: int
    name: str
    routine_type: str
    duration_minutes: int
    exercises_count: int

    class Config:
        from_attributes = True


# ============== Endpoints ==============

@router.get("", response_model=list[CustomRoutineListItem])
async def list_custom_routines(
    session: AsyncSessionDep,
    user: CurrentUser,
    routine_type: str | None = None,
):
    """Get all custom routines for the current user."""
    query = (
        select(UserCustomRoutine)
        .options(selectinload(UserCustomRoutine.exercises))
        .where(UserCustomRoutine.user_id == user.id)
        .where(UserCustomRoutine.is_active is True)
    )

    if routine_type:
        query = query.where(UserCustomRoutine.routine_type == routine_type)

    query = query.order_by(UserCustomRoutine.created_at.desc())

    result = await session.execute(query)
    routines = result.scalars().all()

    return [
        CustomRoutineListItem(
            id=r.id,
            name=r.name,
            routine_type=r.routine_type,
            duration_minutes=r.duration_minutes,
            exercises_count=len(r.exercises),
        )
        for r in routines
    ]


@router.get("/{routine_id}", response_model=CustomRoutineResponse)
async def get_custom_routine(
    routine_id: int,
    session: AsyncSessionDep,
    user: CurrentUser,
):
    """Get a specific custom routine with all exercises."""
    result = await session.execute(
        select(UserCustomRoutine)
        .options(
            selectinload(UserCustomRoutine.exercises).selectinload(UserCustomRoutineExercise.exercise)
        )
        .where(UserCustomRoutine.id == routine_id)
        .where(UserCustomRoutine.user_id == user.id)
    )
    routine = result.scalar_one_or_none()

    if not routine:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Routine not found",
        )

    return CustomRoutineResponse(
        id=routine.id,
        name=routine.name,
        description=routine.description,
        routine_type=routine.routine_type,
        duration_minutes=routine.duration_minutes,
        is_active=routine.is_active,
        exercises=[
            RoutineExerciseResponse(
                id=ex.id,
                exercise_id=ex.exercise_id,
                exercise_slug=ex.exercise.slug,
                exercise_name_ru=ex.exercise.name_ru,
                is_timed=ex.exercise.is_timed,
                sort_order=ex.sort_order,
                target_reps=ex.target_reps,
                target_duration=ex.target_duration,
                rest_seconds=ex.rest_seconds,
            )
            for ex in sorted(routine.exercises, key=lambda x: x.sort_order)
        ],
    )


@router.post("", response_model=CustomRoutineResponse, status_code=status.HTTP_201_CREATED)
async def create_custom_routine(
    data: CustomRoutineCreate,
    session: AsyncSessionDep,
    user: CurrentUser,
):
    """Create a new custom routine."""
    # Calculate estimated duration (30 sec per exercise + rest times)
    duration_minutes = max(1, len(data.exercises) * 30 // 60 + sum(e.rest_seconds for e in data.exercises) // 60)

    routine = UserCustomRoutine(
        user_id=user.id,
        name=data.name,
        description=data.description,
        routine_type=data.routine_type,
        duration_minutes=duration_minutes,
    )
    session.add(routine)
    await session.flush()

    # Add exercises
    for i, ex_data in enumerate(data.exercises):
        # Verify exercise exists
        ex_result = await session.execute(
            select(Exercise).where(Exercise.id == ex_data.exercise_id)
        )
        exercise = ex_result.scalar_one_or_none()
        if not exercise:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Exercise with id {ex_data.exercise_id} not found",
            )

        routine_exercise = UserCustomRoutineExercise(
            routine_id=routine.id,
            exercise_id=ex_data.exercise_id,
            sort_order=i,
            target_reps=ex_data.target_reps,
            target_duration=ex_data.target_duration,
            rest_seconds=ex_data.rest_seconds,
        )
        session.add(routine_exercise)

    await session.commit()

    # Reload with exercises
    return await get_custom_routine(routine.id, session, user)


@router.put("/{routine_id}", response_model=CustomRoutineResponse)
async def update_custom_routine(
    routine_id: int,
    data: CustomRoutineUpdate,
    session: AsyncSessionDep,
    user: CurrentUser,
):
    """Update a custom routine."""
    result = await session.execute(
        select(UserCustomRoutine)
        .options(selectinload(UserCustomRoutine.exercises))
        .where(UserCustomRoutine.id == routine_id)
        .where(UserCustomRoutine.user_id == user.id)
    )
    routine = result.scalar_one_or_none()

    if not routine:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Routine not found",
        )

    # Update basic fields
    if data.name is not None:
        routine.name = data.name
    if data.description is not None:
        routine.description = data.description
    if data.routine_type is not None:
        routine.routine_type = data.routine_type

    # Update exercises if provided
    if data.exercises is not None:
        # Remove existing exercises
        for ex in routine.exercises:
            await session.delete(ex)

        # Add new exercises
        for i, ex_data in enumerate(data.exercises):
            # Verify exercise exists
            ex_result = await session.execute(
                select(Exercise).where(Exercise.id == ex_data.exercise_id)
            )
            exercise = ex_result.scalar_one_or_none()
            if not exercise:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Exercise with id {ex_data.exercise_id} not found",
                )

            routine_exercise = UserCustomRoutineExercise(
                routine_id=routine.id,
                exercise_id=ex_data.exercise_id,
                sort_order=i,
                target_reps=ex_data.target_reps,
                target_duration=ex_data.target_duration,
                rest_seconds=ex_data.rest_seconds,
            )
            session.add(routine_exercise)

        # Recalculate duration
        routine.duration_minutes = max(1, len(data.exercises) * 30 // 60 + sum(e.rest_seconds for e in data.exercises) // 60)

    await session.commit()

    # Reload with exercises
    return await get_custom_routine(routine.id, session, user)


@router.delete("/{routine_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_custom_routine(
    routine_id: int,
    session: AsyncSessionDep,
    user: CurrentUser,
):
    """Delete a custom routine (soft delete)."""
    result = await session.execute(
        select(UserCustomRoutine)
        .where(UserCustomRoutine.id == routine_id)
        .where(UserCustomRoutine.user_id == user.id)
    )
    routine = result.scalar_one_or_none()

    if not routine:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Routine not found",
        )

    routine.is_active = False
    await session.commit()


@router.post("/{routine_id}/duplicate", response_model=CustomRoutineResponse, status_code=status.HTTP_201_CREATED)
async def duplicate_custom_routine(
    routine_id: int,
    session: AsyncSessionDep,
    user: CurrentUser,
):
    """Create a copy of an existing routine."""
    # Get original routine
    result = await session.execute(
        select(UserCustomRoutine)
        .options(selectinload(UserCustomRoutine.exercises))
        .where(UserCustomRoutine.id == routine_id)
        .where(UserCustomRoutine.user_id == user.id)
    )
    original = result.scalar_one_or_none()

    if not original:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Routine not found",
        )

    # Create copy
    new_routine = UserCustomRoutine(
        user_id=user.id,
        name=f"{original.name} (копия)",
        description=original.description,
        routine_type=original.routine_type,
        duration_minutes=original.duration_minutes,
    )
    session.add(new_routine)
    await session.flush()

    # Copy exercises
    for ex in original.exercises:
        new_ex = UserCustomRoutineExercise(
            routine_id=new_routine.id,
            exercise_id=ex.exercise_id,
            sort_order=ex.sort_order,
            target_reps=ex.target_reps,
            target_duration=ex.target_duration,
            rest_seconds=ex.rest_seconds,
        )
        session.add(new_ex)

    await session.commit()

    return await get_custom_routine(new_routine.id, session, user)
