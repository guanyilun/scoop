"""ADS lookups for the exoplanet agent: find papers, and fetch a paper's abstract.

The abstract is what the agent quotes from: checks.check_claims accepts a claim about
a paper only if its excerpt appears word for word in that paper's get_abstract result.

Both go through SCOOP's one ADS client (scoop.literature.ads.ADSClient, the server's,
with the token from Settings), so the token is read in one place. Each result also
carries the client's ADS payload (scoop.literature.serialization.result_payload) as its
artifact; the hand-off publishes those, and the papers appear in the Literature panel
as the chat agent's do.
"""

from __future__ import annotations

import html
import re
from typing import Any, NamedTuple

from ..literature.models import ADSResult, PaperRequest, SearchRequest
from ..literature.serialization import result_payload
from .archive import ArchiveError, now

ABS_URL = "https://ui.adsabs.harvard.edu/abs/"
MAX_ROWS = 20
UNAVAILABLE = "Report that the literature search is unavailable rather than citing papers from memory."


class Published(NamedTuple):
    """A tool's result for the model, and the ADS payload for the Literature panel."""
    result: Any
    artifact: dict


def plain_text(text: str | None) -> str | None:
    """ADS abstracts carry HTML (<BR />, R<SUB>p</SUB>, &amp;): give the model, and the
    quote check, the same plain text."""
    if text is None:
        return None
    text = re.sub(r"<\s*br\s*/?\s*>", " ", text, flags=re.I)
    text = re.sub(r"<[^>]+>", "", text)
    return re.sub(r"\s+", " ", html.unescape(text)).strip()


def _first_author(authors: tuple[str, ...]) -> str | None:
    return f"{authors[0]}{' et al.' if len(authors) > 1 else ''}" if authors else None


def _ok(client) -> None:
    if client is None:
        raise ArchiveError("ADS is not configured (set an ADS token in SCOOP's Settings). " + UNAVAILABLE)


def _checked(result: ADSResult) -> ADSResult:
    if result.error is not None and not result.papers:
        status = f", HTTP {result.error.http_status}" if result.error.http_status else ""
        raise ArchiveError(f"ADS request failed ({result.error.kind}{status}). {UNAVAILABLE}")
    return result


async def find_papers(client, query: str, rows: int = 10, refereed_only: bool = False) -> Published:
    """ADS search, most relevant first: bibcode, title, first author, year, citations.
    No abstracts here (they are long); fetch the ones you need with get_abstract."""
    _ok(client)
    result = _checked(await client.search(SearchRequest(
        query=query, page_size=min(max(rows, 1), MAX_ROWS), refereed=True if refereed_only else None)))
    papers = [{"bibcode": p.publication.ref.native_id, "title": plain_text(p.publication.title),
               "first_author": _first_author(p.authors), "year": p.year, "journal": p.venue,
               "type": p.publication.publication_type, "citations": p.citation_count,
               "url": ABS_URL + p.publication.ref.native_id} for p in result.papers]
    return Published({"query": query, "refereed_only": refereed_only, "n_found": result.total_count or 0,
                      "papers": papers, "archive": "ADS", "retrieved_at": now()}, result_payload(result))


async def get_abstract(client, bibcode: str) -> Published:
    """One paper's title, authors and full abstract, the text claims about it must quote."""
    _ok(client)
    result = _checked(await client.get_paper(PaperRequest(bibcode)))
    if not result.papers:
        raise ArchiveError(f"ADS has no paper with bibcode '{bibcode}'. Use a bibcode returned by "
                           "find_papers or get_planets.")
    p = result.papers[0]
    bibcode = p.publication.ref.native_id
    return Published({"bibcode": bibcode, "title": plain_text(p.publication.title), "authors": list(p.authors[:10]),
                      "year": p.year, "journal": p.venue, "abstract": plain_text(p.abstract),
                      "url": ABS_URL + bibcode, "archive": "ADS", "retrieved_at": now()}, result_payload(result))


__all__ = ["Published", "find_papers", "get_abstract", "plain_text"]
