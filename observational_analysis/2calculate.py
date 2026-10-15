import xarray as xr
import numpy as np
import pandas as pd

ncfile = "./geo_em.d01.nc"

varname = "LU_INDEX"

# ===== set your lat/lon range =====
lat_min = 40.2
lat_max = 41.2
lon_min = -74.2
lon_max = -73.7
# ==================================
 

ds = xr.open_dataset(ncfile)

lu = ds[varname].squeeze().values
lat = ds["XLAT_M"].squeeze().values
lon = ds["XLONG_M"].squeeze().values

# mask for selected lat/lon region
region_mask = (
    (lat >= lat_min) & (lat <= lat_max) &
    (lon >= lon_min) & (lon <= lon_max)
)

categories = range(51, 62)

results = []
for cat in categories:
    count = int(np.sum((lu == cat) & region_mask))
    results.append({"category": cat, "number": count})
    print(f"{cat}: {count}")

df = pd.DataFrame(results)


out_txt = "LU_INDEX_51_61_numbers_region.txt"



with open(out_txt, "w") as f:
    for row in results:
        f.write(f"{row['category']}: {row['number']}\n")


ds.close()
