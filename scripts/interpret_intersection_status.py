#!/usr/bin/env python3
"""
Interpret intersection status based on available data.
Maps data columns to the 4 stages: INSTALLATION, CONFIGURATION, CONNECTION, VALIDATION
"""

import pandas as pd
import os

pd.set_option('display.max_columns', None)
pd.set_option('display.width', None)
pd.set_option('display.max_colwidth', 50)

DATA_DIR = '/home/user/Configurazioni-Radar/data-import'

def safe_str(val):
    if pd.isna(val):
        return ''
    return str(val).strip()

def analyze_installation(row):
    """
    Analyze INSTALLATION stage based on:
    - L1_* columns (for M9.1): planimetrie, passaggio_cavi, install_sensori, cablaggio, completato
    - L2_* columns (for M9.2): data_installaz, n_radar_finiti
    - DISP_INST_BLOCCATI, DISP_DA_INST, SOLUZIONE_BLOCCATI
    """
    lotto = safe_str(row.get('LOTTO'))
    info = {}
    status = 'UNKNOWN'

    if lotto == 'M9.1':
        # Lotto 1 installation data
        l1_match = safe_str(row.get('L1_MATCH'))
        l1_planimetrie = safe_str(row.get('L1_PLANIMETRIE'))
        l1_passaggio_cavi = safe_str(row.get('L1_PASSAGGIO_CAVI'))
        l1_install_sensori = safe_str(row.get('L1_INSTALL_SENSORI'))
        l1_cablaggio = safe_str(row.get('L1_CABLAGGIO'))
        l1_completato = safe_str(row.get('L1_COMPLETATO'))
        l1_data_compl = safe_str(row.get('L1_DATA_COMPL'))

        info['L1_MATCH'] = l1_match
        info['L1_PLANIMETRIE'] = l1_planimetrie
        info['L1_PASSAGGIO_CAVI'] = l1_passaggio_cavi
        info['L1_INSTALL_SENSORI'] = l1_install_sensori
        info['L1_CABLAGGIO'] = l1_cablaggio
        info['L1_COMPLETATO'] = l1_completato
        info['L1_DATA_COMPL'] = l1_data_compl

        # Interpretation
        if l1_completato.lower() == 'ok':
            status = 'COMPLETE'
        elif l1_completato.lower() == 'parziale':
            status = 'PARTIAL'
        elif l1_completato.lower() == 'no':
            status = 'BLOCKED'
        elif l1_match:
            # Has L1 data but not marked complete
            if l1_install_sensori or l1_cablaggio:
                status = 'IN_PROGRESS'
            elif l1_planimetrie:
                status = 'STARTED'
            else:
                status = 'NOT_STARTED'
        else:
            status = 'NO_DATA'

    elif lotto == 'M9.2':
        # Lotto 2 installation data
        l2_match = safe_str(row.get('L2_MATCH'))
        l2_data_inst = safe_str(row.get('L2_DATA_INSTALLAZ'))
        l2_n_radar = safe_str(row.get('L2_N_RADAR_FINITI'))
        l2_centralizzati = safe_str(row.get('L2_CENTRALIZZATI'))

        info['L2_MATCH'] = l2_match
        info['L2_DATA_INSTALLAZ'] = l2_data_inst
        info['L2_N_RADAR_FINITI'] = l2_n_radar
        info['L2_CENTRALIZZATI'] = l2_centralizzati

        # Interpretation
        if l2_data_inst and l2_n_radar:
            status = 'COMPLETE'
        elif l2_data_inst:
            status = 'IN_PROGRESS'
        elif l2_match:
            status = 'STARTED'
        else:
            status = 'NO_DATA'

    # Check for blocking issues
    disp_bloccati = safe_str(row.get('DISP_INST_BLOCCATI'))
    disp_da_inst = safe_str(row.get('DISP_DA_INST'))
    soluzione_bloccati = safe_str(row.get('SOLUZIONE_BLOCCATI'))

    if disp_bloccati:
        info['DISP_INST_BLOCCATI'] = disp_bloccati
    if disp_da_inst:
        info['DISP_DA_INST'] = disp_da_inst
    if soluzione_bloccati:
        info['SOLUZIONE_BLOCCATI'] = soluzione_bloccati

    if disp_bloccati and status not in ['COMPLETE']:
        status = 'BLOCKED'

    return status, info


def analyze_configuration(row):
    """
    Analyze CONFIGURATION stage based on:
    - PLAN_CFG_INVIATE (planimetrie sent)
    - CFG_DEF_STATUS (config status)
    - CFG_DEF_INST
    - L2_CONFIG_RSM, L2_CONFIG_INSTAL (for M9.2)
    """
    info = {}
    status = 'UNKNOWN'

    plan_cfg = safe_str(row.get('PLAN_CFG_INVIATE'))
    cfg_status = safe_str(row.get('CFG_DEF_STATUS'))
    cfg_inst = safe_str(row.get('CFG_DEF_INST'))

    info['PLAN_CFG_INVIATE'] = plan_cfg
    info['CFG_DEF_STATUS'] = cfg_status
    info['CFG_DEF_INST'] = cfg_inst

    lotto = safe_str(row.get('LOTTO'))
    if lotto == 'M9.2':
        l2_config_rsm = safe_str(row.get('L2_CONFIG_RSM'))
        l2_config_instal = safe_str(row.get('L2_CONFIG_INSTAL'))
        info['L2_CONFIG_RSM'] = l2_config_rsm
        info['L2_CONFIG_INSTAL'] = l2_config_instal

    # Interpret CFG_DEF_STATUS
    # Values: DaFare, DA VRF, aff.GO, Ass.FM/MC, INVIATA, ok, daINVIARE
    cfg_status_lower = cfg_status.lower()

    if cfg_status_lower == 'ok':
        status = 'COMPLETE'
    elif cfg_status_lower == 'aff.go':
        status = 'READY_FOR_APPROVAL'  # Affidato GO - assigned
    elif cfg_status_lower == 'da vrf':
        status = 'PENDING_VERIFICATION'
    elif cfg_status_lower == 'inviata':
        status = 'SENT'
    elif cfg_status_lower == 'dainviare':
        status = 'READY_TO_SEND'
    elif cfg_status_lower == 'dafare':
        status = 'NOT_STARTED'
    elif 'ass.' in cfg_status_lower:
        status = 'ASSIGNED'  # Assigned to FM/MC
    else:
        status = 'UNKNOWN'

    return status, info


def analyze_connection(row):
    """
    Analyze CONNECTION stage based on:
    - TABELLA_IF_UTC (interface table)
    - INST_INTERFACCIA_UTC
    - DA_CENTR_AUT (Centralizzato, AUT da install., AUT, etc.)
    - SISTEMA (Omnia vs Tmacs)
    - SWARCO_SPOT_STATUS
    - SEMA_AUT
    """
    info = {}
    status = 'UNKNOWN'

    sistema = safe_str(row.get('SISTEMA'))
    tabella_utc = safe_str(row.get('TABELLA_IF_UTC'))
    inst_if_utc = safe_str(row.get('INST_INTERFACCIA_UTC'))
    da_centr_aut = safe_str(row.get('DA_CENTR_AUT'))
    swarco_status = safe_str(row.get('SWARCO_SPOT_STATUS'))
    sema_aut = safe_str(row.get('SEMA_AUT'))

    info['SISTEMA'] = sistema
    info['TABELLA_IF_UTC'] = tabella_utc
    info['INST_INTERFACCIA_UTC'] = inst_if_utc
    info['DA_CENTR_AUT'] = da_centr_aut

    if sistema.lower() == 'omnia':
        info['SWARCO_SPOT_STATUS'] = swarco_status
    elif sistema.lower() == 'tmacs':
        info['SEMA_AUT'] = sema_aut

    # Interpret connection status
    da_centr_lower = da_centr_aut.lower()

    if 'centralizzato' in da_centr_lower:
        status = 'CENTRALIZED'
    elif da_centr_lower == 'aut':
        status = 'AUT_CONFIGURED'
    elif 'aut da install' in da_centr_lower:
        status = 'AUT_PENDING_INSTALL'
    elif da_centr_lower == 'omnia':
        status = 'OMNIA_PENDING'
    else:
        status = 'NOT_STARTED'

    # Check SWARCO/Semaforica issues
    if swarco_status and 'NO SIM' in swarco_status:
        info['SWARCO_ISSUE'] = 'NO SIM'
        if status == 'NOT_STARTED':
            status = 'BLOCKED_SWARCO'

    if sema_aut:
        if sema_aut.upper() == 'SI':
            info['SEMA_STATUS'] = 'AUT_OK'
        elif sema_aut.upper() == 'NO':
            info['SEMA_STATUS'] = 'AUT_MISSING'

    return status, info


def analyze_validation(row):
    """
    Analyze VALIDATION stage based on:
    - VRF_DATI
    - Overall status of previous stages
    """
    info = {}
    status = 'UNKNOWN'

    vrf_dati = safe_str(row.get('VRF_DATI'))
    info['VRF_DATI'] = vrf_dati

    if vrf_dati:
        if 'vrf' in vrf_dati.lower() or 'utc' in vrf_dati.lower():
            status = 'IN_VERIFICATION'
        else:
            status = 'STARTED'
    else:
        status = 'NOT_STARTED'

    return status, info


def main():
    print("Loading master intersection report...")
    df = pd.read_excel(os.path.join(DATA_DIR, 'MASTER_INTERSECTION_REPORT_CLEAN.xlsx'),
                       sheet_name='All Intersections')

    print(f"Analyzing {len(df)} intersections...\n")
    print("=" * 120)

    results = []

    for idx, row in df.iterrows():
        code = safe_str(row.get('POSTAZIONE_CODE'))
        name = safe_str(row.get('POSTAZIONE_NAME'))
        lotto = safe_str(row.get('LOTTO'))
        sistema = safe_str(row.get('SISTEMA'))
        n_disp = safe_str(row.get('N_DISPOSITIVI'))

        inst_status, inst_info = analyze_installation(row)
        cfg_status, cfg_info = analyze_configuration(row)
        conn_status, conn_info = analyze_connection(row)
        val_status, val_info = analyze_validation(row)

        results.append({
            'CODE': code,
            'NAME': name,
            'LOTTO': lotto,
            'SISTEMA': sistema,
            'N_DISP': n_disp,
            'INSTALLATION': inst_status,
            'INST_INFO': inst_info,
            'CONFIGURATION': cfg_status,
            'CFG_INFO': cfg_info,
            'CONNECTION': conn_status,
            'CONN_INFO': conn_info,
            'VALIDATION': val_status,
            'VAL_INFO': val_info,
        })

    # Print results grouped by status combination
    print("\n" + "=" * 120)
    print("INTERSECTION STATUS ANALYSIS")
    print("=" * 120)

    for r in results:
        print(f"\n[{r['CODE']}] {r['NAME']}")
        print(f"    Lotto: {r['LOTTO']} | Sistema: {r['SISTEMA']} | Dispositivi: {r['N_DISP']}")
        print(f"    ┌─────────────────────────────────────────────────────────────────────────────")
        print(f"    │ INSTALLATION:  {r['INSTALLATION']}")
        if r['INST_INFO']:
            for k, v in r['INST_INFO'].items():
                if v:
                    print(f"    │    {k}: {v}")
        print(f"    │ CONFIGURATION: {r['CONFIGURATION']}")
        if r['CFG_INFO']:
            for k, v in r['CFG_INFO'].items():
                if v:
                    print(f"    │    {k}: {v}")
        print(f"    │ CONNECTION:    {r['CONNECTION']}")
        if r['CONN_INFO']:
            for k, v in r['CONN_INFO'].items():
                if v:
                    print(f"    │    {k}: {v}")
        print(f"    │ VALIDATION:    {r['VALIDATION']}")
        if r['VAL_INFO']:
            for k, v in r['VAL_INFO'].items():
                if v:
                    print(f"    │    {k}: {v}")
        print(f"    └─────────────────────────────────────────────────────────────────────────────")

    # Summary statistics
    print("\n" + "=" * 120)
    print("SUMMARY STATISTICS")
    print("=" * 120)

    df_results = pd.DataFrame(results)

    print("\nINSTALLATION Status:")
    print(df_results['INSTALLATION'].value_counts())

    print("\nCONFIGURATION Status:")
    print(df_results['CONFIGURATION'].value_counts())

    print("\nCONNECTION Status:")
    print(df_results['CONNECTION'].value_counts())

    print("\nVALIDATION Status:")
    print(df_results['VALIDATION'].value_counts())

    # Save to file for review
    output_path = os.path.join(DATA_DIR, 'INTERSECTION_STATUS_ANALYSIS.txt')
    with open(output_path, 'w') as f:
        f.write("INTERSECTION STATUS ANALYSIS\n")
        f.write("=" * 120 + "\n\n")

        for r in results:
            f.write(f"[{r['CODE']}] {r['NAME']}\n")
            f.write(f"    Lotto: {r['LOTTO']} | Sistema: {r['SISTEMA']} | Dispositivi: {r['N_DISP']}\n")
            f.write(f"    INSTALLATION:  {r['INSTALLATION']}\n")
            for k, v in r['INST_INFO'].items():
                if v:
                    f.write(f"        {k}: {v}\n")
            f.write(f"    CONFIGURATION: {r['CONFIGURATION']}\n")
            for k, v in r['CFG_INFO'].items():
                if v:
                    f.write(f"        {k}: {v}\n")
            f.write(f"    CONNECTION:    {r['CONNECTION']}\n")
            for k, v in r['CONN_INFO'].items():
                if v:
                    f.write(f"        {k}: {v}\n")
            f.write(f"    VALIDATION:    {r['VALIDATION']}\n")
            for k, v in r['VAL_INFO'].items():
                if v:
                    f.write(f"        {k}: {v}\n")
            f.write("\n" + "-" * 80 + "\n\n")

    print(f"\nDetailed analysis saved to: {output_path}")


if __name__ == '__main__':
    main()
