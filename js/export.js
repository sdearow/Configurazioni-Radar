/**
 * Export Module
 * Handles data export to Excel, PDF, and JSON formats
 */

const ExportManager = {
    /**
     * Initialize export module
     */
    init() {
        this.bindEvents();
        this.populateIntersectionSelect();
        return this;
    },

    /**
     * Bind event listeners
     */
    bindEvents() {
        // Excel export
        const excelBtn = document.getElementById('export-excel');
        if (excelBtn) {
            excelBtn.addEventListener('click', () => this.exportToExcel());
        }

        // JSON export
        const jsonBtn = document.getElementById('export-json');
        if (jsonBtn) {
            jsonBtn.addEventListener('click', () => this.exportToJSON());
        }

        // Site visit PDF
        const siteVisitBtn = document.getElementById('export-site-visit');
        if (siteVisitBtn) {
            siteVisitBtn.addEventListener('click', () => this.exportSiteVisitPDF());
        }

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

        // Import
        const importBtn = document.getElementById('import-btn');
        if (importBtn) {
            importBtn.addEventListener('click', () => this.importFile());
        }
    },

    /**
     * Populate intersection select for site visit export
     */
    populateIntersectionSelect() {
        const select = document.getElementById('export-intersection-select');
        if (!select) return;

        const intersections = DataManager.getIntersections();
        select.innerHTML = intersections
            .map(i => `<option value="${i.id}">${i.id} - ${i.name}</option>`)
            .join('');
    },

    /**
     * Export all data to Excel
     */
    exportToExcel() {
        const intersections = DataManager.getIntersections();

        // Flatten data for Excel
        const data = intersections.map(i => ({
            'Code': i.id,
            'Name': i.name,
            'Lotto': i.lotto,
            'System': i.system,
            'Num Radars': i.num_radars,
            'Current Stage': i.current_stage,
            'Stage Status': i.stage_status,
            'Planimetry Sent': i.installation?.planimetry_sent ? 'Yes' : 'No',
            'Blocked Conduits': i.installation?.blocked_conduits ? 'Yes' : 'No',
            'Blocked Solution': i.installation?.blocked_solution || '',
            'Config Status': i.configuration?.status || '',
            'Config Installed': i.configuration?.installed || '',
            'UTC Table': i.connection?.utc_table || '',
            'UTC Interface': i.connection?.utc_interface || '',
            'Data Verified': i.validation?.data_verified || '',
            'Notes': i.notes || '',
            'Inconsistencies': i.inconsistencies?.length || 0,
            'Data Sources': i.data_sources?.join(', ') || ''
        }));

        // Create workbook
        const ws = XLSX.utils.json_to_sheet(data);
        const wb = XLSX.utils.book_new();
        XLSX.utils.book_append_sheet(wb, ws, 'Intersections');

        // Add tasks sheet
        const tasks = DataManager.getTasks();
        if (tasks.length > 0) {
            const tasksData = tasks.map(t => ({
                'ID': t.id,
                'Title': t.title,
                'Description': t.description || '',
                'Intersection': t.intersection_id || '',
                'Assignee': t.assignee || '',
                'Status': t.status,
                'Priority': t.priority,
                'Due Date': t.due_date || '',
                'Created': t.created_at,
                'Updated': t.updated_at
            }));
            const tasksWs = XLSX.utils.json_to_sheet(tasksData);
            XLSX.utils.book_append_sheet(wb, tasksWs, 'Tasks');
        }

        // Add inconsistencies sheet
        const inconsistencies = [];
        intersections.forEach(i => {
            if (i.inconsistencies && i.inconsistencies.length > 0) {
                i.inconsistencies.forEach(inc => {
                    inconsistencies.push({
                        'Intersection Code': i.id,
                        'Intersection Name': i.name,
                        'Type': inc.type,
                        'Message': inc.message || '',
                        'Field': inc.field || '',
                        'Main Value': inc.main_value || '',
                        'Other Value': inc.lotto_value || ''
                    });
                });
            }
        });

        if (inconsistencies.length > 0) {
            const incWs = XLSX.utils.json_to_sheet(inconsistencies);
            XLSX.utils.book_append_sheet(wb, incWs, 'Inconsistencies');
        }

        // Download
        const filename = `radar_export_${new Date().toISOString().split('T')[0]}.xlsx`;
        XLSX.writeFile(wb, filename);
    },

    /**
     * Export all data to JSON
     */
    exportToJSON() {
        const json = DataManager.exportJSON();
        const blob = new Blob([json], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `radar_export_${new Date().toISOString().split('T')[0]}.json`;
        a.click();
        URL.revokeObjectURL(url);
    },

    /**
     * Export site visit PDF for an intersection
     */
    exportSiteVisitPDF() {
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

        // Use jsPDF
        const { jsPDF } = window.jspdf;
        const doc = new jsPDF();

        // Title
        doc.setFontSize(18);
        doc.text('Site Visit Sheet', 105, 20, { align: 'center' });

        doc.setFontSize(14);
        doc.text(intersection.name, 105, 30, { align: 'center' });

        // Basic info
        doc.setFontSize(10);
        let y = 45;

        const addLine = (label, value) => {
            doc.setFont(undefined, 'bold');
            doc.text(label + ':', 20, y);
            doc.setFont(undefined, 'normal');
            doc.text(String(value || 'N/A'), 70, y);
            y += 7;
        };

        doc.setFontSize(12);
        doc.setFont(undefined, 'bold');
        doc.text('General Information', 20, y);
        y += 10;
        doc.setFontSize(10);

        addLine('Code', intersection.id);
        addLine('Lotto', intersection.lotto);
        addLine('System', intersection.system);
        addLine('Number of Radars', intersection.num_radars);
        addLine('Current Stage', intersection.current_stage);
        addLine('Stage Status', intersection.stage_status);

        y += 5;
        doc.setFontSize(12);
        doc.setFont(undefined, 'bold');
        doc.text('Installation Status', 20, y);
        y += 10;
        doc.setFontSize(10);

        addLine('Planimetry Sent', intersection.installation?.planimetry_sent ? 'Yes' : 'No');
        addLine('Blocked Conduits', intersection.installation?.blocked_conduits ? 'Yes' : 'No');
        if (intersection.installation?.blocked_solution) {
            addLine('Solution', intersection.installation.blocked_solution);
        }

        y += 5;
        doc.setFontSize(12);
        doc.setFont(undefined, 'bold');
        doc.text('Configuration Status', 20, y);
        y += 10;
        doc.setFontSize(10);

        addLine('Config Status', intersection.configuration?.status);
        addLine('Config Installed', intersection.configuration?.installed);
        addLine('AUT Status', intersection.configuration?.aut_status);

        y += 5;
        doc.setFontSize(12);
        doc.setFont(undefined, 'bold');
        doc.text('Connection Status', 20, y);
        y += 10;
        doc.setFontSize(10);

        addLine('UTC Table', intersection.connection?.utc_table);
        addLine('UTC Interface', intersection.connection?.utc_interface);

        // Radars
        if (intersection.radars && intersection.radars.length > 0) {
            y += 5;
            doc.setFontSize(12);
            doc.setFont(undefined, 'bold');
            doc.text('Individual Radars', 20, y);
            y += 10;
            doc.setFontSize(10);

            intersection.radars.forEach((radar, index) => {
                addLine(`Radar ${index + 1}`, `ID: ${radar.id}, Status: ${radar.status}`);
            });
        }

        // Notes
        if (intersection.notes) {
            y += 5;
            doc.setFontSize(12);
            doc.setFont(undefined, 'bold');
            doc.text('Notes', 20, y);
            y += 10;
            doc.setFontSize(10);
            doc.setFont(undefined, 'normal');

            const splitNotes = doc.splitTextToSize(intersection.notes, 170);
            doc.text(splitNotes, 20, y);
            y += splitNotes.length * 5;
        }

        // Inconsistencies warning
        if (intersection.inconsistencies && intersection.inconsistencies.length > 0) {
            y += 10;
            doc.setFontSize(12);
            doc.setFont(undefined, 'bold');
            doc.setTextColor(255, 0, 0);
            doc.text('Data Inconsistencies', 20, y);
            y += 10;
            doc.setFontSize(10);
            doc.setTextColor(0, 0, 0);

            intersection.inconsistencies.forEach(inc => {
                doc.setFont(undefined, 'normal');
                doc.text(`- ${inc.type}: ${inc.message || ''}`, 20, y);
                y += 7;
            });
        }

        // Footer
        doc.setFontSize(8);
        doc.setTextColor(128, 128, 128);
        doc.text(`Generated: ${new Date().toLocaleString('it-IT')}`, 20, 285);
        doc.text('Radar Project Management - Roma', 105, 285, { align: 'center' });

        // Save
        doc.save(`site_visit_${intersection.id}_${new Date().toISOString().split('T')[0]}.pdf`);
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
    },

    /**
     * Import file
     */
    importFile() {
        const fileInput = document.getElementById('import-file');
        if (!fileInput || !fileInput.files[0]) {
            alert('Please select a file to import');
            return;
        }

        const file = fileInput.files[0];
        const reader = new FileReader();

        reader.onload = (e) => {
            try {
                if (file.name.endsWith('.json')) {
                    // JSON import
                    if (DataManager.importJSON(e.target.result)) {
                        alert('Data imported successfully! Refreshing...');
                        window.location.reload();
                    } else {
                        alert('Error importing JSON data');
                    }
                } else if (file.name.endsWith('.xlsx') || file.name.endsWith('.xls')) {
                    // Excel import (basic)
                    alert('Excel import is not yet fully implemented. Please use JSON for now.');
                }
            } catch (err) {
                alert('Error importing file: ' + err.message);
            }
        };

        if (file.name.endsWith('.json')) {
            reader.readAsText(file);
        } else {
            reader.readAsArrayBuffer(file);
        }
    }
};
