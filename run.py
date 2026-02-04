#!/usr/bin/env python3
"""
Radar Configuration Dashboard - Startup Script

This script initializes the data and starts the web application.
"""

import os
import sys

def main():
    # Ensure we're in the right directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)

    print("=" * 60)
    print("Radar Configuration Dashboard - Roma")
    print("=" * 60)

    # Check for merged data
    from config import MERGED_DATA_PATH

    if not os.path.exists(MERGED_DATA_PATH):
        print("\nStep 1: Extracting data from Excel files...")
        from data_extractor import merge_all_data, save_merged_data
        intersections = merge_all_data()
        save_merged_data(intersections)
        print(f"  Loaded {len(intersections)} intersections.")
    else:
        from data_extractor import load_merged_data
        intersections = load_merged_data()
        print(f"\nLoaded {len(intersections)} intersections from cache.")

    # Check geocoding status
    geocoded = sum(1 for i in intersections if i.get('latitude') is not None)
    not_geocoded = len(intersections) - geocoded

    print(f"\nGeocoding status:")
    print(f"  - Geocoded: {geocoded}")
    print(f"  - Not geocoded: {not_geocoded}")

    if not_geocoded > 0 and geocoded == 0:
        print("\nTIP: Click 'Geocode All' in the dashboard to geocode all intersections.")
        print("     This may take several minutes due to API rate limiting.")

    # Start the web application
    print("\n" + "=" * 60)
    print("Starting web server...")
    print("Open http://localhost:5000 in your browser")
    print("Press Ctrl+C to stop the server")
    print("=" * 60 + "\n")

    from app import app
    app.run(debug=True, host='0.0.0.0', port=5000)


if __name__ == '__main__':
    main()
