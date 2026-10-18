# Setup and maintenance

## Repository layout

```
README.md                         the profile
assets/hero.svg                   static header
assets/generated/*.svg            charts, rendered by scripts/build_charts.py
data/contributions.json           daily contribution counts (refreshed by the workflow)
data/workstreams.json             monthly commits by workstream (manual snapshot)
data/repositories.json            repository totals, languages, categories (manual snapshot)
data/summary.json                 derived metrics (generated)
data/readme-snapshot.json         the figures quoted in README text (manual, tested)
scripts/fetch_contributions.py    GitHub GraphQL → data/contributions.json
scripts/build_charts.py           data → SVG charts + summary.json (stdlib only)
tests/test_profile.py             determinism, SVG validity, README consistency, asset paths
.github/workflows/profile-data.yml  daily fetch → render → test → commit if changed
.github/workflows/snake.yml       contribution snake → `output` branch
docs/profile-evidence.md          sources for every claim
```

## First run

1. Commit everything in this folder to `mirshadab/mirshadab` on `main`. Replace the old `.github/workflows/snake.yml`.
2. Make sure **Settings → Public profile → Contributions & activity → Include private contributions on my profile** is on. Without it every chart would show public activity only.
3. Actions tab → **Profile data** → *Run workflow*. Check the log line `wrote data/contributions.json: … contributions`. The total should match the number above your contribution graph.
4. Actions tab → **Contribution snake** → *Run workflow*. It writes `snake.svg`, `snake-dark.svg` and the old `github-contribution-grid-snake.svg` to the `output` branch.
5. Repository **Settings → Actions → General → Workflow permissions** must allow *Read and write* (both workflows push).

## Secrets

| Secret | Required? | Minimum scope | Why |
| :-- | :-- | :-- | :-- |
| `GITHUB_TOKEN` | automatic | — | Used by default for the GraphQL calendar query and for pushes |
| `PROFILE_TOKEN` | only if step 3's total comes out low | classic PAT with `read:user` only | Some accounts only expose private contribution *counts* to an authenticated user token |

To add `PROFILE_TOKEN`: GitHub → Settings → Developer settings → Personal access tokens (classic) → scope `read:user`, 90-day expiry → copy → this repository → Settings → Secrets and variables → Actions → *New repository secret*. Never paste a token into an issue, commit or chat. The fetch script refuses to overwrite the snapshot if a new total falls more than 20% below the old one, which is the usual symptom of a token that cannot see private counts.

## Local commands

```bash
python scripts/build_charts.py             # re-render charts from data/
python -m unittest discover -s tests -v    # run the checks
GITHUB_TOKEN=… python scripts/fetch_contributions.py   # refresh the calendar locally
```

## Updating the manual snapshots

`data/workstreams.json` and `data/repositories.json` contain category totals that require reading private repository names, which this public workflow deliberately does not do. Refresh them by hand every few months, then update `data/readme-snapshot.json` and the matching figures in the README together — the tests fail if the two disagree.

## Troubleshooting

| Symptom | Likely cause | Fix |
| :-- | :-- | :-- |
| Fetch step shows a warning, charts unchanged | API error or rate limit | Nothing; the last good snapshot is kept. Re-run later |
| "new total … far below snapshot" | Token cannot see private counts | Turn on private contributions on the profile, or add `PROFILE_TOKEN` |
| Snake image broken | `output` branch missing | Run *Contribution snake* once |
| Push rejected in a workflow | Workflow permissions are read-only | Step 5 above |
| Mermaid diagram shows an error box | Syntax not supported by GitHub's Mermaid version | Preview the README on GitHub before committing changes to diagrams |

## Recovering historical contributions

GitHub attributes a commit to an account by the commit's author email. If you still have repositories from the old account — local clones, server copies, archives, client remotes — you can bring that history back **without rewriting anything**:

1. Find the email used in the old commits: `git log --format='%ae' | sort -u` inside an old clone.
2. Add that address under **Settings → Emails** on this account and verify it.
3. Push the repository, unchanged, to this account (a new private repository is fine). Commits keep their original dates and appear on the contribution graph once they are on the default branch.

For the old account itself, use GitHub's account-recovery flow (recovery codes, a verified device, or a verified email). Do **not** recreate history with backdated or empty commits — it is visible on inspection and undermines everything else on the profile.
