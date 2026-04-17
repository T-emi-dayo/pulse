"""
Application Settings and Configuration
"""

from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
   """Application settings loaded from environment variables."""
   
      # Application
   APP_NAME: str = "Pulse AI Service"
   APP_VERSION: str ="v1"
   DEBUG: bool = False
  
   # API Keys
   GEMINI_API_KEY: str = ""
   NEWS_API_KEY: str = ""
   SERP_API_KEY: str = ""

   # Email (Resend)
   RESEND_API_KEY: str = ""
   DIGEST_FROM_EMAIL: str = ""   # must be a Resend-verified domain address
   DIGEST_TO_EMAIL: str = ""     # recipient — your personal email
   
   # LLM Configuration
   BASE_MODEL: str = "gemini-2.5-flash"
   BASE_TEMPERATURE: int = 0
   INGESTION_MODEL: str = "gemini-2.5-flash"
   INGESTION_TEMPERATURE: float = 0.1
   SUMMARIZATION_MODEL: str = "gemini-2.5-flash"

   class Config:
       env_file = ".env"
       env_file_encoding = "utf-8"


settings = Settings()

TOP_N_BY_SOURCE: dict[str, int] = {
    "github_release": 10,
    "docs": 10,
    "research_paper": 5,
    "news": 20,
    "blog": 10,
}

LOOKBACK_HOURS: int = 24
