#!/usr/bin/env python3
"""
Comprehensive analysis of intersection data matching across all sources.
"""

import pandas as pd
import os
import re
from collections import defaultdict

DATA_DIR = "data-import"

def clean_column_name(name):
    if pd.isna(name):
        return "unnamed"
    name = str(name)
    name = name.replace('\n', ' ').replace('\r', '')
    name = re.sub(r'\s+', ' ', name).strip()
    return name

def normalize_name(name):
    """Normalize intersection name for matching."""
    if pd.isna(name):
        return ""
    name = str(name).lower().strip()
    # Remove numeric prefix
    name = re.sub(r'^\d+\s*[-–—]\s*', '', name)
    # Remove "cod. imp. XXXXX" suffix
    name = re.sub(r'\s*cod\.?\s*imp\.?\s*\d+\s*$', '', name)
    # Normalize whitespace
    name = re.sub(r'\s+', ' ', name).strip()
    # Sort streets in intersection names
    if '/' in name:
        streets = sorted([s.strip() for s in name.split('/')])
        name = '/'.join(streets)
    return name

# ============================================================================
# LOAD ALL DATA SOURCES
# ============================================================================

print("Loading data from all sources...")
print("=" * 80)

# 1. MAIN FILE (LOTTI M9_RADAR)
main_file = os.path.join(DATA_DIR, "LOTTI M9_RADAR_v1_2026.01.28.xlsx")
main_df = pd.read_excel(main_file, sheet_name="INST.FIN. LOTTI")
main_df.columns = [clean_column_name(c) for c in main_df.columns]

# Find the intersection name column
name_col = None
for col in main_df.columns:
    if 'nome' in col.lower() and 'postazione' in col.lower():
        name_col = col
        break

main_intersections = []
for idx, row in main_df.iterrows():
    raw_name = row.get(name_col, '')
    if pd.isna(raw_name) or not str(raw_name).strip():
        continue
    raw_name = str(raw_name).strip()
    # Skip header rows
    if any(x in raw_name.lower() for x in ['postazioni aggiuntive', 'progr', 'postazione in']):
        continue
    norm = normalize_name(raw_name)
    main_intersections.append({
        'raw_name': raw_name,
        'normalized': norm,
        'row_index': idx
    })

print(f"Main file (LOTTI M9_RADAR): {len(main_intersections)} intersections")

# 2. LOTTO 1
lotto1_file = os.path.join(DATA_DIR, "ELENCO_LOTTO_1_2026.01.23.xlsx")
lotto1_df = pd.read_excel(lotto1_file, sheet_name="Sheet1")
lotto1_df.columns = [clean_column_name(c) for c in lotto1_df.columns]

lotto1_intersections = []
for idx, row in lotto1_df.iterrows():
    raw_name = row.get('Impianto', '')
    if pd.isna(raw_name) or not str(raw_name).strip():
        continue
    raw_name = str(raw_name).strip()
    # Skip header rows
    if 'edison' in raw_name.lower() or 'impianto' in raw_name.lower():
        continue
    norm = normalize_name(raw_name)
    lotto1_intersections.append({
        'raw_name': raw_name,
        'normalized': norm,
        'row_index': idx
    })

print(f"Lotto 1: {len(lotto1_intersections)} intersections")

# 3. LOTTO 2
lotto2_file = os.path.join(DATA_DIR, "ELENCO LOTTO 2_2026.01.23.xlsx")
lotto2_df = pd.read_excel(lotto2_file, sheet_name="Foglio1")
lotto2_df.columns = [clean_column_name(c) for c in lotto2_df.columns]

lotto2_intersections = []
for idx, row in lotto2_df.iterrows():
    raw_name = row.get('indirizzo', '')
    if pd.isna(raw_name) or not str(raw_name).strip():
        continue
    raw_name = str(raw_name).strip()
    norm = normalize_name(raw_name)
    if norm:  # Skip empty after normalization
        lotto2_intersections.append({
            'raw_name': raw_name,
            'normalized': norm,
            'row_index': idx
        })

print(f"Lotto 2: {len(lotto2_intersections)} intersections")

# 4. SEMAFORICA
semaforica_file = os.path.join(DATA_DIR, "Elenco IS RADAR_SEMAFORICA_per VERIFICA STATO AUT.xlsx")
semaforica_df = pd.read_excel(semaforica_file, sheet_name="IMPIANTI SEMAFORICA")
semaforica_df.columns = [clean_column_name(c) for c in semaforica_df.columns]

semaforica_intersections = []
name_col_sem = None
for col in semaforica_df.columns:
    if 'nome' in col.lower() or 'postazione' in col.lower():
        name_col_sem = col
        break

if name_col_sem:
    for idx, row in semaforica_df.iterrows():
        raw_name = row.get(name_col_sem, '')
        if pd.isna(raw_name) or not str(raw_name).strip():
            continue
        raw_name = str(raw_name).strip()
        norm = normalize_name(raw_name)
        if norm:
            semaforica_intersections.append({
                'raw_name': raw_name,
                'normalized': norm,
                'row_index': idx
            })

print(f"Semaforica: {len(semaforica_intersections)} intersections")

# 5. SWARCO
swarco_file = os.path.join(DATA_DIR, "Swarco_Verifica stato - TOT_2026.01.29.xlsx")
swarco_df = pd.read_excel(swarco_file, sheet_name="Foglio1")
swarco_df.columns = [clean_column_name(c) for c in swarco_df.columns]

swarco_intersections = []
name_col_sw = None
for col in swarco_df.columns:
    if 'nome' in col.lower() or 'postazione' in col.lower():
        name_col_sw = col
        break

if name_col_sw:
    for idx, row in swarco_df.iterrows():
        raw_name = row.get(name_col_sw, '')
        if pd.isna(raw_name) or not str(raw_name).strip():
            continue
        raw_name = str(raw_name).strip()
        norm = normalize_name(raw_name)
        if norm:
            swarco_intersections.append({
                'raw_name': raw_name,
                'normalized': norm,
                'row_index': idx
            })

print(f"Swarco: {len(swarco_intersections)} intersections")

# ============================================================================
# BUILD LOOKUP TABLES
# ============================================================================

# Create lookup sets for each source
lotto1_lookup = {i['normalized']: i['raw_name'] for i in lotto1_intersections}
lotto2_lookup = {i['normalized']: i['raw_name'] for i in lotto2_intersections}
semaforica_lookup = {i['normalized']: i['raw_name'] for i in semaforica_intersections}
swarco_lookup = {i['normalized']: i['raw_name'] for i in swarco_intersections}
main_lookup = {i['normalized']: i['raw_name'] for i in main_intersections}

# ============================================================================
# ANALYSIS PART 1: For each main intersection, show which sources have data
# ============================================================================

print("\n" + "=" * 80)
print("PART 1: MAIN FILE INTERSECTIONS - DATA SOURCE MATCHING")
print("=" * 80)

# Counters
match_counts = {
    'lotto1': 0,
    'lotto2': 0,
    'semaforica': 0,
    'swarco': 0,
    'all_four': 0,
    'three': 0,
    'two': 0,
    'one': 0,
    'none': 0
}

results = []
for intersection in main_intersections:
    norm = intersection['normalized']
    raw = intersection['raw_name']

    has_lotto1 = norm in lotto1_lookup
    has_lotto2 = norm in lotto2_lookup
    has_semaforica = norm in semaforica_lookup
    has_swarco = norm in swarco_lookup

    if has_lotto1: match_counts['lotto1'] += 1
    if has_lotto2: match_counts['lotto2'] += 1
    if has_semaforica: match_counts['semaforica'] += 1
    if has_swarco: match_counts['swarco'] += 1

    total_matches = sum([has_lotto1, has_lotto2, has_semaforica, has_swarco])
    if total_matches == 4: match_counts['all_four'] += 1
    elif total_matches == 3: match_counts['three'] += 1
    elif total_matches == 2: match_counts['two'] += 1
    elif total_matches == 1: match_counts['one'] += 1
    else: match_counts['none'] += 1

    results.append({
        'name': raw,
        'lotto1': 'YES' if has_lotto1 else '-',
        'lotto2': 'YES' if has_lotto2 else '-',
        'semaforica': 'YES' if has_semaforica else '-',
        'swarco': 'YES' if has_swarco else '-',
        'total': total_matches
    })

# Print summary
print(f"\nSUMMARY:")
print(f"  Total main intersections: {len(main_intersections)}")
print(f"  With Lotto 1 data: {match_counts['lotto1']}")
print(f"  With Lotto 2 data: {match_counts['lotto2']}")
print(f"  With Semaforica data: {match_counts['semaforica']}")
print(f"  With Swarco data: {match_counts['swarco']}")
print(f"\n  With ALL 4 sources: {match_counts['all_four']}")
print(f"  With 3 sources: {match_counts['three']}")
print(f"  With 2 sources: {match_counts['two']}")
print(f"  With 1 source: {match_counts['one']}")
print(f"  With NO external data: {match_counts['none']}")

# Print detailed table
print(f"\n{'='*100}")
print(f"{'INTERSECTION NAME':<50} | {'LOTTO1':^7} | {'LOTTO2':^7} | {'SEMAF':^7} | {'SWARCO':^7} | {'TOTAL':^5}")
print(f"{'='*100}")

for r in sorted(results, key=lambda x: (-x['total'], x['name'])):
    print(f"{r['name'][:50]:<50} | {r['lotto1']:^7} | {r['lotto2']:^7} | {r['semaforica']:^7} | {r['swarco']:^7} | {r['total']:^5}")

# ============================================================================
# ANALYSIS PART 2: Find orphan records (no match in main file)
# ============================================================================

print("\n" + "=" * 80)
print("PART 2: ORPHAN RECORDS (in source files but NOT in main file)")
print("=" * 80)

# Lotto 1 orphans
lotto1_orphans = []
for intersection in lotto1_intersections:
    if intersection['normalized'] not in main_lookup:
        lotto1_orphans.append(intersection['raw_name'])

print(f"\n--- LOTTO 1 ORPHANS ({len(lotto1_orphans)} records) ---")
if lotto1_orphans:
    for name in sorted(lotto1_orphans):
        print(f"  - {name}")
else:
    print("  (none)")

# Lotto 2 orphans
lotto2_orphans = []
for intersection in lotto2_intersections:
    if intersection['normalized'] not in main_lookup:
        lotto2_orphans.append(intersection['raw_name'])

print(f"\n--- LOTTO 2 ORPHANS ({len(lotto2_orphans)} records) ---")
if lotto2_orphans:
    for name in sorted(lotto2_orphans):
        print(f"  - {name}")
else:
    print("  (none)")

# Semaforica orphans
semaforica_orphans = []
for intersection in semaforica_intersections:
    if intersection['normalized'] not in main_lookup:
        semaforica_orphans.append(intersection['raw_name'])

print(f"\n--- SEMAFORICA ORPHANS ({len(semaforica_orphans)} records) ---")
if semaforica_orphans:
    for name in sorted(semaforica_orphans):
        print(f"  - {name}")
else:
    print("  (none)")

# Swarco orphans
swarco_orphans = []
for intersection in swarco_intersections:
    if intersection['normalized'] not in main_lookup:
        swarco_orphans.append(intersection['raw_name'])

print(f"\n--- SWARCO ORPHANS ({len(swarco_orphans)} records) ---")
if swarco_orphans:
    for name in sorted(swarco_orphans):
        print(f"  - {name}")
else:
    print("  (none)")

# ============================================================================
# SUMMARY
# ============================================================================

print("\n" + "=" * 80)
print("FINAL SUMMARY")
print("=" * 80)

print(f"""
DATA COVERAGE:
  Main file has {len(main_intersections)} intersections

MATCHING RATES:
  Lotto 1:    {match_counts['lotto1']:3d} / {len(main_intersections)} matched ({100*match_counts['lotto1']/len(main_intersections):.1f}%)
  Lotto 2:    {match_counts['lotto2']:3d} / {len(main_intersections)} matched ({100*match_counts['lotto2']/len(main_intersections):.1f}%)
  Semaforica: {match_counts['semaforica']:3d} / {len(main_intersections)} matched ({100*match_counts['semaforica']/len(main_intersections):.1f}%)
  Swarco:     {match_counts['swarco']:3d} / {len(main_intersections)} matched ({100*match_counts['swarco']/len(main_intersections):.1f}%)

ORPHAN RECORDS (not in main file):
  Lotto 1:    {len(lotto1_orphans)} orphan records
  Lotto 2:    {len(lotto2_orphans)} orphan records
  Semaforica: {len(semaforica_orphans)} orphan records
  Swarco:     {len(swarco_orphans)} orphan records

INTERSECTIONS WITH NO EXTERNAL DATA: {match_counts['none']}
""")

# List intersections with no external data
if match_counts['none'] > 0:
    print("Intersections with NO external source data:")
    for r in results:
        if r['total'] == 0:
            print(f"  - {r['name']}")
