---
name: fetch-bot
description: >
  Retrieves Thai domestic macroeconomic, monetary, and financial series from the Bank of Thailand (BOT) API. Use whenever the user asks for Thai policy rate, money supply, exchange rate, financial institution, or other official BOT indicator data — even if they don't explicitly say "BOT".
---

# Fetch: Bank of Thailand (BOT)

Self-contained skill for browsing and fetching series from the BOT API. No project-wide imports — everything needed lives in this skill folder.

## Prerequisites

- `BOT_API_TOKEN` must be set in the repository-root `.env` (or the parent-directory fallback).
- Register and subscribe to the required API product at the current BOT developer
  portal, https://portal.api.bot.or.th/, if no token exists yet. The former portal
  was retired at the end of 2025, so old keys may no longer work.

## Usage

### 1. List categories

```powershell
& '.\bin\python.ps1' '.agents\skills\fetch-bot\scripts\fetch_bot.py' categories
```

### 2. List series within a category

```powershell
& '.\bin\python.ps1' '.agents\skills\fetch-bot\scripts\fetch_bot.py' series --category <category_code>
```

### 3. Fetch a series

```powershell
& '.\bin\python.ps1' '.agents\skills\fetch-bot\scripts\fetch_bot.py' fetch RP1D --start 2010-01-01 --out session/2026-07-14-my-task/bot_policy_rate.csv
```

- BOT's API caps each request at ~10 years of history — the client automatically chunks the request into 5-year windows and stitches them together.
- Always writes a **wide-format** CSV (Date index). No persistent cache — every call fetches live.

## Priority note

For Thai domestic macro data, BOT is the first-priority source (official central bank data); fall back to `fetch-moc` for retail/wholesale product prices and detailed trade data that BOT doesn't cover.

## Troubleshooting

| Issue | Cause | Resolution |
| :--- | :--- | :--- |
| `BOT_API_TOKEN` error | Missing/expired token in `.env` | Check `.env`, then register or re-subscribe at `https://portal.api.bot.or.th/` |
| Empty result on fetch | Wrong series code | Run `series --category <code>` to confirm the exact code |
| Slow fetch for long histories | BOT's 10-year request cap forces multiple chunked calls | Expected — no action needed, just wait |
