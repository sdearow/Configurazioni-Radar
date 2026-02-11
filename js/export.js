/**
 * Export Module
 * Handles data export to Excel, PDF, and JSON formats
 * With full stage details and file import support
 */

const ExportManager = {
    /**
     * Initialize export module
     */
    init() {
        this.bindEvents();
        this.populateIntersectionSelects();
        return this;
    },

    /**
     * Bind event listeners
     */
    bindEvents() {
        // Backup
        const backupBtn = document.getElementById('backup-data');
        if (backupBtn) {
            backupBtn.addEventListener('click', () => DataManager.createBackup());
        }

        // Restore
        const restoreBtn = document.getElementById('restore-data');
        if (restoreBtn) {
            restoreBtn.addEventListener('click', () => this.triggerRestore());
        }
    },

    /**
     * Populate intersection selects for export
     */
    populateIntersectionSelects() {
        const intersections = DataManager.getIntersections();

        // Site visit select
        const siteVisitSelect = document.getElementById('export-intersection-select');
        if (siteVisitSelect) {
            siteVisitSelect.innerHTML = '<option value="">Seleziona intersezione...</option>' +
                intersections.map(i => `<option value="${i.id}">${i.id} - ${i.name || 'Sconosciuto'}</option>`).join('');
        }

        // Import intersection select
        const importSelect = document.getElementById('import-intersection-select');
        if (importSelect) {
            importSelect.innerHTML = '<option value="">Seleziona intersezione...</option>' +
                intersections.map(i => `<option value="${i.id}">${i.id} - ${i.name || 'Sconosciuto'}</option>`).join('');
        }
    },

    /**
     * Populate intersection select (alias for compatibility)
     */
    populateIntersectionSelect() {
        this.populateIntersectionSelects();
    },

    /**
     * Get stage status safely from nested structure
     */
    getStageStatus(intersection, stage) {
        return intersection[stage]?.status || 'not_started';
    },

    /**
     * Export full data to Excel with all stage details
     */
    exportFullExcel() {
        const intersections = DataManager.getIntersections();

        // Main data sheet with all stage statuses
        const mainData = intersections.map(i => {
            const inst = i.installation || {};
            const conf = i.configuration || {};
            const conn = i.connection || {};
            const val = i.validation || {};
            const coords = i.coordinates || {};

            return {
                'Codice': i.id,
                'Nome': i.name || '',
                'Lotto': i.lotto || '',
                'Sistema': i.system || '',
                'Codice Impianto': i.codice_impianto || '',
                'Num Radar': i.num_radars || 0,
                'Latitudine': coords.lat || '',
                'Longitudine': coords.lng || '',
                'Stato Complessivo': this.formatStatus(i.overall_status),
                // Stage statuses
                'Stato Installazione': this.formatStatus(inst.status),
                'Stato Configurazione': this.formatStatus(conf.status),
                'Stato Connessione': this.formatStatus(conn.status),
                'Stato Validazione': this.formatStatus(val.status),
                // Installation - Lotto 1
                'L1 Match': inst.l1_match || '',
                'L1 Planimetrie': inst.l1_planimetrie || '',
                'L1 Passaggio Cavi': inst.l1_passaggio_cavi || '',
                'L1 Installazione Sensori': inst.l1_install_sensori || '',
                'L1 Cablaggio': inst.l1_cablaggio || '',
                'L1 Screenshot': inst.l1_screenshot || '',
                'L1 Completato': inst.l1_completato || '',
                'L1 Doc Inviata': inst.l1_doc_inviata || '',
                'L1 Data Completamento': inst.l1_data_compl || '',
                // Installation - Lotto 2
                'L2 Match': inst.l2_match || '',
                'L2 Data Installazione': inst.l2_data_installaz || '',
                'L2 Config RSM': inst.l2_config_rsm || '',
                'L2 Config Installata': inst.l2_config_instal || '',
                'L2 Planimetria': inst.l2_planimetria || '',
                'L2 N Radar Finiti': inst.l2_n_radar_finiti || '',
                'L2 Centralizzati': inst.l2_centralizzati || '',
                // Installation - Blocking info
                'Dispositivi Bloccati': inst.disp_inst_bloccati || '',
                'Dispositivi Da Installare': inst.disp_da_inst || '',
                'Soluzione Bloccati': inst.soluzione_bloccati || '',
                // Configuration
                'Plan/Cfg Inviate': conf.plan_cfg_inviate || '',
                'Cfg Definitiva Status': conf.cfg_def_status || '',
                'Cfg Definitiva Installata': conf.cfg_def_inst || '',
                // Connection
                'Da Centralizzare AUT': conn.da_centr_aut || '',
                'Tabella IF UTC': conn.tabella_if_utc || '',
                'Interfaccia UTC Installata': conn.inst_interfaccia_utc || '',
                'SWARCO SPOT Status': conn.swarco_spot_status || '',
                'SWARCO SPOT Firmware': conn.swarco_spot_firmware || '',
                'Semaforica AUT': conn.sema_aut || '',
                'Semaforica Attivita': conn.sema_attivita || '',
                // Validation
                'Verifica Dati': val.vrf_dati || '',
                // Notes
                'Note Principali': i.note_main || '',
                'Note': i.notes || '',
                'Problemi': i.inconsistencies?.length || 0
            };
        });

        // Create workbook
        const wb = XLSX.utils.book_new();
        const ws = XLSX.utils.json_to_sheet(mainData);
        XLSX.utils.book_append_sheet(wb, ws, 'Intersezioni');

        // Tasks sheet
        const tasks = DataManager.getTasks();
        if (tasks.length > 0) {
            const tasksData = tasks.map(t => ({
                'ID': t.id,
                'Titolo': t.title,
                'Descrizione': t.description || '',
                'Intersezione': t.intersection_id || '',
                'Fase': t.stage || '',
                'Sottofase': t.substage || '',
                'Assegnatario': t.assignee || '',
                'Stato': t.status,
                'Priorita': t.priority,
                'Creato': t.created_at,
                'Aggiornato': t.updated_at
            }));
            const tasksWs = XLSX.utils.json_to_sheet(tasksData);
            XLSX.utils.book_append_sheet(wb, tasksWs, 'Tasks');
        }

        // Issues sheet
        const issues = [];
        intersections.forEach(i => {
            if (i.inconsistencies && i.inconsistencies.length > 0) {
                i.inconsistencies.forEach(inc => {
                    issues.push({
                        'Codice Intersezione': i.id,
                        'Nome Intersezione': i.name || '',
                        'Tipo Problema': inc.type,
                        'Messaggio': inc.message || '',
                        'Campo': inc.field || '',
                        'Valore Atteso': inc.main_value || '',
                        'Valore Effettivo': inc.lotto_value || ''
                    });
                });
            }
        });

        if (issues.length > 0) {
            const issuesWs = XLSX.utils.json_to_sheet(issues);
            XLSX.utils.book_append_sheet(wb, issuesWs, 'Problemi');
        }

        // Download
        const filename = `radar_export_completo_${new Date().toISOString().split('T')[0]}.xlsx`;
        XLSX.writeFile(wb, filename);
    },

    /**
     * Export full data to PDF
     */
    exportFullPDF() {
        const { jsPDF } = window.jspdf;
        const doc = new jsPDF('l', 'mm', 'a4'); // Landscape for more columns

        const intersections = DataManager.getIntersections();

        doc.setFontSize(18);
        doc.text('Progetto Radar - Export Completo', 148, 15, { align: 'center' });
        doc.setFontSize(10);
        doc.text(`Generato: ${new Date().toLocaleString('it-IT')}`, 148, 22, { align: 'center' });

        // Summary table
        const tableData = intersections.map(i => {
            const inst = i.installation || {};
            const conf = i.configuration || {};
            const conn = i.connection || {};
            const val = i.validation || {};

            return [
                i.id,
                (i.name || '').substring(0, 25),
                i.lotto || '',
                i.num_radars || 0,
                this.formatStatus(inst.status),
                this.formatStatus(conf.status),
                this.formatStatus(conn.status),
                this.formatStatus(val.status)
            ];
        });

        doc.autoTable({
            startY: 30,
            head: [['Codice', 'Nome', 'Lotto', 'Radar', 'Installazione', 'Configurazione', 'Connessione', 'Validazione']],
            body: tableData,
            styles: { fontSize: 8 },
            headStyles: { fillColor: [37, 99, 235] },
            alternateRowStyles: { fillColor: [241, 245, 249] }
        });

        // Download
        const filename = `radar_export_completo_${new Date().toISOString().split('T')[0]}.pdf`;
        doc.save(filename);
    },

    /**
     * Export site visit sheet for an intersection
     */
    exportSiteVisitSheet() {
        const select = document.getElementById('export-intersection-select');
        if (!select || !select.value) {
            alert('Seleziona un\'intersezione');
            return;
        }

        const intersection = DataManager.getIntersection(select.value);
        if (!intersection) {
            alert('Intersezione non trovata');
            return;
        }

        const { jsPDF } = window.jspdf;
        const doc = new jsPDF();

        const inst = intersection.installation || {};
        const conf = intersection.configuration || {};
        const conn = intersection.connection || {};
        const val = intersection.validation || {};
        const coords = intersection.coordinates || {};
        const isM91 = intersection.lotto === 'M9.1';
        const isOmnia = (intersection.system || '').toUpperCase() === 'OMNIA';

        // Title
        doc.setFontSize(18);
        doc.text('Scheda Sopralluogo', 105, 15, { align: 'center' });

        doc.setFontSize(14);
        doc.text(intersection.name || 'Sconosciuto', 105, 25, { align: 'center' });
        doc.setFontSize(10);
        doc.text(`Codice: ${intersection.id}`, 105, 32, { align: 'center' });

        let y = 45;

        const addSection = (title) => {
            doc.setFontSize(12);
            doc.setFont(undefined, 'bold');
            doc.setFillColor(37, 99, 235);
            doc.setTextColor(255, 255, 255);
            doc.rect(15, y - 5, 180, 8, 'F');
            doc.text(title, 20, y);
            doc.setTextColor(0, 0, 0);
            y += 10;
            doc.setFontSize(9);
        };

        const addLine = (label, value, indent = 20) => {
            doc.setFont(undefined, 'bold');
            doc.text(label + ':', indent, y);
            doc.setFont(undefined, 'normal');
            const valueText = String(value || 'N/A');
            doc.text(valueText.substring(0, 80), 80, y);
            y += 6;
        };

        const addStatusBadge = (label, status, indent = 20) => {
            doc.setFont(undefined, 'bold');
            doc.text(label + ':', indent, y);

            // Color based on status
            const colors = {
                completed: [34, 197, 94],
                in_progress: [59, 130, 246],
                blocked: [239, 68, 68],
                not_started: [156, 163, 175]
            };
            const color = colors[status] || colors.not_started;

            doc.setFillColor(color[0], color[1], color[2]);
            doc.rect(80, y - 4, 30, 5, 'F');
            doc.setTextColor(255, 255, 255);
            doc.setFontSize(8);
            doc.text(this.formatStatus(status), 82, y - 1);
            doc.setTextColor(0, 0, 0);
            doc.setFontSize(9);
            y += 6;
        };

        // General Information
        addSection('Informazioni Generali');
        addLine('Lotto', intersection.lotto);
        addLine('Sistema', intersection.system);
        addLine('Codice Impianto', intersection.codice_impianto);
        addLine('Numero Radar', intersection.num_radars);
        addLine('Coordinate', coords.lat && coords.lng ? `${coords.lat}, ${coords.lng}` : 'N/A');

        y += 3;
        addSection('Stato Fasi');
        addStatusBadge('Installazione', inst.status);
        addStatusBadge('Configurazione', conf.status);
        addStatusBadge('Connessione', conn.status);
        addStatusBadge('Validazione', val.status);

        y += 3;
        addSection('Dettagli Installazione');
        if (isM91) {
            addLine('L1 Planimetrie', inst.l1_planimetrie);
            addLine('L1 Passaggio Cavi', inst.l1_passaggio_cavi);
            addLine('L1 Installazione Sensori', inst.l1_install_sensori);
            addLine('L1 Cablaggio', inst.l1_cablaggio);
            addLine('L1 Screenshot', inst.l1_screenshot);
            addLine('L1 Doc Inviata', inst.l1_doc_inviata);
            addLine('L1 Data Completamento', inst.l1_data_compl);
        } else {
            addLine('L2 Data Installazione', inst.l2_data_installaz);
            addLine('L2 Config RSM', inst.l2_config_rsm);
            addLine('L2 Config Installata', inst.l2_config_instal);
            addLine('L2 Planimetria', inst.l2_planimetria);
            addLine('L2 N Radar Finiti', inst.l2_n_radar_finiti);
            addLine('L2 Centralizzati', inst.l2_centralizzati);
        }
        addLine('Dispositivi Bloccati', inst.disp_inst_bloccati);
        addLine('Dispositivi Da Installare', inst.disp_da_inst);
        addLine('Soluzione Bloccati', inst.soluzione_bloccati);

        // Check if we need a new page
        if (y > 240) {
            doc.addPage();
            y = 20;
        }

        y += 3;
        addSection('Dettagli Configurazione');
        addLine('Plan/Cfg Inviate', conf.plan_cfg_inviate);
        addLine('Cfg Definitiva Status', conf.cfg_def_status);
        addLine('Cfg Definitiva Installata', conf.cfg_def_inst);

        y += 3;
        addSection('Dettagli Connessione');
        addLine('Da Centralizzare AUT', conn.da_centr_aut);
        addLine('Tabella IF UTC', conn.tabella_if_utc);
        addLine('Interfaccia UTC Installata', conn.inst_interfaccia_utc);
        if (isOmnia) {
            addLine('SWARCO SPOT Status', conn.swarco_spot_status);
            addLine('SWARCO SPOT Firmware', conn.swarco_spot_firmware);
        } else {
            addLine('Semaforica AUT', conn.sema_aut);
            addLine('Semaforica Attivita', conn.sema_attivita);
        }

        // Check if we need a new page
        if (y > 240) {
            doc.addPage();
            y = 20;
        }

        y += 3;
        addSection('Dettagli Validazione');
        addLine('Verifica Dati', val.vrf_dati);

        // Notes section
        if (intersection.note_main || intersection.notes) {
            y += 3;
            addSection('Note');
            doc.setFont(undefined, 'normal');
            const notesText = [intersection.note_main, intersection.notes].filter(Boolean).join('\n');
            const splitNotes = doc.splitTextToSize(notesText, 170);
            doc.text(splitNotes, 20, y);
            y += splitNotes.length * 5;
        }

        // Issues warning
        if (intersection.inconsistencies && intersection.inconsistencies.length > 0) {
            if (y > 240) {
                doc.addPage();
                y = 20;
            }
            y += 3;
            doc.setFillColor(239, 68, 68);
            doc.rect(15, y - 5, 180, 8, 'F');
            doc.setTextColor(255, 255, 255);
            doc.setFontSize(12);
            doc.setFont(undefined, 'bold');
            doc.text('Problemi Dati', 20, y);
            doc.setTextColor(0, 0, 0);
            y += 10;
            doc.setFontSize(9);

            intersection.inconsistencies.forEach(inc => {
                doc.setFont(undefined, 'normal');
                const text = `- ${inc.type}: ${inc.message || ''}`;
                doc.text(text.substring(0, 90), 20, y);
                y += 6;
            });
        }

        // Field work checklist
        if (y > 200) {
            doc.addPage();
            y = 20;
        }
        y += 10;
        addSection('Checklist Sopralluogo');
        const checklistItems = [
            'Verifica installazione fisica',
            'Controlla posizione sensori',
            'Test connessioni',
            'Documentazione fotografica',
            'Aggiorna configurazione',
            'Firma: ________________'
        ];
        checklistItems.forEach(item => {
            doc.rect(20, y - 3, 4, 4);
            doc.text(item, 28, y);
            y += 7;
        });

        // Footer
        doc.setFontSize(8);
        doc.setTextColor(128, 128, 128);
        doc.text(`Generato: ${new Date().toLocaleString('it-IT')}`, 20, 285);
        doc.text('Gestione Progetto Installazione Radar', 105, 285, { align: 'center' });

        // Save
        doc.save(`scheda_sopralluogo_${intersection.id}_${new Date().toISOString().split('T')[0]}.pdf`);
    },

    /**
     * Export filtered data
     */
    exportFiltered() {
        const intersections = DataManager.getIntersections();

        // Get filter options
        const lottoM91 = document.getElementById('export-filter-lotto-m91')?.checked;
        const lottoM92 = document.getElementById('export-filter-lotto-m92')?.checked;
        const blockedOnly = document.getElementById('export-filter-blocked')?.checked;
        const issuesOnly = document.getElementById('export-filter-issues')?.checked;

        let filtered = intersections;

        if (lottoM91 && !lottoM92) {
            filtered = filtered.filter(i => i.lotto === 'M9.1');
        } else if (lottoM92 && !lottoM91) {
            filtered = filtered.filter(i => i.lotto === 'M9.2');
        }

        if (blockedOnly) {
            filtered = filtered.filter(i => {
                const inst = i.installation || {};
                const conf = i.configuration || {};
                const conn = i.connection || {};
                const val = i.validation || {};
                return inst.status === 'blocked' ||
                    conf.status === 'blocked' ||
                    conn.status === 'blocked' ||
                    val.status === 'blocked';
            });
        }

        if (issuesOnly) {
            filtered = filtered.filter(i => i.inconsistencies && i.inconsistencies.length > 0);
        }

        if (filtered.length === 0) {
            alert('Nessuna intersezione corrisponde ai filtri selezionati');
            return;
        }

        // Export filtered data
        const data = filtered.map(i => {
            const inst = i.installation || {};
            const conf = i.configuration || {};
            const conn = i.connection || {};
            const val = i.validation || {};

            return {
                'Codice': i.id,
                'Nome': i.name || '',
                'Lotto': i.lotto || '',
                'Sistema': i.system || '',
                'Radar': i.num_radars || 0,
                'Installazione': this.formatStatus(inst.status),
                'Configurazione': this.formatStatus(conf.status),
                'Connessione': this.formatStatus(conn.status),
                'Validazione': this.formatStatus(val.status),
                'Problemi': i.inconsistencies?.length || 0
            };
        });

        const wb = XLSX.utils.book_new();
        const ws = XLSX.utils.json_to_sheet(data);
        XLSX.utils.book_append_sheet(wb, ws, 'Export Filtrato');

        XLSX.writeFile(wb, `radar_export_filtrato_${new Date().toISOString().split('T')[0]}.xlsx`);
    },

    /**
     * Import files for an intersection
     */
    importFiles() {
        const select = document.getElementById('import-intersection-select');
        if (!select || !select.value) {
            alert('Seleziona un\'intersezione');
            return;
        }

        const intersectionId = select.value;
        const intersection = DataManager.getIntersection(intersectionId);
        if (!intersection) {
            alert('Intersezione non trovata');
            return;
        }

        const planimetryInput = document.getElementById('import-planimetry');
        const photosInput = document.getElementById('import-photos');

        const updates = {};

        // Handle planimetry file
        if (planimetryInput && planimetryInput.files.length > 0) {
            const file = planimetryInput.files[0];
            // Store file reference path (in real app would upload to server)
            updates.planimetry_file = `files/${intersectionId}/planimetry/${file.name}`;
        }

        // Handle photo files
        if (photosInput && photosInput.files.length > 0) {
            const photoFiles = [];
            for (let i = 0; i < photosInput.files.length; i++) {
                const file = photosInput.files[i];
                photoFiles.push(`files/${intersectionId}/photos/${file.name}`);
            }
            updates.photo_files = [...(intersection.photo_files || []), ...photoFiles];
        }

        if (Object.keys(updates).length === 0) {
            alert('Seleziona almeno un file da importare');
            return;
        }

        // Update intersection with file references
        DataManager.updateIntersection(intersectionId, updates);

        alert('Riferimenti file aggiunti con successo!\n\nNota: In un ambiente di produzione, i file verrebbero caricati su un server. Attualmente vengono memorizzati solo i riferimenti ai percorsi.');

        // Clear inputs
        if (planimetryInput) planimetryInput.value = '';
        if (photosInput) photosInput.value = '';
    },

    /**
     * Format status for display
     */
    formatStatus(status) {
        const labels = {
            completed: 'Completato',
            in_progress: 'In Corso',
            blocked: 'Bloccato',
            not_started: 'Non Iniziato'
        };
        return labels[status] || status || 'Sconosciuto';
    },

    /**
     * Trigger file restore
     */
    triggerRestore() {
        const input = document.createElement('input');
        input.type = 'file';
        input.accept = '.json';
        input.onchange = async (e) => {
            const file = e.target.files[0];
            if (file) {
                try {
                    await DataManager.restoreBackup(file);
                    alert('Dati ripristinati con successo! Aggiornamento...');
                    window.location.reload();
                } catch (err) {
                    alert('Errore nel ripristino del backup: ' + err.message);
                }
            }
        };
        input.click();
    }
};
