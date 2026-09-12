import argparse
import logging
import sys
from pathlib import Path

from .config import Config
from .storage import StorageManager
from .fetcher import PaperFetcher
from .summarizer import PaperSummarizer, PaperSummaryModel
from .image_generator import GeminiImageGenerator
from .mail_poster import WordPressMailPoster

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("PaperToBlogActions")

def run_pipeline(dry_run: bool = False, force: bool = False, selected_topic: str = None):
    logger.info("=== Starting Paper-to-Blog Pipeline ===")
    logger.info(f"Mode: {'DRY RUN' if dry_run else 'PRODUCTION (Live Posting)'}")

    storage = StorageManager(Config.STORAGE_PATH)

    # Filter topics if requested
    topics = Config.SEARCH_TOPICS
    if selected_topic:
        topics = [t for t in topics if selected_topic in t["name"]]
        if not topics:
            logger.error(f"Topic '{selected_topic}' not found in configuration.")
            return False

    # 1. Fetch unposted paper
    logger.info("--- Step 1: Fetching Paper ---")
    paper = PaperFetcher.get_latest_unposted_paper(storage, topics, force=force)
    if not paper:
        logger.info("No new papers found to post today. Terminating gracefully.")
        return True

    logger.info(f"Selected Paper: {paper.get('title')}")
    logger.info(f"Source: {paper.get('source')}, Published: {paper.get('published_date')}")

    # 2. Summarize with Gemini
    logger.info("--- Step 2: Summarizing Paper (Ochiai 7-Point Format) ---")
    if not Config.GEMINI_API_KEY:
        if dry_run:
            logger.warning("GEMINI_API_KEY is not set. Using dummy summary for dry-run simulation.")
            summary = PaperSummaryModel(
                blog_title=f"【解説】{paper.get('title')}",
                summary_lead="本論文は、プログラミング教育およびコンピュテーショナルシンキング育成における最新の実践的検証を行った研究です。",
                point1_what="研究の背景と概要：初等・中等教育におけるプログラミング指導の効果を実証的に調査した研究です。",
                point2_novelty="先行研究との違い：従来の座学中心のアプローチに対し、対話型AIを取り入れた新しい指導モデルを提案・評価しています。",
                point3_core="技術・手法のキモ：学習者の試行錯誤を促す段階的な足場かけ（Scaffolding）設計にあります。",
                point4_evaluation="検証方法：実際の教育現場で生徒を対象に事前・事後テストおよびアンケート調査を実施して有効性を検証しました。",
                point5_discussion="議論・課題：教員の指導負荷や、個々の学習者の習熟度に応じた個別最適化が今後の課題として挙げられています。",
                point6_next_papers="次に読むべき論文：Computational Thinking Assessmentに関する最新のレビュー論文やACM SIGCSEの関連文献が推奨されます。",
                point7_apa_citation=f"Author et al. (2026). {paper.get('title')}. Retrieved from {paper.get('url')}",
                image_prompt="A modern isometric 3D illustration of students learning programming and computational thinking with glowing digital blocks and friendly AI interfaces."
            )
        else:
            raise ValueError("GEMINI_API_KEY environment variable is required for production.")
    else:
        summarizer = PaperSummarizer(api_key=Config.GEMINI_API_KEY, model_name=Config.GEMINI_TEXT_MODEL)
        summary = summarizer.summarize(paper)

    logger.info(f"Generated Blog Title: {summary.blog_title}")

    # 3. Generate Image
    logger.info("--- Step 3: Generating Summary Illustration ---")
    temp_dir = Config.BASE_DIR / "temp"
    temp_dir.mkdir(exist_ok=True)
    image_path = temp_dir / "eyecatch.png"

    image_generator = GeminiImageGenerator(api_key=Config.GEMINI_API_KEY, model_name=Config.GEMINI_IMAGE_MODEL)
    generated_img_path = image_generator.generate_image(
        prompt=summary.image_prompt,
        output_path=image_path,
        title=summary.blog_title
    )

    # Format HTML post
    html_content = PaperSummarizer.format_html_post(
        summary=summary,
        paper=paper,
        categories=Config.WP_CATEGORIES,
        tags=Config.WP_TAGS,
        status=Config.WP_POST_STATUS
    )

    # 4. Post to WordPress by Email
    logger.info("--- Step 4: Posting to WordPress ---")
    if dry_run:
        logger.info("[DRY RUN] Email sending skipped.")
        preview_file = temp_dir / "preview_post.html"
        with open(preview_file, "w", encoding="utf-8") as f:
            f.write(f"<h1>{summary.blog_title}</h1>\n{html_content}")
        logger.info(f"[DRY RUN] HTML preview saved to: {preview_file}")
        logger.info(f"[DRY RUN] Eyecatch image saved to: {generated_img_path}")
        return True

    # Check credentials
    missing = Config.validate_for_posting()
    if missing:
        raise ValueError(f"Missing required configuration: {', '.join(missing)}")

    poster = WordPressMailPoster(
        smtp_host=Config.SMTP_HOST,
        smtp_port=Config.SMTP_PORT,
        smtp_user=Config.SMTP_USER,
        smtp_pass=Config.SMTP_PASS,
        wp_post_email=Config.WP_POST_EMAIL
    )

    poster.send_post(
        title=summary.blog_title,
        html_content=html_content,
        image_path=generated_img_path
    )

    # 5. Record to storage
    logger.info("--- Step 5: Updating Posted Papers Storage ---")
    storage.record_post(paper, summary.blog_title)
    logger.info("=== Pipeline Completed Successfully ===")
    return True

def main():
    parser = argparse.ArgumentParser(description="Academic Paper to WordPress Auto-Poster via GitHub Actions")
    parser.add_argument("--dry-run", action="store_true", help="Execute without sending email or recording post")
    parser.add_argument("--force", action="store_true", help="Force processing even if paper was already posted")
    parser.add_argument("--topic", type=str, help="Specific topic keyword filter (e.g., プログラミング教育)")
    args = parser.parse_args()

    try:
        success = run_pipeline(dry_run=args.dry_run, force=args.force, selected_topic=args.topic)
        sys.exit(0 if success else 1)
    except Exception as e:
        logger.critical(f"Fatal error in pipeline: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
