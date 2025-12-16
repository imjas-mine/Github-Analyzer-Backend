from app.services.openai_service import OpenAIService
from app.services.github_service import GitHubService


class RepoAnalyzerService:
    def __init__(self):
        self.openai_service = OpenAIService()
        self.github_service = GitHubService()

    def _flatten_tree(self, entries, prefix=""):
        """Flatten directory tree to simple path list: src/, src/main.py"""
        paths = []
        if not entries:
            return paths
        for entry in entries:
            path = f"{prefix}{entry['name']}"
            if entry["type"] == "tree":
                paths.append(f"{path}/")
                nested = entry.get("object", {}).get("entries", [])
                paths.extend(self._flatten_tree(nested, f"{path}/"))
            else:
                paths.append(path)
        return paths

    async def analyze(self, owner: str, repo: str, username: str) -> dict:
        repo_details = await self.github_service.get_repository_details(owner, repo)
        directory_tree = await self.github_service.get_directory_tree(owner, repo)

        # Extract simple lists from GraphQL response
        langs = [
            e.get("node", {}).get("name")
            for e in repo_details.get("languages", {}).get("edges", [])
        ]
        topics = [
            n.get("topic", {}).get("name")
            for n in repo_details.get("repositoryTopics", {}).get("nodes", [])
        ]

        context = {
            "name": repo_details.get("name", "Unknown"),
            "desc": repo_details.get("description") or "",
            "files": self._flatten_tree((directory_tree or {}).get("entries", [])),
            "langs": langs,
            "topics": topics,
            "readme": ((repo_details.get("readme") or {}).get("text", ""))[:500],
        }

        return await self.openai_service.analyze_repository(context)
