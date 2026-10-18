#!/usr/bin/env python3
"""Render the profile's charts from the JSON snapshots in data/.

Inputs (all version-controlled):
    data/contributions.json   daily contribution counts (GitHub calendar)
    data/workstreams.json     monthly commits per workstream category
    data/repositories.json    repository totals and primary languages

Outputs:
    assets/generated/*.svg    static, script-free SVGs for the README
    data/summary.json         derived metrics quoted in the README

Pure standard library and deterministic: the same inputs always produce byte-identical
outputs, so the workflow commits only when the data actually changed.
"""
from __future__ import annotations

import calendar
import datetime as dt
import json
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
OUT = ROOT / "assets" / "generated"

BG, PANEL, BORDER = "#0D1117", "#161B22", "#30363D"
TEXT, MUTED, FAINT = "#E6EDF3", "#8B949E", "#6E7681"
GREEN = ["#161B22", "#0E4429", "#006D32", "#26A641", "#39D353"]
ACCENT, AI, BLUE, AMBER = "#2EA043", "#A371F7", "#58A6FF", "#D29922"
FONT = "-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif"
MONO = "ui-monospace,SFMono-Regular,Menlo,Consolas,monospace"


# --------------------------------------------------------------------------- helpers
def load(name: str) -> dict:
    return json.loads((DATA / name).read_text())


def svg(width: int, height: int, title: str, desc: str, body: list[str]) -> str:
    return "\n".join(
        [
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
            f'viewBox="0 0 {width} {height}" role="img" aria-labelledby="t d">',
            f'<title id="t">{escape(title)}</title><desc id="d">{escape(desc)}</desc>',
            f'<rect width="{width}" height="{height}" rx="12" fill="{BG}" stroke="{BORDER}"/>',
            *body,
            "</svg>",
            "",
        ]
    )


def text(x, y, s, size=12, fill=TEXT, anchor="start", weight=400, family=FONT) -> str:
    return (f'<text x="{x}" y="{y}" font-family="{family}" font-size="{size}" fill="{fill}" '
            f'text-anchor="{anchor}" font-weight="{weight}">{escape(str(s))}</text>')


def level(count: int, q: list[int]) -> int:
    if count <= 0:
        return 0
    for i, edge in enumerate(q, start=1):
        if count <= edge:
            return i
    return 4


def quartiles(values: list[int]) -> list[int]:
    nz = sorted(v for v in values if v > 0)
    if not nz:
        return [1, 2, 3]
    pick = lambda p: nz[min(len(nz) - 1, int(p * (len(nz) - 1)))]  # noqa: E731
    return [pick(0.25), pick(0.5), pick(0.75)]


def nice_ceiling(vmax: float, ticks: int = 4) -> int:
    """Smallest 'round' axis maximum (1, 2, 2.5 or 5 x 10^n per tick) that fits vmax."""
    vmax = max(vmax, 1)
    raw = vmax / ticks
    mag = 10 ** (len(str(int(raw))) - 1)
    for m in (1, 2, 2.5, 5, 10):
        step = m * mag
        if step * ticks >= vmax:
            return int(step * ticks)
    return int(10 * mag * ticks)


def month_key(d: str) -> str:
    return d[:7]


def month_label(key: str, with_year: bool) -> str:
    y, m = key.split("-")
    return f"{calendar.month_abbr[int(m)]} {y[2:]}" if with_year else calendar.month_abbr[int(m)]


# --------------------------------------------------------------------------- metrics
def summarise(days: list[dict], repos: dict, ws: dict, collected: str, created: str) -> dict:
    by_year: dict[str, int] = {}
    by_month: dict[str, int] = {}
    for d in days:
        by_year[d["date"][:4]] = by_year.get(d["date"][:4], 0) + d["count"]
        by_month[month_key(d["date"])] = by_month.get(month_key(d["date"]), 0) + d["count"]
    end = dt.date.fromisoformat(collected)
    start_12 = end - dt.timedelta(days=364)
    last12 = sum(d["count"] for d in days if dt.date.fromisoformat(d["date"]) >= start_12)
    active = [d for d in days if d["count"] > 0]
    best = max(days, key=lambda d: (d["count"], d["date"]))
    # longest run of consecutive active days
    run = longest = 0
    for d in days:
        run = run + 1 if d["count"] > 0 else 0
        longest = max(longest, run)
    peak_month = max(by_month.items(), key=lambda kv: (kv[1], kv[0]))
    commits = sum(sum(v.values()) for v in ws["months"].values())
    return {
        "collected_at": collected,
        "account_created": created,
        "total_contributions": sum(d["count"] for d in days),
        "contributions_last_365_days": last12,
        "contributions_by_year": by_year,
        "active_days_total": len(active),
        "active_days_last_365": sum(1 for d in active if dt.date.fromisoformat(d["date"]) >= start_12),
        "best_day": {"date": best["date"], "count": best["count"]},
        "longest_active_streak_days": longest,
        "peak_month": {"month": peak_month[0], "count": peak_month[1]},
        "commits_attributed": commits,
        "repositories_with_commits": ws["repositories_with_commits"],
        "pull_requests": ws["pull_requests"],
        "repositories": {k: repos[k] for k in ("total", "public", "private", "forks")},
    }


# --------------------------------------------------------------------------- charts
def heatmap(days: list[dict], summary: dict) -> str:
    cell, gap = 11, 3
    step = cell + gap
    left, top = 64, 46
    # Years with almost no activity (the account was created in mid-December) are summarised
    # in the footer instead of drawing an empty grid.
    all_years = sorted({d["date"][:4] for d in days})
    years = [y for y in all_years if summary["contributions_by_year"].get(y, 0) >= 10] or all_years[-1:]
    skipped = [y for y in all_years if y not in years]
    q = quartiles([d["count"] for d in days])
    lookup = {d["date"]: d["count"] for d in days}
    collected = dt.date.fromisoformat(summary["collected_at"])
    row_h = 7 * step + 30
    width = left + 53 * step + 24
    height = top + len(years) * row_h + 34
    body = [text(24, 28, "Contribution heatmap", 15, TEXT, weight=600),
            text(width - 24, 28, f"{summary['total_contributions']:,} contributions since {summary['account_created'][:7]}", 12, MUTED, "end")]
    for yi, year in enumerate(years):
        y0 = top + yi * row_h
        first = dt.date(int(year), 1, 1)
        offset = (first.weekday() + 1) % 7  # Sunday-first rows, like GitHub
        body.append(text(24, y0 + 3 * step + 9, year, 12, MUTED, weight=600, family=MONO))
        body.append(text(24, y0 + 3 * step + 23, f"{summary['contributions_by_year'].get(year, 0):,}", 11, FAINT, family=MONO))
        d = first
        while d.year == int(year):
            idx = (d - first).days + offset
            col, row = divmod(idx, 7)
            x, y = left + col * step, y0 + row * step
            future = d > collected
            c = lookup.get(d.isoformat(), 0)
            fill = "none" if future else GREEN[level(c, q)]
            stroke = f' stroke="{PANEL}"' if future else ""
            body.append(f'<rect x="{x}" y="{y}" width="{cell}" height="{cell}" rx="2" fill="{fill}"{stroke}/>')
            d += dt.timedelta(days=1)
        for m in range(1, 13):
            md = dt.date(int(year), m, 1)
            col = ((md - first).days + offset) // 7
            body.append(text(left + col * step, y0 - 6, calendar.month_abbr[m], 10, FAINT))
    ly = height - 16
    body.append(text(width - 196, ly + 9, "Less", 10, FAINT))
    for i, colr in enumerate(GREEN):
        body.append(f'<rect x="{width - 166 + i * step}" y="{ly}" width="{cell}" height="{cell}" rx="2" fill="{colr}"/>')
    body.append(text(width - 92, ly + 9, "More", 10, FAINT))
    note = "".join(f" · {y}: {summary['contributions_by_year'].get(y, 0)}" for y in skipped)
    body.append(text(24, ly + 9, f"Source: GitHub contribution calendar · snapshot {summary['collected_at']}{note}", 10, FAINT))
    return svg(width, height, "Contribution heatmap",
               f"Daily GitHub contributions for {', '.join(years)}; {summary['total_contributions']} in total.", body)


def monthly(days: list[dict], summary: dict) -> str:
    by_month: dict[str, int] = {}
    for d in days:
        if d["date"] >= summary["account_created"][:7]:
            by_month[month_key(d["date"])] = by_month.get(month_key(d["date"]), 0) + d["count"]
    keys = sorted(by_month)
    width, height = 900, 300
    left, right, top, bottom = 56, 24, 52, 52
    plot_w, plot_h = width - left - right, height - top - bottom
    vmax = max(by_month.values()) or 1
    ceiling = nice_ceiling(vmax)
    bw = plot_w / len(keys)
    body = [text(24, 30, "Contributions per month", 15, TEXT, weight=600),
            text(width - 24, 30, f"peak {month_label(summary['peak_month']['month'], True)}: {summary['peak_month']['count']}", 12, MUTED, "end")]
    for i in range(0, 5):
        v = ceiling * i / 4
        y = top + plot_h - plot_h * v / ceiling
        body.append(f'<line x1="{left}" y1="{y:.1f}" x2="{width - right}" y2="{y:.1f}" stroke="{PANEL}"/>')
        body.append(text(left - 8, y + 4, int(v), 10, FAINT, "end", family=MONO))
    for i, k in enumerate(keys):
        v = by_month[k]
        h = plot_h * v / ceiling
        x = left + i * bw + bw * 0.18
        y = top + plot_h - h
        colr = ACCENT if v >= vmax * 0.5 else "#238636" if v > 0 else PANEL
        body.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{bw * 0.64:.1f}" height="{max(h, 1):.1f}" rx="3" fill="{colr}"/>')
        if v >= vmax * 0.15:
            body.append(text(x + bw * 0.32, y - 6, v, 10, MUTED, "middle", family=MONO))
        show_year = i == 0 or k.endswith("-01")
        body.append(text(x + bw * 0.32, height - bottom + 16, month_label(k, False), 10, FAINT, "middle"))
        if show_year:
            body.append(text(x + bw * 0.32, height - bottom + 30, k[:4], 10, MUTED, "middle", family=MONO))
    body.append(text(24, height - 10, "Source: GitHub contribution calendar (commits, PRs, issues, reviews and repository creation).", 10, FAINT))
    return svg(width, height, "Contributions per month",
               "Monthly GitHub contributions since the account was created. " +
               "; ".join(f"{month_label(k, True)}: {by_month[k]}" for k in keys), body)


def workstreams(ws: dict) -> str:
    cats = ws["categories"]
    colours = {"platform": ACCENT, "data_ai": AI, "collab": BLUE, "studio": AMBER, "tooling": FAINT}
    months = sorted(ws["months"])
    first = dt.date.fromisoformat(months[0] + "-01")
    last = dt.date.fromisoformat(months[-1] + "-01")
    keys = []
    d = first
    while d <= last:
        keys.append(d.strftime("%Y-%m"))
        d = (d.replace(day=28) + dt.timedelta(days=4)).replace(day=1)
    width, height = 900, 330
    left, right, top, bottom = 56, 24, 76, 52
    plot_w, plot_h = width - left - right, height - top - bottom
    totals = {k: sum(ws["months"].get(k, {}).values()) for k in keys}
    ceiling = nice_ceiling(max(totals.values()))
    bw = plot_w / len(keys)
    body = [text(24, 30, "Where the commits went", 15, TEXT, weight=600),
            text(width - 24, 30, f"{sum(totals.values()):,} commits · {ws['repositories_with_commits']} repositories", 12, MUTED, "end")]
    lx = 24
    for key, label in cats.items():
        body.append(f'<rect x="{lx}" y="46" width="10" height="10" rx="2" fill="{colours[key]}"/>')
        body.append(text(lx + 16, 55, label, 11, MUTED))
        lx += 30 + int(len(label) * 5.9)
    for i in range(0, 5):
        v = ceiling * i / 4
        y = top + plot_h - plot_h * v / ceiling
        body.append(f'<line x1="{left}" y1="{y:.1f}" x2="{width - right}" y2="{y:.1f}" stroke="{PANEL}"/>')
        body.append(text(left - 8, y + 4, int(v), 10, FAINT, "end", family=MONO))
    for i, k in enumerate(keys):
        x = left + i * bw + bw * 0.18
        y = top + plot_h
        for cat in cats:
            v = ws["months"].get(k, {}).get(cat, 0)
            if not v:
                continue
            h = plot_h * v / ceiling
            y -= h
            body.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{bw * 0.64:.1f}" height="{max(h, 1):.1f}" fill="{colours[cat]}"/>')
        body.append(text(x + bw * 0.32, height - bottom + 16, month_label(k, False), 10, FAINT, "middle"))
        if i == 0 or k.endswith("-01"):
            body.append(text(x + bw * 0.32, height - bottom + 30, k[:4], 10, MUTED, "middle", family=MONO))
    body.append(text(24, height - 10, "Source: GitHub profile activity, commits per repository per month, grouped by workstream. Repository names withheld.", 10, FAINT))
    return svg(width, height, "Commits by workstream",
               "Monthly commits grouped into workstreams. " +
               "; ".join(f"{month_label(k, True)}: " + ", ".join(f"{cats[c]} {n}" for c, n in ws["months"].get(k, {}).items()) for k in keys if totals[k]),
               body)


def weekdays(days: list[dict]) -> str:
    names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    tot = [0] * 7
    act = [0] * 7
    for d in days:
        wd = dt.date.fromisoformat(d["date"]).weekday()
        tot[wd] += d["count"]
        act[wd] += d["count"] > 0
    width, height = 440, 260
    left, top, plot_h = 24, 56, 140
    vmax = max(tot) or 1
    bw = (width - 48) / 7
    body = [text(24, 30, "Contributions by weekday", 15, TEXT, weight=600)]
    for i, n in enumerate(names):
        h = plot_h * tot[i] / vmax
        x = left + i * bw + bw * 0.15
        y = top + plot_h - h
        colr = ACCENT if tot[i] == vmax else "#238636"
        body.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{bw * 0.7:.1f}" height="{max(h, 1):.1f}" rx="3" fill="{colr}"/>')
        body.append(text(x + bw * 0.35, y - 6, tot[i], 10, MUTED, "middle", family=MONO))
        body.append(text(x + bw * 0.35, top + plot_h + 16, n, 11, MUTED, "middle"))
        body.append(text(x + bw * 0.35, top + plot_h + 30, f"{act[i]}d", 10, FAINT, "middle", family=MONO))
    body.append(text(24, height - 12, "Totals per weekday; 'd' = active days. Calendar dates only, no hour data.", 10, FAINT))
    return svg(width, height, "Contributions by weekday",
               "; ".join(f"{names[i]}: {tot[i]} contributions on {act[i]} active days" for i in range(7)), body)


def cumulative(days: list[dict], summary: dict) -> str:
    pts = [d for d in days if d["date"] >= summary["account_created"]]
    width, height = 440, 260
    left, right, top, bottom = 48, 20, 52, 48
    pw, ph = width - left - right, height - top - bottom
    total = 0
    series = []
    for d in pts:
        total += d["count"]
        series.append(total)
    vmax = series[-1] or 1
    n = len(series) - 1 or 1
    path = " ".join(f"{'M' if i == 0 else 'L'}{left + pw * i / n:.1f},{top + ph - ph * v / vmax:.1f}" for i, v in enumerate(series))
    area = path + f" L{left + pw:.1f},{top + ph:.1f} L{left:.1f},{top + ph:.1f} Z"
    body = [text(24, 30, "Cumulative contributions", 15, TEXT, weight=600),
            f'<path d="{area}" fill="{ACCENT}" fill-opacity="0.12"/>',
            f'<path d="{path}" fill="none" stroke="{ACCENT}" stroke-width="2"/>',
            text(width - right, top - 8, f"{vmax:,}", 12, TEXT, "end", 600, MONO),
            text(left, height - bottom + 16, pts[0]["date"][:7], 10, FAINT, family=MONO),
            text(width - right, height - bottom + 16, pts[-1]["date"][:7], 10, FAINT, "end", family=MONO),
            text(24, height - 12, f"Running total since the account was created ({summary['account_created']}).", 10, FAINT)]
    return svg(width, height, "Cumulative contributions",
               f"Running total of contributions from {pts[0]['date']} to {pts[-1]['date']}, ending at {vmax}.", body)


def languages(repos: dict) -> str:
    langs = sorted(repos["primary_language"].items(), key=lambda kv: (-kv[1], kv[0]))
    width = 440
    row = 24
    top = 56
    height = top + row * len(langs) + 36
    vmax = max(v for _, v in langs) or 1
    colours = {"TypeScript": "#3178C6", "Vue": "#41B883", "Astro": "#FF5D01", "Python": "#3776AB",
               "JavaScript": "#F1E05A", "HTML": "#E34C26"}
    body = [text(24, 30, "Repositories by primary language", 15, TEXT, weight=600),
            text(width - 24, 30, f"{repos['total']} repos", 12, MUTED, "end")]
    for i, (name, v) in enumerate(langs):
        y = top + i * row
        w = (width - 190) * v / vmax
        body.append(text(24, y + 12, name, 11, MUTED))
        body.append(f'<rect x="124" y="{y + 2}" width="{max(w, 2):.1f}" height="12" rx="3" fill="{colours.get(name, FAINT)}"/>')
        body.append(text(130 + w, y + 12, v, 11, TEXT, family=MONO))
    body.append(text(24, height - 12, "Primary language as detected by GitHub (linguist).", 10, FAINT))
    return svg(width, height, "Repositories by primary language",
               "; ".join(f"{n}: {v}" for n, v in langs), body)


# --------------------------------------------------------------------------- main
def build() -> dict[str, str]:
    contrib = load("contributions.json")
    ws = load("workstreams.json")
    repos = load("repositories.json")
    days = contrib["days"]
    summary = summarise(days, repos, ws, contrib["collected_at"], contrib["account_created"])
    return {
        "heatmap.svg": heatmap(days, summary),
        "monthly.svg": monthly(days, summary),
        "workstreams.svg": workstreams(ws),
        "weekday.svg": weekdays(days),
        "cumulative.svg": cumulative(days, summary),
        "languages.svg": languages(repos),
        "__summary__": json.dumps(summary, indent=1, sort_keys=True) + "\n",
    }


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for name, content in build().items():
        target = DATA / "summary.json" if name == "__summary__" else OUT / name
        if not target.exists() or target.read_text() != content:
            target.write_text(content)
            print(f"updated {target.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
