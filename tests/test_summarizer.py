from src.summarizer import PaperSummaryModel, PaperSummarizer

def test_summary_model_and_html():
    summary = PaperSummaryModel(
        blog_title="【海外最新論文】プログラミング教育における生成AI活用の実証研究",
        summary_lead="本研究は初等中等教育におけるプログラミング指導に生成AIを活用した際の学習効果を分析したものです。",
        point1_what="プログラミング教育における対話型指導システムの概要と目的を提示。",
        point2_novelty="従来のコード補完と異なり、思考プロセスを促すソクラテス式対話を導入。",
        point3_core="キモとなるのは、段階的なヒント提示アルゴリズム。",
        point4_evaluation="小学校高学年120名を対象に比較実験を行い、論理的思考力テストで有意差を確認。",
        point5_discussion="過度な依存や自律的試行錯誤の阻害という懸念点も検証。",
        point6_next_papers="AIリテラシー教育に関する最新レビュー論文の併読が推奨される。",
        point7_apa_citation="Smith, J. et al. (2026). Generative AI in Programming Education. Computers & Education, 180, 104500.",
        image_prompt="A 3D isometric illustration of students interacting with a helpful AI tutor for coding."
    )

    paper = {
        "title": "Generative AI in Programming Education",
        "url": "https://doi.org/10.1016/sample",
        "source": "OpenAlex"
    }

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
    assert "[category 情報教育,プログラミング教育]" in html
    assert "[status publish]" in html
    print("test_summary_model_and_html passed!")

if __name__ == "__main__":
    test_summary_model_and_html()
