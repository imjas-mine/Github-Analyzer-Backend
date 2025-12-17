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
        data = await self.send_query(QueryNames.USER_PROFILE, {"username": username})
        return data["user"]

    async def get_user_repositories(self, username: str):
        data = await self.send_query(
            QueryNames.USER_REPOSITORIES, {"username": username}
        )
        return data["user"]["repositories"]

    async def get_repository_details(self, owner: str, name: str):
        data = await self.get_cached_query(
            QueryNames.REPOSITORY_DETAILS, {"owner": owner, "name": name}, ttl=600
        )
        return data["repository"]

    async def get_directory_tree(self, owner: str, name: str):
        data = await self.get_cached_query(
            QueryNames.DIRECTORY_TREE, {"owner": owner, "name": name}, ttl=600
        )
        return data["repository"]["object"]

    async def get_contribution_stats(self, owner: str, name: str):
        data = await self.send_query(
            QueryNames.CONTRIBUTION_STATS, {"owner": owner, "name": name}
        )
        return data["repository"]

    async def get_file_content(self, owner: str, name: str, path: str):
        data = await self.get_cached_query(
            QueryNames.FILE_CONTENT,
            {"owner": owner, "name": name, "expression": path},
            ttl=600,
        )
        return data["repository"]["object"]

    async def get_user_contributions(self, owner: str, name: str, author_id: str):
        data = await self.send_query(
            QueryNames.USER_CONTRIBUTIONS,
            {"owner": owner, "name": name, "author_id": author_id},
        )
        return data["repository"]

    async def get_cached_query(self, query_name: str, variables: dict, ttl: int = 300):
        vars_str = json.dumps(variables or {}, sort_keys=True)
        cache_key = f"{query_name}:{vars_str}"
        try:
            cached_data = await self.redis.get(cache_key)
            if cached_data:
                return json.loads(cached_data)
        except Exception:
            pass

        data = await self.send_query(query_name, variables)

        try:
            await self.redis.set(cache_key, json.dumps(data), ex=ttl)
        except Exception:
            pass

        return data
