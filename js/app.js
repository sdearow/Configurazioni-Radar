/**
 * Main Application Module
 * Coordinates all other modules and handles UI interactions
 */

const App = {
    currentTab: 'map',
    currentFilters: {
        lotto: ['M9.1', 'M9.2'],
        system: ['Omnia', 'Tmacs'],
        stage: ['installation', 'configuration', 'connection', 'validation'],
        search: '',
        hasInconsistencies: false,
        isBlocked: false
    },
    colorBy: 'stage',

    /**
     * Initialize the application
     */
    async init() {
        console.log('Initializing Radar Project Management...');

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

        // Map filters
        document.getElementById('color-by')?.addEventListener('change', (e) => {
            this.colorBy = e.target.value;
            this.renderMap();
        });

        // Checkbox filters
        document.querySelectorAll('input[name="lotto"]').forEach(cb => {
            cb.addEventListener('change', () => this.updateFiltersFromCheckboxes());
        });

        document.querySelectorAll('input[name="system"]').forEach(cb => {
            cb.addEventListener('change', () => this.updateFiltersFromCheckboxes());
        });

        document.querySelectorAll('input[name="stage"]').forEach(cb => {
            cb.addEventListener('change', () => this.updateFiltersFromCheckboxes());
        });

        document.getElementById('show-inconsistencies-only')?.addEventListener('change', (e) => {
            this.currentFilters.hasInconsistencies = e.target.checked;
            this.renderMap();
        });

        document.getElementById('show-blocked-only')?.addEventListener('change', (e) => {
            this.currentFilters.isBlocked = e.target.checked;
            this.renderMap();
        });

        // Search
        document.getElementById('search-input')?.addEventListener('input', (e) => {
            this.currentFilters.search = e.target.value;
            this.renderList();
        });

        // List filters
        document.getElementById('list-filter-lotto')?.addEventListener('change', () => this.renderList());
        document.getElementById('list-filter-stage')?.addEventListener('change', () => this.renderList());
        document.getElementById('list-filter-system')?.addEventListener('change', () => this.renderList());

        // Inconsistency filter
        document.getElementById('inconsistency-type-filter')?.addEventListener('change', () => this.renderInconsistencies());

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
    },

    /**
     * Update filters from checkboxes
     */
    updateFiltersFromCheckboxes() {
        this.currentFilters.lotto = Array.from(document.querySelectorAll('input[name="lotto"]:checked')).map(cb => cb.value);
        this.currentFilters.system = Array.from(document.querySelectorAll('input[name="system"]:checked')).map(cb => cb.value);
        this.currentFilters.stage = Array.from(document.querySelectorAll('input[name="stage"]:checked')).map(cb => cb.value);
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
                // Resize map when tab becomes visible
                setTimeout(() => MapManager.resize(), 100);
                this.renderMap();
                break;
            case 'dashboard':
                this.renderDashboard();
                break;
            case 'list':
                this.renderList();
                break;
            case 'inconsistencies':
                this.renderInconsistencies();
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
        const intersections = DataManager.getIntersections();
        const summary = DataManager.calculateSummary();

        document.getElementById('total-intersections').textContent = summary.total_intersections;
        document.getElementById('total-radars').textContent = summary.total_radars;
        document.getElementById('total-inconsistencies').textContent = summary.inconsistencies.total;

        // Highlight if there are inconsistencies
        const incStat = document.getElementById('inconsistencies-stat');
        if (incStat) {
            incStat.classList.toggle('warning', summary.inconsistencies.total > 0);
        }
    },

    /**
     * Render map view
     */
    renderMap() {
        const filtered = DataManager.filterIntersections(this.currentFilters);
        MapManager.renderMarkers(filtered, this.colorBy);
    },

    /**
     * Render dashboard
     */
    renderDashboard() {
        const intersections = DataManager.getIntersections();
        ChartsManager.renderDashboard(intersections);
    },

    /**
     * Render intersection list
     */
    renderList() {
        const filters = {
            search: document.getElementById('search-input')?.value || '',
            lotto: [],
            stage: [],
            system: []
        };

        const lottoFilter = document.getElementById('list-filter-lotto')?.value;
        if (lottoFilter) filters.lotto = [lottoFilter];

        const stageFilter = document.getElementById('list-filter-stage')?.value;
        if (stageFilter) filters.stage = [stageFilter];

        const systemFilter = document.getElementById('list-filter-system')?.value;
        if (systemFilter) filters.system = [systemFilter];

        const intersections = DataManager.filterIntersections(filters);
        const tbody = document.getElementById('intersection-list');
        if (!tbody) return;

        tbody.innerHTML = intersections.map(i => `
            <tr>
                <td>${i.id}</td>
                <td>${this.escapeHtml(i.name)}</td>
                <td>${i.lotto}</td>
                <td>${i.system || '-'}</td>
                <td>${i.num_radars}</td>
                <td><span class="badge badge-${i.current_stage}">${i.current_stage}</span></td>
                <td><span class="badge badge-${i.stage_status}">${i.stage_status.replace('_', ' ')}</span></td>
                <td>
                    ${i.inconsistencies?.length > 0 ? `<span class="badge badge-warning">${i.inconsistencies.length}</span>` : '-'}
                    ${i.installation?.blocked_conduits ? '<span class="badge badge-danger">Blocked</span>' : ''}
                </td>
                <td>
                    <button class="btn btn-small btn-primary" onclick="App.showIntersectionDetail('${i.id}')">View</button>
                    <button class="btn btn-small btn-secondary" onclick="MapManager.focusIntersection('${i.id}'); App.switchTab('map');">Map</button>
                </td>
            </tr>
        `).join('');
    },

    /**
     * Render inconsistencies list
     */
    renderInconsistencies() {
        const typeFilter = document.getElementById('inconsistency-type-filter')?.value;
        const allInconsistencies = DataManager.getInconsistencies();

        let filtered = allInconsistencies;
        if (typeFilter) {
            filtered = allInconsistencies.filter(item =>
                item.inconsistencies.some(inc => inc.type === typeFilter)
            );
        }

        const container = document.getElementById('inconsistencies-list');
        if (!container) return;

        if (filtered.length === 0) {
            container.innerHTML = '<div class="text-muted" style="text-align: center; padding: 2rem;">No inconsistencies found</div>';
            return;
        }

        container.innerHTML = filtered.map(item => {
            const intersection = item.intersection;
            return item.inconsistencies.map(inc => `
                <div class="inconsistency-card type-${inc.type}">
                    <div class="inconsistency-header">
                        <span class="inconsistency-title">${intersection.id} - ${this.escapeHtml(intersection.name)}</span>
                        <span class="inconsistency-type">${inc.type.replace(/_/g, ' ')}</span>
                    </div>
                    <div class="inconsistency-details">
                        ${inc.message || ''}
                        ${inc.field ? `<br><strong>Field:</strong> ${inc.field}` : ''}
                        ${inc.main_value !== undefined ? `<br><strong>Main file:</strong> ${inc.main_value}` : ''}
                        ${inc.lotto_value !== undefined ? `<br><strong>Lotto file:</strong> ${inc.lotto_value}` : ''}
                    </div>
                    <div style="margin-top: 0.5rem;">
                        <button class="btn btn-small btn-primary" onclick="App.showIntersectionDetail('${intersection.id}')">View Details</button>
                    </div>
                </div>
            `).join('');
        }).join('');
    },

    /**
     * Show intersection detail modal
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
     * Create detail content for modal
     */
    createDetailContent(intersection) {
        const lottoData = intersection.lotto_data || {};
        const centralData = intersection.central_system_data || {};

        return `
            <div class="detail-grid">
                <div class="detail-section">
                    <h4>General Information</h4>
                    <div class="detail-row">
                        <span class="detail-label">Code</span>
                        <span class="detail-value">${intersection.id}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Name</span>
                        <span class="detail-value">${intersection.name}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Lotto</span>
                        <span class="detail-value">${intersection.lotto}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">System</span>
                        <span class="detail-value">${intersection.system || 'Unknown'}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Number of Radars</span>
                        <span class="detail-value">${intersection.num_radars}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Data Sources</span>
                        <span class="detail-value">${intersection.data_sources?.join(', ') || 'main'}</span>
                    </div>
                </div>

                <div class="detail-section">
                    <h4>Current Status</h4>
                    <div class="detail-row">
                        <span class="detail-label">Stage</span>
                        <span class="detail-value"><span class="badge badge-${intersection.current_stage}">${intersection.current_stage}</span></span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Status</span>
                        <span class="detail-value"><span class="badge badge-${intersection.stage_status}">${intersection.stage_status.replace('_', ' ')}</span></span>
                    </div>
                </div>

                <div class="detail-section">
                    <h4>Stage 1: Installation</h4>
                    <div class="detail-row">
                        <span class="detail-label">Planimetry Sent</span>
                        <span class="detail-value">${intersection.installation?.planimetry_sent ? 'Yes' : 'No'}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Devices Installed</span>
                        <span class="detail-value">${intersection.installation?.devices_installed || '-'}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Blocked Conduits</span>
                        <span class="detail-value ${intersection.installation?.blocked_conduits ? 'text-danger' : ''}">${intersection.installation?.blocked_conduits ? 'Yes' : 'No'}</span>
                    </div>
                    ${intersection.installation?.blocked_solution ? `
                    <div class="detail-row">
                        <span class="detail-label">Solution</span>
                        <span class="detail-value">${intersection.installation.blocked_solution}</span>
                    </div>
                    ` : ''}
                </div>

                <div class="detail-section">
                    <h4>Stage 2: Configuration</h4>
                    <div class="detail-row">
                        <span class="detail-label">Config Status</span>
                        <span class="detail-value">${intersection.configuration?.status || '-'}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Config Installed</span>
                        <span class="detail-value">${intersection.configuration?.installed || '-'}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">AUT Status</span>
                        <span class="detail-value">${intersection.configuration?.aut_status || '-'}</span>
                    </div>
                </div>

                <div class="detail-section">
                    <h4>Stage 3: Connection</h4>
                    <div class="detail-row">
                        <span class="detail-label">UTC Table</span>
                        <span class="detail-value">${intersection.connection?.utc_table || '-'}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">UTC Interface</span>
                        <span class="detail-value">${intersection.connection?.utc_interface || '-'}</span>
                    </div>
                    ${centralData.spot_status ? `
                    <div class="detail-row">
                        <span class="detail-label">SPOT Status</span>
                        <span class="detail-value">${centralData.spot_status}</span>
                    </div>
                    ` : ''}
                    ${centralData.aut_status ? `
                    <div class="detail-row">
                        <span class="detail-label">AUT Status</span>
                        <span class="detail-value">${centralData.aut_status}</span>
                    </div>
                    ` : ''}
                </div>

                <div class="detail-section">
                    <h4>Stage 4: Validation</h4>
                    <div class="detail-row">
                        <span class="detail-label">Data Verified</span>
                        <span class="detail-value">${intersection.validation?.data_verified || '-'}</span>
                    </div>
                </div>

                ${intersection.radars && intersection.radars.length > 0 ? `
                <div class="detail-section full-width">
                    <h4>Individual Radars</h4>
                    <div class="radar-list">
                        ${intersection.radars.map((radar, i) => `
                            <div class="radar-item">
                                <span>Radar ${i + 1}: ${radar.id}</span>
                                <span class="badge badge-${radar.status}">${radar.status}</span>
                            </div>
                        `).join('')}
                    </div>
                </div>
                ` : ''}

                ${intersection.inconsistencies && intersection.inconsistencies.length > 0 ? `
                <div class="detail-section full-width">
                    <h4 class="text-warning">Inconsistencies</h4>
                    ${intersection.inconsistencies.map(inc => `
                        <div class="detail-row">
                            <span class="detail-label">${inc.type.replace(/_/g, ' ')}</span>
                            <span class="detail-value">${inc.message || ''} ${inc.main_value !== undefined ? `(Main: ${inc.main_value}, Lotto: ${inc.lotto_value})` : ''}</span>
                        </div>
                    `).join('')}
                </div>
                ` : ''}

                <div class="detail-section full-width">
                    <h4>Notes</h4>
                    <textarea id="detail-notes" rows="3" style="width: 100%; padding: 0.5rem; border: 1px solid var(--border-color); border-radius: 4px;">${intersection.notes || ''}</textarea>
                </div>

                <div class="detail-section full-width">
                    <h4>Quick Actions</h4>
                    <div style="display: flex; gap: 0.5rem; flex-wrap: wrap;">
                        <button class="btn btn-secondary" onclick="TasksManager.createTaskForIntersection('${intersection.id}')">Create Task</button>
                        <button class="btn btn-secondary" onclick="MapManager.focusIntersection('${intersection.id}'); App.closeModals(); App.switchTab('map');">Show on Map</button>
                    </div>
                </div>
            </div>
        `;
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

        alert('Changes saved');
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
