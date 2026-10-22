"""Is the loaded field old, or has SCOOP learned about data it doesn't have?

Checked on every turn (cheap: file times, no network) and put in the chat agent's
context, which mentions it once at the start of a conversation: how old the field is,
and the data-source plug-ins and survey skills added since it was built that it lacks.
The data agent then refreshes the field or adds the new sources if the user wants.
"""
from __future__ import annotations

import time
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]  # the checkout
STALE_DAYS = 30  # a field older than this may have newer data releases behind it


def _days(seconds: float) -> float:
    return round(seconds / 86400, 1)


def _iso(ts: float) -> str:
    return datetime.fromtimestamp(ts, timezone.utc).date().isoformat()


def field_freshness(field: dict, field_path: Path | None, repo: Path = REPO, now: float | None = None) -> dict:
    """How old a field is, and what SCOOP can add to it that it didn't have when built."""
    now = time.time() if now is None else now
    out: dict = {}
    built = field_path.stat().st_mtime if field_path is not None and field_path.exists() else None
    if built is not None:
        out.update(built=_iso(built), age_days=_days(now - built), old=now - built > STALE_DAYS * 86400)
    try:
        from ..sources import SOURCES
    except Exception:  # an optional plug-in failing to import must not break the turn
        SOURCES = {}
    new_sources = []
    for name, source in sorted(SOURCES.items()):
        if not source.query or name in field.get("tables", {}):
            continue
        module = repo / "scoop" / "sources" / f"{getattr(source.query, '__module__', '').rsplit('.', 1)[-1]}.py"
        if built is None or (module.exists() and module.stat().st_mtime > built):
            new_sources.append({"name": name, "label": source.label})
    new_skills = [p.stem for p in sorted((repo / "scoop" / "skills" / "surveys").glob("*.md"))
                  if built is not None and p.stat().st_mtime > built]
    if new_sources:
        out["new_sources"] = new_sources
    if new_skills:
        out["new_skills"] = new_skills
    out["worth_mentioning"] = bool(out.get("old") or new_sources)
    return out


def freshness(field: dict | None, field_path: Path | None, repo: Path = REPO, now: float | None = None) -> dict:
    return {"field": field_freshness(field, field_path, repo, now)} if field is not None else {}


__all__ = ["STALE_DAYS", "field_freshness", "freshness"]
