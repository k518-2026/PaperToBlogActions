# 情報教育・プログラミング教育・コンピュテーショナルシンキング海外論文 自動収集＆WordPressブログ自動投稿システム (GitHub Actions)

arXivやOpenAlexなどの学術論文APIから「情報教育」「プログラミング教育」「コンピュテーショナルシンキング」に関する最新のオープンアクセス論文を自動取得し、**被引用数の多い重要論文を優先採用**。Google Gemini（テキストモデル）で**各観点150〜300文字・専門用語Wikipediaリンク付きの7観点（落合式フォーマット）**に要約・日本語翻訳。さらにGeminiの画像生成機能で**論文内容を1枚にまとめた教育インフォグラフィックイラスト（グラフィックレコーディング風）**を自動生成し、WordPressへメール経由で自動投稿する**GitHub Actions完全自動化パイプライン**です。

---

## 🌟 主な特徴

- **被引用数の多い論文を優先採用**:
  - OpenAlex API（`title_and_abstract.search` ＆ `sort=cited_by_count:desc`）により、世界中で引用・評価されている影響力の高い論文（被引用数数百件超）を優先的に自動選定。
- **徹底した二重投稿防止リスト管理 (`data/POSTED_PAPERS.md`)**:
  - 過去に投稿された論文を機械用JSON（`data/posted_papers.json`）と、GitHub上で誰でも一目で確認できるMarkdown表（`data/POSTED_PAPERS.md`）の双方で厳格に管理。
  - 論文ID、DOI、URLに加え、**正規化タイトル** による多重照合を行い、同じ論文の重複投稿を100%防止。
- **充実の落合式7観点要約（各150〜300文字 ＆ Wikipediaリンク）**:
  1. **どんなもの？**（150〜300字）
  2. **先行研究と比べてどこがすごいの？**（150〜300字）
  3. **技術や手法の"キモ"はどこにある？**（150〜300字）
  4. **どうやって有効だと検証した？**（150〜300字）
  5. **議論はあるか？**（150〜300字）
  6. **次に読むべき論文はあるか？**（150〜300字）
  7. **論文情報・リンクAPA式**（APA形式による正式書誌情報 + URL）
  - 専門用語（コンピュテーショナルシンキング、認知負荷理論、足場かけ、アクティブラーニング等）には、読者の理解を深めるための**日本語版Wikipediaへのハイパーリンク**を自動付与。
- **論文内容を1枚にまとめたインフォグラフィックイラスト**:
  - 単なるアイキャッチ画像ではなく、論文の全体像を1枚のイラスト（16:9）として解説。
  - **上部ヘッダー帯** ＋ **3カラム構成**（①教育概念・データの視覚化、②授業・現場での活用シーン、③成果と留意点・示唆）による日本の教育図解マンガ・グラフィックレコーディング風のイラストを自動生成。
- **WordPressメール投稿（Post by Email）連携**:
  - 添付画像は自動的にアイキャッチ・メディアに保存。
  - カテゴリ・タグ・即時公開（`[status publish]`）ショートコードとともに自動投稿。
- **完全サーバーレス＆無料運用**:
  - GitHub Actionsのcron（毎日定時実行）で自動稼働し、投稿完了後に履歴ファイルをリポジトリへ自動コミット＆プッシュ。

---

## 📂 フォルダ構成

```
PaperToBlogActions/
├── .github/
│   └── workflows/
│       └── paper_to_blog.yml          # GitHub Actions 定期実行ワークフロー（cron）
├── src/
│   ├── __init__.py
│   ├── config.py                     # 環境変数・教育特化キーワード設定
│   ├── fetcher.py                    # 論文取得モジュール（被引用数ソート＆重複除外）
│   ├── summarizer.py                 # Gemini 7観点要約（150〜300字＋Wikipediaリンク）
│   ├── image_generator.py            # 1枚の教育インフォグラフィックイラスト生成エンジン
│   ├── mail_poster.py                # WordPressメール投稿（SMTP + 画像添付）
│   ├── storage.py                    # 投稿履歴・二重判定＆POSTED_PAPERS.md同期
│   └── main.py                       # パイプライン実行エントリーポイント（CLI）
├── data/
│   ├── posted_papers.json            # 投稿済み論文ID履歴（機械用）
│   └── POSTED_PAPERS.md              # 投稿済み論文リスト（GitHub閲覧用マークダウン）
├── tests/
│   ├── test_fetcher.py               # 論文API取得テスト
│   ├── test_summarizer.py            # 要約モデル・文字数・HTML変換テスト
│   ├── test_storage.py               # 重複管理・Markdown同期テスト
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
GitHub Actionsが投稿履歴（`data/posted_papers.json` および `data/POSTED_PAPERS.md`）を自動コミットするために必要です：
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
毎日 **日本時間 19:00（UTC 10:00）** に自動実行されます。
実行時間を変更したい場合は、`.github/workflows/paper_to_blog.yml` の cron 式を編集してください：
```yaml
schedule:
  - cron: '0 10 * * *'  # 10:00 UTC = 19:00 JST（毎晩19時）
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

# 単体テストの実行
python -m tests.test_fetcher
python -m tests.test_storage
python -m tests.test_summarizer

# Dry-run（メール送信なしで論文取得・要約・画像生成をシミュレーション）
python -m src.main --dry-run
```
※ `--dry-run` を実行すると、`temp/preview_post.html` にブログ投稿予定のHTMLファイルが、`temp/eyecatch.png` に生成されたインフォグラフィックイラスト画像が出力されます。
