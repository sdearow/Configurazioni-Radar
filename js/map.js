/**
 * Map Module
 * Handles Leaflet map integration for visualizing intersection locations
 * Supports draggable markers for position correction
 */

const MapManager = {
    map: null,
    markers: [],
    markerLayer: null,
    editMode: false,
    pendingChanges: {},  // Track unsaved coordinate changes

    // Rome center coordinates
    ROME_CENTER: [41.9028, 12.4964],
    DEFAULT_ZOOM: 12,

    // Color schemes for stage statuses
    statusColors: {
        completed: '#22c55e',      // Green
        in_progress: '#3b82f6',    // Blue
        blocked: '#ef4444',        // Red
        not_started: '#9ca3af'     // Grey
    },

    // Default grey color for all markers
    defaultColor: '#9ca3af',

    // Rome area reference coordinates for better placement
    romeAreas: {
        'cassia': { lat: 41.9550, lng: 12.4600 },
        'flaminia': { lat: 41.9400, lng: 12.4750 },
        'salaria': { lat: 41.9300, lng: 12.5100 },
        'nomentana': { lat: 41.9200, lng: 12.5200 },
        'tiburtina': { lat: 41.9000, lng: 12.5400 },
        'prenestina': { lat: 41.8900, lng: 12.5500 },
        'casilina': { lat: 41.8700, lng: 12.5600 },
        'tuscolana': { lat: 41.8600, lng: 12.5300 },
        'appia': { lat: 41.8500, lng: 12.5200 },
        'ardeatina': { lat: 41.8400, lng: 12.5000 },
        'laurentina': { lat: 41.8300, lng: 12.4800 },
        'ostiense': { lat: 41.8500, lng: 12.4700 },
        'portuense': { lat: 41.8600, lng: 12.4400 },
        'aurelia': { lat: 41.9000, lng: 12.4200 },
        'boccea': { lat: 41.9100, lng: 12.4100 },
        'trionfale': { lat: 41.9200, lng: 12.4400 },
        'pineta': { lat: 41.9250, lng: 12.4300 },
        'gregorio': { lat: 41.8950, lng: 12.4550 },
        'trastevere': { lat: 41.8850, lng: 12.4650 },
        'testaccio': { lat: 41.8750, lng: 12.4750 },
        'marconi': { lat: 41.8550, lng: 12.4700 },
        'eur': { lat: 41.8300, lng: 12.4650 },
        'torrino': { lat: 41.8150, lng: 12.4550 },
        'magliana': { lat: 41.8450, lng: 12.4300 },
        'corviale': { lat: 41.8550, lng: 12.3900 },
        'primavalle': { lat: 41.9200, lng: 12.4000 },
        'torrevecchia': { lat: 41.9300, lng: 12.4150 },
        'battistini': { lat: 41.9100, lng: 12.4050 },
        'cornelia': { lat: 41.9050, lng: 12.4150 },
        'cipro': { lat: 41.9080, lng: 12.4450 },
        'prati': { lat: 41.9100, lng: 12.4600 },
        'clodio': { lat: 41.9150, lng: 12.4580 },
        'mazzini': { lat: 41.9200, lng: 12.4500 },
        'ponte': { lat: 41.9000, lng: 12.4700 },
        'centro': { lat: 41.8980, lng: 12.4800 },
        'termini': { lat: 41.9010, lng: 12.5020 },
        'esquilino': { lat: 41.8950, lng: 12.5050 },
        'sanlorenzo': { lat: 41.8970, lng: 12.5200 },
        'verano': { lat: 41.9050, lng: 12.5180 },
        'pietralata': { lat: 41.9150, lng: 12.5400 },
        'montesacro': { lat: 41.9400, lng: 12.5250 },
        'talenti': { lat: 41.9500, lng: 12.5400 },
        'conca': { lat: 41.9350, lng: 12.5150 },
        'parioli': { lat: 41.9300, lng: 12.4900 },
        'aventino': { lat: 41.8830, lng: 12.4850 },
        'garbatella': { lat: 41.8600, lng: 12.4900 },
        'default': { lat: 41.9028, lng: 12.4964 }
    },

    // Generate coordinates based on intersection name (fallback)
    generateCoordinates(intersection) {
        if (intersection.coordinates) {
            return intersection.coordinates;
        }

        const name = (intersection.name || '').toLowerCase();
        const code = parseInt(intersection.id) || 0;

        let baseCoords = this.romeAreas.default;
        for (const [area, coords] of Object.entries(this.romeAreas)) {
            if (name.includes(area)) {
                baseCoords = coords;
                break;
            }
        }

        const offsetLat = ((code * 7919) % 1000) / 100000 - 0.005;
        const offsetLng = ((code * 104729) % 1000) / 100000 - 0.005;

        return {
            lat: baseCoords.lat + offsetLat,
            lng: baseCoords.lng + offsetLng
        };
    },

    searchMarker: null,  // Temporary marker for search results

    /**
     * Initialize the map
     */
    init() {
        this.map = L.map('map').setView(this.ROME_CENTER, this.DEFAULT_ZOOM);

        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        }).addTo(this.map);

        this.markerLayer = L.layerGroup().addTo(this.map);
        this.updateLegend('installation');

        // Bind search events
        this.bindSearchEvents();

        return this;
    },

    /**
     * Bind search input events
     */
    bindSearchEvents() {
        const searchInput = document.getElementById('location-search-input');
        const searchBtn = document.getElementById('location-search-btn');

        if (searchBtn) {
            searchBtn.addEventListener('click', () => this.performSearch());
        }

        if (searchInput) {
            searchInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    this.performSearch();
                }
            });
        }
    },

    /**
     * Perform location search using Nominatim
     */
    async performSearch() {
        const input = document.getElementById('location-search-input');
        const resultsContainer = document.getElementById('location-search-results');

        if (!input || !resultsContainer) return;

        const query = input.value.trim();
        if (!query) return;

        // Add Roma, Italia to improve results
        const searchQuery = query.includes('Roma') ? query : `${query}, Roma, Italia`;

        resultsContainer.innerHTML = '<div class="search-loading">Searching...</div>';

        try {
            const response = await fetch(
                `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(searchQuery)}&limit=5&countrycodes=it`,
                {
                    headers: {
                        'Accept': 'application/json',
                        'User-Agent': 'RadarProjectManagement/1.0'
                    }
                }
            );

            const results = await response.json();

            if (results.length === 0) {
                resultsContainer.innerHTML = '<div class="search-no-results">No results found. Try a different search.</div>';
                return;
            }

            resultsContainer.innerHTML = results.map((r, idx) => `
                <div class="search-result-item" data-lat="${r.lat}" data-lng="${r.lon}">
                    <strong>${r.display_name.split(',')[0]}</strong>
                    <small>${r.display_name.split(',').slice(1, 3).join(',')}</small>
                </div>
            `).join('');

            // Bind click events to results
            resultsContainer.querySelectorAll('.search-result-item').forEach(item => {
                item.addEventListener('click', () => {
                    const lat = parseFloat(item.dataset.lat);
                    const lng = parseFloat(item.dataset.lng);
                    this.jumpToLocation(lat, lng);
                });
            });

        } catch (error) {
            console.error('Search error:', error);
            resultsContainer.innerHTML = '<div class="search-error">Search failed. Please try again.</div>';
        }
    },

    /**
     * Jump to a location and show a temporary marker
     */
    jumpToLocation(lat, lng) {
        // Remove previous search marker
        if (this.searchMarker) {
            this.map.removeLayer(this.searchMarker);
        }

        // Zoom to location
        this.map.setView([lat, lng], 17);

        // Add temporary marker
        this.searchMarker = L.marker([lat, lng], {
            icon: L.divIcon({
                className: 'search-marker',
                html: `<div style="
                    width: 30px;
                    height: 30px;
                    background-color: #ef4444;
                    border: 3px solid white;
                    border-radius: 50%;
                    box-shadow: 0 2px 6px rgba(0,0,0,0.3);
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    color: white;
                    font-weight: bold;
                ">?</div>`,
                iconSize: [30, 30],
                iconAnchor: [15, 15]
            })
        }).addTo(this.map);

        this.searchMarker.bindPopup(`
            <div class="search-popup">
                <strong>Search Result</strong><br>
                <small>Lat: ${lat.toFixed(5)}, Lng: ${lng.toFixed(5)}</small><br>
                <button class="btn btn-small btn-primary" onclick="MapManager.copyCoordinates(${lat}, ${lng})">Copy Coordinates</button>
            </div>
        `).openPopup();

        this.showNotification(`Jumped to ${lat.toFixed(5)}, ${lng.toFixed(5)}`, 'info');
    },

    /**
     * Copy coordinates to clipboard
     */
    copyCoordinates(lat, lng) {
        const text = `${lat}, ${lng}`;
        navigator.clipboard.writeText(text).then(() => {
            this.showNotification('Coordinates copied to clipboard', 'success');
        }).catch(() => {
            this.showNotification('Failed to copy coordinates', 'error');
        });
    },

    /**
     * Toggle edit mode for draggable markers
     */
    toggleEditMode() {
        this.editMode = !this.editMode;

        // Update button state
        const editBtn = document.getElementById('edit-mode-btn');
        if (editBtn) {
            editBtn.classList.toggle('active', this.editMode);
            editBtn.textContent = this.editMode ? 'Exit Edit Mode (Save)' : 'Edit Positions';
        }

        // Update edit info display
        const editInfo = document.getElementById('edit-mode-info');
        if (editInfo) {
            editInfo.style.display = this.editMode ? 'block' : 'none';
        }

        // Show/hide search panel
        const searchPanel = document.getElementById('location-search-panel');
        if (searchPanel) {
            searchPanel.style.display = this.editMode ? 'block' : 'none';
        }

        // Reset pending counter when entering edit mode
        if (this.editMode) {
            const pendingCount = document.getElementById('pending-changes-count');
            if (pendingCount) {
                pendingCount.textContent = '0 changes pending';
            }
        }

        // If exiting edit mode, save changes and remove search marker
        if (!this.editMode) {
            if (Object.keys(this.pendingChanges).length > 0) {
                this.savePositionChanges();
            }
            // Remove search marker
            if (this.searchMarker) {
                this.map.removeLayer(this.searchMarker);
                this.searchMarker = null;
            }
            // Clear search results
            const resultsContainer = document.getElementById('location-search-results');
            if (resultsContainer) {
                resultsContainer.innerHTML = '';
            }
        }

        // Re-render markers with draggable state
        const intersections = DataManager.filterIntersections(App.currentFilters);
        this.renderMarkers(intersections, App.colorBy);

        // Show notification
        if (this.editMode) {
            this.showNotification('Edit mode enabled. Drag markers to correct positions. Use Search to find locations.', 'info');
        }
    },

    /**
     * Save pending position changes
     */
    savePositionChanges() {
        const changeCount = Object.keys(this.pendingChanges).length;
        if (changeCount === 0) return;

        // Update each intersection with new coordinates
        for (const [id, coords] of Object.entries(this.pendingChanges)) {
            DataManager.updateIntersection(id, {
                coordinates: coords,
                coordinates_manual: true  // Flag as manually corrected
            });
        }

        this.pendingChanges = {};

        // Reset pending counter
        const pendingCount = document.getElementById('pending-changes-count');
        if (pendingCount) {
            pendingCount.textContent = '0 changes pending';
        }

        this.showNotification(`Saved ${changeCount} position correction(s).`, 'success');

        // Export corrected coordinates to console for manual update
        this.exportCorrectedCoordinates();
    },

    /**
     * Export corrected coordinates to console for manual update
     */
    exportCorrectedCoordinates() {
        const manuallyAdjusted = DataManager.getIntersections()
            .filter(i => i.coordinates_manual)
            .map(i => ({
                id: i.id,
                name: i.name,
                coordinates: i.coordinates
            }));

        if (manuallyAdjusted.length > 0) {
            console.log('Manually adjusted coordinates:', JSON.stringify(manuallyAdjusted, null, 2));
        }
    },

    /**
     * Create a marker (draggable in edit mode)
     */
    createMarker(intersection, colorBy = 'stage') {
        const coords = this.generateCoordinates(intersection);
        const color = this.getColor(intersection, colorBy);
        const hasIssues = intersection.inconsistencies && intersection.inconsistencies.length > 0;
        const isBlocked = intersection.installation && intersection.installation.blocked_conduits;
        const isManuallySet = intersection.coordinates_manual;

        let marker;

        if (this.editMode) {
            // Use regular marker for dragging
            const icon = L.divIcon({
                className: 'custom-marker',
                html: `<div style="
                    width: 20px;
                    height: 20px;
                    background-color: ${color};
                    border: 3px solid ${isManuallySet ? '#22c55e' : (hasIssues ? '#f59e0b' : '#ffffff')};
                    border-radius: 50%;
                    cursor: move;
                "></div>`,
                iconSize: [20, 20],
                iconAnchor: [10, 10]
            });

            marker = L.marker([coords.lat, coords.lng], {
                icon: icon,
                draggable: true
            });

            // Handle drag events
            marker.on('dragend', (e) => {
                const newPos = e.target.getLatLng();
                this.pendingChanges[intersection.id] = {
                    lat: newPos.lat,
                    lng: newPos.lng
                };

                // Update pending changes counter
                const pendingCount = document.getElementById('pending-changes-count');
                if (pendingCount) {
                    const count = Object.keys(this.pendingChanges).length;
                    pendingCount.textContent = `${count} change${count !== 1 ? 's' : ''} pending`;
                }

                // Update popup with new coordinates
                marker.setPopupContent(this.createPopupContent(intersection, newPos));

                this.showNotification(`Position updated for ${intersection.name}`, 'info');
            });
        } else {
            // Use circle marker for normal view
            marker = L.circleMarker([coords.lat, coords.lng], {
                radius: 8,
                fillColor: color,
                color: isManuallySet ? '#22c55e' : (hasIssues ? '#f59e0b' : (isBlocked ? '#ef4444' : '#ffffff')),
                weight: isManuallySet || hasIssues || isBlocked ? 3 : 2,
                opacity: 1,
                fillOpacity: 0.8
            });
        }

        marker.bindPopup(this.createPopupContent(intersection));
        marker.intersectionId = intersection.id;

        return marker;
    },

    /**
     * Get color based on selected stage status
     * colorByStage is one of: installation, configuration, connection, validation
     */
    getColor(intersection, colorByStage) {
        const stage = intersection[colorByStage];
        if (!stage) return this.defaultColor;

        const status = stage.status || 'not_started';
        return this.statusColors[status] || this.defaultColor;
    },

    /**
     * Create popup content for marker
     */
    createPopupContent(intersection, newCoords = null) {
        const hasIssues = intersection.inconsistencies && intersection.inconsistencies.length > 0;
        const isBlocked = intersection.installation && intersection.installation.blocked_conduits;
        const isManuallySet = intersection.coordinates_manual;
        const coords = newCoords || intersection.coordinates;

        const instStatus = intersection.installation?.status || 'not_started';
        const confStatus = intersection.configuration?.status || 'not_started';
        const connStatus = intersection.connection?.status || 'not_started';
        const valStatus = intersection.validation?.status || 'not_started';

        return `
            <div class="popup-content">
                <div class="popup-title">${intersection.name}</div>
                <div class="popup-info">
                    <span><strong>Code:</strong> ${intersection.id}</span>
                    <span><strong>Lotto:</strong> ${intersection.lotto || '-'}</span>
                    <span><strong>System:</strong> ${intersection.system || '-'}</span>
                    <span><strong>Radars:</strong> ${intersection.num_radars || 0}</span>
                </div>
                <div class="popup-stages">
                    <span class="stage-badge stage-${instStatus}">I: ${this.formatStatus(instStatus)}</span>
                    <span class="stage-badge stage-${confStatus}">C: ${this.formatStatus(confStatus)}</span>
                    <span class="stage-badge stage-${connStatus}">Cn: ${this.formatStatus(connStatus)}</span>
                    <span class="stage-badge stage-${valStatus}">V: ${this.formatStatus(valStatus)}</span>
                </div>
                ${coords ? `<div class="popup-coords">Coords: ${coords.lat.toFixed(5)}, ${coords.lng.toFixed(5)}</div>` : ''}
                ${isManuallySet ? '<div class="text-success">Position verified</div>' : ''}
                ${hasIssues ? '<div class="text-warning">Has data issues</div>' : ''}
                ${isBlocked ? '<div class="text-danger">Blocked conduits</div>' : ''}
                <div class="popup-actions">
                    <button class="btn btn-primary btn-small" onclick="App.showIntersectionDetail('${intersection.id}')">
                        View Details
                    </button>
                    ${this.editMode ? `
                    <button class="btn btn-secondary btn-small" onclick="MapManager.searchLocation('${intersection.id}')">
                        Search Location
                    </button>
                    ` : ''}
                </div>
            </div>
        `;
    },

    /**
     * Format status for display
     */
    formatStatus(status) {
        const labels = {
            'completed': 'OK',
            'in_progress': 'In Prog',
            'blocked': 'Blocked',
            'not_started': 'N/A'
        };
        return labels[status] || status;
    },

    /**
     * Search for a location using the intersection name
     */
    searchLocation(intersectionId) {
        const intersection = DataManager.getIntersection(intersectionId);
        if (!intersection) return;

        // Clean the name for search
        let searchName = intersection.name
            .replace(/^\d+[-\s]*/, '')  // Remove leading numbers
            .replace(/\//g, ' e ')       // Replace / with " e " (and)
            .trim();

        // Open Google Maps search in new tab
        const searchUrl = `https://www.google.com/maps/search/${encodeURIComponent(searchName + ', Roma, Italia')}`;
        window.open(searchUrl, '_blank');
    },

    /**
     * Render markers on map
     */
    renderMarkers(intersections, colorBy = 'stage') {
        this.markerLayer.clearLayers();
        this.markers = [];

        intersections.forEach(intersection => {
            const marker = this.createMarker(intersection, colorBy);
            marker.addTo(this.markerLayer);
            this.markers.push(marker);
        });

        this.updateLegend(colorBy);
        this.updateStats(intersections);
    },

    /**
     * Update the legend to show status colors
     */
    updateLegend(colorByStage) {
        const legendContainer = document.getElementById('map-legend');
        if (!legendContainer) return;

        const stageLabels = {
            installation: 'Installation',
            configuration: 'Configuration',
            connection: 'Connection',
            validation: 'Validation'
        };

        let legendHTML = `
            <div class="legend-title">${stageLabels[colorByStage] || colorByStage} Status:</div>
            <div class="legend-item">
                <span class="legend-color" style="background-color: ${this.statusColors.completed}"></span>
                <span>Completed</span>
            </div>
            <div class="legend-item">
                <span class="legend-color" style="background-color: ${this.statusColors.in_progress}"></span>
                <span>In Progress</span>
            </div>
            <div class="legend-item">
                <span class="legend-color" style="background-color: ${this.statusColors.blocked}"></span>
                <span>Blocked</span>
            </div>
            <div class="legend-item">
                <span class="legend-color" style="background-color: ${this.statusColors.not_started}"></span>
                <span>Not Started</span>
            </div>
            <div class="legend-item" style="margin-top: 0.5rem; border-top: 1px solid #e2e8f0; padding-top: 0.5rem;">
                <span class="legend-color" style="background-color: #fff; border: 3px solid #22c55e;"></span>
                <span>Position verified</span>
            </div>
            <div class="legend-item">
                <span class="legend-color" style="background-color: #fff; border: 3px solid #f59e0b;"></span>
                <span>Has data issues</span>
            </div>
        `;

        legendContainer.innerHTML = legendHTML;
    },

    /**
     * Update quick stats in sidebar
     */
    updateStats(intersections) {
        const statsContainer = document.getElementById('map-stats');
        if (!statsContainer) return;

        const allIntersections = DataManager.getIntersections();
        const verified = allIntersections.filter(i => i.coordinates_manual).length;

        const stats = {
            total: intersections.length,
            radars: intersections.reduce((sum, i) => sum + (i.num_radars || 0), 0),
            blocked: intersections.filter(i => i.installation && i.installation.blocked_conduits).length,
            inconsistencies: intersections.filter(i => i.inconsistencies && i.inconsistencies.length > 0).length,
            verified: verified
        };

        statsContainer.innerHTML = `
            <div class="stat-row">
                <span>Showing</span>
                <span><strong>${stats.total}</strong> intersections</span>
            </div>
            <div class="stat-row">
                <span>Total radars</span>
                <span><strong>${stats.radars}</strong></span>
            </div>
            <div class="stat-row">
                <span>Positions verified</span>
                <span class="text-success"><strong>${stats.verified}</strong>/${allIntersections.length}</span>
            </div>
            <div class="stat-row">
                <span>Blocked</span>
                <span class="text-danger"><strong>${stats.blocked}</strong></span>
            </div>
            <div class="stat-row">
                <span>With issues</span>
                <span class="text-warning"><strong>${stats.inconsistencies}</strong></span>
            </div>
        `;
    },

    /**
     * Show notification
     */
    showNotification(message, type = 'info') {
        // Create notification element
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

        // Remove after 3 seconds
        setTimeout(() => {
            notification.remove();
        }, 3000);
    },

    /**
     * Focus on a specific intersection
     */
    focusIntersection(id) {
        const intersection = DataManager.getIntersection(id);
        if (!intersection) return;

        const coords = this.generateCoordinates(intersection);
        this.map.setView([coords.lat, coords.lng], 16);

        const marker = this.markers.find(m => m.intersectionId === id);
        if (marker) {
            marker.openPopup();
        }
    },

    /**
     * Fit map to show all visible markers
     */
    fitBounds() {
        if (this.markers.length > 0) {
            const group = L.featureGroup(this.markers);
            this.map.fitBounds(group.getBounds().pad(0.1));
        }
    },

    /**
     * Resize map (call when tab becomes visible)
     */
    resize() {
        if (this.map) {
            this.map.invalidateSize();
        }
    }
};
