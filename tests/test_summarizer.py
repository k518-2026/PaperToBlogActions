from src.summarizer import PaperSummaryModel, PaperSummarizer

def test_summary_model_and_html():
    summary = PaperSummaryModel(
        blog_title="【必読論文】プログラミング教育における生成AI活用とコンピュテーショナルシンキングの育成",
        summary_lead="本研究は、初等中等教育におけるプログラミング指導に生成AIを取り入れた際の影響を実証的に分析した重要論文です。",
        point1_what="本研究は、初等・中等教育における情報教育およびプログラミング教育を対象に、児童生徒のコンピュテーショナル・シンキングの成長プロセスを可視化・評価することを目的とした包括的研究です。プログラミングの単なる文法習得にとどまらず、論理的思考や抽象化、問題分解といった高次の思考力をいかに授業内で育成できるかについて、理論的背景と教育実践の両面から詳細に検討されています。",
        point2_novelty="従来の研究では成果物としての完成コード評価が主流でしたが、本研究では認知負荷理論に基づき学習者のリアルタイムな試行錯誤プロセスに着目した点が決定的に画期的です。生徒がつまずくポイントを即座に特定し、個別の習熟度に応じた指導を可能にするフレームワークを構築しました。これにより、学習の脱落防止と自律的思考力の向上を同時に達成できる点が先行研究と比較して極めて優れています。",
        point3_core="技術や手法のキモは、学習者の作業ログから自動的に足場かけを提供する適応型アルゴリズムにあります。画一的な正解を与えるのではなく、思考を促すプロンプトを段階的に提示することで、自律的な問題解決能力を損なわずに学習を継続させることができます。生徒の理解度に合わせてヒントの粒度を動的に調整する仕組みが本手法の最も革新的なコア技術となっています。",
        point4_evaluation="公立中学校の生徒240名を対象に半年間の比較対照実験を実施しました。事前事後テストおよびルーブリック評価の結果、提案システムを利用したグループは論理的思考力と学習意欲のスコアにおいて有意に高い向上を示しました。また、定期的なアンケート調査や授業内観察データからも、生徒の主体的な対話と深い概念理解が促進されていることが統計的に実証されました。",
        point5_discussion="教育現場における教員の指導スキル格差や、分析ダッシュボードを有効活用するための研修の必要性が議論されています。また、個別学習とアクティブ・ラーニングによる協調学習とのバランス設計が今後の課題として示されています。さらに生徒のプライバシー保護と学習履歴データの倫理的な取り扱い方針の確立についても継続的な議論が必要です。",
        point6_next_papers="次に読むべき論文としては、コンピュテーショナルシンキングの定量的評価尺度に関する国際学会の最新研究や、教育現場におけるAI倫理ガイドラインに関するレビュー論文の併読が強く推奨されます。特に学習分析を応用した形成的評価の設計手法を扱う関連文献を読み進めることで、本研究の成果をさらに多角的な授業改善に展開できます。",
        point7_apa_citation="Smith, J. et al. (2026). Generative AI in Programming Education. Computers & Education, 180, 104500.",
        infographic_title="「プログラミング教育」と現場の向き合い方",
        infographic_col1="Background and concept metrics with student character and charts",
        infographic_col2="Classroom teaching scenarios, individual feedback and teacher-student coaching",
        infographic_col3="Outcomes, privacy security guidelines, and balanced qualitative-quantitative data",
        infographic_prompt="A 16:9 Japanese educational infographic poster."
    )

    paper = {
        "title": "Generative AI in Programming Education",
        "url": "https://doi.org/10.1016/sample",
        "source": "OpenAlex",
        "cited_by_count": 520
    }

    # Verify character length constraints (all between 150 and 300 chars)
    for i, pt in enumerate([
        summary.point1_what, summary.point2_novelty, summary.point3_core,
        summary.point4_evaluation, summary.point5_discussion, summary.point6_next_papers
    ], 1):
        assert 150 <= len(pt) <= 300, f"Point {i} length {len(pt)} is outside 150-300 characters!"

    html = PaperSummarizer.format_html_post(
        summary=summary,
        paper=paper,
        categories="情報教育,プログラミング教育",
        tags="AI活用,コンピュテーショナルシンキング",
        status="publish"
    )

    assert "1. どんなもの？" in html
    assert "2. 先行研究と比べてどこがすごいの？" in html
    assert "3. 技術や手法の\"キモ\"はどこにある？" in html
    assert "4. どうやって有効だと検証した？" in html
    assert "5. 議論はあるか？" in html
    assert "6. 次に読むべき論文はあるか？" in html
    assert "7. 論文情報・リンク（APA式）" in html
    assert "被引用数: 520 回" in html
    assert "本記事作成時点の被引用数:" in html
    assert "[category 情報教育,プログラミング教育]" in html
    print("test_summary_model_and_html passed with character length and citations verified!")

def test_wikipedia_validation():
    from src.summarizer import WikipediaValidator

    # Test 1: validate_titles with existing, redirected, and non-existent articles
    titles = ["情報教育", "Scratch", "存在しない架空のテスト項目12345"]
    val_map = WikipediaValidator.validate_titles(titles)

    assert val_map["情報教育"] == "情報教育", f"Expected '情報教育', got {val_map.get('情報教育')}"
    assert val_map["Scratch"] == "スクラッチ", f"Expected 'スクラッチ', got {val_map.get('Scratch')}"
    assert val_map["存在しない架空のテスト項目12345"] is None, f"Expected None for missing article, got {val_map.get('存在しない架空のテスト項目12345')}"

    # Test 2: process_text_links strips missing links and preserves valid ones
    input_text = (
        '本稿では、<a href="https://ja.wikipedia.org/wiki/情報教育">情報教育</a>の発展と、'
        '<a href="https://ja.wikipedia.org/wiki/存在しない架空のテスト項目12345">架空の概念</a>の検討、'
        'および[Scratch](https://ja.wikipedia.org/wiki/Scratch)の活用について解説する。'
    )
    processed = WikipediaValidator.process_text_links(input_text)

    # Valid links must be present with canonical target
    assert 'https://ja.wikipedia.org/wiki/%E6%83%85%E5%A0%B1%E6%95%99%E8%82%B2' in processed
    assert 'https://ja.wikipedia.org/wiki/%E3%82%B9%E3%82%AF%E3%83%A9%E3%83%83%E3%83%81' in processed
    assert 'target="_blank"' in processed

    # Non-existent link must be stripped into plain text (no <a> tag for it)
    assert '架空の概念' in processed
    assert 'href="https://ja.wikipedia.org/wiki/存在しない架空のテスト項目12345"' not in processed
    assert '<a href=' in processed  # Only valid links remain as <a>

    # Test 3: post_process_links on PaperSummaryModel
    summary = PaperSummaryModel(
        blog_title="テストタイトル",
        summary_lead="テストリード文",
        point1_what='初等教育の<a href="https://ja.wikipedia.org/wiki/プログラミング教育">プログラミング教育</a>と<a href="https://ja.wikipedia.org/wiki/情報教育">情報教育</a>の比較。',
        point2_novelty='テスト2',
        point3_core='テスト3',
        point4_evaluation='テスト4',
        point5_discussion='テスト5',
        point6_next_papers='テスト6',
        point7_apa_citation='テスト7',
        infographic_title='テスト',
        infographic_col1='col1',
        infographic_col2='col2',
        infographic_col3='col3',
        infographic_prompt='prompt'
    )

    cleaned_summary = PaperSummarizer.post_process_links(summary)
    # プログラミング教育 does not exist on ja.wikipedia.org, so it should be plain text
    assert '<a href="https://ja.wikipedia.org/wiki/プログラミング教育"' not in cleaned_summary.point1_what
    assert 'プログラミング教育' in cleaned_summary.point1_what
    # 情報教育 exists, so it should be linked
    assert '<a href="https://ja.wikipedia.org/wiki/%E6%83%85%E5%A0%B1%E6%95%99%E8%82%B2"' in cleaned_summary.point1_what

    print("test_wikipedia_validation passed successfully!")

def test_unsplash_photo_info_and_html():
    from src.image_generator import UnsplashPhotoInfo

    photo_info = UnsplashPhotoInfo(
        photo_id="test123abc",
        image_url="https://images.unsplash.com/photo-123456789-test",
        photographer_name="Jane Doe",
        photographer_url="https://unsplash.com/@janedoe",
        download_location="https://api.unsplash.com/photos/test123abc/download",
        alt_description="Classroom computers and code",
        app_name="PaperToBlogActions"
    )

    # Check UTM parameters and attribution HTML
    assert "utm_source=PaperToBlogActions" in photo_info.attribution_html
    assert "utm_medium=referral" in photo_info.attribution_html

    summary = PaperSummaryModel(
        blog_title="Unsplashテスト記事",
        summary_lead="Unsplash連携のテストリード文です。",
        point1_what="1" * 160,
        point2_novelty="2" * 160,
        point3_core="3" * 160,
        point4_evaluation="4" * 160,
        point5_discussion="5" * 160,
        point6_next_papers="6" * 160,
        point7_apa_citation="Test Citation (2026)",
        infographic_title="Title",
        infographic_col1="col1",
        infographic_col2="col2",
        infographic_col3="col3",
        infographic_prompt="prompt",
        unsplash_keywords="coding classroom"
    )

    paper = {
        "title": "Unsplash Integration Paper",
        "url": "https://doi.org/10.1000/182",
        "source": "OpenAlex",
        "cited_by_count": 88
    }

    html = PaperSummarizer.format_html_post(
        summary=summary,
        paper=paper,
        photo_info=photo_info
    )

    # Top image is NOT inserted
    assert '<img src="https://images.unsplash.com/photo-123456789-test"' not in html
    # Footer attribution is present
    assert "utm_source=PaperToBlogActions" in html
    assert "Jane Doe" in html
    assert "Unsplash" in html
    assert "📷 <strong>アイキャッチ写真:</strong>" in html
    print("test_unsplash_photo_info_and_html passed successfully!")

if __name__ == "__main__":
    test_summary_model_and_html()
    test_wikipedia_validation()
    test_unsplash_photo_info_and_html()
