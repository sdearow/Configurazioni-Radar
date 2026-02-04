#!/usr/bin/env python3
"""
Comprehensive intersection analysis - extract all intersections from all sources,
find fuzzy matches, and create a master report.
"""

import pandas as pd
import os
import re
from collections import defaultdict
from difflib import SequenceMatcher
import json

DATA_DIR = '/home/user/Configurazioni-Radar/data-import'

def normalize_name(name):
    """Normalize intersection name for comparison."""
    if pd.isna(name) or not isinstance(name, str):
        return ''

    name = str(name).upper().strip()

    # Remove the number prefix (e.g., "101-" or "101 -")
    name = re.sub(r'^\d+\s*-\s*', '', name)

    # Common replacements
    replacements = [
        (r'\s+', ' '),
        (r"V\.LE\b", 'VIALE'),
        (r"V\.LO\b", 'VICOLO'),
        (r"V\.\b", 'VIA'),
        (r"P\.ZZA\b", 'PIAZZA'),
        (r"P\.ZA\b", 'PIAZZA'),
        (r"P\.LE\b", 'PIAZZALE'),
        (r"L\.GO\b", 'LARGO'),
        (r"L\.TEVERE\b", 'LUNGOTEVERE'),
        (r"LGT\b", 'LUNGOTEVERE'),
        (r"L\.RE\b", 'LUNGOTEVERE'),
        (r"C\.SO\b", 'CORSO'),
        (r"G\.B\.", 'G.B.'),
        (r'\s*/\s*', '/'),
    ]

    for pattern, replacement in replacements:
        name = re.sub(pattern, replacement, name, flags=re.IGNORECASE)

    return name.strip()

def extract_code_and_name(postazione):
    """Extract code number and name from postazione string."""
    if pd.isna(postazione) or not isinstance(postazione, str):
        return None, None

    match = re.match(r'^(\d+)\s*-\s*(.+)$', str(postazione).strip())
    if match:
        return match.group(1), match.group(2).strip()
    return None, str(postazione).strip()

def similarity_ratio(a, b):
    """Calculate similarity between two strings."""
    if not a or not b:
        return 0
    return SequenceMatcher(None, normalize_name(a), normalize_name(b)).ratio()

def load_main_lotti():
    """Load main LOTTI M9 file - first sheet."""
    filepath = os.path.join(DATA_DIR, 'LOTTI M9_RADAR_v1_2026.01.28.xlsx')
    df = pd.read_excel(filepath, sheet_name='INST.FIN. LOTTI')

    intersections = []
    for _, row in df.iterrows():
        postazione = row.get('Numero-Nome Postazione')
        if pd.isna(postazione):
            continue

        code, name = extract_code_and_name(postazione)
        if not name:
            continue

        intersections.append({
            'source': 'MAIN_LOTTI',
            'code': code,
            'name': name,
            'full_name': str(postazione).strip(),
            'codice_impianto': row.get('Codice\nImpianto'),
            'lotto': row.get('Lotto'),
            'sistema': row.get('Sistema'),
            'centr': row.get('Centr'),
            'n_dispositivi': row.get('N.ro Dispositivi'),
            'plan_cfg_inviate': row.get('Plan. e Cfg\nInviate'),
            'cfg_def_status': row.get('CFG. DEF. DaFare/\naff.GO/ daINVIARE'),
            'cfg_def_inst': row.get('CFG. \nDEF. INST.'),
            'tabella_if_utc': row.get('Tabella\nper \nIF UTC'),
            'inst_interfaccia_utc': row.get('INST.\nInter-faccia UTC'),
            'vrf_dati': row.get('VRF\nDATI\nsu UTC\nsu DL'),
            'note': row.get('Note'),
            'disp_inst_bloccati': row.get('Disp. Inst. o Cavidotti Bloccati'),
            'disp_da_inst': row.get('Disp. \nDA \nINST.'),
            'soluzione_bloccati': row.get('Soluzione Cavidotti Bloccati'),
            'da_centr': row.get('da CENTR. con Sistema?\nDa installare AUT ?'),
        })

    return intersections

def load_lotto1():
    """Load Lotto 1 file."""
    filepath = os.path.join(DATA_DIR, 'ELENCO_LOTTO_1_2026.01.23.xlsx')
    df = pd.read_excel(filepath, sheet_name='finale')

    intersections = []
    for _, row in df.iterrows():
        impianto = row.get('Impianto')
        if pd.isna(impianto):
            continue

        intersections.append({
            'source': 'LOTTO1',
            'name': str(impianto).strip(),
            'id_lotto1': row.get('ID'),
            'cod': row.get('cod.'),
            'sistema': row.get('sistema'),
            'odl': row.get('ODL'),
            'installazione': row.get('installazione'),
            'planimetrie_ricevute': row.get('planimetrie ricevute'),
            'passaggio_cavi': row.get('passaggio cavi'),
            'planimetria_scavi_inviata': row.get('planimetria scavi inviata a RSM'),
            'installazione_sensori': row.get('installazione sensori'),
            'cablaggio_regolatore': row.get('cablaggio regolatore'),
            'screenshot': row.get('Screenshoot'),
            'completato': row.get('completato'),
            'documentazione_inviata': row.get('Documentazione inviata'),
            'data_completamento': row.get('data completamento'),
            'umr_info': {
                'umr1': row.get('UMR 1'),
                'ip1': row.get('IP'),
                'pos1': row.get('POSIZIONE'),
                'umr2': row.get('UMR 2'),
                'ip2': row.get('IP.1'),
                'pos2': row.get('POSIZIONE.1'),
            }
        })

    return intersections

def load_lotto2():
    """Load Lotto 2 file."""
    filepath = os.path.join(DATA_DIR, 'ELENCO LOTTO 2_2026.01.23.xlsx')
    df = pd.read_excel(filepath, sheet_name='Foglio1')

    intersections = []
    for _, row in df.iterrows():
        indirizzo = row.get('indirizzo')
        if pd.isna(indirizzo):
            continue

        intersections.append({
            'source': 'LOTTO2',
            'name': str(indirizzo).strip(),
            'codice': row.get('codice'),
            'n_progr': row.get('N.progr.'),
            'scavo_marciapiede': row.get('scavo marciapiede'),
            'scavo_carreggiata': row.get('scavo carreggiata'),
            'm_cavo': row.get('m.cavo'),
            'interfaccia': row.get('interfaccia'),
            'odl': row.get('ordine di lavoro'),
            'numero_radar': row.get('numero radar'),
            'data_installaz': row.get('data installaz'),
            'config_rsm': row.get('config.RSM'),
            'config_instal': row.get('Config.instal.'),
            'da_scavare': row.get('da scavare'),
            'planimetria': row.get('planimetria'),
            'n_radar_montati_senza_cavi': row.get('n.radar montati senza cavi'),
            'n_radar_montati_con_cavi': row.get('n.radar montati con cavi senza collegamento'),
            'n_radar_finiti': row.get('n.radar finiti'),
            'centralizzati': row.get('centralizzati'),
            'manca_sim': row.get('manca SIM'),
            'seriali': row.get('seriali'),
        })

    return intersections

def load_swarco():
    """Load SWARCO file."""
    filepath = os.path.join(DATA_DIR, 'Swarco_Verifica stato - TOT_2026.01.29.xlsx')
    df = pd.read_excel(filepath, sheet_name='Foglio1')

    intersections = []
    for _, row in df.iterrows():
        postazione = row.get('Numero-Nome Postazione')
        if pd.isna(postazione):
            continue

        code, name = extract_code_and_name(postazione)
        if not name:
            continue

        intersections.append({
            'source': 'SWARCO',
            'code': code,
            'name': name,
            'full_name': str(postazione).strip(),
            'lotto': row.get('Lotto'),
            'codice_impianto': row.get('Codice\nImpianto'),
            'sistema': row.get('Sistema'),
            'centralino_scae': row.get('Centralino\nSCAE'),
            'spot_status': row.get('Centralizzati recenti: \nSPOT presente?\nNo SIM? '),
            'spot_firmware': row.get('SPOT:\nSu scheda (centralino SCAE)?\nCon firmware vecchio (da sostituire)?\nCon firmware recente (aggiornabile da remoto)?'),
        })

    return intersections

def load_semaforica():
    """Load Semaforica file."""
    filepath = os.path.join(DATA_DIR, 'Elenco IS RADAR_SEMAFORICA_per VERIFICA STATO AUT.xlsx')
    df = pd.read_excel(filepath, sheet_name='IMPIANTI SEMAFORICA')

    intersections = []
    for _, row in df.iterrows():
        postazione = row.get('Numero-Nome Postazione')
        if pd.isna(postazione):
            continue

        code, name = extract_code_and_name(postazione)
        if not name:
            continue

        intersections.append({
            'source': 'SEMAFORICA',
            'code': code,
            'name': name,
            'full_name': str(postazione).strip(),
            'lotto': row.get('Lotto'),
            'codice_impianto': row.get('Codice\nImpianto'),
            'sistema': row.get('Sistema'),
            'aut': row.get('AUT'),
            'attivita_da_fare': row.get("ATTIVITA' DA FARE"),
        })

    return intersections

def find_fuzzy_matches(main_list, other_list, threshold=0.7):
    """Find fuzzy matches between main list and another list."""
    matches = []
    unmatched = []

    for other in other_list:
        other_name_norm = normalize_name(other['name'])
        best_match = None
        best_score = 0

        for main in main_list:
            main_name_norm = normalize_name(main['name'])
            score = similarity_ratio(main_name_norm, other_name_norm)

            # Also check codice_impianto if available
            if other.get('codice_impianto') and main.get('codice_impianto'):
                try:
                    if int(float(other['codice_impianto'])) == int(float(main['codice_impianto'])):
                        score = max(score, 0.95)  # High score for code match
                except:
                    pass

            if score > best_score:
                best_score = score
                best_match = main

        if best_score >= threshold:
            matches.append({
                'main': best_match,
                'other': other,
                'score': best_score,
                'exact': best_score > 0.95
            })
        else:
            unmatched.append({
                'item': other,
                'best_match': best_match,
                'best_score': best_score
            })

    return matches, unmatched

def main():
    """Main analysis function."""
    print("="*80)
    print("COMPREHENSIVE INTERSECTION ANALYSIS")
    print("="*80)

    # Load all data
    print("\n1. Loading data from all sources...")
    main_lotti = load_main_lotti()
    lotto1 = load_lotto1()
    lotto2 = load_lotto2()
    swarco = load_swarco()
    semaforica = load_semaforica()

    print(f"   - Main LOTTI: {len(main_lotti)} intersections")
    print(f"   - Lotto 1: {len(lotto1)} records")
    print(f"   - Lotto 2: {len(lotto2)} records")
    print(f"   - SWARCO: {len(swarco)} intersections")
    print(f"   - Semaforica: {len(semaforica)} intersections")

    # Create master list from MAIN LOTTI (most complete source)
    print("\n2. Creating master list from MAIN LOTTI...")
    master_list = {}
    for item in main_lotti:
        key = item['code'] if item['code'] else item['name']
        if key not in master_list:
            master_list[key] = {
                'code': item['code'],
                'name': item['name'],
                'full_name': item['full_name'],
                'codice_impianto': item['codice_impianto'],
                'lotto': item['lotto'],
                'sistema': item['sistema'],
                'main_lotti_data': item,
                'swarco_data': None,
                'semaforica_data': None,
                'lotto1_data': None,
                'lotto2_data': None,
            }

    print(f"   Master list has {len(master_list)} unique intersections")

    # Match SWARCO data
    print("\n3. Matching SWARCO data...")
    swarco_matches, swarco_unmatched = find_fuzzy_matches(list(master_list.values()), swarco, threshold=0.6)
    print(f"   - Matched: {len(swarco_matches)}")
    print(f"   - Unmatched: {len(swarco_unmatched)}")

    for match in swarco_matches:
        key = match['main']['code'] if match['main']['code'] else match['main']['name']
        if key in master_list:
            master_list[key]['swarco_data'] = match['other']

    # Match Semaforica data
    print("\n4. Matching Semaforica data...")
    sema_matches, sema_unmatched = find_fuzzy_matches(list(master_list.values()), semaforica, threshold=0.6)
    print(f"   - Matched: {len(sema_matches)}")
    print(f"   - Unmatched: {len(sema_unmatched)}")

    for match in sema_matches:
        key = match['main']['code'] if match['main']['code'] else match['main']['name']
        if key in master_list:
            master_list[key]['semaforica_data'] = match['other']

    # Match Lotto 1 data (fuzzy match on name)
    print("\n5. Matching Lotto 1 data...")
    # For Lotto 1/2 we need to match by name since they don't have the same code format
    lotto1_matched = 0
    lotto1_uncertain = []

    for l1 in lotto1:
        l1_name_norm = normalize_name(l1['name'])
        best_match = None
        best_score = 0

        for key, master in master_list.items():
            # Check if lotto matches (M9.1)
            if master['lotto'] != 'M9.1':
                continue

            master_name_norm = normalize_name(master['name'])
            score = similarity_ratio(master_name_norm, l1_name_norm)

            if score > best_score:
                best_score = score
                best_match = key

        if best_match and best_score >= 0.7:
            master_list[best_match]['lotto1_data'] = l1
            lotto1_matched += 1
        elif best_match and best_score >= 0.5:
            lotto1_uncertain.append({
                'lotto1_name': l1['name'],
                'master_name': master_list[best_match]['name'] if best_match else None,
                'score': best_score
            })

    print(f"   - Matched: {lotto1_matched}")
    print(f"   - Uncertain: {len(lotto1_uncertain)}")

    # Match Lotto 2 data
    print("\n6. Matching Lotto 2 data...")
    lotto2_matched = 0
    lotto2_uncertain = []

    for l2 in lotto2:
        l2_name_norm = normalize_name(l2['name'])
        best_match = None
        best_score = 0

        for key, master in master_list.items():
            # Check if lotto matches (M9.2)
            if master['lotto'] != 'M9.2':
                continue

            master_name_norm = normalize_name(master['name'])
            score = similarity_ratio(master_name_norm, l2_name_norm)

            # Also check codice
            if l2.get('codice') and master.get('codice_impianto'):
                try:
                    if int(float(l2['codice'])) == int(float(master['codice_impianto'])):
                        score = max(score, 0.95)
                except:
                    pass

            if score > best_score:
                best_score = score
                best_match = key

        if best_match and best_score >= 0.7:
            master_list[best_match]['lotto2_data'] = l2
            lotto2_matched += 1
        elif best_match and best_score >= 0.5:
            lotto2_uncertain.append({
                'lotto2_name': l2['name'],
                'lotto2_codice': l2.get('codice'),
                'master_name': master_list[best_match]['name'] if best_match else None,
                'master_codice': master_list[best_match]['codice_impianto'] if best_match else None,
                'score': best_score
            })

    print(f"   - Matched: {lotto2_matched}")
    print(f"   - Uncertain: {len(lotto2_uncertain)}")

    # Print uncertain matches for confirmation
    print("\n" + "="*80)
    print("UNCERTAIN MATCHES - NEED CONFIRMATION")
    print("="*80)

    if swarco_unmatched:
        print("\n--- SWARCO Unmatched ---")
        for item in swarco_unmatched[:20]:
            print(f"  '{item['item']['name']}' -> Best: '{item['best_match']['name'] if item['best_match'] else 'NONE'}' (score: {item['best_score']:.2f})")

    if sema_unmatched:
        print("\n--- Semaforica Unmatched ---")
        for item in sema_unmatched[:20]:
            print(f"  '{item['item']['name']}' -> Best: '{item['best_match']['name'] if item['best_match'] else 'NONE'}' (score: {item['best_score']:.2f})")

    if lotto1_uncertain:
        print("\n--- Lotto 1 Uncertain ---")
        for item in lotto1_uncertain[:20]:
            print(f"  '{item['lotto1_name']}' -> '{item['master_name']}' (score: {item['score']:.2f})")

    if lotto2_uncertain:
        print("\n--- Lotto 2 Uncertain ---")
        for item in lotto2_uncertain[:20]:
            print(f"  '{item['lotto2_name']}' (cod: {item['lotto2_codice']}) -> '{item['master_name']}' (cod: {item['master_codice']}) (score: {item['score']:.2f})")

    # Print summary statistics
    print("\n" + "="*80)
    print("SUMMARY STATISTICS")
    print("="*80)

    m91_count = sum(1 for m in master_list.values() if m['lotto'] == 'M9.1')
    m92_count = sum(1 for m in master_list.values() if m['lotto'] == 'M9.2')

    print(f"\nTotal intersections in master: {len(master_list)}")
    print(f"  - M9.1: {m91_count}")
    print(f"  - M9.2: {m92_count}")

    with_swarco = sum(1 for m in master_list.values() if m['swarco_data'])
    with_sema = sum(1 for m in master_list.values() if m['semaforica_data'])
    with_l1 = sum(1 for m in master_list.values() if m['lotto1_data'])
    with_l2 = sum(1 for m in master_list.values() if m['lotto2_data'])

    print(f"\nData coverage:")
    print(f"  - With SWARCO data: {with_swarco}")
    print(f"  - With Semaforica data: {with_sema}")
    print(f"  - With Lotto 1 installation data: {with_l1}")
    print(f"  - With Lotto 2 installation data: {with_l2}")

    # Save master list to JSON for inspection
    output_path = '/home/user/Configurazioni-Radar/data-import/master_intersections.json'
    with open(output_path, 'w', encoding='utf-8') as f:
        # Convert to serializable format
        serializable = {}
        for k, v in master_list.items():
            serializable[k] = {
                'code': v['code'],
                'name': v['name'],
                'full_name': v['full_name'],
                'codice_impianto': str(v['codice_impianto']) if v['codice_impianto'] else None,
                'lotto': v['lotto'],
                'sistema': v['sistema'],
                'has_main_lotti': v['main_lotti_data'] is not None,
                'has_swarco': v['swarco_data'] is not None,
                'has_semaforica': v['semaforica_data'] is not None,
                'has_lotto1': v['lotto1_data'] is not None,
                'has_lotto2': v['lotto2_data'] is not None,
            }
        json.dump(serializable, f, indent=2, ensure_ascii=False)

    print(f"\n\nMaster list saved to: {output_path}")

    # Print all intersections sorted
    print("\n" + "="*80)
    print("COMPLETE INTERSECTION LIST")
    print("="*80)

    sorted_intersections = sorted(master_list.values(), key=lambda x: (x['lotto'] or '', x['code'] or '999', x['name']))

    for i, item in enumerate(sorted_intersections, 1):
        flags = []
        if item['swarco_data']:
            flags.append('SWARCO')
        if item['semaforica_data']:
            flags.append('SEMA')
        if item['lotto1_data']:
            flags.append('L1')
        if item['lotto2_data']:
            flags.append('L2')

        flags_str = ','.join(flags) if flags else '-'
        print(f"{i:3}. [{item['lotto']}] {item['full_name']:<50} (Cod: {item['codice_impianto']}) [{flags_str}]")

    return master_list, lotto1_uncertain, lotto2_uncertain, swarco_unmatched, sema_unmatched

if __name__ == '__main__':
    main()
