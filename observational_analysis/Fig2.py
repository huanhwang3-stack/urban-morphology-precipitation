"""
MULTI-CITY DEF CALCULATION

This script loops over all cities, reads the already-precomputed NPZ for each city,
calculates all DEF metrics, saves optional per-city detailed CSV files, and writes
ONE merged city-level file for later plotting.

It does NOT reread raw IMERG or ERA5.

Main merged output:
    ./all_city_DEF_results/ALL_CITIES_DEF_SUMMARY.csv

Metrics saved for every city:
    ALL
    0.1-5 mm/day
    5-10 mm/day
    10-20 mm/day
    >20 mm/day
    R95pTOT
    R99pTOT
    RX30min

DEF:
    DEF = (Pdown - Pup) / (Pdown + Pup)

IMPORTANT:
    The saved class key "1_5" corresponds to the actual threshold
    0.1 <= Pdaily < 5 mm/day, matching the current calculation code.
"""

import os
import glob
import numpy as np
import pandas as pd


# ============================================================
# USER SETTINGS
# ============================================================

# Define the x* regions here ONCE for all cities.
UPWIND_XSTAR_RANGE = (-1.0, 0.5)
DOWNWIND_XSTAR_RANGE = (0.5, 2.0)

# Pixel-day precipitation categories.
DAILY_CLASSES = [
    ("1-5", 0.1, 5.0, "left_closed_right_open"),
    ("5-10", 5.0, 10.0, "left_closed_right_open"),
    ("10-20", 10.0, 20.0, "closed"),
    (">20", 20.0, np.inf, "greater_than"),
]

# Bootstrap paired days / years.
N_BOOT = 10000
BOOTSTRAP_SEED = 42
BOOTSTRAP_CHUNK = 1000

# Save the detailed seven CSV files for every city.
# True:  keep the same detailed outputs as the original one-city script.
# False: only save the merged all-city summary.
SAVE_PER_CITY_DETAIL = True

# One common output directory for the merged multi-city result.
MASTER_OUT_DIR = "./all_city_DEF_results"
os.makedirs(MASTER_OUT_DIR, exist_ok=True)

MASTER_CITY_CSV = os.path.join(
    MASTER_OUT_DIR,
    "ALL_CITIES_DEF_SUMMARY.csv",
)

FAILED_CITY_CSV = os.path.join(
    MASTER_OUT_DIR,
    "ALL_CITIES_DEF_FAILED.csv",
)


# ============================================================
# CITY DIRECTORIES
#
# case_dirs:
#     where the precomputed NPZ / DEF-related files are located
#
# lcz_case_dirs:
#     where 0LCZ/LU_INDEX_51_61_numbers_region.txt is located
#
# These two lists MUST be in exactly the same city order.
# ============================================================

case_dirs = [

    "./data",

]


lcz_case_dirs = [

    "../data2/LCZ",

]


if len(case_dirs) != len(lcz_case_dirs):
    raise ValueError(
        "case_dirs and lcz_case_dirs must have the same length: "
        f"{len(case_dirs)} vs {len(lcz_case_dirs)}"
    )


# ============================================================
# GLOBALS USED BY THE ORIGINAL ONE-CITY CALCULATION FUNCTIONS
#
# They are updated city-by-city inside process_one_city().
# ============================================================

CASE_NAME = ""
PRECOMPUTED_NPZ = ""
OUT_DIR = ""


# ============================================================
# LCZ
# ============================================================

LCZ_CLASSES = [51, 52, 53]


def get_city_label(case_dir):
    return os.path.basename(
        os.path.normpath(case_dir)
    )


def read_lcz_percent(lcz_case_dir):

    txtfile = os.path.join(
        lcz_case_dir,
        "0LCZ",
        "LU_INDEX_51_61_numbers_region.txt",
    )

    if not os.path.exists(txtfile):
        raise FileNotFoundError(
            f"LCZ file not found: {txtfile}"
        )

    counts = {}

    with open(txtfile, "r") as f:
        for line in f:
            line = line.strip()

            if not line:
                continue

            if ":" in line:
                key, value = line.split(":", 1)
            else:
                key, value = line.split()

            counts[int(key.strip())] = int(value.strip())

    total_urban = sum(
        counts.get(i, 0)
        for i in range(51, 62)
    )

    selected_count = sum(
        counts.get(i, 0)
        for i in LCZ_CLASSES
    )

    if total_urban <= 0:
        raise ValueError(
            f"No urban LCZ pixels in {txtfile}"
        )

    return float(
        selected_count
        /
        total_urban
        *
        100.0
    )


# ============================================================
# FIND PRECOMPUTED NPZ
# ============================================================

def find_precomputed_npz(case_dir):

    candidates = []

    preferred_dir = os.path.join(
        case_dir,
        "out_john_DEF",
    )

    candidates += glob.glob(
        os.path.join(
            preferred_dir,
            "*_PRECOMPUTED_FOR_LATER_XSTAR_ANALYSIS.npz",
        )
    )

    # Fallback: recursive search below the city directory.
    candidates += glob.glob(
        os.path.join(
            case_dir,
            "**",
            "*_PRECOMPUTED_FOR_LATER_XSTAR_ANALYSIS.npz",
        ),
        recursive=True,
    )

    # Remove duplicate paths while preserving order.
    candidates = list(
        dict.fromkeys(candidates)
    )

    if len(candidates) == 0:
        raise FileNotFoundError(
            "Cannot find "
            "*_PRECOMPUTED_FOR_LATER_XSTAR_ANALYSIS.npz "
            f"under {case_dir}"
        )

    # If several exist, use the newest.
    return max(
        candidates,
        key=os.path.getmtime,
    )



# ============================================================
# HELPERS
# ============================================================

def safe_def(p_up, p_down):
    if not np.isfinite(p_up) or not np.isfinite(p_down):
        return np.nan
    denom = p_down + p_up
    if denom <= 0:
        return np.nan
    return (p_down - p_up) / denom


def safe_enhancement_pct(p_up, p_down):
    if not np.isfinite(p_up) or not np.isfinite(p_down) or p_up <= 0:
        return np.nan
    return 100.0 * (p_down - p_up) / p_up


def class_key(label):
    return label.replace(">", "gt").replace("-", "_").replace(".", "p")


def daily_class_mask(daily_mm, low, high, mode):
    valid = np.isfinite(daily_mm)

    if mode == "left_closed_right_open":
        return valid & (daily_mm >= low) & (daily_mm < high)
    if mode == "closed":
        return valid & (daily_mm >= low) & (daily_mm <= high)
    if mode == "greater_than":
        return valid & (daily_mm > low)

    raise ValueError(f"Unknown class mode: {mode}")


def make_region_mask(xstar, corridor_mask, xstar_range, valid_values=None):
    x0, x1 = xstar_range
    mask = (
        np.asarray(corridor_mask, dtype=bool)
        & np.isfinite(xstar)
        & (xstar >= x0)
        & (xstar < x1)
    )

    if valid_values is not None:
        mask &= np.isfinite(valid_values)

    return mask


def regional_mean(values, mask):
    n = int(np.sum(mask))
    if n == 0:
        return np.nan, 0
    return float(np.mean(values[mask], dtype=np.float64)), n


def regional_contribution_and_fraction(values, condition, base_mask):
    """
    Contribution = sum(rainfall amount in selected class) / ALL valid region pixels.
    Occurrence fraction = selected pixel count / ALL valid region pixels.
    """
    n = int(np.sum(base_mask))
    if n == 0:
        return np.nan, np.nan

    selected = base_mask & condition
    if np.any(selected):
        total = float(np.sum(values[selected], dtype=np.float64))
    else:
        total = 0.0

    contribution = total / n
    occurrence_fraction = float(np.sum(selected)) / n
    return contribution, occurrence_fraction


def bootstrap_paired_metrics(up, down, n_boot=N_BOOT, seed=BOOTSTRAP_SEED,
                             chunk=BOOTSTRAP_CHUNK):
    up = np.asarray(up, dtype=float)
    down = np.asarray(down, dtype=float)

    valid = np.isfinite(up) & np.isfinite(down)
    up = up[valid]
    down = down[valid]
    n = up.size

    if n < 2 or n_boot <= 0:
        return {
            "def_ci_low": np.nan,
            "def_ci_high": np.nan,
            "enh_pct_ci_low": np.nan,
            "enh_pct_ci_high": np.nan,
            "diff_ci_low": np.nan,
            "diff_ci_high": np.nan,
        }

    rng = np.random.default_rng(seed)
    boot_def = np.empty(n_boot, dtype=float)
    boot_pct = np.empty(n_boot, dtype=float)
    boot_diff = np.empty(n_boot, dtype=float)

    done = 0
    while done < n_boot:
        m = min(chunk, n_boot - done)
        idx = rng.integers(0, n, size=(m, n))

        up_m = np.mean(up[idx], axis=1)
        down_m = np.mean(down[idx], axis=1)
        diff = down_m - up_m
        denom = down_m + up_m

        d = np.full(m, np.nan)
        ok = denom > 0
        d[ok] = diff[ok] / denom[ok]

        pct = np.full(m, np.nan)
        ok = up_m > 0
        pct[ok] = 100.0 * diff[ok] / up_m[ok]

        boot_def[done:done + m] = d
        boot_pct[done:done + m] = pct
        boot_diff[done:done + m] = diff
        done += m

    return {
        "def_ci_low": float(np.nanpercentile(boot_def, 2.5)),
        "def_ci_high": float(np.nanpercentile(boot_def, 97.5)),
        "enh_pct_ci_low": float(np.nanpercentile(boot_pct, 2.5)),
        "enh_pct_ci_high": float(np.nanpercentile(boot_pct, 97.5)),
        "diff_ci_low": float(np.nanpercentile(boot_diff, 2.5)),
        "diff_ci_high": float(np.nanpercentile(boot_diff, 97.5)),
    }


def summarize_paired(up, down, seed_offset=0):
    up = np.asarray(up, dtype=float)
    down = np.asarray(down, dtype=float)

    valid = np.isfinite(up) & np.isfinite(down)
    u = up[valid]
    d = down[valid]
    n = u.size

    if n == 0:
        return {
            "n_valid_pairs": 0,
            "mean_up": np.nan,
            "mean_down": np.nan,
            "mean_down_minus_up": np.nan,
            "DEF": np.nan,
            "DEF_ci95_low": np.nan,
            "DEF_ci95_high": np.nan,
            "enhancement_pct": np.nan,
            "enhancement_pct_ci95_low": np.nan,
            "enhancement_pct_ci95_high": np.nan,
            "difference_ci95_low": np.nan,
            "difference_ci95_high": np.nan,
            "fraction_pairs_down_gt_up": np.nan,
            "sum_up": np.nan,
            "sum_down": np.nan,
            "sum_down_minus_up": np.nan,
        }

    mean_up = float(np.mean(u))
    mean_down = float(np.mean(d))

    ci = bootstrap_paired_metrics(
        u,
        d,
        n_boot=N_BOOT,
        seed=BOOTSTRAP_SEED + seed_offset,
        chunk=BOOTSTRAP_CHUNK,
    )

    return {
        "n_valid_pairs": n,
        "mean_up": mean_up,
        "mean_down": mean_down,
        "mean_down_minus_up": mean_down - mean_up,
        "DEF": safe_def(mean_up, mean_down),
        "DEF_ci95_low": ci["def_ci_low"],
        "DEF_ci95_high": ci["def_ci_high"],
        "enhancement_pct": safe_enhancement_pct(mean_up, mean_down),
        "enhancement_pct_ci95_low": ci["enh_pct_ci_low"],
        "enhancement_pct_ci95_high": ci["enh_pct_ci_high"],
        "difference_ci95_low": ci["diff_ci_low"],
        "difference_ci95_high": ci["diff_ci_high"],
        "fraction_pairs_down_gt_up": float(np.mean(d > u)),
        "sum_up": float(np.sum(u)),
        "sum_down": float(np.sum(d)),
        "sum_down_minus_up": float(np.sum(d - u)),
    }


def required(z, name):
    if name not in z.files:
        raise KeyError(f"Required variable '{name}' not found in NPZ.")
    return z[name]


# ============================================================
# DAILY CALCULATION
# ============================================================

def build_daily_dataframe(z):
    dates = required(z, "daily_dates").astype("datetime64[D]")
    precip = required(z, "daily_precip_mm")
    xstar = required(z, "daily_xstar")
    corridor = required(z, "daily_corridor_mask")

    p95 = required(z, "P95_threshold_mmday")
    p99 = required(z, "P99_threshold_mmday")

    geom_valid = z["daily_geometry_valid"] if "daily_geometry_valid" in z.files else np.ones(len(dates), dtype=bool)
    u850 = z["daily_u850_ms"] if "daily_u850_ms" in z.files else np.full(len(dates), np.nan)
    v850 = z["daily_v850_ms"] if "daily_v850_ms" in z.files else np.full(len(dates), np.nan)
    U850 = z["daily_U850_ms"] if "daily_U850_ms" in z.files else np.full(len(dates), np.nan)
    Lc = z["daily_Lc_km"] if "daily_Lc_km" in z.files else np.full(len(dates), np.nan)

    if not (len(dates) == precip.shape[0] == xstar.shape[0] == corridor.shape[0]):
        raise ValueError("Daily arrays have inconsistent time dimensions.")

    rows = []

    for i, day in enumerate(dates):
        if not bool(geom_valid[i]):
            continue

        P = np.asarray(precip[i], dtype=float)
        X = np.asarray(xstar[i], dtype=float)
        C = np.asarray(corridor[i], dtype=bool)

        up_mask = make_region_mask(X, C, UPWIND_XSTAR_RANGE, valid_values=P)
        down_mask = make_region_mask(X, C, DOWNWIND_XSTAR_RANGE, valid_values=P)

        all_up, n_up = regional_mean(P, up_mask)
        all_down, n_down = regional_mean(P, down_mask)

        if n_up == 0 or n_down == 0:
            continue

        row = {
            "case": CASE_NAME,
            "date": str(day),
            "year": int(str(day)[:4]),
            "upwind_xstar_min": UPWIND_XSTAR_RANGE[0],
            "upwind_xstar_max": UPWIND_XSTAR_RANGE[1],
            "downwind_xstar_min": DOWNWIND_XSTAR_RANGE[0],
            "downwind_xstar_max": DOWNWIND_XSTAR_RANGE[1],
            "u850_daily_ms": float(u850[i]),
            "v850_daily_ms": float(v850[i]),
            "U850_daily_ms": float(U850[i]),
            "Lc_daily_km": float(Lc[i]),
            "upwind_pixel_count": n_up,
            "downwind_pixel_count": n_down,
            "daily_upwind_total_mm": all_up,
            "daily_downwind_total_mm": all_down,
            "daily_down_minus_up_total_mm": all_down - all_up,
            "daily_total_DEF": safe_def(all_up, all_down),
            "daily_total_enhancement_pct": safe_enhancement_pct(all_up, all_down),
        }

        # Fixed intensity classes.
        for label, low, high, mode in DAILY_CLASSES:
            condition = daily_class_mask(P, low, high, mode)
            up_c, up_f = regional_contribution_and_fraction(P, condition, up_mask)
            down_c, down_f = regional_contribution_and_fraction(P, condition, down_mask)

            key = class_key(label)
            row[f"{key}_upwind_contribution_mm"] = up_c
            row[f"{key}_downwind_contribution_mm"] = down_c
            row[f"{key}_down_minus_up_contribution_mm"] = down_c - up_c
            row[f"{key}_DEF"] = safe_def(up_c, down_c)
            row[f"{key}_enhancement_pct"] = safe_enhancement_pct(up_c, down_c)
            row[f"{key}_upwind_occurrence_fraction"] = up_f
            row[f"{key}_downwind_occurrence_fraction"] = down_f
            row[f"{key}_occurrence_fraction_difference"] = down_f - up_f

        # Pixel-specific P95/P99 extreme contributions.
        r95_condition = np.isfinite(P) & np.isfinite(p95) & (P > p95)
        r99_condition = np.isfinite(P) & np.isfinite(p99) & (P > p99)

        for name, condition in [("R95pTOT", r95_condition), ("R99pTOT", r99_condition)]:
            up_c, up_f = regional_contribution_and_fraction(P, condition, up_mask)
            down_c, down_f = regional_contribution_and_fraction(P, condition, down_mask)

            row[f"{name}_upwind_contribution_mm"] = up_c
            row[f"{name}_downwind_contribution_mm"] = down_c
            row[f"{name}_down_minus_up_contribution_mm"] = down_c - up_c
            row[f"{name}_DEF"] = safe_def(up_c, down_c)
            row[f"{name}_enhancement_pct"] = safe_enhancement_pct(up_c, down_c)
            row[f"{name}_upwind_occurrence_fraction"] = up_f
            row[f"{name}_downwind_occurrence_fraction"] = down_f
            row[f"{name}_occurrence_fraction_difference"] = down_f - up_f

        rows.append(row)

        if (i + 1) % 100 == 0 or (i + 1) == len(dates):
            print(f"  processed {i + 1}/{len(dates)} days")

    if not rows:
        raise RuntimeError("No valid daily rows were produced. Check x* ranges and stored geometry.")

    return pd.DataFrame(rows).sort_values("date").reset_index(drop=True)


# ============================================================
# FIXED INTENSITY SUMMARY
# ============================================================

def make_fixed_intensity_summary(daily_df):
    rows = []

    s = summarize_paired(
        daily_df["daily_upwind_total_mm"].to_numpy(float),
        daily_df["daily_downwind_total_mm"].to_numpy(float),
        seed_offset=0,
    )

    rows.append({
        "case": CASE_NAME,
        "intensity_class": "ALL_DAILY_RAIN",
        "definition": "all valid daily precipitation",
        "upwind_xstar_range": str(UPWIND_XSTAR_RANGE),
        "downwind_xstar_range": str(DOWNWIND_XSTAR_RANGE),
        "n_days": s["n_valid_pairs"],
        "mean_upwind_contribution_mm_per_day": s["mean_up"],
        "mean_downwind_contribution_mm_per_day": s["mean_down"],
        "mean_down_minus_up_mm_per_day": s["mean_down_minus_up"],
        "DEF": s["DEF"],
        "DEF_ci95_low": s["DEF_ci95_low"],
        "DEF_ci95_high": s["DEF_ci95_high"],
        "enhancement_pct": s["enhancement_pct"],
        "enhancement_pct_ci95_low": s["enhancement_pct_ci95_low"],
        "enhancement_pct_ci95_high": s["enhancement_pct_ci95_high"],
        "fraction_days_downwind_gt_upwind": s["fraction_pairs_down_gt_up"],
        "total_upwind_contribution_mm": s["sum_up"],
        "total_downwind_contribution_mm": s["sum_down"],
        "total_down_minus_up_contribution_mm": s["sum_down_minus_up"],
        "mean_upwind_occurrence_fraction": np.nan,
        "mean_downwind_occurrence_fraction": np.nan,
        "mean_occurrence_fraction_difference": np.nan,
    })

    for j, (label, low, high, mode) in enumerate(DAILY_CLASSES, start=1):
        key = class_key(label)
        up = daily_df[f"{key}_upwind_contribution_mm"].to_numpy(float)
        down = daily_df[f"{key}_downwind_contribution_mm"].to_numpy(float)
        s = summarize_paired(up, down, seed_offset=100 * j)

        up_occ = daily_df[f"{key}_upwind_occurrence_fraction"].to_numpy(float)
        down_occ = daily_df[f"{key}_downwind_occurrence_fraction"].to_numpy(float)

        if mode == "left_closed_right_open":
            definition = f"{low:g} <= Pdaily < {high:g} mm/day at each pixel"
        elif mode == "closed":
            definition = f"{low:g} <= Pdaily <= {high:g} mm/day at each pixel"
        else:
            definition = f"Pdaily > {low:g} mm/day at each pixel"

        rows.append({
            "case": CASE_NAME,
            "intensity_class": label,
            "definition": definition,
            "upwind_xstar_range": str(UPWIND_XSTAR_RANGE),
            "downwind_xstar_range": str(DOWNWIND_XSTAR_RANGE),
            "n_days": s["n_valid_pairs"],
            "mean_upwind_contribution_mm_per_day": s["mean_up"],
            "mean_downwind_contribution_mm_per_day": s["mean_down"],
            "mean_down_minus_up_mm_per_day": s["mean_down_minus_up"],
            "DEF": s["DEF"],
            "DEF_ci95_low": s["DEF_ci95_low"],
            "DEF_ci95_high": s["DEF_ci95_high"],
            "enhancement_pct": s["enhancement_pct"],
            "enhancement_pct_ci95_low": s["enhancement_pct_ci95_low"],
            "enhancement_pct_ci95_high": s["enhancement_pct_ci95_high"],
            "fraction_days_downwind_gt_upwind": s["fraction_pairs_down_gt_up"],
            "total_upwind_contribution_mm": s["sum_up"],
            "total_downwind_contribution_mm": s["sum_down"],
            "total_down_minus_up_contribution_mm": s["sum_down_minus_up"],
            "mean_upwind_occurrence_fraction": float(np.nanmean(up_occ)),
            "mean_downwind_occurrence_fraction": float(np.nanmean(down_occ)),
            "mean_occurrence_fraction_difference": float(np.nanmean(down_occ - up_occ)),
        })

    return pd.DataFrame(rows)


# ============================================================
# R95 / R99 ANNUAL TOTALS + SUMMARY
# ============================================================

def make_r95_r99_summaries(daily_df):
    annual_rows = []

    for year, g in daily_df.groupby("year"):
        row = {
            "case": CASE_NAME,
            "year": int(year),
            "upwind_xstar_range": str(UPWIND_XSTAR_RANGE),
            "downwind_xstar_range": str(DOWNWIND_XSTAR_RANGE),
        }

        for name in ["R95pTOT", "R99pTOT"]:
            up = g[f"{name}_upwind_contribution_mm"].to_numpy(float)
            down = g[f"{name}_downwind_contribution_mm"].to_numpy(float)
            valid = np.isfinite(up) & np.isfinite(down)

            if np.any(valid):
                up_total = float(np.sum(up[valid]))
                down_total = float(np.sum(down[valid]))
            else:
                up_total = np.nan
                down_total = np.nan

            row[f"{name}_upwind_total_mm"] = up_total
            row[f"{name}_downwind_total_mm"] = down_total
            row[f"{name}_down_minus_up_total_mm"] = down_total - up_total
            row[f"{name}_DEF"] = safe_def(up_total, down_total)
            row[f"{name}_enhancement_pct"] = safe_enhancement_pct(up_total, down_total)
            row[f"{name}_n_valid_days"] = int(np.sum(valid))

        annual_rows.append(row)

    annual_df = pd.DataFrame(annual_rows).sort_values("year").reset_index(drop=True)

    summary_rows = []
    for j, name in enumerate(["R95pTOT", "R99pTOT"], start=1):
        up = annual_df[f"{name}_upwind_total_mm"].to_numpy(float)
        down = annual_df[f"{name}_downwind_total_mm"].to_numpy(float)
        s = summarize_paired(up, down, seed_offset=5000 + 100 * j)

        summary_rows.append({
            "case": CASE_NAME,
            "extreme_metric": name,
            "upwind_xstar_range": str(UPWIND_XSTAR_RANGE),
            "downwind_xstar_range": str(DOWNWIND_XSTAR_RANGE),
            "n_years": s["n_valid_pairs"],
            "mean_annual_upwind_total_mm": s["mean_up"],
            "mean_annual_downwind_total_mm": s["mean_down"],
            "mean_annual_down_minus_up_mm": s["mean_down_minus_up"],
            "DEF": s["DEF"],
            "DEF_ci95_low": s["DEF_ci95_low"],
            "DEF_ci95_high": s["DEF_ci95_high"],
            "enhancement_pct": s["enhancement_pct"],
            "enhancement_pct_ci95_low": s["enhancement_pct_ci95_low"],
            "enhancement_pct_ci95_high": s["enhancement_pct_ci95_high"],
            "fraction_years_downwind_gt_upwind": s["fraction_pairs_down_gt_up"],
        })

    return annual_df, pd.DataFrame(summary_rows)


# ============================================================
# RX30MIN
# ============================================================

def make_rx30min(z):
    years = required(z, "rx30min_years").astype(int)
    depth = required(z, "rx30min_depth_mm_30min")
    rate = required(z, "rx30min_rate_mmhr")
    xstar = required(z, "rx30min_xstar")
    corridor = required(z, "rx30min_corridor_mask")

    U850 = z["rx30min_U850_period_mean_ms"] if "rx30min_U850_period_mean_ms" in z.files else np.full(len(years), np.nan)
    Lc = z["rx30min_Lc_km"] if "rx30min_Lc_km" in z.files else np.full(len(years), np.nan)

    rows = []

    for i, year in enumerate(years):
        D = np.asarray(depth[i], dtype=float)
        R = np.asarray(rate[i], dtype=float)
        X = np.asarray(xstar[i], dtype=float)
        C = np.asarray(corridor[i], dtype=bool)

        up_mask = make_region_mask(X, C, UPWIND_XSTAR_RANGE, valid_values=D)
        down_mask = make_region_mask(X, C, DOWNWIND_XSTAR_RANGE, valid_values=D)

        up_depth, n_up = regional_mean(D, up_mask)
        down_depth, n_down = regional_mean(D, down_mask)
        up_rate, _ = regional_mean(R, up_mask)
        down_rate, _ = regional_mean(R, down_mask)

        if n_up == 0 or n_down == 0:
            continue

        rows.append({
            "case": CASE_NAME,
            "year": int(year),
            "upwind_xstar_range": str(UPWIND_XSTAR_RANGE),
            "downwind_xstar_range": str(DOWNWIND_XSTAR_RANGE),
            "U850_period_mean_ms": float(U850[i]),
            "Lc_km": float(Lc[i]),
            "upwind_pixel_count": n_up,
            "downwind_pixel_count": n_down,
            "RX30min_upwind_mean_rate_mmhr": up_rate,
            "RX30min_downwind_mean_rate_mmhr": down_rate,
            "RX30min_upwind_mean_depth_mm_30min": up_depth,
            "RX30min_downwind_mean_depth_mm_30min": down_depth,
            "RX30min_down_minus_up_depth_mm_30min": down_depth - up_depth,
            "RX30min_DEF": safe_def(up_depth, down_depth),
            "RX30min_enhancement_pct": safe_enhancement_pct(up_depth, down_depth),
        })

    if not rows:
        raise RuntimeError("No valid RX30min rows were produced.")

    rx_df = pd.DataFrame(rows).sort_values("year").reset_index(drop=True)

    s = summarize_paired(
        rx_df["RX30min_upwind_mean_depth_mm_30min"].to_numpy(float),
        rx_df["RX30min_downwind_mean_depth_mm_30min"].to_numpy(float),
        seed_offset=9000,
    )

    summary_df = pd.DataFrame([{
        "case": CASE_NAME,
        "extreme_metric": "RX30min",
        "upwind_xstar_range": str(UPWIND_XSTAR_RANGE),
        "downwind_xstar_range": str(DOWNWIND_XSTAR_RANGE),
        "n_years": s["n_valid_pairs"],
        "mean_upwind_RX30min_depth_mm_30min": s["mean_up"],
        "mean_downwind_RX30min_depth_mm_30min": s["mean_down"],
        "mean_down_minus_up_RX30min_depth_mm_30min": s["mean_down_minus_up"],
        "DEF": s["DEF"],
        "DEF_ci95_low": s["DEF_ci95_low"],
        "DEF_ci95_high": s["DEF_ci95_high"],
        "enhancement_pct": s["enhancement_pct"],
        "enhancement_pct_ci95_low": s["enhancement_pct_ci95_low"],
        "enhancement_pct_ci95_high": s["enhancement_pct_ci95_high"],
        "fraction_years_downwind_gt_upwind": s["fraction_pairs_down_gt_up"],
    }])

    return rx_df, summary_df





# ============================================================
# PROCESS ONE CITY
# ============================================================

def process_one_city(
    case_dir,
    lcz_case_dir,
):

    global CASE_NAME
    global PRECOMPUTED_NPZ
    global OUT_DIR

    CASE_NAME = get_city_label(
        case_dir
    )

    PRECOMPUTED_NPZ = find_precomputed_npz(
        case_dir
    )

    OUT_DIR = os.path.join(
        case_dir,
        "2out_DEF_from_precomputed",
    )

    if SAVE_PER_CITY_DETAIL:
        os.makedirs(
            OUT_DIR,
            exist_ok=True,
        )

    lcz13 = read_lcz_percent(
        lcz_case_dir
    )

    print("")
    print("=" * 92)
    print(f"CITY: {CASE_NAME}")
    print("=" * 92)
    print(f"NPZ:      {PRECOMPUTED_NPZ}")
    print(f"LCZ dir:  {lcz_case_dir}")
    print(f"LCZ1-3:   {lcz13:.3f}%")
    print(f"Upwind:   {UPWIND_XSTAR_RANGE}")
    print(f"Downwind: {DOWNWIND_XSTAR_RANGE}")

    with np.load(
        PRECOMPUTED_NPZ,
        allow_pickle=False,
    ) as z:

        if "xstar_storage_range" in z.files:

            storage = np.asarray(
                z["xstar_storage_range"],
                dtype=float,
            )

            lo = min(
                UPWIND_XSTAR_RANGE[0],
                DOWNWIND_XSTAR_RANGE[0],
            )

            hi = max(
                UPWIND_XSTAR_RANGE[1],
                DOWNWIND_XSTAR_RANGE[1],
            )

            if (
                lo < storage[0]
                or
                hi > storage[1]
            ):

                print(
                    "WARNING: requested x* region extends "
                    "outside xstar_storage_range"
                )

                print(
                    f"  stored range:   {tuple(storage)}"
                )

                print(
                    f"  requested span: ({lo}, {hi})"
                )

        # ----------------------------------------------------
        # Calculate all metrics
        # ----------------------------------------------------

        print("Calculating daily metrics...")

        daily_df = build_daily_dataframe(
            z
        )

        print("Calculating fixed-intensity summaries...")

        fixed_summary_df = make_fixed_intensity_summary(
            daily_df
        )

        print("Calculating R95pTOT/R99pTOT...")

        r_annual_df, r_summary_df = make_r95_r99_summaries(
            daily_df
        )

        print("Calculating RX30min...")

        rx_df, rx_summary_df = make_rx30min(
            z
        )


    # ========================================================
    # OPTIONAL: SAVE SAME DETAILED FILES AS ONE-CITY CODE
    # ========================================================

    if SAVE_PER_CITY_DETAIL:

        daily_csv = os.path.join(
            OUT_DIR,
            f"{CASE_NAME}_DAILY_DEF_METRICS.csv",
        )

        fixed_csv = os.path.join(
            OUT_DIR,
            f"{CASE_NAME}_FIXED_INTENSITY_DEF_SUMMARY.csv",
        )

        r_annual_csv = os.path.join(
            OUT_DIR,
            f"{CASE_NAME}_R95_R99_ANNUAL_TOTALS.csv",
        )

        r_summary_csv = os.path.join(
            OUT_DIR,
            f"{CASE_NAME}_R95_R99_DEF_SUMMARY.csv",
        )

        rx_annual_csv = os.path.join(
            OUT_DIR,
            f"{CASE_NAME}_RX30MIN_ANNUAL.csv",
        )

        rx_summary_csv = os.path.join(
            OUT_DIR,
            f"{CASE_NAME}_RX30MIN_DEF_SUMMARY.csv",
        )

        daily_df.to_csv(
            daily_csv,
            index=False,
        )

        fixed_summary_df.to_csv(
            fixed_csv,
            index=False,
        )

        r_annual_df.to_csv(
            r_annual_csv,
            index=False,
        )

        r_summary_df.to_csv(
            r_summary_csv,
            index=False,
        )

        rx_df.to_csv(
            rx_annual_csv,
            index=False,
        )

        rx_summary_df.to_csv(
            rx_summary_csv,
            index=False,
        )


    # ========================================================
    # ONE-ROW CITY SUMMARY
    # ========================================================

    city = {

        "city":
            CASE_NAME,

        "lcz13_percent":
            lcz13,

        "precomputed_npz":
            PRECOMPUTED_NPZ,

        "lcz_directory":
            lcz_case_dir,

        "upwind_xstar_min":
            UPWIND_XSTAR_RANGE[0],

        "upwind_xstar_max":
            UPWIND_XSTAR_RANGE[1],

        "downwind_xstar_min":
            DOWNWIND_XSTAR_RANGE[0],

        "downwind_xstar_max":
            DOWNWIND_XSTAR_RANGE[1],

    }


    # --------------------------------------------------------
    # ALL + fixed intensity classes
    # --------------------------------------------------------

    for _, r in fixed_summary_df.iterrows():

        key = class_key(
            str(
                r["intensity_class"]
            )
        )

        city[
            f"{key}_DEF"
        ] = r["DEF"]

        city[
            f"{key}_DEF_ci95_low"
        ] = r["DEF_ci95_low"]

        city[
            f"{key}_DEF_ci95_high"
        ] = r["DEF_ci95_high"]

        city[
            f"{key}_enhancement_pct"
        ] = r["enhancement_pct"]

        city[
            f"{key}_mean_upwind"
        ] = r[
            "mean_upwind_contribution_mm_per_day"
        ]

        city[
            f"{key}_mean_downwind"
        ] = r[
            "mean_downwind_contribution_mm_per_day"
        ]

        city[
            f"{key}_fraction_down_gt_up"
        ] = r[
            "fraction_days_downwind_gt_upwind"
        ]

        city[
            f"{key}_mean_upwind_occurrence_fraction"
        ] = r[
            "mean_upwind_occurrence_fraction"
        ]

        city[
            f"{key}_mean_downwind_occurrence_fraction"
        ] = r[
            "mean_downwind_occurrence_fraction"
        ]


    # --------------------------------------------------------
    # R95pTOT / R99pTOT
    # --------------------------------------------------------

    for _, r in r_summary_df.iterrows():

        key = str(
            r["extreme_metric"]
        )

        city[
            f"{key}_DEF"
        ] = r["DEF"]

        city[
            f"{key}_DEF_ci95_low"
        ] = r["DEF_ci95_low"]

        city[
            f"{key}_DEF_ci95_high"
        ] = r["DEF_ci95_high"]

        city[
            f"{key}_enhancement_pct"
        ] = r["enhancement_pct"]

        city[
            f"{key}_mean_upwind"
        ] = r[
            "mean_annual_upwind_total_mm"
        ]

        city[
            f"{key}_mean_downwind"
        ] = r[
            "mean_annual_downwind_total_mm"
        ]

        city[
            f"{key}_fraction_down_gt_up"
        ] = r[
            "fraction_years_downwind_gt_upwind"
        ]


    # --------------------------------------------------------
    # RX30min
    # --------------------------------------------------------

    rr = rx_summary_df.iloc[0]

    city[
        "RX30min_DEF"
    ] = rr["DEF"]

    city[
        "RX30min_DEF_ci95_low"
    ] = rr["DEF_ci95_low"]

    city[
        "RX30min_DEF_ci95_high"
    ] = rr["DEF_ci95_high"]

    city[
        "RX30min_enhancement_pct"
    ] = rr["enhancement_pct"]

    city[
        "RX30min_mean_upwind"
    ] = rr[
        "mean_upwind_RX30min_depth_mm_30min"
    ]

    city[
        "RX30min_mean_downwind"
    ] = rr[
        "mean_downwind_RX30min_depth_mm_30min"
    ]

    city[
        "RX30min_fraction_down_gt_up"
    ] = rr[
        "fraction_years_downwind_gt_upwind"
    ]


    # ========================================================
    # SAVE ONE-CITY SUMMARY TOO
    # ========================================================

    if SAVE_PER_CITY_DETAIL:

        city_csv = os.path.join(
            OUT_DIR,
            f"{CASE_NAME}_DEF_CITY_SUMMARY.csv",
        )

        pd.DataFrame(
            [city]
        ).to_csv(
            city_csv,
            index=False,
        )


    # ========================================================
    # PRINT SHORT RESULT
    # ========================================================

    print(
        f"{CASE_NAME:15s} | "
        f"LCZ1-3={lcz13:6.2f}% | "
        f"ALL DEF={city.get('ALL_DAILY_RAIN_DEF', np.nan):+.5f} | "
        f"R95={city.get('R95pTOT_DEF', np.nan):+.5f} | "
        f"R99={city.get('R99pTOT_DEF', np.nan):+.5f} | "
        f"RX30min={city.get('RX30min_DEF', np.nan):+.5f}"
    )

    return city


# ============================================================
# MAIN: PROCESS ALL CITIES
# ============================================================

def main():

    print("=" * 92)
    print("MULTI-CITY DEF CALCULATION")
    print("=" * 92)

    print(
        f"Number of requested cities: {len(case_dirs)}"
    )

    print(
        f"Upwind x*:   {UPWIND_XSTAR_RANGE}"
    )

    print(
        f"Downwind x*: {DOWNWIND_XSTAR_RANGE}"
    )

    print(
        f"Master output: {MASTER_CITY_CSV}"
    )


    all_city_rows = []
    failed_rows = []


    for i, (
        case_dir,
        lcz_case_dir,
    ) in enumerate(
        zip(
            case_dirs,
            lcz_case_dirs,
        ),
        start=1,
    ):

        city = get_city_label(
            case_dir
        )

        lcz_city = get_city_label(
            lcz_case_dir
        )

        print("")
        print(
            f"[{i:02d}/{len(case_dirs):02d}] "
            f"{city}"
        )

        if city != lcz_city:

            print(
                "WARNING: directory-name mismatch: "
                f"{city} vs {lcz_city}"
            )

        try:

            city_row = process_one_city(
                case_dir,
                lcz_case_dir,
            )

            all_city_rows.append(
                city_row
            )

        except Exception as exc:

            print(
                f"FAILED: {city} | {exc}"
            )

            failed_rows.append({

                "city":
                    city,

                "case_dir":
                    case_dir,

                "lcz_case_dir":
                    lcz_case_dir,

                "error":
                    str(exc),

            })


    # ========================================================
    # SAVE MERGED CITY DATA
    # ========================================================

    if len(
        all_city_rows
    ) == 0:

        raise RuntimeError(
            "No city was processed successfully."
        )


    master_df = pd.DataFrame(
        all_city_rows
    )


    master_df.to_csv(
        MASTER_CITY_CSV,
        index=False,
    )


    failed_df = pd.DataFrame(
        failed_rows
    )

    failed_df.to_csv(
        FAILED_CITY_CSV,
        index=False,
    )


    print("")
    print("=" * 92)
    print("FINISHED")
    print("=" * 92)

    print(
        f"Successful cities: {len(master_df)}/{len(case_dirs)}"
    )

    print(
        f"Failed cities:     {len(failed_df)}"
    )

    print("")
    print(
        f"Saved merged city data:\n  {MASTER_CITY_CSV}"
    )

    print(
        f"Saved failure log:\n  {FAILED_CITY_CSV}"
    )

    print("")
    print("Available DEF columns:")

    for name in [

        "ALL_DAILY_RAIN_DEF",
        "1_5_DEF",
        "5_10_DEF",
        "10_20_DEF",
        "gt20_DEF",
        "R95pTOT_DEF",
        "R99pTOT_DEF",
        "RX30min_DEF",

    ]:

        if name in master_df.columns:

            print(
                f"  {name}"
            )


if __name__ == "__main__":
    main()
