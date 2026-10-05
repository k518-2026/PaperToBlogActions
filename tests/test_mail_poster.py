import sys
import tempfile
from pathlib import Path

# Add project root to sys.path so test can run directly
sys.path.insert(0, str(Path(__file__).parent.parent))

from PIL import Image
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage

def test_mime_structure():
    with tempfile.TemporaryDirectory() as tmp_dir:
        img_path = Path(tmp_dir) / "test_image.png"
        img = Image.new("RGB", (100, 100), color=(0, 128, 255))
        img.save(img_path)

        msg = MIMEMultipart("related")
        msg["Subject"] = "Test Post Title"
        msg["From"] = "sender@example.com"
        msg["To"] = "post@wordpress.com"

        alt_part = MIMEMultipart("alternative")
        msg.attach(alt_part)
        alt_part.attach(MIMEText("Fallback text", "plain", "utf-8"))
        alt_part.attach(MIMEText("<h1>Test HTML</h1>", "html", "utf-8"))

        with open(img_path, "rb") as f:
            mime_img = MIMEImage(f.read(), _subtype="png")
        mime_img.add_header("Content-Disposition", "attachment", filename=img_path.name)
        msg.attach(mime_img)

        # Verify MIME payload
        assert len(msg.get_payload()) == 2
        print("test_mime_structure passed!")

def test_sanitize_html_for_email():
    from src.mail_poster import WordPressMailPoster

    sample_html = (
        '<h2>1. どんなもの？</h2>\n'
        '<p>本研究は<a href="https://ja.wikipedia.org/wiki/情報教育" target="_blank">情報教育</a>に関する研究である。</p>\n'
        '<p>引用: <a href="https://doi.org/10.1145/3444944">https://doi.org/10.1145/3444944</a></p>\n'
        '<p>写真: Photo by <a href="https://unsplash.com/@photographer">Photographer</a> on <a href="https://unsplash.com">Unsplash</a></p>\n'
        '<p>DOIリンク: DOI: https://doi.org/10.1016/j.caeai.2023.100147</p>\n'
    )

    sanitized = WordPressMailPoster.sanitize_html_for_email(sample_html)

    # Must NOT contain any <a href="..."> tags
    assert "<a " not in sanitized, f"Found <a tag in sanitized HTML: {sanitized}"
    assert "</a>" not in sanitized, f"Found </a> tag in sanitized HTML: {sanitized}"

    # Must preserve plain inner text of links
    assert "情報教育に関する研究である。" in sanitized
    assert "Photo by Photographer on Unsplash" in sanitized

    # Must convert DOI URLs to plain text notation 'DOI: 10.xxxx/...'
    assert "DOI: 10.1145/3444944" in sanitized
    assert "DOI: 10.1016/j.caeai.2023.100147" in sanitized
    assert "DOI: DOI:" not in sanitized

    print("test_sanitize_html_for_email passed successfully!")

if __name__ == "__main__":
    test_mime_structure()
    test_sanitize_html_for_email()

