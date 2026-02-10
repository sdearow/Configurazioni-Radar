#!/usr/bin/env python3
"""
Batch Geocoding Script for Radar Intersections
Uses OpenStreetMap Nominatim to geocode intersection names to coordinates.
"""

import json
import re
import time
import urllib.request
import urllib.parse
from pathlib import Path

# Rate limiting for Nominatim (max 1 request per second)
REQUEST_DELAY = 1.1

# Rome bounding box for validation
ROME_BOUNDS = {
    'min_lat': 41.65,
    'max_lat': 42.05,
    'min_lng': 12.20,
    'max_lng': 12.80
}

def extract_street_names(intersection_name):
    """
    Extract street names from intersection name.
    Examples:
        "101-Cassia/Grottarossa" -> ["Via Cassia", "Via Grottarossa"]
        "102-Trionfale/Barellai" -> ["Via Trionfale", "Via Barellai"]
        "Via Aurelia/Via Baldo degli Ubaldi" -> ["Via Aurelia", "Via Baldo degli Ubaldi"]
    """
    # Remove the ID prefix (e.g., "101-")
    name = re.sub(r'^\d+-', '', intersection_name)

    # Split by common separators
    parts = re.split(r'[/\\&\-–—]', name)

    streets = []
    for part in parts:
        part = part.strip()
        if not part:
            continue

        # Check if it already has a street prefix
        has_prefix = any(part.lower().startswith(prefix) for prefix in
                        ['via ', 'viale ', 'piazza ', 'piazzale ', 'largo ',
                         'corso ', 'vicolo ', 'lungotevere ', 'circonvallazione '])

        if has_prefix:
            streets.append(part)
        else:
            # Add "Via" prefix as default
            streets.append(f"Via {part}")

    return streets

def geocode_intersection(streets, retry_count=0):
    """
    Geocode an intersection using Nominatim.
    Tries multiple query strategies.
    """
    results = []

    # Strategy 1: Search for intersection of two streets
    if len(streets) >= 2:
        query = f"{streets[0]} & {streets[1]}, Roma, Italy"
        result = nominatim_search(query)
        if result and is_in_rome(result):
            return {
                'lat': result['lat'],
                'lng': result['lon'],
                'confidence': 'high',
                'query': query,
                'display_name': result.get('display_name', '')
            }

    # Strategy 2: Search for first street in Rome
    if streets:
        query = f"{streets[0]}, Roma, Italy"
        result = nominatim_search(query)
        if result and is_in_rome(result):
            confidence = 'medium' if len(streets) == 1 else 'low'
            return {
                'lat': result['lat'],
                'lng': result['lon'],
                'confidence': confidence,
                'query': query,
                'display_name': result.get('display_name', '')
            }

    # Strategy 3: Try without "Via" prefix
    if streets:
        street_name = streets[0].replace('Via ', '').replace('Viale ', '')
        query = f"{street_name}, Roma, Italy"
        result = nominatim_search(query)
        if result and is_in_rome(result):
            return {
                'lat': result['lat'],
                'lng': result['lon'],
                'confidence': 'low',
                'query': query,
                'display_name': result.get('display_name', '')
            }

    return None

def nominatim_search(query):
    """
    Search Nominatim API for a query.
    """
    try:
        encoded_query = urllib.parse.quote(query)
        url = f"https://nominatim.openstreetmap.org/search?format=json&q={encoded_query}&limit=1&countrycodes=it"

        req = urllib.request.Request(url, headers={
            'User-Agent': 'RadarProjectGeocoder/1.0 (radar-installation-project)'
        })

        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())
            if data and len(data) > 0:
                return data[0]
    except Exception as e:
        print(f"  Error geocoding '{query}': {e}")

    return None

def is_in_rome(result):
    """
    Check if coordinates are within Rome bounding box.
    """
    try:
        lat = float(result['lat'])
        lon = float(result['lon'])
        return (ROME_BOUNDS['min_lat'] <= lat <= ROME_BOUNDS['max_lat'] and
                ROME_BOUNDS['min_lng'] <= lon <= ROME_BOUNDS['max_lng'])
    except:
        return False

def load_embedded_data():
    """
    Load the current embedded data.
    """
    embedded_path = Path(__file__).parent.parent / 'js' / 'embedded-data.js'

    with open(embedded_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Extract JSON from JavaScript - handle unquoted keys
    match = re.search(r'const EMBEDDED_DATA = ({[\s\S]*});', content)
    if match:
        json_str = match.group(1)
        # Fix unquoted keys - match word followed by colon that isn't already quoted
        # This handles keys like: intersections:, summary:
        json_str = re.sub(r'([{\[,]\s*)(\w+)(\s*:)', r'\1"\2"\3', json_str)
        # Remove trailing commas before } or ]
        json_str = re.sub(r',(\s*[}\]])', r'\1', json_str)
        return json.loads(json_str)

    raise ValueError("Could not parse embedded-data.js")

def save_embedded_data(data):
    """
    Save updated embedded data.
    """
    embedded_path = Path(__file__).parent.parent / 'js' / 'embedded-data.js'

    header = '''/**
 * Embedded Data - Generated from intersection status analysis
 * Generated: ''' + time.strftime('%Y-%m-%d %H:%M:%S') + '''
 * Total intersections: ''' + str(len(data['intersections'])) + '''
 * Includes ALL fields from Excel for editing
 * Geocoded coordinates included
 */

const EMBEDDED_DATA = '''

    json_str = json.dumps(data, indent=2, ensure_ascii=False)

    with open(embedded_path, 'w', encoding='utf-8') as f:
        f.write(header + json_str + ';\n')

    print(f"\nSaved to {embedded_path}")

def main():
    print("=" * 60)
    print("Batch Geocoding for Radar Intersections")
    print("=" * 60)

    # Load current data
    print("\nLoading embedded data...")
    data = load_embedded_data()
    intersections = data['intersections']

    print(f"Found {len(intersections)} intersections")

    # Count current state
    with_coords = sum(1 for i in intersections if i.get('coordinates'))
    without_coords = len(intersections) - with_coords
    print(f"  - With coordinates: {with_coords}")
    print(f"  - Without coordinates: {without_coords}")

    # Geocode intersections without coordinates
    results = {
        'high': [],
        'medium': [],
        'low': [],
        'failed': []
    }

    print("\nGeocoding intersections...")
    print("-" * 60)

    for i, intersection in enumerate(intersections):
        # Skip if already has manually set coordinates
        if intersection.get('coordinates_manual'):
            continue

        # Skip if already has coordinates with high confidence
        if intersection.get('coordinates') and intersection.get('geocode_confidence') == 'high':
            continue

        name = intersection.get('name', intersection.get('id', 'Unknown'))
        print(f"[{i+1}/{len(intersections)}] {name}")

        # Extract street names
        streets = extract_street_names(name)
        print(f"  Streets: {streets}")

        # Geocode
        result = geocode_intersection(streets)

        if result:
            intersection['coordinates'] = {
                'lat': float(result['lat']),
                'lng': float(result['lng'])
            }
            intersection['geocode_confidence'] = result['confidence']
            intersection['geocode_query'] = result['query']
            intersection['geocode_display'] = result['display_name'][:100] if result['display_name'] else ''

            results[result['confidence']].append(name)
            print(f"  -> {result['confidence'].upper()}: {result['lat']}, {result['lng']}")
        else:
            results['failed'].append(name)
            print(f"  -> FAILED")

        # Rate limiting
        time.sleep(REQUEST_DELAY)

    # Summary
    print("\n" + "=" * 60)
    print("GEOCODING SUMMARY")
    print("=" * 60)
    print(f"High confidence:   {len(results['high'])}")
    print(f"Medium confidence: {len(results['medium'])}")
    print(f"Low confidence:    {len(results['low'])}")
    print(f"Failed:            {len(results['failed'])}")

    if results['failed']:
        print("\nFailed intersections (need manual geocoding):")
        for name in results['failed']:
            print(f"  - {name}")

    if results['low']:
        print("\nLow confidence (should review):")
        for name in results['low'][:10]:
            print(f"  - {name}")
        if len(results['low']) > 10:
            print(f"  ... and {len(results['low']) - 10} more")

    # Save updated data
    print("\nSaving updated data...")
    save_embedded_data(data)

    # Generate review report
    report_path = Path(__file__).parent.parent / 'data' / 'geocoding_review.json'
    report_path.parent.mkdir(exist_ok=True)

    review_data = {
        'generated': time.strftime('%Y-%m-%d %H:%M:%S'),
        'summary': {
            'high': len(results['high']),
            'medium': len(results['medium']),
            'low': len(results['low']),
            'failed': len(results['failed'])
        },
        'needs_review': [],
        'failed': results['failed']
    }

    # Add low confidence items for review
    for intersection in intersections:
        if intersection.get('geocode_confidence') in ['low', 'medium']:
            review_data['needs_review'].append({
                'id': intersection['id'],
                'name': intersection['name'],
                'confidence': intersection.get('geocode_confidence'),
                'query': intersection.get('geocode_query'),
                'coordinates': intersection.get('coordinates'),
                'display': intersection.get('geocode_display')
            })

    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(review_data, f, indent=2, ensure_ascii=False)

    print(f"Review report saved to {report_path}")
    print("\nDone!")

if __name__ == '__main__':
    main()
