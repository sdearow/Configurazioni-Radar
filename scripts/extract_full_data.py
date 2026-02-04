#!/usr/bin/env python3
"""
Comprehensive Data Extractor for Radar Project Management
Extracts all substage data from Excel files and creates a unified data model.
"""

import pandas as pd
import json
import re
from pathlib import Path
from datetime import datetime

# File paths
DATA_DIR = Path(__file__).parent.parent / "data-import"
OUTPUT_DIR = Path(__file__).parent.parent / "data"

# Main tracking file columns mapping
MAIN_COLUMNS = {
    'progr': 'Progr.',
    'lotto': 'Lotto',
    'position_type': 'Postazione in OdS \no Nuova',
    'name': 'Numero-Nome Postazione',
    'code': 'Codice\nImpianto',
    'central': 'Centr',
    'system': 'Sistema',
    'aut_to_install': 'da CENTR. con Sistema?\nDa installare AUT ?',
    'plan_cfg_sent': 'Plan. e Cfg\nInviate',
    'num_devices': 'N.ro Dispositivi',
    'config_status': 'CFG. DEF. DaFare/\naff.GO/ daINVIARE',
    'config_installed': 'CFG. \nDEF. INST.',
    'utc_table': 'Tabella\nper \nIF UTC',
    'utc_interface': 'INST.\nInter-faccia UTC',
    'data_verified': 'VRF\nDATI\nsu UTC\nsu DL',
    'notes': 'Note',
    'devices_blocked': 'Disp. Inst. o Cavidotti Bloccati',
    'devices_to_install': 'Disp. \nDA \nINST.',
    'blocked_solution': 'Soluzione Cavidotti Bloccati'
}

# Lotto 1 columns (detailed installation info)
LOTTO1_COLUMNS = {
    'n': 'N.',
    'id': 'ID',
    'code': 'cod.',
    'name': 'Impianto',
    'system': 'sistema',
    'odl': 'ODL',
    'installation': 'installazione',
    'planimetry_received': 'planimetrie ricevute',
    'cable_passage': 'passaggio cavi',
    'planimetry_sent_rsm': 'planimetria scavi inviata a RSM',
    'sensor_installation': 'installazione sensori',
    'regulator_wiring': 'cablaggio regolatore',
    'screenshot': 'Screenshoot',
    'completed': 'completato',
    'documentation_sent': 'Documentazione inviata',
    'completion_date': 'data completamento'
}

# Lotto 2 columns
LOTTO2_COLUMNS = {
    'n': 'N.progr.',
    'code': 'codice',
    'name': 'indirizzo',
    'sidewalk_excavation': 'scavo marciapiede',
    'road_excavation': 'scavo carreggiata',
    'cable_meters': 'm.cavo',
    'interface': 'interfaccia',
    'work_order': 'ordine di lavoro',
    'num_radars': 'numero radar',
    'installation_date': 'data installaz',
    'config_rsm': 'config.RSM',
    'config_installed': 'Config.instal.',
    'to_excavate': 'da scavare',
    'planimetry': 'planimetria',
    'sap_order': 'ordine sap',
    'radars_no_cables': 'n.radar montati senza cavi',
    'radars_no_connection': 'n.radar montati con cavi senza collegamento',
    'radars_finished': 'n.radar finiti',
    'centralized': 'centralizzati',
    'missing_sim': 'manca SIM',
    'serials': 'seriali'
}

# Swarco columns (connection info)
SWARCO_COLUMNS = {
    'progr': 'Progr.',
    'lotto': 'Lotto',
    'name': 'Numero-Nome Postazione',
    'code': 'Codice\nImpianto',
    'system': 'Sistema',
    'scae_panel': 'Centralino\nSCAE',
    'spot_present': 'Centralizzati recenti: \nSPOT presente?\nNo SIM? ',
    'spot_status': 'SPOT:\nSu scheda (centralino SCAE)?\nCon firmware vecchio (da sostituire)?\nCon firmware recente (aggiornabile da remoto)?'
}

# Semaforica columns (AUT status)
SEMAFORICA_COLUMNS = {
    'progr': 'Progr.',
    'lotto': 'Lotto',
    'name': 'Numero-Nome Postazione',
    'code': 'Codice\nImpianto',
    'system': 'Sistema',
    'aut_status': 'AUT',
    'aut_action': "ATTIVITA' DA FARE"
}


def clean_value(val):
    """Clean and normalize a value."""
    if pd.isna(val):
        return None
    if isinstance(val, str):
        val = val.strip()
        if val.lower() in ['', 'nan', 'none', '-']:
            return None
    return val


def extract_code(name_or_code):
    """Extract numeric code from name or code field."""
    if pd.isna(name_or_code):
        return None
    s = str(name_or_code)
    # Try to find a 5-digit code
    match = re.search(r'\b(\d{5})\b', s)
    if match:
        return match.group(1)
    # Try to find any number
    match = re.search(r'(\d+)', s)
    if match:
        return match.group(1)
    return None


def determine_installation_status(data):
    """
    Determine installation status based on substage data.
    Returns: 'completed', 'in_progress', 'blocked', 'not_started'
    """
    # Check for blocked status
    blocked = data.get('blocked_conduits') or data.get('devices_blocked')
    if blocked and str(blocked).upper() not in ['NO', 'FALSE', '0', '']:
        return 'blocked'

    # Check for completion
    completion_date = data.get('completion_date')
    completed = data.get('completed')
    if completion_date or (completed and str(completed).upper() in ['SI', 'YES', 'OK', 'X', '1']):
        return 'completed'

    # Check for in-progress indicators
    sensor_install = data.get('sensor_installation')
    cable_passage = data.get('cable_passage')
    regulator_wiring = data.get('regulator_wiring')

    has_progress = any([
        sensor_install and str(sensor_install).strip() not in ['', '-'],
        cable_passage and str(cable_passage).strip() not in ['', '-'],
        regulator_wiring and str(regulator_wiring).strip() not in ['', '-']
    ])

    if has_progress:
        return 'in_progress'

    # Check if planimetry received (first step started)
    planimetry = data.get('planimetry_received') or data.get('plan_cfg_sent')
    if planimetry and str(planimetry).strip() not in ['', '-', 'NO']:
        return 'in_progress'

    return 'not_started'


def determine_configuration_status(data):
    """
    Determine configuration status.
    Returns: 'completed', 'in_progress', 'blocked', 'not_started'
    """
    config_installed = data.get('config_installed')
    config_status = data.get('config_status')

    # Check if configuration is installed
    if config_installed and str(config_installed).upper() in ['SI', 'YES', 'OK', 'X', '1', 'FATTO']:
        return 'completed'

    # Check configuration status field
    if config_status:
        status_str = str(config_status).upper()
        if 'GO' in status_str or 'FATTO' in status_str or 'OK' in status_str:
            return 'completed'
        elif 'DAFARE' in status_str or 'DA FARE' in status_str:
            return 'in_progress'
        elif 'INVIARE' in status_str:
            return 'in_progress'

    return 'not_started'


def determine_connection_status(data):
    """
    Determine connection status based on SPOT/AUT and UTC interface.
    Returns: 'completed', 'in_progress', 'blocked', 'not_started'
    """
    utc_interface = data.get('utc_interface')
    spot_status = data.get('spot_status')
    aut_status = data.get('aut_status')

    # Check UTC interface
    if utc_interface and str(utc_interface).upper() in ['SI', 'YES', 'OK', 'X', '1']:
        return 'completed'

    # Check SPOT status for issues
    if spot_status:
        spot_str = str(spot_status).lower()
        if 'firmware vecchio' in spot_str or 'sostituire' in spot_str:
            return 'blocked'
        elif 'firmware recente' in spot_str or 'aggiornabile' in spot_str:
            return 'in_progress'
        elif 'scheda' in spot_str:
            return 'in_progress'

    # Check AUT status
    if aut_status:
        aut_str = str(aut_status).upper()
        if aut_str in ['OK', 'SI', 'YES', 'AUT']:
            return 'in_progress'  # AUT OK but need full connection check

    # Check if UTC table exists (step before interface)
    utc_table = data.get('utc_table')
    if utc_table and str(utc_table).strip() not in ['', '-', 'NO']:
        return 'in_progress'

    return 'not_started'


def determine_validation_status(data):
    """
    Determine validation status.
    Returns: 'completed', 'in_progress', 'blocked', 'not_started'
    """
    data_verified = data.get('data_verified')

    if data_verified:
        verified_str = str(data_verified).upper()
        if verified_str in ['SI', 'YES', 'OK', 'X', '1', 'VERIFICATO']:
            return 'completed'
        elif verified_str not in ['', '-', 'NO']:
            return 'in_progress'

    return 'not_started'


def load_main_file():
    """Load the main tracking file."""
    file_path = DATA_DIR / "LOTTI M9_RADAR_v1_2026.01.28.xlsx"
    df = pd.read_excel(file_path, sheet_name='INST.FIN. LOTTI')

    intersections = {}
    for _, row in df.iterrows():
        code = clean_value(row.get(MAIN_COLUMNS['code']))
        if not code:
            continue

        code = str(code).strip()
        name = clean_value(row.get(MAIN_COLUMNS['name'])) or ''

        intersections[code] = {
            'id': code,
            'name': name,
            'lotto': clean_value(row.get(MAIN_COLUMNS['lotto'])),
            'system': clean_value(row.get(MAIN_COLUMNS['system'])),
            'position_type': clean_value(row.get(MAIN_COLUMNS['position_type'])),
            'num_radars': clean_value(row.get(MAIN_COLUMNS['num_devices'])) or 0,

            # Installation substages
            'installation': {
                'planimetry_sent': clean_value(row.get(MAIN_COLUMNS['plan_cfg_sent'])),
                'devices_installed': clean_value(row.get(MAIN_COLUMNS['devices_blocked'])),
                'devices_to_install': clean_value(row.get(MAIN_COLUMNS['devices_to_install'])),
                'blocked_conduits': bool(clean_value(row.get(MAIN_COLUMNS['devices_blocked'])) and
                                        'BLOCC' in str(row.get(MAIN_COLUMNS['devices_blocked'], '')).upper()),
                'blocked_solution': clean_value(row.get(MAIN_COLUMNS['blocked_solution'])),
                # Will be enriched from Lotto files
                'planimetry_received': None,
                'cable_passage': None,
                'planimetry_sent_rsm': None,
                'sensor_installation': None,
                'regulator_wiring': None,
                'screenshot': None,
                'completed': None,
                'documentation_sent': None,
                'completion_date': None,
                'status': 'not_started'
            },

            # Configuration substages
            'configuration': {
                'config_sent': clean_value(row.get(MAIN_COLUMNS['plan_cfg_sent'])),
                'config_status': clean_value(row.get(MAIN_COLUMNS['config_status'])),
                'config_installed': clean_value(row.get(MAIN_COLUMNS['config_installed'])),
                'base_config': None,  # Configurazione base
                'definitive_config': None,  # Configurazione definitiva
                'definitive_config_status': None,  # Assegnata, Da Verificare, Implementata
                'status': 'not_started'
            },

            # Connection substages
            'connection': {
                'utc_table': clean_value(row.get(MAIN_COLUMNS['utc_table'])),
                'utc_interface': clean_value(row.get(MAIN_COLUMNS['utc_interface'])),
                'utc_table_sent': None,
                'utc_interface_configured': None,
                'spot_status': None,
                'spot_on_board': None,
                'spot_firmware': None,
                'aut_status': None,
                'scae_panel': None,
                'status': 'not_started'
            },

            # Validation substages
            'validation': {
                'data_verified': clean_value(row.get(MAIN_COLUMNS['data_verified'])),
                'sending_to_datalake': None,
                'traffic_data_verified': None,
                'visum_optima_interface': None,
                'status': 'not_started'
            },

            'aut_to_install': clean_value(row.get(MAIN_COLUMNS['aut_to_install'])),
            'notes': clean_value(row.get(MAIN_COLUMNS['notes'])),
            'radars': [],
            'files': {
                'planimetry': None,
                'photos': []
            },
            'data_sources': ['main'],
            'inconsistencies': [],
            'coordinates': None,
            'coordinates_manual': False,
            'geocode_confidence': None
        }

    return intersections


def enrich_from_lotto1(intersections):
    """Enrich data from Lotto 1 file (detailed installation info)."""
    file_path = DATA_DIR / "ELENCO_LOTTO_1_2026.01.23.xlsx"

    # Try 'finale' sheet first, then 'Sheet1'
    try:
        df = pd.read_excel(file_path, sheet_name='finale')
    except:
        df = pd.read_excel(file_path, sheet_name='Sheet1')

    for _, row in df.iterrows():
        code = clean_value(row.get('cod.'))
        if not code:
            continue
        code = str(code).strip()

        if code not in intersections:
            # New intersection from Lotto 1
            name = clean_value(row.get('Impianto')) or ''
            intersections[code] = create_empty_intersection(code, name, 'M9.1')

        inst = intersections[code]
        if 'lotto1' not in inst['data_sources']:
            inst['data_sources'].append('lotto1')

        # Update installation substages
        installation = inst['installation']
        installation['planimetry_received'] = clean_value(row.get('planimetrie ricevute'))
        installation['cable_passage'] = clean_value(row.get('passaggio cavi'))
        installation['planimetry_sent_rsm'] = clean_value(row.get('planimetria scavi inviata a RSM')) or \
                                               clean_value(row.get('planimetria inviata a RSM'))
        installation['sensor_installation'] = clean_value(row.get('installazione sensori'))
        installation['regulator_wiring'] = clean_value(row.get('cablaggio regolatore'))
        installation['screenshot'] = clean_value(row.get('Screenshoot'))
        installation['completed'] = clean_value(row.get('completato'))
        installation['documentation_sent'] = clean_value(row.get('Documentazione inviata'))
        installation['completion_date'] = clean_value(row.get('data completamento'))

        # Extract radar info
        radars = []
        for i in range(1, 8):
            radar_id = clean_value(row.get(f'UMR {i}')) or clean_value(row.get(f'ID sensore {i}'))
            if radar_id:
                ip = clean_value(row.get(f'IP{"" if i == 1 else "." + str(i-1)}'))
                position = clean_value(row.get(f'POSIZIONE{"" if i == 1 else "." + str(i-1)}'))
                radars.append({
                    'id': radar_id,
                    'ip': ip,
                    'position': position,
                    'status': 'installed' if radar_id else 'pending'
                })

        if radars:
            inst['radars'] = radars
            # Update radar count if more specific
            if len(radars) > 0:
                inst['lotto1_radar_count'] = len(radars)

    return intersections


def enrich_from_lotto2(intersections):
    """Enrich data from Lotto 2 file."""
    file_path = DATA_DIR / "ELENCO LOTTO 2_2026.01.23.xlsx"
    df = pd.read_excel(file_path, sheet_name='Foglio1')

    for _, row in df.iterrows():
        code = clean_value(row.get('codice'))
        if not code:
            continue
        code = str(code).strip()

        if code not in intersections:
            name = clean_value(row.get('indirizzo')) or ''
            intersections[code] = create_empty_intersection(code, name, 'M9.2')

        inst = intersections[code]
        if 'lotto2' not in inst['data_sources']:
            inst['data_sources'].append('lotto2')

        # Update installation substages specific to Lotto 2
        installation = inst['installation']
        installation['sidewalk_excavation'] = clean_value(row.get('scavo marciapiede'))
        installation['road_excavation'] = clean_value(row.get('scavo carreggiata'))
        installation['cable_meters'] = clean_value(row.get('m.cavo'))
        installation['to_excavate'] = clean_value(row.get('da scavare'))
        installation['completion_date'] = clean_value(row.get('data installaz'))
        installation['radars_no_cables'] = clean_value(row.get('n.radar montati senza cavi'))
        installation['radars_no_connection'] = clean_value(row.get('n.radar montati con cavi senza collegamento'))
        installation['radars_finished'] = clean_value(row.get('n.radar finiti'))
        installation['planimetry_received'] = clean_value(row.get('planimetria'))

        # Configuration
        inst['configuration']['config_rsm'] = clean_value(row.get('config.RSM'))
        inst['configuration']['config_installed'] = clean_value(row.get('Config.instal.'))

        # Connection
        inst['connection']['centralized'] = clean_value(row.get('centralizzati'))
        inst['connection']['missing_sim'] = clean_value(row.get('manca SIM'))

        # Radar serials
        serials = clean_value(row.get('seriali'))
        if serials:
            inst['radar_serials'] = serials

        # Lotto 2 specific radar count
        num_radars = clean_value(row.get('numero radar'))
        if num_radars:
            inst['lotto2_radar_count'] = num_radars

    return intersections


def enrich_from_swarco(intersections):
    """Enrich connection data from Swarco file (Omnia systems)."""
    file_path = DATA_DIR / "Swarco_Verifica stato - TOT_2026.01.29.xlsx"
    df = pd.read_excel(file_path, sheet_name='Foglio1')

    for _, row in df.iterrows():
        code = clean_value(row.get(SWARCO_COLUMNS['code']))
        if not code:
            continue
        code = str(code).strip()

        if code not in intersections:
            name = clean_value(row.get(SWARCO_COLUMNS['name'])) or ''
            lotto = clean_value(row.get(SWARCO_COLUMNS['lotto']))
            intersections[code] = create_empty_intersection(code, name, lotto)

        inst = intersections[code]
        if 'swarco' not in inst['data_sources']:
            inst['data_sources'].append('swarco')

        # Update connection substages
        connection = inst['connection']
        connection['scae_panel'] = clean_value(row.get(SWARCO_COLUMNS['scae_panel']))
        connection['spot_present'] = clean_value(row.get(SWARCO_COLUMNS['spot_present']))
        connection['spot_status'] = clean_value(row.get(SWARCO_COLUMNS['spot_status']))

        # Parse SPOT status details
        spot_status = connection['spot_status']
        if spot_status:
            spot_str = str(spot_status).lower()
            if 'scheda' in spot_str:
                connection['spot_on_board'] = True
            if 'firmware vecchio' in spot_str:
                connection['spot_firmware'] = 'old'
            elif 'firmware recente' in spot_str:
                connection['spot_firmware'] = 'recent'

    return intersections


def enrich_from_semaforica(intersections):
    """Enrich connection data from Semaforica file (Tmacs systems)."""
    file_path = DATA_DIR / "Elenco IS RADAR_SEMAFORICA_per VERIFICA STATO AUT.xlsx"
    df = pd.read_excel(file_path, sheet_name='IMPIANTI SEMAFORICA')

    for _, row in df.iterrows():
        code = clean_value(row.get(SEMAFORICA_COLUMNS['code']))
        if not code:
            continue
        code = str(code).strip()

        if code not in intersections:
            name = clean_value(row.get(SEMAFORICA_COLUMNS['name'])) or ''
            lotto = clean_value(row.get(SEMAFORICA_COLUMNS['lotto']))
            intersections[code] = create_empty_intersection(code, name, lotto)

        inst = intersections[code]
        if 'semaforica' not in inst['data_sources']:
            inst['data_sources'].append('semaforica')

        # Update connection substages
        connection = inst['connection']
        connection['aut_status'] = clean_value(row.get(SEMAFORICA_COLUMNS['aut_status']))
        connection['aut_action'] = clean_value(row.get(SEMAFORICA_COLUMNS['aut_action']))

    return intersections


def create_empty_intersection(code, name, lotto):
    """Create an empty intersection structure."""
    return {
        'id': code,
        'name': name,
        'lotto': lotto,
        'system': None,
        'position_type': None,
        'num_radars': 0,

        'installation': {
            'planimetry_sent': None,
            'planimetry_received': None,
            'cable_passage': None,
            'planimetry_sent_rsm': None,
            'sensor_installation': None,
            'regulator_wiring': None,
            'screenshot': None,
            'completed': None,
            'documentation_sent': None,
            'completion_date': None,
            'devices_installed': None,
            'devices_to_install': None,
            'blocked_conduits': False,
            'blocked_solution': None,
            'status': 'not_started'
        },

        'configuration': {
            'config_sent': None,
            'config_status': None,
            'config_installed': None,
            'base_config': None,
            'definitive_config': None,
            'definitive_config_status': None,
            'status': 'not_started'
        },

        'connection': {
            'utc_table': None,
            'utc_interface': None,
            'utc_table_sent': None,
            'utc_interface_configured': None,
            'spot_status': None,
            'spot_on_board': None,
            'spot_firmware': None,
            'aut_status': None,
            'scae_panel': None,
            'status': 'not_started'
        },

        'validation': {
            'data_verified': None,
            'sending_to_datalake': None,
            'traffic_data_verified': None,
            'visum_optima_interface': None,
            'status': 'not_started'
        },

        'aut_to_install': None,
        'notes': None,
        'radars': [],
        'files': {
            'planimetry': None,
            'photos': []
        },
        'data_sources': [],
        'inconsistencies': [],
        'coordinates': None,
        'coordinates_manual': False,
        'geocode_confidence': None
    }


def calculate_statuses(intersections):
    """Calculate status for each stage based on substage data."""
    for code, inst in intersections.items():
        # Combine all relevant data for status calculation
        all_data = {
            **inst.get('installation', {}),
            **inst.get('configuration', {}),
            **inst.get('connection', {}),
            **inst.get('validation', {}),
            'num_radars': inst.get('num_radars', 0)
        }

        # Calculate each stage status
        inst['installation']['status'] = determine_installation_status(all_data)
        inst['configuration']['status'] = determine_configuration_status(all_data)
        inst['connection']['status'] = determine_connection_status(all_data)
        inst['validation']['status'] = determine_validation_status(all_data)

        # Calculate overall status
        statuses = [
            inst['installation']['status'],
            inst['configuration']['status'],
            inst['connection']['status'],
            inst['validation']['status']
        ]

        if all(s == 'completed' for s in statuses):
            inst['overall_status'] = 'fully_working'
        elif any(s == 'blocked' for s in statuses):
            inst['overall_status'] = 'blocked'
        elif any(s == 'in_progress' for s in statuses):
            inst['overall_status'] = 'in_progress'
        else:
            inst['overall_status'] = 'not_started'

    return intersections


def detect_inconsistencies(intersections):
    """Detect data inconsistencies between sources."""
    for code, inst in intersections.items():
        inconsistencies = []

        # Check radar count mismatches
        main_count = inst.get('num_radars', 0)
        lotto1_count = inst.get('lotto1_radar_count')
        lotto2_count = inst.get('lotto2_radar_count')

        if lotto1_count and main_count and int(main_count) != int(lotto1_count):
            inconsistencies.append({
                'type': 'radar_count_mismatch',
                'field': 'num_radars',
                'main_value': main_count,
                'lotto_value': lotto1_count,
                'source': 'lotto1'
            })

        if lotto2_count and main_count and int(main_count) != int(lotto2_count):
            inconsistencies.append({
                'type': 'radar_count_mismatch',
                'field': 'num_radars',
                'main_value': main_count,
                'lotto_value': lotto2_count,
                'source': 'lotto2'
            })

        # Check for missing data
        if not inst.get('coordinates'):
            inconsistencies.append({
                'type': 'missing_coordinates',
                'message': 'Location not geocoded'
            })
        elif inst.get('geocode_confidence') == 'low':
            inconsistencies.append({
                'type': 'geocoding_uncertain',
                'message': 'Location geocoding uncertain - needs review'
            })

        # Check for blocked without solution
        if inst['installation'].get('blocked_conduits') and not inst['installation'].get('blocked_solution'):
            inconsistencies.append({
                'type': 'blocked_no_solution',
                'message': 'Blocked conduits with no solution specified'
            })

        inst['inconsistencies'] = inconsistencies

    return intersections


def calculate_summary(intersections):
    """Calculate summary statistics."""
    total = len(intersections)
    total_radars = sum(int(i.get('num_radars', 0) or 0) for i in intersections.values())

    # Count by status
    status_counts = {
        'fully_working': 0,
        'in_progress': 0,
        'blocked': 0,
        'not_started': 0
    }

    # Count by stage status
    stage_status_counts = {
        'installation': {'completed': 0, 'in_progress': 0, 'blocked': 0, 'not_started': 0},
        'configuration': {'completed': 0, 'in_progress': 0, 'blocked': 0, 'not_started': 0},
        'connection': {'completed': 0, 'in_progress': 0, 'blocked': 0, 'not_started': 0},
        'validation': {'completed': 0, 'in_progress': 0, 'blocked': 0, 'not_started': 0}
    }

    for inst in intersections.values():
        overall = inst.get('overall_status', 'not_started')
        if overall in status_counts:
            status_counts[overall] += 1

        for stage in ['installation', 'configuration', 'connection', 'validation']:
            status = inst.get(stage, {}).get('status', 'not_started')
            if status in stage_status_counts[stage]:
                stage_status_counts[stage][status] += 1

    # Count inconsistencies
    total_inconsistencies = sum(len(i.get('inconsistencies', [])) for i in intersections.values())
    geocoding_issues = sum(1 for i in intersections.values()
                          if any(inc.get('type') in ['missing_coordinates', 'geocoding_uncertain']
                                for inc in i.get('inconsistencies', [])))

    return {
        'total_intersections': total,
        'total_radars': total_radars,
        'fully_working': status_counts['fully_working'],
        'overall_status': status_counts,
        'stage_status': stage_status_counts,
        'total_inconsistencies': total_inconsistencies,
        'geocoding_issues': geocoding_issues,
        'by_lotto': {
            'M9.1': sum(1 for i in intersections.values() if i.get('lotto') == 'M9.1'),
            'M9.2': sum(1 for i in intersections.values() if i.get('lotto') == 'M9.2')
        },
        'by_system': {
            'Omnia': sum(1 for i in intersections.values() if i.get('system') == 'Omnia'),
            'Tmacs': sum(1 for i in intersections.values() if i.get('system') == 'Tmacs')
        }
    }


def main():
    """Main extraction function."""
    print("=" * 60)
    print("RADAR PROJECT DATA EXTRACTION")
    print("=" * 60)

    # Load and merge data
    print("\n1. Loading main tracking file...")
    intersections = load_main_file()
    print(f"   Loaded {len(intersections)} intersections from main file")

    print("\n2. Enriching from Lotto 1...")
    intersections = enrich_from_lotto1(intersections)
    print(f"   Now have {len(intersections)} intersections")

    print("\n3. Enriching from Lotto 2...")
    intersections = enrich_from_lotto2(intersections)
    print(f"   Now have {len(intersections)} intersections")

    print("\n4. Enriching from Swarco (Omnia connection data)...")
    intersections = enrich_from_swarco(intersections)

    print("\n5. Enriching from Semaforica (Tmacs connection data)...")
    intersections = enrich_from_semaforica(intersections)

    print("\n6. Calculating stage statuses...")
    intersections = calculate_statuses(intersections)

    print("\n7. Detecting inconsistencies...")
    intersections = detect_inconsistencies(intersections)

    # Calculate summary
    summary = calculate_summary(intersections)

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Total intersections: {summary['total_intersections']}")
    print(f"Total radars: {summary['total_radars']}")
    print(f"Fully working: {summary['fully_working']}")
    print(f"\nBy overall status:")
    for status, count in summary['overall_status'].items():
        print(f"  {status}: {count}")
    print(f"\nBy stage:")
    for stage, counts in summary['stage_status'].items():
        completed = counts['completed']
        total = sum(counts.values())
        print(f"  {stage}: {completed}/{total} completed")
    print(f"\nData issues: {summary['total_inconsistencies']}")
    print(f"Geocoding issues: {summary['geocoding_issues']}")

    # Save output
    OUTPUT_DIR.mkdir(exist_ok=True)

    # Convert to list and add timestamps
    now = datetime.now().isoformat()
    intersections_list = []
    for inst in intersections.values():
        inst['created_at'] = inst.get('created_at', now)
        inst['updated_at'] = now
        intersections_list.append(inst)

    # Sort by ID
    intersections_list.sort(key=lambda x: x.get('id', ''))

    # Save intersections
    with open(OUTPUT_DIR / 'intersections.json', 'w', encoding='utf-8') as f:
        json.dump(intersections_list, f, ensure_ascii=False, indent=2, default=str)

    # Save summary
    with open(OUTPUT_DIR / 'summary.json', 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print(f"\nSaved to {OUTPUT_DIR / 'intersections.json'}")
    print(f"Saved to {OUTPUT_DIR / 'summary.json'}")

    return intersections_list, summary


if __name__ == "__main__":
    main()
