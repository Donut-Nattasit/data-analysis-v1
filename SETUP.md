# Setup and onboarding

This guide is written for both new teammates and their AI coding assistants. The
core project is free to install. Some data sources and NESDC-branded output need
credentials or licensed files that cannot be distributed through GitHub.

## Safe AI-assisted setup

Paste this into the AI coding assistant opened at the repository root:

> Read `AGENTS.md` and `SETUP.md` completely. Set up this repository for me,
> run `bin/doctor.ps1` and the credential-free tests, and guide me through any
> remaining account or licensed-file steps. Never ask me to paste a secret into
> chat, never reveal existing secret values, and use only the official or
> organization-authorized sources in `SETUP.md`.

The assistant may install public dependencies and inspect whether a credential is
configured. The user must personally sign in to provider portals, accept terms,
enter secrets into `.env`, and obtain files governed by an organizational license.

## 1. Install the core environment

Required on the computer:

- Windows 10 or 11 with Windows PowerShell 5.1 or PowerShell 7.
- Git from <https://git-scm.com/download/win>.
- Python 3.12 from <https://www.python.org/downloads/windows/>. During the
  installer, enable the Python launcher or add Python to `PATH`.
- Internet access while public Python packages are installed.

From the cloned repository root, run:

```powershell
PowerShell -ExecutionPolicy Bypass -File .\setup.ps1
PowerShell -ExecutionPolicy Bypass -File .\bin\doctor.ps1
```

`setup.ps1` creates `%LOCALAPPDATA%\venvs\data-analysis-v1`, installs the pinned
public packages, and creates a local `.env` from `.env.example` if needed. It never
overwrites an existing `.env`. The doctor reports readiness without printing any
credential values.

After setup, run all Python commands through the repository launcher:

```powershell
.\bin\python.ps1 --version
```

## 2. Configure only the data sources you are authorized to use

Open `.env` locally in the editor. Replace a placeholder only after obtaining the
corresponding credential. Never commit `.env`, paste its contents into AI chat, or
send credentials through an issue or pull request.

| Feature | What the user obtains | Authorized source | Local setting or file |
| --- | --- | --- | --- |
| CEIC | CEIC API entitlement, API key, and Python wheel version `2.11.5.396` | Ask the organization's CEIC license/API administrator. Product information is at <https://info.ceicdata.com/api-and-data-feed-solution>. Do not use an unofficial wheel. | `CEIC_API_KEY` in `.env`; wheel under `wheels/ceic_api_client-2.11.5.396-*.whl`; rerun `setup.ps1` |
| Bank of Thailand | API key for the required BOT API products | Register and subscribe at the current portal: <https://portal.api.bot.or.th/>. The legacy portal was retired; use a newly issued key. | `BOT_API_TOKEN` in `.env` |
| U.S. EIA | Free API key sent by email | <https://www.eia.gov/opendata/register.php> | `EIA_API_KEY` in `.env` |
| IMF | IMF Data API portal account/subscription key | <https://portal.api.imf.org/>. For access questions, use the support contact shown by the IMF portal. | `IMF_API_KEY` in `.env` |
| S&P Global Connect | Organization-approved API/PAT credentials | Ask the organization's S&P Global Connect or Market Intelligence administrator. API access is contract-dependent; do not reuse another person's account. | `SP_USERNAME` and `SP_PASSWORD` in `.env` |
| Thailand MOC | Nothing | Public API used by the project | No key required |
| World Bank | Nothing | Public World Bank API | No key required |

The S&P client uses the configured credentials only with HTTPS endpoints on
`api.connect.spglobal.com`. CEIC and S&P data remain subject to the organization's
licenses and must not be committed to the repository.

## 3. Install feature files that GitHub cannot contain

### X-13ARIMA-SEATS

1. Open the official U.S. Census Bureau page:
   <https://www.census.gov/data/software/x13as.X-13ARIMA-SEATS.html>.
2. Download the current Windows ASCII distribution.
3. Extract the executable and place or rename it exactly as `bin\x13as.exe`.
4. Rerun `bin\doctor.ps1`.

Do not download `x13as.exe` from a third-party binary mirror.

### FC Vision font

FC Vision is commercial typography and is not included in Git. Ask the authorized
NESDC brand/design, IT, procurement, or licensing contact for the approved `.otf`
or `.ttf` files. Copy them to:

```text
.agents\skills\apply-nesdc-viz-template\assets\fonts\FCVision\
```

Do not use unofficial font-download sites and do not commit the font files. Charts
still work with fallback fonts when FC Vision is absent; FC Vision is needed only
for fully branded NESDC typography.

### Optional shared databases

`GTA.db` and `LFS.db` are internal reference databases, not repository files. If a
teammate is authorized, obtain them through the repository owner or the applicable
NESDC data custodian and place them in the sibling directory:

```text
..\database\GTA.db
..\database\LFS.db
```

Do not copy these databases into Git.

## 4. Verify the installation

Run:

```powershell
PowerShell -ExecutionPolicy Bypass -File .\bin\doctor.ps1
.\bin\python.ps1 -m unittest discover -s tests -v
.\bin\python.ps1 -m pip check
```

`ACTION` does not mean the core installation failed. It means that a particular
optional or licensed feature still needs the item described in its row. For a
machine intended to use every feature, all doctor rows should show `READY` after
the user has supplied every authorized credential and file.

If PowerShell blocks scripts, use the explicit `PowerShell -ExecutionPolicy Bypass
-File ...` form shown above. This changes policy only for that process.

## 5. Before every push

Run `git status` and inspect staged changes. The following must never be committed:

- `.env` or any credential value;
- `session/` outputs or downloaded licensed data;
- `wheels/` or proprietary Python packages;
- `bin/x13as.exe`;
- FC Vision `.otf` or `.ttf` files;
- shared `.db` files.

If a credential may have been exposed, stop, revoke or rotate it at the provider,
and notify the repository owner privately.
