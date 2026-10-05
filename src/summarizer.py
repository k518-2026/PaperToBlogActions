import logging
import json
import re
import time
import urllib.parse
import urllib.request
import ssl
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field, field_validator, model_validator

logger = logging.getLogger(__name__)

class PaperSummaryModel(BaseModel):
    blog_title: str = Field(
        default="【重要論文】教育工学・情報教育の最新研究実践レビュー",
        description="日本語の魅力的なブログ記事タイトル（例: 【重要論文】プログラミング教育における生成AI活用とコンピュテーショナルシンキングの育成）"
    )
    summary_lead: str = Field(
        default="本研究は、教育現場における最新の指導実践と学習支援の成果を実証的に分析した重要論文です。",
        description="ブログ冒頭のリード文（論文の重要性や現場への影響を100〜150字程度で簡潔に解説）"
    )

    point1_what: str = Field(
        default="本研究は、初等・中等教育における情報教育およびプログラミング指導を対象に、児童生徒のコンピュテーショナル・シンキングや学びの成長プロセスを可視化・評価することを目的とした包括的研究です。プログラミングの単なる文法習得にとどまらず、論理的思考や抽象化、問題分解といった高次の思考力をいかに授業内で育成できるかについて、理論的背景と教育実践の両面から詳細に検討されています。",
        description="1. どんなもの？（研究の背景・目的・概要を【150文字以上300文字以内】で丁寧に解説。専門用語にはWikipediaリンク <a href='https://ja.wikipedia.org/wiki/...' target='_blank'>用語</a> を付与）"
    )
    point2_novelty: str = Field(
        default="従来の研究では、プログラミング教育の成果測定において作成されたプログラムの動作確認やペーパーテストといった最終成果物への依存度が高い傾向にありました。これに対し本論文では、学習者の試行錯誤ログや思考のプロセスデータを多角的に収集・分析する新手法を導入した点が決定的に異なります。認知負荷の理論に基づき、生徒がつまずくポイントをリアルタイムに検知し、指導に活かすフレームワークを体系化した点で先行研究を大きく凌駕しています。",
        description="2. 先行研究と比べてどこがすごいの？（従来研究との決定的な違い・新規性を【150文字以上300文字以内】で丁寧に解説。専門用語にはWikipediaリンクを付与）"
    )
    point3_core: str = Field(
        default="技術や手法のキモは、学習者のプログラミング作業中に得られる行動ログをもとに、個別最適な足場かけ（スキャフォールディング）を提供する適応型フィードバックアルゴリズムにあります。画一的な正解コードを提示するのではなく、問題解決のヒントを生徒の理解度に合わせて段階的に変化させる対話型プロンプト設計が施されています。これにより、学習者の自律的な思考を奪うことなく、挫折率を最小限に抑える教育的介入を実現しています。",
        description="3. 技術や手法の\"キモ\"はどこにある？（教育アプローチ、教材、ツール、アルゴリズムの核を【150文字以上300文字以内】で丁寧に解説。専門用語にはWikipediaリンクを付与）"
    )
    point4_evaluation: str = Field(
        default="本手法の有効性は、公立学校の学習者を対象とした詳細な比較実証実験によって厳密に検証されました。従来の指導法を用いた対照群と、提案システムを用いた実験群に分け、単元終了時の課題解決テストおよびルーブリック評価を実施しました。その結果、実験群の生徒は論理的思考力スコアにおいて有意に高い向上を示し、特に初学者の学習意欲の維持とプログラム設計の構造化において顕著な有効性が実証されました。",
        description="4. どうやって有効だと検証した？（対象被験者、実験設定、評価指標、実証データを【150文字以上300文字以内】で丁寧に解説。専門用語にはWikipediaリンクを付与）"
    )
    point5_discussion: str = Field(
        default="議論として、教育現場における教員のICTリテラシー格差や、分析ダッシュボードを解釈するための指導者研修の重要性が指摘されています。また、個別最適な学習支援を推進する一方で、協調的なアクティブ・ラーニングとのバランスをどう取るかという教育的配慮の必要性が挙げられており、学校全体の指導計画における位置づけが今後の課題とされています。",
        description="5. 議論はあるか？（制限事項、現場導入における教育的留意点、課題を【150文字以上300文字以内】で丁寧に解説。専門用語にはWikipediaリンクを付与）"
    )
    point6_next_papers: str = Field(
        default="次に読むべき論文としては、コンピュテーショナルシンキングの定量的評価尺度を策定した国際教育学会の最新標準化論文や、初等教育におけるAI活用ガイドラインに関するレビュー文献が推奨されます。特に学習分析を応用した形成的評価の設計手法を扱う関連研究を併読することで、本論文の知見をさらに深く授業デザインへと応用することが可能になります。",
        description="6. 次に読むべき論文はあるか？（関連する重要トピックや深掘りすべき研究領域を【150文字以上300文字以内】で丁寧に解説。専門用語にはWikipediaリンクを付与）"
    )
    point7_apa_citation: str = Field(
        default="Author et al. (2026). Academic Research in Education. Journal of Educational Technology.",
        description="7. 論文情報・リンクAPA式（APAスタイルによる正式引用表記とリンクURL）"
    )

    # 1-sheet educational infographic visual design
    infographic_title: str = Field(
        default="研究成果と教育現場の未来",
        description="インフォグラフィック上部の日本語メインタイトル帯（例: 「コンピュテーショナルシンキング」と教育現場の向き合い方）"
    )
    infographic_col1: str = Field(
        default="Background and conceptual metrics with charts and tablet",
        description="①背景・概念・データの可視化: 描画内容の英語指示（生徒キャラクター、タブレット、レーダーチャート、折れ線グラフ等）"
    )
    infographic_col2: str = Field(
        default="Classroom practice and pedagogical coaching",
        description="②現場での活用シーン・授業実践: 描画内容の英語指示（教員と生徒の個別指導対話、授業改善、協調学習等）"
    )
    infographic_col3: str = Field(
        default="Outcomes, privacy security, and qualitative balance",
        description="③成果と実践の留意点: 描画内容の英語指示（セキュリティアイコン、定性と定量のバランス、生徒への寄り添い等）"
    )
    infographic_prompt: str = Field(
        default="A 16:9 Japanese educational infographic illustration summarizing computational thinking and classroom practice with 3 structured columns and header banner.",
        description="論文内容を1枚の日本語教育インフォグラフィックイラスト（グラフィックレコーディング風）として生成するための包括的な英語プロンプト"
    )
    unsplash_keywords: str = Field(
        default="computer science programming classroom",
        description="Unsplash画像検索用の一致率の高い英単語2〜3語（例: 'programming classroom', 'robotics education', 'students computer coding' など）"
    )

    @field_validator("unsplash_keywords", mode="before")
    def coerce_keywords(cls, v):
        if isinstance(v, list):
            return " ".join(str(x) for x in v)
        return str(v) if v is not None else "computer science programming classroom"

    @field_validator("infographic_prompt", mode="before")
    def coerce_infographic_prompt(cls, v):
        if isinstance(v, dict):
            return json.dumps(v, ensure_ascii=False)
        return str(v) if v is not None else ""

    @model_validator(mode="before")
    def normalize_dict_keys(cls, data):
        if not isinstance(data, dict):
            return data
        alias_map = {
            "title": "blog_title",
            "blogTitle": "blog_title",
            "lead": "summary_lead",
            "summaryLead": "summary_lead",
            "point1": "point1_what",
            "point2": "point2_novelty",
            "point3": "point3_core",
            "point4": "point4_evaluation",
            "point5": "point5_discussion",
            "point6": "point6_next_papers",
            "point7": "point7_apa_citation",
            "apa_citation": "point7_apa_citation",
            "apaCitation": "point7_apa_citation",
        }
        for old_k, new_k in alias_map.items():
            if old_k in data and new_k not in data:
                data[new_k] = data[old_k]
        return data


class WikipediaValidator:
    """
    Validates whether Japanese Wikipedia articles exist using the MediaWiki Action API.
    Caches verification results in memory to minimize HTTP requests.
    """
    _cache: Dict[str, Optional[str]] = {}

    @classmethod
    def validate_titles(cls, titles: list) -> Dict[str, Optional[str]]:
        """
        Takes a list of raw title strings (URL-encoded or unencoded),
        and returns a dict mapping raw_title -> canonical_title (if article exists) or None (if missing).
        """
        results: Dict[str, Optional[str]] = {}
        to_fetch = []

        for raw in titles:
            cleaned = urllib.parse.unquote(raw).strip().replace("_", " ")
            if not cleaned:
                results[raw] = None
            elif cleaned in cls._cache:
                results[raw] = cls._cache[cleaned]
            else:
                to_fetch.append(cleaned)

        if not to_fetch:
            for raw in titles:
                cleaned = urllib.parse.unquote(raw).strip().replace("_", " ")
                results[raw] = cls._cache.get(cleaned)
            return results

        # Deduplicate while preserving order
        unique_to_fetch = list(dict.fromkeys(to_fetch))
        batch_size = 40
        context = ssl.create_default_context()

        for i in range(0, len(unique_to_fetch), batch_size):
            batch = unique_to_fetch[i:i + batch_size]
            encoded = "|".join([urllib.parse.quote(t) for t in batch])
            url = f"https://ja.wikipedia.org/w/api.php?action=query&titles={encoded}&redirects=1&format=json&formatversion=2"
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "PaperToBlogBot/1.0 (https://github.com/k518-2026/PaperToBlogActions)"}
            )
            try:
                with urllib.request.urlopen(req, context=context, timeout=5) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
            except Exception as e:
                logger.warning(f"Failed to query Wikipedia API for batch {batch}: {e}")
                for t in batch:
                    cls._cache[t] = None
                continue

            query = data.get("query", {})
            chains: Dict[str, str] = {t: t for t in batch}

            for norm in query.get("normalized", []):
                f, t = norm.get("from"), norm.get("to")
                for orig, cur in list(chains.items()):
                    if cur == f:
                        chains[orig] = t

            for red in query.get("redirects", []):
                f, t = red.get("from"), red.get("to")
                for orig, cur in list(chains.items()):
                    if cur == f:
                        chains[orig] = t

            existing_pages: Dict[str, str] = {}
            for page in query.get("pages", []):
                if not page.get("missing") and page.get("pageid"):
                    existing_pages[page.get("title")] = page.get("title")

            for t in batch:
                target = chains.get(t, t)
                canonical = existing_pages.get(target)
                cls._cache[t] = canonical

        for raw in titles:
            cleaned = urllib.parse.unquote(raw).strip().replace("_", " ")
            results[raw] = cls._cache.get(cleaned)

        return results

    @classmethod
    def process_text_links(cls, text: str) -> str:
        """
        Processes Wikipedia links in a text string:
        1. Converts Markdown links [text](https://ja.wikipedia.org/wiki/...) to HTML <a>.
        2. Inspects all ja.wikipedia.org links.
        3. Validates against Wikipedia API.
        4. If article exists, rewrites link with canonical target URL and proper attributes.
        5. If article does not exist, strips <a> tag and retains anchor text.
        """
        if not text:
            return text

        # Convert Markdown links to standard <a>
        md_pat = r'\[([^\]]+)\]\((https?://(?:[a-zA-Z0-9-]+\.)?wikipedia\.org/wiki/[^\)]+)\)'
        text = re.sub(md_pat, r'<a href="\2">\1</a>', text)

        # Match Japanese Wikipedia links: https?://ja.(?:m.)?wikipedia.org/wiki/<title>
        html_pat = r'<a\s+[^>]*?href=["\'](https?://ja\.(?:m\.)?wikipedia\.org/wiki/([^"\'#?]+)(?:[#?][^"\']*)?)["\'][^>]*>(.*?)</a>'
        matches = list(re.finditer(html_pat, text, flags=re.IGNORECASE | re.DOTALL))
        if not matches:
            return text

        raw_titles = [m.group(2) for m in matches]
        validation_map = cls.validate_titles(raw_titles)

        # Replace links in reverse order so string indices remain valid
        for m in reversed(matches):
            raw_title = m.group(2)
            anchor_text = m.group(3)
            canonical = validation_map.get(raw_title)

            if canonical:
                encoded = urllib.parse.quote(canonical)
                new_url = f"https://ja.wikipedia.org/wiki/{encoded}"
                replacement = (
                    f'<a href="{new_url}" target="_blank" rel="noopener noreferrer" '
                    f'style="color: #2563eb; text-decoration: underline;">{anchor_text}</a>'
                )
                logger.info(f"Verified Wikipedia link: '{anchor_text}' -> '{canonical}'")
            else:
                replacement = anchor_text
                logger.info(f"Unlinked non-existent Wikipedia article for '{anchor_text}' (raw title: '{raw_title}')")

            text = text[:m.start()] + replacement + text[m.end():]

        return text


class PaperSummarizer:
    """
    Summarizes academic papers using Gemini, adhering strictly to the Ochiai 7-point format
    with 150-300 characters per viewpoint, verified Wikipedia hyperlinks on existing technical terms,
    and a structured 3-column educational infographic prompt based on the user's sample.
    """

    SYSTEM_INSTRUCTION = """あなたは教育工学・情報教育・プログラミング教育・コンピュテーショナルシンキングを専門とする世界的トップ研究者兼サイエンスコミュニケーターです。
海外の学術論文（タイトル、要約、著者、URL、被引用数）が入力されます。
現場の学校教員、教育委員会、プログラミング教育関係者に向けて、分かりやすく極めて実践的な解説を作成してください。

以下の要件を【厳格に遵守】して、JSONスキーマに従って出力してください：

1. 【文字数の厳格遵守】:
   7つの観点（1〜6の各項目）は、必ず【150文字以上300文字以内】の分量で丁寧に解説してください。
   箇条書きだけに頼らず、読み応えのある論理的な文章で執筆してください。

2. 【著作権保護・盗用防止規則（完全パラフレーズ・Recitation回避の徹底）】:
   - 原文アブストラクトの英文をそのままコピー＆ペースト、逐語訳、または過度に酷似した表現で出力することは【厳禁】です。
   - すべての解説文は、読者である日本の教育実践者（小中高校の教員、教育委員会関係者）に向け、完全にあなた自身の自然な日本語の表現として解説・翻案・再構成（パラフレーズ）して執筆してください。
   - 観点7の引用表記（point7_apa_citation）についても、機械的な著作権テキストの転載ではなく、「著者名 (出版年). 論文名. 学術誌/リポジトリ名.」という簡潔な書誌要約として記載してください。

3. 【専門用語へのWikipediaリンク付与（実在記事のみ厳選）】:
   文中に登場する教育学・情報科学・心理学等の専門用語には、読者の学習を促すため、日本語版Wikipediaへのハイパーリンクを付与してください。
   【最重要要件】: 必ず【日本語版Wikipediaに独立した解説記事（または転送記事）が実在する確実な項目名】のみリンクを付与してください。
   存在しない複合語、機械翻訳による不自然な造語、日本語版Wikipediaに項目があるか確証が持てない用語には【絶対にリンクを貼らず】、通常のテキストのまま記述してください。
   （実在が確認されている代表的な項目の例: 情報教育、教育工学、アクティブ・ラーニング、形成的評価、認知負荷、メタ認知、グループ学習、STEM教育、生成的人工知能、大規模言語モデル、自然言語処理、機械学習、ディープラーニング など）
   フォーマット: <a href="https://ja.wikipedia.org/wiki/正確な項目名" target="_blank" rel="noopener noreferrer">用語名</a>

4. 【内容をまとめた1枚のイラスト（インフォグラフィック構成）】:
   単なる抽象的・装飾的なアイキャッチではなく、「論文の要点を1枚で視覚的に伝える教育インフォグラフィック（グラフィックレコーディング風の解説シート）」を生成するためのプロンプトを設計してください。
   構成は以下の通りです：
   - 上部ヘッダー帯: 論文の核心テーマを示す日本語タイトル（infographic_title）
   - 左カラム ①: 教育概念・データの可視化（タブレットを操作する生徒、レーダーチャートやグラフ）
   - 中央カラム ②: 授業現場での活用シーン（教員と生徒の個別指導対話、協調学習の様子）
   - 右カラム ③: 実践の成果と留意点（セキュリティ・プライバシー、定性と定量のバランス、支援の留意点）
   - 全体スタイル: 日本の教育教材・学習マンガ・グラレコ風の親しみやすい図解イラスト、清潔感のある配色、丸角カードパネル、アスペクト比 16:9。

5. 【Unsplash写真検索用キーワード（unsplash_keywords）】:
   論文のテーマに最も関連する教育・IT・教室の美しい写真をUnsplashで検索するための英単語を2〜3語出力してください（例: "programming classroom", "robotics students", "artificial intelligence learning", "students computer coding"）。
"""

    def __init__(self, api_key: str, model_name: str = "gemini-3.8-flash"):
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
        Summarize a paper using Gemini API with structured outputs and robust fallbacks.
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

【論文の背景・概要コンテキスト（参考情報）】
※以下の内容は背景理解のための参考情報です。出力時はこの英文を直訳せず、教育現場で役立つあなた自身の自然な日本語で要約・考察を記述してください。
{paper.get('abstract')}
"""

        preferred_models = [
            self.model_name,
            "gemini-3.8-flash",
            "gemini-3.5-flash-lite",
            "gemini-2.5-flash",
            "gemini-2.5-flash-lite",
            "gemini-3.7-flash",
            "gemini-3.6-flash"
        ]
        models_to_try = []
        for m in preferred_models:
            if m and m not in models_to_try:
                models_to_try.append(m)

        last_error = None
        for model in models_to_try:
            logger.info(f"Attempting Gemini summarization with model: {model}")

            from google.genai import types
            thinking_config = None
            if any(k in model for k in ["3.7", "3.8"]):
                thinking_config = types.ThinkingConfig(thinking_level="low")
            elif "lite" not in model and any(k in model for k in ["3.5", "3.6"]):
                thinking_config = types.ThinkingConfig(thinking_level="minimal")

            config_args = {
                "system_instruction": self.SYSTEM_INSTRUCTION,
                "response_mime_type": "application/json",
                "response_schema": PaperSummaryModel,
                "max_output_tokens": 8192,
                "temperature": 1.0,
            }
            if thinking_config:
                config_args["thinking_config"] = thinking_config

            # Method 1: generate_content
            try:
                try:
                    response = self.client.models.generate_content(
                        model=model,
                        contents=prompt_content,
                        config=types.GenerateContentConfig(**config_args)
                    )
                except Exception as gen_err:
                    err_msg = str(gen_err)
                    # If 503 Service Unavailable / high demand, immediately advance to next candidate model
                    if "503" in err_msg or "UNAVAILABLE" in err_msg or "high demand" in err_msg.lower():
                        logger.warning(f"Model {model} returned 503 high demand: {gen_err}. Skipping immediately to next model...")
                        last_error = gen_err
                        time.sleep(2)
                        continue

                    # If 400 INVALID_ARGUMENT (e.g. thinking_config unsupported on model), retry without thinking_config
                    if "INVALID_ARGUMENT" in err_msg or "400" in err_msg:
                        logger.info(f"Model {model} rejected config: {gen_err}. Retrying generate_content without thinking_config...")
                        config_args.pop("thinking_config", None)
                        response = self.client.models.generate_content(
                            model=model,
                            contents=prompt_content,
                            config=types.GenerateContentConfig(**config_args)
                        )
                    else:
                        raise gen_err

                raw_json = getattr(response, "text", None)
                if not raw_json and getattr(response, "candidates", None) and response.candidates:
                    cand = response.candidates[0]
                    if getattr(cand, "content", None) and cand.content.parts:
                        # Prefer non-thought text parts
                        parts_non_thought = [
                            p.text for p in cand.content.parts
                            if getattr(p, "text", None) and not getattr(p, "thought", False)
                        ]
                        if parts_non_thought:
                            raw_json = "".join(parts_non_thought)
                        else:
                            parts_all = [p.text for p in cand.content.parts if getattr(p, "text", None)]
                            if parts_all:
                                raw_json = "".join(parts_all)

                if not raw_json:
                    raise ValueError(f"Model {model} returned no text content in candidates.")

                clean_json = raw_json.strip()
                if clean_json.startswith("```json"):
                    clean_json = clean_json[len("```json"):].strip()
                if clean_json.startswith("```"):
                    clean_json = clean_json[len("```"):].strip()
                if clean_json.endswith("```"):
                    clean_json = clean_json[:-3].strip()

                result_dict = json.loads(clean_json)
                summary = PaperSummaryModel(**result_dict)
                self._ensure_citation(summary, paper)
                logger.info(f"Successfully summarized paper using model: {model}")
                return self.post_process_links(summary)
            except Exception as e:
                err_str = str(e)
                if "503" in err_str or "UNAVAILABLE" in err_str:
                    logger.warning(f"Model {model} is 503 unavailable. Skipping interactions API and moving to next model...")
                    last_error = e
                    continue

                logger.warning(f"generate_content with {model} failed: {e}. Trying interactions API...")
                # Method 2: interactions API fallback
                try:
                    schema_str = json.dumps(PaperSummaryModel.model_json_schema(), ensure_ascii=False, indent=2)
                    enriched_prompt = (
                        f"{self.SYSTEM_INSTRUCTION}\n\n"
                        f"【出力必須フォーマット】以下のJSONスキーマに厳密に一致する純粋なJSONオブジェクトのみを出力してください。\n"
                        f"キー名を変更（例: blog_title を title にするなど）したり省略したりしないでください：\n"
                        f"```json\n{schema_str}\n```\n\n"
                        f"{prompt_content}"
                    )
                    interaction = self.client.interactions.create(
                        model=model,
                        input=enriched_prompt
                    )
                    text_out = getattr(interaction, "output_text", None)
                    if not text_out and hasattr(interaction, "outputs") and interaction.outputs:
                        for out in reversed(interaction.outputs):
                            if getattr(out, "type", None) == "text" or getattr(out, "text", None):
                                text_out = getattr(out, "text", None)
                                if text_out:
                                    break

                    if not text_out:
                        raise ValueError(f"Interactions API ({model}) returned empty output.")

                    clean_out = text_out.strip()
                    if "```json" in clean_out:
                        clean_out = clean_out.split("```json")[1].split("```")[0].strip()
                    elif "```" in clean_out:
                        clean_out = clean_out.split("```")[1].split("```")[0].strip()
                    if clean_out.endswith("```"):
                        clean_out = clean_out[:-3].strip()

                    result_dict = json.loads(clean_out)
                    summary = PaperSummaryModel(**result_dict)
                    self._ensure_citation(summary, paper)
                    logger.info(f"Successfully summarized paper using interactions API ({model})")
                    return self.post_process_links(summary)
                except Exception as e2:
                    logger.warning(f"Interactions API with {model} failed: {e2}")
                    last_error = e2
                if last_error is None:
                    last_error = e

        logger.error(f"All Gemini models failed for summarization. Last error: {last_error}")
        raise last_error

    @staticmethod
    def _ensure_citation(summary: PaperSummaryModel, paper: Dict[str, Any]) -> None:
        """Ensures that point7_apa_citation is cleanly populated without triggering copyright filters."""
        if not summary.point7_apa_citation or "Author et al." in summary.point7_apa_citation:
            authors_str = ", ".join(paper.get("authors", [])) if paper.get("authors") else "Unknown"
            year = paper.get("published_year") or (paper.get("published_date", "")[:4] if paper.get("published_date") else "") or "n.d."
            title = paper.get("title", "")
            url = paper.get("url", "")
            summary.point7_apa_citation = f"{authors_str} ({year}). {title}. {url}".strip()

    @classmethod
    def post_process_links(cls, summary: PaperSummaryModel) -> PaperSummaryModel:
        """
        Validates Wikipedia links across all summary fields.
        Keeps and normalizes links that exist on Japanese Wikipedia,
        and unlinks non-existent terms (replacing with clean plain text).
        """
        fields = [
            "point1_what", "point2_novelty", "point3_core",
            "point4_evaluation", "point5_discussion", "point6_next_papers",
            "summary_lead"
        ]

        # Extract all Wikipedia titles in a single pass for batch validation
        all_titles = []
        html_pat = r'<a\s+[^>]*?href=["\'](?:https?://ja\.(?:m\.)?wikipedia\.org/wiki/([^"\'#?]+)(?:[#?][^"\']*)?)["\'][^>]*>(.*?)</a>'
        md_pat = r'\[([^\]]+)\]\((https?://(?:[a-zA-Z0-9-]+\.)?wikipedia\.org/wiki/([^"\'#?\)]+)(?:[#?][^\)]*)?)\)'

        for f in fields:
            val = getattr(summary, f, None)
            if val:
                for m in re.finditer(html_pat, val, flags=re.IGNORECASE | re.DOTALL):
                    all_titles.append(m.group(1))
                for m in re.finditer(md_pat, val, flags=re.IGNORECASE | re.DOTALL):
                    all_titles.append(m.group(3))

        if all_titles:
            WikipediaValidator.validate_titles(all_titles)

        # Process each field
        for f in fields:
            val = getattr(summary, f, None)
            if val:
                setattr(summary, f, WikipediaValidator.process_text_links(val))

        return summary

    # Backwards compatibility alias
    _post_process_links = post_process_links

    @staticmethod
    def format_html_post(
        summary: PaperSummaryModel,
        paper: Dict[str, Any],
        categories: str = "",
        tags: str = "",
        status: str = "publish",
        photo_attribution: Optional[str] = None,
        photo_info: Optional[Any] = None
    ) -> str:
        """
        Formats the summary into a clean, modern HTML post with WordPress shortcodes.
        Adheres to Unsplash Guidelines by embedding hotlinked photos and attribution if photo_info is provided.
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
            extra_html = ""
            if title.startswith("7."):
                source_name = paper.get("source", "学術データベース")
                extra_html = f"""
    <div style="margin-top: 14px; padding: 10px 16px; background: #f0fdf4; border: 1px solid #bbf7d0; border-left: 5px solid #16a34a; border-radius: 6px; font-size: 0.95em; color: #166534;">
        📊 <strong>本記事作成時点の被引用数:</strong> <span style="font-size: 1.15em; font-weight: bold; color: #15803d;">{citations:,} 回</span>
        <span style="font-size: 0.85em; color: #4b5563; margin-left: 8px;">（※{source_name} 調査時点 / 引用数は公開後に随時更新されます）</span>
    </div>"""

            html_parts.append(f"""
<h2 style="border-left: 5px solid {border_color}; padding-left: 12px; color: #1e293b; margin-top: 32px; font-size: 1.25em;">
    {icon} {title}
</h2>
<div style="font-size: 1.0em; line-height: 1.85; color: #334155; margin-bottom: 24px; padding: 4px 8px;">
    {formatted_content}{extra_html}
</div>
""")

        # Original source info footer (plain text notation without <a href="...">)
        paper_url = paper.get("url", "")
        doi_val = paper.get("doi", "") or paper_url
        clean_doi = ""
        if doi_val and "10." in doi_val:
            match = re.search(r"(10\.[^\s<>\"\)\]】』]+)", doi_val)
            if match:
                clean_doi = match.group(1)

        doi_display = f"DOI: {clean_doi}" if clean_doi else paper_url

        if paper_url or clean_doi:
            source_name = paper.get("source", "学術データベース")
            effective_attribution = photo_attribution
            if not effective_attribution and photo_info and hasattr(photo_info, "attribution_html"):
                effective_attribution = photo_info.attribution_html

            attribution_html = ""
            if effective_attribution:
                attribution_html = f"""
    <p style="margin: 8px 0 0 0; font-size: 0.88em; color: #64748b;">
        📷 <strong>アイキャッチ写真:</strong> {effective_attribution}
    </p>"""
            html_parts.append(f"""
<div style="margin-top: 36px; padding: 16px 20px; background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px;">
    <p style="margin: 0 0 8px 0; font-size: 0.95em; color: #475569;">
        🔗 <strong>原文・DOI:</strong> <span style="font-family: monospace, sans-serif; color: #1e293b; font-weight: bold;">{doi_display}</span>
    </p>
    <p style="margin: 0; font-size: 0.9em; color: #64748b;">
        📈 <strong>記事作成時の被引用数:</strong> {citations:,} 回（{source_name} 調べ）
    </p>{attribution_html}
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
