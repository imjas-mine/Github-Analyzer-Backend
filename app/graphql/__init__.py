"""
GraphQL Query Loader Module

Simple utility to load GraphQL queries from individual files.

Usage:
    from app.graphql import load_query
    
    query = load_query("get_user_profile")
    # Returns contents of get_user_profile.graphql
"""

from pathlib import Path
from typing import List
from functools import lru_cache

# Directory containing all query files
QUERIES_DIR = Path(__file__).parent / "queries"


@lru_cache(maxsize=20)
def load_query(name: str) -> str:
    """
    Load a GraphQL query by filename (without .graphql extension).
    
    Args:
        name: Query filename without extension, e.g., "get_user_profile"
        
    Returns:
        The GraphQL query string
        
    Raises:
        FileNotFoundError: If query file doesn't exist
        
    Example:
        >>> query = load_query("get_user_profile")
        >>> print(query[:50])
        'query GetUserProfile($username: String!) {...'
    """
    file_path = QUERIES_DIR / f"{name}.graphql"
    
    if not file_path.exists():
        available = list_available_queries()
        raise FileNotFoundError(
            f"Query '{name}' not found at {file_path}. "
            f"Available queries: {available}"
        )
    
    return file_path.read_text(encoding="utf-8")


def list_available_queries() -> List[str]:
    """
    List all available query names.
    
    Returns:
        List of query names (without .graphql extension)
    """
    if not QUERIES_DIR.exists():
        return []
    return [f.stem for f in QUERIES_DIR.glob("*.graphql")]


# Pre-defined query names for easy reference
class QueryNames:
    """Constants for query names to avoid typos."""
    USER_PROFILE = "get_user_profile"
    USER_REPOSITORIES = "get_user_repositories"
    REPOSITORY_DETAILS = "get_repository_details"
    USER_CONTRIBUTIONS = "get_user_contributions"
    CONTRIBUTION_STATS = "get_contribution_stats"
    FILE_CONTENT = "get_file_content"
    DIRECTORY_TREE = "get_directory_tree"


# Export commonly used items
__all__ = [
    "load_query",
    "list_available_queries",
    "QueryNames",
    "QUERIES_DIR",
]
