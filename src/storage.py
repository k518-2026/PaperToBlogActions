import json
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

class StorageManager:
    """
    Manages the persistent list of posted papers, preventing duplicate posts
    by matching paper IDs, DOIs, URLs, and normalized titles.
    Automatically generates and synchronizes data/POSTED_PAPERS.md.
    """

    def __init__(self, file_path: Path):
        self.file_path = file_path
        self.md_path = file_path.parent / "POSTED_PAPERS.md"
        self._ensure_file()

    @staticmethod
    def normalize_title(title: Optional[str]) -> str:
        """Normalize paper title for fuzzy duplicate detection."""
        if not title:
            return ""
        # Remove non-alphanumeric characters, lowercase, and collapse spaces
        cleaned = re.sub(r"[^\w\s]", "", title.lower())
        return " ".join(cleaned.split())

    def _ensure_file(self):
        if not self.file_path.exists():
            initial_data = {
                "last_updated": None,
                "total_posted": 0,
                "posted_ids": [],
                "posted_titles": [],
                "posts": []
            }
            self.file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump(initial_data, f, indent=2, ensure_ascii=False)
            self._sync_markdown(initial_data)
        elif not self.md_path.exists():
            try:
                with open(self.file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self._sync_markdown(data)
            except Exception as e:
                logger.warning(f"Failed to sync markdown on ensure: {e}")

    def load_data(self) -> Dict[str, Any]:
        self._ensure_file()
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if "posted_titles" not in data:
                    data["posted_titles"] = [self.normalize_title(p.get("title")) for p in data.get("posts", [])]
                return data
        except Exception as e:
            logger.error(f"Error loading {self.file_path}: {e}")
            return {"last_updated": None, "total_posted": 0, "posted_ids": [], "posted_titles": [], "posts": []}

    def is_posted(self, paper_id: str, title: str = "") -> bool:
        """
        Check if the paper was already posted by ID, DOI, URL, or normalized title.
        """
        if not paper_id and not title:
            return False

        data = self.load_data()

        # Check by paper ID
        if paper_id:
            normalized_id = paper_id.strip().lower()
            posted_ids = [str(x).strip().lower() for x in data.get("posted_ids", [])]
            if normalized_id in posted_ids:
                logger.info(f"Duplicate found by ID: {paper_id}")
                return True

        # Check by normalized title
        if title:
            norm_title = self.normalize_title(title)
            posted_titles = [self.normalize_title(t) for t in data.get("posted_titles", [])]
            if norm_title in posted_titles:
                logger.info(f"Duplicate found by title: {title}")
                return True

        return False

    def record_post(self, paper: Dict[str, Any], blog_title: str):
        """
        Record a newly posted paper and update POSTED_PAPERS.md.
        """
        data = self.load_data()
        paper_id = paper.get("id") or paper.get("doi") or paper.get("url")
        paper_title = paper.get("title", "")
        citation_count = paper.get("cited_by_count", 0)

        if not paper_id:
            logger.warning("Paper missing identifier, cannot record accurately.")
            return

        normalized_id = paper_id.strip().lower()
        posted_ids = [str(x).strip().lower() for x in data.get("posted_ids", [])]
        if normalized_id not in posted_ids:
            data.setdefault("posted_ids", []).append(paper_id)

        norm_title = self.normalize_title(paper_title)
        posted_titles = [self.normalize_title(t) for t in data.get("posted_titles", [])]
        if norm_title and norm_title not in posted_titles:
            data.setdefault("posted_titles", []).append(paper_title)

        post_entry = {
            "id": paper_id,
            "title": paper_title,
            "cited_by_count": citation_count,
            "source": paper.get("source"),
            "blog_title": blog_title,
            "url": paper.get("url"),
            "posted_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        data.setdefault("posts", []).append(post_entry)
        data["total_posted"] = len(data["posts"])
        data["last_updated"] = datetime.now().isoformat()

        # Save JSON
        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        logger.info(f"Recorded paper {paper_id} to {self.file_path}")

        # Update Markdown list
        self._sync_markdown(data)

    def _sync_markdown(self, data: Dict[str, Any]):
        """Generate a clean human-readable POSTED_PAPERS.md table."""
        lines = [
            "# 📚 投稿済み論文管理リスト（二重投稿防止）",
            "",
            f"- **最終更新日時**: {data.get('last_updated') or '未実行'}",
            f"- **総投稿件数**: {data.get('total_posted', 0)} 件",
            "",
            "本システムはこのリストと照合し、同じ論文が二重投稿されないよう自動管理しています。",
            "",
            "| No | 投稿日時 | 被引用数 | 論文タイトル | ソース | ブログ記事タイトル | 原文リンク |",
            "| :---: | :---: | :---: | :--- | :---: | :--- | :---: |"
        ]

        posts = data.get("posts", [])
        if not posts:
            lines.append("| - | - | - | （まだ投稿された論文はありません） | - | - | - |")
        else:
            for idx, p in enumerate(reversed(posts), 1):
                posted_at = p.get("posted_at", "")[:16]
                citations = p.get("cited_by_count", "-")
                title = (p.get("title") or "").replace("|", "\\|")
                source = p.get("source", "")
                blog_title = (p.get("blog_title") or "").replace("|", "\\|")
                url = p.get("url", "")
                link_md = f"[リンク]({url})" if url else "-"
                lines.append(f"| {idx} | {posted_at} | **{citations}** | {title} | {source} | {blog_title} | {link_md} |")

        lines.append("")
        with open(self.md_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        logger.info(f"Synchronized markdown list: {self.md_path}")
