import os
from dotenv import load_dotenv
# config class for reading env file and turning it to an object
class Config():

    def __init__(self) -> None:
        load_dotenv()
    
    sentry_dsn = os.getenv("SENTRY_DSN")
    env = os.getenv("ENVIRONMENT")
    release = os.getenv("RELEASE")
    redis_url = os.getenv("REDIS_URL")
    llm_model = os.getenv("LLM_MODEL")
