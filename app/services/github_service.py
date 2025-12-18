import httpx
import redis.asyncio as redis
import json
from app.core.config import settings
from app.graphql import load_query, QueryNames


class GitHubService:
    def __init__(self):
        self.url = "https://api.github.com/graphql"
        self.headers = {
            "Authorization": f"Bearer {settings.GITHUB_TOKEN}",
            "Content-Type": "application/json",
        }
        self.redis = redis.from_url(settings.REDIS_URL, decode_responses=True)

    async def send_query(self, query_name: str, variables: dict = None):
        query = load_query(query_name)
        payload = {
            "query": query,
            "variables": variables or {},
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(self.url, headers=self.headers, json=payload)

            result = response.json()
            if result.get("errors"):
                raise Exception(result["errors"][0]["message"])
            return result["data"]

    async def get_user_profile(self, username: str):
        data = await self.get_cached_query(
            QueryNames.USER_PROFILE, {"username": username}, ttl=3600
        )
        return data["user"]

    async def get_user_repositories(self, username: str):
        data = await self.get_cached_query(
            QueryNames.USER_REPOSITORIES, {"username": username}, ttl=600
        )
        return data["user"]["repositories"]

    async def get_repository_details(self, owner: str, name: str):
        print("Fetching repository details from github api")
        data = await self.get_cached_query(
            QueryNames.REPOSITORY_DETAILS, {"owner": owner, "name": name}, ttl=600
        )
        return data["repository"]

    async def get_directory_tree(self, owner: str, name: str):
        print("Fetching directory tree from github api")
        data = await self.get_cached_query(
            QueryNames.DIRECTORY_TREE, {"owner": owner, "name": name}, ttl=600
        )
        return data["repository"]["object"]

    async def get_contribution_stats(self, owner: str, name: str, username: str):
        data = await self.get_cached_query(
            QueryNames.CONTRIBUTION_STATS,
            {"owner": owner, "name": name, "username": username},
            ttl=600,
        )
        print("Contribution stats:", data)
        return data["repository"]

    async def get_file_content(self, owner: str, name: str, path: str):
        print("Fetching file content from github api")
        data = await self.get_cached_query(
            QueryNames.FILE_CONTENT,
            {"owner": owner, "name": name, "expression": path},
            ttl=600,
        )
        return data["repository"]["object"]

    async def get_user_contributions(self, owner: str, name: str, username: str):
        # 1. Fetch User ID first (required for history filter)
        print(f"Fetching ID for user {username}")
        user_profile = await self.get_user_profile(username)
        author_id = user_profile.get("id")

        if not author_id:
            raise Exception(f"Could not find user ID for {username}")

        # 2. Fetch contributions using the ID
        print(f"Fetching contributions for {owner}/{name} using author ID {author_id}")

        data = await self.get_cached_query(
            QueryNames.USER_CONTRIBUTIONS,
            {"owner": owner, "name": name, "authorId": author_id},
            ttl=600,
        )

        # 3. Extract and return
        repo_data = data.get("repository", {})

        # Extract commits
        history = (
            repo_data.get("defaultBranchRef", {}).get("target", {}).get("history", {})
        )
        commits = history.get("nodes", []) if history else []

        return {"commits": commits, "total_count": len(commits)}

    async def get_cached_query(self, query_name: str, variables: dict, ttl: int = 300):
        vars_str = json.dumps(variables or {}, sort_keys=True)
        cache_key = f"{query_name}:{vars_str}"
        print(f"Checking cache for key: {cache_key}")
        try:
            cached_data = await self.redis.get(cache_key)
            if cached_data:
                print("Using cached response before sending query")
                return json.loads(cached_data)
            else:
                print("Cache miss")
                pass
        except Exception as e:
            print(f"DEBUG: Redis get error: {e}")

        data = await self.send_query(query_name, variables)

        try:
            await self.redis.set(cache_key, json.dumps(data), ex=ttl)
            print("Storing github api response in cache")
        except Exception as e:
            print(f"DEBUG: Redis set error: {e}")

        return data
