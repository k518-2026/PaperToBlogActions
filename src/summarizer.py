import logging
import json
import re
import urllib.parse
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

class PaperSummaryModel(BaseModel):
    blog_title: str = Field(description="日本語の魅力的なブログ記事タイトル（例: 【重要論文】プログラミング教育における生成AI活用とコンピュテーショナルシンキングの育成）")
    summary_lead: str = Field(description="ブログ冒頭のリード文（論文の重要性や現場への影響を100〜150字程度で簡潔に解説）")

    point1_what: str = Field(
        description="1. どんなもの？（研究の背景・目的・概要を【150文字以上300文字以内】で丁寧に解説。専門用語にはWikipediaリンク <a href='https://ja.wikipedia.org/wiki/...' target='_blank'>用語</a> を付与）"
    )
    point2_novelty: str = Field(
        description="2. 先行研究と比べてどこがすごいの？（従来研究との決定的な違い・新規性を【150文字以上300文字以内】で丁寧に解説。専門用語にはWikipediaリンクを付与）"
    )
    point3_core: str = Field(
        description="3. 技術や手法の\"キモ\"はどこにある？（教育アプローチ、教材、ツール、アルゴリズムの核を【150文字以上300文字以内】で丁寧に解説。専門用語にはWikipediaリンクを付与）"
    )
    point4_evaluation: str = Field(
        description="4. どうやって有効だと検証した？（対象被験者、実験設定、評価指標、実証データを【150文字以上300文字以内】で丁寧に解説。専門用語にはWikipediaリンクを付与）"
    )
    point5_discussion: str = Field(
        description="5. 議論はあるか？（制限事項、現場導入における教育的留意点、課題を【150文字以上300文字以内】で丁寧に解説。専門用語にはWikipediaリンクを付与）"
    )
    point6_next_papers: str = Field(
        description="6. 次に読むべき論文はあるか？（関連する重要トピックや深掘りすべき研究領域を【150文字以上300文字以内】で丁寧に解説。専門用語にはWikipediaリンクを付与）"
    )
    point7_apa_citation: str = Field(
        description="7. 論文情報・リンクAPA式（APAスタイルによる正式引用表記とリンクURL）"
    )

    # 1-sheet educational infographic visual design
    infographic_title: str = Field(
        description="インフォグラフィック上部の日本語メインタイトル帯（例: 「コンピュテーショナルシンキング」と教育現場の向き合い方）"
    )
    infographic_col1: str = Field(
        description="①背景・概念・データの可視化: 描画内容の英語指示（生徒キャラクター、タブレット、レーダーチャート、折れ線グラフ等）"
    )
    infographic_col2: str = Field(
        description="②現場での活用シーン・授業実践: 描画内容の英語指示（教員と生徒の個別指導対話、授業改善、協調学習等）"
    )
    infographic_col3: str = Field(
        description="③成果と実践の留意点: 描画内容の英語指示（セキュリティアイコン、定性と定量のバランス、生徒への寄り添い等）"
    )
    infographic_prompt: str = Field(
        description="論文内容を1枚の日本語教育インフォグラフィックイラスト（グラフィックレコーディング風）として生成するための包括的な英語プロンプト"
    )


class PaperSummarizer:
    """
    Summarizes academic papers using Gemini, adhering strictly to the Ochiai 7-point format
    with 150-300 characters per viewpoint, Wikipedia hyperlinks on technical terms,
    and a structured 3-column educational infographic prompt based on the user's sample.
    """

    SYSTEM_INSTRUCTION = """あなたは教育工学・情報教育・プログラミング教育・コンピュテーショナルシンキングを専門とする世界的トップ研究者兼サイエンスコミュニケーターです。
海外の学術論文（タイトル、要約、著者、URL、被引用数）が入力されます。
現場の学校教員、教育委員会、プログラミング教育関係者に向けて、分かりやすく極めて実践的な解説を作成してください。

以下の要件を【厳格に遵守】して、JSONスキーマに従って出力してください：

1. 【文字数の厳格遵守】:
   7つの観点（1〜6の各項目）は、必ず【150文字以上300文字以内】の分量で丁寧に解説してください。
   箇条書きだけに頼らず、読み応えのある論理的な文章で執筆してください。

2. 【専門用語へのWikipediaリンク付与】:
   文中に登場する教育学・情報科学・心理学等の専門用語（例: コンピュテーショナル・シンキング、プログラミング教育、情報教育、アクティブ・ラーニング、足場かけ、認知負荷理論、STEM教育、ブルームの教育目標分類法、形成的評価 など）には、読者の学習を促すため、日本語版Wikipediaへのハイパーリンクを必ず付与してください。
   フォーマット: <a href="https://ja.wikipedia.org/wiki/正確な用語名" target="_blank" rel="noopener noreferrer">用語名</a>

3. 【内容をまとめた1枚のイラスト（インフォグラフィック構成）】:
   単なる抽象的・装飾的なアイキャッチではなく、「論文の要点を1枚で視覚的に伝える教育インフォグラフィック（グラフィックレコーディング風の解説シート）」を生成するためのプロンプトを設計してください。
   構成は以下の通りです：
   - 上部ヘッダー帯: 論文の核心テーマを示す日本語タイトル（infographic_title）
   - 左カラム ①: 教育概念・データの可視化（タブレットを操作する生徒、レーダーチャートやグラフ）
   - 中央カラム ②: 授業現場での活用シーン（教員と生徒の個別指導対話、協調学習の様子）
   - 右カラム ③: 実践の成果と留意点（セキュリティ・プライバシー、定性と定量のバランス、支援の留意点）
   - 全体スタイル: 日本の教育教材・学習マンガ・グラレコ風の親しみやすい図解イラスト、清潔感のある配色、丸角カードパネル、アスペクト比 16:9。
"""

    def __init__(self, api_key: str, model_name: str = "gemini-3.6-flash"):
        self.api_key = api_key
        self.model_name = model_name
        self._client = None

    @property
    def client(self):
        if self._client is None:
            from google import genai
            self._client = genai.Client(api_key=self.api_key)
        return self._client

    def summarize(self, paper: Dict[str, Any]) -> PaperSummaryModel:
        """
        Summarize a paper using Gemini API with structured outputs.
        """
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is not set. Please provide a valid Gemini API key.")

        authors_str = ", ".join(paper.get("authors", [])) if paper.get("authors") else "Unknown"
        citations = paper.get("cited_by_count", 0)

        prompt_content = f"""【対象論文情報】
タイトル: {paper.get('title')}
著者: {authors_str}
公開日: {paper.get('published_date')}
被引用数: {citations} 回
URL: {paper.get('url')}
ソース: {paper.get('source')}

【アブストラクト（抄録）】
{paper.get('abstract')}
"""

        models_to_try = []
        for m in [self.model_name, "gemini-3.6-flash", "gemini-3.7-flash", "gemini-3.5-flash-lite"]:
            if m and m not in models_to_try:
                models_to_try.append(m)

        last_error = None
        for model in models_to_try:
            logger.info(f"Attempting Gemini summarization with model: {model}")
            try:
                response = self.client.models.generate_content(
                    model=model,
                    contents=prompt_content,
                    config={
                        "system_instruction": self.SYSTEM_INSTRUCTION,
                        "response_mime_type": "application/json",
                        "response_schema": PaperSummaryModel,
                        "temperature": 0.3
                    }
                )
                result_dict = json.loads(response.text)
                summary = PaperSummaryModel(**result_dict)
                logger.info(f"Successfully summarized paper using model: {model}")
                return self._post_process_links(summary)
            except Exception as e:
                logger.warning(f"Summarization with {model} failed: {e}")
                last_error = e

        logger.error(f"All Gemini models failed for summarization. Last error: {last_error}")
        raise last_error

    @staticmethod
    def _post_process_links(summary: PaperSummaryModel) -> PaperSummaryModel:
        """Ensure Wikipedia URLs are properly URL-encoded and valid HTML."""
        def fix_text(text: str) -> str:
            # Convert Markdown links [用語](https://ja.wikipedia.org/wiki/...) to HTML
            md_link_pat = r'\[([^\]]+)\]\((https?://ja\.wikipedia\.org/wiki/[^\)]+)\)'
            text = re.sub(
                md_link_pat,
                r'<a href="\2" target="_blank" rel="noopener noreferrer" style="color: #2563eb; text-decoration: underline;">\1</a>',
                text
            )
            # Ensure existing <a> tags have proper attributes
            def replace_a(match):
                url = match.group(1)
                anchor_text = match.group(2)
                return f'<a href="{url}" target="_blank" rel="noopener noreferrer" style="color: #2563eb; text-decoration: underline;">{anchor_text}</a>'

            html_link_pat = r'<a\s+href=["\']([^"\']+)["\'][^>]*>(.*?)</a>'
            text = re.sub(html_link_pat, replace_a, text)
            return text

        summary.point1_what = fix_text(summary.point1_what)
        summary.point2_novelty = fix_text(summary.point2_novelty)
        summary.point3_core = fix_text(summary.point3_core)
        summary.point4_evaluation = fix_text(summary.point4_evaluation)
        summary.point5_discussion = fix_text(summary.point5_discussion)
        summary.point6_next_papers = fix_text(summary.point6_next_papers)
        return summary

    @staticmethod
    def format_html_post(
        summary: PaperSummaryModel,
        paper: Dict[str, Any],
        categories: str = "",
        tags: str = "",
        status: str = "publish"
    ) -> str:
        """
        Formats the summary into a clean, modern HTML post with WordPress shortcodes.
        """
        html_parts = []
        citations = paper.get("cited_by_count", 0)

        # Lead introduction card with citations badge
        html_parts.append(f"""<div style="background: #f0f7ff; border-left: 5px solid #0066cc; padding: 18px 22px; border-radius: 6px; margin-bottom: 26px;">
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
        <span style="font-size: 0.9em; font-weight: bold; color: #1e40af;">🎓 学術論文・重要研究レビュー</span>
        <span style="background: #2563eb; color: #ffffff; padding: 3px 10px; border-radius: 12px; font-size: 0.85em; font-weight: bold;">被引用数: {citations} 回</span>
    </div>
    <p style="margin: 0; font-size: 1.05em; line-height: 1.8; color: #1e3a8a;">{summary.summary_lead}</p>
</div>""")

        sections = [
            ("1. どんなもの？", summary.point1_what, "#2563eb", "💡"),
            ("2. 先行研究と比べてどこがすごいの？", summary.point2_novelty, "#0d9488", "✨"),
            ("3. 技術や手法の\"キモ\"はどこにある？", summary.point3_core, "#7c3aed", "🔑"),
            ("4. どうやって有効だと検証した？", summary.point4_evaluation, "#d97706", "📊"),
            ("5. 議論はあるか？", summary.point5_discussion, "#e11d48", "💬"),
            ("6. 次に読むべき論文はあるか？", summary.point6_next_papers, "#4f46e5", "📖"),
            ("7. 論文情報・リンク（APA式）", summary.point7_apa_citation, "#475569", "📑"),
        ]

        for title, content, border_color, icon in sections:
            formatted_content = content.replace("\n", "<br>")
            html_parts.append(f"""
<h2 style="border-left: 5px solid {border_color}; padding-left: 12px; color: #1e293b; margin-top: 32px; font-size: 1.25em;">
    {icon} {title}
</h2>
<div style="font-size: 1.0em; line-height: 1.85; color: #334155; margin-bottom: 24px; padding: 4px 8px;">
    {formatted_content}
</div>
""")

        # Original source link footer
        paper_url = paper.get("url", "")
        if paper_url:
            html_parts.append(f"""
<div style="margin-top: 36px; padding: 14px 18px; background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px;">
    <p style="margin: 0; font-size: 0.95em; color: #475569;">
        🔗 <strong>原文・DOIリンク:</strong> <a href="{paper_url}" target="_blank" rel="noopener noreferrer" style="color: #2563eb; word-break: break-all;">{paper_url}</a>
    </p>
</div>
""")

        # WordPress Post by Email shortcodes
        html_parts.append("\n<!-- WordPress Post by Email Shortcodes -->\n")
        if categories:
            html_parts.append(f"[category {categories}]\n")
        if tags:
            html_parts.append(f"[tags {tags}]\n")
        html_parts.append(f"[status {status}]\n")

        return "\n".join(html_parts)
