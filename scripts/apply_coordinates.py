#!/usr/bin/env python3
"""
Apply coordinates to intersections using the local Rome coordinates database.
"""

import json
from pathlib import Path
from rome_coordinates import geocode_intersection_name, ROME_STREETS

def main():
    data_dir = Path(__file__).parent.parent / "data"

    # Load intersections
    intersections_file = data_dir / "intersections.json"
    with open(intersections_file, 'r', encoding='utf-8') as f:
        intersections = json.load(f)

    print(f"Processing {len(intersections)} intersections...")

    geocoded = 0
    failed = []

    for intersection in intersections:
        name = intersection.get('name', '')

        coords = geocode_intersection_name(name)

        if coords:
            intersection['coordinates'] = {'lat': coords[0], 'lng': coords[1]}
            geocoded += 1
        else:
            failed.append({'id': intersection.get('id'), 'name': name})

    print(f"\nGeocoded: {geocoded}/{len(intersections)}")
    print(f"Failed: {len(failed)}")

    if failed:
        print("\nFailed to geocode:")
        for f in failed[:30]:
            print(f"  - {f['id']}: {f['name']}")
        if len(failed) > 30:
            print(f"  ... and {len(failed) - 30} more")

    # Save updated intersections
    with open(intersections_file, 'w', encoding='utf-8') as f:
        json.dump(intersections, f, ensure_ascii=False, indent=2)
    print(f"\nSaved to {intersections_file}")

    # Regenerate embedded data
    print("\nRegenerating embedded-data.js...")

    with open(data_dir / "summary.json", 'r', encoding='utf-8') as f:
        summary = json.load(f)

    js_content = f"""/**
 * Embedded Data
 * Contains intersection data with geocoded coordinates.
 */

const EMBEDDED_DATA = {{
    intersections: {json.dumps(intersections, ensure_ascii=False)},
    summary: {json.dumps(summary, ensure_ascii=False)}
}};
"""

    js_dir = Path(__file__).parent.parent / "js"
    with open(js_dir / "embedded-data.js", 'w', encoding='utf-8') as f:
        f.write(js_content)

    print("Done! Files updated.")

if __name__ == "__main__":
    main()
