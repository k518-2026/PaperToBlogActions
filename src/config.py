import os
from pathlib import Path
from typing import List
from dotenv import load_dotenv

# Load .env file if present
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)
STORAGE_FILE = DATA_DIR / "posted_papers.json"

class Config:
    BASE_DIR: Path = BASE_DIR

    # Gemini API settings
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_TEXT_MODEL: str = os.getenv("GEMINI_TEXT_MODEL", "gemini-3.7-flash")
    GEMINI_IMAGE_MODEL: str = os.getenv("GEMINI_IMAGE_MODEL", "gemini-3.1-flash-image")

    # Contact email for OpenAlex / Academic APIs
    CONTACT_EMAIL: str = os.getenv("CONTACT_EMAIL", "bot@example.com")

    # WordPress Post by Email settings
    WP_POST_EMAIL: str = os.getenv("WP_POST_EMAIL", "")
    WP_POST_STATUS: str = os.getenv("WP_POST_STATUS", "publish")  # 'publish' or 'draft'
    WP_CATEGORIES: str = os.getenv("WP_CATEGORIES", "情報教育,プログラミング教育,コンピューテーショナルシンキング")
    WP_TAGS: str = os.getenv("WP_TAGS", "論文紹介,海外研究,教育工学,STEM教育")

    # SMTP Server settings
    SMTP_HOST: str = os.getenv("SMTP_HOST", "smtp.gmail.com")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USER: str = os.getenv("SMTP_USER", "")
    SMTP_PASS: str = os.getenv("SMTP_PASS", "")

    # Paper Search Keywords (English academic query sets)
    SEARCH_TOPICS: List[dict] = [
        {
            "name": "コンピューテーショナルシンキング",
            "arxiv_query": 'all:"computational thinking"',
            "openalex_query": '"computational thinking"'
        },
        {
            "name": "プログラミング教育",
            "arxiv_query": 'all:"programming education" OR all:"teaching programming" OR all:"introductory programming"',
            "openalex_query": '"programming education" OR "introductory programming"'
        },
        {
            "name": "情報教育",
            "arxiv_query": 'all:"computer science education" OR all:"computing education" OR all:"informatics education"',
            "openalex_query": '"computer science education" OR "computing education"'
        }
    ]

    # File paths
    STORAGE_PATH: Path = STORAGE_FILE

    @classmethod
    def validate_for_posting(cls):
        """Check if all required credentials are set for posting."""
        missing = []
        if not cls.GEMINI_API_KEY:
            missing.append("GEMINI_API_KEY")
        if not cls.WP_POST_EMAIL:
            missing.append("WP_POST_EMAIL")
        if not cls.SMTP_USER:
            missing.append("SMTP_USER")
        if not cls.SMTP_PASS:
            missing.append("SMTP_PASS")
        return missing
