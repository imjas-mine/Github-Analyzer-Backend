"""
Pydantic schemas/models for GitHub Analyzer API.
These models map to the data returned by our GraphQL queries.
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


# ============================================
# Shared/Nested Models
# ============================================

class Language(BaseModel):
    """Represents a programming language with optional color."""
    name: str
    color: Optional[str] = None


class LanguageEdge(BaseModel):
    """Language with size information (bytes of code)."""
    size: int
    node: Language


class Topic(BaseModel):
    """Repository topic/tag."""
    name: str


class Owner(BaseModel):
    """Repository or user owner info."""
    login: str
    avatar_url: Optional[str] = Field(None, alias="avatarUrl")


class PageInfo(BaseModel):
    """Pagination info for GraphQL connections."""
    has_next_page: bool = Field(alias="hasNextPage")
    end_cursor: Optional[str] = Field(None, alias="endCursor")


class Label(BaseModel):
    """Issue/PR label."""
    name: str
    color: Optional[str] = None


# ============================================
# Query 1: User Repositories (Timeline View)
# ============================================

class RepositorySummary(BaseModel):
    """
    Lightweight repository info for timeline/list view.
    Maps to: GetUserRepositories query
    """
    name: str
    name_with_owner: str = Field(alias="nameWithOwner")
    description: Optional[str] = None
    url: str
    is_private: bool = Field(alias="isPrivate")
    is_fork: bool = Field(alias="isFork")
    stargazer_count: int = Field(alias="stargazerCount")
    fork_count: int = Field(alias="forkCount")
    primary_language: Optional[Language] = Field(None, alias="primaryLanguage")
    created_at: datetime = Field(alias="createdAt")
    updated_at: datetime = Field(alias="updatedAt")
    pushed_at: Optional[datetime] = Field(None, alias="pushedAt")
    owner: Owner
    
    # Derived field - will be computed
    user_relationship: Optional[str] = None  # "Owner", "Contributor", "Collaborator"

    class Config:
        populate_by_name = True


class UserRepositoriesResponse(BaseModel):
    """Response wrapper for user's repository list."""
    login: str
    avatar_url: str = Field(alias="avatarUrl")
    total_count: int
    repositories: List[RepositorySummary]
    page_info: PageInfo

    class Config:
        populate_by_name = True


# ============================================
# Query 2: Repository Details (Deep Dive)
# ============================================

class DirectoryEntry(BaseModel):
    """File or folder in repository tree."""
    name: str
    type: str  # "blob" (file) or "tree" (directory)


class ConfigFiles(BaseModel):
    """
    Parsed config files for framework detection.
    These are extracted from the raw GraphQL response.
    """
    package_json: Optional[str] = None
    requirements_txt: Optional[str] = None
    pyproject_toml: Optional[str] = None
    cargo_toml: Optional[str] = None
    pom_xml: Optional[str] = None
    build_gradle: Optional[str] = None
    go_mod: Optional[str] = None
    gemfile: Optional[str] = None
    composer_json: Optional[str] = None
    pubspec_yaml: Optional[str] = None
    dockerfile: Optional[str] = None


class RepositoryDetails(BaseModel):
    """
    Comprehensive repository information for AI analysis.
    Maps to: GetRepositoryDetails query
    """
    # Basic Info
    name: str
    name_with_owner: str = Field(alias="nameWithOwner")
    description: Optional[str] = None
    url: str
    homepage_url: Optional[str] = Field(None, alias="homepageUrl")
    is_private: bool = Field(alias="isPrivate")
    is_fork: bool = Field(alias="isFork")
    is_archived: bool = Field(alias="isArchived")
    is_template: bool = Field(alias="isTemplate")
    is_empty: bool = Field(alias="isEmpty")
    
    # Stats
    stargazer_count: int = Field(alias="stargazerCount")
    fork_count: int = Field(alias="forkCount")
    watchers_count: int = Field(0, alias="watchersCount")
    
    # Dates
    created_at: datetime = Field(alias="createdAt")
    updated_at: datetime = Field(alias="updatedAt")
    pushed_at: Optional[datetime] = Field(None, alias="pushedAt")
    
    # Owner
    owner: Owner
    
    # Languages
    primary_language: Optional[Language] = Field(None, alias="primaryLanguage")
    languages: List[LanguageEdge] = []
    total_languages_size: int = 0
    
    # Topics
    topics: List[str] = []
    
    # Content for AI
    readme_content: Optional[str] = None
    root_directory: List[DirectoryEntry] = []
    
    # Commit stats
    default_branch: Optional[str] = None
    total_commits: int = 0



# ============================================
# Query 3: User Contributions
# ============================================

class CommitAuthor(BaseModel):
    """Commit author information."""
    name: Optional[str] = None
    email: Optional[str] = None
    login: Optional[str] = None  # GitHub username if linked


class Commit(BaseModel):
    """Individual commit information."""
    message: str
    committed_date: datetime = Field(alias="committedDate")
    additions: int = 0
    deletions: int = 0
    changed_files: Optional[int] = Field(None, alias="changedFilesIfAvailable")
    author: Optional[CommitAuthor] = None

    class Config:
        populate_by_name = True


class PullRequest(BaseModel):
    """Pull request information."""
    title: str
    state: str  # OPEN, CLOSED, MERGED
    created_at: datetime = Field(alias="createdAt")
    merged_at: Optional[datetime] = Field(None, alias="mergedAt")
    closed_at: Optional[datetime] = Field(None, alias="closedAt")
    additions: int = 0
    deletions: int = 0
    changed_files: int = Field(0, alias="changedFiles")
    author_login: Optional[str] = None

    class Config:
        populate_by_name = True


class Issue(BaseModel):
    """Issue information."""
    title: str
    state: str  # OPEN, CLOSED
    created_at: datetime = Field(alias="createdAt")
    closed_at: Optional[datetime] = Field(None, alias="closedAt")
    author_login: Optional[str] = None
    labels: List[Label] = []

    class Config:
        populate_by_name = True


class UserContributions(BaseModel):
    """
    User's contributions to a specific repository.
    Maps to: GetUserContributions query
    """
    repository_name: str
    
    # Commits
    total_commits: int = 0
    commits: List[Commit] = []
    total_additions: int = 0  # Computed
    total_deletions: int = 0  # Computed
    
    # Pull Requests
    total_pull_requests: int = 0
    pull_requests: List[PullRequest] = []
    merged_prs: int = 0  # Computed
    
    # Issues
    total_issues: int = 0
    issues: List[Issue] = []


# ============================================
# Query 4: User Profile
# ============================================

class ContributionStats(BaseModel):
    """User's contribution statistics."""
    total_commits: int = Field(0, alias="totalCommitContributions")
    total_pull_requests: int = Field(0, alias="totalPullRequestContributions")
    total_issues: int = Field(0, alias="totalIssueContributions")
    total_repositories: int = Field(0, alias="totalRepositoryContributions")
    total_contributions: int = 0  # From calendar

    class Config:
        populate_by_name = True


class UserProfile(BaseModel):
    """
    Complete user profile information.
    Maps to: GetUserId query
    """
    id: str  # GitHub's internal ID (needed for filtering)
    login: str
    name: Optional[str] = None
    avatar_url: str = Field(alias="avatarUrl")
    bio: Optional[str] = None
    company: Optional[str] = None
    location: Optional[str] = None
    email: Optional[str] = None
    website_url: Optional[str] = Field(None, alias="websiteUrl")
    created_at: datetime = Field(alias="createdAt")
    followers_count: int = 0
    following_count: int = 0
    repositories_count: int = 0
    contribution_stats: Optional[ContributionStats] = None

    class Config:
        populate_by_name = True


# ============================================
# AI Generated Content Models
# ============================================

class DetectedFramework(BaseModel):
    """Framework/library detected from config files."""
    name: str
    category: str  # "frontend", "backend", "database", "devops", etc.
    confidence: float  # 0.0 to 1.0
    version: Optional[str] = None


class ProjectAnalysis(BaseModel):
    """
    AI-generated analysis of a project.
    This is what the AI service will produce.
    """
    project_type: str  # "Web App", "API", "Library", "CLI Tool", etc.
    frameworks: List[DetectedFramework] = []
    generated_description: Optional[str] = None
    key_features: List[str] = []
    tech_stack_summary: str = ""
    complexity_score: Optional[int] = None  # 1-10


class ContributionSummary(BaseModel):
    """
    AI-generated summary of user's contributions.
    """
    relationship: str  # "Owner", "Core Contributor", "Contributor"
    contribution_percentage: Optional[float] = None
    primary_areas: List[str] = []  # "Frontend", "API", "Documentation"
    summary_text: str = ""
    notable_contributions: List[str] = []


# ============================================
# API Response Models
# ============================================

class RepositoryAnalysisResponse(BaseModel):
    """Complete response for a single repository analysis."""
    repository: RepositoryDetails
    user_contributions: Optional[UserContributions] = None
    analysis: Optional[ProjectAnalysis] = None
    contribution_summary: Optional[ContributionSummary] = None


class TimelineResponse(BaseModel):
    """Response for the timeline/portfolio view."""
    user: UserProfile
    repositories: List[RepositorySummary]
    total_count: int
    has_next_page: bool
    next_cursor: Optional[str] = None