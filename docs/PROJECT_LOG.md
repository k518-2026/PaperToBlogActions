# PaperToBlogActions プロジェクト全記録・運用ガイド

本ドキュメントは、学術論文自動要約・インフォグラフィック生成・WordPress自動投稿システム（`PaperToBlogActions`）の開発経緯、トラブルシューティング、および運用手順を網羅した記録です。

---

## 1. プロジェクト基本情報

- **リポジトリ**: [k518-2026/PaperToBlogActions](https://github.com/k518-2026/PaperToBlogActions.git)
- **稼働環境**: GitHub Actions（完全サーバーレス自動運用）
- **定期実行**: 毎日 **日本時間 朝4:20（UTC 19:20）**
- **対象分野**: 初等・中等教育、情報教育、プログラミング教育、コンピュテーショナル・シンキング

---

## 2. 実装した主要機能と課題解決

### (1) 被引用数優先の論文取得 & 二重投稿防止
- **機能**: OpenAlex APIより引用数降順で候補論文を取得し、教育界で注目されている重要論文を優先選定。
- **履歴管理**: 投稿済みの論文ID/URLを `data/posted_papers.json` およびマークダウン表 `data/POSTED_PAPERS.md` に自動蓄積。ワークフロー実行後にGitHubへ自動コミット＆プッシュ。

### (2) 落合式7観点要約（各観点150〜300文字）
- **構成**:
  1. 💡 どんなもの？
  2. ✨ 先行研究と比べてどこがすごいの？
  3. 🔑 技術や手法の"キモ"はどこにある？
  4. 📊 どうやって有効だと検証した？
  5. 💬 議論はあるか？
  6. 📖 次に読むべき論文はあるか？
  7. 📑 論文情報・リンク（APA式引用）
- **文字数厳格化**: 各観点150〜300字をプロンプトおよびPydanticスキーマで厳格に担保。

### (3) Wikipediaリンク実在検証（リンク切れ404完全防止）
- **背景**: Geminiが付与する専門用語リンク（例: `コンピュテーショナル・シンキング`、`プログラミング教育` など）について、日本語版Wikipediaに単独記事が存在せず「項目がありません」（404）となる事象が発生。
- **解決策**:
  - `WikipediaValidator` クラスを実装し、MediaWiki API（`https://ja.wikipedia.org/w/api.php?action=query&titles=...&redirects=1`）と連携。
  - **実在記事**: 正規化URL（別タブ表示 `target="_blank"` 付き）でリンクを維持。転送ページ（例: `Scratch` → `スクラッチ`）も自動追跡。
  - **非実在記事**: `<a>` タグを自動除去し、本文用語のみをプレーンテキストとして自然に残す。

### (4) 1枚の教育インフォグラフィック生成 & クォータ対応
- **デザイン構成**:
  - ヘッダー帯: 論文の核心テーマ
  - 左カラム ①: 概念・データの可視化（生徒キャラクター、タブレット、チャート等）
  - 中央カラム ②: 授業現場での活用シーン（個別指導対話、協調学習）
  - 右カラム ③: 成果と留意点（セキュリティ、定性・定量バランス）
- **画像生成エラー対策（フォールバック網）**:
  - Google AI Studio無料枠では画像モデルのクォータ上限が0（`429 RESOURCE_EXHAUSTED`）となるため、以下の多重フォールバックを実装：
    1. Gemini画像生成API（課金有効キー設定時に自動稼働）
    2. 無料AI画像生成（Pollinations FLUX）
    3. NotoSansCJKフォントを用いた Pillow 高品質グラフィックカード（文字化け「□□」対策済み）

### (5) 投稿スケジュール設定
- 当初設定していた19:00はAPIアクセスやGitHub Actionsランナーの混雑ピークと重なるため、負荷が低く安定している **日本時間 毎朝4:20（UTC 19:20）** に自動実行されるよう `.github/workflows/paper_to_blog.yml` の cron を `20 19 * * *` に変更。00分ピッタリを避けて20分に設定することでGitHub側のキュー詰まりも防止。

### (6) 引用（APA式）直後への作成時被引用数明記
- 「7. 論文情報・リンク（APA式）」の直後および末尾のDOIカード内に、記事作成時点の被引用数（例: `📊 本記事作成時点の被引用数: 471 回（※OpenAlex 調査時点 / 引用数は公開後に随時更新されます）`）を視覚的バッジとして自動掲載。
- 引用数は日々変動するため、記事執筆・公開時点での学術的影響力を読者に明確に伝える設計に改善。

### (7) Unsplash API連携（高解像度写真アイキャッチ & Production審査規準遵守）
- **背景**: アイキャッチ画像として、AIイラストに加えてUnsplashの高品質・高解像度写真を利用できるように機能拡張。
- **Unsplash利用規約・本番審査（Apply for Production）完全準拠設計**:
  1. **Hotlink photos**: HTML本文内にUnsplash CDN（`images.unsplash.com`）の直リンク画像を埋め込み（自前サーバー/GitHubへの画像再ホスティングによる配信を防止）。
  2. **Trigger downloads**: 画像利用時にUnsplash公式のダウンロード追跡エンドポイント（`photo.links.download_location?client_id=...`）へGETリクエストを自動発火。
  3. **No Unsplash Logo/Distinct Name**: アプリケーション名称は `PaperToBlogActions` とし、Unsplashロゴを流用しない独自UI。
  4. **Attribution & UTM Parameters**: 写真直下のキャプションおよび記事末尾カードに、撮影者氏名とUnsplashへのリンクを規定のUTMパラメータ付きで記載：
     `Photo by <a href="{photographer_url}?utm_source=PaperToBlogActions&utm_medium=referral">Name</a> on <a href="https://unsplash.com/?utm_source=PaperToBlogActions&utm_medium=referral">Unsplash</a>`
- **ユーザー指定**: 文字入れ等の加工を行わず、純粋な高解像度写真をそのままアイキャッチとして使用。
- **階層型フォールバック**:
  - Priority 0: Unsplash API（`UNSPLASH_ACCESS_KEY` 設定時）
  - Priority 1: Gemini Image API（課金有効キー時）
  - Priority 2: Pollinations FLUX（無料AI画像）
  - Priority 3: Pillow 3カラムグラフィックカード
- **画像配置の最適化**: WordPress「メールで投稿」が末尾に添付画像を自動挿入する仕様に合わせ、記事本文上部の重複画像を除去。記事末尾の出典カード直下に1枚だけ綺麗に表示されるようレイアウトを最適化。

### (8) Gemini 3.8 Flash移行 & 思考モデル（Thinking Model）JSON出力障害対策 (2026-10-03)
- **障害事象**:
  - 定期実行時に `gemini-3.6-flash` が Google バックエンドの需要急増により `503 Service Unavailable` を返却。
  - 次モデル `gemini-3.7-flash` へのフォールバック時に `TypeError: the JSON object must be str, bytes or bytearray, not NoneType` が発生しパイプライン全体が停止。
  - Interactions API フォールバック時にもスキーマ定義不足により Pydantic の `PaperSummaryModel` バリデーションエラー（必須フィールド欠落等）が発生。
- **原因分析**:
  - `gemini-3.7-flash` はデフォルトで拡張思考（Extended Thinking / `part.thought=True`）が有効化されており、SDKの `response.text` プロパティが思考パートを除外した結果 `None` となり、`json.loads(response.text)` がクラッシュ。
  - Interactions API では構造化スキーマがプロンプトへ渡されておらず、モデルがフィールド名を改変（例: `blog_title` → `title`）したり、文字列フィールドに辞書/リストを返却。
- **恒久対策・改善内容**:
  1. **標準モデルの刷新**: 安定稼働かつ高速な最新フラグシップ `gemini-3.8-flash` を標準採用（`src/config.py`, `src/summarizer.py`, `.github/workflows/paper_to_blog.yml`）。
  2. **思考トークンの制御**: `types.GenerateContentConfig` に `thinking_config=types.ThinkingConfig(thinking_budget=0)` および `max_output_tokens=8192` を明示設定。JSON生成時の思考モード干渉を完全抑止。
  3. **安全なコンテンツ抽出**: `response.text` が None の場合でも `candidates[0].content.parts` から通常テキストを抽出し、Markdownフェンス（` ```json `）を安全に除去するロジックを追加。
  4. **Interactions APIのスキーマ注入**: フォールバックプロンプトに `PaperSummaryModel.model_json_schema()` を埋め込み、モデルに厳密なキーと型を出力させるよう強化。
  5. **Pydanticモデルの耐障害性強化**: `PaperSummaryModel` にフィールドバリデータ・モデルバリデータを追加し、キーの揺らぎ（`title` → `blog_title` 等）や型の自動変換（リスト/辞書の文字列化、デフォルト値補完）を実装。

### (9) Recitation（著作権/盗用検知）フィルター回避 ＆ 503即時スキップ ＆ 堅牢フォールバック網 (2026-10-03)
- **障害事象**:
  - 全モデルが 503 高負荷スパイクまたは Recitation フィルター検知（`400 Bad Request: Request blocked due to copyright/recitation content`）で失敗。
  - `gemini-3.5-flash-lite` では `thinking_budget=0` が `400 INVALID_ARGUMENT` となり、フォールバックの Interactions API では低温度（0.3）とアブストラクトの直接参照により著作権・Recitation フィルターが作動。
  - 503 発生時に同一モデルの Interactions API を再試行してしまい、タイムアウトを重ねる事象が発生。
- **原因分析**:
  - Google Gemini API の著作権検知（Recitation Filter）は、入力されたアブストラクトの英文をモデルが逐語訳したり似た文構造を出力した場合、また温度（temperature）を極端に低く（0.3など）設定して決定論的出力にした場合に強く発火する。
  - `thinking_budget` は Gemini 3.5 Flash-Lite など一部モデルでサポート外（未対応引数 400 エラー）。
- **恒久対策・改善内容**:
  1. **完全パラフレーズ・Recitation 回避指示の明記**: `SYSTEM_INSTRUCTION` およびプロンプトに「原文アブストラクトの直訳・丸写し厳禁、日本の教育関係者向けに独自の平易な言葉で完全翻案・再構成すること」を強く指示。
  2. **公式推奨温度への是正**: 公式トラブルシューティングに従い、過度に低い温度を廃止して標準温度（`temperature=1.0`）に設定し、Recitation 誤検知を防止。
  3. **モデル別思考設定 ＆ 400 自動再試行**: 思考設定（`thinking_level="low"`）を対応モデル（3.7 / 3.8）のみに限定。400 INVALID_ARGUMENT 発生時は即座に思考設定を除去して自動再試行する二重防御を実装。
  4. **503 高負荷時の即時次モデルスキップ**: 503 発生時は同一モデルの Interactions API で時間を浪費せず、即座に次の候補モデルへスイッチ。
  5. **高可用性モデル（`gemini-2.5-flash` / `gemini-2.5-flash-lite`）をフォールバック網に追加**: 3.x 世代のサーバー需要逼迫時にも即座に切り替わる大容量インフラの 2.5 世代をフォールバック網に組み込み、パイプラインの停止を完全防止。
  6. **引用表記（APA）の Python 自動生成フォールバック**: 著作権検知の原因となりやすい書誌引用の出力において、モデル側が空やプレースホルダーを出力した場合に Python 側で安全に自動構成する処理を追加。

### (10) WordPress向けメール投稿の `<a href>` リンク除去 ＆ プレーンDOI表記安全対策 (2026-10-05)
- **背景と目的**:
  - WordPressの「メールで投稿（Post by Email）」機能において、メール本文内に外部ハイパーリンク（`<a href="...">`）が多数含まれていると、送信元SMTPサーバーや受信側メールサーバー（Gmail/Outlook/Yahoo/WordPress）の迷惑メール（スパム）判定やフィッシング詐欺防止フィルターを誤認誘発するリスクが存在。
  - 送信メールから `<a href="...">` リンクを除去し、引用文献やDOIを安全なプレーンテキスト表記（例: `DOI: 10.xxxx/...`）に統一する安全対策を実装。
- **実装内容**:
  1. **HTMLメールサニタイザーの実装 (`WordPressMailPoster.sanitize_html_for_email`)**:
     - 全ての `<a href="...">` タグを自動除去し、アンカーテキスト（用語や撮影者名）のみをプレーンテキストとして安全に維持。
     - `<a href="https://doi.org/10.xxxx">...</a>` や本文中の `https://doi.org/10.xxxx` を正規のプレーンテキスト形式 `DOI: 10.xxxx/...` へ自動変換。
  2. **末尾DOIカードのプレーン表記化 (`PaperSummarizer.format_html_post`)**:
     - 原文DOIブロックをハイパーリンクタグではなく、視認性の高い monospace 等幅フォントのプレーン表記（`🔗 原文・DOI: DOI: 10.xxxx/...`）に改修。
  3. **自動適用**:
     - メール送信直前（`send_post`）およびローカルプレビュー作成（`preview_post.html`）の両方にサニタイズ処理を適用。

---

## 3. 運用・保守手順

### APIキー・パスワードの更新
GitHubリポジトリの **[Settings > Secrets and variables > Actions](https://github.com/k518-2026/PaperToBlogActions/settings/secrets/actions)** からいつでも変更可能です：
- `UNSPLASH_ACCESS_KEY`: Unsplash API Access Key（写真取得用）
- `GEMINI_API_KEY`: Google Gemini APIキー
- `WP_POST_EMAIL`: WordPress投稿受信用メールアドレス
- `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`: 送信用SMTP設定

### 手動テスト（Dry-run）の実行方法
1. GitHubの **「Actions」** タブを開く。
2. **「Auto Post Research Papers to WordPress」** ワークフローを選択。
3. **「Run workflow」** プルダウンを開き、`dry_run: true` を選んで実行。
   - メール送信を行わずに、要約本文やインフォグラフィック生成、Wikipediaリンク検証の結果を確認できます。


