#!/usr/bin/env python3
"""
Improved Geocoder for Rome Intersections
Properly handles:
1. Name standardization (removing prefixes, expanding abbreviations)
2. Single location geocoding (piazzas, streets)
3. Intersection geocoding (finding where two streets meet)
"""

import json
import time
import re
import urllib.request
import urllib.parse
from pathlib import Path

# Nominatim API endpoint
NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"

# Rome bounding box
ROME_BBOX = {
    'viewbox': '12.35,41.75,12.65,42.05',
    'bounded': 1
}

# Geocoding cache
cache = {}
cache_file = Path(__file__).parent.parent / "data" / "geocode_cache.json"

# Rate limiting
last_request_time = 0
MIN_REQUEST_INTERVAL = 1.1  # Nominatim requires max 1 request/second

# Abbreviation mappings
ABBREVIATIONS = {
    r'\bP\.zza\b': 'Piazza',
    r'\bP\.za\b': 'Piazza',
    r'\bP\.le\b': 'Piazzale',
    r'\bV\.le\b': 'Viale',
    r'\bV\.lo\b': 'Vicolo',
    r'\bL\.re\b': 'Lungotevere',
    r'\bLgt\b': 'Lungotevere',
    r'\bL\.go\b': 'Largo',
    r'\bC\.so\b': 'Corso',
    r'\bS\.\s': 'San ',
    r'\bS\.S\.\b': 'Santi',
    r'\bV\.E\.\b': 'Vittorio Emanuele',
    r'\bV\.e\.\b': 'Vittorio Emanuele',
    r'\bE\.Filiberto\b': 'Emanuele Filiberto',
    r'\bG\.Cesare\b': 'Giulio Cesare',
    r'\bM\.llo\b': 'Maresciallo',
    r'\bGen\.\b': 'Generale',
}

# Street type prefixes
STREET_TYPES = [
    'via', 'viale', 'piazza', 'piazzale', 'corso', 'largo', 'lungotevere',
    'vicolo', 'ponte', 'circonvallazione', 'via di', 'viale di', 'piazza di'
]


def load_cache():
    """Load geocoding cache from file."""
    global cache
    if cache_file.exists():
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                cache = json.load(f)
            print(f"Loaded {len(cache)} cached results")
        except:
            cache = {}


def save_cache():
    """Save geocoding cache to file."""
    with open(cache_file, 'w', encoding='utf-8') as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)


def standardize_name(name):
    """
    Standardize an intersection name:
    1. Remove numeric prefix (e.g., "101-")
    2. Expand abbreviations
    3. Clean up whitespace
    """
    if not name:
        return ""

    # Remove leading numeric code (e.g., "101-", "20034-")
    name = re.sub(r'^\d+[-\s]*', '', name)

    # Expand abbreviations
    for pattern, replacement in ABBREVIATIONS.items():
        name = re.sub(pattern, replacement, name, flags=re.IGNORECASE)

    # Clean up whitespace
    name = ' '.join(name.split())

    return name.strip()


def parse_intersection(name):
    """
    Parse an intersection name into its component streets.
    Returns: (street1, street2) or (single_location, None)
    """
    standardized = standardize_name(name)

    if not standardized:
        return (None, None)

    # Split by "/" to get component streets
    parts = [p.strip() for p in standardized.split('/') if p.strip()]

    if len(parts) == 1:
        # Single location
        return (parts[0], None)
    else:
        # Intersection of two or more streets
        # Take first two
        return (parts[0], parts[1])


def add_street_prefix(street_name):
    """
    Add 'Via' prefix if the street name doesn't have a type prefix.
    """
    name_lower = street_name.lower()

    # Check if it already has a street type
    for prefix in STREET_TYPES:
        if name_lower.startswith(prefix + ' '):
            return street_name

    # Add "Via" prefix
    return f"Via {street_name}"


def rate_limit():
    """Ensure we don't exceed Nominatim rate limits."""
    global last_request_time
    elapsed = time.time() - last_request_time
    if elapsed < MIN_REQUEST_INTERVAL:
        time.sleep(MIN_REQUEST_INTERVAL - elapsed)
    last_request_time = time.time()


def nominatim_search(query, retries=3):
    """
    Search Nominatim API for a location.
    Returns: {'lat': float, 'lon': float, 'display_name': str} or None
    """
    # Check cache first
    cache_key = query.lower()
    if cache_key in cache:
        return cache[cache_key]

    rate_limit()

    params = {
        'q': query,
        'format': 'json',
        'limit': 1,
        'addressdetails': 1,
        **ROME_BBOX
    }

    url = f"{NOMINATIM_URL}?{urllib.parse.urlencode(params)}"
    headers = {
        'User-Agent': 'RadarConfigDashboard/2.0 (geocoding Rome intersections)'
    }

    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode())

                if data and len(data) > 0:
                    result = {
                        'lat': float(data[0]['lat']),
                        'lon': float(data[0]['lon']),
                        'display_name': data[0].get('display_name', ''),
                        'type': data[0].get('type', ''),
                        'class': data[0].get('class', '')
                    }
                    cache[cache_key] = result
                    return result
                else:
                    cache[cache_key] = None
                    return None

        except Exception as e:
            print(f"  Attempt {attempt + 1} failed: {e}")
            if attempt < retries - 1:
                time.sleep(2)

    cache[cache_key] = None
    return None


def geocode_single_location(location_name):
    """
    Geocode a single location (piazza, largo, etc.)
    """
    # Try with Roma, Italia suffix
    query = f"{location_name}, Roma, Italia"
    result = nominatim_search(query)

    if result:
        return result

    # Try adding Via prefix if not already present
    with_via = add_street_prefix(location_name)
    if with_via != location_name:
        query = f"{with_via}, Roma, Italia"
        result = nominatim_search(query)
        if result:
            return result

    return None


def geocode_intersection(street1, street2):
    """
    Geocode an intersection between two streets.
    Tries multiple strategies to find the intersection point.
    """
    # Add Via prefix if needed
    street1_full = add_street_prefix(street1)
    street2_full = add_street_prefix(street2)

    # Strategy 1: Search for "Street1 & Street2, Roma"
    query = f"{street1_full} & {street2_full}, Roma, Italia"
    result = nominatim_search(query)
    if result:
        return result

    # Strategy 2: Search for "incrocio Street1 Street2, Roma"
    query = f"incrocio {street1} {street2}, Roma, Italia"
    result = nominatim_search(query)
    if result:
        return result

    # Strategy 3: Try with "angolo" (corner)
    query = f"{street1_full} angolo {street2_full}, Roma, Italia"
    result = nominatim_search(query)
    if result:
        return result

    # Strategy 4: Search for first street only (less accurate but better than nothing)
    query = f"{street1_full}, Roma, Italia"
    result = nominatim_search(query)
    if result:
        # Mark as lower confidence since we only found one street
        result['confidence'] = 'low'
        result['note'] = f"Only found {street1_full}, not the intersection"
        return result

    # Strategy 5: Try second street
    query = f"{street2_full}, Roma, Italia"
    result = nominatim_search(query)
    if result:
        result['confidence'] = 'low'
        result['note'] = f"Only found {street2_full}, not the intersection"
        return result

    return None


def geocode_intersection_name(name):
    """
    Main geocoding function. Handles both single locations and intersections.
    Returns: {'lat': float, 'lon': float, 'confidence': str, ...} or None
    """
    street1, street2 = parse_intersection(name)

    if not street1:
        return None

    if street2:
        # It's an intersection
        result = geocode_intersection(street1, street2)
        if result and 'confidence' not in result:
            result['confidence'] = 'high'
    else:
        # Single location
        result = geocode_single_location(street1)
        if result:
            result['confidence'] = 'high'

    return result


def process_intersections(intersections):
    """
    Process all intersections and geocode them.
    """
    total = len(intersections)
    geocoded = 0
    failed = []
    low_confidence = []

    print(f"\nProcessing {total} intersections...")
    print("=" * 60)

    for i, intersection in enumerate(intersections):
        name = intersection.get('name', '')
        existing_manual = intersection.get('coordinates_manual', False)

        # Skip if manually positioned
        if existing_manual:
            print(f"[{i+1}/{total}] {name} - SKIPPED (manually positioned)")
            geocoded += 1
            continue

        print(f"[{i+1}/{total}] Geocoding: {name}")

        result = geocode_intersection_name(name)

        if result:
            intersection['coordinates'] = {
                'lat': result['lat'],
                'lng': result['lon']
            }
            intersection['geocode_confidence'] = result.get('confidence', 'medium')

            if result.get('confidence') == 'low':
                low_confidence.append({
                    'id': intersection.get('id'),
                    'name': name,
                    'note': result.get('note', '')
                })
                print(f"  -> LOW CONFIDENCE: {result['lat']:.5f}, {result['lon']:.5f}")
            else:
                print(f"  -> Found: {result['lat']:.5f}, {result['lon']:.5f}")

            geocoded += 1
        else:
            failed.append({
                'id': intersection.get('id'),
                'name': name
            })
            print(f"  -> NOT FOUND")

        # Save cache periodically
        if (i + 1) % 20 == 0:
            save_cache()

    # Final cache save
    save_cache()

    return geocoded, failed, low_confidence


def main():
    """Main function."""
    data_dir = Path(__file__).parent.parent / "data"

    # Load cache
    load_cache()

    # Load intersections
    intersections_file = data_dir / "intersections.json"
    with open(intersections_file, 'r', encoding='utf-8') as f:
        intersections = json.load(f)

    print(f"Loaded {len(intersections)} intersections")

    # Process intersections
    geocoded, failed, low_confidence = process_intersections(intersections)

    # Print summary
    print("\n" + "=" * 60)
    print("GEOCODING SUMMARY")
    print("=" * 60)
    print(f"Total: {len(intersections)}")
    print(f"Successfully geocoded: {geocoded}")
    print(f"Failed: {len(failed)}")
    print(f"Low confidence: {len(low_confidence)}")

    if failed:
        print(f"\nFailed intersections:")
        for f in failed[:20]:
            print(f"  - {f['id']}: {f['name']}")
        if len(failed) > 20:
            print(f"  ... and {len(failed) - 20} more")

    if low_confidence:
        print(f"\nLow confidence (needs review):")
        for lc in low_confidence[:20]:
            print(f"  - {lc['id']}: {lc['name']}")
            if lc.get('note'):
                print(f"    Note: {lc['note']}")
        if len(low_confidence) > 20:
            print(f"  ... and {len(low_confidence) - 20} more")

    # Save updated intersections
    with open(intersections_file, 'w', encoding='utf-8') as f:
        json.dump(intersections, f, ensure_ascii=False, indent=2)
    print(f"\nSaved to {intersections_file}")

    # Regenerate embedded data
    print("\nRegenerating embedded-data.js...")

    summary_file = data_dir / "summary.json"
    if summary_file.exists():
        with open(summary_file, 'r', encoding='utf-8') as f:
            summary = json.load(f)
    else:
        summary = {'total_intersections': len(intersections)}

    js_content = f"""/**
 * Embedded Data - Geocoded with improved intersection detection
 * Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}
 * Total intersections: {len(intersections)}
 * Geocoded: {geocoded}
 * Low confidence: {len(low_confidence)}
 * Failed: {len(failed)}
 */

const EMBEDDED_DATA = {{
    intersections: {json.dumps(intersections, ensure_ascii=False)},
    summary: {json.dumps(summary, ensure_ascii=False)}
}};
"""

    js_dir = Path(__file__).parent.parent / "js"
    with open(js_dir / "embedded-data.js", 'w', encoding='utf-8') as f:
        f.write(js_content)

    print("Done!")


if __name__ == "__main__":
    main()
