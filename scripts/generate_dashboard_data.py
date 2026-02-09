#!/usr/bin/env python3
"""
Generate embedded-data.js for the dashboard from the intersection status analysis.
Converts status values to dashboard format and creates the JavaScript file.
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
    # If any stage is blocked, overall is blocked
    if 'blocked' in [inst, cfg, conn, val]:
        return 'blocked'

    # If all stages are completed, overall is completed (fully_working)
    if all(s == 'completed' for s in [inst, cfg, conn, val]):
        return 'fully_working'

    # If any stage is in progress, overall is in progress
    if 'in_progress' in [inst, cfg, conn, val]:
        return 'in_progress'

    # Otherwise not started
    return 'not_started'

def main():
    print("Loading status data...")

    # Load the final status table
    df = pd.read_excel(os.path.join(DATA_DIR, 'INTERSECTION_STATUS_FINAL.xlsx'),
                       sheet_name='All Intersections')

    # Also load the master report for additional details
    master_df = pd.read_excel(os.path.join(DATA_DIR, 'MASTER_INTERSECTION_REPORT_CLEAN.xlsx'),
                              sheet_name='All Intersections')

    # Create lookup by code
    master_lookup = {}
    for _, row in master_df.iterrows():
        code = safe_str(row.get('POSTAZIONE_CODE'))
        if code:
            master_lookup[code] = row

    print(f"Processing {len(df)} intersections...")

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

    for _, row in df.iterrows():
        code = safe_str(row.get('CODE'))
        name = safe_str(row.get('NAME'))
        lotto = safe_str(row.get('LOTTO'))
        sistema = safe_str(row.get('SISTEMA'))
        n_disp = safe_int(row.get('N_DISP'))
        codice_imp = safe_str(row.get('CODICE_IMPIANTO'))

        # Get status values and map to dashboard format
        inst_status_raw = safe_str(row.get('INST_STATUS')) or 'NOT_STARTED'
        cfg_status_raw = safe_str(row.get('CFG_STATUS')) or 'NOT_STARTED'
        conn_status_raw = safe_str(row.get('CONN_STATUS')) or 'NOT_STARTED'
        val_status_raw = safe_str(row.get('VAL_STATUS')) or 'NOT_STARTED'

        inst_status = INST_STATUS_MAP.get(inst_status_raw, 'not_started')
        cfg_status = CFG_STATUS_MAP.get(cfg_status_raw, 'not_started')
        conn_status = CONN_STATUS_MAP.get(conn_status_raw, 'not_started')
        val_status = VAL_STATUS_MAP.get(val_status_raw, 'not_started')

        # Get additional data from master
        master_row = master_lookup.get(code, {})

        # Get raw data strings for display
        inst_data = safe_str(row.get('INST_DATA'))
        cfg_data = safe_str(row.get('CFG_DATA'))
        conn_data = safe_str(row.get('CONN_DATA'))
        val_data = safe_str(row.get('VAL_DATA'))

        # Determine overall status
        overall = determine_overall_status(inst_status, cfg_status, conn_status, val_status)

        # Build intersection object
        intersection = {
            'id': code,
            'name': f"{code}-{name}",
            'lotto': lotto,
            'system': sistema,
            'codice_impianto': codice_imp,
            'num_radars': n_disp,

            'installation': {
                'status': inst_status,
                'status_detail': inst_status_raw,
                'data': inst_data,
                'blocked_conduits': inst_status_raw == 'BLOCKED',
            },

            'configuration': {
                'status': cfg_status,
                'status_detail': cfg_status_raw,
                'data': cfg_data,
            },

            'connection': {
                'status': conn_status,
                'status_detail': conn_status_raw,
                'data': conn_data,
            },

            'validation': {
                'status': val_status,
                'status_detail': val_status_raw,
                'data': val_data,
            },

            'overall_status': overall,
            'coordinates': None,  # Would need geocoding
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

        # By lotto
        if lotto:
            if lotto not in summary['by_lotto']:
                summary['by_lotto'][lotto] = {'intersections': 0, 'radars': 0}
            summary['by_lotto'][lotto]['intersections'] += 1
            summary['by_lotto'][lotto]['radars'] += n_disp

        # By system
        if sistema:
            if sistema not in summary['by_system']:
                summary['by_system'][sistema] = {'intersections': 0, 'radars': 0}
            summary['by_system'][sistema]['intersections'] += 1
            summary['by_system'][sistema]['radars'] += n_disp

        # By stage
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
    print(f"Fully working: {summary['fully_working']}")

    print("\nBy Stage Status:")
    for stage, counts in summary['by_stage'].items():
        print(f"  {stage.capitalize()}:")
        for status, count in counts.items():
            print(f"    {status}: {count}")

if __name__ == '__main__':
    main()
