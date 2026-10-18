#!/usr/bin/env python3
"""Refresh data/contributions.json from GitHub's GraphQL contribution calendar.

Scope: the same daily counts GitHub draws on the profile. Private contributions are
included only as counts, and only when the account shares them ("Include private
contributions on my profile"). No repository names or contents are fetched.

Usage:
    GITHUB_TOKEN=... python scripts/fetch_contributions.py [--user mirshadab]

Exit codes: 0 = written (or unchanged), 2 = no token, 3 = API/network failure.
On failure the existing snapshot is left untouched so chart generation still works.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "contributions.json"
API = "https://api.github.com/graphql"

QUERY = """
query($login: String!, $from: DateTime!, $to: DateTime!) {
  user(login: $login) {
    createdAt
    contributionsCollection(from: $from, to: $to) {
      contributionCalendar {
        totalContributions
        weeks { contributionDays { date contributionCount } }
      }
    }
  }
}
"""


def graphql(token: str, variables: dict, retries: int = 3) -> dict:
    body = json.dumps({"query": QUERY, "variables": variables}).encode()
    last: Exception | None = None
    for attempt in range(retries):
        req = urllib.request.Request(
            API,
            data=body,
            headers={
                "Authorization": f"bearer {token}",
                "Content-Type": "application/json",
                "User-Agent": "mirshadab-profile-metrics",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                payload = json.load(resp)
            if payload.get("errors"):
                raise RuntimeError(payload["errors"][0].get("message", "GraphQL error"))
            return payload["data"]
        except (urllib.error.URLError, RuntimeError, TimeoutError) as exc:  # retry transient failures
            last = exc
            time.sleep(2 ** attempt)
    raise RuntimeError(f"GitHub GraphQL failed after {retries} attempts: {last}")


def year_windows(start: dt.date, end: dt.date):
    """GraphQL limits a contributionsCollection to one year; walk calendar years."""
    year = start.year
    while year <= end.year:
        lo = max(start, dt.date(year, 1, 1))
        hi = min(end, dt.date(year, 12, 31))
        yield lo, hi
        year += 1


def fetch(login: str, token: str, today: dt.date) -> dict:
    probe = graphql(token, {"login": login, "from": f"{today.isoformat()}T00:00:00Z", "to": f"{today.isoformat()}T23:59:59Z"})
    if not probe.get("user"):
        raise RuntimeError(f"user {login!r} not found")
    created = dt.date.fromisoformat(probe["user"]["createdAt"][:10])
    # Show whole calendar years so the heatmap starts on 1 January.
    start = dt.date(created.year, 1, 1)
    counts: dict[str, int] = {}
    for lo, hi in year_windows(start, today):
        data = graphql(token, {"login": login, "from": f"{lo}T00:00:00Z", "to": f"{hi}T23:59:59Z"})
        cal = data["user"]["contributionsCollection"]["contributionCalendar"]
        for week in cal["weeks"]:
            for day in week["contributionDays"]:
                d = day["date"]
                if lo.isoformat() <= d <= hi.isoformat():
                    counts[d] = day["contributionCount"]
    days = []
    d = start
    while d <= today:
        days.append({"date": d.isoformat(), "count": counts.get(d.isoformat(), 0)})
        d += dt.timedelta(days=1)
    return {
        "source": f"GitHub GraphQL contributionCalendar for @{login}; private contributions included as counts when shared on the profile",
        "collected_at": today.isoformat(),
        "method": "scripts/fetch_contributions.py",
        "account_created": created.isoformat(),
        "days": days,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--user", default=os.environ.get("PROFILE_USER", "mirshadab"))
    args = ap.parse_args()
    token = os.environ.get("PROFILE_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if not token:
        print("::warning::no PROFILE_TOKEN or GITHUB_TOKEN; keeping existing snapshot", file=sys.stderr)
        return 2
    try:
        data = fetch(args.user, token, dt.datetime.now(dt.timezone.utc).date())
    except Exception as exc:  # noqa: BLE001 - report and keep the old snapshot
        print(f"::warning::contribution fetch failed, keeping existing snapshot: {exc}", file=sys.stderr)
        return 3
    if OUT.exists():
        old = json.loads(OUT.read_text())
        if old.get("days") == data["days"]:
            print("contributions unchanged")
            return 0
        old_total = sum(d["count"] for d in old.get("days", []))
        new_total = sum(d["count"] for d in data["days"])
        if new_total < old_total * 0.8:
            # A sharp drop usually means the token cannot see private counts. Do not overwrite good data.
            print(f"::warning::new total {new_total} is far below snapshot {old_total}; not overwriting. "
                  "Check that 'Include private contributions' is on, or set PROFILE_TOKEN.", file=sys.stderr)
            return 3
    OUT.write_text(json.dumps(data, indent=0) + "\n")
    print(f"wrote {OUT.relative_to(ROOT)}: {len(data['days'])} days, {sum(d['count'] for d in data['days'])} contributions")
    return 0


if __name__ == "__main__":
    sys.exit(main())
