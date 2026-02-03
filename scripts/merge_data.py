#!/usr/bin/env python3
"""
Merge radar data from multiple Excel files into a unified JSON format.
Identifies and flags inconsistencies between data sources.
"""

import pandas as pd
import json
import warnings
from datetime import datetime
from pathlib import Path

warnings.filterwarnings('ignore')

def safe_int_str(x):
    """Convert to int string, return None if not possible"""
    try:
        return str(int(float(x)))
    except:
        return None

def safe_str(x):
    """Convert to string, return empty string if NaN"""
    if pd.isna(x):
        return ""
    return str(x).strip()

def safe_int(x):
    """Convert to int, return None if not possible"""
    try:
        return int(float(x))
    except:
        return None

def safe_date(x):
    """Convert to ISO date string"""
    if pd.isna(x):
        return None
    try:
        if isinstance(x, str):
            return x
        return x.strftime('%Y-%m-%d')
    except:
        return str(x)

def load_and_clean_files(data_dir):
    """Load all Excel files and clean column names"""

    # Load main file
    main_file = pd.read_excel(data_dir / "LOTTI M9_RADAR_v1_2026.01.28.xlsx", sheet_name=0)
    main_file.columns = [str(c).replace('\n', ' ').strip() for c in main_file.columns]

    # Load Lotto files
    lotto1 = pd.read_excel(data_dir / "ELENCO_LOTTO_1_2026.01.23.xlsx", sheet_name=0)
    lotto2 = pd.read_excel(data_dir / "ELENCO LOTTO 2_2026.01.23.xlsx", sheet_name=0)

    # Load central system files
    semaforica = pd.read_excel(data_dir / "Elenco IS RADAR_SEMAFORICA_per VERIFICA STATO AUT.xlsx", sheet_name=0)
    semaforica.columns = [str(c).replace('\n', ' ').strip() for c in semaforica.columns]

    swarco = pd.read_excel(data_dir / "Swarco_Verifica stato - TOT_2026.01.29.xlsx", sheet_name=0)
    swarco.columns = [str(c).replace('\n', ' ').strip() for c in swarco.columns]

    return main_file, lotto1, lotto2, semaforica, swarco

def extract_lotto1_data(lotto1):
    """Extract and structure Lotto 1 (Engin) data"""
    lotto1_dict = {}

    for _, row in lotto1.iterrows():
        code = safe_int_str(row.get('cod.'))
        if not code:
            continue

        # Extract sensor IDs
        sensors = []
        for i in range(1, 8):
            sensor_id = safe_str(row.get(f'ID sensore {i}', ''))
            if sensor_id:
                sensors.append(sensor_id)

        lotto1_dict[code] = {
            'name': safe_str(row.get('Impianto', '')),
            'company': 'ENG',  # Engin
            'sensors': sensors,
            'num_radars': len(sensors) if sensors else safe_int(row.get('N° Radar', 0)),
            'cable_passage': safe_str(row.get('Passaggio cavi', '')),
            'sensor_installation': safe_str(row.get('installazione sensori', '')),
            'regulator_wiring': safe_str(row.get('cablaggio regolatore', '')),
            'screenshots': safe_str(row.get('screenshot', '')),
            'completion_date': safe_date(row.get('data completamento')),
            'system': safe_str(row.get('sistema', '')),
            'planimetry_sent': safe_str(row.get('planimetria inviata', '')),
            'documentation_sent': safe_str(row.get('documentazione inviata', '')),
        }

    return lotto1_dict

def extract_lotto2_data(lotto2):
    """Extract and structure Lotto 2 data"""
    lotto2_dict = {}

    for _, row in lotto2.iterrows():
        code = safe_int_str(row.get('codice'))
        if not code:
            continue

        lotto2_dict[code] = {
            'name': safe_str(row.get('indirizzo', '')),
            'company': 'M9.2',  # Lotto M9.2 company
            'num_radars': safe_int(row.get('numero radar', 0)),
            'installation_date': safe_date(row.get('data installaz')),
            'config_rsm_date': safe_date(row.get('config.RSM')),
            'config_installed_date': safe_date(row.get('Config.instal.')),
            'excavation_sidewalk': safe_int(row.get('scavo marciapiede', 0)),
            'excavation_road': safe_int(row.get('scavo carreggiata', 0)),
            'cable_meters': safe_int(row.get('m.cavo', 0)),
            'radars_mounted_no_cables': safe_str(row.get('n.radar montati senza cavi', '')),
            'radars_mounted_no_connection': safe_str(row.get('n.radar montati con cavi senza collegamento', '')),
            'radars_finished': safe_int(row.get('n.radar finiti', 0)),
            'centralized': safe_str(row.get('centralizzati', '')),
            'missing_sim': safe_str(row.get('manca SIM', '')),
            'serials': safe_str(row.get('seriali', '')),
            'planimetry': safe_str(row.get('planimetria', '')),
            'order_sap': safe_str(row.get('ordine sap', '')),
        }

    return lotto2_dict

def extract_semaforica_data(semaforica):
    """Extract Semaforica (AUT/TMacs) data"""
    semaforica_dict = {}

    for _, row in semaforica.iterrows():
        code = safe_int_str(row.get('Codice Impianto'))
        if not code:
            continue

        # Get AUT status column (has complex name)
        aut_col = [c for c in semaforica.columns if 'AUT' in c and 'presente' in c.lower()]
        aut_status = safe_str(row.get(aut_col[0], '')) if aut_col else ''

        # Get action column
        action_col = [c for c in semaforica.columns if 'da configurare' in c.lower() or 'sostituire' in c.lower()]
        action = safe_str(row.get(action_col[0], '')) if action_col else ''

        semaforica_dict[code] = {
            'system': safe_str(row.get('Sistema', '')),
            'aut_status': aut_status,
            'aut_action': action,
        }

    return semaforica_dict

def extract_swarco_data(swarco):
    """Extract Swarco (SPOT/Omnia) data"""
    swarco_dict = {}

    for _, row in swarco.iterrows():
        code = safe_int_str(row.get('Codice Impianto'))
        if not code:
            continue

        # Get SPOT presence column
        spot_col = [c for c in swarco.columns if 'SPOT presente' in c]
        spot_presence = safe_str(row.get(spot_col[0], '')) if spot_col else ''

        # Get SPOT status column
        status_col = [c for c in swarco.columns if 'firmware' in c.lower()]
        spot_status = safe_str(row.get(status_col[0], '')) if status_col else ''

        swarco_dict[code] = {
            'system': safe_str(row.get('Sistema', '')),
            'centralino_scae': safe_str(row.get('Centralino SCAE', '')),
            'spot_presence': spot_presence,
            'spot_status': spot_status,
        }

    return swarco_dict

def determine_stage(row):
    """Determine the current stage based on status columns"""

    cfg_def_status = safe_str(row.get('CFG. DEF. DaFare/ aff.GO/ daINVIARE', ''))
    cfg_installed = safe_str(row.get('CFG.  DEF. INST.', ''))
    utc_table = safe_str(row.get('Tabella per  IF UTC', ''))
    utc_interface = safe_str(row.get('INST. Inter-faccia UTC', ''))
    data_verified = safe_str(row.get('VRF DATI su UTC su DL', ''))

    # Stage 4: Validation
    if data_verified and 'VRF' in data_verified.upper():
        return 'validation'

    # Stage 3: Connection
    if utc_interface and ('INST' in utc_interface.upper() or 'ok' in utc_interface.lower()):
        return 'connection'

    # Stage 2: Configuration
    if cfg_installed and ('INST' in cfg_installed.upper() or 'ok' in cfg_installed.lower()):
        return 'configuration'

    if cfg_def_status:
        if 'ok' in cfg_def_status.lower():
            return 'configuration'
        if 'INVIATA' in cfg_def_status.upper():
            return 'configuration'
        if 'aff.GO' in cfg_def_status or 'DaFare' in cfg_def_status or 'daINVIARE' in cfg_def_status:
            return 'installation'

    # Stage 1: Installation (default)
    return 'installation'

def determine_stage_status(row, stage):
    """Determine status within the current stage"""

    if stage == 'installation':
        disp_inst = safe_str(row.get('Disp. Inst. o Cavidotti Bloccati', ''))
        if 'BLOCCATI' in disp_inst.upper():
            return 'blocked'
        if disp_inst and disp_inst != '0':
            return 'in_progress'
        return 'pending'

    elif stage == 'configuration':
        cfg_def_status = safe_str(row.get('CFG. DEF. DaFare/ aff.GO/ daINVIARE', ''))
        cfg_installed = safe_str(row.get('CFG.  DEF. INST.', ''))

        if cfg_installed and ('INST' in cfg_installed.upper() or 'ok' in cfg_installed.lower()):
            return 'completed'
        if 'INVIATA' in cfg_def_status.upper():
            return 'in_progress'
        if 'aff.GO' in cfg_def_status:
            return 'in_progress'
        return 'pending'

    elif stage == 'connection':
        utc_interface = safe_str(row.get('INST. Inter-faccia UTC', ''))
        if 'INST' in utc_interface.upper():
            return 'completed'
        if 'Inv.' in utc_interface:
            return 'in_progress'
        return 'pending'

    elif stage == 'validation':
        data_verified = safe_str(row.get('VRF DATI su UTC su DL', ''))
        if 'VRF' in data_verified.upper():
            return 'in_progress'
        return 'pending'

    return 'pending'

def merge_all_data(data_dir):
    """Merge all data sources into unified format"""

    print("Loading files...")
    main_file, lotto1, lotto2, semaforica, swarco = load_and_clean_files(data_dir)

    print("Extracting Lotto 1 data...")
    lotto1_dict = extract_lotto1_data(lotto1)

    print("Extracting Lotto 2 data...")
    lotto2_dict = extract_lotto2_data(lotto2)

    print("Extracting Semaforica data...")
    semaforica_dict = extract_semaforica_data(semaforica)

    print("Extracting Swarco data...")
    swarco_dict = extract_swarco_data(swarco)

    # Track all codes
    main_codes = set()
    lotto1_codes = set(lotto1_dict.keys())
    lotto2_codes = set(lotto2_dict.keys())

    intersections = []

    print("Processing main file intersections...")
    for _, row in main_file.iterrows():
        code = safe_int_str(row.get('Codice Impianto'))
        if not code:
            continue

        main_codes.add(code)

        name = safe_str(row.get('Numero-Nome Postazione', ''))
        lotto = safe_str(row.get('Lotto', ''))
        system = safe_str(row.get('Sistema', ''))
        num_radars = safe_int(row.get('N.ro Dispositivi', 0)) or 0

        # Determine current stage and status
        current_stage = determine_stage(row)
        stage_status = determine_stage_status(row, current_stage)

        # Build intersection object
        intersection = {
            'id': code,
            'name': name,
            'lotto': lotto,
            'system': system,  # Tmacs or Omnia
            'num_radars': num_radars,
            'coordinates': None,  # To be geocoded
            'planimetry_file': None,

            # Current stage tracking
            'current_stage': current_stage,
            'stage_status': stage_status,

            # Stage 1: Installation
            'installation': {
                'planimetry_sent': safe_str(row.get('Plan. e Cfg Inviate', '')).upper() == 'SI',
                'devices_installed': safe_str(row.get('Disp. Inst. o Cavidotti Bloccati', '')),
                'devices_to_install': safe_int(row.get('Disp.  DA  INST.', 0)),
                'blocked_conduits': 'BLOCCATI' in safe_str(row.get('Disp. Inst. o Cavidotti Bloccati', '')).upper(),
                'blocked_solution': safe_str(row.get('Soluzione Cavidotti Bloccati', '')),
            },

            # Stage 2: Configuration
            'configuration': {
                'status': safe_str(row.get('CFG. DEF. DaFare/ aff.GO/ daINVIARE', '')),
                'installed': safe_str(row.get('CFG.  DEF. INST.', '')),
                'aut_status': safe_str(row.get('da CENTR. con Sistema? Da installare AUT ?', '')),
            },

            # Stage 3: Connection
            'connection': {
                'utc_table': safe_str(row.get('Tabella per  IF UTC', '')),
                'utc_interface': safe_str(row.get('INST. Inter-faccia UTC', '')),
            },

            # Stage 4: Validation
            'validation': {
                'data_verified': safe_str(row.get('VRF DATI su UTC su DL', '')),
            },

            # Notes
            'notes': safe_str(row.get('Note', '')),

            # Data sources and inconsistencies
            'data_sources': ['main'],
            'inconsistencies': [],

            # Detailed data from other sources
            'lotto_data': None,
            'central_system_data': None,

            # Radars (individual)
            'radars': [],

            # History
            'history': [],

            # Metadata
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
        }

        # Enrich with Lotto 1 data
        if code in lotto1_dict:
            intersection['data_sources'].append('lotto1')
            intersection['lotto_data'] = lotto1_dict[code]

            # Check for radar count inconsistency
            if lotto1_dict[code]['num_radars'] and lotto1_dict[code]['num_radars'] != num_radars:
                intersection['inconsistencies'].append({
                    'type': 'radar_count_mismatch',
                    'field': 'num_radars',
                    'main_value': num_radars,
                    'lotto_value': lotto1_dict[code]['num_radars'],
                    'source': 'lotto1'
                })

            # Add individual radar info
            if lotto1_dict[code]['sensors']:
                for i, sensor_id in enumerate(lotto1_dict[code]['sensors']):
                    intersection['radars'].append({
                        'id': sensor_id,
                        'position': i + 1,
                        'status': 'installed' if lotto1_dict[code]['completion_date'] else 'pending'
                    })

        # Enrich with Lotto 2 data
        if code in lotto2_dict:
            intersection['data_sources'].append('lotto2')
            intersection['lotto_data'] = lotto2_dict[code]

            # Check for radar count inconsistency
            if lotto2_dict[code]['num_radars'] and lotto2_dict[code]['num_radars'] != num_radars:
                intersection['inconsistencies'].append({
                    'type': 'radar_count_mismatch',
                    'field': 'num_radars',
                    'main_value': num_radars,
                    'lotto_value': lotto2_dict[code]['num_radars'],
                    'source': 'lotto2'
                })

        # Enrich with Semaforica data (for Tmacs systems)
        if code in semaforica_dict:
            intersection['data_sources'].append('semaforica')
            intersection['central_system_data'] = semaforica_dict[code]

        # Enrich with Swarco data (for Omnia systems)
        if code in swarco_dict:
            intersection['data_sources'].append('swarco')
            intersection['central_system_data'] = swarco_dict[code]

        # Flag if missing from Lotto files
        if code not in lotto1_codes and code not in lotto2_codes:
            intersection['inconsistencies'].append({
                'type': 'missing_from_lotto',
                'message': 'Not found in any Lotto file - may be a new addition'
            })

        intersections.append(intersection)

    # Add Lotto 1 intersections not in main file
    print("Adding extra Lotto 1 intersections...")
    extra_lotto1_codes = lotto1_codes - main_codes

    for code in extra_lotto1_codes:
        data = lotto1_dict[code]

        intersection = {
            'id': code,
            'name': data['name'],
            'lotto': 'M9.1',
            'system': data['system'] if data['system'] else 'Unknown',
            'num_radars': data['num_radars'] or len(data['sensors']),
            'coordinates': None,
            'planimetry_file': None,

            'current_stage': 'installation',
            'stage_status': 'in_progress' if data['completion_date'] else 'pending',

            'installation': {
                'planimetry_sent': data['planimetry_sent'].upper() == 'SI' if data['planimetry_sent'] else False,
                'devices_installed': '',
                'devices_to_install': 0,
                'blocked_conduits': False,
                'blocked_solution': '',
            },

            'configuration': {
                'status': '',
                'installed': '',
                'aut_status': '',
            },

            'connection': {
                'utc_table': '',
                'utc_interface': '',
            },

            'validation': {
                'data_verified': '',
            },

            'notes': '',

            'data_sources': ['lotto1'],
            'inconsistencies': [{
                'type': 'missing_from_main',
                'message': 'Found in Lotto 1 file but not in main tracking file'
            }],

            'lotto_data': data,
            'central_system_data': semaforica_dict.get(code) or swarco_dict.get(code),

            'radars': [{'id': s, 'position': i+1, 'status': 'installed' if data['completion_date'] else 'pending'}
                      for i, s in enumerate(data['sensors'])],

            'history': [],
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
        }

        intersections.append(intersection)

    print(f"Total intersections: {len(intersections)}")

    # Count inconsistencies
    total_inconsistencies = sum(len(i['inconsistencies']) for i in intersections)
    print(f"Total inconsistencies flagged: {total_inconsistencies}")

    return intersections

def generate_summary(intersections):
    """Generate summary statistics"""

    summary = {
        'total_intersections': len(intersections),
        'total_radars': sum(i['num_radars'] for i in intersections),
        'by_lotto': {},
        'by_system': {},
        'by_stage': {},
        'by_stage_status': {},
        'inconsistencies': {
            'total': 0,
            'by_type': {}
        }
    }

    for intersection in intersections:
        # By Lotto
        lotto = intersection['lotto'] or 'Unknown'
        if lotto not in summary['by_lotto']:
            summary['by_lotto'][lotto] = {'intersections': 0, 'radars': 0}
        summary['by_lotto'][lotto]['intersections'] += 1
        summary['by_lotto'][lotto]['radars'] += intersection['num_radars']

        # By System
        system = intersection['system'] or 'Unknown'
        if system not in summary['by_system']:
            summary['by_system'][system] = {'intersections': 0, 'radars': 0}
        summary['by_system'][system]['intersections'] += 1
        summary['by_system'][system]['radars'] += intersection['num_radars']

        # By Stage
        stage = intersection['current_stage']
        if stage not in summary['by_stage']:
            summary['by_stage'][stage] = 0
        summary['by_stage'][stage] += 1

        # By Stage Status
        status_key = f"{stage}_{intersection['stage_status']}"
        if status_key not in summary['by_stage_status']:
            summary['by_stage_status'][status_key] = 0
        summary['by_stage_status'][status_key] += 1

        # Inconsistencies
        for inc in intersection['inconsistencies']:
            summary['inconsistencies']['total'] += 1
            inc_type = inc['type']
            if inc_type not in summary['inconsistencies']['by_type']:
                summary['inconsistencies']['by_type'][inc_type] = 0
            summary['inconsistencies']['by_type'][inc_type] += 1

    return summary

def main():
    data_dir = Path(__file__).parent.parent / "data-import"
    output_dir = Path(__file__).parent.parent / "data"
    output_dir.mkdir(exist_ok=True)

    # Merge all data
    intersections = merge_all_data(data_dir)

    # Generate summary
    summary = generate_summary(intersections)

    # Save intersections
    with open(output_dir / "intersections.json", 'w', encoding='utf-8') as f:
        json.dump(intersections, f, ensure_ascii=False, indent=2)
    print(f"Saved {len(intersections)} intersections to data/intersections.json")

    # Save summary
    with open(output_dir / "summary.json", 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    print(f"Saved summary to data/summary.json")

    # Print summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Total intersections: {summary['total_intersections']}")
    print(f"Total radars: {summary['total_radars']}")
    print(f"\nBy Lotto:")
    for lotto, data in summary['by_lotto'].items():
        print(f"  {lotto}: {data['intersections']} intersections, {data['radars']} radars")
    print(f"\nBy Stage:")
    for stage, count in summary['by_stage'].items():
        print(f"  {stage}: {count}")
    print(f"\nInconsistencies: {summary['inconsistencies']['total']}")
    for inc_type, count in summary['inconsistencies']['by_type'].items():
        print(f"  {inc_type}: {count}")

if __name__ == "__main__":
    main()
