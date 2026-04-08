"""
3D Prime Number Spiral Visualization
=====================================
Reveals hidden spatial patterns in prime distribution using 3D spiral mappings.

Requirements:
    pip install plotly numpy scikit-learn

Run:
    python main.py
"""

import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from plotly.offline import get_plotlyjs
from sklearn.cluster import DBSCAN
from sklearn.neighbors import NearestNeighbors
from pathlib import Path
import json
import webbrowser

# ─────────────────────────────────────────────
# 1. SIEVE OF ERATOSTHENES
# ─────────────────────────────────────────────

def sieve_of_eratosthenes(n):
    """
    Returns a boolean array `is_prime` of length n+1.
    is_prime[i] == True  →  i is prime.
    O(n log log n) time, O(n) space.
    """
    is_prime = np.ones(n + 1, dtype=bool)
    is_prime[0:2] = False                      # 0 and 1 are not prime
    for i in range(2, int(n**0.5) + 1):
        if is_prime[i]:
            is_prime[i*i::i] = False           # mark multiples as composite
    return is_prime


def semiprimes_up_to(n, prime_values):
    """
    Returns all semiprimes <= n together with one prime factorization a * b.
    A semiprime is a number that is the product of exactly two primes.
    """
    semiprime_mask = np.zeros(n + 1, dtype=bool)
    factor_a = np.zeros(n + 1, dtype=int)
    factor_b = np.zeros(n + 1, dtype=int)

    for i, p in enumerate(prime_values):
        if p * p > n:
            break
        for q in prime_values[i:]:
            product = p * q
            if product > n:
                break
            if not semiprime_mask[product]:
                semiprime_mask[product] = True
                factor_a[product] = p
                factor_b[product] = q

    semiprimes = np.where(semiprime_mask)[0]
    return semiprimes, factor_a[semiprimes], factor_b[semiprimes]


N = 100_000                                    # upper limit — raise if your machine is fast
is_prime = sieve_of_eratosthenes(N)
primes = np.where(is_prime)[0]                 # array of prime values
semiprimes, semiprime_a, semiprime_b = semiprimes_up_to(N, primes)
print(f"Found {len(primes)} primes up to {N:,}")
print(f"Found {len(semiprimes)} semiprimes up to {N:,}")


# ─────────────────────────────────────────────
# 2. SPIRAL COORDINATE MAPPINGS
# ─────────────────────────────────────────────

def helix_coords(numbers, tightness=0.07, vertical_spacing=0.3):
    """
    Maps each integer n to a 3D helix point.
      theta = tightness * n          (angle grows linearly with n)
      r     = 1 + 0.01 * sqrt(n)    (radius slowly expands → open spiral)
      x = r * cos(theta)
      y = r * sin(theta)
      z = vertical_spacing * theta
    """
    theta = tightness * numbers
    r = 1 + 0.008 * np.sqrt(numbers)
    x = r * np.cos(theta)
    y = r * np.sin(theta)
    z = vertical_spacing * theta
    return x, y, z


def ulam_xy(n):
    """
    Standard 2D Ulam spiral coordinates for integer n.
    """
    if n == 0:
        return 0, 0
    shell = int(np.ceil((np.sqrt(n + 1) - 1) / 2))
    side = 2 * shell
    start = (2 * shell - 1) ** 2
    pos = n - start
    if pos < side:
        x, y = shell - 1 - pos, -shell
    elif pos < 2 * side:
        x, y = -shell, -shell + (pos - side + 1)
    elif pos < 3 * side:
        x, y = -shell + (pos - 2 * side + 1), shell
    else:
        x, y = shell, shell - (pos - 3 * side + 1)
    return x, y


def ulam_helix_3d(numbers, layers=0.5):
    """
    Ulam-spiral-inspired 3D version:
    maps n on a square outward spiral in XY, then lifts it in Z by prime index.
    (visually shows the famous diagonal prime alignments in a 3D tower)
    """
    coords = np.array([ulam_xy(int(n)) for n in numbers])
    x = coords[:, 0].astype(float)
    y = coords[:, 1].astype(float)
    z = np.arange(len(numbers), dtype=float) * layers   # lift each prime up
    return x, y, z


def spherical_prime_map(numbers, N_total):
    """
    Distributes n on a sphere using the golden angle (Fibonacci lattice),
    so primes show up as scattered points on a sphere surface.
    phi = golden angle ≈ 137.5°
    """
    golden = np.pi * (3 - np.sqrt(5))          # golden angle in radians
    theta = golden * numbers                    # azimuthal angle
    # latitude: map n → [-1, 1]
    lat = 1 - 2 * numbers / N_total
    r = np.sqrt(1 - lat**2)
    x = r * np.cos(theta)
    y = r * np.sin(theta)
    z = lat
    return x, y, z


# ─────────────────────────────────────────────
# 3. COLOR ENCODING
# ─────────────────────────────────────────────

def prime_colors(primes):
    """
    Color by p mod 6 — primes > 3 must be 1 or 5 mod 6.
    This reveals the twin-prime and cousin-prime clustering visually.
    """
    return primes % 6


def prime_density_color(primes, window=500):
    """
    Local density: count primes in a sliding window of consecutive values.
    Higher density → brighter color.
    """
    density = np.zeros(len(primes))
    vals = primes
    for i, p in enumerate(vals):
        density[i] = np.sum((vals >= p - window) & (vals <= p + window))
    return density


# ─────────────────────────────────────────────
# 4. DBSCAN CLUSTERING (bonus)
# ─────────────────────────────────────────────

def find_clusters(x, y, z, eps=1.5, min_samples=8):
    """
    DBSCAN on 3D prime positions.
    Returns cluster labels (-1 = noise/outlier).
    """
    coords = np.column_stack([x, y, z])
    # Use a single worker for broad Windows compatibility in simple local runs.
    db = DBSCAN(eps=eps, min_samples=min_samples, n_jobs=1).fit(coords)
    return db.labels_


def density_by_layers(x, y, z, labels, z_bins=20, weights=None):
    """
    Summarize prime vs semiprime density by Z layer and XY quadrant.
    labels: 0 = prime, 1 = semiprime
    """
    z_min, z_max = z.min(), z.max()
    bins = np.linspace(z_min, z_max, z_bins + 1)
    results = []
    use_weights = weights is not None
    if not use_weights:
        weights = np.ones(len(z), dtype=float)
    else:
        weights = np.asarray(weights, dtype=float)

    for i in range(z_bins):
        if i == z_bins - 1:
            mask = (z >= bins[i]) & (z <= bins[i + 1])
        else:
            mask = (z >= bins[i]) & (z < bins[i + 1])

        if np.sum(mask) == 0:
            continue

        x_layer = x[mask]
        y_layer = y[mask]
        labels_layer = labels[mask]
        weight_layer = weights[mask]

        quadrants = [
            (x_layer > 0) & (y_layer > 0),
            (x_layer < 0) & (y_layer > 0),
            (x_layer < 0) & (y_layer < 0),
            (x_layer > 0) & (y_layer < 0),
        ]

        layer_data = []

        for quadrant_mask in quadrants:
            prime_mask = (labels_layer == 0) & quadrant_mask
            semiprime_mask = (labels_layer == 1) & quadrant_mask

            if use_weights:
                primes = float(np.sum(weight_layer[prime_mask]))
                semiprimes = float(np.sum(weight_layer[semiprime_mask]))
            else:
                primes = int(np.sum(prime_mask))
                semiprimes = int(np.sum(semiprime_mask))

            ratio = float(semiprimes / (primes + 1e-9))

            layer_data.append({
                "primes": primes,
                "semiprimes": semiprimes,
                "ratio": ratio,
            })

        results.append(layer_data)

    return results


def pure_ulam_validation_coords(numbers, z_mode="value"):
    """
    Validation coordinates on the exact Ulam grid.
    x and y stay untouched; only z chooses between value and index.
    """
    coords = np.array([ulam_xy(int(n)) for n in numbers])
    x = coords[:, 0].astype(float)
    y = coords[:, 1].astype(float)
    if z_mode == "index":
        z = np.arange(len(numbers), dtype=float)
    else:
        z = np.asarray(numbers, dtype=float)
    return x, y, z


def nearest_neighbor_distances(source_points, target_points):
    """
    Distance from each point in source_points to its nearest neighbor in target_points.
    """
    model = NearestNeighbors(n_neighbors=1, algorithm="auto")
    model.fit(target_points)
    distances, _ = model.kneighbors(source_points)
    return distances[:, 0]


def normalize_visual(values, low, high):
    """
    Normalize an array to a fixed visual range.
    """
    values = np.asarray(values, dtype=float)
    v_min = float(values.min())
    v_max = float(values.max())
    if np.isclose(v_min, v_max):
        return np.full(values.shape, (low + high) / 2, dtype=float)
    scaled = (values - v_min) / (v_max - v_min)
    return low + scaled * (high - low)


def build_layer_payload(layer_stats, quadrant_labels):
    """
    Convert layer/quadrant statistics into plot-friendly payload.
    """
    layer_numbers = []
    ratio_values = []
    prime_values = []
    semiprime_values = []
    heatmap_ratios = [[] for _ in range(len(quadrant_labels))]
    heatmap_text = [[] for _ in range(len(quadrant_labels))]

    for layer_index, layer_data in enumerate(layer_stats, start=1):
        total_primes = sum(item["primes"] for item in layer_data)
        total_semiprimes = sum(item["semiprimes"] for item in layer_data)
        total_ratio = total_semiprimes / (total_primes + 1e-9)

        layer_numbers.append(layer_index)
        ratio_values.append(float(total_ratio))
        prime_values.append(float(total_primes))
        semiprime_values.append(float(total_semiprimes))

        for quadrant_index, cell in enumerate(layer_data):
            heatmap_ratios[quadrant_index].append(float(cell["ratio"]))
            heatmap_text[quadrant_index].append(
                f"primes={cell['primes']:.3f}<br>semiprimes={cell['semiprimes']:.3f}"
            )

    return {
        "layers": layer_numbers,
        "overall_ratio": ratio_values,
        "overall_primes": prime_values,
        "overall_semiprimes": semiprime_values,
        "quadrants": quadrant_labels,
        "heatmap_ratio": heatmap_ratios,
        "heatmap_text": heatmap_text,
    }


def diagonal_expected_rates(all_x, all_y, prime_mask_all, semiprime_mask_all):
    """
    Expected prime/semiprime rates induced by the two Ulam diagonal families.
    """
    main_ids = (all_y - all_x).astype(int)
    anti_ids = (all_y + all_x).astype(int)

    _, main_inverse = np.unique(main_ids, return_inverse=True)
    _, anti_inverse = np.unique(anti_ids, return_inverse=True)

    total_main = np.bincount(main_inverse).astype(float)
    total_anti = np.bincount(anti_inverse).astype(float)

    prime_main = np.bincount(main_inverse, weights=prime_mask_all.astype(float)) / total_main
    prime_anti = np.bincount(anti_inverse, weights=prime_mask_all.astype(float)) / total_anti
    semiprime_main = np.bincount(main_inverse, weights=semiprime_mask_all.astype(float)) / total_main
    semiprime_anti = np.bincount(anti_inverse, weights=semiprime_mask_all.astype(float)) / total_anti

    expected_prime = 0.5 * (prime_main[main_inverse] + prime_anti[anti_inverse])
    expected_semiprime = 0.5 * (semiprime_main[main_inverse] + semiprime_anti[anti_inverse])

    return expected_prime, expected_semiprime


def normalized_residual_weights(expected_rates, global_rate, clip_low=0.25, clip_high=4.0):
    """
    Downweight points that lie on diagonals with unusually high expected density.
    """
    raw = global_rate / np.maximum(expected_rates, 1e-9)
    normalized = raw / np.mean(raw)
    return np.clip(normalized, clip_low, clip_high)


def distance_histogram_payload(
    real_prime_to_semiprime,
    real_semiprime_to_prime,
    random_prime_to_semiprime,
    random_semiprime_to_prime,
    prime_weights=None,
    semiprime_weights=None,
    bins=28,
):
    """
    Build histogram and average-distance payload for real vs random comparisons.
    """
    all_distances = np.concatenate([
        real_prime_to_semiprime,
        real_semiprime_to_prime,
        random_prime_to_semiprime,
        random_semiprime_to_prime,
    ])
    max_distance = float(np.max(all_distances)) if len(all_distances) else 1.0
    max_distance = max(max_distance, 1e-6)
    edges = np.linspace(0.0, max_distance, bins + 1)
    centers = 0.5 * (edges[:-1] + edges[1:])

    prime_weights = None if prime_weights is None else np.asarray(prime_weights, dtype=float)
    semiprime_weights = None if semiprime_weights is None else np.asarray(semiprime_weights, dtype=float)

    def histogram(values, weights):
        counts, _ = np.histogram(values, bins=edges, weights=weights, density=True)
        return counts.tolist()

    def average(values, weights):
        if weights is None:
            return float(np.mean(values))
        return float(np.average(values, weights=weights))

    real_prime_avg = average(real_prime_to_semiprime, prime_weights)
    real_semiprime_avg = average(real_semiprime_to_prime, semiprime_weights)
    random_prime_avg = average(random_prime_to_semiprime, prime_weights)
    random_semiprime_avg = average(random_semiprime_to_prime, semiprime_weights)

    anisotropy_reference = max(
        np.mean([
            real_prime_avg,
            real_semiprime_avg,
            random_prime_avg,
            random_semiprime_avg,
        ]),
        1e-9,
    )
    anisotropy_score = 0.0

    return {
        "bins": centers.tolist(),
        "real_prime_to_semiprime": histogram(real_prime_to_semiprime, prime_weights),
        "real_semiprime_to_prime": histogram(real_semiprime_to_prime, semiprime_weights),
        "random_prime_to_semiprime": histogram(random_prime_to_semiprime, prime_weights),
        "random_semiprime_to_prime": histogram(random_semiprime_to_prime, semiprime_weights),
        "comparison": {
            "labels": ["prime → semiprime", "semiprime → prime"],
            "real": [real_prime_avg, real_semiprime_avg],
            "random": [random_prime_avg, random_semiprime_avg],
        },
        "mean_distance_gap": float(
            ((real_prime_avg + real_semiprime_avg) - (random_prime_avg + random_semiprime_avg)) / 2.0
        ),
        "anisotropy_reference": anisotropy_reference,
        "anisotropy_score": anisotropy_score,
    }


# ─────────────────────────────────────────────
# 5. BUILD VISUALIZATION
# ─────────────────────────────────────────────

print("Computing coordinates …")

# --- Helix mapping (main view) ---
hx, hy, hz = helix_coords(primes, tightness=0.07, vertical_spacing=0.25)
shx, shy, shz = helix_coords(semiprimes, tightness=0.07, vertical_spacing=0.25)
all_numbers = np.arange(1, N + 1)
modulo_default_k = 12
mx, my, mz = helix_coords(all_numbers, tightness=0.07, vertical_spacing=0.25)
modulo_residues = all_numbers % modulo_default_k
modulo_customdata = np.column_stack([all_numbers, modulo_residues])
modulo_size = 1.6 + 1.0 / (1 + np.log10(all_numbers + 1))

# --- Ulam 3D (second view, use subset for speed) ---
prime_subset = primes[:3000]
ux, uy, uz = ulam_helix_3d(prime_subset)
ulam_limit = int(prime_subset[-1])
semiprime_subset_mask = semiprimes <= ulam_limit
semiprime_subset = semiprimes[semiprime_subset_mask]
semiprime_subset_a = semiprime_a[semiprime_subset_mask]
semiprime_subset_b = semiprime_b[semiprime_subset_mask]
sux, suy, suz = ulam_helix_3d(semiprime_subset)
ulam_layer_stats = density_by_layers(
    np.concatenate([ux, sux]),
    np.concatenate([uy, suy]),
    np.concatenate([uz, suz]),
    np.concatenate([
        np.zeros(len(ux), dtype=int),
        np.ones(len(sux), dtype=int),
    ]),
    z_bins=20,
)
ulam_quadrant_labels = [
    "Q1 (+x, +y)",
    "Q2 (-x, +y)",
    "Q3 (-x, -y)",
    "Q4 (+x, -y)",
]
ulam_layer_numbers = []
ulam_ratio_values = []
ulam_ratio_prime_counts = []
ulam_ratio_semiprime_counts = []
ulam_heatmap_ratios = [[] for _ in range(4)]
ulam_heatmap_text = [[] for _ in range(4)]

for layer_index, layer_data in enumerate(ulam_layer_stats, start=1):
    total_primes = sum(item["primes"] for item in layer_data)
    total_semiprimes = sum(item["semiprimes"] for item in layer_data)
    total_ratio = total_semiprimes / (total_primes + 1e-9)

    ulam_layer_numbers.append(layer_index)
    ulam_ratio_values.append(float(total_ratio))
    ulam_ratio_prime_counts.append(int(total_primes))
    ulam_ratio_semiprime_counts.append(int(total_semiprimes))

    for quadrant_index, cell in enumerate(layer_data):
        ulam_heatmap_ratios[quadrant_index].append(float(cell["ratio"]))
        ulam_heatmap_text[quadrant_index].append(
            f"primes={cell['primes']}<br>semiprimes={cell['semiprimes']}"
        )

ulam_density_payload = {
    "layers": ulam_layer_numbers,
    "overall_ratio": ulam_ratio_values,
    "overall_primes": ulam_ratio_prime_counts,
    "overall_semiprimes": ulam_ratio_semiprime_counts,
    "quadrants": ulam_quadrant_labels,
    "heatmap_ratio": ulam_heatmap_ratios,
    "heatmap_text": ulam_heatmap_text,
}

# --- Spherical map ---
sx, sy, sz = spherical_prime_map(primes, N)
ssx, ssy, ssz = spherical_prime_map(semiprimes, N)

# Size: smaller primes slightly larger (inverted log)
helix_size = 2.5 + 3.0 / (1 + np.log10(primes + 1))

print("Running DBSCAN clustering on helix …")
# Use a small subset for clustering demo (full set is slow)
cluster_limit = 5000
cluster_prime_values = primes[primes < cluster_limit]
cluster_semiprime_mask = semiprimes < cluster_limit
cluster_semiprime_values = semiprimes[cluster_semiprime_mask]
cluster_semiprime_a = semiprime_a[cluster_semiprime_mask]
cluster_semiprime_b = semiprime_b[cluster_semiprime_mask]

cluster_numbers = np.concatenate([cluster_prime_values, cluster_semiprime_values])
cluster_is_semiprime = np.concatenate([
    np.zeros(len(cluster_prime_values), dtype=bool),
    np.ones(len(cluster_semiprime_values), dtype=bool),
])
cluster_factor_a = np.concatenate([
    np.zeros(len(cluster_prime_values), dtype=int),
    cluster_semiprime_a,
])
cluster_factor_b = np.concatenate([
    np.zeros(len(cluster_prime_values), dtype=int),
    cluster_semiprime_b,
])

cluster_order = np.argsort(cluster_numbers)
cluster_numbers = cluster_numbers[cluster_order]
cluster_is_semiprime = cluster_is_semiprime[cluster_order]
cluster_factor_a = cluster_factor_a[cluster_order]
cluster_factor_b = cluster_factor_b[cluster_order]
cluster_prime_mask = ~cluster_is_semiprime
cluster_semiprime_mask_sorted = cluster_is_semiprime

chx, chy, chz = helix_coords(cluster_numbers, tightness=0.07, vertical_spacing=0.25)
labels = find_clusters(chx, chy, chz, eps=0.8, min_samples=5)
n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
print(f"  Found {n_clusters} clusters in values < {cluster_limit:,}")

zeta_term_count = 6000
zeta_t = 14.134725
zeta_n = np.arange(1, zeta_term_count + 1, dtype=float)
zeta_terms = np.exp(-(0.5 + 1j * zeta_t) * np.log(zeta_n))
zeta_partial = np.cumsum(zeta_terms)
zx = zeta_partial.real
zy = zeta_partial.imag
zz = np.log10(zeta_n)
zeta_customdata = np.column_stack([zeta_n.astype(int), np.abs(zeta_terms)])

vector_prime_values = primes[:4000]
vx, vy, vz = helix_coords(vector_prime_values, tightness=0.07, vertical_spacing=0.25)
vector_deltas = np.column_stack([np.diff(vx), np.diff(vy), np.diff(vz)])
vector_norms = np.linalg.norm(vector_deltas, axis=1)
vector_dirs = vector_deltas / vector_norms[:, None]
vector_gaps = np.diff(vector_prime_values)
vector_customdata = np.column_stack([
    vector_prime_values[:-1],
    vector_prime_values[1:],
    vector_gaps,
    vector_dirs,
])

# --- Pure Ulam validation mode (exact Ulam geometry + compensated analytics) ---
validation_quadrant_labels = [
    "Q1 (+x, +y)",
    "Q2 (-x, +y)",
    "Q3 (-x, -y)",
    "Q4 (+x, -y)",
]
validation_prime_numbers = prime_subset.astype(float)
validation_semiprime_numbers = semiprime_subset.astype(float)
vpx, vpy, vpz = pure_ulam_validation_coords(validation_prime_numbers, z_mode="value")
vsx, vsy, vsz = pure_ulam_validation_coords(validation_semiprime_numbers, z_mode="value")

validation_prime_weights = np.log(validation_prime_numbers)
validation_semiprime_weights = np.log(validation_semiprime_numbers) / np.log(np.log(validation_semiprime_numbers))

validation_prime_opacity = normalize_visual(validation_prime_weights, 0.42, 0.95)
validation_semiprime_opacity = normalize_visual(validation_semiprime_weights, 0.14, 0.78)
validation_prime_size = normalize_visual(validation_prime_weights, 2.1, 4.6)
validation_semiprime_size = normalize_visual(validation_semiprime_weights, 1.1, 3.1)

validation_downsample_rng = np.random.default_rng(42)
validation_downsample_size = min(len(validation_semiprime_numbers), len(validation_prime_numbers))
validation_downsample_indices = np.sort(
    validation_downsample_rng.choice(
        len(validation_semiprime_numbers),
        size=validation_downsample_size,
        replace=False,
    )
)

validation_prime_points = np.column_stack([vpx, vpy, vpz])
validation_semiprime_points = np.column_stack([vsx, vsy, vsz])
validation_semiprime_downsample_points = validation_semiprime_points[validation_downsample_indices]

validation_all_numbers = np.arange(2, ulam_limit + 1, dtype=int)
validation_grid_x, validation_grid_y, validation_grid_z = pure_ulam_validation_coords(validation_all_numbers, z_mode="value")
validation_grid_points = np.column_stack([validation_grid_x, validation_grid_y, validation_grid_z])
validation_prime_mask_all = np.isin(validation_all_numbers, prime_subset)
validation_semiprime_mask_all = np.isin(validation_all_numbers, semiprime_subset)
validation_expected_prime_all, validation_expected_semiprime_all = diagonal_expected_rates(
    validation_grid_x,
    validation_grid_y,
    validation_prime_mask_all,
    validation_semiprime_mask_all,
)
validation_global_prime_rate = float(np.mean(validation_prime_mask_all))
validation_global_semiprime_rate = float(np.mean(validation_semiprime_mask_all))
validation_prime_residual_weights = normalized_residual_weights(
    validation_expected_prime_all[validation_prime_mask_all],
    validation_global_prime_rate,
)
validation_semiprime_residual_weights = normalized_residual_weights(
    validation_expected_semiprime_all[validation_semiprime_mask_all],
    validation_global_semiprime_rate,
)
validation_random_rng = np.random.default_rng(314159)
validation_random_order = validation_random_rng.permutation(len(validation_grid_points))
validation_random_prime_indices = validation_random_order[:len(validation_prime_points)]
validation_random_semiprime_indices = validation_random_order[
    len(validation_prime_points):len(validation_prime_points) + len(validation_semiprime_points)
]
validation_random_semiprime_downsample_indices = validation_random_order[
    len(validation_prime_points):len(validation_prime_points) + len(validation_semiprime_downsample_points)
]
validation_random_prime_points = validation_grid_points[validation_random_prime_indices]
validation_random_semiprime_points = validation_grid_points[validation_random_semiprime_indices]
validation_random_semiprime_downsample_points = validation_grid_points[validation_random_semiprime_downsample_indices]
validation_random_prime_residual_weights = normalized_residual_weights(
    validation_expected_prime_all[validation_random_prime_indices],
    validation_global_prime_rate,
)
validation_random_semiprime_residual_weights = normalized_residual_weights(
    validation_expected_semiprime_all[validation_random_semiprime_indices],
    validation_global_semiprime_rate,
)

validation_real_prime_to_semiprime = nearest_neighbor_distances(
    validation_prime_points, validation_semiprime_points
)
validation_real_semiprime_to_prime = nearest_neighbor_distances(
    validation_semiprime_points, validation_prime_points
)
validation_real_prime_to_semiprime_downsample = nearest_neighbor_distances(
    validation_prime_points, validation_semiprime_downsample_points
)
validation_real_semiprime_downsample_to_prime = nearest_neighbor_distances(
    validation_semiprime_downsample_points, validation_prime_points
)

validation_random_prime_to_semiprime = nearest_neighbor_distances(
    validation_random_prime_points, validation_random_semiprime_points
)
validation_random_semiprime_to_prime = nearest_neighbor_distances(
    validation_random_semiprime_points, validation_random_prime_points
)
validation_random_prime_to_semiprime_downsample = nearest_neighbor_distances(
    validation_random_prime_points, validation_random_semiprime_downsample_points
)
validation_random_semiprime_downsample_to_prime = nearest_neighbor_distances(
    validation_random_semiprime_downsample_points, validation_random_prime_points
)

validation_labels = np.concatenate([
    np.zeros(len(validation_prime_points), dtype=int),
    np.ones(len(validation_semiprime_points), dtype=int),
])
validation_downsample_labels = np.concatenate([
    np.zeros(len(validation_prime_points), dtype=int),
    np.ones(len(validation_semiprime_downsample_points), dtype=int),
])

validation_layer_stats_downsample = density_by_layers(
    np.concatenate([vpx, vsx[validation_downsample_indices]]),
    np.concatenate([vpy, vsy[validation_downsample_indices]]),
    np.concatenate([vpz, vsz[validation_downsample_indices]]),
    validation_downsample_labels,
    z_bins=20,
)
validation_layer_stats_weighting = density_by_layers(
    np.concatenate([vpx, vsx]),
    np.concatenate([vpy, vsy]),
    np.concatenate([vpz, vsz]),
    validation_labels,
    z_bins=20,
    weights=np.concatenate([validation_prime_weights, validation_semiprime_weights]),
)

validation_analytics_payload = {
    "downsample": build_layer_payload(validation_layer_stats_downsample, validation_quadrant_labels),
    "weighting": build_layer_payload(validation_layer_stats_weighting, validation_quadrant_labels),
}
validation_analytics_payload["downsample"]["distance"] = distance_histogram_payload(
    validation_real_prime_to_semiprime_downsample,
    validation_real_semiprime_downsample_to_prime,
    validation_random_prime_to_semiprime_downsample,
    validation_random_semiprime_downsample_to_prime,
)
validation_analytics_payload["weighting"]["distance"] = distance_histogram_payload(
    validation_real_prime_to_semiprime,
    validation_real_semiprime_to_prime,
    validation_random_prime_to_semiprime,
    validation_random_semiprime_to_prime,
    prime_weights=validation_prime_weights,
    semiprime_weights=validation_semiprime_weights,
)
validation_layer_stats_residual = density_by_layers(
    np.concatenate([vpx, vsx]),
    np.concatenate([vpy, vsy]),
    np.concatenate([vpz, vsz]),
    validation_labels,
    z_bins=20,
    weights=np.concatenate([validation_prime_residual_weights, validation_semiprime_residual_weights]),
)
validation_analytics_payload["residual"] = build_layer_payload(
    validation_layer_stats_residual,
    validation_quadrant_labels,
)
validation_analytics_payload["residual"]["distance"] = distance_histogram_payload(
    validation_real_prime_to_semiprime,
    validation_real_semiprime_to_prime,
    validation_random_prime_to_semiprime,
    validation_random_semiprime_to_prime,
    prime_weights=validation_prime_residual_weights,
    semiprime_weights=validation_semiprime_residual_weights,
)
validation_prime_residual_opacity = normalize_visual(validation_prime_residual_weights, 0.28, 0.98)
validation_semiprime_residual_opacity = normalize_visual(validation_semiprime_residual_weights, 0.20, 0.92)
validation_prime_residual_size = normalize_visual(validation_prime_residual_weights, 1.8, 5.0)
validation_semiprime_residual_size = normalize_visual(validation_semiprime_residual_weights, 1.0, 3.6)

def diagonal_dominance_score(x_values, y_values):
    main_diagonals = (y_values - x_values).astype(int)
    anti_diagonals = (y_values + x_values).astype(int)
    main_counts = np.unique(main_diagonals, return_counts=True)[1]
    anti_counts = np.unique(anti_diagonals, return_counts=True)[1]
    return float(max(main_counts.max(), anti_counts.max()) / max(len(x_values), 1))

validation_diagonal_real = diagonal_dominance_score(vpx, vpy)
validation_diagonal_random = diagonal_dominance_score(
    validation_random_prime_points[:, 0], validation_random_prime_points[:, 1]
)

for method_key in ("downsample", "weighting", "residual"):
    quadrant_matrix = np.array(validation_analytics_payload[method_key]["heatmap_ratio"], dtype=float)
    mean_by_quadrant = quadrant_matrix.mean(axis=1)
    anisotropy = float(np.std(mean_by_quadrant) / (np.mean(mean_by_quadrant) + 1e-9))
    validation_analytics_payload[method_key]["anisotropy"] = anisotropy
    distance_block = validation_analytics_payload[method_key]["distance"]
    distance_gap = float(
        np.mean(distance_block["comparison"]["real"]) - np.mean(distance_block["comparison"]["random"])
    )
    validation_analytics_payload[method_key]["distance_gap"] = distance_gap
    if distance_gap <= 0.02 and anisotropy <= 0.08:
        verdict = "No new structure"
    else:
        verdict = "Possible structure"
    validation_analytics_payload[method_key]["verdict"] = verdict
    validation_analytics_payload[method_key]["diagonal_real"] = validation_diagonal_real
    validation_analytics_payload[method_key]["diagonal_random"] = validation_diagonal_random

validation_render_payload = {
    "downsample_semiprime_indices": validation_downsample_indices.tolist(),
    "prime_opacity": validation_prime_opacity.tolist(),
    "semiprime_opacity": validation_semiprime_opacity.tolist(),
    "prime_size": validation_prime_size.tolist(),
    "semiprime_size": validation_semiprime_size.tolist(),
    "prime_residual_weight": validation_prime_residual_weights.tolist(),
    "semiprime_residual_weight": validation_semiprime_residual_weights.tolist(),
    "prime_residual_opacity": validation_prime_residual_opacity.tolist(),
    "semiprime_residual_opacity": validation_semiprime_residual_opacity.tolist(),
    "prime_residual_size": validation_prime_residual_size.tolist(),
    "semiprime_residual_size": validation_semiprime_residual_size.tolist(),
}

# ─────────────────────────────────────────────
# 6. PLOTLY FIGURE — 3 TABS via buttons
# ─────────────────────────────────────────────

# We'll build traces and use updatemenus to toggle between views

# ── Trace 0: Helix ──
trace_helix = go.Scatter3d(
    x=hx, y=hy, z=hz,
    mode="markers",
    name="Helix spiral",
    marker=dict(
        size=helix_size,
        color="#39d353",
        opacity=0.85,
        line=dict(width=0),
    ),
    text=[f"p={p}" for p in primes],
    hovertemplate="<b>%{text}</b><br>x=%{x:.2f} y=%{y:.2f} z=%{z:.2f}<extra></extra>",
    visible=True,
)

# ── Trace 0b: Semiprimes overlaid on helix ──
trace_semiprimes = go.Scatter3d(
    x=shx, y=shy, z=shz,
    mode="markers",
    name="Semiprimes",
    marker=dict(
        size=2.2,
        color="#ff3b30",
        opacity=0.8,
        line=dict(width=0),
    ),
    text=[f"s={n} = {a} * {b}" for n, a, b in zip(semiprimes, semiprime_a, semiprime_b)],
    hovertemplate="<b>%{text}</b><br>x=%{x:.2f} y=%{y:.2f} z=%{z:.2f}<extra></extra>",
    visible=True,
)

# ── Trace 1: Ulam 3D tower ──
trace_ulam = go.Scatter3d(
    x=ux, y=uy, z=uz,
    mode="markers",
    name="Ulam 3D tower",
    marker=dict(
        size=3,
        color="#39d353",
        opacity=0.9,
        line=dict(width=0),
    ),
    text=[f"p={p}" for p in prime_subset],
    hovertemplate="<b>%{text}</b><extra></extra>",
    visible=False,
)

trace_ulam_semiprimes = go.Scatter3d(
    x=sux, y=suy, z=suz,
    mode="markers",
    name="Ulam semiprimes",
    marker=dict(
        size=2.6,
        color="#ff3b30",
        opacity=0.85,
        line=dict(width=0),
    ),
    text=[f"s={n} = {a} * {b}" for n, a, b in zip(semiprime_subset, semiprime_subset_a, semiprime_subset_b)],
    hovertemplate="<b>%{text}</b><extra></extra>",
    visible=False,
)

# ── Trace 2: Sphere ──
trace_sphere = go.Scatter3d(
    x=sx, y=sy, z=sz,
    mode="markers",
    name="Fibonacci sphere",
    marker=dict(
        size=1.8,
        color="#39d353",
        opacity=0.8,
        line=dict(width=0),
    ),
    text=[f"p={p}" for p in primes],
    hovertemplate="<b>%{text}</b><extra></extra>",
    visible=False,
)

trace_sphere_semiprimes = go.Scatter3d(
    x=ssx, y=ssy, z=ssz,
    mode="markers",
    name="Sphere semiprimes",
    marker=dict(
        size=1.6,
        color="#ff3b30",
        opacity=0.75,
        line=dict(width=0),
    ),
    text=[f"s={n} = {a} * {b}" for n, a, b in zip(semiprimes, semiprime_a, semiprime_b)],
    hovertemplate="<b>%{text}</b><extra></extra>",
    visible=False,
)

# ── Trace 3: Cluster highlight (helix, values < 5000) ──
trace_clusters_primes = go.Scatter3d(
    x=chx[cluster_prime_mask], y=chy[cluster_prime_mask], z=chz[cluster_prime_mask],
    mode="markers",
    name="Clustered primes",
    marker=dict(
        size=4,
        color="#39d353",
        opacity=0.9,
        line=dict(width=0),
    ),
    text=[f"p={n}  cluster={label}" for n, label in zip(cluster_numbers[cluster_prime_mask], labels[cluster_prime_mask])],
    hovertemplate="<b>%{text}</b><extra></extra>",
    visible=False,
)

trace_clusters_semiprimes = go.Scatter3d(
    x=chx[cluster_semiprime_mask_sorted], y=chy[cluster_semiprime_mask_sorted], z=chz[cluster_semiprime_mask_sorted],
    mode="markers",
    name="Clustered semiprimes",
    marker=dict(
        size=4,
        color="#ff3b30",
        opacity=0.9,
        line=dict(width=0),
    ),
    text=[
        f"s={n} = {a} * {b}  cluster={label}"
        for n, a, b, label in zip(
            cluster_numbers[cluster_semiprime_mask_sorted],
            cluster_factor_a[cluster_semiprime_mask_sorted],
            cluster_factor_b[cluster_semiprime_mask_sorted],
            labels[cluster_semiprime_mask_sorted],
        )
    ],
    hovertemplate="<b>%{text}</b><extra></extra>",
    visible=False,
)

trace_modulo = go.Scatter3d(
    x=mx, y=my, z=mz,
    mode="markers",
    name="Modulo view",
    marker=dict(
        size=modulo_size,
        color=modulo_residues,
        colorscale="Turbo",
        opacity=0.9,
        line=dict(width=0),
        cmin=0,
        cmax=modulo_default_k - 1,
        colorbar=dict(
            title=f"n mod {modulo_default_k}",
            thickness=12,
            len=0.5,
            x=1.02,
        ),
    ),
    customdata=modulo_customdata,
    hovertemplate="<b>n=%{customdata[0]}</b><br>n mod k = %{customdata[1]}<br>x=%{x:.2f} y=%{y:.2f} z=%{z:.2f}<extra></extra>",
    visible=False,
)

trace_zeta = go.Scatter3d(
    x=zx, y=zy, z=zz,
    mode="lines+markers",
    name="Zeta critical walk",
    line=dict(color="#59d5ff", width=3),
    marker=dict(
        size=2.8,
        color=np.angle(zeta_terms),
        colorscale="IceFire",
        opacity=0.85,
        line=dict(width=0),
    ),
    customdata=zeta_customdata,
    hovertemplate="<b>n=%{customdata[0]}</b><br>|n^(-s)|=%{customdata[1]:.4f}<br>Re=%{x:.4f}<br>Im=%{y:.4f}<br>log10(n)=%{z:.3f}<extra></extra>",
    visible=False,
)

trace_vectors = go.Scatter3d(
    x=vector_dirs[:, 0], y=vector_dirs[:, 1], z=vector_dirs[:, 2],
    mode="markers",
    name="Next-prime directions",
    marker=dict(
        size=3.4,
        color=vector_gaps,
        colorscale="Sunset",
        opacity=0.9,
        line=dict(width=0),
        colorbar=dict(
            title="prime gap",
            thickness=12,
            len=0.5,
            x=1.02,
        ),
    ),
    customdata=vector_customdata,
    hovertemplate="<b>p=%{customdata[0]} -> %{customdata[1]}</b><br>gap=%{customdata[2]}<br>dir=(%{customdata[3]:.3f}, %{customdata[4]:.3f}, %{customdata[5]:.3f})<extra></extra>",
    visible=False,
)

trace_validation_primes = go.Scatter3d(
    x=vpx, y=vpy, z=vpz,
    mode="markers",
    name="Pure Ulam primes",
    marker=dict(
        size=2.8,
        color="#39d353",
        opacity=0.9,
        line=dict(width=0),
    ),
    customdata=np.column_stack([validation_prime_numbers, validation_prime_weights]),
    hovertemplate="<b>p=%{customdata[0]:.0f}</b><br>Ulam z=%{z:.0f}<br>weight=%{customdata[1]:.3f}<extra></extra>",
    visible=False,
)

trace_validation_semiprimes = go.Scatter3d(
    x=vsx, y=vsy, z=vsz,
    mode="markers",
    name="Pure Ulam semiprimes",
    marker=dict(
        size=2.0,
        color="#ff3b30",
        opacity=0.78,
        line=dict(width=0),
    ),
    customdata=np.column_stack([validation_semiprime_numbers, validation_semiprime_weights]),
    hovertemplate="<b>s=%{customdata[0]:.0f}</b><br>Ulam z=%{z:.0f}<br>weight=%{customdata[1]:.3f}<extra></extra>",
    visible=False,
)

# ─────────────────────────────────────────────
# 7. ASSEMBLE FIGURE
# ─────────────────────────────────────────────

fig = go.Figure(
    data=[
        trace_helix,
        trace_semiprimes,
        trace_ulam,
        trace_ulam_semiprimes,
        trace_sphere,
        trace_sphere_semiprimes,
        trace_clusters_primes,
        trace_clusters_semiprimes,
        trace_modulo,
        trace_zeta,
        trace_vectors,
        trace_validation_primes,
        trace_validation_semiprimes,
    ]
)

view_configs = {
    "helix": {
        "trace_indices": [0, 1],
        "filterable": True,
        "titles": {
            "both": f"Helix spiral - {len(primes):,} primes in green, {len(semiprimes):,} semiprimes in red",
            "prime": f"Helix spiral - {len(primes):,} primes only",
            "semiprime": f"Helix spiral - {len(semiprimes):,} semiprimes only",
        },
    },
    "ulam": {
        "trace_indices": [2, 3],
        "filterable": True,
        "titles": {
            "both": f"Ulam 3D tower - primes in green, semiprimes in red up to {ulam_limit:,}",
            "prime": f"Ulam 3D tower - primes only up to {ulam_limit:,}",
            "semiprime": f"Ulam 3D tower - semiprimes only up to {ulam_limit:,}",
        },
    },
    "sphere": {
        "trace_indices": [4, 5],
        "filterable": True,
        "titles": {
            "both": f"Fibonacci sphere - primes in green, semiprimes in red up to {N:,}",
            "prime": f"Fibonacci sphere - primes only up to {N:,}",
            "semiprime": f"Fibonacci sphere - semiprimes only up to {N:,}",
        },
    },
    "cluster": {
        "trace_indices": [6, 7],
        "filterable": True,
        "titles": {
            "both": f"DBSCAN clustering - {n_clusters} clusters in values < {cluster_limit:,}",
            "prime": f"DBSCAN clustering - prime values only < {cluster_limit:,}",
            "semiprime": f"DBSCAN clustering - semiprime values only < {cluster_limit:,}",
        },
    },
    "modulo": {
        "trace_indices": [8],
        "filterable": False,
        "titles": {
            "both": f"Modulo helix - every number colored by n mod {modulo_default_k}",
            "prime": f"Modulo helix - every number colored by n mod {modulo_default_k}",
            "semiprime": f"Modulo helix - every number colored by n mod {modulo_default_k}",
        },
    },
    "zeta": {
        "trace_indices": [9],
        "filterable": False,
        "titles": {
            "both": f"Zeta critical walk - partial sums of n^(-s), s = 0.5 + {zeta_t}i",
            "prime": f"Zeta critical walk - partial sums of n^(-s), s = 0.5 + {zeta_t}i",
            "semiprime": f"Zeta critical walk - partial sums of n^(-s), s = 0.5 + {zeta_t}i",
        },
    },
    "vectors": {
        "trace_indices": [10],
        "filterable": False,
        "titles": {
            "both": "Vector directions - normalized direction to the next prime on the helix",
            "prime": "Vector directions - normalized direction to the next prime on the helix",
            "semiprime": "Vector directions - normalized direction to the next prime on the helix",
        },
    },
    "validation": {
        "trace_indices": [11, 12],
        "filterable": True,
        "titles": {
            "both": "Pure Ulam Validation Mode - exact Ulam geometry with density compensation",
            "prime": "Pure Ulam Validation Mode - primes only",
            "semiprime": "Pure Ulam Validation Mode - semiprimes only",
        },
    },
}

filter_configs = {
    "both": {"prime": True, "semiprime": True},
    "prime": {"prime": True, "semiprime": False},
    "semiprime": {"prime": False, "semiprime": True},
}

dark_bg = "#0d0d14"
axis_style = dict(
    backgroundcolor=dark_bg,
    gridcolor="#1e1e30",
    showbackground=True,
    zerolinecolor="#2a2a40",
    tickfont=dict(color="#888", size=9),
    title=dict(font=dict(color="#aaa", size=11)),
)

fig.update_layout(
    title=dict(
        text=view_configs["helix"]["titles"]["both"],
        font=dict(color="#e0e0ff", size=16, family="monospace"),
        x=0.5,
    ),
    paper_bgcolor=dark_bg,
    plot_bgcolor=dark_bg,
    scene=dict(
        xaxis={**axis_style, "title": "x"},
        yaxis={**axis_style, "title": "y"},
        zaxis={**axis_style, "title": "z"},
        bgcolor=dark_bg,
        domain=dict(x=[0.0, 1.0], y=[0.0, 1.0]),
        aspectmode="manual",
        aspectratio=dict(x=1.35, y=1.35, z=1.0),
        camera=dict(eye=dict(x=1.0, y=1.0, z=0.52)),
    ),
    legend=dict(
        font=dict(color="#ccc"),
        bgcolor="rgba(0,0,0,0)",
        bordercolor="#333",
        borderwidth=0.5,
    ),
    autosize=True,
    margin=dict(l=0, r=0, t=28, b=0),
)

# ─────────────────────────────────────────────
# 8. LAUNCH
# ─────────────────────────────────────────────

print("Launching interactive visualization …")
print("  - Drag: rotate")
print("  - Scroll: zoom")
print("  - Use the controls above the plot to switch view, filter, modulo, and validation mode")
print("  - Hover any point to see its prime value")
output_file = Path(__file__).parent / "docs" / "index.html"
plotly_js = get_plotlyjs()
figure_json = fig.to_json()
plot_config_json = json.dumps({"responsive": True, "displaylogo": False})
trace_indices_json = json.dumps(list(range(len(fig.data))))
view_configs_json = json.dumps(view_configs)
filter_configs_json = json.dumps(filter_configs)
ulam_density_json = json.dumps(ulam_density_payload, separators=(",", ":"))
validation_analytics_json = json.dumps(validation_analytics_payload, separators=(",", ":"))
validation_render_json = json.dumps(validation_render_payload, separators=(",", ":"))

html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Prime Spiral Explorer | Interactive 3D Prime Visualization</title>
  <meta name="description" content="Explore prime numbers and semiprimes across helix, Ulam, spherical, cluster, and analytical views in a self-contained 3D visualization.">
  <meta name="robots" content="index,follow">
  <meta name="theme-color" content="#0d0d14">
  <meta property="og:type" content="website">
  <meta property="og:title" content="Prime Spiral Explorer">
  <meta property="og:description" content="Interactive 3D prime number and semiprime visualization with multiple mathematical views and validation analytics.">
  <meta property="og:image:alt" content="Prime Spiral Explorer interactive visualization">
  <meta name="twitter:card" content="summary">
  <meta name="twitter:title" content="Prime Spiral Explorer">
  <meta name="twitter:description" content="Interactive 3D visualization of prime and semiprime structure across multiple spatial mappings.">
  <script type="application/ld+json">
    {{
      "@context": "https://schema.org",
      "@type": "WebPage",
      "name": "Prime Spiral Explorer",
      "description": "Interactive 3D visualization of prime and semiprime structure across helix, Ulam, spherical, clustering, and validation views.",
      "about": ["Prime numbers", "Semiprimes", "Ulam spiral", "Number theory", "Data visualization"]
    }}
  </script>
  <style>
    body {{
      margin: 0;
      background: {dark_bg};
      color: #ddd;
      font-family: Consolas, "Courier New", monospace;
      overflow-x: hidden;
    }}
    .intro {{
      max-width: 1100px;
      margin: 0 auto;
      padding: 40px 24px 20px;
      box-sizing: border-box;
    }}
    .eyebrow {{
      margin: 0 0 10px;
      color: #59d5ff;
      text-transform: uppercase;
      letter-spacing: 0.12em;
      font-size: 12px;
    }}
    h1 {{
      margin: 0;
      font-size: clamp(32px, 5vw, 58px);
      line-height: 1.02;
      color: #f5f7ff;
    }}
    .intro p {{
      max-width: 860px;
      margin: 16px 0 0;
      color: #aeb6ca;
      line-height: 1.7;
      font-size: 15px;
    }}
    .intro strong {{
      color: #f5f7ff;
    }}
    .page {{
      width: min(1400px, calc(100vw - 32px));
      height: min(78vh, 920px);
      min-height: 760px;
      padding: 0;
      box-sizing: border-box;
      position: relative;
      overflow: hidden;
      margin: 0 auto 24px;
      border: 1px solid #1e1e30;
      border-radius: 20px;
      background: #090910;
      box-shadow: 0 24px 80px rgba(0, 0, 0, 0.35);
    }}
    .controls {{
      display: flex;
      flex-wrap: wrap;
      gap: 16px;
      align-items: center;
      justify-content: center;
      position: absolute;
      top: 0;
      left: 0;
      right: 0;
      padding: 10px 12px 8px;
      box-sizing: border-box;
      background: rgba(13, 13, 20, 0.92);
      backdrop-filter: blur(10px);
      z-index: 9999;
      pointer-events: auto;
    }}
    .control-group {{
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      align-items: center;
      justify-content: center;
    }}
    .hidden-control {{
      display: none;
    }}
    .control-label {{
      color: #9aa0b3;
      font-size: 13px;
      margin-right: 4px;
    }}
    button {{
      background: #1a1a2e;
      color: #ddd;
      border: 1px solid #555;
      border-radius: 8px;
      padding: 8px 12px;
      cursor: pointer;
      font: inherit;
      pointer-events: auto;
    }}
    button.active {{
      background: #2a7f62;
      border-color: #39d353;
      color: #fff;
    }}
    button[data-filter="semiprime"].active {{
      background: #8a2d2a;
      border-color: #ff3b30;
    }}
    button:disabled,
    input:disabled {{
      opacity: 0.45;
      cursor: not-allowed;
    }}
    input[type="range"] {{
      width: 180px;
      accent-color: #59d5ff;
    }}
    .range-value {{
      min-width: 28px;
      text-align: right;
      color: #59d5ff;
      font-weight: 700;
    }}
    #plot-shell {{
      position: absolute;
      left: 0;
      right: 0;
      bottom: 0;
      top: 0;
      min-height: 0;
      z-index: 1;
    }}
    #prime-plot {{
      width: 100%;
      height: 100%;
      position: relative;
      min-height: 0;
    }}
    .js-plotly-plot,
    .plotly,
    #prime-plot .plot-container,
    #prime-plot .svg-container,
    #prime-plot .main-svg {{
      width: 100% !important;
      height: 100% !important;
    }}
    #ulam-analytics {{
      position: absolute;
      left: 12px;
      right: 12px;
      bottom: 12px;
      display: none;
      gap: 12px;
      grid-template-columns: minmax(0, 1.05fr) minmax(0, 0.95fr);
      z-index: 2;
    }}
    .analysis-plot {{
      min-height: 0;
      border: 1px solid #1e1e30;
      border-radius: 12px;
      overflow: hidden;
      background: #10101a;
    }}
    @media (max-width: 1100px) {{
      #ulam-analytics {{    
        grid-template-columns: 1fr;
        grid-template-rows: 1fr 1fr;
      }}
    }}
    #validation-analytics {{
      position: absolute;
      left: 12px;
      right: 12px;
      bottom: 12px;
      display: none;
      gap: 12px;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      grid-template-rows: repeat(2, minmax(0, 1fr));
      z-index: 2;
    }}
    @media (max-width: 1100px) {{
      #validation-analytics {{
        grid-template-columns: 1fr;
        grid-template-rows: repeat(4, minmax(0, 1fr));
      }}
    }}
    .notes {{
      max-width: 1100px;
      margin: 0 auto;
      padding: 0 24px 40px;
      box-sizing: border-box;
    }}
    .notes h2 {{
      margin: 0 0 12px;
      color: #f5f7ff;
      font-size: 20px;
    }}
    .notes p {{
      margin: 0 0 14px;
      color: #aeb6ca;
      line-height: 1.7;
      font-size: 15px;
    }}
    .noscript {{
      max-width: 1100px;
      margin: 0 auto 20px;
      padding: 0 24px;
      color: #ffb4a8;
      box-sizing: border-box;
    }}
  </style>
</head>
<body>
  <header class="intro">
    <p class="eyebrow">Public math and data visualization project</p>
    <h1>Prime Spiral Explorer</h1>
    <p>
      An interactive 3D study of <strong>prime numbers</strong> and <strong>semiprimes</strong> across helix, Ulam-inspired, spherical, clustering, modulo, and validation views.
      This page is designed as a self-contained showcase that works directly from GitHub Pages without a backend.
    </p>
  </header>
  <noscript class="noscript">
    JavaScript is required to render the interactive Plotly visualization on this page.
  </noscript>
  <div class="page">
    <div class="controls" id="controls">
        <div class="control-group">
          <span class="control-label">View</span>
          <button type="button" data-view="helix" onclick="window.setView('helix')">Helix</button>
          <button type="button" data-view="ulam" onclick="window.setView('ulam')">Ulam 3D tower</button>
          <button type="button" data-view="sphere" onclick="window.setView('sphere')">Fibonacci sphere</button>
          <button type="button" data-view="cluster" onclick="window.setView('cluster')">DBSCAN clusters</button>
          <button type="button" data-view="modulo" onclick="window.setView('modulo')">Modulo</button>
          <button type="button" data-view="zeta" onclick="window.setView('zeta')">Zeta mapping</button>
          <button type="button" data-view="vectors" onclick="window.setView('vectors')">Vector directions</button>
          <button type="button" data-view="validation" onclick="window.setView('validation')">Pure Ulam validation</button>
        </div>
        <div class="control-group">
          <span class="control-label">Filter</span>
          <button type="button" data-filter="both" onclick="window.setFilter('both')">Both</button>
          <button type="button" data-filter="prime" onclick="window.setFilter('prime')">Prime only</button>
          <button type="button" data-filter="semiprime" onclick="window.setFilter('semiprime')">Semiprime only</button>
        </div>
        <div class="control-group" data-validation-control-group="true">
          <span class="control-label">Validation</span>
          <button type="button" data-validation-mode="downsample" onclick="window.setValidationMode('downsample')">Downsample</button>
          <button type="button" data-validation-mode="weighting" onclick="window.setValidationMode('weighting')">Weighting</button>
          <button type="button" data-validation-mode="residual" onclick="window.setValidationMode('residual')">Residual</button>
        </div>
        <div class="control-group" data-validation-control-group="true">
          <span class="control-label">Weight channel</span>
          <button type="button" data-weight-channel="opacity" onclick="window.setWeightChannel('opacity')">Opacity</button>
          <button type="button" data-weight-channel="size" onclick="window.setWeightChannel('size')">Size</button>
        </div>
        <div class="control-group">
          <span class="control-label">Modulo k</span>
          <input id="modulo-k" type="range" min="2" max="36" step="1" value="{modulo_default_k}" oninput="window.setModulo(this.value)">
          <span class="range-value" id="modulo-k-value">{modulo_default_k}</span>
        </div>
    </div>
    <div id="plot-shell">
      <div id="prime-plot"></div>
    </div>
    <div id="ulam-analytics">
      <div id="ulam-ratio-plot" class="analysis-plot"></div>
      <div id="ulam-heatmap-plot" class="analysis-plot"></div>
    </div>
    <div id="validation-analytics">
      <div id="validation-ratio-plot" class="analysis-plot"></div>
      <div id="validation-distance-plot" class="analysis-plot"></div>
      <div id="validation-baseline-plot" class="analysis-plot"></div>
      <div id="validation-heatmap-plot" class="analysis-plot"></div>
    </div>
  </div>
  <section class="notes">
    <h2>What this project shows</h2>
    <p>
      The visualization maps large prime sets into multiple geometric systems to reveal repeating structure, density shifts, residue class behavior, and semiprime relationships that are difficult to notice in raw tables.
    </p>
    <p>
      Because the page is fully static, it can be versioned in Git, published with GitHub Pages, shared in a portfolio, and opened locally without any server setup.
    </p>
  </section>
  <script>
{plotly_js}
  </script>
  <script>
    const figure = {figure_json};
    const plotConfig = {plot_config_json};
    const plotDiv = document.getElementById("prime-plot");
    const plotShell = document.getElementById("plot-shell");
    const controlsDiv = document.getElementById("controls");
    const ulamAnalyticsDiv = document.getElementById("ulam-analytics");
    const ulamRatioDiv = document.getElementById("ulam-ratio-plot");
    const ulamHeatmapDiv = document.getElementById("ulam-heatmap-plot");
    const validationAnalyticsDiv = document.getElementById("validation-analytics");
    const validationRatioDiv = document.getElementById("validation-ratio-plot");
    const validationDistanceDiv = document.getElementById("validation-distance-plot");
    const validationBaselineDiv = document.getElementById("validation-baseline-plot");
    const validationHeatmapDiv = document.getElementById("validation-heatmap-plot");
    const moduloInput = document.getElementById("modulo-k");
    const moduloValue = document.getElementById("modulo-k-value");
    const traceIndices = {trace_indices_json};
    const viewConfigs = {view_configs_json};
    const filterConfigs = {filter_configs_json};
    const ulamDensity = {ulam_density_json};
    const validationAnalytics = {validation_analytics_json};
    const validationRender = {validation_render_json};
    const baseData = figure.data;
    const baseLayout = figure.layout;
    const analysisPlotConfig = {{
      responsive: true,
      displaylogo: false,
      displayModeBar: false,
    }};
    let currentView = "helix";
    let currentFilter = "both";
    let currentModulo = {modulo_default_k};
    let currentValidationMode = "downsample";
    let currentWeightChannel = "opacity";
    let moduloTimer = null;
    let moduloNumbers = [];
    let renderChain = Promise.resolve();

    function ulamAnalyticsEnabled() {{
      return currentView === "ulam";
    }}

    function validationAnalyticsEnabled() {{
      return currentView === "validation";
    }}

    function validationModeEnabled() {{
      return currentView === "validation";
    }}

    function weightChannelEnabled() {{
      return currentView === "validation" && (currentValidationMode === "weighting" || currentValidationMode === "residual");
    }}

    function analyticsMode() {{
      if (validationAnalyticsEnabled()) {{
        return "validation";
      }}
      if (ulamAnalyticsEnabled()) {{
        return "ulam";
      }}
      return "none";
    }}

    function analyticsHeight() {{
      const mode = analyticsMode();
      if (mode === "none") {{
        return 0;
      }}
      if (mode === "validation") {{
        if (window.innerWidth < 1100) {{
          return Math.min(760, Math.max(520, Math.floor(window.innerHeight * 0.60)));
        }}
        return Math.min(560, Math.max(380, Math.floor(window.innerHeight * 0.46)));
      }}
      if (window.innerWidth < 1100) {{
        return Math.min(420, Math.max(320, Math.floor(window.innerHeight * 0.42)));
      }}
      return Math.min(320, Math.max(240, Math.floor(window.innerHeight * 0.30)));
    }}

    function syncLayoutBounds() {{
      const controlsHeight = controlsDiv.getBoundingClientRect().height;
      const analyticsSpace = analyticsHeight();
      const gap = analyticsSpace > 0 ? 12 : 0;
      const plotHeight = Math.max(420, window.innerHeight - controlsHeight - analyticsSpace - gap);
      plotShell.style.top = `${{controlsHeight}}px`;
      plotShell.style.bottom = "auto";
      plotShell.style.height = `${{plotHeight}}px`;
      ulamAnalyticsDiv.style.display = ulamAnalyticsEnabled() ? "grid" : "none";
      validationAnalyticsDiv.style.display = validationAnalyticsEnabled() ? "grid" : "none";
      if (ulamAnalyticsEnabled()) {{
        ulamAnalyticsDiv.style.height = `${{analyticsSpace}}px`;
      }}
      if (validationAnalyticsEnabled()) {{
        validationAnalyticsDiv.style.height = `${{analyticsSpace}}px`;
      }}
    }}

    function availablePlotHeight() {{
      return Math.max(420, plotShell.getBoundingClientRect().height);
    }}

    function currentTitle() {{
      if (currentView === "modulo") {{
        return `Modulo helix - every number colored by n mod ${{currentModulo}}`;
      }}
      if (currentView === "validation") {{
        let tail = "density-balanced by downsampling";
        if (currentValidationMode === "weighting") {{
          tail = `weighted by ${{currentWeightChannel}}`;
        }} else if (currentValidationMode === "residual") {{
          tail = `diagonal-adjusted residuals via ${{currentWeightChannel}}`;
        }}
        return `Pure Ulam Validation Mode - exact Ulam geometry, ${{tail}}`;
      }}
      return viewConfigs[currentView].titles[currentFilter];
    }}

    function deepClone(value) {{
      return JSON.parse(JSON.stringify(value));
    }}

    function activeVisibility() {{
      const visible = new Array(traceIndices.length).fill(false);
      const config = viewConfigs[currentView];
      if (config.filterable) {{
        const tracePair = config.trace_indices;
        visible[tracePair[0]] = filterConfigs[currentFilter].prime;
        visible[tracePair[1]] = filterConfigs[currentFilter].semiprime;
      }} else {{
        config.trace_indices.forEach((traceIndex) => {{
          visible[traceIndex] = true;
        }});
      }}
      return visible;
    }}

    function setActiveButtons() {{
      document.querySelectorAll("[data-view]").forEach((button) => {{
        button.classList.toggle("active", button.dataset.view === currentView);
      }});
      document.querySelectorAll("[data-filter]").forEach((button) => {{
        button.classList.toggle("active", button.dataset.filter === currentFilter);
        button.disabled = !viewConfigs[currentView].filterable;
      }});
      document.querySelectorAll("[data-validation-mode]").forEach((button) => {{
        button.classList.toggle("active", button.dataset.validationMode === currentValidationMode);
        button.disabled = !validationModeEnabled();
      }});
      document.querySelectorAll("[data-weight-channel]").forEach((button) => {{
        button.classList.toggle("active", button.dataset.weightChannel === currentWeightChannel);
        button.disabled = !weightChannelEnabled();
      }});
      document.querySelectorAll("[data-validation-control-group='true']").forEach((element) => {{
        element.classList.toggle("hidden-control", !validationModeEnabled());
      }});
      moduloInput.disabled = currentView !== "modulo";
    }}

    function rgbaList(kind, alphaValues) {{
      const rgb = kind === "prime" ? [57, 211, 83] : [255, 59, 48];
      return alphaValues.map((alpha) => `rgba(${{rgb[0]}}, ${{rgb[1]}}, ${{rgb[2]}}, ${{Number(alpha).toFixed(4)}})`);
    }}

    function applyModuloData(nextData) {{
      const moduloTraceIndex = viewConfigs.modulo.trace_indices[0];
      const residues = moduloNumbers.map((n) => n % currentModulo);
      const trace = nextData[moduloTraceIndex];
      trace.marker.color = residues;
      trace.marker.cmin = 0;
      trace.marker.cmax = Math.max(1, currentModulo - 1);
      trace.marker.colorbar = trace.marker.colorbar || {{}};
      trace.marker.colorbar.title = trace.marker.colorbar.title || {{}};
      trace.marker.colorbar.title.text = `n mod ${{currentModulo}}`;
      trace.customdata = moduloNumbers.map((n, index) => [n, residues[index]]);
    }}

    function sliceTrace(trace, sourceTrace, indices) {{
      trace.x = indices.map((index) => sourceTrace.x[index]);
      trace.y = indices.map((index) => sourceTrace.y[index]);
      trace.z = indices.map((index) => sourceTrace.z[index]);
      if (sourceTrace.customdata) {{
        trace.customdata = indices.map((index) => sourceTrace.customdata[index]);
      }}
      if (sourceTrace.text) {{
        trace.text = indices.map((index) => sourceTrace.text[index]);
      }}
    }}

    function applyValidationData(nextData) {{
      if (!validationAnalyticsEnabled()) {{
        return;
      }}

      const [primeTraceIndex, semiprimeTraceIndex] = viewConfigs.validation.trace_indices;
      const primeTrace = nextData[primeTraceIndex];
      const semiprimeTrace = nextData[semiprimeTraceIndex];
      const basePrimeTrace = baseData[primeTraceIndex];
      const baseSemiprimeTrace = baseData[semiprimeTraceIndex];

      if (currentValidationMode === "downsample") {{
        sliceTrace(semiprimeTrace, baseSemiprimeTrace, validationRender.downsample_semiprime_indices);
        primeTrace.marker.size = 2.8;
        primeTrace.marker.color = "#39d353";
        primeTrace.marker.opacity = 0.9;
        semiprimeTrace.marker.size = 2.0;
        semiprimeTrace.marker.color = "#ff3b30";
        semiprimeTrace.marker.opacity = 0.78;
        return;
      }}

      if (currentValidationMode === "residual" && currentWeightChannel === "size") {{
        primeTrace.marker.size = validationRender.prime_residual_size;
        semiprimeTrace.marker.size = validationRender.semiprime_residual_size;
        primeTrace.marker.color = "#39d353";
        semiprimeTrace.marker.color = "#ff3b30";
        primeTrace.marker.opacity = 0.94;
        semiprimeTrace.marker.opacity = 0.84;
      }} else if (currentValidationMode === "residual") {{
        primeTrace.marker.size = 2.8;
        semiprimeTrace.marker.size = 2.0;
        primeTrace.marker.color = rgbaList("prime", validationRender.prime_residual_opacity);
        semiprimeTrace.marker.color = rgbaList("semiprime", validationRender.semiprime_residual_opacity);
        primeTrace.marker.opacity = 1.0;
        semiprimeTrace.marker.opacity = 1.0;
      }} else if (currentWeightChannel === "size") {{
        primeTrace.marker.size = validationRender.prime_size;
        semiprimeTrace.marker.size = validationRender.semiprime_size;
        primeTrace.marker.color = "#39d353";
        semiprimeTrace.marker.color = "#ff3b30";
        primeTrace.marker.opacity = 0.92;
        semiprimeTrace.marker.opacity = 0.82;
      }} else {{
        primeTrace.marker.size = 2.8;
        semiprimeTrace.marker.size = 2.0;
        primeTrace.marker.color = rgbaList("prime", validationRender.prime_opacity);
        semiprimeTrace.marker.color = rgbaList("semiprime", validationRender.semiprime_opacity);
        primeTrace.marker.opacity = 1.0;
        semiprimeTrace.marker.opacity = 1.0;
      }}
    }}

    function buildData() {{
      const visible = activeVisibility();
      const nextData = baseData.map((trace, index) => {{
        const clonedTrace = deepClone(trace);
        clonedTrace.visible = visible[index];
        return clonedTrace;
      }});

      applyModuloData(nextData);
      applyValidationData(nextData);
      return nextData;
    }}

    function buildLayout() {{
      const layout = deepClone(baseLayout);
      layout.title = layout.title || {{}};
      layout.title.text = currentTitle();
      layout.height = availablePlotHeight();
      layout.autosize = true;
      return layout;
    }}

    function renderPlot() {{
      syncLayoutBounds();
      const height = availablePlotHeight();
      plotDiv.style.height = `${{height}}px`;
      plotDiv.style.minHeight = `${{height}}px`;
      const nextData = buildData();
      const nextLayout = buildLayout();
      return Plotly.react(plotDiv, nextData, nextLayout, plotConfig).then(() => {{
        Plotly.Plots.resize(plotDiv);
      }});
    }}

    function renderUlamAnalytics() {{
      if (!ulamAnalyticsEnabled()) {{
        return Promise.resolve();
      }}

      const ratioData = [{{
        x: ulamDensity.layers,
        y: ulamDensity.overall_ratio,
        mode: "lines+markers",
        type: "scatter",
        line: {{ color: "#59d5ff", width: 2.5 }},
        marker: {{ color: "#59d5ff", size: 6 }},
        customdata: ulamDensity.layers.map((_, index) => [
          ulamDensity.overall_primes[index],
          ulamDensity.overall_semiprimes[index],
        ]),
        hovertemplate: "<b>layer=%{{x}}</b><br>semiprime/prime=%{{y:.3f}}<br>primes=%{{customdata[0]}}<br>semiprimes=%{{customdata[1]}}<extra></extra>",
      }}];

      const ratioLayout = {{
        title: {{
          text: "Z vs ratio",
          font: {{ color: "#e0e0ff", size: 14, family: "monospace" }},
        }},
        paper_bgcolor: "{dark_bg}",
        plot_bgcolor: "{dark_bg}",
        margin: {{ l: 58, r: 16, t: 42, b: 44 }},
        xaxis: {{
          title: "layer",
          gridcolor: "#1e1e30",
          zerolinecolor: "#2a2a40",
          color: "#b7bfd8",
        }},
        yaxis: {{
          title: "semiprime / prime",
          gridcolor: "#1e1e30",
          zerolinecolor: "#2a2a40",
          color: "#b7bfd8",
        }},
      }};

      const heatmapData = [{{
        x: ulamDensity.layers,
        y: ulamDensity.quadrants,
        z: ulamDensity.heatmap_ratio,
        text: ulamDensity.heatmap_text,
        type: "heatmap",
        colorscale: "Turbo",
        hovertemplate: "<b>%{{y}}</b><br>layer=%{{x}}<br>semiprime/prime=%{{z:.3f}}<br>%{{text}}<extra></extra>",
        colorbar: {{
          title: "ratio",
          thickness: 10,
          len: 0.72,
        }},
      }}];

      const heatmapLayout = {{
        title: {{
          text: "Quadrant heatmap",
          font: {{ color: "#e0e0ff", size: 14, family: "monospace" }},
        }},
        paper_bgcolor: "{dark_bg}",
        plot_bgcolor: "{dark_bg}",
        margin: {{ l: 76, r: 22, t: 42, b: 44 }},
        xaxis: {{
          title: "layer",
          gridcolor: "#1e1e30",
          zerolinecolor: "#2a2a40",
          color: "#b7bfd8",
        }},
        yaxis: {{
          title: "quadrant",
          color: "#b7bfd8",
        }},
      }};

      return Promise.all([
        Plotly.react(ulamRatioDiv, ratioData, ratioLayout, analysisPlotConfig),
        Plotly.react(ulamHeatmapDiv, heatmapData, heatmapLayout, analysisPlotConfig),
      ]);
    }}

    function renderValidationAnalytics() {{
      if (!validationAnalyticsEnabled()) {{
        return Promise.resolve();
      }}

      const analytics = validationAnalytics[currentValidationMode];
      const distance = analytics.distance;

      const ratioData = [{{
        x: analytics.layers,
        y: analytics.overall_ratio,
        mode: "lines+markers",
        type: "scatter",
        line: {{ color: "#9dff8a", width: 2.5 }},
        marker: {{ color: "#9dff8a", size: 6 }},
        customdata: analytics.layers.map((_, index) => [
          analytics.overall_primes[index],
          analytics.overall_semiprimes[index],
        ]),
        hovertemplate: "<b>layer=%{{x}}</b><br>ratio=%{{y:.3f}}<br>prime mass=%{{customdata[0]:.3f}}<br>semiprime mass=%{{customdata[1]:.3f}}<extra></extra>",
      }}];

      const ratioLayout = {{
        title: {{
          text: "Z vs ratio",
          font: {{ color: "#e0e0ff", size: 14, family: "monospace" }},
        }},
        paper_bgcolor: "{dark_bg}",
        plot_bgcolor: "{dark_bg}",
        margin: {{ l: 58, r: 16, t: 42, b: 44 }},
        xaxis: {{
          title: "layer",
          gridcolor: "#1e1e30",
          zerolinecolor: "#2a2a40",
          color: "#b7bfd8",
        }},
        yaxis: {{
          title: "semiprime / prime",
          gridcolor: "#1e1e30",
          zerolinecolor: "#2a2a40",
          color: "#b7bfd8",
        }},
      }};

      const histogramData = [
        {{
          x: distance.bins,
          y: distance.real_prime_to_semiprime,
          mode: "lines",
          name: "real p→s",
          line: {{ color: "#39d353", width: 2 }},
        }},
        {{
          x: distance.bins,
          y: distance.real_semiprime_to_prime,
          mode: "lines",
          name: "real s→p",
          line: {{ color: "#ff5b52", width: 2 }},
        }},
        {{
          x: distance.bins,
          y: distance.random_prime_to_semiprime,
          mode: "lines",
          name: "random p→s",
          line: {{ color: "#58c4ff", width: 2, dash: "dash" }},
        }},
        {{
          x: distance.bins,
          y: distance.random_semiprime_to_prime,
          mode: "lines",
          name: "random s→p",
          line: {{ color: "#ffb454", width: 2, dash: "dash" }},
        }},
      ];

      const histogramLayout = {{
        title: {{
          text: "Distance histogram (real vs random on Ulam grid)",
          font: {{ color: "#e0e0ff", size: 14, family: "monospace" }},
        }},
        paper_bgcolor: "{dark_bg}",
        plot_bgcolor: "{dark_bg}",
        margin: {{ l: 58, r: 16, t: 42, b: 44 }},
        xaxis: {{
          title: "nearest-neighbor distance",
          gridcolor: "#1e1e30",
          zerolinecolor: "#2a2a40",
          color: "#b7bfd8",
        }},
        yaxis: {{
          title: "density",
          gridcolor: "#1e1e30",
          zerolinecolor: "#2a2a40",
          color: "#b7bfd8",
        }},
        legend: {{
          orientation: "h",
          y: 1.12,
          x: 0,
          font: {{ color: "#cfd6ee", size: 10 }},
        }},
      }};

      const comparisonData = [
        {{
          x: distance.comparison.labels,
          y: distance.comparison.real,
          type: "bar",
          name: "real",
          marker: {{ color: "#7ee787" }},
        }},
        {{
          x: distance.comparison.labels,
          y: distance.comparison.random,
          type: "bar",
          name: "random",
          marker: {{ color: "#79c0ff" }},
        }},
      ];

      const comparisonLayout = {{
        title: {{
          text: currentValidationMode === "residual"
            ? `Diagonal-adjusted residual mode: ${{analytics.verdict}}`
            : `Distance gap metric: ${{analytics.verdict}}`,
          font: {{ color: "#e0e0ff", size: 14, family: "monospace" }},
        }},
        paper_bgcolor: "{dark_bg}",
        plot_bgcolor: "{dark_bg}",
        margin: {{ l: 58, r: 16, t: 54, b: 50 }},
        barmode: "group",
        xaxis: {{
          color: "#b7bfd8",
        }},
        yaxis: {{
          title: "average nearest distance",
          gridcolor: "#1e1e30",
          zerolinecolor: "#2a2a40",
          color: "#b7bfd8",
        }},
        annotations: [
          {{
            xref: "paper",
            yref: "paper",
            x: 0,
            y: 1.18,
            showarrow: false,
            align: "left",
            font: {{ color: "#9fb3d1", size: 11 }},
            text: `distance gap=${{analytics.distance_gap.toFixed(4)}} | anisotropy=${{analytics.anisotropy.toFixed(4)}} | diagonal real=${{analytics.diagonal_real.toFixed(4)}} | diagonal random=${{analytics.diagonal_random.toFixed(4)}}`,
          }},
        ],
      }};

      const heatmapData = [{{
        x: analytics.layers,
        y: analytics.quadrants,
        z: analytics.heatmap_ratio,
        text: analytics.heatmap_text,
        type: "heatmap",
        colorscale: "Turbo",
        hovertemplate: "<b>%{{y}}</b><br>layer=%{{x}}<br>ratio=%{{z:.3f}}<br>%{{text}}<extra></extra>",
        colorbar: {{
          title: "ratio",
          thickness: 10,
          len: 0.7,
        }},
      }}];

      const heatmapLayout = {{
        title: {{
          text: "Quadrant heatmap",
          font: {{ color: "#e0e0ff", size: 14, family: "monospace" }},
        }},
        paper_bgcolor: "{dark_bg}",
        plot_bgcolor: "{dark_bg}",
        margin: {{ l: 76, r: 22, t: 42, b: 44 }},
        xaxis: {{
          title: "layer",
          gridcolor: "#1e1e30",
          zerolinecolor: "#2a2a40",
          color: "#b7bfd8",
        }},
        yaxis: {{
          title: "quadrant",
          color: "#b7bfd8",
        }},
      }};

      return Promise.all([
        Plotly.react(validationRatioDiv, ratioData, ratioLayout, analysisPlotConfig),
        Plotly.react(validationDistanceDiv, histogramData, histogramLayout, analysisPlotConfig),
        Plotly.react(validationBaselineDiv, comparisonData, comparisonLayout, analysisPlotConfig),
        Plotly.react(validationHeatmapDiv, heatmapData, heatmapLayout, analysisPlotConfig),
      ]);
    }}

    function applyState() {{
      setActiveButtons();
      renderChain = renderChain
        .catch(() => null)
        .then(() => renderPlot())
        .then(() => renderUlamAnalytics())
        .then(() => renderValidationAnalytics());
      return renderChain;
    }}

    function resizePlot() {{
      syncLayoutBounds();
      const height = availablePlotHeight();
      plotDiv.style.height = `${{height}}px`;
      plotDiv.style.minHeight = `${{height}}px`;
      applyState();
    }}

    window.setView = function(view) {{
      currentView = view;
      applyState();
    }};

    window.setFilter = function(filter) {{
      if (!viewConfigs[currentView].filterable) {{
        return;
      }}
      currentFilter = filter;
      applyState();
    }};

    window.setModulo = function(value) {{
      currentModulo = Number(value);
      moduloValue.textContent = currentModulo;
      window.clearTimeout(moduloTimer);
      moduloTimer = window.setTimeout(() => {{
        applyState();
      }}, 50);
    }};

    window.setValidationMode = function(mode) {{
      currentView = "validation";
      currentValidationMode = mode;
      applyState();
    }};

    window.setWeightChannel = function(mode) {{
      currentView = "validation";
      currentWeightChannel = mode;
      applyState();
    }};

    Plotly.newPlot(plotDiv, figure.data, figure.layout, plotConfig).then(() => {{
      const moduloTraceIndex = viewConfigs.modulo.trace_indices[0];
      moduloNumbers = (baseData[moduloTraceIndex].customdata || []).map((row) => Number(row[0]));
      applyState();
      window.addEventListener("resize", resizePlot);
    }});
  </script>
</body>
</html>
"""
output_file.parent.mkdir(parents=True, exist_ok=True)
output_file.write_text(html, encoding="utf-8")
(output_file.parent / ".nojekyll").write_text("", encoding="utf-8")
(output_file.parent / "robots.txt").write_text("User-agent: *\nAllow: /\n", encoding="utf-8")
webbrowser.open(output_file.resolve().as_uri())
print(f"  - Saved to: {output_file.name}")

# Optionally save as self-contained HTML (works offline):
# fig.write_html("prime_spiral_3d.html")
