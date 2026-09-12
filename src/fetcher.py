import logging
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
import json
from typing import List, Dict, Any, Optional
from .storage import StorageManager

logger = logging.getLogger(__name__)

class PaperFetcher:
    """
    Fetches academic papers on Computer Science Education, Programming Education,
    and Computational Thinking, prioritizing papers with high citation counts.
    """

    DEFAULT_USER_AGENT = "PaperToBlogActions/1.0 (mailto:education-research-bot@example.com)"

    @staticmethod
    def _clean_text(text: Optional[str]) -> str:
        if not text:
            return ""
        return " ".join(text.replace("\n", " ").split()).strip()

    @classmethod
    def fetch_openalex(cls, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """
        Fetch papers from OpenAlex API sorted by citation count descending.
        """
        encoded_query = urllib.parse.quote(query)
        # Sort by cited_by_count:desc to actively fetch high-impact educational papers
        url = (
            f"https://api.openalex.org/works?"
            f"filter=open_access.is_oa:true,from_publication_date:2020-01-01,title_and_abstract.search:{encoded_query}"
            f"&sort=cited_by_count:desc&per_page={max_results}"
        )

        papers = []
        try:
            req = urllib.request.Request(url, headers={"User-Agent": cls.DEFAULT_USER_AGENT})
            with urllib.request.urlopen(req, timeout=25) as resp:
                data = json.loads(resp.read().decode("utf-8"))

            for work in data.get("results", []):
                work_id = work.get("id")
                doi = work.get("doi")
                title = cls._clean_text(work.get("title"))
                pub_date = work.get("publication_date", "")
                cited_by_count = work.get("cited_by_count", 0)

                # Reconstruct abstract from inverted index
                inverted = work.get("abstract_inverted_index")
                abstract = ""
                if inverted:
                    pos_map = {pos: word for word, positions in inverted.items() for pos in positions}
                    abstract = " ".join(pos_map[i] for i in sorted(pos_map.keys()))
                abstract = cls._clean_text(abstract)

                # Authors
                authors = []
                for authorship in work.get("authorships", []):
                    author = authorship.get("author", {})
                    display_name = author.get("display_name")
                    if display_name:
                        authors.append(display_name)

                # Landing URL
                primary_loc = work.get("primary_location") or {}
                landing_url = doi or primary_loc.get("landing_page_url") or work_id

                if title and (abstract or len(title) > 30):
                    papers.append({
                        "id": doi or work_id,
                        "doi": doi,
                        "title": title,
                        "abstract": abstract or title,
                        "authors": authors,
                        "published_date": pub_date,
                        "cited_by_count": cited_by_count,
                        "url": landing_url,
                        "source": "OpenAlex"
                    })
            logger.info(f"OpenAlex fetched {len(papers)} papers (Top citation: {papers[0]['cited_by_count'] if papers else 0})")
        except Exception as e:
            logger.error(f"Error fetching from OpenAlex: {e}")

        return papers

    @classmethod
    def fetch_arxiv(cls, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """Fetch papers from arXiv Atom API."""
        encoded_query = urllib.parse.quote(query)
        url = (
            f"http://export.arxiv.org/api/query?search_query={encoded_query}"
            f"&start=0&max_results={max_results}&sortBy=relevance&sortOrder=descending"
        )

        papers = []
        try:
            req = urllib.request.Request(url, headers={"User-Agent": cls.DEFAULT_USER_AGENT})
            with urllib.request.urlopen(req, timeout=20) as resp:
                xml_data = resp.read()

            root = ET.fromstring(xml_data)
            atom_ns = {"atom": "http://www.w3.org/2005/Atom"}

            for entry in root.findall("atom:entry", atom_ns):
                paper_id = entry.find("atom:id", atom_ns).text.strip()
                title = cls._clean_text(entry.find("atom:title", atom_ns).text)
                summary = cls._clean_text(entry.find("atom:summary", atom_ns).text)
                published = entry.find("atom:published", atom_ns).text[:10]

                authors = []
                for author in entry.findall("atom:author", atom_ns):
                    name = author.find("atom:name", atom_ns)
                    if name is not None and name.text:
                        authors.append(name.text.strip())

                # URL
                paper_url = paper_id
                for link in entry.findall("atom:link", atom_ns):
                    if link.attrib.get("type") == "text/html":
                        paper_url = link.attrib.get("href")
                        break

                papers.append({
                    "id": paper_id,
                    "title": title,
                    "abstract": summary,
                    "authors": authors,
                    "published_date": published,
                    "cited_by_count": 0,  # arXiv preprints citation default
                    "url": paper_url,
                    "source": "arXiv"
                })
        except Exception as e:
            logger.error(f"Error fetching from arXiv: {e}")

        return papers

    @classmethod
    def get_latest_unposted_paper(
        cls,
        storage: StorageManager,
        topics: List[Dict[str, Any]],
        force: bool = False
    ) -> Optional[Dict[str, Any]]:
        """
        Scan topics, sort all candidates strictly by citation count descending,
        and select the highest-impact paper that has not been posted yet.
        """
        all_candidates = []

        for topic_info in topics:
            topic_name = topic_info.get("name", "")
            openalex_q = topic_info.get("openalex_query", "")
            arxiv_q = topic_info.get("arxiv_query", "")

            # Prioritize OpenAlex for citation-ranked peer-reviewed papers
            logger.info(f"Searching OpenAlex (cited_by_count:desc) for: {topic_name}")
            openalex_papers = cls.fetch_openalex(openalex_q, max_results=8)
            for p in openalex_papers:
                p["topic"] = topic_name
            all_candidates.extend(openalex_papers)

            # Also fetch from arXiv
            logger.info(f"Searching arXiv for: {topic_name}")
            arxiv_papers = cls.fetch_arxiv(arxiv_q, max_results=4)
            for p in arxiv_papers:
                p["topic"] = topic_name
            all_candidates.extend(arxiv_papers)

        logger.info(f"Total candidate papers retrieved: {len(all_candidates)}")

        # Deduplicate candidates by ID and normalized title
        unique_candidates = []
        seen_ids = set()
        seen_titles = set()

        for paper in all_candidates:
            pid = paper.get("id")
            norm_title = StorageManager.normalize_title(paper.get("title"))

            if pid and pid in seen_ids:
                continue
            if norm_title and norm_title in seen_titles:
                continue

            if pid:
                seen_ids.add(pid)
            if norm_title:
                seen_titles.add(norm_title)
            unique_candidates.append(paper)

        # Sort candidate papers by citation count DESCENDING (highest citations first!)
        unique_candidates.sort(key=lambda p: p.get("cited_by_count", 0), reverse=True)

        logger.info("Candidate papers ranked by citations:")
        for idx, p in enumerate(unique_candidates[:5], 1):
            logger.info(f"  #{idx} [Citations: {p.get('cited_by_count')}] [{p.get('source')}] {p.get('title')[:60]}...")

        # Find first unposted paper
        for paper in unique_candidates:
            paper_id = paper.get("id")
            paper_title = paper.get("title")
            if force or not storage.is_posted(paper_id, paper_title):
                logger.info(
                    f"Selected paper: [Citations: {paper.get('cited_by_count')}] "
                    f"[{paper.get('source')}] {paper_title}"
                )
                return paper

        logger.info("All retrieved candidate papers have already been posted.")
        return None
