import io
import os
import base64
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from PIL import Image, ImageDraw, ImageFont

logger = logging.getLogger(__name__)

class GeminiImageGenerator:
    """
    Generates structured 1-sheet educational infographic illustrations
    (modeled after Japanese graphic recording / educational manga summary sheets)
    using Gemini Image Generation (gemini-3.1-flash-image / imagen-3.0-generate-002).
    Includes an aesthetic 3-column infographic fallback using Pillow.
    """

    def __init__(self, api_key: str, model_name: str = "gemini-3.1-flash-image"):
        self.api_key = api_key
        self.model_name = model_name
        self._client = None

    @property
    def client(self):
        if self._client is None:
            from google import genai
            self._client = genai.Client(api_key=self.api_key)
        return self._client

    def generate_infographic(
        self,
        summary_data: Dict[str, Any],
        output_path: Path
    ) -> Optional[Path]:
        """
        Generate a comprehensive 1-sheet Japanese educational infographic poster.
        """
        from google.genai import types

        title = summary_data.get("infographic_title") or summary_data.get("blog_title", "教育研究まとめ")
        col1 = summary_data.get("infographic_col1", "Background, computational thinking metrics, student with tablet, radar charts")
        col2 = summary_data.get("infographic_col2", "Classroom practice, teacher coaching student, active learning, interactive software")
        col3 = summary_data.get("infographic_col3", "Key findings, security icons, qualitative and quantitative balance, educational guidelines")
        base_prompt = summary_data.get("infographic_prompt", "")

        # Formulate explicit visual prompt replicating the user's sample style
        refined_prompt = (
            f"A detailed Japanese educational infographic illustration and graphic recording poster summarizing: '{title}'. "
            f"Layout structure: 16:9 widescreen composition with 3 clearly defined vertical panels and a prominent top header banner. "
            f"Top Header: A decorative dark blue/teal banner ribbon with Japanese headline. "
            f"Panel 1 (Left): ① Background and Concept Visualization: {col1}. Include a student in school uniform using a digital tablet, colorful educational data charts (radar chart, progress line graph), and metric badges. "
            f"Panel 2 (Center): ② Classroom Practice and Practical Scenes: {col2}. Include a friendly Japanese teacher advising a student, classroom collaboration, interactive learning screen, and speech callout bubbles. "
            f"Panel 3 (Right): ③ Key Findings and Essential Guidelines: {col3}. Include security shield and lock icons, a balance scale comparing quantitative and qualitative factors, and warm smiling characters. "
            f"Art Style: Clean Japanese educational manga and textbook illustration style, cute anime characters, soft clean outlines, modern flat colors, rounded rectangular card frames with thin borders, teal and soft pastel background palette. Highly structured and easy to read. "
            f"Additional context: {base_prompt}"
        )

        logger.info(f"Generating 1-sheet infographic illustration: {refined_prompt[:140]}...")

        # Strategy 1: generate_content with response_modalities=["IMAGE"] (Gemini 3.1 Flash Image)
        for img_model in [self.model_name, "gemini-3.1-flash-image", "gemini-3-pro-image-preview"]:
            try:
                logger.info(f"Attempting image generation via generate_content ({img_model})...")
                response = self.client.models.generate_content(
                    model=img_model,
                    contents=refined_prompt,
                    config=types.GenerateContentConfig(
                        response_modalities=["IMAGE"],
                        image_config=types.ImageConfig(aspect_ratio="16:9")
                    )
                )
                if hasattr(response, "parts") and response.parts:
                    for part in response.parts:
                        if getattr(part, "inline_data", None):
                            output_path.parent.mkdir(parents=True, exist_ok=True)
                            gen_img = part.as_image()
                            gen_img.save(output_path)
                            logger.info(f"Successfully generated infographic via generate_content ({img_model}): {output_path}")
                            return output_path
            except Exception as e:
                logger.warning(f"generate_content with {img_model} failed: {e}")

        # Strategy 2: Interactions API with response_modalities=['IMAGE']
        try:
            logger.info("Attempting infographic generation via interactions API...")
            interaction = self.client.interactions.create(
                model=self.model_name,
                input=refined_prompt,
                response_modalities=["IMAGE"]
            )
            for out in getattr(interaction, "outputs", []):
                if getattr(out, "type", "") == "image" and hasattr(out, "data"):
                    output_path.parent.mkdir(parents=True, exist_ok=True)
                    img_bytes = base64.b64decode(out.data) if isinstance(out.data, str) else out.data
                    with open(output_path, "wb") as f:
                        f.write(img_bytes)
                    logger.info(f"Successfully generated infographic via interactions API: {output_path}")
                    return output_path
        except Exception as e:
            logger.warning(f"Interactions image generation failed: {e}")

        # Strategy 3: Imagen 3 / 4 (models.generate_images)
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
                    return output_path
            except Exception as e:
                logger.warning(f"{imagen_model} generation failed: {e}")

        # Strategy 4: Fallback Pillow 3-column infographic
        logger.info("AI image generation unavailable or restricted. Creating 3-column educational infographic card sheet...")
        return self._create_fallback_infographic(title, output_path)

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
        draw.text((x1 + 35, y_top + 230), "生徒の端末活用・思考傾向", fill=(15, 118, 110))
        draw.rounded_rectangle([x1 + 40, y_top + 265, x1 + 120, y_top + 335], radius=8, fill=(13, 148, 136))
        draw.text((x1 + 55, y_top + 290), "Tablet", fill=(255, 255, 255))
        draw.text((x1 + 135, y_top + 275), "・リアルタイム把握\n・弱点の早期発見\n・個別最適な支援", fill=(51, 65, 85))
        # Card C (Key points)
        draw.text((x1 + 35, y_top + 380), "【要点】データに基づく\n学習者の思考プロセスの可視化", fill=(71, 85, 105))

        # Column 2: 現場での授業活用シーン
        x2 = x_positions[1]
        draw.rounded_rectangle([x2, y_top, x2 + col_width, y_top + col_height], radius=12, fill=(255, 255, 255), outline=(220, 230, 230), width=2)
        draw.rounded_rectangle([x2 + 15, y_top + 15, x2 + 240, y_top + 50], radius=18, fill=(42, 157, 143))
        draw.text((x2 + 30, y_top + 23), "2. 授業・現場の活用シーン", fill=(255, 255, 255))
        scenes = [
            ("1. 個別指導・対話", "生徒ごとのニーズに応じた段階的フィードバック"),
            ("2. 授業改善の計画", "理解度データに応じたカリキュラム最適化"),
            ("3. 協調学習のファシリテート", "グループワークにおける対話と思考の促進"),
            ("4. 教員間の連携", "データ共有による多角的な教育支援体制")
        ]
        y_scene = y_top + 70
        for s_title, s_desc in scenes:
            draw.rounded_rectangle([x2 + 20, y_scene, x2 + col_width - 20, y_scene + 75], radius=8, fill=(248, 250, 252), outline=(226, 232, 240))
            draw.text((x2 + 35, y_scene + 10), s_title, fill=(30, 41, 59))
            draw.text((x2 + 35, y_scene + 35), s_desc[:24], fill=(100, 116, 139))
            y_scene += 90

        # Column 3: 成果と実践の留意点
        x3 = x_positions[2]
        draw.rounded_rectangle([x3, y_top, x3 + col_width, y_top + col_height], radius=12, fill=(255, 255, 255), outline=(220, 230, 230), width=2)
        draw.rounded_rectangle([x3 + 15, y_top + 15, x3 + 240, y_top + 50], radius=18, fill=(231, 111, 81))
        draw.text((x3 + 30, y_top + 23), "3. 成果と実践の留意点", fill=(255, 255, 255))
        points = [
            ("1. プライバシーと保護", "学習履歴の安全な管理と倫理的配慮"),
            ("2. 定量と定性の調和", "数値データだけでなく生徒の観察を重視"),
            ("3. 主体性の尊重", "AIやツールに依存せず試行錯誤を保障"),
            ("4. 教育的効果の実証", "思考力・問題解決力の継続的アセスメント")
        ]
        y_point = y_top + 70
        for p_title, p_desc in points:
            draw.rounded_rectangle([x3 + 20, y_point, x3 + col_width - 20, y_point + 75], radius=8, fill=(255, 251, 235), outline=(254, 215, 170))
            draw.text((x3 + 35, y_point + 10), p_title, fill=(154, 52, 18))
            draw.text((x3 + 35, y_point + 35), p_desc[:24], fill=(120, 53, 15))
            y_point += 90

        output_path.parent.mkdir(parents=True, exist_ok=True)
        img.save(output_path, "PNG")
        logger.info(f"Saved 3-column infographic fallback: {output_path}")
        return output_path
