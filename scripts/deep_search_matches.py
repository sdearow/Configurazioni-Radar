#!/usr/bin/env python3
"""
Deep search for unmatched Lotto 1 records across all master intersections.
"""

import pandas as pd
import os
import re
from difflib import SequenceMatcher

DATA_DIR = '/home/user/Configurazioni-Radar/data-import'

def normalize_name(name):
    if pd.isna(name) or not isinstance(name, str):
        return ''
    return str(name).upper().strip()

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

def keyword_match(l1_name, master_name):
    """Check if key words match between names."""
    l1_words = set(normalize_name(l1_name).replace('/', ' ').replace('-', ' ').split())
    master_words = set(normalize_name(master_name).replace('/', ' ').replace('-', ' ').split())

    # Remove common words
    common_words = {'VIA', 'VIALE', 'PIAZZA', 'PIAZZALE', 'LARGO', 'PONTE', 'CORSO', 'LUNGOTEVERE', 'L', 'P', 'V'}
    l1_words = l1_words - common_words
    master_words = master_words - common_words

    if not l1_words or not master_words:
        return 0

    intersection = l1_words & master_words
    return len(intersection) / min(len(l1_words), len(master_words))

def main():
    # Load main LOTTI - ALL intersections (both M9.1 and M9.2)
    main_lotti_df = pd.read_excel(os.path.join(DATA_DIR, 'LOTTI M9_RADAR_v1_2026.01.28.xlsx'), sheet_name='INST.FIN. LOTTI')

    # Extract master list
    master_all = []
    for _, row in main_lotti_df.iterrows():
        postazione = row.get('Numero-Nome Postazione')
        if pd.isna(postazione):
            continue
        code, name = extract_code_and_name(postazione)
        master_all.append({
            'code': code,
            'name': name,
            'full_name': str(postazione).strip(),
            'codice_impianto': row.get('Codice\nImpianto'),
            'lotto': row.get('Lotto'),
        })

    # Unmatched Lotto 1 items
    unmatched_l1 = [
        'Emo - Bus',
        'L.RE Diaz - Largo Mllo Diaz',
        'Via Cristoforo Colombo - Via Druso',
        'Ponte Garibaldi/Trastevere',
        'Galvani/Marmorata/Gelsomini',
        'Viale Camillo Sabatini',
        'Rolli/Porta',
        'Milizie/Angelico',
        'Piazzale Ostiense',
        'Via Cernaia - Via Goito',
        'Marconi/Pincherle',
        'P.le Umanesimo',
        'Portuense/Casetta Mattei',
        'Via Anastasio II - Pio XI',
        'Piazza di porta Portese',
        'Aventino/Circo Massimo',
        'Piazza Pia/Conciliazione',
        'Rolli/Pascarella',
        'Ponte Matteotti/P.zza delle Cinque Giornate',
        'Ponte Garibaldi/Arenula',
        'Ponte Risorgimento/P.zza Monte Grappa',
        'Ponte Mazzini/Lungara/L.re Farnesina',
        'Ponte Mazzini/L.re Tebaldi/L.re San Gallo',
        'Ponte Sublicio',
        'Rolli/Stradivari',
    ]

    print("="*100)
    print("DEEP SEARCH FOR LOTTO 1 UNMATCHED INTERSECTIONS")
    print("Searching across ALL master intersections (M9.1 and M9.2)")
    print("="*100)

    for l1_name in unmatched_l1:
        print(f"\n{'='*80}")
        print(f"LOTTO 1: '{l1_name}'")
        print("-"*80)

        # Find all potential matches
        matches = []
        for master in master_all:
            sim_score = similarity_ratio(l1_name, master['name'])
            kw_score = keyword_match(l1_name, master['name'])
            combined_score = (sim_score + kw_score) / 2

            if sim_score > 0.3 or kw_score > 0.3:
                matches.append({
                    'master_name': master['name'],
                    'full_name': master['full_name'],
                    'lotto': master['lotto'],
                    'codice': master['codice_impianto'],
                    'sim_score': sim_score,
                    'kw_score': kw_score,
                    'combined': combined_score
                })

        # Sort by combined score
        matches.sort(key=lambda x: -x['combined'])

        if matches:
            print(f"Top matches (by similarity + keyword):")
            for m in matches[:5]:
                print(f"  [{m['lotto']}] {m['full_name']:<50} (sim: {m['sim_score']:.2f}, kw: {m['kw_score']:.2f})")
        else:
            print("  No matches found!")

    # Also print the complete list of master intersections for reference
    print("\n" + "="*100)
    print("COMPLETE MASTER LIST FOR REFERENCE")
    print("="*100)

    m91_masters = sorted([m for m in master_all if m['lotto'] == 'M9.1'], key=lambda x: x['full_name'])
    print(f"\n--- M9.1 ({len(m91_masters)} intersections) ---")
    for m in m91_masters:
        print(f"  {m['full_name']}")

if __name__ == '__main__':
    main()
