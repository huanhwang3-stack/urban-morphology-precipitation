import os
import requests
from tqdm import tqdm
from typing import Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

# ============================================================
# NASA CMR settings
# ============================================================
CMR_BASE_URL = "https://cmr.earthdata.nasa.gov"

SHORT_NAME = "GPM_3IMERGHH"
VERSION = "07"

# ============================================================
# Time range: JJA only, 2001-2024
# ============================================================

START_YEAR = 2020
END_YEAR = 2024

# ============================================================
# Region: New York domain
# Format: min_lon,min_lat,max_lon,max_lat
# ============================================================
FILTER_BBOX = "-77.5,37.5,-70.5,43.5"
 

# Optional filters
FILTER_SEARCH = ""
FILTER_CLOUD_COVER_MIN = ""
FILTER_CLOUD_COVER_MAX = ""

# ============================================================
# Output directory
# Each year will be saved as:
# ./GPM_3IMERGHH_07_NYC_JJA_2001_2024/2001_JJA/
# ./GPM_3IMERGHH_07_NYC_JJA_2001_2024/2002_JJA/
# ...
# ============================================================
DOWNLOAD_DIR_BASE = f"./{SHORT_NAME}_{VERSION}_NYC_JJA_{START_YEAR}_{END_YEAR}"

# Parallel download workers
MAX_WORKERS = 10

os.makedirs(DOWNLOAD_DIR_BASE, exist_ok=True)


def query_cmr_granules(
    short_name: str,
    version: str,
    page_size: int = 2000,
    search_after: Optional[str] = None,
    **extra_params
):
    """
    Query the CMR granules endpoint.

    Args:
        short_name: Collection short name
        version: Collection version
        page_size: Results per page
        search_after: Pagination token
        extra_params: Additional query parameters

    Returns:
        tuple: (response, items)
    """
    url = f"{CMR_BASE_URL}/search/granules.umm_json"

    params = {
        "short_name": short_name,
        "version": version,
        "page_size": page_size,
        **extra_params,
    }

    headers = {"Accept": "application/json"}

    if search_after:
        headers["CMR-Search-After"] = search_after

    response = requests.get(url, params=params, headers=headers, timeout=120)

    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError:
        print("Failed to fetch granules:")
        print(response.text)
        raise

    data = response.json()
    items = data.get("items", [])

    return response, items


def fetch_total_granules_count_from_cmr(
    short_name: str,
    version: str,
    **params
):
    """
    Fetch total number of granules matching filters.
    """
    response, _ = query_cmr_granules(
        short_name,
        version,
        page_size=1,
        **params
    )

    data = response.json()
    return data.get("hits", 0)


def collect_download_urls(
    short_name: str,
    version: str,
    total_granules: int,
    page_size: int = 2000,
    **params
):
    """
    Collect all GET DATA URLs from CMR search results.
    """
    search_after_value = None
    all_download_urls = []
    granules_without_urls = 0

    print("Collecting download URLs...")

    with tqdm(total=total_granules, desc="Collecting URLs", unit="granule") as pbar:
        while True:
            response, items = query_cmr_granules(
                short_name=short_name,
                version=version,
                page_size=page_size,
                search_after=search_after_value,
                **params
            )

            if not items:
                break

            for item in items:
                pbar.update(1)

                related_urls = item.get("umm", {}).get("RelatedUrls", [])
                download_urls = []

                for related_url in related_urls:
                    if related_url.get("Type") == "GET DATA":
                        url = related_url.get("URL")
                        if url:
                            download_urls.append(url)

                if download_urls:
                    all_download_urls.extend(download_urls)
                else:
                    granules_without_urls += 1

            search_after_value = response.headers.get("CMR-Search-After")

            if not search_after_value:
                break

    print(f"Found {len(all_download_urls)} files to download")

    if granules_without_urls > 0:
        print(f"{granules_without_urls} granules have no download URLs")

    return all_download_urls


def download_file(url: str, download_dir: str):
    """
    Download a single file.

    Returns:
        tuple: (status, filename)
               status in ["success", "skipped", "failed"]
    """
    filename = os.path.basename(url)
    local_filename = os.path.join(download_dir, filename)

    if os.path.exists(local_filename):
        return "skipped", filename

    try:
        with requests.get(url, stream=True, timeout=120) as r:
            r.raise_for_status()

            with open(local_filename, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)

        return "success", filename

    except Exception as e:
        print(f"Error downloading {filename}: {e}")
        return "failed", filename


def download_data_from_cmr(
    short_name: str,
    version: str,
    total_granules: int,
    download_dir: str,
    page_size: int = 2000,
    **params
):
    """
    Fetch granules from CMR and download all GET DATA files.
    """
    os.makedirs(download_dir, exist_ok=True)

    all_download_urls = collect_download_urls(
        short_name=short_name,
        version=version,
        total_granules=total_granules,
        page_size=page_size,
        **params
    )

    if len(all_download_urls) == 0:
        print("No download URLs found.")
        return

    downloaded_count = 0
    skipped_count = 0
    failed_count = 0

    with tqdm(total=len(all_download_urls), desc="Downloading files", unit="file") as pbar:
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            future_to_url = {
                executor.submit(download_file, url, download_dir): url
                for url in all_download_urls
            }

            for future in as_completed(future_to_url):
                try:
                    status, filename = future.result()
                except Exception as e:
                    failed_count += 1
                    print(f"Unexpected error: {e}")
                    pbar.update(1)
                    continue

                if status == "success":
                    downloaded_count += 1
                elif status == "skipped":
                    skipped_count += 1
                else:
                    failed_count += 1

                pbar.set_postfix(
                    downloaded=downloaded_count,
                    skipped=skipped_count,
                    failed=failed_count
                )
                pbar.update(1)

    print(f"Downloaded: {downloaded_count} files")
    print(f"Skipped: {skipped_count} files")
    print(f"Failed: {failed_count} files")


def build_filter_params_for_year(year: int):
    """
    Build CMR filter parameters for one JJA season.
    """
    filter_temporal = (
       f"{year}-06-01T00:00:00.000Z,"
       f"{year}-08-31T23:59:00.000Z"
    )

    filter_params = {
        "temporal": filter_temporal,
        "bounding_box": FILTER_BBOX,
    }

    if FILTER_SEARCH:
        filter_params["producer_granule_id[]"] = FILTER_SEARCH
        filter_params["options[producer_granule_id][pattern]"] = "true"

    if FILTER_CLOUD_COVER_MIN and FILTER_CLOUD_COVER_MAX:
        filter_params["cloud_cover"] = (
            f"{FILTER_CLOUD_COVER_MIN},{FILTER_CLOUD_COVER_MAX}"
        )

    return filter_temporal, filter_params


def main():
    """
    Main entry point.
    Download IMERG half-hourly data for NYC region, JJA only, 2001-2024.
    """

    print("=" * 80)
    print("GPM IMERG half-hourly download")
    print(f"Product: {SHORT_NAME}")
    print(f"Version: {VERSION}")
    print(f"Years: {START_YEAR}-{END_YEAR}")
    print("Season: JJA")
    print(f"BBOX: {FILTER_BBOX}")
    print(f"Output base directory: {DOWNLOAD_DIR_BASE}")
    print("=" * 80)

    for year in range(START_YEAR, END_YEAR + 1):

        filter_temporal, filter_params = build_filter_params_for_year(year)

        year_dir = os.path.join(DOWNLOAD_DIR_BASE, f"{year}_JJA")
        os.makedirs(year_dir, exist_ok=True)

        print("\n" + "=" * 80)
        print(f"Year: {year}")
        print(f"Temporal filter: {filter_temporal}")
        print(f"Download directory: {year_dir}")
        print("=" * 80)

        total_granules = fetch_total_granules_count_from_cmr(
            SHORT_NAME,
            VERSION,
            **filter_params
        )

        print(f"Total granules for {year} JJA: {total_granules:,}")

        if total_granules == 0:
            print(f"No granules found for {year}. Skipping.")
            continue

        download_data_from_cmr(
            SHORT_NAME,
            VERSION,
            total_granules,
            download_dir=year_dir,
            **filter_params
        )

    print("\nAll JJA downloads complete.")


if __name__ == "__main__":
    main()
