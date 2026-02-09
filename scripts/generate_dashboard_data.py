#!/usr/bin/env python3
"""
Generate embedded-data.js for the dashboard from the intersection status analysis.
Converts status values to dashboard format and creates the JavaScript file.
Includes ALL fields from Excel for detailed editing.
"""

import pandas as pd
import json
import os
from datetime import datetime

DATA_DIR = '/home/user/Configurazioni-Radar/data-import'
OUTPUT_DIR = '/home/user/Configurazioni-Radar/js'

# Status mapping from our analysis to dashboard format
INST_STATUS_MAP = {
    'COMPLETE': 'completed',
    'IN_PROGRESS': 'in_progress',
    'STARTED': 'in_progress',
    'BLOCKED': 'blocked',
    'PARTIAL': 'in_progress',
    'NO_DATA': 'not_started',
    'NOT_STARTED': 'not_started',
    'UNKNOWN': 'not_started'
}

CFG_STATUS_MAP = {
    'COMPLETE': 'completed',
    'READY_FOR_APPROVAL': 'in_progress',
    'PENDING_VERIFICATION': 'in_progress',
    'ASSIGNED': 'in_progress',
    'SENT': 'in_progress',
    'READY_TO_SEND': 'in_progress',
    'NOT_STARTED': 'not_started',
    'UNKNOWN': 'not_started'
}

CONN_STATUS_MAP = {
    'IN_PROGRESS': 'in_progress',
    'BLOCKED': 'blocked',
    'MISSING_DATA': 'not_started',
    'NO_INFO': 'not_started',
    'NOT_STARTED': 'not_started',
    'UNKNOWN': 'not_started'
}

VAL_STATUS_MAP = {
    'IN_VERIFICATION': 'in_progress',
    'NOT_STARTED': 'not_started',
    'UNKNOWN': 'not_started'
}

def convert_value(val):
    """Convert pandas values to JSON-safe format"""
    if pd.isna(val):
        return None
    if isinstance(val, (pd.Timestamp, datetime)):
        return val.strftime('%Y-%m-%d')
    if isinstance(val, float):
        if val == int(val):
            return int(val)
        return val
    return str(val).strip() if val else None

def safe_str(val):
    if pd.isna(val):
        return None
    return str(val).strip() if val else None

def safe_int(val):
    if pd.isna(val):
        return 0
    try:
        return int(float(val))
    except:
        return 0

def determine_overall_status(inst, cfg, conn, val):
    """Determine overall status based on 4 stages"""
    if 'blocked' in [inst, cfg, conn, val]:
        return 'blocked'
    if all(s == 'completed' for s in [inst, cfg, conn, val]):
        return 'fully_working'
    if 'in_progress' in [inst, cfg, conn, val]:
        return 'in_progress'
    return 'not_started'

def main():
    print("Loading data...")

    # Load the final status table
    status_df = pd.read_excel(os.path.join(DATA_DIR, 'INTERSECTION_STATUS_FINAL.xlsx'),
                              sheet_name='All Intersections')

    # Load the master report with ALL fields
    master_df = pd.read_excel(os.path.join(DATA_DIR, 'MASTER_INTERSECTION_REPORT_CLEAN.xlsx'),
                              sheet_name='All Intersections')

    # Create status lookup by code
    status_lookup = {}
    for _, row in status_df.iterrows():
        code = safe_str(row.get('CODE'))
        if code:
            status_lookup[code] = row

    print(f"Processing {len(master_df)} intersections with full details...")

    intersections = []
    summary = {
        'total_intersections': 0,
        'total_radars': 0,
        'fully_working': 0,
        'by_lotto': {},
        'by_system': {},
        'by_stage': {
            'installation': {'completed': 0, 'in_progress': 0, 'blocked': 0, 'not_started': 0},
            'configuration': {'completed': 0, 'in_progress': 0, 'blocked': 0, 'not_started': 0},
            'connection': {'completed': 0, 'in_progress': 0, 'blocked': 0, 'not_started': 0},
            'validation': {'completed': 0, 'in_progress': 0, 'blocked': 0, 'not_started': 0}
        }
    }

    for _, master_row in master_df.iterrows():
        code = safe_str(master_row.get('POSTAZIONE_CODE'))
        if not code:
            continue

        name = safe_str(master_row.get('POSTAZIONE_NAME'))
        lotto = safe_str(master_row.get('LOTTO'))
        sistema = safe_str(master_row.get('SISTEMA'))
        n_disp = safe_int(master_row.get('N_DISPOSITIVI'))
        codice_imp = convert_value(master_row.get('CODICE_IMPIANTO'))

        # Get status from status table
        status_row = status_lookup.get(code, {})
        inst_status_raw = safe_str(status_row.get('INST_STATUS')) if hasattr(status_row, 'get') else 'NOT_STARTED'
        cfg_status_raw = safe_str(status_row.get('CFG_STATUS')) if hasattr(status_row, 'get') else 'NOT_STARTED'
        conn_status_raw = safe_str(status_row.get('CONN_STATUS')) if hasattr(status_row, 'get') else 'NOT_STARTED'
        val_status_raw = safe_str(status_row.get('VAL_STATUS')) if hasattr(status_row, 'get') else 'NOT_STARTED'

        inst_status = INST_STATUS_MAP.get(inst_status_raw or 'NOT_STARTED', 'not_started')
        cfg_status = CFG_STATUS_MAP.get(cfg_status_raw or 'NOT_STARTED', 'not_started')
        conn_status = CONN_STATUS_MAP.get(conn_status_raw or 'NOT_STARTED', 'not_started')
        val_status = VAL_STATUS_MAP.get(val_status_raw or 'NOT_STARTED', 'not_started')

        overall = determine_overall_status(inst_status, cfg_status, conn_status, val_status)

        # Build intersection with ALL fields from master report
        intersection = {
            'id': code,
            'name': f"{code}-{name}",
            'lotto': lotto,
            'system': sistema,
            'codice_impianto': codice_imp,
            'num_radars': n_disp,

            # Installation stage - ALL fields
            'installation': {
                'status': inst_status,
                'status_detail': inst_status_raw,
                'blocked_conduits': inst_status_raw == 'BLOCKED',
                # L1 fields (Lotto 1)
                'l1_match': convert_value(master_row.get('L1_MATCH')),
                'l1_planimetrie': convert_value(master_row.get('L1_PLANIMETRIE')),
                'l1_passaggio_cavi': convert_value(master_row.get('L1_PASSAGGIO_CAVI')),
                'l1_install_sensori': convert_value(master_row.get('L1_INSTALL_SENSORI')),
                'l1_cablaggio': convert_value(master_row.get('L1_CABLAGGIO')),
                'l1_screenshot': convert_value(master_row.get('L1_SCREENSHOT')),
                'l1_completato': convert_value(master_row.get('L1_COMPLETATO')),
                'l1_doc_inviata': convert_value(master_row.get('L1_DOC_INVIATA')),
                'l1_data_compl': convert_value(master_row.get('L1_DATA_COMPL')),
                # L2 fields (Lotto 2)
                'l2_match': convert_value(master_row.get('L2_MATCH')),
                'l2_data_installaz': convert_value(master_row.get('L2_DATA_INSTALLAZ')),
                'l2_config_rsm': convert_value(master_row.get('L2_CONFIG_RSM')),
                'l2_config_instal': convert_value(master_row.get('L2_CONFIG_INSTAL')),
                'l2_planimetria': convert_value(master_row.get('L2_PLANIMETRIA')),
                'l2_n_radar_finiti': convert_value(master_row.get('L2_N_RADAR_FINITI')),
                'l2_centralizzati': convert_value(master_row.get('L2_CENTRALIZZATI')),
                # Blocking info
                'disp_inst_bloccati': convert_value(master_row.get('DISP_INST_BLOCCATI')),
                'disp_da_inst': convert_value(master_row.get('DISP_DA_INST')),
                'soluzione_bloccati': convert_value(master_row.get('SOLUZIONE_BLOCCATI')),
            },

            # Configuration stage - ALL fields
            'configuration': {
                'status': cfg_status,
                'status_detail': cfg_status_raw,
                'plan_cfg_inviate': convert_value(master_row.get('PLAN_CFG_INVIATE')),
                'cfg_def_status': convert_value(master_row.get('CFG_DEF_STATUS')),
                'cfg_def_inst': convert_value(master_row.get('CFG_DEF_INST')),
            },

            # Connection stage - ALL fields
            'connection': {
                'status': conn_status,
                'status_detail': conn_status_raw,
                'da_centr_aut': convert_value(master_row.get('DA_CENTR_AUT')),
                'tabella_if_utc': convert_value(master_row.get('TABELLA_IF_UTC')),
                'inst_interfaccia_utc': convert_value(master_row.get('INST_INTERFACCIA_UTC')),
                # SWARCO/Omnia fields
                'swarco_spot_status': convert_value(master_row.get('SWARCO_SPOT_STATUS')),
                'swarco_spot_firmware': convert_value(master_row.get('SWARCO_SPOT_FIRMWARE')),
                # Semaforica/Tmacs fields
                'sema_aut': convert_value(master_row.get('SEMA_AUT')),
                'sema_attivita': convert_value(master_row.get('SEMA_ATTIVITA')),
            },

            # Validation stage - ALL fields
            'validation': {
                'status': val_status,
                'status_detail': val_status_raw,
                'vrf_dati': convert_value(master_row.get('VRF_DATI')),
            },

            # General fields
            'note_main': convert_value(master_row.get('NOTE_MAIN')),
            'overall_status': overall,
            'coordinates': None,
            'coordinates_manual': False,
            'inconsistencies': [],
            'notes': None,
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }

        intersections.append(intersection)

        # Update summary
        summary['total_intersections'] += 1
        summary['total_radars'] += n_disp

        if overall == 'fully_working':
            summary['fully_working'] += 1

        if lotto:
            if lotto not in summary['by_lotto']:
                summary['by_lotto'][lotto] = {'intersections': 0, 'radars': 0}
            summary['by_lotto'][lotto]['intersections'] += 1
            summary['by_lotto'][lotto]['radars'] += n_disp

        if sistema:
            if sistema not in summary['by_system']:
                summary['by_system'][sistema] = {'intersections': 0, 'radars': 0}
            summary['by_system'][sistema]['intersections'] += 1
            summary['by_system'][sistema]['radars'] += n_disp

        summary['by_stage']['installation'][inst_status] += 1
        summary['by_stage']['configuration'][cfg_status] += 1
        summary['by_stage']['connection'][conn_status] += 1
        summary['by_stage']['validation'][val_status] += 1

    # Generate JavaScript file
    output_path = os.path.join(OUTPUT_DIR, 'embedded-data.js')

    js_content = f"""/**
 * Embedded Data - Generated from intersection status analysis
 * Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
 * Total intersections: {len(intersections)}
 * Includes ALL fields from Excel for editing
 */

const EMBEDDED_DATA = {{
    intersections: {json.dumps(intersections, ensure_ascii=False, indent=2)},
    summary: {json.dumps(summary, ensure_ascii=False, indent=2)}
}};
"""

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(js_content)

    print(f"\nGenerated: {output_path}")
    print(f"Total intersections: {summary['total_intersections']}")
    print(f"Total radars: {summary['total_radars']}")

    print("\nBy Stage Status:")
    for stage, counts in summary['by_stage'].items():
        print(f"  {stage.capitalize()}:")
        for status, count in counts.items():
            print(f"    {status}: {count}")

if __name__ == '__main__':
    main()
