---
name: apply-nesdc-viz-template
description: >
  Applies the official NESDC visual brand template (Sapphire/Saffron/Caribbean color cycle, FC Vision font, layout rules) to a chart. Use ONLY when the user explicitly asks to apply NESDC styling, the NESDC brand/template, or "official" NESDC visualization standards to a chart. Do NOT use this for ordinary chart requests with no such explicit ask — those should get plain, sensible default matplotlib/seaborn styling instead.
---

# Apply NESDC Visualization Template

Skill bundling the official NESDC brand palette and matplotlib style sheet. FC Vision is a separately licensed commercial font and is loaded from this skill's local assets directory only when an authorized user supplies it.

## When to use this skill

**Only when the user explicitly asks for NESDC branding/style/template** — e.g. "apply the NESDC style", "make this look official", "use the NESDC template", "brand this chart". A plain "make me a chart" or "plot this" request should NOT trigger this skill — use ordinary default styling (seaborn `whitegrid` or matplotlib defaults) for those.

## Usage

```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path(".agents/skills/apply-nesdc-viz-template/scripts").resolve()))
from apply_style import apply_nesdc_style

apply_nesdc_style()  # registers locally supplied fonts + applies color/layout rcParams
# ... build the chart as usual with matplotlib/seaborn
```

Read `references/color_palette.md` for the full color/typography/layout spec and `references/chart_templates.md` for ready-to-use chart function templates (line, stacked bar, Altair) before building a new chart from scratch.

## Thai localization

Only when the user also explicitly asks for Thai localization: use `scripts/thai_utils.py` (`to_thai_year`, `to_thai_quarter`, `to_thai_month`) for Buddhist Era year conversion. `TH Sarabun New` is legacy — never use it; Thai charts still use FC Vision.

## Execution

Write scripts to the active session folder (`session/YYYY-MM-DD-<slug>/`), run via the project launcher (`bin\python.ps1`), save the chart PNG into the same session folder.

## Troubleshooting

| Issue | Cause | Resolution |
| :--- | :--- | :--- |
| Font not rendering as FC Vision | Licensed font files are absent, or style is applied too late | Add authorized font files as described in `assets/fonts/FCVision/README.md`, then call `apply_nesdc_style()` before creating a figure |
| Colors don't match the palette | Manual color codes used instead of the style sheet's cycle | Let matplotlib's `axes.prop_cycle` assign colors automatically, or reference `references/color_palette.md` hex codes directly |
