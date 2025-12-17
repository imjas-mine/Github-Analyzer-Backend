from openai import AsyncOpenAI
from app.core.config import settings
import json
import redis.asyncio as redis
import hashlib


class OpenAIService:
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = "gpt-4o-mini"
        self.redis = redis.from_url(settings.REDIS_URL, decode_responses=True)

    async def send_prompt(self, system_prompt: str, user_prompt: str):
        prompt_hash = hashlib.md5((system_prompt + user_prompt).encode()).hexdigest()

        cache_key = f"openai:{prompt_hash}"

        cached_data = await self.redis.get(cache_key)
        if cached_data:
            print("Using cached response")
            return json.loads(cached_data)

        print("Sending prompt to OpenAI...")

        response = await self.client.chat.completions.create(
            model=self.model,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        print("Response from OpenAI, the response is:", response)
        content = response.choices[0].message.content
        print("Response from OpenAI, the content is:", content)

        print("Storing response in cache...")
        await self.redis.set(cache_key, content, ex=3600)

        return json.loads(content)

    async def analyze_repository(self, ctx: dict) -> dict:
        system_prompt = """You help hiring managers understand GitHub projects quickly.
Analyze the repo and return JSON with:
{"description":"2-3 sentence summary explaining what this project does, its purpose, and key features","technologies":["list ONLY major frameworks, languages, databases, and infrastructure tools"]}

**CRITICAL - Technologies List Rules:**
Only include HIGH-LEVEL technologies that define the project stack:
✅ INCLUDE: Programming languages (Python, JavaScript, TypeScript, Java), Major frameworks (React, Django, Spring Boot, Express, FastAPI, Next.js), Databases (PostgreSQL, MongoDB, Redis), Infrastructure (Docker, Kubernetes, AWS, Firebase), Build tools (Webpack, Vite), ORMs (Prisma, SQLAlchemy, Hibernate)

❌ EXCLUDE: Utility libraries (uuid, dotenv, cors, helmet, morgan), Dev tools (nodemon, eslint, prettier), Small helpers (lodash, moment, axios)

Examples:
- Good: ["TypeScript", "React", "Next.js", "PostgreSQL", "Prisma", "Docker"]
- Bad: ["TypeScript", "React", "Next.js", "PostgreSQL", "Prisma", "Docker", "uuid", "dotenv", "cors", "nodemon", "eslint"]

Be thorough detecting technologies from:
- File names: package.json/node_modules=Node.js, requirements.txt/venv=Python, pom.xml/gradle=Java
- Config files: next.config=Next.js, vite.config=Vite, angular.json=Angular, vue.config=Vue
- Folders: prisma/=Prisma, .github/workflows=GitHub Actions, docker-compose=Docker

**IMPORTANT**: If a config file (package.json, pom.xml, etc.) is provided, extract:
1. Project description/name from metadata
2. ONLY major frameworks from dependencies (ignore utilities)
3. Specific versions of major frameworks only
Use this as the PRIMARY source of truth for technologies."""

        # Format lists compactly
        files = "\n".join(ctx.get("files", []))
        langs = ", ".join(ctx.get("langs", [])) or "Unknown"
        topics = ", ".join(ctx.get("topics", [])) or "None"

        # Build user prompt with config file if available
        config_section = ""
        if ctx.get("config_content"):
            config_section = f"""
Config File ({ctx.get("config_file")}):
{ctx.get("config_content")}
"""

        user_prompt = f"""Repo: {ctx.get("name")}
Desc: {ctx.get("desc") or "None"}
Topics: {topics}
Langs: {langs}
Files:
{files}
README:
{ctx.get("readme") or "None"}{config_section}"""

        # Log the context being sent to AI
        print("\n" + "=" * 60)
        print("CONTEXT SENT TO AI:")
        print("=" * 60)
        print(user_prompt)
        print("=" * 60 + "\n")

        return await self.send_prompt(system_prompt, user_prompt)
