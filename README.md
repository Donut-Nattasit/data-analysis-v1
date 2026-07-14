# data-analysis_v1

A Windows-first, session-organized toolkit for economic data analysis with major
AI coding assistants. It includes reusable, open-format skills for data retrieval,
transformation, seasonal adjustment, visualization, econometrics, machine learning,
and report export.

This edition is prepared for a private team GitHub repository. It contains no API
keys, fetched data, local virtual environment, proprietary Python wheel, X-13
executable, or commercial font files.

## Easiest setup: ask your AI assistant

Open this cloned folder in your AI coding tool and send this prompt:

> Read `AGENTS.md` and `SETUP.md` completely. Set up this repository for me,
> run the setup doctor, and guide me through any items that require my own account
> or licensed files. Never ask me to paste a secret into chat.

The repository provides native guidance for OpenAI Codex, Claude Code, Gemini CLI,
GitHub Copilot, and Cursor. Other repository-aware assistants should read
`AGENTS.md` directly.

## Requirements

- Windows PowerShell 5.1 or PowerShell 7
- Python 3.12 available through `py -3.12`, `python3.12`, or `python`
- Git

## Quick start

```powershell
git clone <repository-url>
cd data-analysis_v1
PowerShell -ExecutionPolicy Bypass -File .\setup.ps1
PowerShell -ExecutionPolicy Bypass -File .\bin\doctor.ps1
.\bin\python.ps1 --version
```

`setup.ps1` creates a machine-local virtual environment at
`%LOCALAPPDATA%\venvs\data-analysis-v1`, outside the repository, and installs the
public dependencies in `requirements.txt`. If `.env` does not exist, it also copies
the safe placeholder template. It does not change the user's global `PYTHONPATH` or
delete an existing in-repository environment.

Fetch scripts prefer `.env` in the repository root. For compatibility with related
internal projects, they also check for `.env` one directory above the repository.
Real credential files are ignored by Git.

See `SETUP.md` for the feature-by-feature checklist, official registration links,
authorized sources for licensed files, and safe secret-handling instructions.

## Optional licensed components

The core environment works without these components:

| Feature | Local file | Setup |
| --- | --- | --- |
| CEIC retrieval | `wheels/ceic_api_client-2.11.5.396-py3-none-any.whl` | Obtain through your organization's authorized CEIC contact, place it in `wheels/`, then rerun `setup.ps1` |
| X-13 seasonal adjustment | `bin/x13as.exe` | Download the current Windows ASCII build from the [U.S. Census Bureau](https://www.census.gov/data/software/x13as.X-13ARIMA-SEATS.html), then copy or rename its executable to `bin/x13as.exe` |
| FC Vision typography | `.agents/skills/apply-nesdc-viz-template/assets/fonts/FCVision/*.otf` | Each authorized user supplies their own licensed font files |

These files are intentionally excluded from Git. See `THIRD_PARTY_NOTICES.md`.

## Repository layout

- `session/YYYY-MM-DD-<slug>/` — task inputs, scripts, data, charts, and reports.
  Session contents are local and ignored by Git.
- `.agents/skills/` — canonical task playbooks and their scripts.
- `.agents/roles/` — vendor-neutral specialist role playbooks.
- `AGENTS.md` — canonical instructions for every AI assistant.
- `CLAUDE.md`, `GEMINI.md`, `.github/copilot-instructions.md`, `.cursor/rules/` — small compatibility adapters.
- `bin/python.ps1` — the project-aware Python launcher.
- `bin/doctor.ps1` — safe readiness report that never prints secret values.
- `setup.ps1` — reproducible Windows environment setup.
- `tests/` — fast, credential-free repository checks.

See `AGENTS.md` for working conventions, `SETUP.md` for onboarding, and
`MEMORY.md` for the lean project decision log.

## AI compatibility

`AGENTS.md` is the single source of truth, so project rules do not drift between
vendors. Skills are stored once in `.agents/skills/` using the open Agent Skills
format. Claude-specific skill and role files are intentionally tiny adapters that
point back to those canonical files.

| Assistant | Entry point |
| --- | --- |
| OpenAI Codex and other `AGENTS.md` tools | `AGENTS.md` |
| Claude Code | `CLAUDE.md` and `.claude/` adapters |
| Gemini CLI | `GEMINI.md` and `.agents/skills/` |
| GitHub Copilot | `AGENTS.md`, `.github/copilot-instructions.md`, and `.agents/skills/` |
| Cursor | `AGENTS.md` and `.cursor/rules/project.mdc` |

## Validation

Run the same lightweight checks used by GitHub Actions:

```powershell
.\bin\python.ps1 -m unittest discover -s tests -v
.\bin\python.ps1 -m compileall -q .agents tests
.\bin\python.ps1 -m pip check
```

Live API tests require the corresponding credentials and are intentionally not run
in CI.

## Publishing

This folder intentionally has no inherited Git history. To publish it as a new
private repository:

```powershell
git init
git add .
git commit -m "Initial team-ready data-analysis_v1"
git branch -M main
git remote add origin <private-repository-url>
git push -u origin main
```

Keep the repository private unless the owner deliberately selects and adds a
project `LICENSE`. Never commit `.env`, session data, proprietary wheels,
executables, commercial fonts, or licensed source datasets.
