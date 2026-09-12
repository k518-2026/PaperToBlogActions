# 情報教育・プログラミング教育・コンピュテーショナルシンキング海外論文 自動収集＆WordPressブログ自動投稿システム (GitHub Actions)

arXivやOpenAlexなどの学術論文APIから「情報教育」「プログラミング教育」「コンピュテーショナルシンキング」に関する最新のオープンアクセス論文を自動取得し、Google Gemini（テキストモデル）で**7観点（落合式フォーマット）**に要約・日本語翻訳。さらにGeminiの画像生成機能で内容を象徴するアイキャッチイラストを自動生成し、WordPressへメール経由で自動投稿する**GitHub Actions完全自動化パイプライン**です。

---

## 🌟 特徴

- **完全サーバーレス＆無料運用**: GitHub Actions（パブリックリポジトリなら実行時間無制限、プライベートでも月2,000分無料枠）で完全自動稼働。
- **学術APIハイブリッド自動収集**:
  - **arXiv API**: `cs.CY` (社会と計算機), `cs.HC` (ヒューマン・コンピュータ・インタラクション) などの最新プレプリントを取得。
  - **OpenAlex API**: 世界中の査読付きオープンアクセス教育論文を取得。
  - 重複判定機構（`data/posted_papers.json`）により、同じ論文が二重投稿されることはありません。
- **厳格な落合式7観点要約**:
  1. **どんなもの？**
  2. **先行研究と比べてどこがすごいの？**
  3. **技術や手法の"キモ"はどこにある？**
  4. **どうやって有効だと検証した？**
  5. **議論はあるか？**
  6. **次に読むべき論文はあるか？**
  7. **論文情報・リンクAPA式**
- **AIアイキャッチイラスト自動生成**: Geminiの画像生成機能（`gemini-3.1-flash-image` / `imagen-3.0-generate-002`）を用いて、論文のコアコンセプトを象徴する高品質なイラストを自動生成・添付。
- **WordPressメール投稿（Post by Email）連携**: 添付された画像は自動的にアイキャッチ・メディアライブラリに保存され、カテゴリ・タグ・即時公開（`[status publish]`）ショートコードとともに自動投稿。

---

## 📂 フォルダ構成

```
PaperToBlogActions/
├── .github/
│   └── workflows/
│       └── paper_to_blog.yml          # GitHub Actions 定期実行ワークフロー（cron）
├── src/
│   ├── __init__.py
│   ├── config.py                     # 環境変数・キーワード設定
│   ├── fetcher.py                    # arXiv & OpenAlex 論文取得モジュール
│   ├── summarizer.py                 # Gemini 7観点要約＆画像プロンプト生成
│   ├── image_generator.py            # Gemini 画像生成エンジン（フォールバック付き）
│   ├── mail_poster.py                # WordPressメール投稿（SMTP + 画像添付）
│   ├── storage.py                    # 投稿履歴・重複判定管理
│   └── main.py                       # パイプライン実行エントリーポイント（CLI）
├── data/
│   └── posted_papers.json            # 投稿済み論文ID履歴（Git自動更新）
├── tests/
│   ├── test_fetcher.py               # 論文API取得テスト
│   ├── test_summarizer.py            # 要約モデル・HTML変換テスト
│   ├── test_storage.py               # 重複管理テスト
│   └── test_mail_poster.py           # メールMIME構築テスト
├── requirements.txt                  # Python依存ライブラリ一覧
├── .env.example                      # ローカル実行用設定テンプレート
├── .gitignore
└── README.md                         # 本説明書
```

---

## 🚀 セットアップ手順（5ステップ）

### ステップ1: WordPress「メールで投稿」を有効化
1. WordPress管理画面（WordPress.com、またはJetpack連携済みWordPress）を開きます。
2. **「設定」** ＞ **「投稿」** を開きます。
3. **「メールで投稿 (Post by Email)」** を有効化します。
4. 生成された専用の投稿用メールアドレス（例: `secret-string12345@post.wordpress.com`）をコピーします。

### ステップ2: Google Gemini APIキーの取得
1. [Google AI Studio](https://aistudio.google.com/) にアクセスします。
2. **「Get API key」** から新しいAPIキーを発行して控えます。

### ステップ3: 送信用SMTPメールアカウントの準備
GitHub Actionsからメールを送信するために、SMTPサーバーを利用します（Gmail推奨）。
- Gmailの場合:
  1. Googleアカウントの [セキュリティ設定](https://myaccount.google.com/security) を開きます。
  2. **「2段階認証」** を有効にします。
  3. **「アプリ パスワード」** を生成し、16桁のパスワードを控えます（これが `SMTP_PASS` になります）。

### ステップ4: GitHubリポジトリの設定（Secrets & Permissions）

#### 4-1. リポジトリの書き込み権限を許可
GitHub Actionsが投稿履歴（`data/posted_papers.json`）を自動コミットするために必要です：
1. GitHubリポジトリの **「Settings」** ＞ **「Actions」** ＞ **「General」** を開きます。
2. **「Workflow permissions」** で **「Read and write permissions」** を選択し、保存（Save）します。

#### 4-2. GitHub Secrets の登録
リポジトリの **「Settings」** ＞ **「Secrets and variables」** ＞ **「Actions」** に移動し、**「New repository secret」** から以下のシークレットを登録します：

| Secret名 | 必須 | 設定する値 |
| :--- | :--- | :--- |
| `GEMINI_API_KEY` | **必須** | ステップ2で取得したGemini APIキー |
| `WP_POST_EMAIL` | **必須** | ステップ1で取得したWordPress投稿用メールアドレス |
| `SMTP_HOST` | 任意 | SMTPサーバー（デフォルト: `smtp.gmail.com`） |
| `SMTP_PORT` | 任意 | SMTPポート（デフォルト: `587`） |
| `SMTP_USER` | **必須** | 送信用メールアドレス（例: `yourname@gmail.com`） |
| `SMTP_PASS` | **必須** | ステップ3で生成したアプリパスワード |

---

## ⏰ 定期実行スケジュールと手動実行

### 自動実行（cron）
デフォルトでは、毎日 **日本時間 午前8:00（UTC 23:00）** に自動実行されます。
実行時間を変更したい場合は、`.github/workflows/paper_to_blog.yml` の cron 式を編集してください：
```yaml
schedule:
  - cron: '0 23 * * *'  # 23:00 UTC = 翌朝 08:00 JST
```

### 手動実行（テスト実行）
GitHubリポジトリの **「Actions」** タブから、いつでもワンクリックで実行できます：
1. **「Auto Post Research Papers to WordPress」** ワークフローを選択。
2. **「Run workflow」** プルダウンをクリック。
3. 以下のオプションを選択して **「Run workflow」** を実行：
   - **`dry_run`**: `true` にするとメール送信を行わずに動作テスト（HTMLや画像生成の確認）ができます。
   - **`force`**: `true` にすると過去の投稿履歴を無視して最新論文を取得します。
   - **`topic`**: `プログラミング教育` や `コンピューテーショナルシンキング` 等、特定の分野に絞り込んで実行できます。

---

## 💻 ローカル環境でのテスト実行

ローカルPCで動作確認を行う場合の手順です：

```bash
# 依存パッケージのインストール
pip install -r requirements.txt

# 環境変数ファイルの作成
cp .env.example .env
# .env を開いて GEMINI_API_KEY などを記入

# 単体テストの実行
python -m tests.test_fetcher
python -m tests.test_storage
python -m tests.test_summarizer

# Dry-run（メール送信なしで論文取得・要約・画像生成をシミュレーション）
python -m src.main --dry-run
```
※ `--dry-run` を実行すると、`temp/preview_post.html` にブログ投稿予定のHTMLファイルが、`temp/eyecatch.png` に生成されたアイキャッチ画像が出力されます。

---

## ⚙️ カスタマイズ設定

### 検索キーワードの調整
`src/config.py` 内の `SEARCH_TOPICS` で、検索クエリを追加・変更できます：
```python
SEARCH_TOPICS = [
    {
        "name": "コンピューテーショナルシンキング",
        "arxiv_query": 'all:"computational thinking"',
        "openalex_query": '"computational thinking"'
    },
    {
        "name": "プログラミング教育",
        "arxiv_query": 'all:"programming education" OR all:"teaching programming"',
        "openalex_query": '"programming education" OR "introductory programming"'
    },
    {
        "name": "情報教育",
        "arxiv_query": 'all:"computer science education" OR all:"computing education"',
        "openalex_query": '"computer science education"'
    }
]
```

### カテゴリとタグの変更
`src/config.py` または `.env`（GitHub Secrets/Variables）で設定できます：
- `WP_CATEGORIES`: WordPressに設定するカテゴリ（カンマ区切り）
- `WP_TAGS`: WordPressに設定するタグ（カンマ区切り）
- `WP_POST_STATUS`: `publish`（即時公開）または `draft`（下書き保存）
