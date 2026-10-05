import smtplib
import logging
import re
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

class WordPressMailPoster:
    """
    Posts content to WordPress via the Post by Email feature using SMTP.
    Attaches generated images to set as media/featured images.
    """

    def __init__(
        self,
        smtp_host: str,
        smtp_port: int,
        smtp_user: str,
        smtp_pass: str,
        wp_post_email: str
    ):
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.smtp_user = smtp_user
        self.smtp_pass = smtp_pass
        self.wp_post_email = wp_post_email

    @staticmethod
    def sanitize_html_for_email(html_text: str) -> str:
        """
        Sanitizes HTML content specifically for WordPress Post by Email:
        1. Strips all <a href="..."> tags while preserving anchor text.
        2. Normalizes DOI links and bare DOI URLs into plain text notation 'DOI: 10.xxxx/...'.
        3. Prevents outbound and inbound email anti-spam/anti-phishing filters from flagging the post.
        """
        if not html_text:
            return ""

        cleaned = html_text

        # 1. Convert <a href="...doi.org/10.xxx">...</a> to DOI: 10.xxx
        cleaned = re.sub(
            r'<a\b[^>]*href=["\']https?://(?:dx\.)?doi\.org/(10\.[^"\'\s>]+)["\'][^>]*>.*?</a>',
            r'DOI: \1',
            cleaned,
            flags=re.IGNORECASE | re.DOTALL
        )

        # 2. Convert <a href="...">DOI: 10.xxx</a> to DOI: 10.xxx
        cleaned = re.sub(
            r'<a\b[^>]*>(?:DOI:\s*)?(10\.[^<]+)</a>',
            r'DOI: \1',
            cleaned,
            flags=re.IGNORECASE
        )

        # 3. Strip any remaining <a> tags, keeping inner text (e.g. Wikipedia terms or attribution names)
        cleaned = re.sub(r'<a\b[^>]*>(.*?)</a>', r'\1', cleaned, flags=re.IGNORECASE | re.DOTALL)

        # 4. Convert bare DOI URLs (https://doi.org/10.xxxx) to plain 'DOI: 10.xxxx'
        cleaned = re.sub(r'(?:DOI:\s*)?https?://(?:dx\.)?doi\.org/(10\.[^\s<>\"\)\]】』]+)', r'DOI: \1', cleaned)

        # 5. Clean up any accidental duplicate "DOI: DOI: "
        cleaned = re.sub(r'(?:DOI:\s*)+', 'DOI: ', cleaned)

        return cleaned

    def send_post(
        self,
        title: str,
        html_content: str,
        image_path: Optional[Path] = None
    ) -> bool:
        """
        Constructs and sends a multipart MIME email to WordPress Post by Email.
        """
        if not self.wp_post_email:
            raise ValueError("WP_POST_EMAIL is not configured.")
        if not self.smtp_user or not self.smtp_pass:
            raise ValueError("SMTP credentials (SMTP_USER / SMTP_PASS) are not configured.")

        # Sanitize HTML content for email delivery (strip <a href="..."> tags, keep plain text notation like 'DOI: 10.xxxx/...')
        clean_html = self.sanitize_html_for_email(html_content)

        # Create outer message container
        msg = MIMEMultipart("related")
        msg["Subject"] = title
        msg["From"] = self.smtp_user
        msg["To"] = self.wp_post_email

        # Alternative part for text/html
        alt_part = MIMEMultipart("alternative")
        msg.attach(alt_part)

        # Plain text fallback
        plain_text = "この投稿を表示するにはHTML対応のメールクライアントが必要です。"
        alt_part.attach(MIMEText(plain_text, "plain", "utf-8"))

        # HTML content
        html_part = MIMEText(clean_html, "html", "utf-8")
        alt_part.attach(html_part)

        # Attach image if provided
        if image_path and image_path.exists():
            try:
                with open(image_path, "rb") as img_file:
                    img_data = img_file.read()

                suffix = image_path.suffix.lower()
                subtype = "png" if "png" in suffix else "jpeg"

                mime_img = MIMEImage(img_data, _subtype=subtype)
                mime_img.add_header("Content-Disposition", "attachment", filename=image_path.name)
                mime_img.add_header("Content-ID", f"<{image_path.stem}>")
                msg.attach(mime_img)
                logger.info(f"Attached image: {image_path.name} to email.")
            except Exception as e:
                logger.warning(f"Failed to attach image {image_path}: {e}")

        # Send through SMTP
        logger.info(f"Connecting to SMTP server {self.smtp_host}:{self.smtp_port}...")
        try:
            with smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=30) as server:
                server.ehlo()
                server.starttls()
                server.ehlo()
                server.login(self.smtp_user, self.smtp_pass)
                server.send_message(msg)
            logger.info(f"Successfully sent email post '{title}' to {self.wp_post_email}!")
            return True
        except Exception as e:
            logger.error(f"Failed to send email to WordPress: {e}")
            raise
