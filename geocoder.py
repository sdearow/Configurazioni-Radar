"""
Intelligent geocoding module for Rome intersections.

Handles:
- Simple street names
- Intersections (Street1/Street2)
- Piazzas and landmarks
- Street name normalization and expansion
"""

import re
import time
import json
import os
from typing import Dict, List, Any, Optional, Tuple
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
from config import (
    ROME_BOUNDS, ROME_CENTER, NOMINATIM_USER_AGENT,
    GEOCODE_RATE_LIMIT, GEOCODE_CACHE_PATH
)


class RomeGeocoder:
    """Geocoder specialized for Rome street intersections."""

    # Common Italian street type abbreviations and their expansions
    STREET_EXPANSIONS = {
        'v.': 'via',
        'v.le': 'viale',
        'vle': 'viale',
        'p.': 'piazza',
        'p.zza': 'piazza',
        'pza': 'piazza',
        'p.le': 'piazzale',
        'ple': 'piazzale',
        'l.re': 'lungotevere',
        'l.go': 'largo',
        'lgo': 'largo',
        'c.so': 'corso',
        'cso': 'corso',
        'l.mare': 'lungomare',
        'lgt': 'lungotevere',
        'l.re': 'lungotevere',
    }

    # Common street type prefixes in Rome
    STREET_TYPES = [
        'via', 'viale', 'piazza', 'piazzale', 'largo', 'corso',
        'lungotevere', 'lungomare', 'ponte', 'vicolo', 'circonvallazione',
        'tangenziale', 'galleria', 'passeggiata'
    ]

    def __init__(self):
        self.geolocator = Nominatim(user_agent=NOMINATIM_USER_AGENT)
        self.cache = self._load_cache()
        self.last_request_time = 0

    def _load_cache(self) -> Dict[str, Any]:
        """Load geocoding cache from file."""
        if os.path.exists(GEOCODE_CACHE_PATH):
            with open(GEOCODE_CACHE_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}

    def _save_cache(self):
        """Save geocoding cache to file."""
        with open(GEOCODE_CACHE_PATH, 'w', encoding='utf-8') as f:
            json.dump(self.cache, f, indent=2, ensure_ascii=False)

    def _rate_limit(self):
        """Enforce rate limiting for API requests."""
        elapsed = time.time() - self.last_request_time
        if elapsed < (1.0 / GEOCODE_RATE_LIMIT):
            time.sleep((1.0 / GEOCODE_RATE_LIMIT) - elapsed)
        self.last_request_time = time.time()

    def _is_in_rome(self, lat: float, lon: float) -> bool:
        """Check if coordinates are within Rome bounds."""
        return (ROME_BOUNDS['min_lat'] <= lat <= ROME_BOUNDS['max_lat'] and
                ROME_BOUNDS['min_lon'] <= lon <= ROME_BOUNDS['max_lon'])

    def expand_abbreviations(self, name: str) -> str:
        """Expand common Italian street abbreviations."""
        result = name.lower()

        # Replace abbreviations
        for abbrev, expansion in self.STREET_EXPANSIONS.items():
            # Match abbreviation at word boundaries
            pattern = r'\b' + re.escape(abbrev) + r'\b'
            result = re.sub(pattern, expansion, result, flags=re.IGNORECASE)

        return result

    def normalize_street_name(self, name: str) -> str:
        """
        Normalize a street name for geocoding.

        Steps:
        1. Expand abbreviations
        2. Add "Via" prefix if no street type present
        3. Clean up whitespace
        """
        if not name:
            return ""

        name = self.expand_abbreviations(name)

        # Check if name already has a street type
        has_type = any(name.lower().startswith(t) for t in self.STREET_TYPES)

        # If no type, try adding "Via" (most common in Rome)
        if not has_type:
            # Don't add Via to names that are clearly places (e.g., "Centro comm.")
            if not any(x in name.lower() for x in ['centro', 'comm.', 'mercato', 'stazione']):
                name = f"Via {name}"

        # Clean up whitespace
        name = re.sub(r'\s+', ' ', name).strip()

        return name

    def _geocode_single(self, query: str) -> Optional[Dict[str, Any]]:
        """Geocode a single query string."""
        cache_key = query.lower().strip()

        if cache_key in self.cache:
            return self.cache[cache_key]

        self._rate_limit()

        try:
            # Search with Rome context
            location = self.geolocator.geocode(
                query,
                viewbox=[(ROME_BOUNDS['max_lat'], ROME_BOUNDS['min_lon']),
                         (ROME_BOUNDS['min_lat'], ROME_BOUNDS['max_lon'])],
                bounded=True,
                timeout=10
            )

            if location:
                result = {
                    'lat': location.latitude,
                    'lon': location.longitude,
                    'address': location.address,
                    'found': True
                }
            else:
                result = {'found': False}

            self.cache[cache_key] = result
            self._save_cache()
            return result

        except (GeocoderTimedOut, GeocoderServiceError) as e:
            print(f"Geocoding error for '{query}': {e}")
            return {'found': False, 'error': str(e)}

    def geocode_street(self, street_name: str) -> Optional[Dict[str, Any]]:
        """
        Geocode a single street in Rome.

        Tries multiple query variations:
        1. Original name + Roma
        2. Normalized name + Roma
        3. Just the street name in Rome bounds
        """
        if not street_name:
            return None

        # Try variations
        variations = [
            f"{street_name}, Roma, Italia",
            f"{self.normalize_street_name(street_name)}, Roma, Italia",
            f"{street_name}, Rome, Italy",
        ]

        for query in variations:
            result = self._geocode_single(query)
            if result and result.get('found') and self._is_in_rome(result['lat'], result['lon']):
                result['query_used'] = query
                return result

        return {'found': False, 'tried': variations}

    def geocode_intersection(self, street1: str, street2: str) -> Optional[Dict[str, Any]]:
        """
        Find the intersection of two streets in Rome.

        Strategy:
        1. Try direct intersection query
        2. Geocode both streets and find midpoint (approximate)
        3. Try various name normalizations
        """
        if not street1 or not street2:
            return None

        # Normalize street names
        norm1 = self.normalize_street_name(street1)
        norm2 = self.normalize_street_name(street2)

        # Try direct intersection queries
        intersection_queries = [
            f"{norm1} & {norm2}, Roma, Italia",
            f"{norm1} e {norm2}, Roma, Italia",
            f"{street1} e {street2}, Roma, Italia",
            f"{norm1}, {norm2}, Roma, Italia",
        ]

        for query in intersection_queries:
            result = self._geocode_single(query)
            if result and result.get('found') and self._is_in_rome(result['lat'], result['lon']):
                result['query_used'] = query
                result['method'] = 'direct_intersection'
                return result

        # Fallback: geocode both streets and estimate intersection
        loc1 = self.geocode_street(street1)
        loc2 = self.geocode_street(street2)

        if loc1 and loc1.get('found') and loc2 and loc2.get('found'):
            # Use midpoint as approximation (will need manual adjustment)
            mid_lat = (loc1['lat'] + loc2['lat']) / 2
            mid_lon = (loc1['lon'] + loc2['lon']) / 2

            if self._is_in_rome(mid_lat, mid_lon):
                return {
                    'lat': mid_lat,
                    'lon': mid_lon,
                    'found': True,
                    'method': 'midpoint_approximation',
                    'confidence': 'low',
                    'street1_location': loc1,
                    'street2_location': loc2,
                    'needs_review': True
                }

        # Last resort: just use first street location
        if loc1 and loc1.get('found'):
            loc1['method'] = 'street1_only'
            loc1['confidence'] = 'very_low'
            loc1['needs_review'] = True
            return loc1

        return {'found': False, 'tried': intersection_queries}

    def geocode_place(self, place_name: str) -> Optional[Dict[str, Any]]:
        """
        Geocode a place name (piazza, landmark, etc.) in Rome.
        """
        if not place_name:
            return None

        # Try variations
        variations = [
            f"{place_name}, Roma, Italia",
            f"{self.expand_abbreviations(place_name)}, Roma, Italia",
            f"Piazza {place_name}, Roma, Italia",
            f"{place_name}, Rome, Italy",
        ]

        for query in variations:
            result = self._geocode_single(query)
            if result and result.get('found') and self._is_in_rome(result['lat'], result['lon']):
                result['query_used'] = query
                return result

        return {'found': False, 'tried': variations}

    def geocode_intersection_record(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """
        Geocode an intersection record from the merged data.

        Returns the record with updated latitude, longitude, and geocode_status.
        """
        streets = record.get('streets', [])
        name = record.get('name_for_geocoding', '')

        result = None
        method = None

        if len(streets) >= 2:
            # It's an intersection - try to find intersection point
            result = self.geocode_intersection(streets[0], streets[1])
            method = 'intersection'

            # If more than 2 streets, it's a complex intersection
            if len(streets) > 2 and result and result.get('found'):
                result['complex_intersection'] = True
                result['all_streets'] = streets

        elif len(streets) == 1:
            # Single location - could be a street segment, piazza, or landmark
            street = streets[0]

            # Check if it's a piazza/piazzale
            if any(p in street.lower() for p in ['piazza', 'p.zza', 'p.', 'piazzale', 'p.le', 'largo', 'l.go']):
                result = self.geocode_place(street)
                method = 'place'
            else:
                result = self.geocode_street(street)
                method = 'street'

        else:
            # No street info - try the raw name
            if name:
                result = self.geocode_place(name)
                method = 'raw_name'

        # Update record with results
        if result and result.get('found'):
            record['latitude'] = result['lat']
            record['longitude'] = result['lon']
            record['geocode_status'] = 'found'
            record['geocode_method'] = method
            record['geocode_confidence'] = result.get('confidence', 'high' if result.get('method') == 'direct_intersection' else 'medium')
            record['geocode_address'] = result.get('address', '')
            record['geocode_needs_review'] = result.get('needs_review', False)
        else:
            record['geocode_status'] = 'not_found'
            record['geocode_method'] = method
            record['geocode_confidence'] = None
            record['geocode_needs_review'] = True

        return record


def geocode_all_intersections(intersections: List[Dict[str, Any]],
                               progress_callback=None) -> List[Dict[str, Any]]:
    """
    Geocode all intersections in the list.

    Args:
        intersections: List of intersection records
        progress_callback: Optional callback(current, total, record) for progress updates

    Returns:
        List of geocoded intersection records
    """
    geocoder = RomeGeocoder()
    total = len(intersections)

    for i, record in enumerate(intersections):
        # Skip if already geocoded (unless it needs review)
        if (record.get('latitude') is not None and
            record.get('longitude') is not None and
            not record.get('geocode_needs_review', False) and
            record.get('manual_position', False)):
            continue

        geocoder.geocode_intersection_record(record)

        if progress_callback:
            progress_callback(i + 1, total, record)
        else:
            status = record.get('geocode_status', 'unknown')
            conf = record.get('geocode_confidence', 'N/A')
            print(f"[{i+1}/{total}] {record.get('raw_name', 'Unknown')}: {status} (confidence: {conf})")

    return intersections


if __name__ == "__main__":
    from data_extractor import load_merged_data, save_merged_data, merge_all_data, MERGED_DATA_PATH

    # Load or create merged data
    intersections = load_merged_data()
    if not intersections:
        print("No merged data found. Extracting from Excel files...")
        intersections = merge_all_data()
        save_merged_data(intersections)

    print(f"\nGeocoding {len(intersections)} intersections...")
    print("This may take a while due to rate limiting.\n")

    geocoded = geocode_all_intersections(intersections)
    save_merged_data(geocoded)

    # Summary
    found = sum(1 for i in geocoded if i.get('geocode_status') == 'found')
    not_found = sum(1 for i in geocoded if i.get('geocode_status') == 'not_found')
    needs_review = sum(1 for i in geocoded if i.get('geocode_needs_review', False))

    print(f"\n{'='*60}")
    print(f"Geocoding Summary:")
    print(f"  Found: {found}")
    print(f"  Not found: {not_found}")
    print(f"  Needs manual review: {needs_review}")
    print(f"{'='*60}")
