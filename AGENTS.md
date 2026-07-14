# Data Analysis Workspace v1

You are a data analysis assistant for this general-purpose workspace. The user directs the work; you handle the technical execution — fetching data, transforming it, modeling it, visualizing it, and writing it up.

This is a lean, general-purpose toolkit. Domain-specific recurring pipelines belong in dedicated projects rather than this workspace; see "Graduating a pipeline" below.

This `AGENTS.md` is the vendor-neutral, canonical instruction file for every AI assistant. Provider-specific files such as `CLAUDE.md`, `GEMINI.md`, `.github/copilot-instructions.md`, and `.cursor/rules/project.mdc` are compatibility adapters only. Do not duplicate project rules into those adapters.

## Environment

- **Python**: Run every script through `.\bin\python.ps1 <script.py>`. It resolves the machine-local venv at `%LOCALAPPDATA%\venvs\data-analysis-v1` and sets process-local PYTHONPATH/UTF-8. Never call system Python directly for project work.
- **New machine**: run `.\setup.ps1` once to build this machine's local venv.
- **Never hardcode absolute user or OneDrive paths.** Resolve from `Path(__file__).resolve().parents[N]` or `Path.cwd()`.
- **`.env` loading**: scripts prefer the repository-root `.env` and fall back to a shared `.env` one directory above the repository. Never rely on an implicit upward search.
- **Optional shared databases**: if available, `GTA.db` (Global Trade Atlas) and `LFS.db` (Labor Force Survey) live in `../database/`. Do not assume every teammate has access.

## New-machine setup

When the user asks you to install, configure, onboard, or make the repository fully functional:

1. Read `SETUP.md` completely before making changes.
2. Run `PowerShell -ExecutionPolicy Bypass -File .\setup.ps1` from the repository root.
3. Run `PowerShell -ExecutionPolicy Bypass -File .\bin\doctor.ps1` and explain each item that still needs user action.
4. Direct the user to the official or authorized source listed in `SETUP.md`; never invent a download source for a licensed file.
5. Never ask the user to paste API keys, passwords, tokens, font binaries, or licensed wheels into chat. Let the user enter secrets directly into their local `.env` and obtain licensed files through their organization.
6. After the user confirms that missing items are in place, rerun setup, the doctor, and the credential-free repository tests.

Core setup works without paid services. CEIC, S&P Global, FC Vision, and shared databases require separate organizational access. X-13 and several public APIs are available from official public sources. Treat `SETUP.md` as the source of truth for what is required by each feature.

## Session folder convention (mandatory)

**All output for a conversation goes into one folder: `session/YYYY-MM-DD-<short-slug>/`.** No exceptions, no `output/{chart,data,report,model_summary}` subfolders, no pipeline namespacing.

- At the start of a new task, create (or resume) `session/YYYY-MM-DD-<slug>/` before writing anything. Slug = 2-5 words, kebab-case, describing the task (e.g. `session/2026-07-14-thailand-gdp-nowcast/`).
- Everything for that conversation — inputs, working/temp scripts, fetched data, charts, model summaries, reports — goes flat inside that one folder. No further subfolder taxonomy.
- If a genuinely new task starts the same day, create a new dated folder (append a qualifier if the slug would collide, e.g. `-2`).
- When delegating to a sub-agent mid-conversation, pass the active session folder path explicitly in the task prompt — sub-agents don't share cwd/context automatically.
- Reports and their charts live in the *same* folder, so image references in a report are just `./chart_name.png` — no `../` depth-counting needed.

## Reusable roles

Reusable role playbooks live in `.agents/roles/`. Use them directly or delegate to an equivalent sub-agent when the active AI tool supports delegation:

| Agent | Role |
|---|---|
| `data-fetcher` | API retrieval via this project's `fetch-*` skills (CEIC, BOT, MOC, EIA, IMF, World Bank, S&P) |
| `data-transformer` | Cleaning, resampling, seasonal adjustment (via `x13-sa`), wide format |
| `econometrician` | ADF, ARIMA, ARDL, VAR, ECM, cointegration |
| `data-scientist` | XGBoost, MIDAS, DFM, nowcasting |
| `viz-expert` | Charts (clean defaults by default; NESDC brand template only on explicit request) |
| `report-writer` | Formal Markdown/HTML reports |
| `qualitative-analyst` | Web research, policy analysis, research briefs |
| `db-manager` | Ad-hoc SQLite files in a session folder, or the two shared reference DBs |

## Skills reference

- `fetch-ceic`, `fetch-bot`, `fetch-moc`, `fetch-eia`, `fetch-imf`, `fetch-worldbank`, `fetch-sp` — self-contained per-source data fetch skills. No persistent cache: always fetch live, write straight to the session folder.
- `md-to-html` — converts Markdown reports to single-file HTML with base64-embedded local assets; CDN-backed math, diagrams, and fonts require internet access.
- `apply-nesdc-viz-template` — applies the official NESDC brand palette/font/layout to a chart. **Opt-in only** — fires only when the user explicitly asks for NESDC/official styling.
- `x13-sa` — X-13ARIMA-SEATS seasonal adjustment via a locally installed `bin/x13as.exe`.

Canonical skills live under `.agents/skills/` and follow the open Agent Skills `SKILL.md` format. Read the relevant `SKILL.md` completely before invoking a skill.

## Visualization Rule

By default, charts use clean, sensible styling (e.g. seaborn `whitegrid`). Apply the NESDC brand template (`apply-nesdc-viz-template`) **only** when the user explicitly requests NESDC/official styling; this project is a general-purpose toolkit.

## Data Standards

- **Wide format mandatory**: Date as row index, variable names as columns. No long/stacked format in outputs.
- **Quarterly resampling**: Use `.resample('QE').mean()` (quarter-end alignment).
- **Schema check**: Before querying any `.db` file, run `PRAGMA table_info(<table>)` or `SELECT name FROM sqlite_master WHERE type='table'` first. Never guess table/column names.

## Report Formatting

- **Figure captions**: `**Figure N: Descriptive title**` immediately below each embedded image. Sequential numbering restarts in each report.
- **Table captions**: `**Table N: Descriptive title**` immediately above each table.
- **Source citations**: Place below the table as italic text — `*Source: Organisation, Year.*` — never as a row inside the table.
- **Chart paths in reports**: Charts and reports live in the same session folder — use a flat relative path, `./chart_name.png`.
- **No absolute paths in reports**.

## Localization

- **Default**: English, Gregorian years (YYYY).
- **Thai localization**: Only when the user explicitly requests it. Use locally licensed FC Vision files when available, Buddhist Era years (YYYY+543), and Thai labels via `apply-nesdc-viz-template`'s `scripts/thai_utils.py`.
- `TH Sarabun New` is legacy — do not use it.

## Graduating a pipeline

If work started in a session grows into a recurring pipeline (the same analysis rerun on a schedule with its own dependency chain), move it out of this general toolkit into a dedicated sibling project.

To graduate a pipeline: create a sibling folder, give it its own Git repository and distinctly named venv under `%LOCALAPPDATA%\venvs\`, copy the session scripts and required skills, and build its pipeline-specific structure there.
