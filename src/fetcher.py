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
    and Computational Thinking from arXiv, OpenAlex, and PLOS.
    """

    DEFAULT_USER_AGENT = "PaperToBlogActions/1.0 (mailto:education-research-bot@example.com)"

    @staticmethod
    def _clean_text(text: Optional[str]) -> str:
        if not text:
            return ""
        return " ".join(text.replace("\n", " ").split()).strip()

    @classmethod
    def fetch_arxiv(cls, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """Fetch papers from arXiv Atom API."""
        encoded_query = urllib.parse.quote(query)
        url = f"http://export.arxiv.org/api/query?search_query={encoded_query}&start=0&max_results={max_results}&sortBy=submittedDate&sortOrder=descending"

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
                    "url": paper_url,
                    "source": "arXiv"
                })
        except Exception as e:
            logger.error(f"Error fetching from arXiv: {e}")

        return papers

    @classmethod
    def fetch_openalex(cls, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """Fetch open access papers from OpenAlex API."""
        encoded_query = urllib.parse.quote(query)
        url = (
            f"https://api.openalex.org/works?search={encoded_query}"
            f"&filter=open_access.is_oa:true&sort=publication_date:desc&per_page={max_results}"
        )

        papers = []
        try:
            req = urllib.request.Request(url, headers={"User-Agent": cls.DEFAULT_USER_AGENT})
            with urllib.request.urlopen(req, timeout=20) as resp:
                data = json.loads(resp.read().decode("utf-8"))

            for work in data.get("results", []):
                work_id = work.get("id")
                doi = work.get("doi")
                title = cls._clean_text(work.get("title"))
                pub_date = work.get("publication_date", "")

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

                if title and abstract:
                    papers.append({
                        "id": doi or work_id,
                        "doi": doi,
                        "title": title,
                        "abstract": abstract,
                        "authors": authors,
                        "published_date": pub_date,
                        "url": landing_url,
                        "source": "OpenAlex"
                    })
        except Exception as e:
            logger.error(f"Error fetching from OpenAlex: {e}")

        return papers

    @classmethod
    def fetch_plos(cls, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """Fetch papers from PLOS Search API."""
        encoded_query = urllib.parse.quote(f'"{query}"')
        url = (
            f"https://api.plos.org/search?q={encoded_query}"
            f"&fl=id,title,abstract,author_display,publication_date&rows={max_results}&sort=publication_date+desc"
        )

        papers = []
        try:
            req = urllib.request.Request(url, headers={"User-Agent": cls.DEFAULT_USER_AGENT})
            with urllib.request.urlopen(req, timeout=20) as resp:
                data = json.loads(resp.read().decode("utf-8"))

            for doc in data.get("response", {}).get("docs", []):
                doc_id = doc.get("id")
                title = cls._clean_text(doc.get("title"))
                abstract_list = doc.get("abstract", [])
                abstract = cls._clean_text(" ".join(abstract_list) if isinstance(abstract_list, list) else str(abstract_list))
                pub_date = (doc.get("publication_date") or "")[:10]
                authors = doc.get("author_display") or []

                if title and abstract:
                    papers.append({
                        "id": doc_id,
                        "doi": f"https://doi.org/{doc_id}",
                        "title": title,
                        "abstract": abstract,
                        "authors": authors,
                        "published_date": pub_date,
                        "url": f"https://journals.plos.org/plosone/article?id={doc_id}",
                        "source": "PLOS"
                    })
        except Exception as e:
            logger.error(f"Error fetching from PLOS: {e}")

        return papers

    @classmethod
    def get_latest_unposted_paper(
        cls,
        storage: StorageManager,
        topics: List[Dict[str, Any]],
        force: bool = False
    ) -> Optional[Dict[str, Any]]:
        """
        Scan topics across arXiv, OpenAlex, and PLOS, and return the first unposted paper.
        If force=True, ignore whether it has been posted.
        """
        all_candidates = []

        for topic_info in topics:
            topic_name = topic_info.get("name", "")
            arxiv_q = topic_info.get("arxiv_query", "")
            openalex_q = topic_info.get("openalex_query", "")

            logger.info(f"Searching arXiv for: {topic_name}")
            arxiv_papers = cls.fetch_arxiv(arxiv_q, max_results=5)
            for p in arxiv_papers:
                p["topic"] = topic_name
            all_candidates.extend(arxiv_papers)

            logger.info(f"Searching OpenAlex for: {topic_name}")
            openalex_papers = cls.fetch_openalex(openalex_q, max_results=5)
            for p in openalex_papers:
                p["topic"] = topic_name
            all_candidates.extend(openalex_papers)

        logger.info(f"Total retrieved candidate papers: {len(all_candidates)}")

        # Deduplicate candidates by ID
        unique_candidates = []
        seen_ids = set()
        for paper in all_candidates:
            pid = paper.get("id")
            if pid and pid not in seen_ids:
                seen_ids.add(pid)
                unique_candidates.append(paper)

        # Find first unposted paper
        for paper in unique_candidates:
            paper_id = paper.get("id")
            if force or not storage.is_posted(paper_id):
                logger.info(f"Selected unposted paper: [{paper.get('source')}] {paper.get('title')}")
                return paper

        logger.info("All retrieved papers have already been posted.")
        return None
