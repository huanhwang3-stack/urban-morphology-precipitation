import os
import glob
import numpy as np
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt

from scipy.ndimage import gaussian_filter1d
from scipy.stats import pearsonr, spearmanr, linregress


# ============================================================
# Matplotlib settings
# ============================================================

font = {
    "family": "serif",
    "size": 30,
}

matplotlib.rc("font", **font)

plt.rc("legend", fontsize=30)
plt.rc("legend", frameon=False)
plt.rc("text", usetex=True)

matplotlib.rcParams["axes.linewidth"] = 1.3
matplotlib.rcParams["xtick.major.width"] = 1.2
matplotlib.rcParams["ytick.major.width"] = 1.2


# ============================================================
# User settings
# ============================================================

CASE_NAME = "NYC_"


# ============================================================
# LCZ definition
# ============================================================

LCZ_CLASSES = [51, 52, 53]


# ============================================================
# Enhancement definition
# ============================================================
#
# Background:
#
#     -3 <= x* < 0
#
# Downwind enhancement:
#
#      1 <= x* <= 4
#
# ============================================================

BG_XMIN = -1.0
BG_XMAX = 0.0

DOWN_XMIN = 1.0
DOWN_XMAX = 4.0


# ============================================================
# Smoothing
# ============================================================

SMOOTH_SIGMA = 1.5


# ============================================================
# Bootstrap / permutation
# ============================================================

N_BOOT = 10000
N_PERM = 10000

RANDOM_SEED = 10


# ============================================================
# Plot
# ============================================================

SHOW_CITY_LABELS = True
LABEL_FONT_SIZE = 15


# ============================================================
# Output
# ============================================================

OUT_CSV = "111.csv"
OUT_FIG = "Fig1c.png"


# ============================================================
# Case directories
# ============================================================

case_dirs = [

    "./data",

]


# ============================================================
# Read LCZ percentage
# ============================================================

def read_lcz_percent(case_dir):

    txtfile = os.path.join(
        case_dir,
        "0LCZ",
        "LU_INDEX_51_61_numbers_region.txt"
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

                key, value = line.split(
                    ":",
                    1
                )

            else:

                key, value = line.split()

            counts[
                int(key.strip())
            ] = int(
                value.strip()
            )

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

    return (
        selected_count
        /
        total_urban
        *
        100.0
    )


# ============================================================
# City label
# ============================================================

def get_city_label(case_dir):

    return os.path.basename(
        os.path.normpath(
            case_dir
        )
    )


# ============================================================
# Find profile
# ============================================================

def find_profile_file(case_dir):

    data_dir = os.path.join(
        case_dir,
        "out"
    )

    candidates = [

        os.path.join(
            data_dir,
            f"{CASE_NAME}_NORM_PROFILE_BY_WIND.npz"
        ),

        os.path.join(
            data_dir,
            "NYC_NORM_PROFILE_BY_WIND.npz"
        ),

        os.path.join(
            data_dir,
            "NYC__NORM_PROFILE_BY_WIND.npz"
        ),

    ]

    candidates += sorted(
        glob.glob(
            os.path.join(
                data_dir,
                "*NORM_PROFILE_BY_WIND.npz"
            )
        )
    )

    seen = set()

    for filename in candidates:

        if filename in seen:
            continue

        seen.add(filename)

        if os.path.exists(filename):

            return filename

    raise FileNotFoundError(
        f"Cannot find profile file in {data_dir}"
    )


# ============================================================
# Read profile
# ============================================================

def read_city_profile(case_dir):

    infile = find_profile_file(
        case_dir
    )

    data = np.load(
        infile,
        allow_pickle=True
    )

    x = np.asarray(
        data["x_centers"],
        dtype=float
    )

    # ========================================================
    # Prefer raw mean profile if saved
    # ========================================================

    if "mean_profile" in data.files:

        precip_all = np.asarray(
            data["mean_profile"],
            dtype=float
        )

        profile_type = "raw"

    else:

        precip_all = np.asarray(
            data["mean_profile_norm"],
            dtype=float
        )

        profile_type = "normalized"

    if precip_all.ndim == 1:

        precip = precip_all.copy()

    else:

        precip = precip_all[0, :].copy()

    n_events = np.nan

    if "group_n" in data.files:

        group_n = np.asarray(
            data["group_n"]
        )

        if len(group_n) > 0:

            n_events = int(
                group_n[0]
            )

    return (
        x,
        precip,
        infile,
        n_events,
        profile_type,
    )


# ============================================================
# Smooth profile
# ============================================================

def smooth_profile(
    precip,
    sigma=1.5,
):

    precip = np.asarray(
        precip,
        dtype=float
    )

    if sigma is None or sigma <= 0:

        return precip.copy()

    valid = np.isfinite(
        precip
    )

    if np.sum(valid) < 2:

        return np.full_like(
            precip,
            np.nan
        )

    index = np.arange(
        len(precip)
    )

    precip_fill = precip.copy()

    precip_fill[~valid] = np.interp(

        index[~valid],

        index[valid],

        precip[valid],

    )

    return gaussian_filter1d(
        precip_fill,
        sigma=sigma
    )


# ============================================================
# Calculate x50
# ============================================================

def compute_enhancement_x50(
    x,
    precip,
    bg_xmin=-3.0,
    bg_xmax=0.0,
    down_xmin=1.0,
    down_xmax=4.0,
):

    x = np.asarray(
        x,
        dtype=float
    )

    precip = np.asarray(
        precip,
        dtype=float
    )


    # ========================================================
    # Upwind background
    # ========================================================

    bg_mask = (

        (x >= bg_xmin)

        &

        (x < bg_xmax)

        &

        np.isfinite(
            precip
        )

    )

    if np.sum(bg_mask) < 2:

        raise ValueError(
            "Not enough upwind points."
        )

    p_bg = float(
        np.nanmean(
            precip[
                bg_mask
            ]
        )
    )


    # ========================================================
    # Downwind region
    # ========================================================

    down_mask = (

        (x >= down_xmin)

        &

        (x <= down_xmax)

        &

        np.isfinite(
            precip
        )

    )

    if np.sum(down_mask) < 2:

        raise ValueError(
            "Not enough downwind points."
        )

    xd = x[
        down_mask
    ].copy()

    pd = precip[
        down_mask
    ].copy()


    # ========================================================
    # Sort
    # ========================================================

    order = np.argsort(
        xd
    )

    xd = xd[
        order
    ]

    pd = pd[
        order
    ]


    # ========================================================
    # Enhancement
    # ========================================================

    enhancement = (
        pd
        -
        p_bg
    )

    enhancement = np.maximum(
        enhancement,
        0.0
    )


    # ========================================================
    # Cumulative integral
    # ========================================================

    cumulative = np.zeros_like(
        xd,
        dtype=float
    )

    for i in range(
        1,
        len(xd)
    ):

        dx = (
            xd[i]
            -
            xd[i - 1]
        )

        area = (

            0.5

            *

            (
                enhancement[i]
                +
                enhancement[i - 1]
            )

            *

            dx

        )

        cumulative[i] = (
            cumulative[i - 1]
            +
            area
        )


    total_enhancement = cumulative[
        -1
    ]


    if (

        not np.isfinite(
            total_enhancement
        )

        or

        total_enhancement <= 0

    ):

        return (
            np.nan,
            p_bg,
            total_enhancement,
            xd,
            enhancement,
            cumulative,
        )


    # ========================================================
    # 50% cumulative enhancement
    # ========================================================

    target = (
        0.5
        *
        total_enhancement
    )


    # ========================================================
    # Interpolate exact x50
    # ========================================================

    x50 = np.interp(

        target,

        cumulative,

        xd,

    )


    return (
        float(x50),
        p_bg,
        total_enhancement,
        xd,
        enhancement,
        cumulative,
    )


# ============================================================
# Permutation test
# ============================================================

def permutation_test_slope(
    x,
    y,
    n_perm=10000,
    seed=10,
):

    rng = np.random.default_rng(
        seed
    )

    observed_slope = linregress(
        x,
        y
    ).slope

    perm_slopes = np.full(
        n_perm,
        np.nan
    )

    for i in range(n_perm):

        y_perm = rng.permutation(
            y
        )

        perm_slopes[i] = linregress(
            x,
            y_perm
        ).slope

    p_perm = (

        np.sum(

            np.abs(
                perm_slopes
            )

            >=

            np.abs(
                observed_slope
            )

        )

        + 1

    ) / (

        n_perm + 1

    )

    return (
        observed_slope,
        p_perm,
        perm_slopes,
    )


# ============================================================
# Bootstrap
# ============================================================

def bootstrap_regression(
    x,
    y,
    n_boot=10000,
    seed=10,
):

    rng = np.random.default_rng(
        seed
    )

    n = len(x)

    boot_slopes = np.full(
        n_boot,
        np.nan
    )

    boot_intercepts = np.full(
        n_boot,
        np.nan
    )

    boot_r = np.full(
        n_boot,
        np.nan
    )

    for i in range(n_boot):

        idx = rng.integers(
            0,
            n,
            size=n
        )

        xb = x[
            idx
        ]

        yb = y[
            idx
        ]

        if (
            np.nanmax(xb)
            ==
            np.nanmin(xb)
        ):

            continue

        reg = linregress(
            xb,
            yb
        )

        boot_slopes[i] = reg.slope

        boot_intercepts[i] = reg.intercept

        boot_r[i] = reg.rvalue

    return (
        boot_slopes,
        boot_intercepts,
        boot_r,
    )


# ============================================================
# MAIN
# ============================================================

records = []


for case_dir in case_dirs:

    city = get_city_label(
        case_dir
    )

    lcz = read_lcz_percent(
        case_dir
    )

    (
        x,
        precip,
        infile,
        n_events,
        profile_type,

    ) = read_city_profile(
        case_dir
    )


    precip_smooth = smooth_profile(

        precip,

        sigma=SMOOTH_SIGMA,

    )


    (
        x50,
        p_bg,
        total_enhancement,
        xd,
        enhancement,
        cumulative,

    ) = compute_enhancement_x50(

        x,

        precip_smooth,

        bg_xmin=BG_XMIN,

        bg_xmax=BG_XMAX,

        down_xmin=DOWN_XMIN,

        down_xmax=DOWN_XMAX,

    )


    records.append({

        "city":
            city,

        "lcz13_percent":
            lcz,

        "enhancement_x50":
            x50,

        "upwind_background":
            p_bg,

        "total_downwind_enhancement":
            total_enhancement,

        "n_events":
            n_events,

        "profile_type":
            profile_type,

        "profile_file":
            infile,

    })


    print(

        f"{city:15s} | "

        f"LCZ1-3 = {lcz:6.2f}% | "

        f"x50 = {x50:6.3f} | "

        f"Pbg = {p_bg:8.4f}"

    )


# ============================================================
# DataFrame
# ============================================================

df = pd.DataFrame(
    records
)


# ============================================================
# Remove invalid x50
# ============================================================

valid = (

    np.isfinite(
        df["lcz13_percent"]
    )

    &

    np.isfinite(
        df["enhancement_x50"]
    )

)


if not valid.all():

    print("")
    print("Cities without valid enhancement x50:")
    print(
        df.loc[
            ~valid,
            [
                "city",
                "total_downwind_enhancement",
            ]
        ]
    )


df_valid = df.loc[
    valid
].copy()


df_valid = df_valid.sort_values(
    "lcz13_percent"
).reset_index(
    drop=True
)


x_lcz = df_valid[
    "lcz13_percent"
].to_numpy()

y_x50 = df_valid[
    "enhancement_x50"
].to_numpy()


# ============================================================
# Statistics
# ============================================================

pearson_r, pearson_p = pearsonr(
    x_lcz,
    y_x50
)

spearman_rho, spearman_p = spearmanr(
    x_lcz,
    y_x50
)

reg = linregress(
    x_lcz,
    y_x50
)

slope = reg.slope
intercept = reg.intercept
linear_p = reg.pvalue
linear_r2 = reg.rvalue ** 2


(
    observed_slope,
    permutation_p,
    permutation_slopes,

) = permutation_test_slope(

    x_lcz,
    y_x50,

    n_perm=N_PERM,

    seed=RANDOM_SEED,

)


(
    boot_slopes,
    boot_intercepts,
    boot_r,

) = bootstrap_regression(

    x_lcz,
    y_x50,

    n_boot=N_BOOT,

    seed=RANDOM_SEED,

)


slope_ci_low, slope_ci_high = np.nanpercentile(

    boot_slopes,

    [2.5, 97.5],

)


# ============================================================
# Add statistics
# ============================================================

df["pearson_r"] = pearson_r
df["pearson_p"] = pearson_p

df["spearman_rho"] = spearman_rho
df["spearman_p"] = spearman_p

df["linear_slope"] = slope
df["linear_p"] = linear_p
df["linear_r2"] = linear_r2

df["permutation_p"] = permutation_p

df["slope_ci_low"] = slope_ci_low
df["slope_ci_high"] = slope_ci_high


df.to_csv(
    OUT_CSV,
    index=False
)


# ============================================================
# Print
# ============================================================

print("")
print("======================================================")
print("LCZ1--3 vs downwind precipitation enhancement x50")
print("======================================================")

print(
    f"N valid cities    = {len(df_valid)}"
)

print(
    f"Pearson r         = {pearson_r:.4f}"
)

print(
    f"Pearson p         = {pearson_p:.5f}"
)

print(
    f"Spearman rho      = {spearman_rho:.4f}"
)

print(
    f"Spearman p        = {spearman_p:.5f}"
)

print(
    f"Slope             = {slope:.6f}"
)

print(
    f"Regression p      = {linear_p:.5f}"
)

print(
    f"R2                = {linear_r2:.4f}"
)

print(
    f"Permutation p     = {permutation_p:.5f}"
)

print(
    "Slope 95% CI      = "
    f"[{slope_ci_low:.6f}, "
    f"{slope_ci_high:.6f}]"
)


# ============================================================
# Regression line
# ============================================================

xfit = np.linspace(

    np.nanmin(
        x_lcz
    ),

    np.nanmax(
        x_lcz
    ),

    300

)

yfit = (
    intercept
    +
    slope * xfit
)


# ============================================================
# Bootstrap confidence band
# ============================================================

valid_boot = (

    np.isfinite(
        boot_slopes
    )

    &

    np.isfinite(
        boot_intercepts
    )

)

yboot = (

    boot_intercepts[
        valid_boot,
        None
    ]

    +

    boot_slopes[
        valid_boot,
        None
    ]

    *

    xfit[
        None,
        :
    ]

)

yfit_low = np.nanpercentile(
    yboot,
    2.5,
    axis=0
)

yfit_high = np.nanpercentile(
    yboot,
    97.5,
    axis=0
)


# ============================================================
# Plot
# ============================================================

fig, ax = plt.subplots(
    figsize=(8.5, 6.0)
)

plt.subplots_adjust(
    left=0.16,
    bottom=0.17,
    right=0.97,
    top=0.96,
)


ax.fill_between(

    xfit,

    yfit_low,

    yfit_high,

    color="gray",

    alpha=0.25,

    linewidth=0,

    zorder=1,

)


ax.plot(

    xfit,

    yfit,

    color="black",

    linewidth=2.5,

    zorder=2,

)


ax.scatter(

    x_lcz,

    y_x50,

    s=90,

    facecolor="white",

    edgecolor="black",

    linewidth=1.5,

    zorder=3,

)


# ============================================================
# Urban edge
# ============================================================

ax.axhline(

    1.0,

    color="gray",

    linestyle="--",

    linewidth=1.2,

    zorder=0,

)


# ============================================================
# City labels
# ============================================================

if SHOW_CITY_LABELS:

    for _, row in df_valid.iterrows():

        ax.text(

            row["lcz13_percent"] + 0.10,

            row["enhancement_x50"] + 0.018,

            row["city"],

            fontsize=LABEL_FONT_SIZE,

            ha="left",

            va="bottom",

        )


# ============================================================
# Statistics
# ============================================================

textstr = (

    rf"Pearson $r={pearson_r:.2f}$, "
    rf"$p={pearson_p:.3f}$"
    "\n"

    rf"Spearman $\rho={spearman_rho:.2f}$, "
    rf"$p={spearman_p:.3f}$"
    "\n"

    rf"Slope $={slope:.3f}$"

)

ax.text(

    0.35,
    0.94,

    textstr,

    transform=ax.transAxes,

    fontsize=24,

    ha="left",

    va="top",

)


# ============================================================
# Axis labels
# ============================================================

ax.set_xlabel(
    r"LCZ1--3 coverage (\%)",fontsize =40
)

ax.set_ylabel(

    r"$x^{*}_{50}$",fontsize =40
)


ax.set_xlim(
    -0.2,
    21.8
)

ax.set_ylim(
    0.9,
    4.1
)


ax.grid(
    alpha=0.18
)


plt.savefig(
    OUT_FIG,
    dpi=300,
    bbox_inches="tight"
)

 
