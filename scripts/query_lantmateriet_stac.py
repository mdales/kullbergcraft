#!/usr/bin/env python3
"""
Query Lantmäteriet STAC API for elevation data around Kullberg, Sweden
Coordinates: 63.77°N, 17.02°E
"""

import requests
from requests.auth import HTTPBasicAuth
import json
import sys
import getpass
import os

# STAC API endpoint
STAC_API = "https://api.lantmateriet.se/stac-hojd/v1"

# Your Kullberg area of interest (from the GeoJSON)
BBOX = [16.918, 63.725, 17.122, 63.815]  # [west, south, east, north]

# Authentication credentials
# You can either hardcode them here or the script will prompt you
USERNAME = os.getenv("LANDMATERIET_USERNAME")  # Your Lantmäteriet username/email
PASSWORD = os.getenv("LANDMATERIET_PASSWORD")  # Your password or API token

def get_auth():
    """Get authentication credentials"""
    username = USERNAME
    password = PASSWORD

    if not username:
        username = input("Lantmäteriet username/email: ")
    if not password:
        password = getpass.getpass("Password/Token: ")

    return HTTPBasicAuth(username, password)

def explore_stac_api(auth):
    """Explore the STAC API structure"""
    print("=== Exploring STAC API ===\n")

    # 1. Get the root/landing page
    print("1. Fetching STAC root...")
    response = requests.get(f"{STAC_API}/", auth=auth)
    response.raise_for_status()
    root = response.json()

    print(f"   API Type: {root.get('type', 'Unknown')}")
    print(f"   Title: {root.get('title', 'N/A')}")
    print(f"   Description: {root.get('description', 'N/A')}")

    # 2. List available collections
    print("\n2. Fetching collections...")
    response = requests.get(f"{STAC_API}/collections", auth=auth)
    response.raise_for_status()
    collections = response.json()

    print(f"   Found {len(collections.get('collections', []))} collection(s):")
    for coll in collections.get('collections', []):
        print(f"   - {coll['id']}: {coll.get('title', 'No title')}")
        print(f"     Description: {coll.get('description', 'N/A')}")

    return collections

def search_items(auth, collection_id=None):
    """Search for items in the Kullberg area"""
    print(f"\n=== Searching for items in Kullberg area ===")
    print(f"Bounding box: {BBOX}")

    search_url = f"{STAC_API}/search"

    params = {
        "bbox": BBOX,  # Send as array, not comma-separated string
        "limit": 100
    }

    if collection_id:
        params["collections"] = [collection_id]

    print(f"\nQuerying: {search_url}")
    response = requests.post(search_url, json=params, auth=auth)
    response.raise_for_status()
    results = response.json()

    features = results.get('features', [])
    print(f"\nFound {len(features)} item(s)")

    for i, feature in enumerate(features[:10], 1):  # Show first 10
        print(f"\n--- Item {i} ---")
        print(f"ID: {feature.get('id')}")
        print(f"Collection: {feature.get('collection')}")

        props = feature.get('properties', {})
        print(f"Properties:")
        for key, value in list(props.items())[:5]:
            print(f"  - {key}: {value}")

        # Show assets (the actual data files)
        assets = feature.get('assets', {})
        print(f"Assets ({len(assets)}):")
        for asset_name, asset_info in assets.items():
            print(f"  - {asset_name}:")
            print(f"    URL: {asset_info.get('href', 'N/A')}")
            print(f"    Type: {asset_info.get('type', 'N/A')}")
            if 'title' in asset_info:
                print(f"    Title: {asset_info['title']}")

    return results

def download_asset(asset_url, output_path, auth):
    """Download a specific asset (e.g., GeoTIFF)"""
    print(f"\nDownloading {asset_url} to {output_path}...")

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
                print(f"\r  Progress: {percent:.1f}%", end='', flush=True)

    print(f"\nDownloaded successfully: {output_path}")

if __name__ == "__main__":
    try:
        # Get authentication credentials
        print("=== Lantmäteriet STAC API Query Tool ===\n")
        auth = get_auth()
        print("\nAuthentication configured.\n")

        # Step 1: Explore the API
        collections = explore_stac_api(auth)

        # Step 2: Search for items in the Kullberg area
        results = search_items(auth)

        # Step 3: Show how to download
        features = results.get('features', [])
        if features:
            print("\n=== To download data ===")
            print("Use the asset URLs shown above. For example:")

            first_feature = features[0]
            assets = first_feature.get('assets', {})

            for asset_name, asset_info in list(assets.items())[:1]:
                print(f"\ndownload_asset(")
                print(f"    '{asset_info.get('href')}',")
                print(f"    'kullberg_dem_{first_feature.get('id')}.tif',")
                print(f"    auth")
                print(f")")

            # Ask if user wants to download the first asset
            print("\n" + "="*60)
            download_first = input("\nDownload the first DEM tile? (y/n): ")
            if download_first.lower() == 'y':
                first_asset = list(assets.values())[0]
                output_file = f"kullberg_dem_{first_feature.get('id')}.tif"
                download_asset(first_asset['href'], output_file, auth)

        # Optionally save the search results
        with open('stac_search_results.json', 'w') as f:
            json.dump(results, f, indent=2)
        print("\nFull results saved to: stac_search_results.json")

    except requests.exceptions.HTTPError as e:
        print(f"\nHTTP Error: {e}")
        if e.response.status_code == 401:
            print("Authentication failed. Check your username and password.")
        print(f"Response: {e.response.text}")
    except requests.exceptions.RequestException as e:
        print(f"\nError: {e}")
    except KeyboardInterrupt:
        print("\n\nInterrupted by user.")
