"""Checks for the profile repository. Standard library only: python -m unittest discover -s tests"""
from __future__ import annotations

import datetime as dt
import json
import re
import sys
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import build_charts  # noqa: E402

README = (ROOT / "README.md").read_text()
SNAP = json.loads((ROOT / "data" / "readme-snapshot.json").read_text())


def fmt(n: int) -> str:
    return f"{n:,}"


class ChartBuild(unittest.TestCase):
    def setUp(self):
        self.outputs = build_charts.build()

    def test_deterministic(self):
        self.assertEqual(self.outputs, build_charts.build())

    def test_svgs_are_valid_and_accessible(self):
        for name, content in self.outputs.items():
            if name.startswith("__"):
                continue
            root = ET.fromstring(content)
            ns = "{http://www.w3.org/2000/svg}"
            self.assertEqual(root.tag, ns + "svg", name)
            self.assertEqual(root.get("role"), "img", name)
            self.assertIsNotNone(root.find(ns + "title"), name)
            self.assertIsNotNone(root.find(ns + "desc"), name)
            self.assertNotIn("<script", content, name)

    def test_committed_outputs_are_current(self):
        for name, content in self.outputs.items():
            path = ROOT / "data" / "summary.json" if name == "__summary__" else ROOT / "assets" / "generated" / name
            self.assertTrue(path.exists(), f"{path} missing: run scripts/build_charts.py")
            self.assertEqual(path.read_text(), content, f"{path} stale: run scripts/build_charts.py")


class DataIntegrity(unittest.TestCase):
    def test_calendar_is_contiguous_and_non_negative(self):
        days = json.loads((ROOT / "data" / "contributions.json").read_text())["days"]
        dates = [dt.date.fromisoformat(d["date"]) for d in days]
        self.assertEqual(dates, sorted(dates))
        self.assertTrue(all((b - a).days == 1 for a, b in zip(dates, dates[1:])))
        self.assertTrue(all(isinstance(d["count"], int) and d["count"] >= 0 for d in days))

    def test_repository_totals_add_up(self):
        repos = json.loads((ROOT / "data" / "repositories.json").read_text())
        self.assertEqual(repos["public"] + repos["private"], repos["total"])
        self.assertEqual(sum(repos["primary_language"].values()), repos["total"])
        self.assertEqual(sum(repos["categories"].values()), repos["total"])

    def test_snapshot_matches_data_when_dates_agree(self):
        summary = json.loads(build_charts.build()["__summary__"])
        if summary["collected_at"] != SNAP["snapshot"]:
            self.skipTest("calendar refreshed since the README snapshot; README figures are dated")
        for key in ("contributions_last_365_days", "contributions_by_year", "commits_attributed",
                    "repositories_with_commits", "best_day", "peak_month", "pull_requests", "repositories"):
            self.assertEqual(summary[key], SNAP[key], key)


class ReadmeConsistency(unittest.TestCase):
    def test_snapshot_figures_appear_in_readme(self):
        s = SNAP
        expected = [
            fmt(s["contributions_last_365_days"]),
            fmt(s["contributions_by_year"]["2026"]),
            f"vs {s['contributions_by_year']['2025']} in 2025",
            fmt(s["commits_attributed"]),
            f"across {s['repositories_with_commits']} repositories",
            f"**{s['best_day']['count']} / {s['peak_month']['count']}**",
            f"**{s['repositories']['total']}**",
            f"{s['repositories']['private']} private, {s['repositories']['public']} public",
            f"{s['pull_requests']['opened']} opened, {s['pull_requests']['merged']} merged",
        ]
        for needle in expected:
            self.assertIn(needle, README, needle)

    def test_local_asset_and_doc_links_resolve(self):
        refs = re.findall(r'(?:src|srcset|href)="([^"]+)"', README) + re.findall(r"\]\(([^)]+)\)", README)
        local = [r.split("#")[0] for r in refs if not re.match(r"^(https?:|mailto:|#)", r)]
        self.assertTrue(local)
        for ref in local:
            self.assertTrue((ROOT / ref).exists(), f"broken local reference: {ref}")

    def test_external_hosts_are_known(self):
        hosts = set(re.findall(r'https?://([^/"\s)]+)', README))
        allowed = {"www.whipp.studio", "www.linkedin.com", "raw.githubusercontent.com", "github.com"}
        self.assertLessEqual(hosts, allowed, hosts - allowed)

    def test_no_placeholder_or_inflated_language(self):
        lowered = README.lower()
        for phrase in ("lorem", "todo", "passionate", "superpower", "coffee", "ai enthusiast",
                       "building the future", "90%", "●●"):
            self.assertNotIn(phrase, lowered, phrase)

    def test_mermaid_blocks_are_closed(self):
        self.assertEqual(README.count("```mermaid"), len(re.findall(r"```mermaid\n.*?\n```", README, re.S)))

    def test_html_tags_balanced(self):
        for tag in ("details", "table", "picture", "p"):
            opened = len(re.findall(rf"<{tag}[\s>]", README))
            closed = README.count(f"</{tag}>")
            self.assertEqual(opened, closed, tag)


if __name__ == "__main__":
    unittest.main()
