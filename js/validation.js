/**
 * Data Validation Module
 * Performs comprehensive data quality checks on intersection data
 */

const DataValidator = {
    issues: [],
    completenessScores: {},

    /**
     * Run all validations and return results
     */
    validateAll() {
        this.issues = [];
        this.completenessScores = {};

        const intersections = DataManager.getIntersections();

        // Debug: log data structure
        console.log('Validation: Found', intersections.length, 'intersections');
        if (intersections.length > 0) {
            const sample = intersections[0];
            console.log('Sample intersection structure:', {
                id: sample.id,
                hasInstallation: !!sample.installation,
                installationStatus: sample.installation?.status,
                hasConfiguration: !!sample.configuration,
                hasConnection: !!sample.connection,
                hasValidation: !!sample.validation
            });
        }

        intersections.forEach(intersection => {
            // Run all validation checks
            this.validateStatusLogic(intersection);
            this.validateMissingData(intersection);
            this.calculateCompleteness(intersection);
        });

        // Run cross-intersection checks
        this.detectDuplicates(intersections);
        this.crossSourceValidation(intersections);

        return {
            issues: this.issues,
            completenessScores: this.completenessScores,
            summary: this.generateSummary()
        };
    },

    /**
     * Validate status logic - check that status progressions make sense
     */
    validateStatusLogic(intersection) {
        const inst = intersection.installation || {};
        const conf = intersection.configuration || {};
        const conn = intersection.connection || {};
        const val = intersection.validation || {};

        // Rule 1: Can't have Configuration "completed" if Installation is "blocked"
        if (inst.status === 'blocked' && conf.status === 'completed') {
            this.addIssue(intersection, 'status_logic', 'critical',
                'Configurazione completata ma Installazione bloccata',
                'La configurazione non puo essere completata se l\'installazione e bloccata',
                { stage: 'configuration', conflicting_stage: 'installation' }
            );
        }

        // Rule 2: Can't have Connection "completed" if Installation is "blocked"
        if (inst.status === 'blocked' && conn.status === 'completed') {
            this.addIssue(intersection, 'status_logic', 'critical',
                'Connessione completata ma Installazione bloccata',
                'La connessione non puo essere completata se l\'installazione e bloccata',
                { stage: 'connection', conflicting_stage: 'installation' }
            );
        }

        // Rule 3: Can't have Validation started if Installation not completed
        if (inst.status !== 'completed' && val.status === 'in_progress') {
            this.addIssue(intersection, 'status_logic', 'warning',
                'Validazione in corso ma Installazione non completata',
                'La validazione normalmente inizia dopo il completamento dell\'installazione',
                { stage: 'validation', conflicting_stage: 'installation' }
            );
        }

        // Rule 4: Can't have Validation completed if any other stage is blocked
        if (val.status === 'completed' &&
            (inst.status === 'blocked' || conf.status === 'blocked' || conn.status === 'blocked')) {
            this.addIssue(intersection, 'status_logic', 'critical',
                'Validazione completata ma altre fasi bloccate',
                'La validazione non puo essere completata se ci sono fasi bloccate',
                { stage: 'validation' }
            );
        }

        // Rule 5: Installation blocked but no blocking info
        if (inst.status === 'blocked' && !inst.disp_inst_bloccati && !inst.soluzione_bloccati) {
            this.addIssue(intersection, 'missing_blocking_info', 'warning',
                'Installazione bloccata senza dettagli',
                'Specificare il motivo del blocco e la possibile soluzione',
                { stage: 'installation' }
            );
        }
    },

    /**
     * Validate missing data - identify intersections with critical missing fields
     */
    validateMissingData(intersection) {
        const inst = intersection.installation || {};
        const lotto = intersection.lotto;
        const isM91 = lotto === 'M9.1';
        const isOmnia = (intersection.system || '').toUpperCase() === 'OMNIA';

        // Critical: No coordinates
        if (!intersection.coordinates) {
            this.addIssue(intersection, 'missing_coordinates', 'critical',
                'Coordinate mancanti',
                'L\'intersezione non puo essere visualizzata sulla mappa',
                { field: 'coordinates' }
            );
        }

        // Critical: No codice impianto
        if (!intersection.codice_impianto) {
            this.addIssue(intersection, 'missing_codice_impianto', 'critical',
                'Codice Impianto mancante',
                'Impossibile collegare ai dati SWARCO/Semaforica',
                { field: 'codice_impianto' }
            );
        }

        // Critical: No lotto assignment
        if (!lotto) {
            this.addIssue(intersection, 'missing_lotto', 'critical',
                'Lotto non assegnato',
                'Specificare se M9.1 o M9.2',
                { field: 'lotto' }
            );
        }

        // Critical: No system assignment
        if (!intersection.system) {
            this.addIssue(intersection, 'missing_system', 'critical',
                'Sistema non specificato',
                'Specificare se Omnia o Tmacs',
                { field: 'system' }
            );
        }

        // Warning: No radar count
        if (!intersection.num_radars || intersection.num_radars === 0) {
            this.addIssue(intersection, 'missing_radar_count', 'warning',
                'Numero dispositivi mancante o zero',
                'Specificare il numero di radar da installare',
                { field: 'num_radars' }
            );
        }

        // Lotto-specific missing data
        if (isM91) {
            // M9.1 should have L1 match
            if (!inst.l1_match) {
                this.addIssue(intersection, 'missing_l1_match', 'warning',
                    'Corrispondenza Lotto 1 mancante',
                    'Verificare la corrispondenza con il file Lotto 1',
                    { field: 'l1_match' }
                );
            }
        } else if (lotto === 'M9.2') {
            // M9.2 should have L2 match
            if (!inst.l2_match) {
                this.addIssue(intersection, 'missing_l2_match', 'warning',
                    'Corrispondenza Lotto 2 mancante',
                    'Verificare la corrispondenza con il file Lotto 2',
                    { field: 'l2_match' }
                );
            }
        }

        // System-specific missing data for Connection
        const conn = intersection.connection || {};
        if (isOmnia) {
            if (!conn.swarco_spot_status && conn.status !== 'not_started') {
                this.addIssue(intersection, 'missing_swarco_data', 'info',
                    'Dati SWARCO mancanti',
                    'Verificare lo stato SPOT nel file SWARCO',
                    { field: 'swarco_spot_status' }
                );
            }
        } else {
            if (!conn.sema_aut && conn.status !== 'not_started') {
                this.addIssue(intersection, 'missing_semaforica_data', 'info',
                    'Dati Semaforica mancanti',
                    'Verificare lo stato AUT nel file Semaforica',
                    { field: 'sema_aut' }
                );
            }
        }
    },

    /**
     * Calculate data completeness score for an intersection
     */
    calculateCompleteness(intersection) {
        const lotto = intersection.lotto;
        const isM91 = lotto === 'M9.1';
        const isOmnia = (intersection.system || '').toUpperCase() === 'OMNIA';
        const inst = intersection.installation || {};
        const conf = intersection.configuration || {};
        const conn = intersection.connection || {};

        // Define required fields by section
        const generalFields = ['id', 'name', 'lotto', 'system', 'codice_impianto', 'num_radars', 'coordinates'];

        const installationFieldsL1 = ['l1_match', 'l1_planimetrie', 'l1_passaggio_cavi',
            'l1_install_sensori', 'l1_cablaggio'];
        const installationFieldsL2 = ['l2_match', 'l2_data_installaz', 'l2_config_rsm',
            'l2_planimetria', 'l2_n_radar_finiti'];

        const configFields = ['plan_cfg_inviate', 'cfg_def_status', 'cfg_def_inst'];

        const connectionFieldsOmnia = ['da_centr_aut', 'swarco_spot_status', 'swarco_spot_firmware'];
        const connectionFieldsTmacs = ['da_centr_aut', 'sema_aut'];

        // Calculate scores
        let scores = {};

        // General completeness
        let generalFilled = 0;
        generalFields.forEach(field => {
            if (intersection[field] !== null && intersection[field] !== undefined && intersection[field] !== '') {
                generalFilled++;
            }
        });
        scores.general = Math.round((generalFilled / generalFields.length) * 100);

        // Installation completeness
        const instFields = isM91 ? installationFieldsL1 : installationFieldsL2;
        let instFilled = 0;
        instFields.forEach(field => {
            if (inst[field] !== null && inst[field] !== undefined && inst[field] !== '') {
                instFilled++;
            }
        });
        scores.installation = Math.round((instFilled / instFields.length) * 100);

        // Configuration completeness
        let confFilled = 0;
        configFields.forEach(field => {
            if (conf[field] !== null && conf[field] !== undefined && conf[field] !== '') {
                confFilled++;
            }
        });
        scores.configuration = Math.round((confFilled / configFields.length) * 100);

        // Connection completeness
        const connFields = isOmnia ? connectionFieldsOmnia : connectionFieldsTmacs;
        let connFilled = 0;
        connFields.forEach(field => {
            if (conn[field] !== null && conn[field] !== undefined && conn[field] !== '') {
                connFilled++;
            }
        });
        scores.connection = Math.round((connFilled / connFields.length) * 100);

        // Overall score (weighted average)
        scores.overall = Math.round(
            (scores.general * 0.3) +
            (scores.installation * 0.3) +
            (scores.configuration * 0.2) +
            (scores.connection * 0.2)
        );

        this.completenessScores[intersection.id] = scores;

        // Flag low completeness
        if (scores.overall < 50) {
            this.addIssue(intersection, 'low_completeness', 'warning',
                `Completezza dati bassa (${scores.overall}%)`,
                'Molti campi mancanti - verificare i dati',
                { scores }
            );
        }
    },

    /**
     * Detect duplicate intersections
     */
    detectDuplicates(intersections) {
        const nameMap = {};
        const codiceMap = {};

        intersections.forEach(intersection => {
            // Check for same name with different codes
            const nameLower = (intersection.name || '').toLowerCase().trim();
            if (nameLower) {
                if (nameMap[nameLower] && nameMap[nameLower] !== intersection.id) {
                    this.addIssue(intersection, 'duplicate_name', 'warning',
                        'Possibile duplicato - stesso nome',
                        `Nome simile a intersezione ${nameMap[nameLower]}`,
                        { duplicate_id: nameMap[nameLower] }
                    );
                } else {
                    nameMap[nameLower] = intersection.id;
                }
            }

            // Check for same codice impianto
            const codice = intersection.codice_impianto;
            if (codice) {
                if (codiceMap[codice] && codiceMap[codice] !== intersection.id) {
                    this.addIssue(intersection, 'duplicate_codice', 'critical',
                        'Codice Impianto duplicato',
                        `Stesso codice impianto di intersezione ${codiceMap[codice]}`,
                        { duplicate_id: codiceMap[codice], codice_impianto: codice }
                    );
                } else {
                    codiceMap[codice] = intersection.id;
                }
            }
        });

        // Check for similar names (fuzzy matching)
        const names = intersections.map(i => ({ id: i.id, name: i.name || '' }));
        for (let i = 0; i < names.length; i++) {
            for (let j = i + 1; j < names.length; j++) {
                const similarity = this.calculateSimilarity(names[i].name, names[j].name);
                if (similarity > 0.8 && similarity < 1) {
                    // Already handled exact matches above
                    this.addIssue({ id: names[i].id, name: names[i].name }, 'similar_name', 'info',
                        'Nome molto simile ad altra intersezione',
                        `Simile a ${names[j].id}: ${names[j].name} (${Math.round(similarity * 100)}% simile)`,
                        { similar_id: names[j].id, similarity: Math.round(similarity * 100) }
                    );
                }
            }
        }
    },

    /**
     * Cross-source validation - check consistency between data sources
     */
    crossSourceValidation(intersections) {
        intersections.forEach(intersection => {
            const lotto = intersection.lotto;
            const isM91 = lotto === 'M9.1';
            const isOmnia = (intersection.system || '').toUpperCase() === 'OMNIA';
            const inst = intersection.installation || {};
            const conn = intersection.connection || {};

            // Check Lotto data consistency
            if (isM91 && inst.l1_match) {
                // M9.1 should have L1 data, not L2
                if (inst.l2_match || inst.l2_data_installaz) {
                    this.addIssue(intersection, 'lotto_mismatch', 'warning',
                        'Dati Lotto incongruenti',
                        'Intersezione M9.1 ha dati Lotto 2',
                        { expected: 'M9.1', found: 'L2 data present' }
                    );
                }
            } else if (lotto === 'M9.2' && inst.l2_match) {
                // M9.2 should have L2 data, not L1
                if (inst.l1_match && inst.l1_planimetrie) {
                    this.addIssue(intersection, 'lotto_mismatch', 'warning',
                        'Dati Lotto incongruenti',
                        'Intersezione M9.2 ha dati Lotto 1',
                        { expected: 'M9.2', found: 'L1 data present' }
                    );
                }
            }

            // Check system data consistency
            if (isOmnia) {
                // Omnia should have SWARCO data, not Semaforica
                if (conn.sema_aut && !conn.swarco_spot_status) {
                    this.addIssue(intersection, 'system_mismatch', 'warning',
                        'Dati sistema incongruenti',
                        'Sistema Omnia ma presenti solo dati Semaforica',
                        { expected: 'SWARCO', found: 'Semaforica' }
                    );
                }
            } else if (intersection.system && intersection.system.toUpperCase() === 'TMACS') {
                // Tmacs should have Semaforica data, not SWARCO
                if (conn.swarco_spot_status && !conn.sema_aut) {
                    this.addIssue(intersection, 'system_mismatch', 'warning',
                        'Dati sistema incongruenti',
                        'Sistema Tmacs ma presenti solo dati SWARCO',
                        { expected: 'Semaforica', found: 'SWARCO' }
                    );
                }
            }

            // Check radar count consistency
            if (isM91 && inst.l1_install_sensori && intersection.num_radars) {
                if (inst.l1_install_sensori !== intersection.num_radars) {
                    this.addIssue(intersection, 'radar_count_mismatch', 'warning',
                        'Conteggio radar incongruente',
                        `Master: ${intersection.num_radars}, Lotto 1: ${inst.l1_install_sensori}`,
                        { master_count: intersection.num_radars, l1_count: inst.l1_install_sensori }
                    );
                }
            }

            if (lotto === 'M9.2' && inst.l2_n_radar_finiti && intersection.num_radars) {
                if (inst.l2_n_radar_finiti !== intersection.num_radars) {
                    this.addIssue(intersection, 'radar_count_mismatch', 'warning',
                        'Conteggio radar incongruente',
                        `Master: ${intersection.num_radars}, Lotto 2: ${inst.l2_n_radar_finiti}`,
                        { master_count: intersection.num_radars, l2_count: inst.l2_n_radar_finiti }
                    );
                }
            }
        });
    },

    /**
     * Calculate string similarity (Levenshtein-based)
     */
    calculateSimilarity(str1, str2) {
        if (!str1 || !str2) return 0;
        str1 = str1.toLowerCase();
        str2 = str2.toLowerCase();

        if (str1 === str2) return 1;

        const len1 = str1.length;
        const len2 = str2.length;
        const maxLen = Math.max(len1, len2);

        if (maxLen === 0) return 1;

        // Simple Levenshtein distance
        const matrix = [];
        for (let i = 0; i <= len1; i++) {
            matrix[i] = [i];
        }
        for (let j = 0; j <= len2; j++) {
            matrix[0][j] = j;
        }

        for (let i = 1; i <= len1; i++) {
            for (let j = 1; j <= len2; j++) {
                const cost = str1[i - 1] === str2[j - 1] ? 0 : 1;
                matrix[i][j] = Math.min(
                    matrix[i - 1][j] + 1,
                    matrix[i][j - 1] + 1,
                    matrix[i - 1][j - 1] + cost
                );
            }
        }

        const distance = matrix[len1][len2];
        return 1 - (distance / maxLen);
    },

    /**
     * Add an issue to the list
     */
    addIssue(intersection, type, severity, title, message, details = {}) {
        this.issues.push({
            intersection_id: intersection.id,
            intersection_name: intersection.name,
            type,
            severity, // 'critical', 'warning', 'info'
            title,
            message,
            details,
            timestamp: new Date().toISOString()
        });
    },

    /**
     * Generate summary statistics
     */
    generateSummary() {
        const critical = this.issues.filter(i => i.severity === 'critical').length;
        const warning = this.issues.filter(i => i.severity === 'warning').length;
        const info = this.issues.filter(i => i.severity === 'info').length;

        // Group by type
        const byType = {};
        this.issues.forEach(issue => {
            byType[issue.type] = (byType[issue.type] || 0) + 1;
        });

        // Completeness stats
        const scores = Object.values(this.completenessScores);
        const avgCompleteness = scores.length > 0
            ? Math.round(scores.reduce((sum, s) => sum + s.overall, 0) / scores.length)
            : 0;

        const lowCompleteness = scores.filter(s => s.overall < 50).length;
        const highCompleteness = scores.filter(s => s.overall >= 80).length;

        return {
            total_issues: this.issues.length,
            critical,
            warning,
            info,
            by_type: byType,
            completeness: {
                average: avgCompleteness,
                low_count: lowCompleteness,
                high_count: highCompleteness
            }
        };
    },

    /**
     * Get issues for a specific intersection
     */
    getIssuesForIntersection(id) {
        return this.issues.filter(i => i.intersection_id === id);
    },

    /**
     * Get issues by severity
     */
    getIssuesBySeverity(severity) {
        return this.issues.filter(i => i.severity === severity);
    },

    /**
     * Get issues by type
     */
    getIssuesByType(type) {
        return this.issues.filter(i => i.type === type);
    },

    /**
     * Export validation report to Excel-compatible format
     */
    exportToExcel() {
        const rows = [];

        // Header
        rows.push(['ID', 'Nome Intersezione', 'Tipo Problema', 'Gravita', 'Titolo', 'Descrizione', 'Dettagli']);

        // Issues
        this.issues.forEach(issue => {
            rows.push([
                issue.intersection_id,
                issue.intersection_name,
                issue.type,
                issue.severity,
                issue.title,
                issue.message,
                JSON.stringify(issue.details)
            ]);
        });

        return rows;
    },

    /**
     * Export completeness scores to Excel-compatible format
     */
    exportCompletenessToExcel() {
        const rows = [];

        // Header
        rows.push(['ID', 'Generale %', 'Installazione %', 'Configurazione %', 'Connessione %', 'Totale %']);

        // Scores
        Object.entries(this.completenessScores).forEach(([id, scores]) => {
            rows.push([
                id,
                scores.general,
                scores.installation,
                scores.configuration,
                scores.connection,
                scores.overall
            ]);
        });

        return rows;
    }
};
