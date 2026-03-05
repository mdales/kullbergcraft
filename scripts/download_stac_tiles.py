#!/usr/bin/env python3
"""
Download all DEM tiles from STAC search results
Reads stac_search_results.json and downloads all elevation data assets
"""

import requests
from requests.auth import HTTPBasicAuth
import json
import os
import getpass
from pathlib import Path

# Authentication credentials
USERNAME = os.getenv("LANDMATERIET_USERNAME")
PASSWORD = os.getenv("LANDMATERIET_PASSWORD")

# Output directory for downloaded tiles
OUTPUT_DIR = "dem_tiles"

def get_auth():
    """Get authentication credentials"""
    username = USERNAME
    password = PASSWORD

    if not username:
        username = input("Lantmäteriet username/email: ")
    if not password:
        password = getpass.getpass("Password/Token: ")

    return HTTPBasicAuth(username, password)

def download_asset(asset_url, output_path, auth):
    """Download a specific asset (e.g., GeoTIFF) with progress indicator"""
    print(f"Downloading: {output_path}")

    response = requests.get(asset_url, stream=True, auth=auth)
    response.raise_for_status()

    total_size = int(response.headers.get('content-length', 0))
    downloaded = 0

    with open(output_path, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
            downloaded += len(chunk)
            if total_size > 0:
                percent = (downloaded / total_size) * 100
                mb_downloaded = downloaded / (1024 * 1024)
                mb_total = total_size / (1024 * 1024)
                print(f"\r  Progress: {percent:.1f}% ({mb_downloaded:.1f}/{mb_total:.1f} MB)",
                      end='', flush=True)
    print()  # New line after progress

def download_all_tiles(results_file="stac_search_results.json", output_dir=OUTPUT_DIR):
    """Download all DEM tiles from the search results"""

    # Create output directory
    Path(output_dir).mkdir(exist_ok=True)

    # Load search results
    print(f"Loading search results from: {results_file}")
    with open(results_file, 'r') as f:
        results = json.load(f)

    features = results.get('features', [])
    print(f"Found {len(features)} tile(s) to download\n")

    if not features:
        print("No tiles found in search results!")
        return

    # Get authentication
    auth = get_auth()
    print()

    # Download each tile
    downloaded = []
    skipped = []
    failed = []

    for i, feature in enumerate(features, 1):
        feature_id = feature.get('id', f'unknown_{i}')
        collection = feature.get('collection', 'unknown')

        print(f"\n[{i}/{len(features)}] Processing: {feature_id}")
        print(f"  Collection: {collection}")

        # Get the assets
        assets = feature.get('assets', {})

        # Look for the main elevation data asset
        # Common asset names: 'data', 'elevation', 'dem', or the first asset
        asset_name = None
        asset_info = None

        # Try common names first
        for name in ['data', 'elevation', 'dem', 'geotiff']:
            if name in assets:
                asset_name = name
                asset_info = assets[name]
                break

        # If not found, just use the first asset
        if not asset_info and assets:
            asset_name = list(assets.keys())[0]
            asset_info = assets[asset_name]

        if not asset_info:
            print("  ⚠️  No assets found, skipping")
            skipped.append(feature_id)
            continue

        asset_url = asset_info.get('href')
        asset_type = asset_info.get('type', 'unknown')

        print(f"  Asset: {asset_name} ({asset_type})")

        # Generate output filename
        # Use collection and feature ID to make it unique
        output_filename = f"{collection}_{feature_id}.tif"
        output_path = os.path.join(output_dir, output_filename)

        # Check if already downloaded
        if os.path.exists(output_path):
            file_size = os.path.getsize(output_path)
            print(f"  ✓ Already exists ({file_size / (1024*1024):.1f} MB), skipping")
            skipped.append(feature_id)
            continue

        # Download the asset
        try:
            download_asset(asset_url, output_path, auth)
            file_size = os.path.getsize(output_path)
            print(f"  ✓ Downloaded successfully ({file_size / (1024*1024):.1f} MB)")
            downloaded.append(output_path)
        except Exception as e:
            print(f"  ✗ Failed: {e}")
            failed.append(feature_id)
            # Clean up partial download
            if os.path.exists(output_path):
                os.remove(output_path)

    # Summary
    print("\n" + "="*60)
    print("Download Summary:")
    print(f"  Downloaded: {len(downloaded)} tile(s)")
    print(f"  Skipped: {len(skipped)} tile(s)")
    print(f"  Failed: {len(failed)} tile(s)")

    if downloaded:
        print(f"\nTiles saved to: {os.path.abspath(output_dir)}/")
        print("\nDownloaded files:")
        for filepath in downloaded:
            print(f"  - {os.path.basename(filepath)}")

    if failed:
        print("\nFailed downloads:")
        for feature_id in failed:
            print(f"  - {feature_id}")

    return downloaded, skipped, failed

if __name__ == "__main__":
    import sys

    # Allow custom results file as argument
    results_file = sys.argv[1] if len(sys.argv) > 1 else "stac_search_results.json"

    if not os.path.exists(results_file):
        print(f"Error: {results_file} not found!")
        print("\nRun the query script first to generate search results.")
        sys.exit(1)

    try:
        downloaded, skipped, failed = download_all_tiles(results_file)

        if downloaded:
            print("\n" + "="*60)
            print("Next steps:")
            print("1. View a tile: gdalinfo dem_tiles/<filename>.tif")
            print("2. Create a mosaic: gdal_merge.py -o merged.tif dem_tiles/*.tif")
            print("3. Or create a VRT: gdalbuildvrt mosaic.vrt dem_tiles/*.tif")

    except KeyboardInterrupt:
        print("\n\nDownload interrupted by user.")
    except Exception as e:
        print(f"\n\nError: {e}")
        import traceback
        traceback.print_exc()
