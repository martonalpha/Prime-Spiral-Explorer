import os
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "assets" / "readme"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
MPL_CONFIG_DIR = ROOT / ".mplconfig"
MPL_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
os.environ["MPLCONFIGDIR"] = str(MPL_CONFIG_DIR)

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.cluster import DBSCAN


def sieve_of_eratosthenes(limit: int) -> np.ndarray:
    is_prime = np.ones(limit + 1, dtype=bool)
    is_prime[:2] = False
    for value in range(2, int(limit**0.5) + 1):
        if is_prime[value]:
            is_prime[value * value :: value] = False
    return is_prime


def semiprimes_up_to(limit: int, prime_values: np.ndarray) -> np.ndarray:
    semiprime_mask = np.zeros(limit + 1, dtype=bool)
    for index, left in enumerate(prime_values):
        if left * left > limit:
            break
        for right in prime_values[index:]:
            product = left * right
            if product > limit:
                break
            semiprime_mask[product] = True
    return np.where(semiprime_mask)[0]


def helix_coords(numbers: np.ndarray, tightness: float = 0.07) -> tuple[np.ndarray, np.ndarray]:
    theta = tightness * numbers
    radius = 1 + 0.008 * np.sqrt(numbers)
    x_values = radius * np.cos(theta)
    y_values = radius * np.sin(theta)
    return x_values, y_values


def helix_coords_3d(
    numbers: np.ndarray, tightness: float = 0.07, vertical_spacing: float = 0.3
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    theta = tightness * numbers
    radius = 1 + 0.008 * np.sqrt(numbers)
    x_values = radius * np.cos(theta)
    y_values = radius * np.sin(theta)
    z_values = vertical_spacing * theta
    return x_values, y_values, z_values


def ulam_xy(number: int) -> tuple[int, int]:
    if number == 0:
        return 0, 0
    shell = int(np.ceil((np.sqrt(number + 1) - 1) / 2))
    side = 2 * shell
    start = (2 * shell - 1) ** 2
    position = number - start
    if position < side:
        return shell - 1 - position, -shell
    if position < 2 * side:
        return -shell, -shell + (position - side + 1)
    if position < 3 * side:
        return -shell + (position - 2 * side + 1), shell
    return shell, shell - (position - 3 * side + 1)


def spherical_prime_map(numbers: np.ndarray, limit: int) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    golden = np.pi * (3 - np.sqrt(5))
    theta = golden * numbers
    latitude = 1 - 2 * numbers / limit
    radius = np.sqrt(1 - latitude**2)
    x_values = radius * np.cos(theta)
    y_values = radius * np.sin(theta)
    z_values = latitude
    return x_values, y_values, z_values


def style_axes(axis, title: str, subtitle: str) -> None:
    axis.set_facecolor("#090910")
    axis.figure.set_facecolor("#090910")
    for spine in axis.spines.values():
        spine.set_color("#202038")
    axis.tick_params(colors="#94a0be", labelsize=9)
    axis.grid(color="#1b1f33", linewidth=0.6, alpha=0.8)
    axis.set_title(title, loc="left", color="#f4f7ff", fontsize=18, pad=18, fontweight="bold")
    axis.text(
        0.0,
        1.01,
        subtitle,
        transform=axis.transAxes,
        color="#9aa7c7",
        fontsize=10,
        va="bottom",
    )


def save_helix_preview(primes: np.ndarray, semiprimes: np.ndarray) -> None:
    sample_primes = primes[primes <= 12_000]
    sample_semiprimes = semiprimes[semiprimes <= 12_000]
    prime_x, prime_y = helix_coords(sample_primes)
    semi_x, semi_y = helix_coords(sample_semiprimes)

    fig, axis = plt.subplots(figsize=(12, 8), dpi=180)
    style_axes(
        axis,
        "Helix Projection of Primes and Semiprimes",
        "Prime Spiral Explorer preview: green points are primes, coral points are semiprimes.",
    )
    axis.scatter(semi_x, semi_y, s=7, c="#ff6b5a", alpha=0.34, linewidths=0, label="Semiprimes")
    axis.scatter(prime_x, prime_y, s=9, c="#63f28d", alpha=0.78, linewidths=0, label="Primes")
    axis.set_xlabel("x", color="#b8c4df")
    axis.set_ylabel("y", color="#b8c4df")
    axis.set_aspect("equal", adjustable="box")
    legend = axis.legend(facecolor="#101525", edgecolor="#24304e", labelcolor="#dce5ff", loc="upper right")
    for text in legend.get_texts():
        text.set_color("#dce5ff")
    fig.tight_layout()
    fig.savefig(OUTPUT_DIR / "helix-preview.png", bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)


def save_ulam_preview(primes: np.ndarray, semiprimes: np.ndarray) -> None:
    sample_primes = primes[primes <= 8_000]
    sample_semiprimes = semiprimes[semiprimes <= 8_000]
    prime_coords = np.array([ulam_xy(int(value)) for value in sample_primes])
    semi_coords = np.array([ulam_xy(int(value)) for value in sample_semiprimes])

    fig, axis = plt.subplots(figsize=(12, 8), dpi=180)
    style_axes(
        axis,
        "Ulam-Style Grid Structure",
        "Prime diagonals and semiprime density become easier to compare in the square-spiral projection.",
    )
    axis.scatter(semi_coords[:, 0], semi_coords[:, 1], s=6, c="#ff8b61", alpha=0.26, linewidths=0, label="Semiprimes")
    axis.scatter(prime_coords[:, 0], prime_coords[:, 1], s=9, c="#56d4ff", alpha=0.82, linewidths=0, label="Primes")
    axis.set_xlabel("grid x", color="#b8c4df")
    axis.set_ylabel("grid y", color="#b8c4df")
    axis.set_aspect("equal", adjustable="box")
    legend = axis.legend(facecolor="#101525", edgecolor="#24304e", labelcolor="#dce5ff", loc="upper right")
    for text in legend.get_texts():
        text.set_color("#dce5ff")
    fig.tight_layout()
    fig.savefig(OUTPUT_DIR / "ulam-preview.png", bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)


def save_sphere_preview(primes: np.ndarray, semiprimes: np.ndarray) -> None:
    sample_primes = primes[primes <= 10_000]
    sample_semiprimes = semiprimes[semiprimes <= 10_000]
    prime_x, prime_y, prime_z = spherical_prime_map(sample_primes, 10_000)
    semi_x, semi_y, semi_z = spherical_prime_map(sample_semiprimes, 10_000)

    fig = plt.figure(figsize=(12, 8), dpi=180)
    axis = fig.add_subplot(111, projection="3d")
    fig.patch.set_facecolor("#090910")
    axis.set_facecolor("#090910")
    axis.set_title("Fibonacci Sphere Mapping", loc="left", color="#f4f7ff", fontsize=18, pad=18, fontweight="bold")
    axis.text2D(
        0.0,
        0.98,
        "Prime Spiral Explorer preview: values distributed on a sphere with golden-angle spacing.",
        transform=axis.transAxes,
        color="#9aa7c7",
        fontsize=10,
    )
    axis.scatter(semi_x, semi_y, semi_z, s=6, c="#ff8b61", alpha=0.22, depthshade=False, label="Semiprimes")
    axis.scatter(prime_x, prime_y, prime_z, s=8, c="#6df7a1", alpha=0.72, depthshade=False, label="Primes")
    axis.set_xlabel("x", color="#b8c4df")
    axis.set_ylabel("y", color="#b8c4df")
    axis.set_zlabel("z", color="#b8c4df")
    axis.tick_params(colors="#94a0be", labelsize=8)
    axis.xaxis.pane.set_facecolor((0.05, 0.06, 0.11, 1.0))
    axis.yaxis.pane.set_facecolor((0.05, 0.06, 0.11, 1.0))
    axis.zaxis.pane.set_facecolor((0.05, 0.06, 0.11, 1.0))
    axis.view_init(elev=18, azim=35)
    legend = axis.legend(facecolor="#101525", edgecolor="#24304e", labelcolor="#dce5ff", loc="upper right")
    for text in legend.get_texts():
        text.set_color("#dce5ff")
    fig.tight_layout()
    fig.savefig(OUTPUT_DIR / "sphere-preview.png", bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)


def save_modulo_preview(primes: np.ndarray) -> None:
    sample_primes = primes[primes <= 15_000]
    prime_x, prime_y = helix_coords(sample_primes)
    residues = sample_primes % 12

    fig, axis = plt.subplots(figsize=(12, 8), dpi=180)
    style_axes(
        axis,
        "Modulo View on the Helix",
        "Prime values colored by n mod 12 to expose repeating residue-class bands.",
    )
    scatter = axis.scatter(
        prime_x,
        prime_y,
        s=9,
        c=residues,
        cmap="turbo",
        alpha=0.82,
        linewidths=0,
    )
    axis.set_xlabel("x", color="#b8c4df")
    axis.set_ylabel("y", color="#b8c4df")
    axis.set_aspect("equal", adjustable="box")
    colorbar = fig.colorbar(scatter, ax=axis, pad=0.015)
    colorbar.set_label("n mod 12", color="#dce5ff")
    colorbar.ax.yaxis.set_tick_params(color="#94a0be")
    plt.setp(colorbar.ax.get_yticklabels(), color="#dce5ff")
    fig.tight_layout()
    fig.savefig(OUTPUT_DIR / "modulo-preview.png", bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)


def save_cluster_preview(primes: np.ndarray) -> None:
    sample_primes = primes[primes <= 5_000]
    x_values, y_values, z_values = helix_coords_3d(sample_primes)
    coords = np.column_stack([x_values, y_values, z_values])
    labels = DBSCAN(eps=1.5, min_samples=8, n_jobs=1).fit(coords).labels_
    visible_points = sample_primes <= 4_000

    fig, axis = plt.subplots(figsize=(12, 8), dpi=180)
    style_axes(
        axis,
        "DBSCAN Cluster View",
        "Clusters detected from the 3D helix coordinates and projected back into 2D for preview.",
    )
    axis.scatter(
        x_values[visible_points],
        y_values[visible_points],
        s=12,
        c=labels[visible_points],
        cmap="tab20",
        alpha=0.86,
        linewidths=0,
    )
    axis.set_xlabel("x", color="#b8c4df")
    axis.set_ylabel("y", color="#b8c4df")
    axis.set_aspect("equal", adjustable="box")
    fig.tight_layout()
    fig.savefig(OUTPUT_DIR / "cluster-preview.png", bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)


def main() -> None:
    limit = 20_000
    is_prime = sieve_of_eratosthenes(limit)
    primes = np.where(is_prime)[0]
    semiprimes = semiprimes_up_to(limit, primes)
    save_helix_preview(primes, semiprimes)
    save_ulam_preview(primes, semiprimes)
    save_sphere_preview(primes, semiprimes)
    save_modulo_preview(primes)
    save_cluster_preview(primes)


if __name__ == "__main__":
    main()
