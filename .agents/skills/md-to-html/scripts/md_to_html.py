# md_to_html.py  (part of the md-to-html skill)
# Convert a Markdown report to a single HTML file with embedded local assets.
#   - All local images are base64-embedded (no broken paths when emailing).
#   - LaTeX math ($...$ / $$...$$) rendered via MathJax v3 CDN.
#   - Tables, fenced code blocks, footnotes supported.
#
# Usage (from workspace root):
#   $env:PYTHONPATH='.'; .\bin\python.ps1 .agents/skills/md-to-html/scripts/md_to_html.py <input.md> <output.html>
#
# If output path is omitted, replaces the .md extension with .html in the same directory.

import sys
import re
import base64
import html as html_lib
import markdown
from pathlib import Path

# ── paths ─────────────────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parents[4]   # workspace root (.agents/skills/md-to-html/scripts/ is 4 levels deep)

if len(sys.argv) >= 2 and sys.argv[1] in {"-h", "--help"}:
    print("Usage: md_to_html.py <input.md> [output.html]")
    sys.exit(0)
elif len(sys.argv) >= 2:
    md_path = Path(sys.argv[1])
    if not md_path.is_absolute():
        md_path = ROOT / md_path
else:
    print("[ERROR] Please supply an input Markdown path as the first argument.")
    sys.exit(1)

if len(sys.argv) >= 3:
    out_path = Path(sys.argv[2])
    if not out_path.is_absolute():
        out_path = ROOT / out_path
else:
    out_path = md_path.with_suffix(".html")

if not md_path.exists():
    print(f"[ERROR] Input file not found: {md_path}")
    sys.exit(1)

# ── read markdown ─────────────────────────────────────────────────────────────
raw_md = md_path.read_text(encoding="utf-8")

# Strip YAML front-matter (---...---) if present
if raw_md.startswith("---"):
    end = raw_md.find("---", 3)
    if end != -1:
        raw_md = raw_md[end + 3:].lstrip()

# ── pre-process: embed images as base64 ──────────────────────────────────────
embedded_count = 0

def embed_image(match):
    global embedded_count
    alt  = match.group(1)
    path = match.group(2)

    # Skip already-embedded data URIs and remote images.
    if path.startswith(("data:", "http://", "https://")):
        return match.group(0)

    img_path = (md_path.parent / path).resolve()
    if img_path.exists():
        ext  = img_path.suffix.lower().lstrip(".")
        mime = {
            "png":  "image/png",
            "jpg":  "image/jpeg",
            "jpeg": "image/jpeg",
            "gif":  "image/gif",
            "svg":  "image/svg+xml",
        }.get(ext, "image/png")
        b64 = base64.b64encode(img_path.read_bytes()).decode()
        embedded_count += 1
        return f"![{alt}](data:{mime};base64,{b64})"
    else:
        print(f"  [WARN] Image not found: {img_path}")
        return match.group(0)

raw_md = re.sub(r"!\[([^\]]*)\]\(([^)]+)\)", embed_image, raw_md)

# ── pre-process: embed CSV datasets as base64 ──────────────────────────────────
embedded_csv_count = 0

def embed_csv(match):
    global embedded_csv_count
    text = match.group(1)
    path = match.group(2)

    # Skip non-csv or remote URLs
    if not path.lower().endswith(".csv") or path.startswith("data:") or path.startswith("http"):
        return match.group(0)

    csv_path = (md_path.parent / path).resolve()
    if csv_path.exists():
        b64 = base64.b64encode(csv_path.read_bytes()).decode()
        embedded_csv_count += 1
        return f"[{text}](data:text/csv;base64,{b64})"
    else:
        print(f"  [WARN] CSV not found: {csv_path}")
        return match.group(0)

raw_md = re.sub(r"\[([^\]]*)\]\(([^)]+)\)", embed_csv, raw_md)


# ── convert Markdown -> HTML ──────────────────────────────────────────────────
extensions = [
    "tables",
    "fenced_code",
    "footnotes",
    "toc",
    "attr_list",
    "pymdownx.arithmatex",
]
extension_configs = {
    "pymdownx.arithmatex": {
        "generic": True,   # outputs \(...\) and \[...\] for MathJax v3
        "inline_syntax": ["round"],
        "block_syntax": ["square"]
    },
}

body_html = markdown.markdown(
    raw_md,
    extensions=extensions,
    extension_configs=extension_configs,
)

# Convert fenced code blocks marked as mermaid to <div class="mermaid"> for MermaidJS
has_mermaid = "class=\"language-mermaid\"" in body_html
mermaid_scripts = ""
if has_mermaid:
    def convert_mermaid(match):
        raw_content = match.group(1)
        # Unescape HTML entities so MermaidJS gets raw syntax (like --> instead of --&gt;)
        unescaped = html_lib.unescape(raw_content)
        return f'<div class="mermaid">{unescaped}</div>'

    body_html = re.sub(
        r'<pre><code class="language-mermaid">(.*?)</code></pre>',
        convert_mermaid,
        body_html,
        flags=re.DOTALL
    )

    mermaid_scripts = """
  <!-- MermaidJS -->
  <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
  <script>
    mermaid.initialize({ startOnLoad: true, theme: 'default' });
  </script>
"""

# ── derive page title from filename ──────────────────────────────────────────
title = html_lib.escape(md_path.stem.replace("_", " "))
source_name = html_lib.escape(md_path.name)

# ── full HTML shell ───────────────────────────────────────────────────────────
html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{title}</title>

  <!-- Fonts -->
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Outfit:wght@500;600;700;800&display=swap" rel="stylesheet">

  <!-- MathJax v3: renders \\( \\) inline and \\[ \\] display math -->
  <script>
    window.MathJax = {{
      tex: {{
        inlineMath:  [['\\\\(', '\\\\)']],
        displayMath: [['\\\\[', '\\\\]']],
      }},
      options: {{ skipHtmlTags: ['script','noscript','style','textarea','pre'] }},
    }};
  </script>
  <script async src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-chtml.js"></script>
  {mermaid_scripts}
  <style>
    *, *::before, *::after {{ box-sizing: border-box; }}
    html {{ font-size: 16px; }}
    body {{
      font-family: 'Inter', 'Segoe UI', Helvetica, Arial, sans-serif;
      line-height: 1.75;
      color: #334155;
      background: #f8fafc;
      margin: 0;
      padding: 2.5rem 1rem;
    }}

    /* Paper */
    .paper {{
      max-width: 900px;
      margin: 0 auto;
      background: #ffffff;
      border-radius: 12px;
      box-shadow: 0 10px 30px rgba(15, 23, 42, 0.08);
      padding: 3.5rem 4.5rem;
      border: 1px solid #e2e8f0;
    }}

    /* Headings */
    h1, h2, h3, h4 {{
      font-family: 'Outfit', 'Segoe UI', sans-serif;
      color: #0f172a;
      margin-top: 0;
    }}
    h1 {{
      font-size: 2.2rem;
      font-weight: 800;
      color: #00109E; /* NESDC Sapphire */
      border-bottom: 3px solid #00109E;
      padding-bottom: .6rem;
      margin-bottom: 1.8rem;
    }}
    h2 {{
      font-size: 1.5rem;
      font-weight: 700;
      color: #1e293b;
      border-left: 4px solid #FFA300; /* Saffron Accent */
      padding-left: .8rem;
      margin-top: 2.5rem;
      margin-bottom: 1.2rem;
    }}
    h3 {{
      font-size: 1.2rem;
      font-weight: 600;
      color: #334155;
      margin-top: 1.8rem;
      margin-bottom: 0.8rem;
    }}

    /* Text */
    p {{ margin: .85rem 0 1.2rem; }}
    ul, ol {{ padding-left: 1.8rem; margin-bottom: 1.5rem; }}
    li {{ margin: .4rem 0; }}
    strong {{ color: #0f172a; font-weight: 600; }}
    hr {{ border: none; border-top: 1px solid #e2e8f0; margin: 3rem 0; }}

    /* Tables - Rebuilt for Perfect Layout and Auto Widths */
    table {{
      width: 100%;
      border-collapse: collapse;
      font-size: .92rem;
      margin: 2rem 0;
      border: 1px solid #cbd5e1;
      border-radius: 8px;
      overflow: hidden;
      box-shadow: 0 4px 15px rgba(0, 0, 0, 0.03);
    }}

    /* Make table scrollable on mobile screens via a clean utility wrapper */
    @media (max-width: 768px) {{
      table {{
        display: block;
        overflow-x: auto;
        white-space: nowrap;
      }}
    }}

    thead tr {{
      background: #00109E; /* NESDC Primary Navy */
      color: #ffffff;
      border-bottom: 2px solid #000c80;
    }}
    thead th {{
      padding: .9rem 1.2rem;
      font-weight: 600;
      letter-spacing: 0.01em;
      vertical-align: middle;
    }}
    tbody tr {{
      border-bottom: 1px solid #e2e8f0;
      transition: background-color 0.15s ease;
    }}
    tbody tr:last-child {{
      border-bottom: none;
    }}
    tbody tr:hover {{
      background-color: #f1f5f9; /* Subtle slate hover */
    }}
    tbody tr:nth-child(even) {{
      background: #f8fafc; /* Alternating rows */
    }}
    tbody tr:nth-child(even):hover {{
      background-color: #f1f5f9;
    }}
    tbody td {{
      padding: .85rem 1.2rem;
      vertical-align: middle;
      color: #334155;
    }}

    /* Maintain cell align from markdown parsing */
    th[align="left"], td[align="left"] {{ text-align: left; }}
    th[align="center"], td[align="center"] {{ text-align: center; }}
    th[align="right"], td[align="right"] {{ text-align: right; }}

    /* Images */
    img {{
      max-width: 100%;
      height: auto;
      display: block;
      margin: 2rem auto;
      border-radius: 8px;
      box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
      border: 1px solid #e2e8f0;
    }}

    /* Code */
    code {{
      background: #f1f5f9;
      border-radius: 4px;
      padding: .15em .4em;
      font-size: .9em;
      font-family: 'Courier New', monospace;
      color: #0f172a;
    }}
    pre code {{ background: none; padding: 0; color: inherit; }}
    pre {{
      padding: 1rem 1.2rem;
      overflow-x: auto;
    }}

    /* Footer */
    .footer {{
      margin-top: 3rem;
      padding-top: 1rem;
      border-top: 1px solid #dce3f0;
      font-size: .78rem;
      color: #6b7280;
      text-align: center;
    }}

    /* Print */
    @media print {{
      body {{ background: #fff; padding: 0; }}
      .paper {{ box-shadow: none; padding: 1rem 1.5rem; }}
      a {{ color: inherit; text-decoration: none; }}
    }}

    /* Download buttons */
    .download-btn {{
      display: inline-block;
      background: #0f172a;
      color: #ffffff !important;
      padding: 0.3rem 0.6rem;
      border-radius: 4px;
      text-decoration: none;
      font-size: 0.8rem;
      font-weight: 500;
      margin-left: 0.5rem;
      transition: background-color 0.15s ease;
      border: 1px solid #0f172a;
      vertical-align: middle;
    }}
    .download-btn:hover {{
      background: #334155;
      border-color: #334155;
    }}
  </style>
</head>
<body>
  <div class="paper">
    {body_html}
    <div class="footer">
      Generated from <em>{source_name}</em> &mdash; NESDC Economic Research Unit
    </div>
  </div>
</body>
</html>
"""

# ── write output ──────────────────────────────────────────────────────────────
out_path.parent.mkdir(parents=True, exist_ok=True)
out_path.write_text(html, encoding="utf-8")

size_kb = out_path.stat().st_size / 1024
try:
    display_path = out_path.relative_to(ROOT)
except ValueError:
    display_path = out_path
print(f"[OK] Single-file HTML saved: {display_path}")
print(f"     File size     : {size_kb:.1f} KB")
print(f"     Images embedded: {embedded_count}")
print(f"     Datasets embedded: {embedded_csv_count}")
print(f"     MathJax       : yes (CDN)")
