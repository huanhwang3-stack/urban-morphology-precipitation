import os
import re
import glob
import h5py
import numpy as np
import xarray as xr
from netCDF4 import Dataset
from datetime import datetime

# ============================================================
# User settings
# ============================================================
IMERG_DIR = "/glade/derecho/scratch/huanwang/00Analysis/1NY/2IMERGE/GPM_3IMERGHH_07_NYC_JJA_2020_2024"

ERA5_FILES = sorted(glob.glob(
    "/glade/derecho/scratch/huanwang/00Analysis/1NY/1ERA5/ERA5_uv_850_NYC_JJA_*.nc"
))

GEO_EM_FILE = "./0LCZ/geo_em.d01.nc"

OUT_DIR = "./out"
os.makedirs(OUT_DIR, exist_ok=True)

CASE_NAME = "NYC_"


BBOX = (-77.5, 37.5, -70.5, 43.5)
CITY_BBOX = (-74.25, 40.4, -73.4, 41.1)

URBAN_LU_CLASSES = [13] + list(range(51, 62))

WIND_LEVEL_HPA = 850
MIN_BOX_MEAN_MMHR = 0.1
CROSSWIND_BUFFER_KM = 30.0

X_BINS = np.arange(-3.0, 4.01, 0.1)
IMERG_DT_HOURS = 1.0

N_JOBS = 4


# ============================================================
# Helpers
# ============================================================
def read_geo_urban_fraction_mask(geo_file,  city_bbox):
    with Dataset(geo_file) as nc:
        lat = nc.variables["XLAT_M"][0, :, :]
        lon = nc.variables["XLONG_M"][0, :, :]

        if "LU_INDEX" not in nc.variables:
            raise KeyError(f"Cannot find LU_INDEX in {geo_file}")

        lu = np.squeeze(nc.variables["LU_INDEX"][:])

    minlon, minlat, maxlon, maxlat = city_bbox

    city_box_mask = (
        (lon >= minlon) & (lon <= maxlon) &
        (lat >= minlat) & (lat <= maxlat)
    )

    urban_mask = np.isin(lu, URBAN_LU_CLASSES) & city_box_mask

    if np.sum(city_box_mask) == 0:
        raise RuntimeError("CITY_BBOX does not overlap geo_em domain.")

    if np.sum(urban_mask) == 0:
        vals = np.unique(lu[city_box_mask])
        raise RuntimeError(f"No urban pixels found. LU_INDEX in CITY_BBOX: {vals}")

    return lon, lat, lu, urban_mask

def parse_imerg_time_from_filename(fname):
    base = os.path.basename(fname)
    m = re.search(r"(\d{8})-S(\d{6})", base)
    if m is None:
        return None
    return datetime.strptime(m.group(1) + m.group(2), "%Y%m%d%H%M%S")


def lonlat_to_xy_km(lon, lat, lon0, lat0):
    x = (lon - lon0) * 111.0 * np.cos(np.deg2rad(lat0))
    y = (lat - lat0) * 111.0
    return x, y


def rotate_precomputed_xy(dx, dy, u_mean, v_mean):
    speed = np.sqrt(u_mean ** 2 + v_mean ** 2)
    if speed < 1.0e-6:
        raise ValueError("Wind speed too small.")

    ex = u_mean / speed
    ey = v_mean / speed

    x_down = dx * ex + dy * ey
    y_cross = -dx * ey + dy * ex

    return x_down, y_cross

 

def find_precip_variable(f):
    if "Grid/precipitation" in f:
        return "Grid/precipitation"
    if "Grid/precipitationCal" in f:
        return "Grid/precipitationCal"
    raise KeyError("Cannot find precipitation variable.")


def prepare_imerg_grid(first_file, bbox):
    minlon, minlat, maxlon, maxlat = bbox

    with h5py.File(first_file, "r") as f:
        lon = f["Grid/lon"][:]
        lat = f["Grid/lat"][:]
        pvar = find_precip_variable(f)
        shape = np.squeeze(f[pvar]).shape

    lon_idx = np.where((lon >= minlon) & (lon <= maxlon))[0]
    lat_idx = np.where((lat >= minlat) & (lat <= maxlat))[0]

    if lon_idx.size == 0 or lat_idx.size == 0:
        raise RuntimeError("IMERG bbox does not overlap lon/lat grid.")

    lon_slice = slice(lon_idx[0], lon_idx[-1] + 1)
    lat_slice = slice(lat_idx[0], lat_idx[-1] + 1)

    lon_sub = lon[lon_slice]
    lat_sub = lat[lat_slice]

    if shape == (len(lon), len(lat)):
        orientation = "lon_lat"
    elif shape == (len(lat), len(lon)):
        orientation = "lat_lon"
    else:
        raise RuntimeError(f"Unexpected IMERG shape: {shape}")

    lon2d, lat2d = np.meshgrid(lon_sub, lat_sub)

    return {
        "lon_slice": lon_slice,
        "lat_slice": lat_slice,
        "orientation": orientation,
        "lon2d": lon2d,
        "lat2d": lat2d,
    }


def read_imerg_precip_sub(fname, imerg_grid):
    lon_slice = imerg_grid["lon_slice"]
    lat_slice = imerg_grid["lat_slice"]
    orientation = imerg_grid["orientation"]

    with h5py.File(fname, "r") as f:
        pvar = find_precip_variable(f)
        dset = f[pvar]

        if orientation == "lat_lon":
            p_sub = np.squeeze(dset)[lat_slice, lon_slice]
        elif orientation == "lon_lat":
            p_sub = np.squeeze(dset)[lon_slice, lat_slice].T
        else:
            raise RuntimeError(f"Unknown orientation: {orientation}")

    p_sub = p_sub.astype(float)
    p_sub[p_sub < 0] = np.nan

    return p_sub


def open_era5_wind(era5_files):
    if len(era5_files) == 0:
        raise RuntimeError("No ERA5 files found.")

    datasets = [xr.open_dataset(f) for f in era5_files]
    ds = xr.combine_by_coords(datasets, combine_attrs="override")

    if "valid_time" in ds.coords:
        time_name = "valid_time"
    elif "time" in ds.coords:
        time_name = "time"
    else:
        raise KeyError("Cannot find ERA5 time coordinate.")

    if "pressure_level" in ds.coords:
        lev_name = "pressure_level"
    elif "level" in ds.coords:
        lev_name = "level"
    else:
        raise KeyError("Cannot find ERA5 pressure coordinate.")

    if "u" not in ds or "v" not in ds:
        raise KeyError("Cannot find ERA5 u/v.")

    return ds, time_name, lev_name


def prepare_era5_mean_wind(era5_files, level_hpa, bbox):
    minlon, minlat, maxlon, maxlat = bbox

    ds, time_name, lev_name = open_era5_wind(era5_files)
    dsl = ds.sel({lev_name: level_hpa}, method="nearest")

    lons = dsl["longitude"]
    if float(lons.max()) > 180:
        minlon2 = minlon % 360
        maxlon2 = maxlon % 360
    else:
        minlon2 = minlon
        maxlon2 = maxlon

    lat_vals = dsl["latitude"].values
    if lat_vals[0] > lat_vals[-1]:
        dsl_box = dsl.sel(
            longitude=slice(minlon2, maxlon2),
            latitude=slice(maxlat, minlat),
        )
    else:
        dsl_box = dsl.sel(
            longitude=slice(minlon2, maxlon2),
            latitude=slice(minlat, maxlat),
        )

    spatial_dims = []
    for dim in ["latitude", "longitude"]:
        if dim in dsl_box["u"].dims:
            spatial_dims.append(dim)

    u_mean = dsl_box["u"].mean(dim=spatial_dims).load()
    v_mean = dsl_box["v"].mean(dim=spatial_dims).load()

    times = dsl_box[time_name].values.astype("datetime64[ns]")
    u_values = u_mean.values.astype(float)
    v_values = v_mean.values.astype(float)

    ds.close()

    order = np.argsort(times)

    return times[order], u_values[order], v_values[order]


def nearest_era5_wind(t, era_times, era_u, era_v):
    t64 = np.datetime64(t, "ns")
    idx = np.searchsorted(era_times, t64)

    if idx <= 0:
        j = 0
    elif idx >= era_times.size:
        j = era_times.size - 1
    else:
        before = idx - 1
        after = idx
        if abs(era_times[after] - t64) < abs(t64 - era_times[before]):
            j = after
        else:
            j = before

    return float(era_u[j]), float(era_v[j])


def fast_binned_mean(x_norm, y_cross, y_center, cross_limit, values, x_bins):
    nbins = len(x_bins) - 1
    out = np.full(nbins, np.nan)

    valid = (
        np.isfinite(x_norm) &
        np.isfinite(y_cross) &
        np.isfinite(values) &
        (np.abs(y_cross - y_center) <= cross_limit) &
        (x_norm >= x_bins[0]) &
        (x_norm < x_bins[-1])
    )

    if not np.any(valid):
        return out

    x_valid = x_norm[valid]
    v_valid = values[valid]

    bin_idx = np.searchsorted(x_bins, x_valid, side="right") - 1
    good = (bin_idx >= 0) & (bin_idx < nbins)

    if not np.any(good):
        return out

    bin_idx = bin_idx[good]
    v_valid = v_valid[good]

    sums = np.bincount(bin_idx, weights=v_valid, minlength=nbins)
    counts = np.bincount(bin_idx, minlength=nbins)

    ok = counts > 0
    out[ok] = sums[ok] / counts[ok]

    return out


def process_one_imerg_file(
    fname,
    imerg_grid,
    grid_dx,
    grid_dy,
    urban_dx,
    urban_dy,
    era_times,
    era_u,
    era_v,
):
    t = parse_imerg_time_from_filename(fname)
    if t is None:
        return None

    try:
        precip_rate = read_imerg_precip_sub(fname, imerg_grid)
    except Exception:
        return None

    box_mean = np.nanmean(precip_rate)

    if not np.isfinite(box_mean) or box_mean < MIN_BOX_MEAN_MMHR:
        return None

    try:
        u_mean, v_mean = nearest_era5_wind(t, era_times, era_u, era_v)
    except Exception:
        return None

    speed = np.sqrt(u_mean ** 2 + v_mean ** 2)

    if speed < 1.0e-6:
        return None

    try:
        x_down, y_cross = rotate_precomputed_xy(
            grid_dx, grid_dy, u_mean, v_mean
        )
        x_urb, y_urb = rotate_precomputed_xy(
            urban_dx, urban_dy, u_mean, v_mean
        )
    except Exception:
        return None

    x_up_edge = np.nanmin(x_urb)
    x_down_edge = np.nanmax(x_urb)
    lc = x_down_edge - x_up_edge

    if not np.isfinite(lc) or lc < 5.0:
        return None

    y_center = 0.5 * (np.nanmin(y_urb) + np.nanmax(y_urb))
    y_half_width = 0.5 * (np.nanmax(y_urb) - np.nanmin(y_urb))
    cross_limit = y_half_width + CROSSWIND_BUFFER_KM

    x_norm = (x_down - x_up_edge) / lc

    profile_rate = fast_binned_mean(
        x_norm=x_norm,
        y_cross=y_cross,
        y_center=y_center,
        cross_limit=cross_limit,
        values=precip_rate,
        x_bins=X_BINS,
    )

    if np.all(~np.isfinite(profile_rate)):
        return None

    profile_amount = profile_rate * IMERG_DT_HOURS

    return {
        "profile_rate": profile_rate,
        "profile_amount": profile_amount,
        "time": np.datetime64(t),
        "speed": speed,
        "u": u_mean,
        "v": v_mean,
        "lc": lc,
        "box_mean": box_mean,
        "x_up_edge": x_up_edge,
        "x_down_edge": x_down_edge,
        "cross_limit": cross_limit,
    }


# ============================================================
# Main
# ============================================================

def main():
    print("Reading urban mask...")

    geo_lon, geo_lat, lu_index, urban_mask= read_geo_urban_fraction_mask(
        GEO_EM_FILE,
        CITY_BBOX,
    )

    urban_lon = geo_lon[urban_mask]
    urban_lat = geo_lat[urban_mask]
    urban_frac_values = lu_index[urban_mask]

    lon0 = float(np.nanmean(urban_lon))
    lat0 = float(np.nanmean(urban_lat))

    urban_dx, urban_dy = lonlat_to_xy_km(
        urban_lon,
        urban_lat,
        lon0,
        lat0,
    )

    print("Finding IMERG files...")

    imerg_files = sorted(
        glob.glob(os.path.join(IMERG_DIR, "**", "*.HDF5"), recursive=True) +
        glob.glob(os.path.join(IMERG_DIR, "**", "*.h5"), recursive=True) +
        glob.glob(os.path.join(IMERG_DIR, "**", "*.H5"), recursive=True)
    )

    imerg_files = [
        f for f in imerg_files
        if parse_imerg_time_from_filename(f) is not None
    ]

    if len(imerg_files) == 0:
        raise RuntimeError(f"No IMERG files found under {IMERG_DIR}")

    print(f"Found {len(imerg_files)} IMERG files.")

    print("Preparing IMERG grid...")

    imerg_grid = prepare_imerg_grid(imerg_files[0], BBOX)

    lon2d = imerg_grid["lon2d"]
    lat2d = imerg_grid["lat2d"]

    grid_dx, grid_dy = lonlat_to_xy_km(
        lon2d,
        lat2d,
        lon0,
        lat0,
    )

    print("Preparing ERA5 wind...")

    era_times, era_u, era_v = prepare_era5_mean_wind(
        ERA5_FILES,
        WIND_LEVEL_HPA,
        BBOX,
    )

    print(f"Loaded ERA5 wind time steps: {era_times.size}")
    print("Processing IMERG events...")

    if N_JOBS == 1:
        results = [
            process_one_imerg_file(
                fname,
                imerg_grid,
                grid_dx,
                grid_dy,
                urban_dx,
                urban_dy,
                era_times,
                era_u,
                era_v,
            )
            for fname in imerg_files
        ]
    else:
        try:
            from joblib import Parallel, delayed

            results = Parallel(n_jobs=N_JOBS, backend="loky", verbose=10)(
                delayed(process_one_imerg_file)(
                    fname,
                    imerg_grid,
                    grid_dx,
                    grid_dy,
                    urban_dx,
                    urban_dy,
                    era_times,
                    era_u,
                    era_v,
                )
                for fname in imerg_files
            )
        except ImportError:
            print("joblib not found. Falling back to serial mode.")

            results = [
                process_one_imerg_file(
                    fname,
                    imerg_grid,
                    grid_dx,
                    grid_dy,
                    urban_dx,
                    urban_dy,
                    era_times,
                    era_u,
                    era_v,
                )
                for fname in imerg_files
            ]

    results = [r for r in results if r is not None]

    if len(results) == 0:
        raise RuntimeError("No valid precipitation events.")

    print(f"Valid precipitation events: {len(results)}")

    profile_rates = np.asarray([r["profile_rate"] for r in results])
    profile_amounts = np.asarray([r["profile_amount"] for r in results])

    times_used = np.asarray([r["time"] for r in results])
    speed_used = np.asarray([r["speed"] for r in results])
    u_used = np.asarray([r["u"] for r in results])
    v_used = np.asarray([r["v"] for r in results])
    lc_used = np.asarray([r["lc"] for r in results])
    box_mean_used = np.asarray([r["box_mean"] for r in results])
    x_up_edge_used = np.asarray([r["x_up_edge"] for r in results])
    x_down_edge_used = np.asarray([r["x_down_edge"] for r in results])
    cross_limit_used = np.asarray([r["cross_limit"] for r in results])

    x_centers = 0.5 * (X_BINS[:-1] + X_BINS[1:])

    out_file = os.path.join(
        OUT_DIR,
        f"{CASE_NAME}_EVENT_PROFILES_RAW.npz"
    )

    np.savez_compressed(
        out_file,

        case_name=CASE_NAME,

        x_bins=X_BINS,
        x_centers=x_centers,
        x_normalization="event_specific_lc",

        profile_rates=profile_rates,
        profile_amounts=profile_amounts,

        times_used=times_used,
        speed_used=speed_used,
        u_used=u_used,
        v_used=v_used,
        lc_used=lc_used,
        box_mean_used=box_mean_used,

        x_up_edge_used=x_up_edge_used,
        x_down_edge_used=x_down_edge_used,
        cross_limit_used=cross_limit_used,

        lon0=lon0,
        lat0=lat0,
        bbox=np.asarray(BBOX),
        city_bbox=np.asarray(CITY_BBOX),

        urban_frac_var="LU_INDEX",
        urban_frac_threshold=np.nan,
        urban_pixel_count=urban_lon.size,
        mean_urban_frac_selected_pixels=float(np.nanmean(urban_frac_values)),

        wind_level_hpa=WIND_LEVEL_HPA,
        crosswind_buffer_km=CROSSWIND_BUFFER_KM,
        min_box_mean_mmhr=MIN_BOX_MEAN_MMHR,
        imerg_dt_hours=IMERG_DT_HOURS,
    )

    print(f"Wrote {out_file}")
    print("Done.")


if __name__ == "__main__":
    main()
