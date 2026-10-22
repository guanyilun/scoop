"""Skills: every agent lists and reads the same ones, and the index keeps up with them."""
import asyncio
import re
import tempfile
import unittest
from pathlib import Path

try:
    from scoop.agents.skills import SKILLS_DIR, build_read_skill, front_matter, skill_paths, with_skills
except ModuleNotFoundError as exc:
    if exc.name.split(".")[0] not in {"langchain_core", "pydantic"}:
        raise
    SKILLS_DIR = None


def read(tool, path):
    return asyncio.run(tool.ainvoke({"type": "tool_call", "name": "read_skill", "id": "s", "args": {"path": path}}))


@unittest.skipIf(SKILLS_DIR is None, "optional agent dependencies absent")
class SkillTests(unittest.TestCase):
    def test_every_skill_says_when_to_read_it_and_the_index_lists_it(self):
        index = (SKILLS_DIR / "index.md").read_text()
        linked = set(re.findall(r"\]\(([^)#]+\.md)\)", index))
        for path in skill_paths():
            with self.subTest(skill=path):
                meta = front_matter((SKILLS_DIR / f"{path}.md").read_text())
                self.assertTrue(meta.get("name") and len(meta.get("description", "")) > 20)
                self.assertIn(f"{path}.md", linked)
        self.assertEqual([p for p in linked if not (SKILLS_DIR / p).is_file()], [])

    def test_the_listing_marks_drafts_and_read_skill_stays_inside(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "surveys").mkdir()
            (root / "surveys" / "act.md").write_text("---\nname: act\ndescription: ACT maps,\n  and y maps.\n"
                                                     "status: draft\n---\n# ACT\n")
            (root / "index.md").write_text("# index\n")
            prompt = with_skills("You are an agent.", root)
            self.assertTrue(prompt.endswith("- surveys/act (draft): ACT maps, and y maps.\n"))
            tool = build_read_skill(root)
            self.assertIn("# ACT", read(tool, "surveys/act").content)
            self.assertIn("# index", read(tool, "index").content)
            for bad in ("../x", "surveys/nope", "/etc/passwd"):
                self.assertEqual(read(tool, bad).status, "error")

    def test_no_skill_is_cut_short(self):
        from scoop.agents.skills import MAX_SKILL_CHARS
        self.assertEqual([p for p in skill_paths() if len((SKILLS_DIR / f"{p}.md").read_text()) > MAX_SKILL_CHARS],
                         [])


if __name__ == "__main__":
    unittest.main()
