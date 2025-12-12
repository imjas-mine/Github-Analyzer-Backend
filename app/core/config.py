from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "GitHub Analyzer"
    VERSION: str = "0.1.0"
    
    # These are read from Windows environment variables
    GITHUB_TOKEN: str = ""
    OPENAI_API_KEY: str = ""

settings = Settings()
