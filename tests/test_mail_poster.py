import tempfile
from pathlib import Path
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

if __name__ == "__main__":
    test_mime_structure()
