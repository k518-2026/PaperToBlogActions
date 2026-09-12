import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class StorageManager:
    def __init__(self, file_path: Path):
        self.file_path = file_path
        self._ensure_file()

    def _ensure_file(self):
        if not self.file_path.exists():
            initial_data = {
                "last_updated": None,
                "total_posted": 0,
                "posted_ids": [],
                "posts": []
            }
            self.file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump(initial_data, f, indent=2, ensure_ascii=False)

    def load_data(self) -> Dict[str, Any]:
        self._ensure_file()
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading {self.file_path}: {e}")
            return {"last_updated": None, "total_posted": 0, "posted_ids": [], "posts": []}

    def is_posted(self, paper_id: str) -> bool:
        if not paper_id:
            return False
        data = self.load_data()
        normalized_id = paper_id.strip().lower()
        posted_ids = [str(x).strip().lower() for x in data.get("posted_ids", [])]
        return normalized_id in posted_ids

    def record_post(self, paper: Dict[str, Any], blog_title: str):
        data = self.load_data()
        paper_id = paper.get("id") or paper.get("doi") or paper.get("url")
        if not paper_id:
            logger.warning("Paper missing identifier, cannot record accurately.")
            return

        normalized_id = paper_id.strip().lower()
        if normalized_id not in [str(x).strip().lower() for x in data.get("posted_ids", [])]:
            data.setdefault("posted_ids", []).append(paper_id)

        post_entry = {
            "id": paper_id,
            "title": paper.get("title"),
            "source": paper.get("source"),
            "blog_title": blog_title,
            "url": paper.get("url"),
            "posted_at": datetime.now().isoformat()
        }
        data.setdefault("posts", []).append(post_entry)
        data["total_posted"] = len(data["posts"])
        data["last_updated"] = datetime.now().isoformat()

        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        logger.info(f"Recorded paper {paper_id} to {self.file_path}")
