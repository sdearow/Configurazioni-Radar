#!/usr/bin/env python3
"""
Generate a clean master intersection report.
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

def safe_str(val):
    if pd.isna(val):
        return ''
    return str(val).strip()

def main():
    print("Loading all data sources...")

    # Load main LOTTI
    main_lotti_df = pd.read_excel(os.path.join(DATA_DIR, 'LOTTI M9_RADAR_v1_2026.01.28.xlsx'), sheet_name='INST.FIN. LOTTI')
    lotto1_df = pd.read_excel(os.path.join(DATA_DIR, 'ELENCO_LOTTO_1_2026.01.23.xlsx'), sheet_name='finale')
    lotto2_df = pd.read_excel(os.path.join(DATA_DIR, 'ELENCO LOTTO 2_2026.01.23.xlsx'), sheet_name='Foglio1')
    swarco_df = pd.read_excel(os.path.join(DATA_DIR, 'Swarco_Verifica stato - TOT_2026.01.29.xlsx'), sheet_name='Foglio1')
    semaforica_df = pd.read_excel(os.path.join(DATA_DIR, 'Elenco IS RADAR_SEMAFORICA_per VERIFICA STATO AUT.xlsx'), sheet_name='IMPIANTI SEMAFORICA')

    print("Creating master intersection list...")
    master_data = []

    for _, row in main_lotti_df.iterrows():
        postazione = row.get('Numero-Nome Postazione')
        if pd.isna(postazione):
            continue

        code, name = extract_code_and_name(postazione)
        if not code or not name:
            continue  # Skip rows without proper code-name format

        lotto = row.get('Lotto')
        if lotto not in ['M9.1', 'M9.2']:
            continue  # Skip rows without valid lotto

        codice_impianto = row.get('Codice\nImpianto')

        # Find matching SWARCO data
        swarco_match = None
        for _, sw_row in swarco_df.iterrows():
            sw_code, sw_name = extract_code_and_name(sw_row.get('Numero-Nome Postazione'))
            if code and sw_code and code == sw_code:
                swarco_match = sw_row
                break

        # Find matching Semaforica data
        sema_match = None
        for _, se_row in semaforica_df.iterrows():
            se_code, se_name = extract_code_and_name(se_row.get('Numero-Nome Postazione'))
            if code and se_code and code == se_code:
                sema_match = se_row
                break

        # Find matching Lotto 1 data (for M9.1)
        lotto1_match = None
        lotto1_match_score = 0
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
            'POSTAZIONE_CODE': code,
            'POSTAZIONE_NAME': name,
            'FULL_NAME': safe_str(postazione),
            'CODICE_IMPIANTO': safe_str(codice_impianto),
            'LOTTO': safe_str(lotto),
            'SISTEMA': safe_str(row.get('Sistema')),
            'N_DISPOSITIVI': safe_str(row.get('N.ro Dispositivi')),

            # Configuration info
            'PLAN_CFG_INVIATE': safe_str(row.get('Plan. e Cfg\nInviate')),
            'CFG_DEF_STATUS': safe_str(row.get('CFG. DEF. DaFare/\naff.GO/ daINVIARE')),
            'CFG_DEF_INST': safe_str(row.get('CFG. \nDEF. INST.')),
            'DA_CENTR_AUT': safe_str(row.get('da CENTR. con Sistema?\nDa installare AUT ?')),

            # Connection info
            'TABELLA_IF_UTC': safe_str(row.get('Tabella\nper \nIF UTC')),
            'INST_INTERFACCIA_UTC': safe_str(row.get('INST.\nInter-faccia UTC')),
            'VRF_DATI': safe_str(row.get('VRF\nDATI\nsu UTC\nsu DL')),

            # Installation status
            'DISP_INST_BLOCCATI': safe_str(row.get('Disp. Inst. o Cavidotti Bloccati')),
            'DISP_DA_INST': safe_str(row.get('Disp. \nDA \nINST.')),
            'SOLUZIONE_BLOCCATI': safe_str(row.get('Soluzione Cavidotti Bloccati')),
            'NOTE_MAIN': safe_str(row.get('Note')),
        }

        # Add SWARCO connection data
        if swarco_match is not None:
            record['SWARCO_SPOT_STATUS'] = safe_str(swarco_match.get('Centralizzati recenti: \nSPOT presente?\nNo SIM? '))
            record['SWARCO_SPOT_FIRMWARE'] = safe_str(swarco_match.get('SPOT:\nSu scheda (centralino SCAE)?\nCon firmware vecchio (da sostituire)?\nCon firmware recente (aggiornabile da remoto)?'))
        else:
            record['SWARCO_SPOT_STATUS'] = ''
            record['SWARCO_SPOT_FIRMWARE'] = ''

        # Add Semaforica AUT data
        if sema_match is not None:
            record['SEMA_AUT'] = safe_str(sema_match.get('AUT'))
            record['SEMA_ATTIVITA'] = safe_str(sema_match.get("ATTIVITA' DA FARE"))
        else:
            record['SEMA_AUT'] = ''
            record['SEMA_ATTIVITA'] = ''

        # Add Lotto 1 installation data
        if lotto1_match is not None and lotto1_match_score >= 0.7:
            record['L1_MATCH'] = safe_str(lotto1_match.get('Impianto'))
            record['L1_PLANIMETRIE'] = safe_str(lotto1_match.get('planimetrie ricevute'))
            record['L1_PASSAGGIO_CAVI'] = safe_str(lotto1_match.get('passaggio cavi'))
            record['L1_INSTALL_SENSORI'] = safe_str(lotto1_match.get('installazione sensori'))
            record['L1_CABLAGGIO'] = safe_str(lotto1_match.get('cablaggio regolatore'))
            record['L1_SCREENSHOT'] = safe_str(lotto1_match.get('Screenshoot'))
            record['L1_COMPLETATO'] = safe_str(lotto1_match.get('completato'))
            record['L1_DOC_INVIATA'] = safe_str(lotto1_match.get('Documentazione inviata'))
            record['L1_DATA_COMPL'] = safe_str(lotto1_match.get('data completamento'))
        else:
            record['L1_MATCH'] = f"UNCERTAIN ({lotto1_match_score:.2f})" if lotto1_match is not None and lotto1_match_score >= 0.5 else ''
            record['L1_PLANIMETRIE'] = ''
            record['L1_PASSAGGIO_CAVI'] = ''
            record['L1_INSTALL_SENSORI'] = ''
            record['L1_CABLAGGIO'] = ''
            record['L1_SCREENSHOT'] = ''
            record['L1_COMPLETATO'] = ''
            record['L1_DOC_INVIATA'] = ''
            record['L1_DATA_COMPL'] = ''

        # Add Lotto 2 installation data
        if lotto2_match is not None and lotto2_match_score >= 0.7:
            record['L2_MATCH'] = safe_str(lotto2_match.get('indirizzo'))
            record['L2_DATA_INSTALLAZ'] = safe_str(lotto2_match.get('data installaz'))
            record['L2_CONFIG_RSM'] = safe_str(lotto2_match.get('config.RSM'))
            record['L2_CONFIG_INSTAL'] = safe_str(lotto2_match.get('Config.instal.'))
            record['L2_PLANIMETRIA'] = safe_str(lotto2_match.get('planimetria'))
            record['L2_N_RADAR_FINITI'] = safe_str(lotto2_match.get('n.radar finiti'))
            record['L2_CENTRALIZZATI'] = safe_str(lotto2_match.get('centralizzati'))
        else:
            record['L2_MATCH'] = ''
            record['L2_DATA_INSTALLAZ'] = ''
            record['L2_CONFIG_RSM'] = ''
            record['L2_CONFIG_INSTAL'] = ''
            record['L2_PLANIMETRIA'] = ''
            record['L2_N_RADAR_FINITI'] = ''
            record['L2_CENTRALIZZATI'] = ''

        # Status columns (for user to fill)
        record['INSTALLATION_STATUS'] = ''
        record['CONFIGURATION_STATUS'] = ''
        record['CONNECTION_STATUS'] = ''
        record['VALIDATION_STATUS'] = ''

        master_data.append(record)

    # Create DataFrame
    df = pd.DataFrame(master_data)

    # Sort by Lotto, then by code
    def safe_sort_key(x):
        try:
            return int(float(x))
        except:
            return 9999

    df['sort_code'] = df['POSTAZIONE_CODE'].apply(safe_sort_key)
    df = df.sort_values(['LOTTO', 'sort_code'])
    df = df.drop(columns=['sort_code'])

    # Save to Excel with multiple sheets
    output_path = '/home/user/Configurazioni-Radar/data-import/MASTER_INTERSECTION_REPORT_CLEAN.xlsx'

    with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
        # All data
        df.to_excel(writer, sheet_name='All Intersections', index=False)

        # M9.1 only
        m91 = df[df['LOTTO'] == 'M9.1']
        m91.to_excel(writer, sheet_name='M9.1 Only', index=False)

        # M9.2 only
        m92 = df[df['LOTTO'] == 'M9.2']
        m92.to_excel(writer, sheet_name='M9.2 Only', index=False)

        # Uncertain matches only
        uncertain = df[df['L1_MATCH'].str.startswith('UNCERTAIN', na=False)]
        if len(uncertain) > 0:
            uncertain.to_excel(writer, sheet_name='Uncertain Matches', index=False)

    print(f"\nReport saved to: {output_path}")
    print(f"\nTotal intersections: {len(df)}")
    print(f"  - M9.1: {len(m91)}")
    print(f"  - M9.2: {len(m92)}")

    print(f"\nData coverage:")
    print(f"  - M9.1 with L1 installation data: {len(m91[m91['L1_MATCH'].str.len() > 0]) - len(m91[m91['L1_MATCH'].str.startswith('UNCERTAIN', na=False)])}")
    print(f"  - M9.1 with uncertain match: {len(m91[m91['L1_MATCH'].str.startswith('UNCERTAIN', na=False)])}")
    print(f"  - M9.2 with L2 installation data: {len(m92[m92['L2_MATCH'].str.len() > 0])}")
    print(f"  - With SWARCO data: {len(df[df['SWARCO_SPOT_STATUS'].str.len() > 0])}")
    print(f"  - With Semaforica data: {len(df[df['SEMA_AUT'].str.len() > 0])}")

    # Print sample
    print("\n" + "="*80)
    print("SAMPLE DATA (first 10 intersections)")
    print("="*80)
    for i, (_, row) in enumerate(df.head(10).iterrows()):
        print(f"\n{i+1}. [{row['LOTTO']}] {row['FULL_NAME']}")
        print(f"   Codice Impianto: {row['CODICE_IMPIANTO']}, Sistema: {row['SISTEMA']}, N.Disp: {row['N_DISPOSITIVI']}")
        print(f"   Config: {row['CFG_DEF_STATUS']} | UTC: {row['INST_INTERFACCIA_UTC']}")
        if row['L1_MATCH']:
            print(f"   L1 Match: {row['L1_MATCH'][:50]}")
        if row['L2_MATCH']:
            print(f"   L2 Match: {row['L2_MATCH'][:50]}")

    return df

if __name__ == '__main__':
    main()
