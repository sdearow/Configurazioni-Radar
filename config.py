"""Configuration settings for the Radar Configuration Dashboard."""

import os

# Base directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Data directory
DATA_DIR = os.path.join(BASE_DIR, "data-import")

# Database file (SQLite for portability)
DATABASE_PATH = os.path.join(BASE_DIR, "radar_data.db")

# Geocoded data cache (JSON for easy inspection)
GEOCODE_CACHE_PATH = os.path.join(BASE_DIR, "geocode_cache.json")

# Merged data output
MERGED_DATA_PATH = os.path.join(BASE_DIR, "merged_data.json")

# Excel files
EXCEL_FILES = {
    "main": "LOTTI M9_RADAR_v1_2026.01.28.xlsx",
    "lotto1": "ELENCO_LOTTO_1_2026.01.23.xlsx",
    "lotto2": "ELENCO LOTTO 2_2026.01.23.xlsx",
    "semaforica": "Elenco IS RADAR_SEMAFORICA_per VERIFICA STATO AUT.xlsx",
    "swarco": "Swarco_Verifica stato - TOT_2026.01.29.xlsx",
}

# Rome bounding box for validation
ROME_BOUNDS = {
    "min_lat": 41.7,
    "max_lat": 42.1,
    "min_lon": 12.2,
    "max_lon": 12.8,
}

# Default center of Rome
ROME_CENTER = {"lat": 41.9028, "lon": 12.4964}

# Nominatim user agent (required by OpenStreetMap terms of service)
NOMINATIM_USER_AGENT = "radar-config-dashboard/1.0"

# Rate limiting for geocoding (requests per second)
GEOCODE_RATE_LIMIT = 1.0  # 1 request per second to be respectful to Nominatim
