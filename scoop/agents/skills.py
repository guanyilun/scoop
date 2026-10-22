"""SCOOP's skills, for every agent: the list in its prompt, the text on demand.

A skill is knowledge in markdown (scoop/skills/<group>/<name>.md): what data exist and
where, versions, gotchas, defaults. It holds no code; tools do the computing. Each agent's
prompt lists the skills by name and one-line description (from their front matter), and
the agent reads one in full with read_skill when the task needs it.
"""
from __future__ import annotations

from pathlib import Path
from typing import Annotated

from langchain_core.messages import ToolMessage
from langchain_core.tools import InjectedToolCallId, tool

SKILLS_DIR = Path(__file__).resolve().parents[1] / "skills"
MAX_SKILL_CHARS = 20000


def front_matter(text: str) -> dict[str, str]:
    """The YAML-style header between the first two '---' lines, as flat strings
    (indented lines continue the previous value)."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}
    fields: dict[str, str] = {}
    key = None
    for line in lines[1:]:
        if line.strip() == "---":
            break
        if line[:1].isspace() and key:
            fields[key] += " " + line.strip()
        elif ":" in line:
            key, value = line.split(":", 1)
            key = key.strip()
            fields[key] = value.strip()
    return fields


def skill_paths(skills_dir: Path = SKILLS_DIR) -> list[str]:
    """Every skill's path as read_skill takes it, e.g. "surveys/gaia"."""
    return sorted(str(p.relative_to(skills_dir).with_suffix("")) for p in skills_dir.rglob("*.md")
                  if p.parent != skills_dir)


def skills_listing(skills_dir: Path = SKILLS_DIR) -> str:
    """One line per skill for a prompt: its path, status if not reviewed, and description."""
    lines = []
    for path in skill_paths(skills_dir):
        meta = front_matter((skills_dir / f"{path}.md").read_text())
        draft = " (draft)" if meta.get("status") == "draft" else ""
        lines.append(f"- {path}{draft}: {meta.get('description', '')}".rstrip(": "))
    return "\n".join(lines)


def with_skills(prompt: str, skills_dir: Path = SKILLS_DIR) -> str:
    """An agent's instructions followed by the skills it can read."""
    return (f"{prompt.rstrip()}\n\n# Skills (read one in full with read_skill before relying on it)\n"
            f"{skills_listing(skills_dir)}\n")


def build_read_skill(skills_dir: Path = SKILLS_DIR):
    @tool
    async def read_skill(path: str, tool_call_id: Annotated[str, InjectedToolCallId]):
        """Read one of SCOOP's skills in full: a path from the skills list in your
        instructions, without ".md", e.g. "surveys/gaia" or "astrometry/proper_motions"
        ("index" gives the list grouped by topic)."""
        target = (skills_dir / f"{path.strip().strip('/')}.md").resolve()
        if not target.is_relative_to(skills_dir.resolve()) or not target.is_file():
            return ToolMessage(content=f"No skill {path!r}. Available: {skill_paths(skills_dir)}",
                               tool_call_id=tool_call_id, status="error")
        text = target.read_text()
        cut = f"\n[... truncated at {MAX_SKILL_CHARS} characters]" if len(text) > MAX_SKILL_CHARS else ""
        return ToolMessage(content=text[:MAX_SKILL_CHARS] + cut, tool_call_id=tool_call_id)

    return read_skill


__all__ = ["MAX_SKILL_CHARS", "SKILLS_DIR", "build_read_skill", "front_matter", "skill_paths", "skills_listing",
           "with_skills"]
