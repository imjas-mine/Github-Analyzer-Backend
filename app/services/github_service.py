import httpx
from app.core.config import settings
from app.graphql import load_query, QueryNames

class GitHubService:

    def __init__(self):
        self.url="https://api.github.com/graphql"
        self.headers={
            "Authorization": f"Bearer {settings.GITHUB_TOKEN}",
            "Content-Type": "application/json",
        }


    async def send_query(self, query_name: str, variables: dict = None):
        query=load_query(query_name)
        payload={
            "query": query,
            "variables": variables or {},
        }

        async with httpx.AsyncClient() as client:
            response=await client.post(self.url, headers=self.headers, json=payload)

            result=response.json()
            if result.get("errors"):
                raise Exception(result["errors"][0]["message"])
            return result["data"]

    async def get_user_profile(self, username: str):

        data=await self.send_query(
            QueryNames.USER_PROFILE,
            {
                "username": username
            }
        )
        return data["user"]