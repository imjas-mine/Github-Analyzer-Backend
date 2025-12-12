from fastapi import APIRouter
from app.services.github_service import GitHubService
router = APIRouter()

@router.get("/health")
def health_check():
    return {"status": "ok", "service": "GitHub Analyzer"}

@router.get("/users/{username}")
async def get_user(username: str):
    github_service=GitHubService()
    user=await github_service.get_user_profile(username)
    return user

    
    

