import io
import os
import base64
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from PIL import Image, ImageDraw, ImageFont

logger = logging.getLogger(__name__)

class UnsplashPhotoInfo:
    """
    Holds Unsplash photo metadata strictly adhering to Unsplash API Guidelines:
    - Hotlinking directly to images.unsplash.com
    - Triggering the official download endpoint
    - Photographer and Unsplash attribution with utm_source and utm_medium=referral
    """
    def __init__(
        self,
        photo_id: str,
        image_url: str,
        photographer_name: str,
        photographer_url: str,
        download_location: str,
        alt_description: str = "",
        app_name: str = "PaperToBlogActions"
    ):
        self.photo_id = photo_id
        self.image_url = image_url
        self.photographer_name = photographer_name
        self.photographer_url = photographer_url
        self.download_location = download_location
        self.alt_description = alt_description
        self.app_name = app_name

    @property
    def attribution_html(self) -> str:
        return (
            f'Photo by <a href="{self.photographer_url}?utm_source={self.app_name}&utm_medium=referral" '
            f'target="_blank" rel="noopener noreferrer" style="color: #2563eb; text-decoration: underline;">{self.photographer_name}</a> '
            f'on <a href="https://unsplash.com/?utm_source={self.app_name}&utm_medium=referral" '
            f'target="_blank" rel="noopener noreferrer" style="color: #2563eb; text-decoration: underline;">Unsplash</a>'
        )

    @property
    def hotlink_img_html(self) -> str:
        alt = self.alt_description or "Educational research topic image"
        return (
            f'<div style="text-align: center; margin: 20px 0 30px 0;">\n'
            f'    <img src="{self.image_url}" alt="{alt}" style="width: 100%; max-height: 520px; object-fit: cover; border-radius: 8px; box-shadow: 0 4px 10px rgba(0,0,0,0.08);" />\n'
            f'    <p style="font-size: 0.85em; color: #64748b; margin-top: 8px;">{self.attribution_html}</p>\n'
            f'</div>'
        )


class GeminiImageGenerator:
    """
    Generates structured 1-sheet educational infographic illustrations
    or fetches high-resolution Unsplash photography in compliance with Unsplash API Guidelines.
    Includes an aesthetic 3-column infographic fallback using Pillow.
    """

    def __init__(
        self,
        api_key: str,
        model_name: str = "gemini-3.1-flash-image",
        unsplash_access_key: str = ""
    ):
        self.api_key = api_key
        self.model_name = model_name
        self.unsplash_access_key = (unsplash_access_key or "").strip()
        self.last_photo_info: Optional[UnsplashPhotoInfo] = None
        self._client = None

    @property
    def client(self):
        if self._client is None:
            from google import genai
            self._client = genai.Client(api_key=self.api_key)
        return self._client

    def _fetch_from_unsplash(
        self,
        summary_data: Dict[str, Any],
        output_path: Path,
        debug_logs: list
    ) -> Optional[UnsplashPhotoInfo]:
        """
        Fetches a relevant landscape photo from Unsplash API adhering strictly to API Guidelines:
        1. Query search based on unsplash_keywords or fallback terms.
        2. Hotlinking to original Unsplash CDN image URL.
        3. Triggering download tracking endpoint.
        4. Photographer and Unsplash attribution with utm params.
        """
        if not self.unsplash_access_key:
            return None

        import urllib.request
        import urllib.parse
        import json

        # Determine queries to search
        custom_kw = summary_data.get("unsplash_keywords", "").strip()
        queries = []
        if custom_kw:
            queries.append(custom_kw)

        # Fallback educational technology / programming topics
        for fb in [
            "computer science education classroom",
            "programming students learning",
            "classroom technology tablet coding",
            "artificial intelligence education learning"
        ]:
            if fb not in queries:
                queries.append(fb)

        for q in queries:
            try:
                logger.info(f"Searching Unsplash for query: '{q}'...")
                encoded = urllib.parse.quote(q)
                api_url = f"https://api.unsplash.com/search/photos?query={encoded}&orientation=landscape&content_filter=high&per_page=10"
                req = urllib.request.Request(
                    api_url,
                    headers={
                        "Authorization": f"Client-ID {self.unsplash_access_key}",
                        "Accept-Version": "v1",
                        "User-Agent": "PaperToBlogActions/1.0"
                    }
                )
                with urllib.request.urlopen(req, timeout=10) as resp:
                    if resp.status != 200:
                        debug_logs.append(f"Unsplash API returned HTTP {resp.status} for query '{q}'")
                        continue
                    data = json.loads(resp.read().decode("utf-8"))

                results = data.get("results", [])
                if not results:
                    debug_logs.append(f"Unsplash returned 0 results for query '{q}'")
                    continue

                # Select the best matching photo (first result)
                photo = results[0]
                img_url = photo.get("urls", {}).get("regular") or photo.get("urls", {}).get("full")
                if not img_url:
                    continue

                download_location = photo.get("links", {}).get("download_location")

                # Requirement 2: Trigger download tracking endpoint
                if download_location:
                    try:
                        sep = "&" if "?" in download_location else "?"
                        track_url = f"{download_location}{sep}client_id={self.unsplash_access_key}"
                        track_req = urllib.request.Request(track_url, headers={"User-Agent": "PaperToBlogActions/1.0"})
                        urllib.request.urlopen(track_req, timeout=5)
                        debug_logs.append(f"Unsplash download event triggered: {photo.get('id')}")
                    except Exception as te:
                        logger.warning(f"Unsplash download tracking notice: {te}")
                        debug_logs.append(f"Unsplash download tracking warning: {te}")

                # Download high-resolution image bytes for WordPress email attachment
                img_req = urllib.request.Request(img_url, headers={"User-Agent": "Mozilla/5.0"})
                with urllib.request.urlopen(img_req, timeout=15) as img_resp:
                    img_bytes = img_resp.read()

                output_path.parent.mkdir(parents=True, exist_ok=True)
                with open(output_path, "wb") as f:
                    f.write(img_bytes)

                user_info = photo.get("user", {})
                photographer_name = user_info.get("name") or user_info.get("username", "Photographer")
                photographer_url = user_info.get("links", {}).get("html", "https://unsplash.com")
                alt_desc = photo.get("alt_description") or photo.get("description") or summary_data.get("blog_title", "Research paper topic image")

                photo_info = UnsplashPhotoInfo(
                    photo_id=photo.get("id", ""),
                    image_url=img_url,
                    photographer_name=photographer_name,
                    photographer_url=photographer_url,
                    download_location=download_location or "",
                    alt_description=alt_desc,
                    app_name="PaperToBlogActions"
                )
                logger.info(f"Successfully fetched and hotlinked Unsplash photo by {photographer_name} ({len(img_bytes)} bytes)")
                debug_logs.append(f"Unsplash: Success (Photo by {photographer_name}, query: '{q}')")
                return photo_info

            except Exception as e:
                err_msg = f"Unsplash query '{q}' failed: {type(e).__name__} - {e}"
                logger.warning(err_msg)
                debug_logs.append(err_msg)

        return None

    def generate_infographic(
        self,
        summary_data: Dict[str, Any],
        output_path: Path
    ) -> Optional[Path]:
        """
        Generate a comprehensive 1-sheet Japanese educational infographic poster,
        or fetch a relevant Unsplash photograph if UNSPLASH_ACCESS_KEY is provided.
        """
        from google.genai import types

        self.last_photo_info = None
        debug_logs = []

        # Strategy 0: High-Resolution Unsplash Photography (if UNSPLASH_ACCESS_KEY is set)
        if self.unsplash_access_key:
            logger.info("Unsplash Access Key detected. Attempting to fetch relevant high-resolution photo...")
            unsplash_res = self._fetch_from_unsplash(summary_data, output_path, debug_logs)
            if unsplash_res:
                self.last_photo_info = unsplash_res
                self._save_debug_log(debug_logs, output_path)
                return output_path
            else:
                logger.warning("Unsplash photo retrieval failed or returned 0 results. Falling back to AI image generation...")

        title = summary_data.get("infographic_title") or summary_data.get("blog_title", "教育研究まとめ")
        col1 = summary_data.get("infographic_col1", "Background, computational thinking metrics, student with tablet, radar charts")
        col2 = summary_data.get("infographic_col2", "Classroom practice, teacher coaching student, active learning, interactive software")
        col3 = summary_data.get("infographic_col3", "Key findings, security icons, qualitative and quantitative balance, educational guidelines")
        base_prompt = summary_data.get("infographic_prompt", "")

        # Formulate explicit visual prompt starting with clear generative command
        refined_prompt = (
            f"Generate an image: A clean, high-resolution educational infographic illustration and graphic recording poster summarizing academic research: '{title}'. "
            f"Layout structure: 16:9 widescreen composition with 3 clearly defined vertical card panels and a prominent top title banner ribbon. "
            f"Top Header: A decorative dark blue/teal banner ribbon with clear headline. "
            f"Panel 1 (Left): ① Theoretical background & metrics: {col1}. Include a learner using a digital tablet, colorful educational data charts (radar chart, progress line graph), and achievement rate badges. "
            f"Panel 2 (Center): ② Classroom pedagogical practices: {col2}. Include a teacher guiding a learner, active learning collaboration, interactive educational software interface, and thought bubbles. "
            f"Panel 3 (Right): ③ Key findings and essential guidelines: {col3}. Include security shield icons, a balance scale comparing quantitative and qualitative factors, and helpful educational icons. "
            f"Visual Art Style: Modern Japanese educational graphic recording diagram, clean vector art, soft clean outlines, modern flat pastel colors, rounded rectangular cards with thin borders, light teal and cream background. Highly structured, professional and educational. "
            f"Additional context: {base_prompt}"
        )

        logger.info(f"Generating 1-sheet infographic illustration: {refined_prompt[:140]}...")

        # Model candidates for Gemini native image generation
        models_to_try = []
        for m in [self.model_name, "gemini-3.1-flash-image", "gemini-3.1-flash-image-preview", "gemini-3-pro-image-preview", "gemini-2.5-flash-image"]:
            if m and m not in models_to_try:
                models_to_try.append(m)

        # Strategy 1: generate_content with Gemini Image models
        for img_model in models_to_try:
            # 1a. Try with explicit IMAGE modality and 16:9 aspect ratio config
            try:
                logger.info(f"Attempting image generation via generate_content ({img_model}) with 16:9 config...")
                response = self.client.models.generate_content(
                    model=img_model,
                    contents=[refined_prompt],
                    config=types.GenerateContentConfig(
                        response_modalities=["IMAGE"],
                        image_config=types.ImageConfig(aspect_ratio="16:9")
                    )
                )
                if self._extract_and_save_image(response, output_path, debug_logs):
                    logger.info(f"Successfully generated infographic via generate_content ({img_model}): {output_path}")
                    self._save_debug_log(debug_logs, output_path)
                    return output_path
                else:
                    debug_logs.append(f"{img_model} (config): API call completed but no image binary was found in response.")
            except Exception as e:
                err_msg = f"{img_model} (config) failed: {type(e).__name__} - {e}"
                logger.warning(err_msg)
                debug_logs.append(err_msg)

            # 1b. Try without config (canonical simple pattern)
            try:
                logger.info(f"Attempting image generation via generate_content ({img_model}) default...")
                response = self.client.models.generate_content(
                    model=img_model,
                    contents=[refined_prompt]
                )
                if self._extract_and_save_image(response, output_path, debug_logs):
                    logger.info(f"Successfully generated infographic via generate_content ({img_model}) [simple]: {output_path}")
                    self._save_debug_log(debug_logs, output_path)
                    return output_path
                else:
                    debug_logs.append(f"{img_model} (simple): API call completed but no image binary was found in response.")
            except Exception as e:
                err_msg = f"{img_model} (simple) failed: {type(e).__name__} - {e}"
                logger.warning(err_msg)
                debug_logs.append(err_msg)

        # Strategy 2: Interactions API with response_modalities=['image']
        try:
            logger.info("Attempting infographic generation via interactions API...")
            interaction = self.client.interactions.create(
                model=self.model_name or "gemini-3.1-flash-image",
                input=refined_prompt,
                response_modalities=["image"]
            )
            for out in getattr(interaction, "outputs", []):
                if getattr(out, "type", "") == "image" and hasattr(out, "data"):
                    output_path.parent.mkdir(parents=True, exist_ok=True)
                    img_bytes = base64.b64decode(out.data) if isinstance(out.data, str) else out.data
                    with open(output_path, "wb") as f:
                        f.write(img_bytes)
                    logger.info(f"Successfully generated infographic via interactions API: {output_path}")
                    self._save_debug_log(debug_logs, output_path)
                    return output_path
            debug_logs.append("Interactions API completed but returned no image outputs.")
        except Exception as e:
            err_msg = f"Interactions image generation failed: {type(e).__name__} - {e}"
            logger.warning(err_msg)
            debug_logs.append(err_msg)

        # Strategy 3: Imagen models (models.generate_images)
        for imagen_model in ["imagen-3.0-generate-002", "imagen-4.0-generate-001"]:
            try:
                logger.info(f"Attempting infographic generation via models.generate_images ({imagen_model})...")
                result = self.client.models.generate_images(
                    model=imagen_model,
                    prompt=refined_prompt,
                    config=types.GenerateImagesConfig(
                        number_of_images=1,
                        output_mime_type="image/jpeg",
                        aspect_ratio="16:9"
                    )
                )
                if result.generated_images:
                    img_bytes = result.generated_images[0].image.image_bytes
                    output_path.parent.mkdir(parents=True, exist_ok=True)
                    with open(output_path, "wb") as f:
                        f.write(img_bytes)
                    logger.info(f"Successfully generated infographic via {imagen_model}: {output_path}")
                    self._save_debug_log(debug_logs, output_path)
                    return output_path
                else:
                    debug_logs.append(f"{imagen_model}: API call completed but generated_images was empty.")
            except Exception as e:
                err_msg = f"{imagen_model} generation failed: {type(e).__name__} - {e}"
                logger.warning(err_msg)
                debug_logs.append(err_msg)

        # Strategy 4: Free AI Infographic Generator Fallback (Pollinations.ai / FLUX)
        # Enables genuine AI-generated illustrations even when Google AI Studio API key is on Free Tier (limit: 0)
        try:
            logger.info("Attempting free AI infographic generation via Pollinations (FLUX)...")
            import urllib.parse
            import requests

            flux_prompt = (
                f"An aesthetic Japanese educational infographic illustration and graphic recording poster summarizing: {title}. "
                f"Three distinct vertical panel columns with educational charts, diagrams, digital learning tablet, and teacher guidance, "
                f"clean vector illustration, modern flat pastel colors, highly detailed, 16:9 widescreen composition."
            )
            encoded = urllib.parse.quote(flux_prompt)
            api_url = f"https://image.pollinations.ai/prompt/{encoded}?width=1280&height=720&model=flux&nologo=true"
            
            resp = requests.get(api_url, timeout=35, headers={"User-Agent": "Mozilla/5.0"})
            if resp.status_code == 200 and len(resp.content) > 10000:
                output_path.parent.mkdir(parents=True, exist_ok=True)
                with open(output_path, "wb") as f:
                    f.write(resp.content)
                logger.info(f"Successfully generated AI infographic via Pollinations FLUX ({len(resp.content)} bytes): {output_path}")
                debug_logs.append(f"Pollinations FLUX AI: Success ({len(resp.content)} bytes)")
                self._save_debug_log(debug_logs, output_path)
                return output_path
            else:
                debug_logs.append(f"Pollinations FLUX returned status {resp.status_code}")
        except Exception as e:
            err_msg = f"Pollinations FLUX generation failed: {type(e).__name__} - {e}"
            logger.warning(err_msg)
            debug_logs.append(err_msg)

        # Strategy 5: Fallback Pillow 3-column infographic
        logger.info("AI image generation unavailable or restricted. Creating 3-column educational infographic card sheet...")
        self._save_debug_log(debug_logs, output_path)
        return self._create_fallback_infographic(title, output_path)

    @staticmethod
    def _save_debug_log(debug_logs: list, output_path: Path):
        """Save image generation diagnostics log for inspection in artifacts."""
        try:
            log_file = output_path.parent / "image_generation_debug.txt"
            with open(log_file, "w", encoding="utf-8") as f:
                f.write("=== Gemini Image Generation Diagnostic Log ===\n")
                for entry in debug_logs:
                    f.write(f"- {entry}\n")
        except Exception:
            pass

    @staticmethod
    def _extract_and_save_image(response, output_path: Path, debug_logs: list = None) -> bool:
        """Helper to reliably extract and save image from SDK response candidates or parts."""
        # Check candidates first
        candidates = getattr(response, "candidates", None) or []
        for cand in candidates:
            finish_reason = getattr(cand, "finish_reason", None)
            if finish_reason and finish_reason != "STOP":
                msg = f"Candidate finish_reason: {finish_reason}"
                logger.warning(msg)
                if debug_logs is not None:
                    debug_logs.append(msg)
            content = getattr(cand, "content", None)
            parts = getattr(content, "parts", None) or []
            for part in parts:
                if getattr(part, "text", None):
                    snippet = part.text[:120].replace('\n', ' ')
                    msg = f"Candidate returned text part: {snippet}"
                    logger.info(msg)
                    if debug_logs is not None:
                        debug_logs.append(msg)
                if getattr(part, "inline_data", None):
                    try:
                        gen_img = part.as_image()
                        output_path.parent.mkdir(parents=True, exist_ok=True)
                        gen_img.save(output_path)
                        return True
                    except Exception:
                        pass
                    data = getattr(part.inline_data, "data", None)
                    if data:
                        if isinstance(data, str):
                            data = base64.b64decode(data)
                        output_path.parent.mkdir(parents=True, exist_ok=True)
                        with open(output_path, "wb") as f:
                            f.write(data)
                        return True

        # Check response.parts convenience property
        try:
            parts = getattr(response, "parts", None) or []
            for part in parts:
                if getattr(part, "inline_data", None):
                    try:
                        gen_img = part.as_image()
                        output_path.parent.mkdir(parents=True, exist_ok=True)
                        gen_img.save(output_path)
                        return True
                    except Exception:
                        pass
                    data = getattr(part.inline_data, "data", None)
                    if data:
                        if isinstance(data, str):
                            data = base64.b64decode(data)
                        output_path.parent.mkdir(parents=True, exist_ok=True)
                        with open(output_path, "wb") as f:
                            f.write(data)
                        return True
        except Exception:
            pass

        return False

    @staticmethod
    def _get_font(size: int):
        candidates = [
            "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
            "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
            "/usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc",
            "C:/Windows/Fonts/meiryo.ttc",
            "C:/Windows/Fonts/msgothic.ttc",
        ]
        for p in candidates:
            if os.path.exists(p):
                try:
                    return ImageFont.truetype(p, size)
                except Exception:
                    pass
        return ImageFont.load_default()

    def _create_fallback_infographic(self, title: str, output_path: Path) -> Path:
        """
        Renders a structured 3-column educational infographic visual summary
        matching the sample layout (Header banner + 3 rounded columns with icons/charts).
        """
        width, height = 1280, 720
        img = Image.new("RGB", (width, height), color=(240, 248, 247))
        draw = ImageDraw.Draw(img)

        font_header = self._get_font(26)
        font_badge = self._get_font(20)
        font_sub = self._get_font(18)
        font_body = self._get_font(15)

        # Outer decorative frame
        draw.rounded_rectangle([20, 20, width - 20, height - 20], radius=16, outline=(180, 215, 210), width=3)

        # Top Header Banner Ribbon
        draw.rounded_rectangle([220, 36, 1060, 100], radius=12, fill=(15, 76, 92))
        draw.rounded_rectangle([225, 41, 1055, 95], radius=10, outline=(255, 210, 63), width=2)
        display_title = (title[:32] + "...") if len(title) > 32 else title
        draw.text((260, 48), f"【研究図解】 {display_title}", fill=(255, 255, 255), font=font_header)

        # Column settings
        col_width = 370
        col_height = 560
        y_top = 125
        x_positions = [45, 455, 865]

        # Column 1: 背景・教育データの視覚化
        x1 = x_positions[0]
        draw.rounded_rectangle([x1, y_top, x1 + col_width, y_top + col_height], radius=12, fill=(255, 255, 255), outline=(220, 230, 230), width=2)
        draw.rounded_rectangle([x1 + 15, y_top + 15, x1 + 250, y_top + 52], radius=18, fill=(247, 127, 0))
        draw.text((x1 + 28, y_top + 20), "1. 概念・データの視覚化", fill=(255, 255, 255), font=font_badge)
        # Visual elements: Card A (Radar Chart representation)
        draw.rounded_rectangle([x1 + 20, y_top + 65, x1 + col_width - 20, y_top + 200], radius=8, fill=(248, 250, 252), outline=(203, 213, 225))
        draw.text((x1 + 35, y_top + 75), "個人の成長・進捗推移", fill=(30, 41, 59), font=font_sub)
        draw.polygon([(x1 + 100, y_top + 130), (x1 + 140, y_top + 110), (x1 + 170, y_top + 140), (x1 + 150, y_top + 180), (x1 + 90, y_top + 170)], outline=(14, 165, 233), width=2)
        draw.rounded_rectangle([x1 + 240, y_top + 120, x1 + 335, y_top + 158], radius=6, fill=(16, 185, 129))
        draw.text((x1 + 250, y_top + 128), "達成 92%", fill=(255, 255, 255), font=font_body)
        # Card B (Student tablet interaction)
        draw.rounded_rectangle([x1 + 20, y_top + 215, x1 + col_width - 20, y_top + 360], radius=8, fill=(240, 253, 250), outline=(153, 246, 228))
        draw.text((x1 + 35, y_top + 230), "生徒の端末活用・思考傾向", fill=(15, 118, 110), font=font_sub)
        draw.rounded_rectangle([x1 + 40, y_top + 265, x1 + 120, y_top + 335], radius=8, fill=(13, 148, 136))
        draw.text((x1 + 55, y_top + 290), "Tablet", fill=(255, 255, 255), font=font_sub)
        draw.text((x1 + 135, y_top + 275), "・リアルタイム把握\n・弱点の早期発見\n・個別最適な支援", fill=(51, 65, 85), font=font_body)
        # Card C (Key points)
        draw.text((x1 + 35, y_top + 380), "【要点】データに基づく\n学習者の思考プロセスの可視化", fill=(71, 85, 105), font=font_sub)

        # Column 2: 現場での授業活用シーン
        x2 = x_positions[1]
        draw.rounded_rectangle([x2, y_top, x2 + col_width, y_top + col_height], radius=12, fill=(255, 255, 255), outline=(220, 230, 230), width=2)
        draw.rounded_rectangle([x2 + 15, y_top + 15, x2 + 270, y_top + 50], radius=18, fill=(42, 157, 143))
        draw.text((x2 + 25, y_top + 23), "2. 授業・現場の活用シーン", fill=(255, 255, 255), font=font_badge)
        scenes = [
            ("1. 個別指導・対話", "生徒ごとのニーズに応じた段階的フィードバック"),
            ("2. 授業改善の計画", "理解度データに応じたカリキュラム最適化"),
            ("3. 協調学習のファシリテート", "グループワークにおける対話と思考の促進"),
            ("4. 教員間の連携", "データ共有による多角的な教育支援体制")
        ]
        y_scene = y_top + 70
        for s_title, s_desc in scenes:
            draw.rounded_rectangle([x2 + 20, y_scene, x2 + col_width - 20, y_scene + 75], radius=8, fill=(248, 250, 252), outline=(226, 232, 240))
            draw.text((x2 + 35, y_scene + 10), s_title, fill=(30, 41, 59), font=font_sub)
            draw.text((x2 + 35, y_scene + 35), s_desc[:24], fill=(100, 116, 139), font=font_body)
            y_scene += 90

        # Column 3: 成果と実践の留意点
        x3 = x_positions[2]
        draw.rounded_rectangle([x3, y_top, x3 + col_width, y_top + col_height], radius=12, fill=(255, 255, 255), outline=(220, 230, 230), width=2)
        draw.rounded_rectangle([x3 + 15, y_top + 15, x3 + 270, y_top + 50], radius=18, fill=(231, 111, 81))
        draw.text((x3 + 25, y_top + 23), "3. 成果と実践の留意点", fill=(255, 255, 255), font=font_badge)
        points = [
            ("1. プライバシーと保護", "学習履歴の安全な管理と倫理的配慮"),
            ("2. 定量と定性の調和", "数値データだけでなく生徒の観察を重視"),
            ("3. 主体性の尊重", "AIやツールに依存せず試行錯誤を保障"),
            ("4. 教育的効果の実証", "思考力・問題解決力の継続的アセスメント")
        ]
        y_point = y_top + 70
        for p_title, p_desc in points:
            draw.rounded_rectangle([x3 + 20, y_point, x3 + col_width - 20, y_point + 75], radius=8, fill=(255, 251, 235), outline=(254, 215, 170))
            draw.text((x3 + 35, y_point + 10), p_title, fill=(154, 52, 18), font=font_sub)
            draw.text((x3 + 35, y_point + 35), p_desc[:24], fill=(120, 53, 15), font=font_body)
            y_point += 90

        output_path.parent.mkdir(parents=True, exist_ok=True)
        img.save(output_path, "PNG")
        logger.info(f"Saved 3-column infographic fallback: {output_path}")
        return output_path
