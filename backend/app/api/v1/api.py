from fastapi import APIRouter
from app.api.v1.endpoints import projects, epics, user_stories, meetings, agents, communication

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(projects.router, prefix="/projects", tags=["projects"])
api_router.include_router(epics.router, prefix="/epics", tags=["epics"])
api_router.include_router(user_stories.router, prefix="/user-stories", tags=["user-stories"])
api_router.include_router(meetings.router, prefix="/meetings", tags=["meetings"])
api_router.include_router(agents.router, prefix="/agents", tags=["agents"])
api_router.include_router(communication.router, prefix="/communication", tags=["communication"]) 