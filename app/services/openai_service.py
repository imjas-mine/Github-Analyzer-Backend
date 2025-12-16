from openai import AsyncOpenAI
from app.core.config import settings
import json


class OpenAIService:
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = "gpt-4o-mini"

    async def send_prompt(self, system_prompt: str, user_prompt: str):
        response = await self.client.chat.completions.create(
            model=self.model,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        return json.loads(response.choices[0].message.content)

    async def analyze_repository(self, ctx: dict) -> dict:
        system_prompt = """You help hiring managers understand GitHub projects quickly.
Analyze the repo and return JSON with:
{"description":"2-3 sentence summary explaining what this project does, its purpose, and key features","technologies":["list ALL frameworks, libraries, languages, databases, and tools used"]}

Be thorough detecting technologies from:
- File names: package.json/node_modules=Node.js, requirements.txt/venv=Python, pom.xml/gradle=Java, Gemfile=Ruby, go.mod=Go, Cargo.toml=Rust
- Config files: next.config=Next.js, vite.config=Vite, angular.json=Angular, vue.config=Vue, tailwind.config=Tailwind, tsconfig=TypeScript, .eslintrc=ESLint
- Folders: prisma/=Prisma, .github/workflows=GitHub Actions, docker-compose=Docker, terraform/=Terraform, k8s/=Kubernetes
- Dependencies in README or package files
List specific versions/names when possible (e.g., "React 18", "PostgreSQL", "Redis")."""

        # Format lists compactly
        files = "\n".join(ctx.get("files", []))
        langs = ", ".join(ctx.get("langs", [])) or "Unknown"
        topics = ", ".join(ctx.get("topics", [])) or "None"

        user_prompt = f"""Repo: {ctx.get("name")}
Desc: {ctx.get("desc") or "None"}
Topics: {topics}
Langs: {langs}
Files:
{files}
README:
{ctx.get("readme") or "None"}"""

        # Log the context being sent to AI
        print("\n" + "=" * 60)
        print("CONTEXT SENT TO AI:")
        print("=" * 60)
        print(user_prompt)
        print("=" * 60 + "\n")

        return await self.send_prompt(system_prompt, user_prompt)
