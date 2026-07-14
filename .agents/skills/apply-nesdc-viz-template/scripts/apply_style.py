"""
Self-contained NESDC brand style loader for matplotlib/seaborn.

Usage (import from another script):
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parent))  # if calling from outside this skill
    from apply_style import apply_nesdc_style

    apply_nesdc_style()
    # ... then build charts as usual with plt / sns

Registers locally licensed FC Vision files from assets/fonts/FCVision/ when present,
applies the bundled nesdc_style.mplstyle color cycle and layout rcParams, and uses
a system-font fallback when the commercial font files are absent.
"""

import os
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib import font_manager

_SKILL_DIR = Path(__file__).resolve().parent.parent  # .../apply-nesdc-viz-template/
_FONTS_DIR = _SKILL_DIR / "assets" / "fonts" / "FCVision"
_STYLE_PATH = _SKILL_DIR / "assets" / "nesdc_style.mplstyle"


def apply_nesdc_style(font_name: str = "FC Vision") -> None:
    """Register licensed local fonts when available and apply the NESDC style."""
    registered_font = False
    if _FONTS_DIR.exists():
        for f in os.listdir(_FONTS_DIR):
            if f.endswith((".ttf", ".otf")):
                try:
                    font_manager.fontManager.addfont(str(_FONTS_DIR / f))
                    registered_font = True
                except Exception as e:
                    print(f"Warning: could not register font {f}: {e}")

    if _STYLE_PATH.exists():
        plt.style.use(str(_STYLE_PATH))

    if registered_font:
        plt.rcParams["font.family"] = font_name
    else:
        plt.rcParams["font.family"] = ["Leelawadee UI", "Tahoma", "DejaVu Sans", "sans-serif"]
        print(
            "Warning: FC Vision is not installed in this repository. Using a fallback font; "
            "see assets/fonts/FCVision/README.md."
        )


if __name__ == "__main__":
    apply_nesdc_style()
    print(f"NESDC style applied. Fonts dir: {_FONTS_DIR}")
    print(f"Style sheet: {_STYLE_PATH}")
