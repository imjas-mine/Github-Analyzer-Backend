import httpx
from app.core.config import settings
from app.graphql import load_query, QueryNames


class GitHubService:
    def __init__(self):
        self.url = "https://api.github.com/graphql"
        self.headers = {
            "Authorization": f"Bearer {settings.GITHUB_TOKEN}",
            "Content-Type": "application/json",
        }

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
        data = await self.send_query(
            QueryNames.REPOSITORY_DETAILS, {"owner": owner, "name": name}
        )
        return data["repository"]

    async def get_directory_tree(self, owner: str, name: str):
        data = await self.send_query(
            QueryNames.DIRECTORY_TREE, {"owner": owner, "name": name}
        )
        return data["repository"]["object"]

    async def get_contribution_stats(self, owner: str, name: str):
        data = await self.send_query(
            QueryNames.CONTRIBUTION_STATS, {"owner": owner, "name": name}
        )
        return data["repository"]

    async def get_file_content(self, owner: str, name: str, expression: str):
        data = await self.send_query(
            QueryNames.FILE_CONTENT,
            {"owner": owner, "name": name, "expression": expression},
        )
        return data["repository"]["object"]

    async def get_user_contributions(self, owner: str, name: str, author_id: str):
        data = await self.send_query(
            QueryNames.USER_CONTRIBUTIONS,
            {"owner": owner, "name": name, "author_id": author_id},
        )
        return data["repository"]
