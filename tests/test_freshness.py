import os
import tempfile
import time
import unittest
from pathlib import Path

from scoop.runtime.freshness import field_freshness, freshness


class FreshnessTests(unittest.TestCase):
    def test_old_fields_and_new_sources_are_worth_mentioning(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            (tmp / "scoop" / "skills" / "surveys").mkdir(parents=True)
            (tmp / "scoop" / "sources").mkdir(parents=True)
            field_path = tmp / "draco_1_field.json"
            field_path.write_text("{}")
            built = time.time() - 40 * 86400
            os.utime(field_path, (built, built))
            (tmp / "scoop" / "skills" / "surveys" / "euclid.md").write_text("new")  # written after the field
            for module in ("tic", "tess_tois", "exoplanets", "mast_tso"):
                (tmp / "scoop" / "sources" / f"{module}.py").write_text("")
            out = field_freshness({"tables": {"gaia": {}, "tic": {}}}, field_path, repo=tmp)
        self.assertTrue(out["old"])
        self.assertEqual(out["age_days"], 40.0)
        names = [s["name"] for s in out["new_sources"]]
        self.assertIn("tess_tois", names)
        self.assertNotIn("tic", names)  # the field already has it
        self.assertEqual(out["new_skills"], ["euclid"])
        self.assertTrue(out["worth_mentioning"])

    def test_a_fresh_field_is_not_mentioned(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            field_path = tmp / "f_field.json"
            field_path.write_text("{}")
            out = freshness({"tables": {}}, field_path, repo=tmp, now=field_path.stat().st_mtime + 60)
        self.assertFalse(out["field"]["old"])
        self.assertFalse(out["field"]["worth_mentioning"])
        self.assertEqual(freshness(None, None), {})


if __name__ == "__main__":
    unittest.main()
