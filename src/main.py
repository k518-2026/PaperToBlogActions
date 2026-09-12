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
    logger.info(f"Mode: {'DRY RUN (Simulation)' if dry_run else 'PRODUCTION (Live Posting)'}")

    storage = StorageManager(Config.STORAGE_PATH)

    # Filter topics if requested
    topics = Config.SEARCH_TOPICS
    if selected_topic:
        topics = [t for t in topics if selected_topic in t["name"]]
        if not topics:
            logger.error(f"Topic '{selected_topic}' not found in configuration.")
            return False

    # 1. Fetch unposted paper (Prioritizing high citation counts)
    logger.info("--- Step 1: Fetching Paper (Prioritizing High Citations) ---")
    paper = PaperFetcher.get_latest_unposted_paper(storage, topics, force=force)
    if not paper:
        logger.info("No new papers found to post today. Terminating gracefully.")
        return True

    citations = paper.get("cited_by_count", 0)
    logger.info(f"Selected Paper: {paper.get('title')}")
    logger.info(f"Citations: {citations} | Source: {paper.get('source')} | Published: {paper.get('published_date')}")

    # 2. Summarize with Gemini (Strict 150-300 chars & Wikipedia links)
    logger.info("--- Step 2: Summarizing Paper (Ochiai 7-Point Format with Wikipedia Links) ---")
    summary = None
    if Config.GEMINI_API_KEY:
        try:
            summarizer = PaperSummarizer(api_key=Config.GEMINI_API_KEY, model_name=Config.GEMINI_TEXT_MODEL)
            summary = summarizer.summarize(paper)
        except Exception as e:
            if dry_run:
                logger.warning(f"Gemini API summarization encountered an error: {e}. Using simulation summary for dry-run.")
            else:
                raise

    if summary is None:
        if dry_run:
            logger.warning("Using simulation 150-300 char summary with Wikipedia links for dry-run mode.")
            summary = PaperSummaryModel(
                blog_title=f"【必読論文】{paper.get('title')}",
                summary_lead=f"本研究は、海外の教育現場において{citations}回以上引用されている極めて影響力の高い実践研究です。コンピュテーショナルシンキングの育成とプログラミング指導における新たな知見を包括的に提示しています。",
                point1_what="本研究は、初等・中等教育における<a href=\"https://ja.wikipedia.org/wiki/%E6%83%85%E5%A0%B1%E6%95%99%E8%82%B2\" target=\"_blank\">情報教育</a>および<a href=\"https://ja.wikipedia.org/wiki/%E3%83%97%E3%83%AD%E3%82%B0%E3%83%A9%E3%83%9F%E3%83%B3%E3%82%B0%E6%95%99%E8%82%B2\" target=\"_blank\">プログラミング教育</a>を対象に、児童生徒の<a href=\"https://ja.wikipedia.org/wiki/%E3%82%B3%E3%83%B3%E3%83%94%E3%83%A5%E3%83%86%E3%83%BC%E3%82%B7%E3%83%A7%E3%83%8A%E3%83%AB%E3%83%BB%E3%82%B7%E3%83%B3%E3%82%AD%E3%83%B3%E3%82%B0\" target=\"_blank\">コンピュテーショナル・シンキング</a>の成長プロセスを可視化・評価することを目的とした包括的研究です。プログラミングの単なる文法習得にとどまらず、論理的思考や抽象化、問題分解といった高次の思考力をいかに授業内で育成できるかについて、理論的背景と教育実践の両面から詳細に検討されています。",
                point2_novelty="従来の研究では、プログラミング教育の成果測定において作成されたプログラムの動作確認やペーパーテストといった最終成果物への依存度が高い傾向にありました。これに対し本論文では、学習者の試行錯誤ログや思考のプロセスデータを多角的に収集・分析する新手法を導入した点が決定的に異なります。<a href=\"https://ja.wikipedia.org/wiki/%E8%AA%8D%E7%9F%A5%E8%B2%A0%E8%8D%B7%E7%90%86%E8%AB%96\" target=\"_blank\">認知負荷理論</a>に基づき、生徒がつまずくポイントをリアルタイムに検知し、指導に活かすフレームワークを世界で初めて体系化した点で先行研究を大きく凌駕しています。",
                point3_core="技術や手法のキモは、学習者のプログラミング作業中に得られる行動ログをもとに、個別最適な<a href=\"https://ja.wikipedia.org/wiki/%E8%B6%B3%E5%A0%B4%E3%81%8B%E3%81%91\" target=\"_blank\">足場かけ</a>（スキャフォールディング）を提供する適応型フィードバックアルゴリズムにあります。画一的な正解コードを提示するのではなく、問題解決のヒントを生徒の理解度に合わせて段階的に変化させる対話型プロンプト設計が施されています。これにより、学習者の自律的な思考を奪うことなく、挫折率を最小限に抑える教育的介入を実現しています。",
                point4_evaluation="本手法の有効性は、公立中学校3校の生徒240名を対象とした半年間にわたる比較実証実験によって厳密に検証されました。従来の指導法を用いた対照群と、提案システムを用いた実験群に分け、単元終了時の課題解決テストおよびルーブリック評価を実施しました。その結果、実験群の生徒は論理的思考力スコアにおいて有意に高い向上（効果サイズd=0.74）を示し、特に初学者の学習意欲の維持とプログラム設計の構造化において顕著な有効性が実証されました。",
                point5_discussion="議論として、教育現場における教員のICTリテラシー格差や、分析ダッシュボードを解釈するための指導者研修の重要性が指摘されています。また、個別最適な学習支援を推進する一方で、協調的な<a href=\"https://ja.wikipedia.org/wiki/%E3%82%A2%E3%82%AF%E3%83%86%E3%82%A3%E3%83%96%E3%83%BB%E3%83%A9%E3%83%BC%E3%83%8ByteArray%E3%82%B0\" target=\"_blank\">アクティブ・ラーニング</a>とのバランスをどう取るかという教育的配慮の必要性が挙げられており、学校全体の指導計画における位置づけが今後の課題とされています。",
                point6_next_papers="次に読むべき論文としては、コンピュテーショナルシンキングの定量的評価尺度を策定した国際教育学会（ACM SIGCSE）の最新標準化論文や、初等教育における生成AI活用ガイドラインに関する欧米の政策レビュー文献が推奨されます。特に学習分析（Learning Analytics）を応用した形成的評価の設計手法を扱う関連研究を併読することで、本論文の知見をさらに深く授業デザインへと応用することが可能になります。",
                point7_apa_citation=f"Author et al. (2026). {paper.get('title')}. Retrieved from {paper.get('url')}",
                infographic_title=f"「{paper.get('title')[:18]}」と授業実践の未来",
                infographic_col1="Background and concept: Computational thinking visualization, student in school uniform using digital tablet, radar chart, achievement rate badge",
                infographic_col2="Classroom practice: Teacher giving individual guidance to student, pair programming, interactive lesson improvement",
                infographic_col3="Outcomes and guidelines: Data balance scale, qualitative vs quantitative insights, student privacy and warm educational support",
                infographic_prompt="A 16:9 Japanese educational infographic illustration summarizing computational thinking and programming education with 3 structured columns and a top headline ribbon."
            )
        else:
            raise ValueError("GEMINI_API_KEY environment variable is required for production.")

    logger.info(f"Generated Blog Title: {summary.blog_title}")

    # 3. Generate 1-Sheet Educational Infographic Illustration
    logger.info("--- Step 3: Generating 1-Sheet Educational Infographic Illustration ---")
    temp_dir = Config.BASE_DIR / "temp"
    temp_dir.mkdir(exist_ok=True)
    image_path = temp_dir / "eyecatch.png"

    image_generator = GeminiImageGenerator(api_key=Config.GEMINI_API_KEY, model_name=Config.GEMINI_IMAGE_MODEL)
    generated_img_path = image_generator.generate_infographic(
        summary_data=summary.model_dump(),
        output_path=image_path
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
        logger.info(f"[DRY RUN] Infographic image saved to: {generated_img_path}")
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

    # 5. Record to storage & sync POSTED_PAPERS.md
    logger.info("--- Step 5: Updating Posted Papers Storage & POSTED_PAPERS.md ---")
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
