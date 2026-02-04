#!/usr/bin/env python3
"""
Find all unmatched records from Lotto 1 and Lotto 2 files.
"""

import pandas as pd
import os
import re
from difflib import SequenceMatcher

DATA_DIR = '/home/user/Configurazioni-Radar/data-import'

def normalize_name(name):
    if pd.isna(name) or not isinstance(name, str):
        return ''
    name = str(name).upper().strip()
    name = re.sub(r'^\d+\s*-\s*', '', name)
    return name.strip()

def extract_code_and_name(postazione):
    if pd.isna(postazione) or not isinstance(postazione, str):
        return None, None
    match = re.match(r'^(\d+)\s*-\s*(.+)$', str(postazione).strip())
    if match:
        return match.group(1), match.group(2).strip()
    return None, str(postazione).strip()

def similarity_ratio(a, b):
    if not a or not b:
        return 0
    return SequenceMatcher(None, normalize_name(a), normalize_name(b)).ratio()

def main():
    # Load main LOTTI
    main_lotti_df = pd.read_excel(os.path.join(DATA_DIR, 'LOTTI M9_RADAR_v1_2026.01.28.xlsx'), sheet_name='INST.FIN. LOTTI')

    # Extract master list
    master_m91 = []
    master_m92 = []

    for _, row in main_lotti_df.iterrows():
        postazione = row.get('Numero-Nome Postazione')
        if pd.isna(postazione):
            continue
        code, name = extract_code_and_name(postazione)
        lotto = row.get('Lotto')

        entry = {
            'code': code,
            'name': name,
            'full_name': str(postazione).strip(),
            'codice_impianto': row.get('Codice\nImpianto'),
        }

        if lotto == 'M9.1':
            master_m91.append(entry)
        elif lotto == 'M9.2':
            master_m92.append(entry)

    # Load Lotto 1
    lotto1_df = pd.read_excel(os.path.join(DATA_DIR, 'ELENCO_LOTTO_1_2026.01.23.xlsx'), sheet_name='finale')
    lotto1_names = []
    for _, row in lotto1_df.iterrows():
        name = row.get('Impianto')
        if pd.isna(name):
            continue
        lotto1_names.append({
            'name': str(name).strip(),
            'matched': False,
            'best_master': None,
            'best_score': 0
        })

    # Find matches for each Lotto 1 entry
    for l1 in lotto1_names:
        for master in master_m91:
            score = similarity_ratio(l1['name'], master['name'])
            if score > l1['best_score']:
                l1['best_score'] = score
                l1['best_master'] = master['name']
            if score >= 0.7:
                l1['matched'] = True

    # Load Lotto 2
    lotto2_df = pd.read_excel(os.path.join(DATA_DIR, 'ELENCO LOTTO 2_2026.01.23.xlsx'), sheet_name='Foglio1')
    lotto2_names = []
    for _, row in lotto2_df.iterrows():
        name = row.get('indirizzo')
        codice = row.get('codice')
        if pd.isna(name):
            continue
        lotto2_names.append({
            'name': str(name).strip(),
            'codice': codice,
            'matched': False,
            'best_master': None,
            'best_master_code': None,
            'best_score': 0
        })

    # Find matches for each Lotto 2 entry
    for l2 in lotto2_names:
        for master in master_m92:
            # Check code match first
            try:
                if l2['codice'] and master['codice_impianto']:
                    if int(float(l2['codice'])) == int(float(master['codice_impianto'])):
                        l2['matched'] = True
                        l2['best_master'] = master['name']
                        l2['best_master_code'] = master['codice_impianto']
                        l2['best_score'] = 1.0
                        continue
            except:
                pass

            score = similarity_ratio(l2['name'], master['name'])
            if score > l2['best_score']:
                l2['best_score'] = score
                l2['best_master'] = master['name']
                l2['best_master_code'] = master['codice_impianto']
            if score >= 0.7:
                l2['matched'] = True

    # Print unmatched Lotto 1
    print("="*80)
    print("LOTTO 1 - UNMATCHED OR UNCERTAIN RECORDS")
    print("="*80)

    unmatched_l1 = [l for l in lotto1_names if not l['matched']]
    print(f"\nTotal Lotto 1 records: {len(lotto1_names)}")
    print(f"Unmatched records: {len(unmatched_l1)}")

    print("\nDETAILED UNCERTAIN MATCHES FOR LOTTO 1:")
    print("-"*80)

    for l1 in sorted(lotto1_names, key=lambda x: x['best_score']):
        if l1['best_score'] < 0.7:
            status = "NO MATCH" if l1['best_score'] < 0.5 else "UNCERTAIN"
            print(f"\n[{status}] LOTTO1: '{l1['name']}'")
            print(f"         BEST MASTER: '{l1['best_master']}' (score: {l1['best_score']:.2f})")

    # Print unmatched Lotto 2
    print("\n" + "="*80)
    print("LOTTO 2 - UNMATCHED OR UNCERTAIN RECORDS")
    print("="*80)

    unmatched_l2 = [l for l in lotto2_names if not l['matched']]
    print(f"\nTotal Lotto 2 records: {len(lotto2_names)}")
    print(f"Unmatched records: {len(unmatched_l2)}")

    if unmatched_l2:
        print("\nDETAILED UNCERTAIN MATCHES FOR LOTTO 2:")
        print("-"*80)

        for l2 in sorted(unmatched_l2, key=lambda x: x['best_score']):
            status = "NO MATCH" if l2['best_score'] < 0.5 else "UNCERTAIN"
            print(f"\n[{status}] LOTTO2: '{l2['name']}' (cod: {l2['codice']})")
            print(f"         BEST MASTER: '{l2['best_master']}' (cod: {l2['best_master_code']}) (score: {l2['best_score']:.2f})")

    # Create a clear table for confirmation
    print("\n" + "="*80)
    print("INTERSECTIONS REQUIRING MANUAL MATCHING")
    print("="*80)

    print("\nPlease confirm the following matches (Y = Yes, N = No):\n")
    print(f"{'#':<3} | {'LOTTO 1 NAME':<45} | {'BEST MASTER MATCH':<45} | {'SCORE':<6}")
    print("-"*110)

    idx = 1
    for l1 in sorted([l for l in lotto1_names if l['best_score'] < 0.7 and l['best_score'] >= 0.5],
                     key=lambda x: -x['best_score']):
        print(f"{idx:<3} | {l1['name']:<45} | {l1['best_master'] or 'NONE':<45} | {l1['best_score']:.2f}")
        idx += 1

    print("\n" + "-"*110)
    print("NO MATCH FOUND IN MASTER (need to add manually or verify):")
    print("-"*110)

    for l1 in [l for l in lotto1_names if l['best_score'] < 0.5]:
        print(f"   | {l1['name']:<45} | (no good match)")

if __name__ == '__main__':
    main()
