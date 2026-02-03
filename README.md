# Radar Configuration Dashboard - Roma

A web-based dashboard for managing radar installation configurations in Rome. Features interactive maps with geolocation, data editing, and Excel import/export.

## Features

- **Interactive Map**: View all intersections on an OpenStreetMap-based map
- **Draggable Markers**: Manually adjust positions by dragging markers
- **Automatic Geocoding**: Intelligent geocoding using OpenStreetMap Nominatim
- **Data Merging**: Combines data from multiple Excel files (Lotti, Semaforica, Swarco)
- **Full Data Editor**: View and edit all columns from source files
- **Export**: Export to Excel or GeoJSON formats
- **Portable**: Runs locally, easy to copy to other machines

## Quick Start

### 1. Install Dependencies

```bash
# Create a virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install required packages
pip install -r requirements.txt
```

### 2. Run the Dashboard

```bash
python run.py
```

Then open http://localhost:5000 in your browser.

## Usage Guide

### First Run

1. The system will automatically extract data from the Excel files in `data-import/`
2. Click **"Geocode All"** to automatically find coordinates for all intersections
3. Geocoding takes time due to API rate limiting (~1 request/second)

### Adjusting Positions

For intersections that weren't found or are inaccurate:

1. **Drag the marker** directly on the map to the correct position
2. The position is saved automatically
3. Markers turn **blue** when manually positioned

### Understanding Marker Colors

| Color | Meaning |
|-------|---------|
| 🟢 Green | Geocoded with high confidence |
| 🟠 Orange | Needs review (low confidence) |
| 🔴 Red | Not found - needs manual positioning |
| 🔵 Blue | Manually positioned |

### Filters

Use the filter buttons to show:
- **All**: All intersections
- **Geocoded**: Successfully found
- **Not Found**: Failed geocoding
- **Needs Review**: Low confidence results
- **Manual**: Manually positioned

### Exporting Data

- **Export Excel**: Downloads a complete Excel file with coordinates
- **Export GeoJSON**: Downloads a GeoJSON file for GIS applications

### Reloading from Excel

If you update the source Excel files:
1. Click **"Reload from Excel"**
2. This re-reads all Excel files while preserving manual position corrections

## File Structure

```
Configurazioni-Radar/
├── data-import/              # Source Excel files
│   ├── LOTTI M9_RADAR_v1_2026.01.28.xlsx
│   ├── ELENCO_LOTTO_1_2026.01.23.xlsx
│   ├── ELENCO LOTTO 2_2026.01.23.xlsx
│   ├── Elenco IS RADAR_SEMAFORICA_...xlsx
│   └── Swarco_Verifica stato...xlsx
├── templates/                # HTML templates
│   └── index.html
├── app.py                    # Flask web application
├── config.py                 # Configuration settings
├── data_extractor.py         # Excel parsing and merging
├── geocoder.py               # Geocoding logic
├── run.py                    # Startup script
├── requirements.txt          # Python dependencies
├── merged_data.json          # Combined data (auto-generated)
└── geocode_cache.json        # Geocoding cache (auto-generated)
```

## How Geocoding Works

The geocoder handles various name formats:

### Simple Streets
`Via Cassia` → searches for "Via Cassia, Roma, Italia"

### Intersections
`Cassia/Grottarossa` → searches for intersection of Via Cassia and Via Grottarossa

### Piazzas
`Piazza Ungheria` → searches for the piazza directly

### Abbreviations
The system expands common abbreviations:
- `L.re` → Lungotevere
- `P.zza` → Piazza
- `C.so` → Corso
- `V.le` → Viale

### Numeric Prefixes
`101-Cassia/Grottarossa` → ID preserved, text used for geocoding

## Troubleshooting

### "Geocoding not working"
- Ensure you have internet connectivity
- Nominatim has rate limits; wait and retry
- For VPN/proxy environments, geocoding may be blocked

### "Intersection not found"
1. Try re-geocoding with the "Re-geocode" button
2. If still not found, drag the marker manually
3. Some names may need clarification (the system will flag them)

### "Data not loading"
- Check that Excel files are in `data-import/` folder
- Run `python data_extractor.py` to diagnose issues

## Copying to Another Machine

1. Copy the entire `Configurazioni-Radar` folder
2. Install dependencies: `pip install -r requirements.txt`
3. Run: `python run.py`

The `merged_data.json` file preserves all geocoded positions and manual corrections.

## API Endpoints

For advanced users, the following API endpoints are available:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/intersections` | GET | Get all intersection data |
| `/api/intersection/<id>/position` | PUT | Update position (lat, lon) |
| `/api/intersection/<id>` | PUT | Update intersection data |
| `/api/geocode/<id>` | POST | Re-geocode single intersection |
| `/api/geocode/all` | POST | Geocode all pending intersections |
| `/api/reload` | POST | Reload from Excel files |
| `/api/export/excel` | GET | Download Excel export |
| `/api/export/geojson` | GET | Download GeoJSON export |

## Requirements

- Python 3.8+
- Flask
- Pandas
- Geopy
- OpenPyXL

## License

Internal use only - Edison Next Government / Roma Capitale
