# Profile evidence

How each claim in the profile README is supported. Audit date: **18 October 2026**.

Private repositories were read through the owner's authenticated GitHub session. This public file records *what kind* of evidence exists and how strong it is; it deliberately omits private repository names, code, client names and business details.

## Evidence levels

| Level | Meaning |
| :-- | :-- |
| **Verified** | Read directly from GitHub data or source code during the audit |
| **Documented** | Stated in a repository's own README or docs; not independently executed |
| **Stated** | From the owner's profile or account of their work; no repository evidence |
| **Excluded** | Previously claimed on the profile but not supported; removed |

## Metrics

| Claim | Value | Level | Source and method |
| :-- | --: | :-- | :-- |
| Contributions, last 365 days | 1,025 | Verified | GitHub contribution calendar (`/users/mirshadab/contributions`); matches the profile's own headline |
| Contributions by year | 2024: 1 · 2025: 71 · 2026: 994 | Verified | Same calendar, per calendar year; `data/contributions.json` |
| Account created | 13 Dec 2024 | Verified | REST `GET /users/mirshadab` |
| Commits attributed | 988 in 26 repositories | Verified | Profile activity ("Created N commits in M repositories"), Jun 2025 – Oct 2026; `data/workstreams.json` |
| Busiest day | 86 on 5 Jul 2026 | Verified | Calendar |
| Busiest month | 318 in Sep 2026 | Verified | Calendar |
| Longest active streak | 10 days | Verified | Calendar, consecutive non-zero days |
| Pull requests | 4 opened, 1 merged | Verified | Authenticated PR search `is:pr author:mirshadab` |
| Repositories | 72 (58 private, 14 public, 3 forks) | Verified | Owner repository list |
| Primary languages | TypeScript 50, Vue 5, Astro 3, Python 3, JS 1, HTML 1, none 9 | Verified | GitHub linguist, per repository |
| Repository categories | 41 / 18 / 8 / 3 / 1 / 1 | Verified (classification is a judgement) | Manual classification of names and stacks |
| Deployed industry builds | 29 | Verified | Vercel deployments linked from the previous profile README; Vite + React + Motion repositories |

Derived values are recomputed by `scripts/build_charts.py` into `data/summary.json`; `tests/test_profile.py` fails if the README's snapshot figures drift from the snapshot data.

## Systems

| README claim | Level | Basis |
| :-- | :-- | :-- |
| Demand engine: 44 collectors, 345 demand + 39 revenue sources catalogued, ~530 platforms | Documented | Repository README and config files |
| Demand engine: 265 tests | Documented | Repository README; tests not executed in this audit (~50 test modules present) |
| Demand engine: PII scrub, robots-aware HTTP, Parquet + DuckDB, daily Actions → R2 | Verified | Source files and workflow present |
| Demand engine: rule-based taxonomy, specificity-weighted niche phrases, exact-fingerprint dedupe, MinHash planned | Verified | Module docstrings |
| Idea Lab: Claude structured outputs, evidence-ID citations, schema validation, stubbable client, 400-item / 8-match caps | Verified | Server-side Claude client and evaluation schema |
| Operations SaaS: Turborepo, Hono on Workers, three Nuxt apps + Astro, Drizzle | Verified | Workspace layout and package manifests |
| Operations SaaS: 82 migration files, 82 test files | Verified | File counts |
| Operations SaaS: OpenAI-compatible provider, NIM in dev, Zod re-validation, review gate, deterministic CSV path | Verified | `ai` package source and comments |
| Financial state machine: RLS, atomic SQL functions, 52 migrations, privilege audit, payments not enabled | Documented + verified | README status table; migration count and scripts verified |
| Retrieval-first sites: content collections, JSON-LD builders, `llms.txt`, query-cluster research, GSC table, payment gateways | Verified | Source, migrations and research files across four repositories |
| Marketplace: Next.js 16, Prisma 7, Better Auth with Reddit/X linking, 23 migrations, Vitest | Verified | README and manifests |
| Genkit + Gemini prototypes | Verified | Dependencies and flow files |
| Studied forks (swarm engine, AI assistant) | Verified | Fork metadata; zero commits by the owner |

## Roles

| Claim | Level |
| :-- | :-- |
| Co-founder and delivery lead, Whipp Studio (2025 –) | Stated (profile bio, studio website) |
| Independent full-stack engineer (2025 –) | Verified as engineering activity; client relationships not verified |
| Data and AI systems R&D (2026 –) | Verified |
| Freelance full-stack engineer via Upwork and Whipp Studio, 2021 – 2024 | Stated by the owner; code history on a previous GitHub account, not recoverable from this account |

## Excluded or downgraded

| Previous claim | Decision | Reason |
| :-- | :-- | :-- |
| RAG pipelines, pgvector, embeddings, re-ranking | Moved to *researching* | No embedding or vector-search code in audited repositories |
| Whisper speech pipelines, WhatsApp/Twilio agents | Removed | No repository evidence |
| Custom MCP servers | Moved to *researching* | No MCP server code found; Claude Code skills are present |
| Swarm-intelligence forecasting as own research | Downgraded to *exploring* | Only a fork exists, with no commits by the owner |
| ML lead / prospect scoring model | Removed | No model code found; demand engine scoring is a later phase |
| "Evaluation process run on every change" | Removed | Schema and citation checks exist; no eval sets or metrics |
| Five-dot proficiency ratings | Removed | Not evidence-based |
| "~90% of my week touches AI" | Removed | Unsupported number |
| "29+ production sites for clients" | Reworded | Evidence shows studio industry builds, not individual client engagements |
| Third-party stats card showing commits/PRs | Removed | Public instance cannot see private repositories (showed ~52), contradicting the calendar |

## Gaps the owner can close

1. Verifiable detail for 2021 – 2024 (Upwork profile link, project types, outcomes).
2. Any repository (current or recovered) containing RAG, embeddings, MCP servers or speech work.
3. Measured results for R2 and R3 (see README research programme).
