# NESDC Brand Palette & Typography

## Color cycle

| Name | Hex | Usage weight | Role |
| --- | --- | --- | --- |
| Sapphire Blue | `#00109E` | 60% | Primary — single-variable lines, baseline |
| Caribbean Sea | `#78DED4` | 15% | Secondary support |
| Clay | `#BFB997` | 15% | Neutral comparison / historical |
| Maya Blue | `#60B1E7` | 5% | Accent, auxiliary segments |
| Saffron | `#FFA300` | 5% | Critical flags, forecast boundaries |

- **Gridlines**: `#E9ECEF` (soft, alpha 0.7)
- **Recession/event shading**: `#E5E5E5` at `alpha=0.15`
- **Axis labels/ticks**: `#334155` (labels), `#64748B` (ticks)

## Typography

- **Font**: `FC Vision` when an authorized user supplies licensed files in `assets/fonts/FCVision/`. Otherwise `apply_nesdc_style()` uses a system fallback and warns. Never `TH Sarabun New` (legacy, deprecated).
- **English (default)**: Gregorian years (YYYY), English labels.
- **Thai (only when the user explicitly asks for Thai localization)**: Buddhist Era years (+543), Thai labels — use this skill's `scripts/thai_utils.py` (`to_thai_year`, `to_thai_quarter`, `to_thai_month`).

## Applying the style

```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path(".agents/skills/apply-nesdc-viz-template/scripts").resolve()))
from apply_style import apply_nesdc_style

apply_nesdc_style()  # registers FCVision fonts + applies nesdc_style.mplstyle color cycle/layout
```

Or with seaborn's theme API directly:
```python
import seaborn as sns
sns.set_theme(style="whitegrid", rc={"font.family": "FC Vision", "figure.facecolor": "#FFFFFF", "axes.facecolor": "#FFFFFF", "grid.color": "#E9ECEF", "grid.alpha": 0.7})
```

## Layout rules

- **Titles**: `fig.suptitle()` for main title, `ax.set_title()` for subtitle. One line each, never wrap.
- **X-axis dates**: Hide the axis label (`ax.set_xlabel(None)`). Max 8 ticks (`ax.xaxis.set_major_locator(plt.MaxNLocator(8))`). Rotate labels 30°.
- **Legend**: Bottom-center, max 4 columns, `bbox_to_anchor=(0.5, -0.06)`, `fig.subplots_adjust(bottom=0.14)`.
- **Source attribution**: Always include — `fig.text(0.08, 0.02, "Source: ...", fontsize=9, color='#64748b', ha='left')`.
- **Bar chart headroom**: `ax.set_ylim(top=max_val * 1.15)`.

## Visual quality self-audit

After generating each chart, check:
- Title fits one line (no wrapping)
- Legend not clipped by figure edge
- No NaN or "nan" visible in data
- Source attribution present at bottom-left
- Only NESDC palette colors used

Fix and regenerate if any check fails.
