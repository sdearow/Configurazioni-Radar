#!/usr/bin/env python3
"""
Create a detailed intersection report with all data combined.
Outputs a CSV/Excel file for review.
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
    name = re.sub(r'^\d+\s*-\s*', '', name)

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

def safe_str(val):
    """Convert value to string safely."""
    if pd.isna(val):
        return ''
    return str(val).strip()

def load_main_lotti():
    """Load main LOTTI M9 file - first sheet."""
    filepath = os.path.join(DATA_DIR, 'LOTTI M9_RADAR_v1_2026.01.28.xlsx')
    df = pd.read_excel(filepath, sheet_name='INST.FIN. LOTTI')
    return df

def load_lotto1():
    """Load Lotto 1 file."""
    filepath = os.path.join(DATA_DIR, 'ELENCO_LOTTO_1_2026.01.23.xlsx')
    df = pd.read_excel(filepath, sheet_name='finale')
    return df

def load_lotto2():
    """Load Lotto 2 file."""
    filepath = os.path.join(DATA_DIR, 'ELENCO LOTTO 2_2026.01.23.xlsx')
    df = pd.read_excel(filepath, sheet_name='Foglio1')
    return df

def load_swarco():
    """Load SWARCO file."""
    filepath = os.path.join(DATA_DIR, 'Swarco_Verifica stato - TOT_2026.01.29.xlsx')
    df = pd.read_excel(filepath, sheet_name='Foglio1')
    return df

def load_semaforica():
    """Load Semaforica file."""
    filepath = os.path.join(DATA_DIR, 'Elenco IS RADAR_SEMAFORICA_per VERIFICA STATO AUT.xlsx')
    df = pd.read_excel(filepath, sheet_name='IMPIANTI SEMAFORICA')
    return df

def main():
    print("Loading all data sources...")

    # Load all data
    main_lotti_df = load_main_lotti()
    lotto1_df = load_lotto1()
    lotto2_df = load_lotto2()
    swarco_df = load_swarco()
    semaforica_df = load_semaforica()

    # Create master list from main LOTTI
    print("Creating master intersection list...")
    master_data = []

    for _, row in main_lotti_df.iterrows():
        postazione = row.get('Numero-Nome Postazione')
        if pd.isna(postazione):
            continue

        code, name = extract_code_and_name(postazione)
        if not name:
            continue

        codice_impianto = row.get('Codice\nImpianto')

        # Find matching SWARCO data
        swarco_match = None
        for _, sw_row in swarco_df.iterrows():
            sw_code, sw_name = extract_code_and_name(sw_row.get('Numero-Nome Postazione'))
            if code and sw_code and code == sw_code:
                swarco_match = sw_row
                break
            elif similarity_ratio(name, sw_name or '') > 0.8:
                swarco_match = sw_row
                break

        # Find matching Semaforica data
        sema_match = None
        for _, se_row in semaforica_df.iterrows():
            se_code, se_name = extract_code_and_name(se_row.get('Numero-Nome Postazione'))
            if code and se_code and code == se_code:
                sema_match = se_row
                break
            elif similarity_ratio(name, se_name or '') > 0.8:
                sema_match = se_row
                break

        # Find matching Lotto 1 data (for M9.1)
        lotto1_match = None
        lotto1_match_score = 0
        lotto = row.get('Lotto')
        if lotto == 'M9.1':
            for _, l1_row in lotto1_df.iterrows():
                l1_name = l1_row.get('Impianto')
                if pd.isna(l1_name):
                    continue
                score = similarity_ratio(name, str(l1_name))
                if score > lotto1_match_score:
                    lotto1_match_score = score
                    lotto1_match = l1_row

        # Find matching Lotto 2 data (for M9.2)
        lotto2_match = None
        lotto2_match_score = 0
        if lotto == 'M9.2':
            for _, l2_row in lotto2_df.iterrows():
                l2_name = l2_row.get('indirizzo')
                l2_codice = l2_row.get('codice')
                if pd.isna(l2_name):
                    continue

                # Check code match first
                try:
                    if codice_impianto and l2_codice:
                        if int(float(codice_impianto)) == int(float(l2_codice)):
                            lotto2_match = l2_row
                            lotto2_match_score = 1.0
                            break
                except:
                    pass

                score = similarity_ratio(name, str(l2_name))
                if score > lotto2_match_score:
                    lotto2_match_score = score
                    lotto2_match = l2_row

        # Build record
        record = {
            # Basic info
            'POSTAZIONE_CODE': code,
            'POSTAZIONE_NAME': name,
            'FULL_NAME': safe_str(postazione),
            'CODICE_IMPIANTO': safe_str(codice_impianto),
            'LOTTO': safe_str(lotto),
            'SISTEMA': safe_str(row.get('Sistema')),
            'CENTR': safe_str(row.get('Centr')),

            # Configuration (from main LOTTI)
            'N_DISPOSITIVI': safe_str(row.get('N.ro Dispositivi')),
            'PLAN_CFG_INVIATE': safe_str(row.get('Plan. e Cfg\nInviate')),
            'CFG_DEF_STATUS': safe_str(row.get('CFG. DEF. DaFare/\naff.GO/ daINVIARE')),
            'CFG_DEF_INST': safe_str(row.get('CFG. \nDEF. INST.')),
            'DA_CENTR_AUT': safe_str(row.get('da CENTR. con Sistema?\nDa installare AUT ?')),

            # Connection (from main LOTTI)
            'TABELLA_IF_UTC': safe_str(row.get('Tabella\nper \nIF UTC')),
            'INST_INTERFACCIA_UTC': safe_str(row.get('INST.\nInter-faccia UTC')),
            'VRF_DATI': safe_str(row.get('VRF\nDATI\nsu UTC\nsu DL')),

            # Installation blocking info
            'DISP_INST_BLOCCATI': safe_str(row.get('Disp. Inst. o Cavidotti Bloccati')),
            'DISP_DA_INST': safe_str(row.get('Disp. \nDA \nINST.')),
            'SOLUZIONE_BLOCCATI': safe_str(row.get('Soluzione Cavidotti Bloccati')),
            'NOTE_MAIN': safe_str(row.get('Note')),
        }

        # Add SWARCO data
        if swarco_match is not None:
            record['SWARCO_SPOT_STATUS'] = safe_str(swarco_match.get('Centralizzati recenti: \nSPOT presente?\nNo SIM? '))
            record['SWARCO_SPOT_FIRMWARE'] = safe_str(swarco_match.get('SPOT:\nSu scheda (centralino SCAE)?\nCon firmware vecchio (da sostituire)?\nCon firmware recente (aggiornabile da remoto)?'))
            record['SWARCO_CENTRALINO'] = safe_str(swarco_match.get('Centralino\nSCAE'))
        else:
            record['SWARCO_SPOT_STATUS'] = ''
            record['SWARCO_SPOT_FIRMWARE'] = ''
            record['SWARCO_CENTRALINO'] = ''

        # Add Semaforica data
        if sema_match is not None:
            record['SEMA_AUT'] = safe_str(sema_match.get('AUT'))
            record['SEMA_ATTIVITA'] = safe_str(sema_match.get("ATTIVITA' DA FARE"))
        else:
            record['SEMA_AUT'] = ''
            record['SEMA_ATTIVITA'] = ''

        # Add Lotto 1 installation data
        if lotto1_match is not None and lotto1_match_score >= 0.7:
            record['L1_MATCH_NAME'] = safe_str(lotto1_match.get('Impianto'))
            record['L1_MATCH_SCORE'] = f"{lotto1_match_score:.2f}"
            record['L1_PLANIMETRIE_RICEVUTE'] = safe_str(lotto1_match.get('planimetrie ricevute'))
            record['L1_PASSAGGIO_CAVI'] = safe_str(lotto1_match.get('passaggio cavi'))
            record['L1_PLANIMETRIA_SCAVI'] = safe_str(lotto1_match.get('planimetria scavi inviata a RSM'))
            record['L1_INSTALLAZIONE_SENSORI'] = safe_str(lotto1_match.get('installazione sensori'))
            record['L1_CABLAGGIO_REGOLATORE'] = safe_str(lotto1_match.get('cablaggio regolatore'))
            record['L1_SCREENSHOT'] = safe_str(lotto1_match.get('Screenshoot'))
            record['L1_COMPLETATO'] = safe_str(lotto1_match.get('completato'))
            record['L1_DOC_INVIATA'] = safe_str(lotto1_match.get('Documentazione inviata'))
            record['L1_DATA_COMPLETAMENTO'] = safe_str(lotto1_match.get('data completamento'))
        elif lotto1_match is not None and lotto1_match_score >= 0.5:
            # Uncertain match
            record['L1_MATCH_NAME'] = f"UNCERTAIN: {safe_str(lotto1_match.get('Impianto'))}"
            record['L1_MATCH_SCORE'] = f"{lotto1_match_score:.2f}"
            record['L1_PLANIMETRIE_RICEVUTE'] = ''
            record['L1_PASSAGGIO_CAVI'] = ''
            record['L1_PLANIMETRIA_SCAVI'] = ''
            record['L1_INSTALLAZIONE_SENSORI'] = ''
            record['L1_CABLAGGIO_REGOLATORE'] = ''
            record['L1_SCREENSHOT'] = ''
            record['L1_COMPLETATO'] = ''
            record['L1_DOC_INVIATA'] = ''
            record['L1_DATA_COMPLETAMENTO'] = ''
        else:
            record['L1_MATCH_NAME'] = ''
            record['L1_MATCH_SCORE'] = ''
            record['L1_PLANIMETRIE_RICEVUTE'] = ''
            record['L1_PASSAGGIO_CAVI'] = ''
            record['L1_PLANIMETRIA_SCAVI'] = ''
            record['L1_INSTALLAZIONE_SENSORI'] = ''
            record['L1_CABLAGGIO_REGOLATORE'] = ''
            record['L1_SCREENSHOT'] = ''
            record['L1_COMPLETATO'] = ''
            record['L1_DOC_INVIATA'] = ''
            record['L1_DATA_COMPLETAMENTO'] = ''

        # Add Lotto 2 installation data
        if lotto2_match is not None and lotto2_match_score >= 0.7:
            record['L2_MATCH_NAME'] = safe_str(lotto2_match.get('indirizzo'))
            record['L2_MATCH_SCORE'] = f"{lotto2_match_score:.2f}"
            record['L2_SCAVO_MARCIAPIEDE'] = safe_str(lotto2_match.get('scavo marciapiede'))
            record['L2_SCAVO_CARREGGIATA'] = safe_str(lotto2_match.get('scavo carreggiata'))
            record['L2_M_CAVO'] = safe_str(lotto2_match.get('m.cavo'))
            record['L2_DATA_INSTALLAZ'] = safe_str(lotto2_match.get('data installaz'))
            record['L2_CONFIG_RSM'] = safe_str(lotto2_match.get('config.RSM'))
            record['L2_CONFIG_INSTAL'] = safe_str(lotto2_match.get('Config.instal.'))
            record['L2_PLANIMETRIA'] = safe_str(lotto2_match.get('planimetria'))
            record['L2_N_RADAR_MONTATI_SENZA_CAVI'] = safe_str(lotto2_match.get('n.radar montati senza cavi'))
            record['L2_N_RADAR_MONTATI_CON_CAVI'] = safe_str(lotto2_match.get('n.radar montati con cavi senza collegamento'))
            record['L2_N_RADAR_FINITI'] = safe_str(lotto2_match.get('n.radar finiti'))
            record['L2_CENTRALIZZATI'] = safe_str(lotto2_match.get('centralizzati'))
        elif lotto2_match is not None and lotto2_match_score >= 0.5:
            record['L2_MATCH_NAME'] = f"UNCERTAIN: {safe_str(lotto2_match.get('indirizzo'))}"
            record['L2_MATCH_SCORE'] = f"{lotto2_match_score:.2f}"
            record['L2_SCAVO_MARCIAPIEDE'] = ''
            record['L2_SCAVO_CARREGGIATA'] = ''
            record['L2_M_CAVO'] = ''
            record['L2_DATA_INSTALLAZ'] = ''
            record['L2_CONFIG_RSM'] = ''
            record['L2_CONFIG_INSTAL'] = ''
            record['L2_PLANIMETRIA'] = ''
            record['L2_N_RADAR_MONTATI_SENZA_CAVI'] = ''
            record['L2_N_RADAR_MONTATI_CON_CAVI'] = ''
            record['L2_N_RADAR_FINITI'] = ''
            record['L2_CENTRALIZZATI'] = ''
        else:
            record['L2_MATCH_NAME'] = ''
            record['L2_MATCH_SCORE'] = ''
            record['L2_SCAVO_MARCIAPIEDE'] = ''
            record['L2_SCAVO_CARREGGIATA'] = ''
            record['L2_M_CAVO'] = ''
            record['L2_DATA_INSTALLAZ'] = ''
            record['L2_CONFIG_RSM'] = ''
            record['L2_CONFIG_INSTAL'] = ''
            record['L2_PLANIMETRIA'] = ''
            record['L2_N_RADAR_MONTATI_SENZA_CAVI'] = ''
            record['L2_N_RADAR_MONTATI_CON_CAVI'] = ''
            record['L2_N_RADAR_FINITI'] = ''
            record['L2_CENTRALIZZATI'] = ''

        # Status fields (for user to fill)
        record['INSTALLATION_STATUS'] = ''
        record['CONFIGURATION_STATUS'] = ''
        record['CONNECTION_STATUS'] = ''
        record['VALIDATION_STATUS'] = ''

        master_data.append(record)

    # Create DataFrame
    df = pd.DataFrame(master_data)

    # Sort by Lotto, then by code
    def safe_sort_key(x):
        if pd.isna(x) or x == '':
            return 9999
        try:
            return int(float(x))
        except:
            return 9999

    df['sort_code'] = df['POSTAZIONE_CODE'].apply(safe_sort_key)
    df = df.sort_values(['LOTTO', 'sort_code'])
    df = df.drop(columns=['sort_code'])

    # Save to Excel
    output_path = '/home/user/Configurazioni-Radar/data-import/MASTER_INTERSECTION_REPORT.xlsx'
    df.to_excel(output_path, index=False, sheet_name='All Intersections')

    print(f"\nReport saved to: {output_path}")
    print(f"Total intersections: {len(df)}")
    print(f"  - M9.1: {len(df[df['LOTTO'] == 'M9.1'])}")
    print(f"  - M9.2: {len(df[df['LOTTO'] == 'M9.2'])}")

    # Print uncertain matches that need confirmation
    print("\n" + "="*80)
    print("UNCERTAIN MATCHES REQUIRING YOUR CONFIRMATION")
    print("="*80)

    uncertain_l1 = df[df['L1_MATCH_NAME'].str.startswith('UNCERTAIN:', na=False)]
    uncertain_l2 = df[df['L2_MATCH_NAME'].str.startswith('UNCERTAIN:', na=False)]

    if len(uncertain_l1) > 0:
        print(f"\n--- LOTTO 1 Uncertain Matches ({len(uncertain_l1)}) ---")
        for _, row in uncertain_l1.iterrows():
            print(f"  MASTER: '{row['POSTAZIONE_NAME']}'")
            print(f"  LOTTO1: '{row['L1_MATCH_NAME'].replace('UNCERTAIN: ', '')}' (score: {row['L1_MATCH_SCORE']})")
            print(f"  -> Is this a match? (Y/N)\n")

    if len(uncertain_l2) > 0:
        print(f"\n--- LOTTO 2 Uncertain Matches ({len(uncertain_l2)}) ---")
        for _, row in uncertain_l2.iterrows():
            print(f"  MASTER: '{row['POSTAZIONE_NAME']}'")
            print(f"  LOTTO2: '{row['L2_MATCH_NAME'].replace('UNCERTAIN: ', '')}' (score: {row['L2_MATCH_SCORE']})")
            print(f"  -> Is this a match? (Y/N)\n")

    # Print summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)

    m91 = df[df['LOTTO'] == 'M9.1']
    m92 = df[df['LOTTO'] == 'M9.2']

    print(f"\nM9.1 ({len(m91)} intersections):")
    print(f"  - With Lotto 1 installation data: {len(m91[m91['L1_MATCH_NAME'].str.len() > 0])}")
    print(f"  - Uncertain matches: {len(uncertain_l1)}")

    print(f"\nM9.2 ({len(m92)} intersections):")
    print(f"  - With Lotto 2 installation data: {len(m92[m92['L2_MATCH_NAME'].str.len() > 0])}")
    print(f"  - Uncertain matches: {len(uncertain_l2)}")

    print(f"\nConnection data coverage:")
    print(f"  - With SWARCO data: {len(df[df['SWARCO_SPOT_STATUS'].str.len() > 0])}")
    print(f"  - With Semaforica data: {len(df[df['SEMA_AUT'].str.len() > 0])}")

    return df

if __name__ == '__main__':
    main()
