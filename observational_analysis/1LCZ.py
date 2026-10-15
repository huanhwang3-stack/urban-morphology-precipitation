import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl
import matplotlib.ticker as mticker
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from netCDF4 import Dataset
from matplotlib.patches import Circle
# =========================
# Font (HPC-friendly, Times-like)
# =========================
plt.rcParams["font.family"] = "STIXGeneral"
plt.rcParams["font.size"] = 22

# =========================
# Helper: format degree to deg+min (115°30′E)
# =========================
def _deg_to_degmin(val):
    sign = 1 if val >= 0 else -1
    aval = abs(val)
    deg = int(np.floor(aval + 1e-12))
    minutes = int(np.round((aval - deg) * 60))
    if minutes == 60:
        deg += 1
        minutes = 0
    return sign, deg, minutes

def lon_degmin_formatter(x, pos=None):
    sign, deg, minutes = _deg_to_degmin(x)
    hemi = "E" if sign >= 0 else "W"
    if minutes == 0:
        return f"{deg}°{hemi}"
    return f"{deg}°{minutes:02d}′{hemi}"

def lat_degmin_formatter(y, pos=None):
    sign, deg, minutes = _deg_to_degmin(y)
    hemi = "N" if sign >= 0 else "S"
    if minutes == 0:
        return f"{deg}°{hemi}"
    return f"{deg}°{minutes:02d}′{hemi}"

# =========================
# Input: geo_em for the domain you want
# =========================
ncfile = '/glade/work/huanwang/WRF/WPS_2BEP2/geo_em.d01.nc'   # <-- change to your path

with Dataset(ncfile) as nc:
    lu  = nc.variables["LU_INDEX"][0, :, :].astype(int)
    lat = nc.variables["XLAT_M"][0, :, :]
    lon = nc.variables["XLONG_M"][0, :, :]
# classes present (ignore 0)
cats = np.unique(lu)
cats = cats[cats > 0]

# =========================
# Label map: follow your table
# =========================
label_map = {
    1:  "Evergreen Needleleaf Forest",
    2:  "Evergreen Broadleaf Forest",
    3:  "Deciduous Needleleaf Forest",
    4:  "Deciduous Broadleaf Forest",
    5:  "Mixed Forests",
    6:  "Closed Shrublands",
    7:  "Open Shrublands",
    8:  "Woody Savannas",
    9:  "Savannas",
    10: "Grasslands",
    11: "Permanent wetlands",
    12: "Croplands",
    13: "Urban and Built-Up",
    14: "Cropland/natural vegetation mosaic",
    15: "Snow and Ice",
    16: "Barren or Sparsely Vegetated",
    17: "Water",
    18: "Wooded Tundra",
    19: "Mixed Tundra",
    20: "Barren Tundra",
}

# 21-50 are Unassigned in your table
for k in range(21, 51):
    label_map[k] = "Unassigned"

# LCZ 51-61: LCZ_1 ... LCZ_11
for k in range(51, 62):
    label_map[k] = f"LCZ_{k-50}"

# =========================
# Color map
# =========================
color_map_hex = {
    # Water / Ice
    17: "#2c4a9a",   # Water
    15: "#e6e6e6",   # snow/ice

    # Urban (legacy)
    13: "#f4a3a3",

    # Crops / mosaic
    12: "#f5d67a",
    14: "#c2b7ff",

    # Wetlands
    11: "#e15aa7",

    # Forests
    1: "#2d7f3b",
    2: "#1f8f2a",
    3: "#3fae2a",
    4: "#2f9a00",
    5: "#6f8f1a",

    # Shrub/grass/savanna
    6:  "#9bbd2a",
    7:  "#bfe36c",
    8:  "#a9d030",
    9:  "#b8d63a",
    10: "#d7df4a",

    # Tundra-ish
    18: "#cccccc",
    19: "#cccccc",
    20: "#cccccc",

    # Barren
    16: "#b07d4f",
}

# Unassigned 21-50 light gray
for k in range(21, 51):
    color_map_hex[k] = "#dddddd"

# LCZ colors (orange gradient)
lcz_colors = {
    51: "#67000d",  # darkest red
    52: "#8c0d18",
    53: "#b2182b",
    54: "#d7301f",
    55: "#ef3b2c",
    56: "#fb6a4a",
    57: "#fc8d59",
    58: "#fdae6b",
    59: "#fdd49e",
    60: "#fee6ce",
    61: "#fff5eb",  # shallow orange
}
color_map_hex.update(lcz_colors)

# =========================
# Legend ordering
# LCZ first, then Urban, Water, Snow/Ice, then natural, then Unassigned
# =========================
legend_order = []
legend_order += [c for c in range(51, 62) if c in cats]  # LCZ 51-61
legend_order += [c for c in [13, 17, 15] if c in cats]   # Urban, Water, Snow/Ice
legend_order += [c for c in range(1, 21) if c in cats and c not in legend_order]
legend_order += [c for c in range(21, 51) if c in cats]  # Unassigned last

remaining = [c for c in cats if c not in legend_order]
cats_ordered = legend_order + remaining

# Map LU_INDEX -> 0..N-1 in ordered scheme
cat_to_idx = {c: i for i, c in enumerate(cats_ordered)}
lu_idx = np.vectorize(lambda x: cat_to_idx.get(int(x), -1))(lu)

# Discrete colormap following cats_ordered
colors = [mpl.colors.to_rgba(color_map_hex.get(int(c), "#cccccc")) for c in cats_ordered]
cmap = mpl.colors.ListedColormap(colors)
norm = mpl.colors.BoundaryNorm(np.arange(-0.5, len(cats_ordered) + 0.5, 1), cmap.N)

# =========================
# Figure / map
# =========================
proj = ccrs.PlateCarree()
fig = plt.figure(figsize=(7, 6), dpi=200)
ax = plt.axes(projection=proj)

lon_min, lon_max = float(lon.min()), float(lon.max())
lat_min, lat_max = float(lat.min()), float(lat.max())
ax.set_extent([lon_min, lon_max, lat_min, lat_max], crs=proj)

# Basemap (optional)
ax.add_feature(cfeature.COASTLINE.with_scale("10m"), linewidth=0.5)
ax.add_feature(cfeature.BORDERS.with_scale("10m"), linewidth=0.4)
ax.add_feature(cfeature.STATES.with_scale("10m"), linewidth=0.3, edgecolor="gray")

# Plot landuse (NO smoothing)
im = ax.pcolormesh(
    lon, lat, lu_idx,
    cmap=cmap, norm=norm,
    transform=proj,
    shading="nearest"
)

# Optional: keep gridlines without labels
# gl = ax.gridlines(draw_labels=False, linewidth=0.4, color="k", alpha=0.4, linestyle="--")

# Remove x/y ticks and labels
ax.set_xticks([])
ax.set_yticks([])
ax.set_xlabel("")
ax.set_ylabel("")

# =========================
# Crop to NYC 50 km circle area
# =========================
nyc_lon = -74.0060
nyc_lat = 40.7128
radius_km = 50.0

# 50 km -> degree buffer
dlat = radius_km / 111.0
dlon = radius_km / (111.0 * np.cos(np.deg2rad(nyc_lat)))

ax.set_extent(
    [nyc_lon - dlon, nyc_lon + dlon,
     nyc_lat - dlat, nyc_lat + dlat],
    crs=ccrs.PlateCarree()
)

# Make axes square, important for circular output
ax.set_aspect("equal", adjustable="box")

# Remove x/y ticks and labels
ax.set_xticks([])
ax.set_yticks([])
ax.set_xlabel("")
ax.set_ylabel("")
ax.set_axis_off()

# =========================
# Circular clipping
# =========================
circle_clip = Circle(
    (0.5, 0.5),
    0.5,
    transform=ax.transAxes
)

for artist in ax.get_children():
    try:
        artist.set_clip_path(circle_clip)
    except Exception:
        pass

# Draw circular boundary
circle_boundary = Circle(
    (0.5, 0.5),
    0.5,
    transform=ax.transAxes,
    facecolor="none",
    edgecolor="black",
    linewidth=2.0,
    zorder=100
)
ax.add_patch(circle_boundary)

# White background outside circle
ax.patch.set_facecolor("white")
fig.patch.set_facecolor("white")

# IMPORTANT: do not save before this
plt.savefig(
    "1LCZ_circle.png",
    dpi=300,
    bbox_inches="tight",
    pad_inches=0.02,
    facecolor="white"
)

plt.close(fig)


