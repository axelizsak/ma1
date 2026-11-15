"""
One look for every chart: the two brand colours and a quiet axis style.

The colours come from a palette that was checked for colour-blind readers
(orange and blue stay distinct for all common types of colour blindness).
"""
import matplotlib.pyplot as plt

BRAND_COLOR = {"Brewhaus": "#eb6834", "Trailnorth": "#2a78d6"}
SURFACE = "#fcfcfb"     # chart background
TEXT = "#0b0b0b"        # titles and values
TEXT_SOFT = "#52514e"   # subtitles and labels
MUTED = "#898781"       # axis ticks
GRID = "#e1e0d9"        # hairline grid
NEUTRAL = "#b9b7ae"     # marks that are not about one brand


def use_style():
    plt.rcParams.update({
        "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
        "font.family": "sans-serif", "font.sans-serif": ["Helvetica Neue", "Helvetica", "Arial", "DejaVu Sans"],
        "font.size": 11, "text.color": TEXT,
        "axes.edgecolor": GRID, "axes.linewidth": 1, "axes.labelcolor": TEXT_SOFT,
        "axes.spines.top": False, "axes.spines.right": False, "axes.spines.left": False,
        "axes.grid": True, "axes.grid.axis": "y", "grid.color": GRID, "grid.linewidth": 1,
        "axes.axisbelow": True,
        "xtick.color": MUTED, "ytick.color": MUTED, "xtick.labelsize": 10, "ytick.labelsize": 10,
        "xtick.major.size": 0, "ytick.major.size": 0,
        "legend.frameon": False, "savefig.dpi": 200, "savefig.bbox": "tight",
    })


def title(fig, main, sub=None, x=0.01, y=1.0):
    """Left-aligned title with an optional one-line subtitle."""
    fig.text(x, y + 0.055, main, fontsize=14, fontweight="bold", color=TEXT, ha="left", va="bottom")
    if sub:
        fig.text(x, y + 0.01, sub, fontsize=10.5, color=TEXT_SOFT, ha="left", va="bottom")
