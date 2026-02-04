#!/usr/bin/env python3
"""
Analyze all Excel files to extract and match intersections across different sources.
"""

import pandas as pd
import os
import re
from collections import defaultdict
from difflib import SequenceMatcher
import json

# Data directory
DATA_DIR = '/home/user/Configurazioni-Radar/data-import'

def normalize_name(name):
    """Normalize intersection name for comparison."""
    if pd.isna(name) or not isinstance(name, str):
        return ''

    # Convert to uppercase
    name = str(name).upper().strip()

    # Common replacements
    replacements = [
        (r'\s+', ' '),  # Multiple spaces to single
        (r'V\.LE', 'VIALE'),
        (r'V\.LE\.', 'VIALE'),
        (r'V\.LO', 'VICOLO'),
        (r'V\.', 'VIA'),
        (r'P\.ZZA', 'PIAZZA'),
        (r'P\.ZA', 'PIAZZA'),
        (r'P\.LE', 'PIAZZALE'),
        (r'P\.', 'PIAZZA'),
        (r'L\.GO', 'LARGO'),
        (r'L\.GHE', 'LUNGHE'),
        (r'L\.TEVERE', 'LUNGOTEVERE'),
        (r'C\.SO', 'CORSO'),
        (r'S\.S\.', 'SS'),
        (r'/',' / '),
        (r'\s+/\s+', ' / '),  # Normalize slashes
        (r'\s+-\s+', ' / '),  # Dashes to slashes
        (r'\s*\(\s*', ' ('),  # Normalize parentheses
        (r'\s*\)\s*', ') '),
    ]

    for pattern, replacement in replacements:
        name = re.sub(pattern, replacement, name)

    return name.strip()

def similarity_ratio(a, b):
    """Calculate similarity between two strings."""
    return SequenceMatcher(None, a, b).ratio()

def extract_from_lotto1():
    """Extract intersections from Lotto 1 file."""
    filepath = os.path.join(DATA_DIR, 'ELENCO_LOTTO_1_2026.01.23.xlsx')
    print(f"\n{'='*60}")
    print(f"Analyzing: LOTTO 1")
    print(f"{'='*60}")

    try:
        # Read all sheets
        xl = pd.ExcelFile(filepath)
        print(f"Sheets: {xl.sheet_names}")

        results = []
        for sheet in xl.sheet_names:
            df = pd.read_excel(filepath, sheet_name=sheet)
            print(f"\n--- Sheet: {sheet} ---")
            print(f"Columns: {list(df.columns)}")
            print(f"Rows: {len(df)}")

            # Try to identify intersection column
            for col in df.columns:
                if any(keyword in str(col).upper() for keyword in ['INCROCIO', 'INTERSEZIONE', 'VIA', 'NOME', 'LOCATION']):
                    print(f"  Potential intersection column: {col}")
                    unique_vals = df[col].dropna().unique()
                    print(f"  Unique values: {len(unique_vals)}")
                    if len(unique_vals) < 50:
                        for v in unique_vals[:10]:
                            print(f"    - {v}")

            # Store full dataframe for later
            results.append({'sheet': sheet, 'df': df})

        return results
    except Exception as e:
        print(f"Error reading Lotto 1: {e}")
        return []

def extract_from_lotto2():
    """Extract intersections from Lotto 2 file."""
    filepath = os.path.join(DATA_DIR, 'ELENCO LOTTO 2_2026.01.23.xlsx')
    print(f"\n{'='*60}")
    print(f"Analyzing: LOTTO 2")
    print(f"{'='*60}")

    try:
        xl = pd.ExcelFile(filepath)
        print(f"Sheets: {xl.sheet_names}")

        results = []
        for sheet in xl.sheet_names:
            df = pd.read_excel(filepath, sheet_name=sheet)
            print(f"\n--- Sheet: {sheet} ---")
            print(f"Columns: {list(df.columns)}")
            print(f"Rows: {len(df)}")

            for col in df.columns:
                if any(keyword in str(col).upper() for keyword in ['INCROCIO', 'INTERSEZIONE', 'VIA', 'NOME', 'LOCATION']):
                    print(f"  Potential intersection column: {col}")
                    unique_vals = df[col].dropna().unique()
                    print(f"  Unique values: {len(unique_vals)}")

            results.append({'sheet': sheet, 'df': df})

        return results
    except Exception as e:
        print(f"Error reading Lotto 2: {e}")
        return []

def extract_from_swarco():
    """Extract intersections from SWARCO file."""
    filepath = os.path.join(DATA_DIR, 'Swarco_Verifica stato - TOT_2026.01.29.xlsx')
    print(f"\n{'='*60}")
    print(f"Analyzing: SWARCO")
    print(f"{'='*60}")

    try:
        xl = pd.ExcelFile(filepath)
        print(f"Sheets: {xl.sheet_names}")

        results = []
        for sheet in xl.sheet_names:
            df = pd.read_excel(filepath, sheet_name=sheet)
            print(f"\n--- Sheet: {sheet} ---")
            print(f"Columns: {list(df.columns)}")
            print(f"Rows: {len(df)}")

            # Show first few rows
            print(f"First 3 rows:")
            print(df.head(3).to_string())

            results.append({'sheet': sheet, 'df': df})

        return results
    except Exception as e:
        print(f"Error reading SWARCO: {e}")
        return []

def extract_from_semaforica():
    """Extract intersections from Semaforica file."""
    filepath = os.path.join(DATA_DIR, 'Elenco IS RADAR_SEMAFORICA_per VERIFICA STATO AUT.xlsx')
    print(f"\n{'='*60}")
    print(f"Analyzing: SEMAFORICA")
    print(f"{'='*60}")

    try:
        xl = pd.ExcelFile(filepath)
        print(f"Sheets: {xl.sheet_names}")

        results = []
        for sheet in xl.sheet_names:
            df = pd.read_excel(filepath, sheet_name=sheet)
            print(f"\n--- Sheet: {sheet} ---")
            print(f"Columns: {list(df.columns)}")
            print(f"Rows: {len(df)}")

            print(f"First 3 rows:")
            print(df.head(3).to_string())

            results.append({'sheet': sheet, 'df': df})

        return results
    except Exception as e:
        print(f"Error reading Semaforica: {e}")
        return []

def extract_from_main_lotti():
    """Extract intersections from main LOTTI M9 file."""
    filepath = os.path.join(DATA_DIR, 'LOTTI M9_RADAR_v1_2026.01.28.xlsx')
    print(f"\n{'='*60}")
    print(f"Analyzing: MAIN LOTTI M9")
    print(f"{'='*60}")

    try:
        xl = pd.ExcelFile(filepath)
        print(f"Sheets: {xl.sheet_names}")

        results = []
        for sheet in xl.sheet_names:
            df = pd.read_excel(filepath, sheet_name=sheet)
            print(f"\n--- Sheet: {sheet} ---")
            print(f"Columns: {list(df.columns)}")
            print(f"Rows: {len(df)}")

            # Show first few rows
            print(f"First 5 rows:")
            print(df.head(5).to_string())

            results.append({'sheet': sheet, 'df': df})

        return results
    except Exception as e:
        print(f"Error reading Main LOTTI: {e}")
        return []

def main():
    """Main analysis function."""
    print("="*80)
    print("INTERSECTION ANALYSIS - ALL FILES")
    print("="*80)

    # Analyze all files
    lotto1_data = extract_from_lotto1()
    lotto2_data = extract_from_lotto2()
    swarco_data = extract_from_swarco()
    semaforica_data = extract_from_semaforica()
    main_lotti_data = extract_from_main_lotti()

    print("\n" + "="*80)
    print("ANALYSIS COMPLETE")
    print("="*80)

if __name__ == '__main__':
    main()
