# NESDC Chart Templates (Matplotlib & Altair)

Pre-tested charting code for NESDC-branded output. Apply `apply_nesdc_style()` (see `apply_style.py` / `color_palette.md`) before building any matplotlib/seaborn figure below.

## 1. Matplotlib line chart (standard)

```python
import matplotlib.pyplot as plt

def plot_line_chart(df, date_col, value_col, title, output_path, source="NESDC"):
    fig, ax = plt.subplots()
    ax.plot(df[date_col], df[value_col], color="#00109E", linewidth=2.5)
    fig.suptitle(title)
    ax.set_xlabel(None)
    ax.xaxis.set_major_locator(plt.MaxNLocator(8))
    plt.setp(ax.get_xticklabels(), rotation=30)
    fig.text(0.08, 0.02, f"Source: {source}", fontsize=9, color='#64748b', ha='left')
    fig.savefig(output_path, dpi=300, bbox_inches="tight")
```

## 2. Matplotlib stacked bar (decomposition)

```python
import matplotlib.pyplot as plt

def plot_decomposition(df, date_col, components, title, output_path):
    fig, ax = plt.subplots()
    df.plot(x=date_col, y=components, kind='bar', stacked=True, ax=ax)
    ax.set_title(title)
    ax.set_ylabel('Contribution')
    fig.tight_layout()
    fig.savefig(output_path, dpi=300)
```

## 3. Thai localization (only when the user explicitly requests it)

```python
import matplotlib.pyplot as plt
import sys
from pathlib import Path
sys.path.insert(0, str(Path(".agents/skills/apply-nesdc-viz-template/scripts").resolve()))
from thai_utils import to_thai_year

plt.rcParams['font.family'] = 'FC Vision'
plt.rcParams['font.size'] = 16

df = to_thai_year(df, 'date')  # adds 'thai_year_label'
```

## 4. Altair line chart

```python
import altair as alt

def create_economic_line_chart(df, x_col, y_col, color_col, title):
    return alt.Chart(df).mark_line(strokeWidth=3).encode(
        x=alt.X(f'{x_col}:T', title='Date'),
        y=alt.Y(f'{y_col}:Q', title='Value', scale=alt.Scale(zero=False)),
        color=alt.Color(f'{color_col}:N', legend=alt.Legend(title="Series"),
                         scale=alt.Scale(range=["#00109E", "#78DED4", "#BFB997", "#60B1E7", "#FFA300"])),
        tooltip=[x_col, y_col, color_col]
    ).properties(title=title, width=600, height=400).interactive()
```
