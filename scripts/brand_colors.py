# Confluent Brand Color System
# Source: Official Confluent logo (rainbow gradient) + DebtBusters/JustMoney brand guidelines

CONFLUENT = {
    "red":    "#E8363B",
    "orange": "#F57C2D",
    "yellow": "#F5C842",
    "green":  "#52B748",
    "teal":   "#00A99D",
    "blue":   "#1E88E5",
    "purple": "#8B4DC8",
}

# Ordered rainbow sequence (left-to-right from logo)
RAINBOW = [
    CONFLUENT["red"],
    CONFLUENT["orange"],
    CONFLUENT["yellow"],
    CONFLUENT["green"],
    CONFLUENT["teal"],
    CONFLUENT["blue"],
    CONFLUENT["purple"],
]

# DebtBusters brand (dark navy + teal)
DEBTBUSTERS = {
    "navy":        "#1A2B4B",
    "teal":        "#00A99D",
    "light_grey":  "#F5F6FA",
    "mid_grey":    "#8E9BB0",
    "white":       "#FFFFFF",
    "danger":      "#E8363B",
    "success":     "#52B748",
    "warning":     "#F5C842",
}

# JustMoney brand (green/white)
JUSTMONEY = {
    "green":  "#00B14F",
    "dark":   "#1A3024",
    "white":  "#FFFFFF",
    "grey":   "#F4F4F4",
}

# Combined palette for charts (7 categorical colours)
CHART_PALETTE = RAINBOW

# Matplotlib rcParams preset for Confluent style
import matplotlib as mpl

def apply_confluent_style():
    mpl.rcParams.update({
        "figure.facecolor":   DEBTBUSTERS["light_grey"],
        "axes.facecolor":     "#FFFFFF",
        "axes.edgecolor":     DEBTBUSTERS["mid_grey"],
        "axes.labelcolor":    DEBTBUSTERS["navy"],
        "axes.titlesize":     13,
        "axes.labelsize":     10,
        "axes.grid":          True,
        "grid.color":         "#E0E4EC",
        "grid.linestyle":     "--",
        "grid.linewidth":     0.6,
        "xtick.color":        DEBTBUSTERS["mid_grey"],
        "ytick.color":        DEBTBUSTERS["mid_grey"],
        "text.color":         DEBTBUSTERS["navy"],
        "font.family":        "sans-serif",
        "font.size":          9,
        "legend.framealpha":  0.9,
        "legend.edgecolor":   DEBTBUSTERS["mid_grey"],
        "figure.dpi":         150,
    })
