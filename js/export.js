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
            siteVisitSelect.innerHTML = '<option value="">Select intersection...</option>' +
                intersections.map(i => `<option value="${i.id}">${i.id} - ${i.name || 'Unknown'}</option>`).join('');
        }

        // Import intersection select
        const importSelect = document.getElementById('import-intersection-select');
        if (importSelect) {
            importSelect.innerHTML = '<option value="">Select intersection...</option>' +
                intersections.map(i => `<option value="${i.id}">${i.id} - ${i.name || 'Unknown'}</option>`).join('');
        }
    },

    /**
     * Export full data to Excel with all stage details
     */
    exportFullExcel() {
        const intersections = DataManager.getIntersections();

        // Main data sheet with all stage statuses
        const mainData = intersections.map(i => ({
            'Code': i.id,
            'Name': i.name || '',
            'Lotto': i.lotto || '',
            'System': i.system || '',
            'Num Radars': i.num_radars || 0,
            'Latitude': i.latitude || '',
            'Longitude': i.longitude || '',
            // Stage statuses
            'Installation Status': this.formatStatus(i.installation_status),
            'Configuration Status': this.formatStatus(i.configuration_status),
            'Connection Status': this.formatStatus(i.connection_status),
            'Validation Status': this.formatStatus(i.validation_status),
            // Installation substages
            'Planimetrie Ricevute': i.installation?.planimetrie_ricevute || '',
            'Passaggio Cavi': i.installation?.passaggio_cavi || '',
            'Planimetria Scavi Inviata': i.installation?.planimetria_scavi_inviata || '',
            'Installazione Sensori': i.installation?.installazione_sensori || '',
            'Cablaggio Regolatore': i.installation?.cablaggio_regolatore || '',
            'Screenshot': i.installation?.screenshot || '',
            'Installation Completato': i.installation?.completato || '',
            'Documentazione Inviata': i.installation?.documentazione_inviata || '',
            'Data Completamento': i.installation?.data_completamento || '',
            // Configuration substages
            'Configurazione Base': i.configuration?.base || '',
            'Config Definitiva Assegnata': i.configuration?.definitiva_assegnata || '',
            'Config Definitiva Da Verificare': i.configuration?.definitiva_da_verificare || '',
            'Config Implementata Sito': i.configuration?.implementata_sito || '',
            // Connection substages
            'SPOT Status': i.connection?.spot_status || '',
            'AUT Status': i.connection?.aut_status || '',
            'Tabella Interfaccia UTC': i.connection?.tabella_interfaccia_utc || '',
            'Connessione UTC Attiva': i.connection?.connessione_utc_attiva || '',
            // Validation substages
            'Data Lake Sending': i.validation?.data_lake_sending || '',
            'Verifica Dati Traffic': i.validation?.verifica_dati_traffic || '',
            'Interfaccia Visum Optima': i.validation?.interfaccia_visum_optima || '',
            // Files and notes
            'Planimetry File': i.planimetry_file || '',
            'Photo Files': i.photo_files?.join('; ') || '',
            'Notes': i.notes || '',
            'Issues Count': i.inconsistencies?.length || 0
        }));

        // Create workbook
        const wb = XLSX.utils.book_new();
        const ws = XLSX.utils.json_to_sheet(mainData);
        XLSX.utils.book_append_sheet(wb, ws, 'Intersections');

        // Tasks sheet
        const tasks = DataManager.getTasks();
        if (tasks.length > 0) {
            const tasksData = tasks.map(t => ({
                'ID': t.id,
                'Title': t.title,
                'Description': t.description || '',
                'Intersection': t.intersection_id || '',
                'Stage': t.stage || '',
                'Substage': t.substage || '',
                'Assignee': t.assignee || '',
                'Status': t.status,
                'Priority': t.priority,
                'Created': t.created_at,
                'Updated': t.updated_at
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
                        'Intersection Code': i.id,
                        'Intersection Name': i.name || '',
                        'Issue Type': inc.type,
                        'Message': inc.message || '',
                        'Field': inc.field || '',
                        'Expected Value': inc.main_value || '',
                        'Actual Value': inc.lotto_value || ''
                    });
                });
            }
        });

        if (issues.length > 0) {
            const issuesWs = XLSX.utils.json_to_sheet(issues);
            XLSX.utils.book_append_sheet(wb, issuesWs, 'Issues');
        }

        // Download
        const filename = `radar_full_export_${new Date().toISOString().split('T')[0]}.xlsx`;
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
        doc.text('Radar Project - Full Export', 148, 15, { align: 'center' });
        doc.setFontSize(10);
        doc.text(`Generated: ${new Date().toLocaleString('it-IT')}`, 148, 22, { align: 'center' });

        // Summary table
        const tableData = intersections.map(i => [
            i.id,
            (i.name || '').substring(0, 25),
            i.lotto || '',
            i.num_radars || 0,
            this.formatStatus(i.installation_status),
            this.formatStatus(i.configuration_status),
            this.formatStatus(i.connection_status),
            this.formatStatus(i.validation_status)
        ]);

        doc.autoTable({
            startY: 30,
            head: [['Code', 'Name', 'Lotto', 'Radars', 'Installation', 'Configuration', 'Connection', 'Validation']],
            body: tableData,
            styles: { fontSize: 8 },
            headStyles: { fillColor: [37, 99, 235] },
            alternateRowStyles: { fillColor: [241, 245, 249] }
        });

        // Download
        const filename = `radar_full_export_${new Date().toISOString().split('T')[0]}.pdf`;
        doc.save(filename);
    },

    /**
     * Export site visit sheet for an intersection
     */
    exportSiteVisitSheet() {
        const select = document.getElementById('export-intersection-select');
        if (!select || !select.value) {
            alert('Please select an intersection');
            return;
        }

        const intersection = DataManager.getIntersection(select.value);
        if (!intersection) {
            alert('Intersection not found');
            return;
        }

        const { jsPDF } = window.jspdf;
        const doc = new jsPDF();

        // Title
        doc.setFontSize(18);
        doc.text('Site Visit Sheet', 105, 15, { align: 'center' });

        doc.setFontSize(14);
        doc.text(intersection.name || 'Unknown', 105, 25, { align: 'center' });
        doc.setFontSize(10);
        doc.text(`Code: ${intersection.id}`, 105, 32, { align: 'center' });

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
        addSection('General Information');
        addLine('Lotto', intersection.lotto);
        addLine('System', intersection.system);
        addLine('Number of Radars', intersection.num_radars);
        addLine('Coordinates', `${intersection.latitude || 'N/A'}, ${intersection.longitude || 'N/A'}`);

        y += 3;
        addSection('Stage Status Overview');
        addStatusBadge('Installation', intersection.installation_status);
        addStatusBadge('Configuration', intersection.configuration_status);
        addStatusBadge('Connection', intersection.connection_status);
        addStatusBadge('Validation', intersection.validation_status);

        y += 3;
        addSection('Installation Details');
        addLine('Planimetrie Ricevute', intersection.installation?.planimetrie_ricevute);
        addLine('Passaggio Cavi', intersection.installation?.passaggio_cavi);
        addLine('Installazione Sensori', intersection.installation?.installazione_sensori);
        addLine('Cablaggio Regolatore', intersection.installation?.cablaggio_regolatore);
        addLine('Screenshot', intersection.installation?.screenshot);
        addLine('Documentazione Inviata', intersection.installation?.documentazione_inviata);
        addLine('Data Completamento', intersection.installation?.data_completamento);

        // Check if we need a new page
        if (y > 240) {
            doc.addPage();
            y = 20;
        }

        y += 3;
        addSection('Configuration Details');
        addLine('Configurazione Base', intersection.configuration?.base);
        addLine('Config Definitiva Assegnata', intersection.configuration?.definitiva_assegnata);
        addLine('Config Definitiva Da Verificare', intersection.configuration?.definitiva_da_verificare);
        addLine('Config Implementata Sito', intersection.configuration?.implementata_sito);

        y += 3;
        addSection('Connection Details');
        addLine('SPOT Status', intersection.connection?.spot_status);
        addLine('AUT Status', intersection.connection?.aut_status);
        addLine('Tabella Interfaccia UTC', intersection.connection?.tabella_interfaccia_utc);
        addLine('Connessione UTC Attiva', intersection.connection?.connessione_utc_attiva);

        // Check if we need a new page
        if (y > 240) {
            doc.addPage();
            y = 20;
        }

        y += 3;
        addSection('Validation Details');
        addLine('Data Lake Sending', intersection.validation?.data_lake_sending);
        addLine('Verifica Dati Traffic', intersection.validation?.verifica_dati_traffic);
        addLine('Interfaccia Visum/Optima', intersection.validation?.interfaccia_visum_optima);

        // Files section
        if (intersection.planimetry_file || (intersection.photo_files && intersection.photo_files.length > 0)) {
            y += 3;
            addSection('Attached Files');
            if (intersection.planimetry_file) {
                addLine('Planimetry', intersection.planimetry_file);
            }
            if (intersection.photo_files && intersection.photo_files.length > 0) {
                intersection.photo_files.forEach((photo, idx) => {
                    addLine(`Photo ${idx + 1}`, photo);
                });
            }
        }

        // Notes section
        if (intersection.notes) {
            y += 3;
            addSection('Notes');
            doc.setFont(undefined, 'normal');
            const splitNotes = doc.splitTextToSize(intersection.notes, 170);
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
            doc.text('Data Issues', 20, y);
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
        addSection('Field Work Checklist');
        const checklistItems = [
            'Verify physical installation',
            'Check sensor positions',
            'Test connections',
            'Document with photos',
            'Update configuration',
            'Signature: ________________'
        ];
        checklistItems.forEach(item => {
            doc.rect(20, y - 3, 4, 4);
            doc.text(item, 28, y);
            y += 7;
        });

        // Footer
        doc.setFontSize(8);
        doc.setTextColor(128, 128, 128);
        doc.text(`Generated: ${new Date().toLocaleString('it-IT')}`, 20, 285);
        doc.text('Radar Installation Project Management', 105, 285, { align: 'center' });

        // Save
        doc.save(`site_visit_${intersection.id}_${new Date().toISOString().split('T')[0]}.pdf`);
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
            filtered = filtered.filter(i =>
                i.installation_status === 'blocked' ||
                i.configuration_status === 'blocked' ||
                i.connection_status === 'blocked' ||
                i.validation_status === 'blocked'
            );
        }

        if (issuesOnly) {
            filtered = filtered.filter(i => i.inconsistencies && i.inconsistencies.length > 0);
        }

        if (filtered.length === 0) {
            alert('No intersections match the selected filters');
            return;
        }

        // Export filtered data
        const data = filtered.map(i => ({
            'Code': i.id,
            'Name': i.name || '',
            'Lotto': i.lotto || '',
            'System': i.system || '',
            'Radars': i.num_radars || 0,
            'Installation': this.formatStatus(i.installation_status),
            'Configuration': this.formatStatus(i.configuration_status),
            'Connection': this.formatStatus(i.connection_status),
            'Validation': this.formatStatus(i.validation_status),
            'Issues': i.inconsistencies?.length || 0
        }));

        const wb = XLSX.utils.book_new();
        const ws = XLSX.utils.json_to_sheet(data);
        XLSX.utils.book_append_sheet(wb, ws, 'Filtered Export');

        XLSX.writeFile(wb, `radar_filtered_export_${new Date().toISOString().split('T')[0]}.xlsx`);
    },

    /**
     * Import files for an intersection
     */
    importFiles() {
        const select = document.getElementById('import-intersection-select');
        if (!select || !select.value) {
            alert('Please select an intersection');
            return;
        }

        const intersectionId = select.value;
        const intersection = DataManager.getIntersection(intersectionId);
        if (!intersection) {
            alert('Intersection not found');
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
            alert('Please select at least one file to import');
            return;
        }

        // Update intersection with file references
        DataManager.updateIntersection(intersectionId, updates);

        alert('File references added successfully!\n\nNote: In a production environment, files would be uploaded to a server. Currently storing file path references only.');

        // Clear inputs
        if (planimetryInput) planimetryInput.value = '';
        if (photosInput) photosInput.value = '';
    },

    /**
     * Format status for display
     */
    formatStatus(status) {
        const labels = {
            completed: 'Completed',
            in_progress: 'In Progress',
            blocked: 'Blocked',
            not_started: 'Not Started'
        };
        return labels[status] || status || 'Unknown';
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
                    alert('Data restored successfully! Refreshing...');
                    window.location.reload();
                } catch (err) {
                    alert('Error restoring backup: ' + err.message);
                }
            }
        };
        input.click();
    }
};
