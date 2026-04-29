"""
Neolysis — PubMed Crawler
===========================
Crawls PubMed for research papers on ASEAN Neglected Tropical Diseases (NTDs)
and populates the Qdrant "pubmed_ntd" vector collection for RAG.

Usage:
    python scripts/pubmed_crawler.py

Requirements:
    - Qdrant running locally at localhost:6333
    - sentence-transformers installed (pip install sentence-transformers)
    - Internet access for PubMed E-utilities API

Workflow:
    1. Query PubMed E-utilities (no API key needed for ≤ 3 req/sec)
    2. Fetch title + abstract + PMID for each result
    3. Embed with all-MiniLM-L6-v2 (384-dim vectors)
    4. Batch upsert to Qdrant collection "pubmed_ntd"
    5. Save raw results to pubmed_cache.json (for inspection/reuse)

Search terms (ASEAN NTD focus):
    - leptospirosis treatment
    - dengue drug target
    - melioidosis antibiotic
    - scrub typhus therapy
    - ASEAN neglected tropical disease drug

Estimated time: ~5–15 minutes depending on PubMed rate limits.
"""

import sys
import json
import time
import uuid
import logging
from pathlib import Path
from typing import List, Dict, Optional
import requests

# ── Configuration ──────────────────────────────────────────────────────────

SEARCH_TERMS = [
    "leptospirosis treatment drug",
    "dengue NS5 drug target inhibitor",
    "melioidosis antibiotic Burkholderia pseudomallei",
    "scrub typhus therapy Orientia tsutsugamushi",
    "ASEAN neglected tropical disease drug discovery",
]

PUBMED_SEARCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
PUBMED_FETCH_URL  = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
PUBMED_SUMMARY_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"

MAX_RESULTS_PER_TERM = 100     # PubMed free tier limit per call
BATCH_EMBED_SIZE = 32          # Papers per embedding batch
QDRANT_HOST = "localhost"
QDRANT_PORT = 6333
COLLECTION_NAME = "pubmed_ntd"
VECTOR_SIZE = 384
CACHE_FILE = Path("pubmed_cache.json")

# Respect PubMed rate limit: max 3 req/sec without API key
REQUEST_DELAY = 0.4  # seconds between requests

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger("pubmed_crawler")


# ── PubMed Fetching ────────────────────────────────────────────────────────

def search_pubmed(term: str, max_results: int = MAX_RESULTS_PER_TERM) -> List[str]:
    """
    Search PubMed and return a list of PMIDs for the given search term.

    Args:
        term:        Search query string
        max_results: Maximum number of PMIDs to return

    Returns:
        List of PMID strings
    """
    params = {
        "db": "pubmed",
        "term": term,
        "retmax": max_results,
        "retmode": "json",
        "sort": "relevance",
    }
    try:
        resp = requests.get(PUBMED_SEARCH_URL, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        pmids = data.get("esearchresult", {}).get("idlist", [])
        log.info(f"  Found {len(pmids)} PMIDs for: '{term}'")
        return pmids
    except Exception as e:
        log.error(f"  Search failed for '{term}': {e}")
        return []


def fetch_abstracts(pmids: List[str]) -> List[Dict]:
    """
    Fetch titles and abstracts for a list of PMIDs using PubMed efetch.

    Processes in batches of 20 to stay within URL length limits.

    Args:
        pmids: List of PMID strings

    Returns:
        List of {pmid, title, abstract} dicts
    """
    results = []
    batch_size = 20

    for i in range(0, len(pmids), batch_size):
        batch = pmids[i:i + batch_size]
        params = {
            "db": "pubmed",
            "id": ",".join(batch),
            "retmode": "xml",
            "rettype": "abstract",
        }
        try:
            resp = requests.get(PUBMED_FETCH_URL, params=params, timeout=30)
            resp.raise_for_status()
            papers = _parse_pubmed_xml(resp.text, batch)
            results.extend(papers)
            log.debug(f"  Fetched batch {i//batch_size + 1}: {len(papers)} papers")
        except Exception as e:
            log.error(f"  Fetch failed for batch {i}–{i+batch_size}: {e}")

        time.sleep(REQUEST_DELAY)

    return results


def _parse_pubmed_xml(xml_text: str, pmids: List[str]) -> List[Dict]:
    """
    Parse PubMed XML response and extract title + abstract per article.

    Uses xml.etree.ElementTree (stdlib, no extra deps).
    """
    import xml.etree.ElementTree as ET

    results = []
    try:
        root = ET.fromstring(xml_text)
        for article in root.findall(".//PubmedArticle"):
            # PMID
            pmid_el = article.find(".//PMID")
            pmid = pmid_el.text if pmid_el is not None else "unknown"

            # Title
            title_el = article.find(".//ArticleTitle")
            title = "".join(title_el.itertext()) if title_el is not None else ""

            # Abstract: may have multiple AbstractText sections
            abstract_parts = article.findall(".//AbstractText")
            abstract = " ".join(
                "".join(a.itertext()) for a in abstract_parts
            ).strip()

            if title and abstract:  # Skip papers without abstracts
                results.append({
                    "pmid": pmid,
                    "title": title.strip(),
                    "abstract": abstract,
                })
    except ET.ParseError as e:
        log.error(f"XML parse error: {e}")

    return results


# ── Qdrant Upsert ──────────────────────────────────────────────────────────

def ensure_qdrant_collection(client) -> None:
    """Create the Qdrant collection if it doesn't exist."""
    from qdrant_client.models import Distance, VectorParams

    collections = [c.name for c in client.get_collections().collections]
    if COLLECTION_NAME not in collections:
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE),
        )
        log.info(f"Created Qdrant collection '{COLLECTION_NAME}'")
    else:
        log.info(f"Qdrant collection '{COLLECTION_NAME}' already exists")


def upsert_papers_to_qdrant(
    client,
    encoder,
    papers: List[Dict],
) -> int:
    """
    Embed and batch-upsert papers to Qdrant.

    Args:
        client:  QdrantClient instance
        encoder: SentenceTransformer model
        papers:  List of {pmid, title, abstract} dicts

    Returns:
        Number of papers successfully upserted
    """
    from qdrant_client.models import PointStruct

    total_upserted = 0

    for i in range(0, len(papers), BATCH_EMBED_SIZE):
        batch = papers[i:i + BATCH_EMBED_SIZE]
        texts = [f"{p['title']}. {p.get('abstract', '')}" for p in batch]

        # Embed batch
        vectors = encoder.encode(
            texts,
            normalize_embeddings=True,
            batch_size=BATCH_EMBED_SIZE,
            show_progress_bar=False,
        )

        # Build Qdrant points with deterministic UUIDs (pmid-based)
        points = [
            PointStruct(
                id=str(uuid.uuid5(uuid.NAMESPACE_URL, f"pmid:{p['pmid']}")),
                vector=vec.tolist(),
                payload={
                    "pmid":     p["pmid"],
                    "title":    p["title"],
                    "abstract": p.get("abstract", ""),
                },
            )
            for p, vec in zip(batch, vectors)
        ]

        client.upsert(collection_name=COLLECTION_NAME, points=points)
        total_upserted += len(points)
        log.info(f"  Upserted batch {i//BATCH_EMBED_SIZE + 1}: {len(points)} papers")

    return total_upserted


# ── Main ────────────────────────────────────────────────────────────────────

def main() -> None:
    log.info("=" * 60)
    log.info("Neolysis PubMed Crawler")
    log.info(f"Search terms: {len(SEARCH_TERMS)}")
    log.info(f"Max results per term: {MAX_RESULTS_PER_TERM}")
    log.info("=" * 60)

    # ── Import heavy deps ──────────────────────────────────────────────────
    try:
        from qdrant_client import QdrantClient
        from sentence_transformers import SentenceTransformer
    except ImportError as e:
        log.error(f"Missing dependency: {e}")
        log.error("Install with: pip install qdrant-client sentence-transformers")
        sys.exit(1)

    # ── Connect to Qdrant ──────────────────────────────────────────────────
    log.info(f"Connecting to Qdrant at {QDRANT_HOST}:{QDRANT_PORT}...")
    try:
        client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
        ensure_qdrant_collection(client)
        log.info("✓ Qdrant connected")
    except Exception as e:
        log.error(f"✗ Could not connect to Qdrant: {e}")
        log.error("Ensure Qdrant is running: docker run -p 6333:6333 qdrant/qdrant")
        sys.exit(1)

    # ── Load embedding model ───────────────────────────────────────────────
    log.info("Loading embedding model (all-MiniLM-L6-v2)...")
    encoder = SentenceTransformer("all-MiniLM-L6-v2")
    log.info("✓ Model loaded")

    # ── Crawl PubMed ───────────────────────────────────────────────────────
    all_papers: List[Dict] = []
    seen_pmids: set = set()

    for term in SEARCH_TERMS:
        log.info(f"\nSearching: '{term}'")
        pmids = search_pubmed(term)
        time.sleep(REQUEST_DELAY)

        if not pmids:
            continue

        # Deduplicate
        new_pmids = [p for p in pmids if p not in seen_pmids]
        seen_pmids.update(new_pmids)

        if not new_pmids:
            log.info("  All PMIDs already seen — skipping fetch")
            continue

        log.info(f"  Fetching abstracts for {len(new_pmids)} new PMIDs...")
        papers = fetch_abstracts(new_pmids)
        all_papers.extend(papers)
        log.info(f"  → {len(papers)} papers with abstracts")

    log.info(f"\nTotal unique papers with abstracts: {len(all_papers)}")

    if not all_papers:
        log.warning("No papers fetched. Check network connectivity and PubMed API.")
        sys.exit(0)

    # ── Save cache ─────────────────────────────────────────────────────────
    CACHE_FILE.write_text(json.dumps(all_papers, indent=2, ensure_ascii=False))
    log.info(f"✓ Raw results saved to: {CACHE_FILE}")

    # ── Upsert to Qdrant ───────────────────────────────────────────────────
    log.info("\nEmbedding and upserting to Qdrant...")
    total = upsert_papers_to_qdrant(client, encoder, all_papers)
    log.info(f"✓ Successfully upserted {total} papers to Qdrant collection '{COLLECTION_NAME}'")
    log.info("\nCrawler complete! The RAG pipeline is ready.")
    log.info("You can now call POST /api/v1/insight to generate grounded insights.")


if __name__ == "__main__":
    main()
