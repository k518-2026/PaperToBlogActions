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
            "title": "A Study on Computational Thinking",
            "source": "arXiv",
            "url": "https://arxiv.org/abs/1234.5678"
        }
        storage.record_post(paper, "【最新研究】コンピュテーショナルシンキングの研究")

        assert storage.is_posted("test-paper-1")
        assert storage.is_posted("TEST-PAPER-1")  # Case insensitive

        data = storage.load_data()
        assert data["total_posted"] == 1
        assert len(data["posts"]) == 1
        assert data["posts"][0]["title"] == "A Study on Computational Thinking"
        print("test_storage_manager passed!")

if __name__ == "__main__":
    test_storage_manager()
