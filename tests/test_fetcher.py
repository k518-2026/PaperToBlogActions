from src.fetcher import PaperFetcher

def test_fetch_arxiv():
    papers = PaperFetcher.fetch_arxiv('all:"computational thinking"', max_results=2)
    print(f"Fetched {len(papers)} papers from arXiv")
    assert len(papers) > 0
    p = papers[0]
    assert "title" in p
    assert "abstract" in p
    assert "url" in p
    assert p["source"] == "arXiv"
    print(f"Sample arXiv paper: {p['title']}")

def test_fetch_openalex():
    papers = PaperFetcher.fetch_openalex('"computational thinking"', max_results=2)
    print(f"Fetched {len(papers)} papers from OpenAlex")
    assert len(papers) > 0
    p = papers[0]
    assert "title" in p
    assert "abstract" in p
    assert "url" in p
    assert p["source"] == "OpenAlex"
    print(f"Sample OpenAlex paper: {p['title']}")

if __name__ == "__main__":
    test_fetch_arxiv()
    test_fetch_openalex()
    print("All fetcher tests passed!")
