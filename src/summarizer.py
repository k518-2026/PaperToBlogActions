import logging
import json
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

class PaperSummaryModel(BaseModel):
    blog_title: str = Field(description="日本語の魅力的なブログ記事タイトル（例: 【最新研究】◯◯）")
    summary_lead: str = Field(description="ブログ冒頭のリード文（論文の重要性を2〜3文で解説）")
    point1_what: str = Field(description="1. どんなもの？（研究の概要、目的、背景）")
    point2_novelty: str = Field(description="2. 先行研究と比べてどこがすごいの？（従来研究との決定的な違い、新規性）")
    point3_core: str = Field(description="3. 技術や手法の\"キモ\"はどこにある？（教育アプローチ、教材、ツール、アルゴリズムの核）")
    point4_evaluation: str = Field(description="4. どうやって有効だと検証した？（対象被験者、実験設定、評価指標、実証データ）")
    point5_discussion: str = Field(description="5. 議論はあるか？（制限事項、現場導入における教育的留意点、課題）")
    point6_next_papers: str = Field(description="6. 次に読むべき論文はあるか？（関連する重要トピックや深掘りすべき研究領域）")
    point7_apa_citation: str = Field(description="7. 論文情報・リンクAPA式（APAスタイルによる正式引用表記とリンクURL）")
    image_prompt: str = Field(description="論文内容を象徴するイラスト・インフォグラフィック生成用の詳細な英語プロンプト（3D isometric illustration / educational tech art style, no gibberish text）")


class PaperSummarizer:
    """
    Summarizes and translates academic papers into Japanese using the Gemini model,
    adhering strictly to the 7-item Ochiai format and generating an image prompt.
    """

    SYSTEM_INSTRUCTION = """あなたは教育工学・情報教育・プログラミング教育・コンピュテーショナルシンキングを専門とするトップ研究者兼サイエンスコミュニケーターです。
英語の学術論文（タイトル、要約、著者、URL）が入力されます。
現場の教員、教育関係者、プログラミング教育に携わる読者に向けて、深くかつ分かりやすく解説してください。

必ず以下の7つの観点（落合式フォーマット）に厳密に沿って、JSONスキーマに従って回答してください：
1. どんなもの？
2. 先行研究と比べてどこがすごいの？
3. 技術や手法の"キモ"はどこにある？
4. どうやって有効だと検証した？
5. 議論はあるか？
6. 次に読むべき論文はあるか？
7. 論文情報・リンクAPA式

各項目は単なる一言ではなく、具体的かつ実践的な内容を200〜400字程度で詳細に解説してください。
同時に、この論文の教育的コアコンセプトを視覚的に表現したイラストを作成するための、英語の画像生成プロンプト（image_prompt）も作成してください。文字の描画は乱れやすいため、イラストスタイル（isometric 3D, vector flat art, modern educational technology visualization, vibrant colors）でテキストを含めないよう指定してください。
"""

    def __init__(self, api_key: str, model_name: str = "gemini-3.7-flash"):
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
        prompt_content = f"""【対象論文情報】
タイトル: {paper.get('title')}
著者: {authors_str}
公開日: {paper.get('published_date')}
URL: {paper.get('url')}
ソース: {paper.get('source')}

【アブストラクト（抄録）】
{paper.get('abstract')}
"""

        logger.info(f"Calling Gemini ({self.model_name}) to summarize paper: {paper.get('title')}")

        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=[
                    {"role": "user", "parts": [{"text": prompt_content}]}
                ],
                config={
                    "system_instruction": self.SYSTEM_INSTRUCTION,
                    "response_mime_type": "application/json",
                    "response_schema": PaperSummaryModel,
                    "temperature": 0.3
                }
            )

            result_dict = json.loads(response.text)
            return PaperSummaryModel(**result_dict)
        except Exception as e:
            logger.error(f"Error calling Gemini for summarization: {e}")
            raise

    @staticmethod
    def format_html_post(summary: PaperSummaryModel, paper: Dict[str, Any], categories: str = "", tags: str = "", status: str = "publish") -> str:
        """
        Formats the summary into a clean, modern HTML post with WordPress shortcodes.
        """
        html_parts = []

        # Lead introduction
        html_parts.append(f"""<div style="background: #f0f7ff; border-left: 5px solid #0066cc; padding: 16px 20px; border-radius: 4px; margin-bottom: 24px;">
    <p style="margin: 0; font-size: 1.05em; line-height: 1.7; color: #1e3a8a;"><strong>【研究の要点】</strong><br>{summary.summary_lead}</p>
</div>""")

        sections = [
            ("1. どんなもの？", summary.point1_what, "#2563eb"),
            ("2. 先行研究と比べてどこがすごいの？", summary.point2_novelty, "#0d9488"),
            ("3. 技術や手法の\"キモ\"はどこにある？", summary.point3_core, "#7c3aed"),
            ("4. どうやって有効だと検証した？", summary.point4_evaluation, "#d97706"),
            ("5. 議論はあるか？", summary.point5_discussion, "#e11d48"),
            ("6. 次に読むべき論文はあるか？", summary.point6_next_papers, "#4f46e5"),
            ("7. 論文情報・リンク（APA式）", summary.point7_apa_citation, "#475569"),
        ]

        for title, content, border_color in sections:
            formatted_content = content.replace("\n", "<br>")
            html_parts.append(f"""
<h2 style="border-bottom: 2px solid {border_color}; padding-bottom: 6px; color: #1e293b; margin-top: 28px;">{title}</h2>
<p style="font-size: 1.0em; line-height: 1.8; color: #334155; margin-bottom: 20px;">{formatted_content}</p>
""")

        # Original source link footer
        paper_url = paper.get("url", "")
        if paper_url:
            html_parts.append(f"""
<div style="margin-top: 32px; padding: 12px 16px; background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px;">
    <p style="margin: 0; font-size: 0.9em; color: #64748b;">
        🔗 <strong>原文リンク:</strong> <a href="{paper_url}" target="_blank" rel="noopener noreferrer" style="color: #2563eb; word-break: break-all;">{paper_url}</a>
    </p>
</div>
""")

        # WordPress Post by Email shortcodes
        html_parts.append("\n<!-- WordPress Shortcodes -->\n")
        if categories:
            html_parts.append(f"[category {categories}]\n")
        if tags:
            html_parts.append(f"[tags {tags}]\n")
        html_parts.append(f"[status {status}]\n")

        return "\n".join(html_parts)
