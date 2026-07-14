# Security

## Credentials

- Store API credentials only in `.env`; never commit that file.
- Keep `.env.example` limited to obvious placeholder values.
- Use repository or organization secrets for any future credentialed automation.
- Never paste credentials into an AI chat. An assistant may identify the required
  variable but must let the user enter its value privately in `.env`.
- Do not paste credentials into issues, pull requests, logs, notebooks, or session
  artifacts.

The S&P client sends HTTP Basic credentials only to HTTPS endpoints on
`api.connect.spglobal.com`.

## Sensitive and licensed data

Session folders, database files, spreadsheets, CSV files, proprietary wheels,
executables, and commercial fonts are ignored by default. Before committing, always
review `git status` and inspect the staged diff.

## Reporting a problem

Report suspected credential exposure or other vulnerabilities privately to the
repository owner. Do not open a public issue containing secrets or sensitive data.
