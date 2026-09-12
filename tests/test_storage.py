import json
import tempfile
from pathlib import Path
from src.storage import StorageManager

def test_storage_manager():
    with tempfile.TemporaryDirectory() as tmp_dir:
        file_path = Path(tmp_dir) / "test_posted.json"
        storage = StorageManager(file_path)

        assert not storage.is_posted("test-paper-1")

        paper = {
            "id": "test-paper-1",
            "title": "A Study on Computational Thinking in Schools",
            "cited_by_count": 450,
            "source": "OpenAlex",
            "url": "https://doi.org/10.1234/sample"
        }
        storage.record_post(paper, "【最新研究】コンピュテーショナルシンキングの研究")

        # Check deduplication by ID
        assert storage.is_posted("test-paper-1")
        assert storage.is_posted("TEST-PAPER-1")

        # Check deduplication by title (even with different ID or slight case differences)
        assert storage.is_posted("different-id-999", "a study on computational thinking in schools")

        # Verify JSON
        data = storage.load_data()
        assert data["total_posted"] == 1
        assert len(data["posts"]) == 1
        assert data["posts"][0]["cited_by_count"] == 450

        # Verify POSTED_PAPERS.md was created and contains the table row
        md_file = Path(tmp_dir) / "POSTED_PAPERS.md"
        assert md_file.exists()
        content = md_file.read_text(encoding="utf-8")
        assert "450" in content
        assert "A Study on Computational Thinking in Schools" in content
        assert "投稿済み論文管理リスト" in content
        print("test_storage_manager passed with POSTED_PAPERS.md sync!")

if __name__ == "__main__":
    test_storage_manager()
