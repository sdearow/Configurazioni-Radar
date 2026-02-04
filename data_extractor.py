"""
Data extraction module for parsing Excel files and merging intersection data.
"""

import pandas as pd
import os
import re
import json
from typing import Dict, List, Any, Optional, Tuple
from config import DATA_DIR, EXCEL_FILES, MERGED_DATA_PATH


def clean_column_name(name: str) -> str:
    """Clean column names by removing newlines and extra spaces."""
    if pd.isna(name):
        return "unnamed"
    name = str(name)
    name = name.replace('\n', ' ').replace('\r', '')
    name = re.sub(r'\s+', ' ', name).strip()
    return name


def parse_intersection_name(raw_name: str) -> Dict[str, Any]:
    """
    Parse intersection name to extract components.

    Examples:
    - "101-Cassia/Grottarossa" -> id=101, streets=["Cassia", "Grottarossa"]
    - "452-Some Name" -> id=452, streets=["Some Name"]
    - "Colombo/Navigatori" -> id=None, streets=["Colombo", "Navigatori"]
    - "Piazza Ungheria/Liegi" -> id=None, streets=["Piazza Ungheria", "Liegi"]
    """
    if pd.isna(raw_name):
        return {"id": None, "raw_name": None, "streets": [], "is_intersection": False}

    raw_name = str(raw_name).strip()

    # Extract numeric ID prefix if present (e.g., "101-" or "452-")
    id_match = re.match(r'^(\d+)\s*[-–—]\s*(.+)$', raw_name)
    if id_match:
        location_id = id_match.group(1)
        name_part = id_match.group(2).strip()
    else:
        location_id = None
        name_part = raw_name

    # Clean up common artifacts
    name_part = re.sub(r'\s+', ' ', name_part).strip()

    # Split by "/" to get street names
    if '/' in name_part:
        streets = [s.strip() for s in name_part.split('/') if s.strip()]
        is_intersection = len(streets) >= 2
    else:
        streets = [name_part] if name_part else []
        is_intersection = False

    return {
        "id": location_id,
        "raw_name": raw_name,
        "name_part": name_part,
        "streets": streets,
        "is_intersection": is_intersection
    }


def extract_main_data() -> pd.DataFrame:
    """Extract data from the main LOTTI file."""
    filepath = os.path.join(DATA_DIR, EXCEL_FILES["main"])

    # Read the main sheet with all lots
    df = pd.read_excel(filepath, sheet_name="INST.FIN. LOTTI")

    # Clean column names
    df.columns = [clean_column_name(c) for c in df.columns]

    # Rename key columns for clarity
    column_mapping = {
        'Numero-Nome Postazione': 'intersection_name',
        'Codice Impianto': 'facility_code',
        'Progr.': 'progress_num',
        'Lotto': 'lot',
        'Centr': 'centralized',
        'Sistema': 'system',
        'N.ro Dispositivi': 'num_devices',
        'Postazione in OdS o Nuova': 'position_type',
    }

    for old_name, new_name in column_mapping.items():
        for col in df.columns:
            if old_name.lower() in col.lower():
                df = df.rename(columns={col: new_name})
                break

    # Filter out rows without intersection names
    df = df[df['intersection_name'].notna()]

    # Filter out header/note rows
    df = df[~df['intersection_name'].astype(str).str.contains('postazioni aggiuntive|Progr|Postazione', case=False, na=False)]

    return df


def extract_lotto1_data() -> pd.DataFrame:
    """Extract data from Lotto 1 file."""
    filepath = os.path.join(DATA_DIR, EXCEL_FILES["lotto1"])

    df = pd.read_excel(filepath, sheet_name="Sheet1")
    df.columns = [clean_column_name(c) for c in df.columns]

    # Skip header rows
    df = df[df['N.'].apply(lambda x: isinstance(x, (int, float)) and not pd.isna(x))]

    # Add source identifier
    df['source'] = 'lotto1'

    return df


def extract_lotto2_data() -> pd.DataFrame:
    """Extract data from Lotto 2 file."""
    filepath = os.path.join(DATA_DIR, EXCEL_FILES["lotto2"])

    df = pd.read_excel(filepath, sheet_name="Foglio1")
    df.columns = [clean_column_name(c) for c in df.columns]

    # Clean the address column - remove "cod. imp. XXXXX" suffix
    if 'indirizzo' in df.columns:
        df['indirizzo_clean'] = df['indirizzo'].apply(
            lambda x: re.sub(r'\s*cod\.?\s*imp\.?\s*\d+\s*$', '', str(x)).strip() if pd.notna(x) else x
        )

    # Add source identifier
    df['source'] = 'lotto2'

    return df


def extract_semaforica_data() -> pd.DataFrame:
    """Extract data from Semaforica file."""
    filepath = os.path.join(DATA_DIR, EXCEL_FILES["semaforica"])

    df = pd.read_excel(filepath, sheet_name="IMPIANTI SEMAFORICA")
    df.columns = [clean_column_name(c) for c in df.columns]

    # Add source identifier
    df['source'] = 'semaforica'

    return df


def extract_swarco_data() -> pd.DataFrame:
    """Extract data from Swarco file."""
    filepath = os.path.join(DATA_DIR, EXCEL_FILES["swarco"])

    df = pd.read_excel(filepath, sheet_name="Foglio1")
    df.columns = [clean_column_name(c) for c in df.columns]

    # Add source identifier
    df['source'] = 'swarco'

    return df


def normalize_intersection_name(name: str) -> str:
    """
    Normalize intersection name for matching across files.

    Handles variations like:
    - 'Anastasio II - Centro comm.' vs '123-Anastasio II'
    - 'Ponte Duca d'Aosta - Stadio' vs '140-Ponte Duca d'Aosta/Stadio'
    - 'Nomentana-Graf-Kant' vs '163-Nomentana/Graf/Kant'
    - 'L.re Cadorna' vs 'Lungotevere Cadorna'
    """
    if pd.isna(name):
        return ""

    name = str(name).lower().strip()

    # Remove numeric prefix (e.g., "101-", "452-")
    name = re.sub(r'^\d+\s*[-–—]\s*', '', name)

    # Remove "cod. imp. XXXXX" suffix
    name = re.sub(r'\s*cod\.?\s*imp\.?\s*\d+\s*$', '', name)

    # Expand common abbreviations BEFORE splitting
    abbreviations = {
        r'\bl\.re\b': 'lungotevere',
        r'\bl\.go\b': 'largo',
        r'\blgo\b': 'largo',
        r'\bp\.le\b': 'piazzale',
        r'\bple\b': 'piazzale',
        r'\bp\.zza\b': 'piazza',
        r'\bpza\b': 'piazza',
        r'\bp\.\b': 'piazza',
        r'\bc\.so\b': 'corso',
        r'\bcso\b': 'corso',
        r'\bv\.le\b': 'viale',
        r'\bvle\b': 'viale',
        r'\bv\.\b': 'via',
        r'\blgt\b': 'lungotevere',
        r'\bl\.mare\b': 'lungomare',
        r'\bm\.llo\b': 'maresciallo',
        r'\bs\.\b': 'san',
        r'\bs\.m\.\b': 'santa maria',
    }
    for abbrev, expansion in abbreviations.items():
        name = re.sub(abbrev, expansion, name, flags=re.IGNORECASE)

    # Normalize separators: convert " - " to "/" for intersection detection
    # But be careful not to convert compound names like "Santa Maria del Soccorso"
    name = re.sub(r'\s+[-–—]\s+', '/', name)

    # Remove common words that vary between sources
    name = re.sub(r'\bvia\b', '', name)
    name = re.sub(r'\bviale\b', '', name)
    name = re.sub(r'\bdir\.\s*\w+', '', name)  # Remove direction indicators
    name = re.sub(r'\bdir\s+\w+', '', name)

    # Normalize whitespace
    name = re.sub(r'\s+', ' ', name).strip()

    # Sort streets in intersection names for consistent matching
    if '/' in name:
        streets = sorted([s.strip() for s in name.split('/') if s.strip()])
        name = '/'.join(streets)

    # Final cleanup
    name = re.sub(r'\s+', ' ', name).strip()

    return name


def fuzzy_match_name(name1: str, name2: str) -> float:
    """
    Calculate similarity score between two normalized names.
    Returns a score between 0 and 1.
    """
    if not name1 or not name2:
        return 0.0

    # Exact match
    if name1 == name2:
        return 1.0

    # Check if one contains the other (partial match)
    if name1 in name2 or name2 in name1:
        return 0.8

    # Check street overlap for intersection names
    streets1 = set(name1.split('/'))
    streets2 = set(name2.split('/'))

    if streets1 and streets2:
        # Calculate Jaccard similarity
        intersection = streets1 & streets2
        union = streets1 | streets2
        if union:
            jaccard = len(intersection) / len(union)
            if jaccard >= 0.5:  # At least half the streets match
                return jaccard

    return 0.0


def find_best_match(name: str, lookup: Dict[str, Any], threshold: float = 0.6) -> Optional[str]:
    """
    Find the best matching key in lookup for the given name.
    Returns the matching key or None if no good match found.
    """
    norm_name = normalize_intersection_name(name)

    # Try exact match first
    if norm_name in lookup:
        return norm_name

    # Try fuzzy matching
    best_match = None
    best_score = 0.0

    for key in lookup.keys():
        score = fuzzy_match_name(norm_name, key)
        if score > best_score and score >= threshold:
            best_score = score
            best_match = key

    return best_match


def merge_all_data() -> List[Dict[str, Any]]:
    """
    Merge data from all Excel files into a unified structure.
    Returns a list of intersection records with all available information.
    """
    # Extract data from all sources
    main_df = extract_main_data()

    try:
        lotto1_df = extract_lotto1_data()
    except Exception as e:
        print(f"Warning: Could not load Lotto 1 data: {e}")
        lotto1_df = pd.DataFrame()

    try:
        lotto2_df = extract_lotto2_data()
    except Exception as e:
        print(f"Warning: Could not load Lotto 2 data: {e}")
        lotto2_df = pd.DataFrame()

    try:
        semaforica_df = extract_semaforica_data()
    except Exception as e:
        print(f"Warning: Could not load Semaforica data: {e}")
        semaforica_df = pd.DataFrame()

    try:
        swarco_df = extract_swarco_data()
    except Exception as e:
        print(f"Warning: Could not load Swarco data: {e}")
        swarco_df = pd.DataFrame()

    # Build unified intersection list from main file
    intersections = []

    for idx, row in main_df.iterrows():
        raw_name = row.get('intersection_name', '')
        parsed = parse_intersection_name(raw_name)

        # Convert row to dict, handling NaN values
        row_dict = {}
        for col in main_df.columns:
            val = row[col]
            if pd.isna(val):
                row_dict[col] = None
            elif isinstance(val, (int, float)):
                row_dict[col] = val if not pd.isna(val) else None
            else:
                row_dict[col] = str(val)

        record = {
            "id": parsed["id"],
            "raw_name": parsed["raw_name"],
            "name_for_geocoding": parsed["name_part"],
            "streets": parsed["streets"],
            "is_intersection": parsed["is_intersection"],
            "normalized_name": normalize_intersection_name(raw_name),
            "latitude": None,
            "longitude": None,
            "geocode_status": "pending",
            "geocode_confidence": None,
            "manual_position": False,
            "main_data": row_dict,
            "lotto1_data": None,
            "lotto2_data": None,
            "semaforica_data": None,
            "swarco_data": None,
        }

        intersections.append(record)

    # Match and merge Lotto 1 data (with fuzzy matching)
    if not lotto1_df.empty and 'Impianto' in lotto1_df.columns:
        lotto1_lookup = {}
        for idx, row in lotto1_df.iterrows():
            norm_name = normalize_intersection_name(row.get('Impianto', ''))
            if norm_name:
                row_dict = {col: (None if pd.isna(row[col]) else row[col]) for col in lotto1_df.columns}
                lotto1_lookup[norm_name] = row_dict

        for intersection in intersections:
            raw_name = intersection.get("raw_name", "")
            match_key = find_best_match(raw_name, lotto1_lookup, threshold=0.5)
            if match_key:
                intersection["lotto1_data"] = lotto1_lookup[match_key]
                intersection["lotto1_match_key"] = match_key

    # Match and merge Lotto 2 data (with fuzzy matching)
    if not lotto2_df.empty and 'indirizzo_clean' in lotto2_df.columns:
        lotto2_lookup = {}
        for idx, row in lotto2_df.iterrows():
            norm_name = normalize_intersection_name(row.get('indirizzo_clean', ''))
            if norm_name:
                row_dict = {col: (None if pd.isna(row[col]) else row[col]) for col in lotto2_df.columns}
                lotto2_lookup[norm_name] = row_dict

        for intersection in intersections:
            raw_name = intersection.get("raw_name", "")
            match_key = find_best_match(raw_name, lotto2_lookup, threshold=0.5)
            if match_key:
                intersection["lotto2_data"] = lotto2_lookup[match_key]
                intersection["lotto2_match_key"] = match_key

    # Match and merge Semaforica data (with fuzzy matching)
    if not semaforica_df.empty:
        name_col = None
        for col in semaforica_df.columns:
            if 'nome' in col.lower() or 'postazione' in col.lower():
                name_col = col
                break

        if name_col:
            semaforica_lookup = {}
            for idx, row in semaforica_df.iterrows():
                norm_name = normalize_intersection_name(row.get(name_col, ''))
                if norm_name:
                    row_dict = {col: (None if pd.isna(row[col]) else row[col]) for col in semaforica_df.columns}
                    semaforica_lookup[norm_name] = row_dict

            for intersection in intersections:
                raw_name = intersection.get("raw_name", "")
                match_key = find_best_match(raw_name, semaforica_lookup, threshold=0.5)
                if match_key:
                    intersection["semaforica_data"] = semaforica_lookup[match_key]
                    intersection["semaforica_match_key"] = match_key

    # Match and merge Swarco data (with fuzzy matching)
    if not swarco_df.empty:
        name_col = None
        for col in swarco_df.columns:
            if 'nome' in col.lower() or 'postazione' in col.lower():
                name_col = col
                break

        if name_col:
            swarco_lookup = {}
            for idx, row in swarco_df.iterrows():
                norm_name = normalize_intersection_name(row.get(name_col, ''))
                if norm_name:
                    row_dict = {col: (None if pd.isna(row[col]) else row[col]) for col in swarco_df.columns}
                    swarco_lookup[norm_name] = row_dict

            for intersection in intersections:
                raw_name = intersection.get("raw_name", "")
                match_key = find_best_match(raw_name, swarco_lookup, threshold=0.5)
                if match_key:
                    intersection["swarco_data"] = swarco_lookup[match_key]
                    intersection["swarco_match_key"] = match_key

    return intersections


def save_merged_data(intersections: List[Dict[str, Any]], filepath: str = MERGED_DATA_PATH):
    """Save merged data to JSON file."""
    # Convert any remaining numpy/pandas types to native Python types
    def convert_types(obj):
        import datetime
        if isinstance(obj, dict):
            return {k: convert_types(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [convert_types(i) for i in obj]
        elif isinstance(obj, (pd.Timestamp, datetime.datetime, datetime.date)):
            return obj.isoformat()
        elif hasattr(obj, 'item'):  # numpy types
            return obj.item()
        elif pd.isna(obj):
            return None
        return obj

    clean_data = convert_types(intersections)

    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(clean_data, f, indent=2, ensure_ascii=False)

    print(f"Saved {len(intersections)} intersection records to {filepath}")


def load_merged_data(filepath: str = MERGED_DATA_PATH) -> List[Dict[str, Any]]:
    """Load merged data from JSON file."""
    if not os.path.exists(filepath):
        return []

    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


if __name__ == "__main__":
    print("Extracting and merging data from Excel files...")
    intersections = merge_all_data()
    save_merged_data(intersections)

    # Print summary
    print(f"\nSummary:")
    print(f"  Total intersections: {len(intersections)}")
    print(f"  With Lotto 1 data: {sum(1 for i in intersections if i['lotto1_data'])}")
    print(f"  With Lotto 2 data: {sum(1 for i in intersections if i['lotto2_data'])}")
    print(f"  With Semaforica data: {sum(1 for i in intersections if i['semaforica_data'])}")
    print(f"  With Swarco data: {sum(1 for i in intersections if i['swarco_data'])}")
    print(f"  Intersection type (two+ streets): {sum(1 for i in intersections if i['is_intersection'])}")
