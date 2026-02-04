/**
 * Main Application Module
 * Coordinates all other modules and handles UI interactions
 */

const App = {
    currentTab: 'map',
    currentFilters: {
        lotto: ['M9.1', 'M9.2'],
        system: ['Omnia', 'Tmacs'],
        search: '',
        hasIssues: false,
        showActiveTasks: false,
        overallStatus: ''
    },
    colorByStage: 'installation',

    // Substages for each stage
    substages: {
        installation: [
            { key: 'planimetry_received', label: 'Planimetry Received' },
            { key: 'cable_passage', label: 'Cable Passage' },
            { key: 'planimetry_sent_rsm', label: 'Planimetry Sent to RSM' },
            { key: 'sensor_installation', label: 'Sensor Installation' },
            { key: 'regulator_wiring', label: 'Regulator Wiring' },
            { key: 'screenshot', label: 'Screenshot' },
            { key: 'documentation_sent', label: 'Documentation Sent' },
            { key: 'completion_date', label: 'Completion Date' }
        ],
        configuration: [
            { key: 'config_sent', label: 'Config Sent' },
            { key: 'base_config', label: 'Base Configuration' },
            { key: 'definitive_config', label: 'Definitive Config' },
            { key: 'config_installed', label: 'Config Installed' }
        ],
        connection: [
            { key: 'utc_table', label: 'UTC Table' },
            { key: 'utc_table_sent', label: 'UTC Table Sent' },
            { key: 'utc_interface', label: 'UTC Interface' },
            { key: 'spot_status', label: 'SPOT Status' },
            { key: 'aut_status', label: 'AUT Status' }
        ],
        validation: [
            { key: 'data_verified', label: 'Data Verified' },
            { key: 'sending_to_datalake', label: 'Sending to DataLake' },
            { key: 'traffic_data_verified', label: 'Traffic Data Verified' },
            { key: 'visum_optima_interface', label: 'Visum/Optima Interface' }
        ]
    },

    /**
     * Initialize the application
     */
    async init() {
        console.log('Initializing Radar Installation Project Management...');

        // Initialize data
        await DataManager.init();

        // Initialize modules
        MapManager.init();
        ChartsManager.init();
        TasksManager.init();
        ExportManager.init();

        // Bind events
        this.bindEvents();

        // Update header stats
        this.updateHeaderStats();

        // Initial render
        this.renderCurrentTab();

        console.log('Application initialized successfully');
    },

    /**
     * Bind event listeners
     */
    bindEvents() {
        // Tab navigation
        document.querySelectorAll('.nav-tab').forEach(tab => {
            tab.addEventListener('click', (e) => {
                this.switchTab(e.target.dataset.tab);
            });
        });

        // Map color by stage dropdown
        document.getElementById('color-by-stage')?.addEventListener('change', (e) => {
            this.colorByStage = e.target.value;
            this.renderMap();
        });

        // Checkbox filters
        document.querySelectorAll('input[name="lotto"]').forEach(cb => {
            cb.addEventListener('change', () => this.updateFiltersFromCheckboxes());
        });

        document.querySelectorAll('input[name="system"]').forEach(cb => {
            cb.addEventListener('change', () => this.updateFiltersFromCheckboxes());
        });

        document.getElementById('show-issues-only')?.addEventListener('change', (e) => {
            this.currentFilters.hasIssues = e.target.checked;
            this.renderMap();
        });

        document.getElementById('show-active-tasks')?.addEventListener('change', (e) => {
            this.currentFilters.showActiveTasks = e.target.checked;
            this.renderMap();
        });

        // Edit mode button for map markers
        document.getElementById('edit-mode-btn')?.addEventListener('click', () => {
            MapManager.toggleEditMode();
        });

        // Search
        document.getElementById('search-input')?.addEventListener('input', (e) => {
            this.currentFilters.search = e.target.value;
            this.renderList();
        });

        // List filters
        document.getElementById('list-filter-lotto')?.addEventListener('change', () => this.renderList());
        document.getElementById('list-filter-system')?.addEventListener('change', () => this.renderList());
        document.getElementById('list-filter-status')?.addEventListener('change', () => this.renderList());

        // Issue type filter
        document.getElementById('issue-type-filter')?.addEventListener('change', () => this.renderIssues());
        document.getElementById('show-geocoding-issues')?.addEventListener('click', () => {
            document.getElementById('issue-type-filter').value = 'geocoding_uncertain';
            this.renderIssues();
        });

        // Modal close buttons
        document.querySelectorAll('.modal-close').forEach(btn => {
            btn.addEventListener('click', () => this.closeModals());
        });

        // Click outside modal to close
        document.querySelectorAll('.modal').forEach(modal => {
            modal.addEventListener('click', (e) => {
                if (e.target === modal) {
                    this.closeModals();
                }
            });
        });

        // Modal save button
        document.getElementById('modal-save')?.addEventListener('click', () => this.saveIntersectionChanges());

        // Task modal
        document.getElementById('add-task-btn')?.addEventListener('click', () => TasksManager.showAddTaskModal());
        document.getElementById('batch-task-btn')?.addEventListener('click', () => TasksManager.showBatchTaskModal());
        document.getElementById('save-task-btn')?.addEventListener('click', () => TasksManager.saveTask());
        document.getElementById('save-batch-tasks-btn')?.addEventListener('click', () => TasksManager.saveBatchTasks());

        // Task stage change updates substages
        document.getElementById('task-stage')?.addEventListener('change', (e) => {
            this.populateSubstages(e.target.value, 'task-substage');
        });
    },

    /**
     * Populate substage dropdown based on selected stage
     */
    populateSubstages(stage, selectId) {
        const select = document.getElementById(selectId);
        if (!select) return;

        select.innerHTML = '<option value="">Select substage...</option>';

        const substages = this.substages[stage] || [];
        substages.forEach(sub => {
            const option = document.createElement('option');
            option.value = sub.key;
            option.textContent = sub.label;
            select.appendChild(option);
        });
    },

    /**
     * Update filters from checkboxes
     */
    updateFiltersFromCheckboxes() {
        this.currentFilters.lotto = Array.from(document.querySelectorAll('input[name="lotto"]:checked')).map(cb => cb.value);
        this.currentFilters.system = Array.from(document.querySelectorAll('input[name="system"]:checked')).map(cb => cb.value);
        this.renderMap();
    },

    /**
     * Switch to a different tab
     */
    switchTab(tabName) {
        this.currentTab = tabName;

        // Update nav tabs
        document.querySelectorAll('.nav-tab').forEach(tab => {
            tab.classList.toggle('active', tab.dataset.tab === tabName);
        });

        // Update tab content
        document.querySelectorAll('.tab-content').forEach(content => {
            content.classList.toggle('active', content.id === tabName + '-tab');
        });

        // Render tab content
        this.renderCurrentTab();
    },

    /**
     * Render content for current tab
     */
    renderCurrentTab() {
        switch (this.currentTab) {
            case 'map':
                setTimeout(() => MapManager.resize(), 100);
                this.renderMap();
                break;
            case 'dashboard':
                this.renderDashboard();
                break;
            case 'list':
                this.renderList();
                break;
            case 'issues':
                this.renderIssues();
                break;
            case 'tasks':
                TasksManager.render();
                break;
            case 'export':
                ExportManager.populateIntersectionSelect();
                break;
        }
    },

    /**
     * Update header statistics
     */
    updateHeaderStats() {
        const summary = DataManager.getSummary();

        document.getElementById('total-intersections').textContent = summary.total_intersections || 0;
        document.getElementById('total-radars').textContent = summary.total_radars || 0;
        document.getElementById('fully-working').textContent = summary.fully_working || 0;
    },

    /**
     * Render map view
     */
    renderMap() {
        const filtered = DataManager.filterIntersections(this.currentFilters);
        MapManager.renderMarkers(filtered, this.colorByStage);
    },

    /**
     * Render dashboard
     */
    renderDashboard() {
        const intersections = DataManager.getIntersections();
        const summary = DataManager.getSummary();
        ChartsManager.renderDashboard(intersections, summary);
    },

    /**
     * Render intersection list with 4 stage columns
     */
    renderList() {
        const filters = {
            search: document.getElementById('search-input')?.value || '',
            lotto: [],
            system: [],
            overallStatus: ''
        };

        const lottoFilter = document.getElementById('list-filter-lotto')?.value;
        if (lottoFilter) filters.lotto = [lottoFilter];

        const systemFilter = document.getElementById('list-filter-system')?.value;
        if (systemFilter) filters.system = [systemFilter];

        const statusFilter = document.getElementById('list-filter-status')?.value;
        if (statusFilter) filters.overallStatus = statusFilter;

        const intersections = DataManager.filterIntersections(filters);
        const tbody = document.getElementById('intersection-list');
        if (!tbody) return;

        tbody.innerHTML = intersections.map(i => {
            const instStatus = i.installation?.status || 'not_started';
            const confStatus = i.configuration?.status || 'not_started';
            const connStatus = i.connection?.status || 'not_started';
            const valStatus = i.validation?.status || 'not_started';

            const issueCount = i.inconsistencies?.length || 0;
            const isBlocked = i.installation?.blocked_conduits;

            return `
                <tr>
                    <td>${i.id}</td>
                    <td>${this.escapeHtml(i.name)}</td>
                    <td>${i.lotto || '-'}</td>
                    <td>${i.num_radars || 0}</td>
                    <td><span class="status-badge status-${instStatus}">${this.formatStatus(instStatus)}</span></td>
                    <td><span class="status-badge status-${confStatus}">${this.formatStatus(confStatus)}</span></td>
                    <td><span class="status-badge status-${connStatus}">${this.formatStatus(connStatus)}</span></td>
                    <td><span class="status-badge status-${valStatus}">${this.formatStatus(valStatus)}</span></td>
                    <td>
                        ${issueCount > 0 ? `<span class="badge badge-warning">${issueCount}</span>` : ''}
                        ${isBlocked ? '<span class="badge badge-danger">Blocked</span>' : ''}
                        ${issueCount === 0 && !isBlocked ? '-' : ''}
                    </td>
                    <td class="actions-cell">
                        <button class="btn btn-small btn-primary" onclick="App.showIntersectionDetail('${i.id}')">View</button>
                        <button class="btn btn-small btn-secondary" onclick="MapManager.focusIntersection('${i.id}'); App.switchTab('map');">Map</button>
                        <button class="btn btn-small btn-secondary" onclick="App.showPlanimetry('${i.id}')">Plan</button>
                    </td>
                </tr>
            `;
        }).join('');
    },

    /**
     * Format status for display
     */
    formatStatus(status) {
        const labels = {
            'completed': 'OK',
            'in_progress': 'In Progress',
            'blocked': 'Blocked',
            'not_started': 'Not Started'
        };
        return labels[status] || status;
    },

    /**
     * Render data issues list
     */
    renderIssues() {
        const typeFilter = document.getElementById('issue-type-filter')?.value;
        const allIssues = DataManager.getIssues();

        let filtered = allIssues;
        if (typeFilter) {
            filtered = allIssues.filter(item =>
                item.issues.some(issue => issue.type === typeFilter)
            );
        }

        const container = document.getElementById('issues-list');
        if (!container) return;

        if (filtered.length === 0) {
            container.innerHTML = '<div class="empty-state">No data issues found</div>';
            return;
        }

        container.innerHTML = filtered.map(item => {
            const intersection = item.intersection;
            return item.issues.map(issue => `
                <div class="issue-card issue-type-${issue.type}">
                    <div class="issue-header">
                        <span class="issue-title">${intersection.id} - ${this.escapeHtml(intersection.name)}</span>
                        <span class="issue-type-badge">${issue.type.replace(/_/g, ' ')}</span>
                    </div>
                    <div class="issue-details">
                        ${issue.message || ''}
                        ${issue.field ? `<br><strong>Field:</strong> ${issue.field}` : ''}
                        ${issue.main_value !== undefined ? `<br><strong>Main file:</strong> ${issue.main_value}` : ''}
                        ${issue.lotto_value !== undefined ? `<br><strong>Lotto file:</strong> ${issue.lotto_value}` : ''}
                    </div>
                    <div class="issue-actions">
                        <button class="btn btn-small btn-primary" onclick="App.showIntersectionDetail('${intersection.id}')">View Details</button>
                        <button class="btn btn-small btn-secondary" onclick="App.editIssue('${intersection.id}', '${issue.type}')">Edit</button>
                        ${issue.type === 'geocoding_uncertain' || issue.type === 'missing_coordinates' ?
                            `<button class="btn btn-small btn-secondary" onclick="App.editCoordinates('${intersection.id}')">Fix Location</button>` : ''
                        }
                    </div>
                </div>
            `).join('');
        }).join('');
    },

    /**
     * Show edit issue modal
     */
    editIssue(intersectionId, issueType) {
        const intersection = DataManager.getIntersection(intersectionId);
        if (!intersection) return;

        const modal = document.getElementById('edit-issue-modal');
        const body = document.getElementById('edit-issue-body');

        body.innerHTML = `
            <div class="form-group">
                <label>Intersection</label>
                <input type="text" value="${intersection.id} - ${intersection.name}" readonly>
            </div>
            <div class="form-group">
                <label>Issue Type</label>
                <input type="text" value="${issueType.replace(/_/g, ' ')}" readonly>
            </div>
            ${issueType === 'radar_count_mismatch' ? `
                <div class="form-group">
                    <label>Correct Radar Count</label>
                    <input type="number" id="edit-radar-count" value="${intersection.num_radars || 0}">
                </div>
            ` : ''}
            ${issueType === 'blocked_no_solution' ? `
                <div class="form-group">
                    <label>Solution</label>
                    <textarea id="edit-blocked-solution" rows="3">${intersection.installation?.blocked_solution || ''}</textarea>
                </div>
            ` : ''}
        `;

        body.dataset.intersectionId = intersectionId;
        body.dataset.issueType = issueType;

        modal.classList.add('active');
    },

    /**
     * Edit coordinates for an intersection
     */
    editCoordinates(intersectionId) {
        const intersection = DataManager.getIntersection(intersectionId);
        if (!intersection) return;

        const coords = intersection.coordinates || { lat: 41.9028, lng: 12.4964 };

        const modal = document.getElementById('edit-issue-modal');
        const body = document.getElementById('edit-issue-body');

        body.innerHTML = `
            <div class="form-group">
                <label>Intersection</label>
                <input type="text" value="${intersection.id} - ${intersection.name}" readonly>
            </div>
            <div class="form-group">
                <label>Latitude</label>
                <input type="number" step="0.00001" id="edit-lat" value="${coords.lat}">
            </div>
            <div class="form-group">
                <label>Longitude</label>
                <input type="number" step="0.00001" id="edit-lng" value="${coords.lng}">
            </div>
            <p class="help-text">You can also edit coordinates by dragging the marker in Map View (Edit Positions mode)</p>
        `;

        body.dataset.intersectionId = intersectionId;
        body.dataset.issueType = 'coordinates';

        document.getElementById('save-issue-btn').onclick = () => {
            const lat = parseFloat(document.getElementById('edit-lat').value);
            const lng = parseFloat(document.getElementById('edit-lng').value);

            if (!isNaN(lat) && !isNaN(lng)) {
                DataManager.updateIntersection(intersectionId, {
                    coordinates: { lat, lng },
                    coordinates_manual: true
                });
                this.closeModals();
                this.renderIssues();
                this.showNotification('Coordinates updated', 'success');
            }
        };

        modal.classList.add('active');
    },

    /**
     * Show planimetry modal
     */
    showPlanimetry(intersectionId) {
        const intersection = DataManager.getIntersection(intersectionId);
        if (!intersection) return;

        const modal = document.getElementById('planimetry-modal');
        const title = document.getElementById('planimetry-modal-title');
        const body = document.getElementById('planimetry-body');

        title.textContent = `Planimetry - ${intersection.id}`;

        const planimetryPath = intersection.files?.planimetry;
        if (planimetryPath) {
            body.innerHTML = `<img src="${planimetryPath}" alt="Planimetry" style="max-width: 100%; height: auto;">`;
        } else {
            body.innerHTML = '<p class="no-planimetry">No planimetry file available. Import one in the Export tab.</p>';
        }

        modal.classList.add('active');
    },

    /**
     * Show intersection detail modal with all substages
     */
    showIntersectionDetail(id) {
        const intersection = DataManager.getIntersection(id);
        if (!intersection) return;

        const modal = document.getElementById('intersection-modal');
        const title = document.getElementById('modal-title');
        const body = document.getElementById('modal-body');

        title.textContent = `${intersection.id} - ${intersection.name}`;
        body.innerHTML = this.createDetailContent(intersection);
        body.dataset.intersectionId = id;

        modal.classList.add('active');
    },

    /**
     * Create detailed content for modal with all substages
     */
    createDetailContent(intersection) {
        const inst = intersection.installation || {};
        const conf = intersection.configuration || {};
        const conn = intersection.connection || {};
        const val = intersection.validation || {};

        return `
            <div class="detail-grid">
                <!-- General Information -->
                <div class="detail-section">
                    <h4>General Information</h4>
                    <div class="detail-row"><span class="detail-label">Code</span><span class="detail-value">${intersection.id}</span></div>
                    <div class="detail-row"><span class="detail-label">Name</span><span class="detail-value">${intersection.name}</span></div>
                    <div class="detail-row"><span class="detail-label">Lotto</span><span class="detail-value">${intersection.lotto || '-'}</span></div>
                    <div class="detail-row"><span class="detail-label">System</span><span class="detail-value">${intersection.system || '-'}</span></div>
                    <div class="detail-row"><span class="detail-label">Radars</span><span class="detail-value">${intersection.num_radars || 0}</span></div>
                    <div class="detail-row"><span class="detail-label">Overall Status</span><span class="detail-value"><span class="status-badge status-${intersection.overall_status}">${this.formatStatus(intersection.overall_status)}</span></span></div>
                </div>

                <!-- Installation Stage -->
                <div class="detail-section">
                    <h4>Installation <span class="status-badge status-${inst.status}">${this.formatStatus(inst.status)}</span></h4>
                    <div class="detail-row"><span class="detail-label">Planimetry Received</span><span class="detail-value">${this.formatValue(inst.planimetry_received)}</span></div>
                    <div class="detail-row"><span class="detail-label">Cable Passage</span><span class="detail-value">${this.formatValue(inst.cable_passage)}</span></div>
                    <div class="detail-row"><span class="detail-label">Planimetry Sent to RSM</span><span class="detail-value">${this.formatValue(inst.planimetry_sent_rsm)}</span></div>
                    <div class="detail-row"><span class="detail-label">Sensor Installation</span><span class="detail-value">${this.formatValue(inst.sensor_installation)}</span></div>
                    <div class="detail-row"><span class="detail-label">Regulator Wiring</span><span class="detail-value">${this.formatValue(inst.regulator_wiring)}</span></div>
                    <div class="detail-row"><span class="detail-label">Screenshot</span><span class="detail-value">${this.formatValue(inst.screenshot)}</span></div>
                    <div class="detail-row"><span class="detail-label">Completed</span><span class="detail-value">${this.formatValue(inst.completed)}</span></div>
                    <div class="detail-row"><span class="detail-label">Documentation Sent</span><span class="detail-value">${this.formatValue(inst.documentation_sent)}</span></div>
                    <div class="detail-row"><span class="detail-label">Completion Date</span><span class="detail-value">${this.formatValue(inst.completion_date)}</span></div>
                    ${inst.blocked_conduits ? `
                    <div class="detail-row text-danger"><span class="detail-label">Blocked Conduits</span><span class="detail-value">Yes</span></div>
                    <div class="detail-row"><span class="detail-label">Solution</span><span class="detail-value">${this.formatValue(inst.blocked_solution)}</span></div>
                    ` : ''}
                </div>

                <!-- Configuration Stage -->
                <div class="detail-section">
                    <h4>Configuration <span class="status-badge status-${conf.status}">${this.formatStatus(conf.status)}</span></h4>
                    <div class="detail-row"><span class="detail-label">Config Sent</span><span class="detail-value">${this.formatValue(conf.config_sent)}</span></div>
                    <div class="detail-row"><span class="detail-label">Config Status</span><span class="detail-value">${this.formatValue(conf.config_status)}</span></div>
                    <div class="detail-row"><span class="detail-label">Config Installed</span><span class="detail-value">${this.formatValue(conf.config_installed)}</span></div>
                    <div class="detail-row"><span class="detail-label">Base Config</span><span class="detail-value">${this.formatValue(conf.base_config)}</span></div>
                    <div class="detail-row"><span class="detail-label">Definitive Config</span><span class="detail-value">${this.formatValue(conf.definitive_config)}</span></div>
                </div>

                <!-- Connection Stage -->
                <div class="detail-section">
                    <h4>Connection <span class="status-badge status-${conn.status}">${this.formatStatus(conn.status)}</span></h4>
                    <div class="detail-row"><span class="detail-label">UTC Table</span><span class="detail-value">${this.formatValue(conn.utc_table)}</span></div>
                    <div class="detail-row"><span class="detail-label">UTC Interface</span><span class="detail-value">${this.formatValue(conn.utc_interface)}</span></div>
                    <div class="detail-row"><span class="detail-label">SPOT Status</span><span class="detail-value">${this.formatValue(conn.spot_status)}</span></div>
                    <div class="detail-row"><span class="detail-label">AUT Status</span><span class="detail-value">${this.formatValue(conn.aut_status)}</span></div>
                    <div class="detail-row"><span class="detail-label">SCAE Panel</span><span class="detail-value">${this.formatValue(conn.scae_panel)}</span></div>
                </div>

                <!-- Validation Stage -->
                <div class="detail-section">
                    <h4>Validation <span class="status-badge status-${val.status}">${this.formatStatus(val.status)}</span></h4>
                    <div class="detail-row"><span class="detail-label">Data Verified</span><span class="detail-value">${this.formatValue(val.data_verified)}</span></div>
                    <div class="detail-row"><span class="detail-label">Sending to DataLake</span><span class="detail-value">${this.formatValue(val.sending_to_datalake)}</span></div>
                    <div class="detail-row"><span class="detail-label">Traffic Data Verified</span><span class="detail-value">${this.formatValue(val.traffic_data_verified)}</span></div>
                </div>

                <!-- Radars -->
                ${intersection.radars && intersection.radars.length > 0 ? `
                <div class="detail-section full-width">
                    <h4>Individual Radars</h4>
                    <div class="radar-grid">
                        ${intersection.radars.map((radar, i) => `
                            <div class="radar-item">
                                <strong>Radar ${i + 1}</strong>
                                <div>ID: ${radar.id || '-'}</div>
                                <div>IP: ${radar.ip || '-'}</div>
                                <div>Position: ${radar.position || '-'}</div>
                            </div>
                        `).join('')}
                    </div>
                </div>
                ` : ''}

                <!-- Files -->
                <div class="detail-section">
                    <h4>Files</h4>
                    <div class="detail-row">
                        <span class="detail-label">Planimetry</span>
                        <span class="detail-value">
                            ${intersection.files?.planimetry ?
                                `<a href="${intersection.files.planimetry}" target="_blank">View</a>` :
                                'Not uploaded'}
                        </span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Photos</span>
                        <span class="detail-value">${intersection.files?.photos?.length || 0} files</span>
                    </div>
                </div>

                <!-- Issues -->
                ${intersection.inconsistencies && intersection.inconsistencies.length > 0 ? `
                <div class="detail-section full-width">
                    <h4 class="text-warning">Data Issues</h4>
                    ${intersection.inconsistencies.map(issue => `
                        <div class="issue-item">
                            <span class="issue-type-badge">${issue.type.replace(/_/g, ' ')}</span>
                            <span>${issue.message || ''}</span>
                        </div>
                    `).join('')}
                </div>
                ` : ''}

                <!-- Notes -->
                <div class="detail-section full-width">
                    <h4>Notes</h4>
                    <textarea id="detail-notes" rows="3">${intersection.notes || ''}</textarea>
                </div>

                <!-- Actions -->
                <div class="detail-section full-width">
                    <h4>Quick Actions</h4>
                    <div class="action-buttons">
                        <button class="btn btn-secondary" onclick="TasksManager.createTaskForIntersection('${intersection.id}')">Create Task</button>
                        <button class="btn btn-secondary" onclick="MapManager.focusIntersection('${intersection.id}'); App.closeModals(); App.switchTab('map');">Show on Map</button>
                        <button class="btn btn-secondary" onclick="App.showPlanimetry('${intersection.id}')">View Planimetry</button>
                    </div>
                </div>
            </div>
        `;
    },

    /**
     * Format value for display
     */
    formatValue(val) {
        if (val === null || val === undefined || val === '') return '-';
        if (val === true) return 'Yes';
        if (val === false) return 'No';
        return String(val);
    },

    /**
     * Save intersection changes from modal
     */
    saveIntersectionChanges() {
        const body = document.getElementById('modal-body');
        const id = body.dataset.intersectionId;
        if (!id) return;

        const notes = document.getElementById('detail-notes')?.value;

        DataManager.updateIntersection(id, { notes });

        this.showNotification('Changes saved', 'success');
        this.closeModals();
        this.renderCurrentTab();
    },

    /**
     * Close all modals
     */
    closeModals() {
        document.querySelectorAll('.modal').forEach(modal => {
            modal.classList.remove('active');
        });
    },

    /**
     * Show notification
     */
    showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.textContent = message;
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 12px 20px;
            background: ${type === 'success' ? '#22c55e' : type === 'error' ? '#ef4444' : '#3b82f6'};
            color: white;
            border-radius: 6px;
            z-index: 10000;
            animation: slideIn 0.3s ease;
        `;

        document.body.appendChild(notification);
        setTimeout(() => notification.remove(), 3000);
    },

    /**
     * Escape HTML to prevent XSS
     */
    escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
};

// Initialize app when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    App.init();
});
