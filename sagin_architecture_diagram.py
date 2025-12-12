"""
Generate a simplified SAGIN (Space-Air-Ground Integrated Network) architecture diagram.

The output is a compact, paper-friendly schematic with three layers (Space/Air/Ground),
annotated altitude ticks (not to scale), and dashed wireless links.
"""

import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, Rectangle, Circle


def add_arrow(ax, start, end, color="#2f5597", style="--", alpha=0.9, zorder=2, lw=0.8):
    """Add a dashed arrow between two points."""
    arrow = FancyArrowPatch(
        start,
        end,
        arrowstyle="->",
        mutation_scale=6,
        lw=lw,
        linestyle=style,
        color=color,
        alpha=alpha,
        zorder=zorder,
    )
    ax.add_patch(arrow)


def add_label(ax, text, xy, color="#1d3d70", size=7, weight="bold", ha="center"):
    """Place a small label."""
    ax.text(xy[0], xy[1], text, ha=ha, va="center", fontsize=size, color=color, weight=weight)


def draw_satellite(ax, x, y, size=120, face="#dce8ff", edge="#2f5597", label=None):
    """Draw a stylized satellite marker."""
    ax.scatter(x, y, s=size, marker="^", facecolor=face, edgecolor=edge, linewidth=1.0, zorder=4)
    ax.scatter(x, y, s=size * 0.35, marker="s", facecolor=face, edgecolor=edge, linewidth=1.0, zorder=5)
    if label:
        add_label(ax, label, (x, y + 0.12), color=edge, size=6, weight="semibold")


def draw_hap(ax, x, y):
    """Draw a high-altitude platform as a rounded rectangle with a small mast."""
    body = Rectangle((x - 1.2, y - 0.08), 2.4, 0.16, linewidth=0.8, edgecolor="#2f5f98", facecolor="#ebf2ff", zorder=4)
    mast = Rectangle((x - 0.05, y), 0.1, 0.12, linewidth=0.6, edgecolor="#2f5f98", facecolor="#2f5f98", zorder=5)
    ax.add_patch(body)
    ax.add_patch(mast)
    add_label(ax, "HAP", (x, y + 0.18), color="#2f5f98")


def draw_uav(ax, x, y):
    """Draw a small UAV marker."""
    body = Rectangle((x - 0.7, y - 0.05), 1.4, 0.1, linewidth=0.7, edgecolor="#3b6ea3", facecolor="#dfefff", zorder=4)
    wing = Rectangle((x - 1.0, y - 0.02), 2.0, 0.04, linewidth=0.6, edgecolor="#3b6ea3", facecolor="#b6d5ff", zorder=3)
    ax.add_patch(wing)
    ax.add_patch(body)
    add_label(ax, "UAV", (x, y + 0.16), color="#3b6ea3")


def draw_ground_station(ax, x, y):
    """Draw a ground station with a large antenna."""
    base = Rectangle((x - 1.2, y - 0.15), 1.5, 0.3, linewidth=0.8, edgecolor="#2f4f4f", facecolor="#e2efe2", zorder=3)
    dish = Circle((x + 0.2, y + 0.4), 0.45, edgecolor="#2f4f4f", facecolor="#d6e7ff", linewidth=0.8, zorder=4)
    mast = Rectangle((x + 0.1, y + 0.05), 0.2, 0.35, linewidth=0.7, edgecolor="#2f4f4f", facecolor="#c7d7ff", zorder=4)
    ax.add_patch(base)
    ax.add_patch(mast)
    ax.add_patch(dish)
    add_label(ax, "Ground Station", (x, y - 0.35), color="#2f4f4f", size=6)


def draw_base_station(ax, x, y):
    """Draw a simple cellular tower."""
    tower = Rectangle((x - 0.1, y), 0.2, 0.8, linewidth=0.8, edgecolor="#355b3b", facecolor="#cce8cc", zorder=4)
    ax.add_patch(tower)
    for i in range(3):
        y_level = y + 0.2 + i * 0.2
        ax.plot([x, x - 0.35], [y_level, y_level + 0.18], color="#355b3b", lw=0.8, zorder=4)
        ax.plot([x, x + 0.35], [y_level, y_level + 0.18], color="#355b3b", lw=0.8, zorder=4)
    add_label(ax, "Base Station", (x, y - 0.25), color="#355b3b", size=6)


def draw_mobile_user(ax, x, y, label, color="#2f4f4f"):
    """Draw a simple mobile user icon."""
    phone = Rectangle((x - 0.15, y), 0.3, 0.5, linewidth=0.7, edgecolor=color, facecolor="#fff7e6", zorder=4)
    screen = Rectangle((x - 0.12, y + 0.05), 0.24, 0.32, linewidth=0.5, edgecolor=color, facecolor="#e8f3ff", zorder=5)
    ax.add_patch(phone)
    ax.add_patch(screen)
    add_label(ax, label, (x, y - 0.22), color=color, size=6)


def draw_vehicle(ax, x, y, label):
    """Draw a ground vehicle marker."""
    body = Rectangle((x - 0.6, y), 1.2, 0.28, linewidth=0.7, edgecolor="#2f4f4f", facecolor="#dfe9f5", zorder=4)
    roof = Rectangle((x - 0.3, y + 0.22), 0.6, 0.18, linewidth=0.7, edgecolor="#2f4f4f", facecolor="#c7d7ee", zorder=5)
    ax.add_patch(body)
    ax.add_patch(roof)
    ax.scatter([x - 0.4, x + 0.4], [y, y], s=14, color="#2f4f4f", zorder=5)
    add_label(ax, label, (x, y - 0.28), color="#2f4f4f", size=6)


def main():
    plt.rcParams.update({"font.size": 8, "font.family": "DejaVu Sans"})

    fig, ax = plt.subplots(figsize=(3.35, 5.2), dpi=300)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 6)
    ax.set_xticks([])

    # Altitude ticks (conceptual, not to scale).
    yticks = [0, 0.5, 1.0, 2.5, 3.5, 5.5]
    ylabels = ["0", "10", "20", "500", "2000", "35786 km"]
    ax.set_yticks(yticks)
    ax.set_yticklabels(ylabels, fontsize=7)
    ax.tick_params(axis="y", which="both", length=3, width=0.8, labelsize=7)
    ax.set_ylabel("Height (km, not to scale)", fontsize=7, labelpad=8)

    for spine in ["right", "top", "bottom"]:
        ax.spines[spine].set_visible(False)
    ax.spines["left"].set_position(("axes", -0.03))
    ax.spines["left"].set_linewidth(0.8)

    # Layer backgrounds.
    ax.axhspan(0, 0.8, facecolor="#d8f1d5", alpha=0.9, zorder=0)
    ax.axhspan(0.8, 2.0, facecolor="#e8f4ff", alpha=0.9, zorder=0)
    ax.axhspan(2.0, 6.0, facecolor="#d9e7ff", alpha=0.85, zorder=0)

    # Layer labels.
    add_label(ax, "Space Layer", (92, 5.2), color="#1f4f99", size=8)
    add_label(ax, "Air Layer", (92, 1.6), color="#1f4f99", size=8)
    add_label(ax, "Ground Layer", (92, 0.35), color="#1f4f99", size=8)

    # Space layer objects.
    draw_satellite(ax, 20, 3.0, size=130, label="LEO")
    draw_satellite(ax, 55, 3.3, size=130, label="LEO")
    draw_satellite(ax, 80, 3.1, size=130, label="LEO")

    draw_satellite(ax, 35, 4.0, size=150, label="MEO")
    draw_satellite(ax, 70, 4.2, size=150, label="MEO")

    draw_satellite(ax, 50, 5.5, size=190, label="GEO")

    # ISL dashed links.
    add_arrow(ax, (20, 3.0), (55, 3.3), color="#6a7fb8", style="--", lw=0.8)
    add_arrow(ax, (55, 3.3), (80, 3.1), color="#6a7fb8", style="--", lw=0.8)
    add_arrow(ax, (35, 4.0), (70, 4.2), color="#6a7fb8", style="--", lw=0.8)
    add_arrow(ax, (50, 5.5), (70, 4.2), color="#6a7fb8", style="--", lw=0.8)
    add_arrow(ax, (50, 5.5), (35, 4.0), color="#6a7fb8", style="--", lw=0.8)

    # Air layer objects.
    draw_hap(ax, 32, 1.3)
    draw_uav(ax, 18, 0.9)
    draw_uav(ax, 70, 0.95)

    # Ground layer objects.
    draw_ground_station(ax, 18, 0.22)
    draw_base_station(ax, 60, 0.2)
    draw_vehicle(ax, 45, 0.25, "Connected Vehicle")
    draw_mobile_user(ax, 72, 0.22, "Handset")
    draw_mobile_user(ax, 85, 0.24, "Maritime")

    # Remote area indicator.
    ax.fill_between([5, 15], [0.05, 0.05], [0.25, 0.25], color="#c7e4c2", alpha=0.8, zorder=1)
    add_label(ax, "Remote / Mountainous", (10, 0.43), color="#2f4f4f", size=6)

    # Links: air-to-ground and air-to-space.
    add_arrow(ax, (32, 1.3), (18, 0.4), color="#2f5597", style=":", lw=0.9)  # HAP -> ground station
    add_arrow(ax, (32, 1.3), (60, 0.8), color="#2f5597", style=":", lw=0.9)  # HAP -> base station
    add_arrow(ax, (32, 1.3), (55, 3.3), color="#2f5597", style=":", lw=0.9)  # HAP -> LEO

    add_arrow(ax, (18, 0.9), (18, 0.35), color="#2f5597", style=":", lw=0.9)  # UAV -> ground
    add_arrow(ax, (18, 0.9), (35, 4.0), color="#2f5597", style=":", lw=0.9)  # UAV -> MEO

    add_arrow(ax, (70, 0.95), (60, 1.0), color="#2f5597", style=":", lw=0.9)  # UAV -> base station
    add_arrow(ax, (70, 0.95), (80, 3.1), color="#2f5597", style=":", lw=0.9)  # UAV -> LEO

    # Ground user links.
    add_arrow(ax, (60, 0.8), (45, 0.35), color="#2f5597", style=":", lw=0.9)  # Base -> vehicle
    add_arrow(ax, (60, 0.8), (72, 0.4), color="#2f5597", style=":", lw=0.9)  # Base -> handset
    add_arrow(ax, (18, 0.55), (85, 0.45), color="#2f5597", style=":", lw=0.7, alpha=0.7)  # Backhaul (conceptual)

    # Titles.
    ax.text(0, 6.1, "SAGIN Architecture (Space-Air-Ground Integrated Network)", fontsize=8.2, weight="bold", va="bottom")

    fig.tight_layout(rect=[0.06, 0.03, 0.98, 0.98])
    fig.savefig("sagin_architecture_diagram.png", dpi=400, bbox_inches="tight")
    fig.savefig("sagin_architecture_diagram.svg", bbox_inches="tight")


if __name__ == "__main__":
    main()
