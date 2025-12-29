from fastapi import APIRouter

from .routes import auth, users, exercises, workouts, achievements, leaderboard, friends, goals, shop, custom_routines, notifications

api_router = APIRouter(prefix="/api")

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(exercises.router, prefix="/exercises", tags=["exercises"])
api_router.include_router(workouts.router, prefix="/workouts", tags=["workouts"])
api_router.include_router(achievements.router, prefix="/achievements", tags=["achievements"])
api_router.include_router(leaderboard.router, prefix="/leaderboard", tags=["leaderboard"])
api_router.include_router(friends.router, prefix="/friends", tags=["friends"])
api_router.include_router(goals.router, prefix="/goals", tags=["goals"])
api_router.include_router(shop.router, prefix="/shop", tags=["shop"])
api_router.include_router(custom_routines.router, prefix="/custom-routines", tags=["custom-routines"])
api_router.include_router(notifications.router, prefix="/notifications", tags=["notifications"])
