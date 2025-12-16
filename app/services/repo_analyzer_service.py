from app.services.openai_service import OpenAIService
from app.services.github_service import GitHubService


class RepoAnalyzerService:
    # Priority-ordered list of config files to analyze
    CONFIG_FILES = [
        "package.json",  # Node.js - highest priority
        "pom.xml",  # Java Maven
        "build.gradle",  # Java Gradle
        "pyproject.toml",  # Python (modern)
        "requirements.txt",  # Python (classic)
        "go.mod",  # Go
        "Cargo.toml",  # Rust
        "composer.json",  # PHP
        "Gemfile",  # Ruby
        "setup.py",  # Python (old)
    ]

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

    def _detect_config_file(self, files):
        """Detect the most relevant config file from the flattened file list"""
        for config_file in self.CONFIG_FILES:
            if config_file in files:
                return config_file
        return None

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

        # Flatten file tree
        files = self._flatten_tree((directory_tree or {}).get("entries", []))
        print("files after flattenign are:", files)
        # Detect and fetch config file content
        config_content = ""
        detected_config = self._detect_config_file(files)
        if detected_config:
            try:
                file_data = await self.github_service.get_file_content(
                    owner, repo, f"HEAD:{detected_config}"
                )
                config_content = file_data.get("text", "") if file_data else ""
                # Limit to prevent token overflow (most important parts are at the top)
                config_content = config_content[:2000]
            except Exception as e:
                print(f"Failed to fetch {detected_config}: {e}")
                config_content = ""

        context = {
            "name": repo_details.get("name", "Unknown"),
            "desc": repo_details.get("description") or "",
            "files": files,
            "langs": langs,
            "topics": topics,
            "readme": ((repo_details.get("readme") or {}).get("text", ""))[:500],
            "config_file": detected_config,
            "config_content": config_content,
        }

        return await self.openai_service.analyze_repository(context)
