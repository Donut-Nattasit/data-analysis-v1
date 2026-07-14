---
name: md-to-html
description: >
  Converts Markdown reports to single-file HTML with base64-embedded local images and CSV files plus MathJax rendering from a CDN. Use whenever the user asks to export a report, create shareable HTML, convert Markdown to HTML, or prepare a document for email distribution.
---

# Markdown to HTML Export Skill

## Purpose
This skill converts Markdown reports into portable, single-file HTML documents. It embeds local image and CSV assets as base64 data URIs. Fonts, MathJax, and Mermaid are loaded from public CDNs, so those features require an internet connection when the HTML is opened.

## Input/output convention

Both the input `.md` and output `.html` live in the same session folder — `session/YYYY-MM-DD-<slug>/`. There is no project-name branching or output/chart-vs-output/report split to worry about; everything for a conversation is already flat in one folder.

```
Input:  session/2026-07-14-my-task/report.md
Output: session/2026-07-14-my-task/report.html
                  │
                  ▼
     Run Black-Box Python Script
 (Embeds base64 charts & MathJax CDN)
```

## Execution Protocol

### Step 1 — Check Dependencies
* Run the validation snippet to ensure the required python libraries (`markdown`, `pymdown-extensions`) are installed:
  ```powershell
  $env:PYTHONPATH='.'; .\bin\python.ps1 -c "import markdown; import pymdownx; print('Dependencies OK')"
  ```
* If this command fails, install them:
  ```powershell
  $env:PYTHONPATH='.'; .\bin\python.ps1 -m pip install markdown pymdown-extensions
  ```

### Step 2 — Execute the Conversion
* Call the python converter script with the input and output arguments:
  ```powershell
  $env:PYTHONPATH='.'; .\bin\python.ps1 .agents/skills/md-to-html/scripts/md_to_html.py <INPUT_MD_PATH> <OUTPUT_HTML_PATH>
  ```

### Step 3 — Post-Flight Verification
* Verify that the generated HTML has base64 data strings instead of relative paths for all visual figures.
* **Why?** Embedded local assets will not break when the user emails the file or shares it on a network drive. CDN-backed math, diagrams, and web fonts still require internet access.

## Examples

**Example 1:**
*Input:* "Convert my report in session/2026-07-14-my-task/ to HTML."
*Action:* Use `.\bin\python.ps1 .agents/skills/md-to-html/scripts/md_to_html.py session/2026-07-14-my-task/report.md session/2026-07-14-my-task/report.html`. Check the output file to confirm the images were base64 encoded successfully.

## Troubleshooting

| Issue / Error | Cause | Resolution |
| :--- | :--- | :--- |
| `ModuleNotFoundError: markdown` | Dependencies not installed in the active virtual environment | Run the pip install commands specified in Step 1. |
| `Warning: Image path not found` | Chart image does not exist at the relative path specified in markdown | Verify that the chart PNG exists in the same session folder and is referenced correctly relative to the markdown file. |
| `Math equations display raw LaTeX code` | MathJax CDN blocked or offline | Open the HTML file in a browser with active internet connection. On first load, MathJax resources are cached locally. |
