"""
Flask web application for Radar Configuration Dashboard.

Features:
- Interactive map with Leaflet.js showing all intersections
- Draggable markers for manual position correction
- Data editor for all columns
- Export to Excel functionality
- Geocoding status overview
"""

import os
import json
from flask import Flask, render_template, jsonify, request, send_file
from datetime import datetime
import pandas as pd

from config import (
    BASE_DIR, MERGED_DATA_PATH, DATA_DIR, EXCEL_FILES,
    ROME_CENTER, ROME_BOUNDS
)
from data_extractor import merge_all_data, save_merged_data, load_merged_data
from geocoder import RomeGeocoder, geocode_all_intersections

app = Flask(__name__, template_folder='templates', static_folder='static')


def get_intersections():
    """Load intersections from merged data file."""
    return load_merged_data()


def save_intersections(intersections):
    """Save intersections to merged data file."""
    save_merged_data(intersections)


@app.route('/')
def index():
    """Main dashboard page."""
    return render_template('index.html')


@app.route('/api/intersections')
def api_get_intersections():
    """Get all intersections as JSON."""
    intersections = get_intersections()

    # Calculate statistics
    stats = {
        'total': len(intersections),
        'geocoded': sum(1 for i in intersections if i.get('latitude') is not None),
        'not_found': sum(1 for i in intersections if i.get('geocode_status') == 'not_found'),
        'needs_review': sum(1 for i in intersections if i.get('geocode_needs_review', False)),
        'manual_positioned': sum(1 for i in intersections if i.get('manual_position', False)),
    }

    return jsonify({
        'intersections': intersections,
        'stats': stats,
        'rome_center': ROME_CENTER,
        'rome_bounds': ROME_BOUNDS
    })


@app.route('/api/intersection/<int:index>', methods=['GET'])
def api_get_intersection(index):
    """Get a single intersection by index."""
    intersections = get_intersections()
    if 0 <= index < len(intersections):
        return jsonify(intersections[index])
    return jsonify({'error': 'Intersection not found'}), 404


@app.route('/api/intersection/<int:index>/position', methods=['PUT'])
def api_update_position(index):
    """Update the position of an intersection (from dragging marker)."""
    intersections = get_intersections()
    if 0 <= index < len(intersections):
        data = request.json
        intersections[index]['latitude'] = data.get('lat')
        intersections[index]['longitude'] = data.get('lon')
        intersections[index]['manual_position'] = True
        intersections[index]['geocode_needs_review'] = False
        intersections[index]['position_updated_at'] = datetime.now().isoformat()
        save_intersections(intersections)
        return jsonify({'success': True, 'intersection': intersections[index]})
    return jsonify({'error': 'Intersection not found'}), 404


@app.route('/api/intersection/<int:index>', methods=['PUT'])
def api_update_intersection(index):
    """Update intersection data."""
    intersections = get_intersections()
    if 0 <= index < len(intersections):
        data = request.json

        # Update allowed fields
        allowed_fields = [
            'latitude', 'longitude', 'manual_position', 'geocode_needs_review',
            'notes', 'main_data', 'lotto1_data', 'lotto2_data',
            'semaforica_data', 'swarco_data'
        ]

        for field in allowed_fields:
            if field in data:
                intersections[index][field] = data[field]

        intersections[index]['updated_at'] = datetime.now().isoformat()
        save_intersections(intersections)
        return jsonify({'success': True, 'intersection': intersections[index]})
    return jsonify({'error': 'Intersection not found'}), 404


@app.route('/api/geocode/<int:index>', methods=['POST'])
def api_geocode_single(index):
    """Geocode a single intersection."""
    intersections = get_intersections()
    if 0 <= index < len(intersections):
        geocoder = RomeGeocoder()
        record = intersections[index]

        # Clear existing position to force re-geocoding
        record['latitude'] = None
        record['longitude'] = None
        record['manual_position'] = False

        geocoder.geocode_intersection_record(record)
        save_intersections(intersections)

        return jsonify({'success': True, 'intersection': record})
    return jsonify({'error': 'Intersection not found'}), 404


@app.route('/api/geocode/all', methods=['POST'])
def api_geocode_all():
    """Geocode all intersections that haven't been geocoded yet."""
    intersections = get_intersections()

    # Filter to only those needing geocoding
    to_geocode = [i for i in intersections if
                  i.get('latitude') is None or
                  (not i.get('manual_position', False) and i.get('geocode_needs_review', False))]

    if not to_geocode:
        return jsonify({
            'success': True,
            'message': 'All intersections already geocoded',
            'geocoded_count': 0
        })

    geocoded = geocode_all_intersections(intersections)
    save_intersections(geocoded)

    found = sum(1 for i in geocoded if i.get('geocode_status') == 'found')
    return jsonify({
        'success': True,
        'message': f'Geocoded {found} intersections',
        'geocoded_count': found
    })


@app.route('/api/reload', methods=['POST'])
def api_reload_data():
    """Reload data from Excel files (re-merge)."""
    try:
        intersections = merge_all_data()
        save_intersections(intersections)
        return jsonify({
            'success': True,
            'message': f'Reloaded {len(intersections)} intersections from Excel files'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/export/excel', methods=['GET'])
def api_export_excel():
    """Export data to Excel file."""
    intersections = get_intersections()

    # Flatten the data for Excel export
    rows = []
    for idx, intersection in enumerate(intersections):
        row = {
            'index': idx,
            'id': intersection.get('id'),
            'raw_name': intersection.get('raw_name'),
            'latitude': intersection.get('latitude'),
            'longitude': intersection.get('longitude'),
            'geocode_status': intersection.get('geocode_status'),
            'geocode_confidence': intersection.get('geocode_confidence'),
            'manual_position': intersection.get('manual_position', False),
            'needs_review': intersection.get('geocode_needs_review', False),
        }

        # Add main data columns
        if intersection.get('main_data'):
            for key, value in intersection['main_data'].items():
                row[f'main_{key}'] = value

        # Add lotto1 data columns
        if intersection.get('lotto1_data'):
            for key, value in intersection['lotto1_data'].items():
                row[f'lotto1_{key}'] = value

        # Add lotto2 data columns
        if intersection.get('lotto2_data'):
            for key, value in intersection['lotto2_data'].items():
                row[f'lotto2_{key}'] = value

        # Add semaforica data columns
        if intersection.get('semaforica_data'):
            for key, value in intersection['semaforica_data'].items():
                row[f'semaforica_{key}'] = value

        # Add swarco data columns
        if intersection.get('swarco_data'):
            for key, value in intersection['swarco_data'].items():
                row[f'swarco_{key}'] = value

        rows.append(row)

    # Create DataFrame and export
    df = pd.DataFrame(rows)

    export_path = os.path.join(BASE_DIR, 'export_with_coordinates.xlsx')
    df.to_excel(export_path, index=False, engine='openpyxl')

    return send_file(
        export_path,
        as_attachment=True,
        download_name=f'radar_intersections_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
    )


@app.route('/api/export/geojson', methods=['GET'])
def api_export_geojson():
    """Export geocoded data as GeoJSON."""
    intersections = get_intersections()

    features = []
    for idx, intersection in enumerate(intersections):
        if intersection.get('latitude') and intersection.get('longitude'):
            feature = {
                'type': 'Feature',
                'geometry': {
                    'type': 'Point',
                    'coordinates': [intersection['longitude'], intersection['latitude']]
                },
                'properties': {
                    'index': idx,
                    'id': intersection.get('id'),
                    'name': intersection.get('raw_name'),
                    'geocode_status': intersection.get('geocode_status'),
                    'manual_position': intersection.get('manual_position', False),
                }
            }
            features.append(feature)

    geojson = {
        'type': 'FeatureCollection',
        'features': features
    }

    export_path = os.path.join(BASE_DIR, 'export_intersections.geojson')
    with open(export_path, 'w', encoding='utf-8') as f:
        json.dump(geojson, f, indent=2, ensure_ascii=False)

    return send_file(
        export_path,
        as_attachment=True,
        download_name=f'radar_intersections_{datetime.now().strftime("%Y%m%d_%H%M%S")}.geojson'
    )


# Create templates directory if it doesn't exist
os.makedirs(os.path.join(BASE_DIR, 'templates'), exist_ok=True)
os.makedirs(os.path.join(BASE_DIR, 'static'), exist_ok=True)


if __name__ == '__main__':
    # Initialize data if not exists
    if not os.path.exists(MERGED_DATA_PATH):
        print("Initializing data from Excel files...")
        intersections = merge_all_data()
        save_intersections(intersections)
        print(f"Loaded {len(intersections)} intersections.")

    print("\nStarting Radar Configuration Dashboard...")
    print("Open http://localhost:5000 in your browser")
    app.run(debug=True, host='0.0.0.0', port=5000)
