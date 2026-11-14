from fastapi import APIRouter

from app.api.v1.routes import (
    analytics,
    assessments,
    auth,
    career,
    catalog,
    dashboard,
    health,
    roadmaps,
    tutor,
    users,
)

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(catalog.router)
api_router.include_router(assessments.router)
api_router.include_router(roadmaps.router)
api_router.include_router(tutor.router)
api_router.include_router(analytics.router)
api_router.include_router(career.router)
api_router.include_router(dashboard.router)
