import matplotlib.pyplot as plt
import numpy as np
import matplotlib
import os

# -----------------------------
# matplotlib settings
# -----------------------------
 
font = {'family' : 'serif', 'size' :30}
matplotlib.rc('font', **font)
plt.rc('legend', fontsize=30)
plt.rc('legend', frameon=False)
plt.rc('text',usetex=True)
fig, ax = plt.subplots(figsize=(8.3,5.5))
plt.subplots_adjust(left=0.12, bottom=0.16, right=0.95,top=0.95)




plt.rc('legend', fontsize=30)
plt.rc('legend', frameon=False)
plt.rc('text', usetex=True)

 

plt.subplots_adjust(
    left=0.15,
    bottom=0.15,
    right=0.97,
    top=0.95
)

# -----------------------------
# case directories 
# -----------------------------
case_dirs = [
    "./data",
]

# -----------------------------
# colormap
# -----------------------------
# -----------------------------
# colormap
# -----------------------------
cmap = plt.get_cmap('jet')

# 用于统一颜色范围
all_rain = []

# -----------------------------
# first pass:
# collect all rainfall values
# -----------------------------
for case_dir in case_dirs:

    DATA_DIR = os.path.join(case_dir, "out")
    CASE_NAME = "NYC_"

    IN_FILE = os.path.join(
        DATA_DIR,
        f"{CASE_NAME}_NORM_PROFILE_BY_WIND.npz"
    )

    data = np.load(IN_FILE, allow_pickle=True)

    y_all = data["mean_profile_norm"]

    rain = y_all[0, :]

    all_rain.extend(rain)

all_rain = np.array(all_rain)

vmin = np.min(all_rain)
vmax = np.max(all_rain)




# -----------------------------
# y bins
# -----------------------------
BIN_SIZE = 5.0
y_bins = np.arange(0, 20 + BIN_SIZE, BIN_SIZE)
y_centers = 0.5 * (y_bins[:-1] + y_bins[1:])

# store rainfall profiles by y-bin
rain_sum = None
rain_count = None
x_ref = None


# -----------------------------
# second pass:
# collect profiles into LCZ1-3 bins
# -----------------------------
for case_dir in case_dirs:

    # ---------------------------------
    # read LCZ percentages
    # ---------------------------------
    txtfile = os.path.join(
        case_dir,
        "0LCZ",
        "LU_INDEX_51_61_numbers_region.txt"
    )

    counts = {}

    with open(txtfile, "r") as f:
        for line in f:
            line = line.strip()

            if not line:
                continue

            if ":" in line:
                key, value = line.split(":")
            else:
                key, value = line.split()

            counts[int(key.strip())] = int(value.strip())

    groups = {
        "LCZ1-3": [51, 52, 53],
        "LCZ4-6": [54, 55, 56],
        "LCZ7-11": [57, 58, 59, 60, 61],
    }

    total = sum(counts.get(i, 0) for i in range(51, 62))

    group_sum = sum(counts.get(cat, 0) for cat in groups["LCZ1-3"])

    lcz13_percent = group_sum / total * 100 if total > 0 else np.nan

    # ---------------------------------
    # read rainfall profile
    # ---------------------------------
    DATA_DIR = os.path.join(case_dir, "out")
    CASE_NAME = "NYC_"

    IN_FILE = os.path.join(
        DATA_DIR,
        f"{CASE_NAME}_NORM_PROFILE_BY_WIND.npz"
    )

    data = np.load(IN_FILE, allow_pickle=True)

    x = data["x_centers"]
    rain = data["mean_profile_norm"][0, :]   # all events

    if x_ref is None:
        x_ref = x.copy()
        nx = len(x_ref)
        rain_sum = np.zeros((len(y_centers), nx))
        rain_count = np.zeros((len(y_centers), nx))

    # find LCZ1-3 bin
    y_bin_idx = np.searchsorted(y_bins, lcz13_percent, side="right") - 1

    if y_bin_idx < 0 or y_bin_idx >= len(y_centers):
        continue

    valid = np.isfinite(rain)

    rain_sum[y_bin_idx, valid] += rain[valid]
    rain_count[y_bin_idx, valid] += 1

    print(
        case_dir,
        f"LCZ1-3={lcz13_percent:.2f}%",
        f"bin={y_bins[y_bin_idx]:.1f}-{y_bins[y_bin_idx+1]:.1f}%"
    )





# -----------------------------
# calculate binned mean rainfall
# -----------------------------
rain_bin_mean = np.full_like(rain_sum, np.nan, dtype=float)

valid_count = rain_count > 0
rain_bin_mean[valid_count] = rain_sum[valid_count] / rain_count[valid_count]

vmin = np.nanmin(rain_bin_mean)
vmax = np.nanmax(rain_bin_mean)

from scipy.ndimage import gaussian_filter
from scipy.ndimage import gaussian_filter1d
# -----------------------------
# smooth rainfall field
# -----------------------------
rain_plot = rain_bin_mean.copy()

# 处理 NaN，避免 smooth 出问题
nan_mask = ~np.isfinite(rain_plot)
rain_plot[nan_mask] = np.nanmean(rain_plot)

 
rain_smooth = gaussian_filter1d(
    rain_bin_mean,
    sigma=1.5,
    axis=1
)

# 把原来没有数据的位置重新设为 NaN
rain_smooth[nan_mask] = np.nan

# -----------------------------
# better colormap
# -----------------------------
cmap = plt.get_cmap("jet")   # 比 jet 更顺滑
# cmap = plt.get_cmap("Spectral_r")
# cmap = plt.get_cmap("viridis")

vmin = 0.1
vmax = 0.75

# -----------------------------
# plot smooth heatmap
# -----------------------------
im = ax.imshow(
    rain_smooth,
    origin="lower",
    aspect="auto",
    extent=[x_ref[0], x_ref[-1], y_bins[0], y_bins[-1]],
    cmap=cmap,
    vmin=vmin,
    vmax=vmax,
    interpolation="nearest"
)
 

# -----------------------------
# axis settings
# -----------------------------
ax.set_xlabel(r"$x^*$")
 
ax.set_ylabel(r"LCZ1-3 coverage (\%)")


# -----------------------------
# only search peak in -3 <= x <= -1
# -----------------------------
xmask = (x_ref >= -1.0) & (x_ref <=4.0)

peak_x = []
peak_y = []
peak_val = []

for i in range(len(y_centers)):

    row = rain_smooth[i, :]

    if np.all(np.isnan(row[xmask])):
        continue

    subrow = row[xmask]
    subx   = x_ref[xmask]

    idx = np.nanargmax(subrow)

    peak_x.append(subx[idx])
    peak_y.append(y_centers[i])
    peak_val.append(subrow[idx])

    print(
        f"LCZ bin {y_bins[i]:.0f}-{y_bins[i+1]:.0f}%: "
        f"max={subrow[idx]:.3f} "
        f"at x={subx[idx]:.2f}"
    )


ax.plot(
    peak_x,
    peak_y,
    color="white",
    linewidth=3
)

ax.scatter(
    peak_x,
    peak_y,
    s=100,
    color="white",
    edgecolor="black",
    zorder=10
)


# x axis 不变
ax.set_xlim(-1.5, 4.0)
ax.set_xticks([-1, 0, 1, 2, 3, 4])
ax.set_xticklabels(['-1', '0', '1', '2', '3', '4'])
 
 

 
cbar = plt.colorbar(im, ax=ax)

cbar.set_label(r"$P^*$")

plt.text(
    0.5, 0.03,
    "Urban",
    transform=ax.get_xaxis_transform(),
    ha="center",
    va="bottom",
    fontsize=30
)

plt.text(
    -0.7, 0.03,
    "Upwind",
    transform=ax.get_xaxis_transform(),
    ha="center",
    va="bottom",
    fontsize=30
)

plt.text(
    2.5, 0.03,
    "Downwind",
    transform=ax.get_xaxis_transform(),
    ha="center",
    va="bottom",
    fontsize=30
)
 
plt.axvline(0, linestyle="--", color="lightgray",linewidth=1)
plt.axvline(1, linestyle="--", color="lightgray",linewidth=1)
plt.axvspan(0, 1, color="gray", alpha=0.4)


# -----------------------------
# save
# -----------------------------
plt.savefig(
    "Fig1b.png",
    dpi=300,
    bbox_inches="tight"
)

 
