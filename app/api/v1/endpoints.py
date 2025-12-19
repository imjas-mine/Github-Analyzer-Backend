from fastapi import APIRouter
from app.services.github_service import GitHubService
from app.services.repo_analyzer_service import RepoAnalyzerService

router = APIRouter()


@router.get("/health")
def health_check():
    return {"status": "ok", "service": "GitHub Analyzer"}


@router.get("/users/{username}")
async def get_user(username: str):
    github_service = GitHubService()
    user = await github_service.get_user_profile(username)
    return user


@router.get("/users/{username}/repositories")
async def get_user_repositories(username: str):
    github_service = GitHubService()
    repositories = await github_service.get_user_repositories(username)
    return repositories


@router.get("/users/{username}/repositories/{owner}/{name}")
async def get_repository_details(owner: str, name: str):
    github_service = GitHubService()
    repository = await github_service.get_repository_details(owner, name)
    return repository


@router.get("/users/{username}/repositories/{owner}/{name}/directory")
async def get_directory_tree(owner: str, name: str):
    github_service = GitHubService()
    directory_tree = await github_service.get_directory_tree(owner, name)
    return directory_tree


@router.get("/users/{username}/repositories/{owner}/{name}/file/{path}")
async def get_file_content(owner: str, name: str, path: str):
    github_service = GitHubService()
    file_content = await github_service.get_file_content(owner, name, path)
    return file_content


@router.get("/users/{username}/repositories/{owner}/{name}/contributors")
async def get_contribution_stats(username: str, owner: str, name: str):
    github_service = GitHubService()
    contribution_stats = await github_service.get_contribution_stats(
        owner, name, username
    )
    return contribution_stats


@router.get("/users/{username}/repositories/{owner}/{name}/contributions")
async def get_user_contributions(owner: str, name: str, username: str):
    github_service = GitHubService()
    user_contributions = await github_service.get_user_contributions(
        owner, name, username
    )
    return user_contributions


@router.get("/analyze/{owner}/{repo}")
async def analyze_repository(owner: str, repo: str, username: str = "default"):
    analyzer = RepoAnalyzerService()
    analysis = await analyzer.analyze(owner, repo, username)
    return analysis


@router.get("/analyze/{owner}/{repo}/contributions/{username}")
async def analyze_user_contributions(owner: str, repo: str, username: str):
    analyzer = RepoAnalyzerService()
    return await analyzer.analyze_contributions(owner, repo, username)
