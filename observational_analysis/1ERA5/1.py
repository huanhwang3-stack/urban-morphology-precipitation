import os
import cdsapi

# ============================================================
# ERA5 pressure-level wind download
# NYC region, JJA, 2001-2024
# ============================================================

OUTDIR = "./ERA5_pressure_wind_NYC_JJA_2020_2024"
os.makedirs(OUTDIR, exist_ok=True)

START_YEAR = 2020
END_YEAR = 2024


# NYC / surrounding region
# CDS area format is [North, West, South, East]
# Your IMERG BBOX was: min_lon,min_lat,max_lon,max_lat
# -75.2,39.9,-72.6,41.6
AREA = [
    43.5,   # North
    -77.5,  # West
    37.5,   # South
    -70.5,  # East
]

client = cdsapi.Client()

for year in range(START_YEAR, END_YEAR + 1):

    outfile = os.path.join(
        OUTDIR,
        f"ERA5_uv_850_NYC_JJA_{year}.nc"
    )

    if os.path.exists(outfile):
        print(f"[SKIP] {outfile} already exists")
        continue

    print("=" * 80)
    print(f"Downloading ERA5 pressure-level winds for {year} JJA")
    print(f"Output: {outfile}")
    print("=" * 80)

    request = {
        "product_type": ["reanalysis"],
        "variable": [
            "u_component_of_wind",
            "v_component_of_wind",
        ],
        "pressure_level": [
            "850",
        ],
        "year": [str(year)],
       "month": [ "06", "07", "08",],
        "day": [
            "01", "02", "03", "04", "05", "06", "07",
            "08", "09", "10", "11", "12", "13", "14",
            "15", "16", "17", "18", "19", "20", "21",
            "22", "23", "24", "25", "26", "27", "28",
            "29", "30", "31",
        ],
        "time": [
            "00:00", "01:00", "02:00", "03:00",
            "04:00", "05:00", "06:00", "07:00",
            "08:00", "09:00", "10:00", "11:00",
            "12:00", "13:00", "14:00", "15:00",
            "16:00", "17:00", "18:00", "19:00",
            "20:00", "21:00", "22:00", "23:00",
        ],
        "data_format": "netcdf",
        "download_format": "unarchived",
        "area": AREA,
    }

    client.retrieve(
        "reanalysis-era5-pressure-levels",
        request,
        outfile
    )

print("All ERA5 wind downloads complete.")
