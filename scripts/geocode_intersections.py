#!/usr/bin/env python3
"""
Geocode Rome intersections using OpenStreetMap Nominatim API.
Parses intersection names and finds real coordinates.
"""

import json
import time
import re
import urllib.request
import urllib.parse
from pathlib import Path

# Nominatim API endpoint
NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"

# Rome bounding box to restrict searches
ROME_VIEWBOX = "12.35,41.80,12.65,42.00"

# Cache for geocoding results to avoid duplicate requests
geocode_cache = {}

def clean_intersection_name(name):
    """
    Clean intersection name by removing codes and prefixes.
    Examples:
        "101-Cassia/Grottarossa" -> "Cassia/Grottarossa"
        "116-P.zza Villa Carpegna/Madonna del Riposo" -> "Piazza Villa Carpegna/Madonna del Riposo"
    """
    if not name:
        return ""

    # Remove leading number codes (e.g., "101-", "116-")
    name = re.sub(r'^\d+[-\s]*', '', name)

    # Expand common abbreviations
    abbreviations = {
        r'\bP\.zza\b': 'Piazza',
        r'\bP\.le\b': 'Piazzale',
        r'\bP\.za\b': 'Piazza',
        r'\bV\.le\b': 'Viale',
        r'\bV\.lo\b': 'Vicolo',
        r'\bL\.re\b': 'Lungotevere',
        r'\bL\.go\b': 'Largo',
        r'\bLgt\b': 'Lungotevere',
        r'\bC\.so\b': 'Corso',
        r'\bS\.\b': 'San',
    }

    for abbr, full in abbreviations.items():
        name = re.sub(abbr, full, name, flags=re.IGNORECASE)

    return name.strip()

def parse_street_names(name):
    """
    Parse intersection name to extract individual street names.
    Returns a list of street names.

    Examples:
        "Cassia/Grottarossa" -> ["Via Cassia", "Via Grottarossa"]
        "Piazza Villa Carpegna" -> ["Piazza Villa Carpegna"]
        "Boccea/Cornelia/Giureconsulti" -> ["Via Boccea", "Via Cornelia", "Via Giureconsulti"]
    """
    cleaned = clean_intersection_name(name)

    if not cleaned:
        return []

    # Split by "/" to get individual street names
    parts = [p.strip() for p in cleaned.split('/') if p.strip()]

    streets = []
    for part in parts:
        # Check if it already has a street type prefix
        has_prefix = any(part.lower().startswith(prefix) for prefix in
                        ['via ', 'viale ', 'piazza ', 'piazzale ', 'corso ', 'largo ',
                         'lungotevere ', 'vicolo ', 'ponte ', 'circonvallazione '])

        if has_prefix:
            streets.append(part)
        else:
            # Add "Via" prefix for regular street names
            streets.append(f"Via {part}")

    return streets

def geocode_location(query, attempt=1):
    """
    Geocode a location using Nominatim API.
    Returns (lat, lng) tuple or None if not found.
    """
    if query in geocode_cache:
        return geocode_cache[query]

    # Add Rome, Italy to the query
    full_query = f"{query}, Roma, Italia"

    params = {
        'q': full_query,
        'format': 'json',
        'limit': 1,
        'viewbox': ROME_VIEWBOX,
        'bounded': 1,
    }

    url = f"{NOMINATIM_URL}?{urllib.parse.urlencode(params)}"

    headers = {
        'User-Agent': 'RadarProjectManagement/1.0 (radar-dashboard-geocoding)'
    }

    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())

            if data and len(data) > 0:
                result = (float(data[0]['lat']), float(data[0]['lon']))
                geocode_cache[query] = result
                return result
    except Exception as e:
        print(f"  Error geocoding '{query}': {e}")
        if attempt < 3:
            time.sleep(2)
            return geocode_location(query, attempt + 1)

    geocode_cache[query] = None
    return None

def geocode_intersection(name):
    """
    Geocode an intersection by trying multiple strategies.
    """
    streets = parse_street_names(name)

    if not streets:
        return None

    # Strategy 1: If it's a single place (piazza, largo, etc.), search directly
    if len(streets) == 1:
        result = geocode_location(streets[0])
        if result:
            return result

    # Strategy 2: Search for intersection of two streets
    if len(streets) >= 2:
        # Try "street1 & street2"
        intersection_query = f"{streets[0]} & {streets[1]}"
        result = geocode_location(intersection_query)
        if result:
            return result

        # Try just the first street
        result = geocode_location(streets[0])
        if result:
            return result

        # Try just the second street
        result = geocode_location(streets[1])
        if result:
            return result

    # Strategy 3: Try the cleaned name directly
    cleaned = clean_intersection_name(name)
    if cleaned:
        result = geocode_location(cleaned)
        if result:
            return result

    return None

def geocode_all_intersections(intersections, batch_size=50):
    """
    Geocode all intersections with rate limiting.
    Nominatim requires max 1 request per second.
    """
    total = len(intersections)
    geocoded = 0
    failed = []

    print(f"Geocoding {total} intersections...")
    print("This will take approximately {:.0f} minutes due to API rate limits.".format(total * 1.5 / 60))
    print("-" * 60)

    for i, intersection in enumerate(intersections):
        name = intersection.get('name', '')
        existing_coords = intersection.get('coordinates')

        # Skip if already has coordinates
        if existing_coords and existing_coords.get('lat') and existing_coords.get('lng'):
            geocoded += 1
            continue

        print(f"[{i+1}/{total}] Geocoding: {name}")

        coords = geocode_intersection(name)

        if coords:
            intersection['coordinates'] = {'lat': coords[0], 'lng': coords[1]}
            geocoded += 1
            print(f"  -> Found: {coords[0]:.6f}, {coords[1]:.6f}")
        else:
            failed.append({'id': intersection.get('id'), 'name': name})
            print(f"  -> NOT FOUND")

        # Rate limiting: Nominatim requires max 1 request/second
        time.sleep(1.1)

        # Progress update every batch_size
        if (i + 1) % batch_size == 0:
            print(f"\n--- Progress: {i+1}/{total} ({geocoded} geocoded, {len(failed)} failed) ---\n")

    return geocoded, failed

def main():
    data_dir = Path(__file__).parent.parent / "data"

    # Load intersections
    intersections_file = data_dir / "intersections.json"
    with open(intersections_file, 'r', encoding='utf-8') as f:
        intersections = json.load(f)

    print(f"Loaded {len(intersections)} intersections")

    # Geocode all intersections
    geocoded, failed = geocode_all_intersections(intersections)

    # Save updated intersections
    with open(intersections_file, 'w', encoding='utf-8') as f:
        json.dump(intersections, f, ensure_ascii=False, indent=2)

    print("\n" + "=" * 60)
    print(f"GEOCODING COMPLETE")
    print(f"Successfully geocoded: {geocoded}/{len(intersections)}")
    print(f"Failed: {len(failed)}")

    if failed:
        print("\nFailed intersections:")
        for f in failed[:20]:  # Show first 20
            print(f"  - {f['id']}: {f['name']}")
        if len(failed) > 20:
            print(f"  ... and {len(failed) - 20} more")

        # Save failed list
        failed_file = data_dir / "geocoding_failed.json"
        with open(failed_file, 'w', encoding='utf-8') as f:
            json.dump(failed, f, ensure_ascii=False, indent=2)
        print(f"\nFull list saved to: {failed_file}")

    print("\nNow regenerating embedded-data.js...")

    # Regenerate embedded data
    with open(data_dir / "summary.json", 'r', encoding='utf-8') as f:
        summary = json.load(f)

    js_content = f"""/**
 * Embedded Data
 * This file contains the intersection data embedded directly to avoid CORS issues
 * when opening the HTML file directly from the filesystem.
 *
 * Generated with geocoded coordinates from OpenStreetMap Nominatim.
 */

const EMBEDDED_DATA = {{
    intersections: {json.dumps(intersections, ensure_ascii=False)},
    summary: {json.dumps(summary, ensure_ascii=False)}
}};
"""

    js_dir = Path(__file__).parent.parent / "js"
    with open(js_dir / "embedded-data.js", 'w', encoding='utf-8') as f:
        f.write(js_content)

    print("Done! embedded-data.js has been updated with geocoded coordinates.")

if __name__ == "__main__":
    main()
