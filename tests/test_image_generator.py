import io
import json
from pathlib import Path
from unittest.mock import patch, MagicMock
from PIL import Image
from src.image_generator import GeminiImageGenerator, UnsplashPhotoInfo

def test_unsplash_fetch_workflow():
    generator = GeminiImageGenerator(
        api_key="",
        unsplash_access_key="dummy_unsplash_key"
    )

    # Mock Unsplash search response
    dummy_photo_data = {
        "results": [
            {
                "id": "photo_123",
                "urls": {
                    "regular": "https://images.unsplash.com/photo-123-regular",
                    "full": "https://images.unsplash.com/photo-123-full"
                },
                "links": {
                    "download_location": "https://api.unsplash.com/photos/photo_123/download"
                },
                "user": {
                    "name": "Jane Doe",
                    "username": "janedoe",
                    "links": {
                        "html": "https://unsplash.com/@janedoe"
                    }
                },
                "alt_description": "Students programming computers in classroom"
            }
        ]
    }

    # Create dummy 1x1 image bytes
    dummy_img = Image.new("RGB", (100, 100), color=(10, 20, 30))
    img_buf = io.BytesIO()
    dummy_img.save(img_buf, format="PNG")
    dummy_img_bytes = img_buf.getvalue()

    download_endpoint_called = []

    def mock_urlopen(req, *args, **kwargs):
        url = req.full_url if hasattr(req, "full_url") else str(req)
        mock_resp = MagicMock()
        mock_resp.status = 200

        if "api.unsplash.com/search/photos" in url:
            mock_resp.read.return_value = json.dumps(dummy_photo_data).encode("utf-8")
        elif "api.unsplash.com/photos/photo_123/download" in url:
            download_endpoint_called.append(url)
            mock_resp.read.return_value = b'{"url": "https://unsplash.com/download"}'
        elif "images.unsplash.com" in url:
            mock_resp.read.return_value = dummy_img_bytes
        else:
            mock_resp.read.return_value = b""
        
        mock_resp.__enter__.return_value = mock_resp
        return mock_resp

    test_output_path = Path("temp/test_unsplash_eyecatch.png")

    with patch("urllib.request.urlopen", side_effect=mock_urlopen):
        summary_data = {
            "blog_title": "Test Educational Article",
            "unsplash_keywords": "robotics learning classroom"
        }
        res_path = generator.generate_infographic(summary_data, test_output_path)

        assert res_path == test_output_path
        assert test_output_path.exists()
        assert generator.last_photo_info is not None
        assert generator.last_photo_info.photographer_name == "Jane Doe"
        assert generator.last_photo_info.image_url == "https://images.unsplash.com/photo-123-regular"
        assert "utm_source=PaperToBlogActions" in generator.last_photo_info.attribution_html
        assert len(download_endpoint_called) == 1
        assert "client_id=dummy_unsplash_key" in download_endpoint_called[0]
        print("test_unsplash_fetch_workflow passed successfully!")

    if test_output_path.exists():
        test_output_path.unlink()

def test_pillow_infographic_fallback():
    generator = GeminiImageGenerator(api_key="")
    test_output_path = Path("temp/test_pillow_eyecatch.png")
    
    summary_data = {
        "blog_title": "Pillow Fallback Test",
        "infographic_title": "Pillow Test Title",
        "infographic_col1": "Col 1 details",
        "infographic_col2": "Col 2 details",
        "infographic_col3": "Col 3 details"
    }

    # Calling pillow fallback directly
    res_path = generator._create_fallback_infographic(summary_data["blog_title"], test_output_path)
    assert res_path == test_output_path
    assert test_output_path.exists()
    with Image.open(test_output_path) as img:
        assert img.size == (1280, 720)
    print("test_pillow_infographic_fallback passed successfully!")

    if test_output_path.exists():
        test_output_path.unlink()

if __name__ == "__main__":
    test_unsplash_fetch_workflow()
    test_pillow_infographic_fallback()
