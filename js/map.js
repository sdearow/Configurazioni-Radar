/**
 * Map Module
 * Handles Leaflet map integration for visualizing intersection locations
 */

const MapManager = {
    map: null,
    markers: [],
    markerLayer: null,

    // Rome center coordinates
    ROME_CENTER: [41.9028, 12.4964],
    DEFAULT_ZOOM: 12,

    // Color schemes
    colors: {
        stage: {
            installation: '#f59e0b',
            configuration: '#3b82f6',
            connection: '#8b5cf6',
            validation: '#22c55e'
        },
        lotto: {
            'M9.1': '#2563eb',
            'M9.2': '#dc2626'
        },
        system: {
            'Omnia': '#059669',
            'Tmacs': '#7c3aed',
            'Unknown': '#6b7280'
        },
        status: {
            pending: '#6b7280',
            in_progress: '#3b82f6',
            completed: '#22c55e',
            blocked: '#ef4444'
        }
    },

    // Simulated coordinates for Rome intersections (will be replaced with real geocoding)
    // This generates approximate positions based on equipment code
    generateCoordinates(intersection) {
        // If coordinates are already set, use them
        if (intersection.coordinates) {
            return intersection.coordinates;
        }

        // Generate pseudo-random but deterministic coordinates based on ID
        const code = parseInt(intersection.id) || 0;
        const seed = code * 9301 + 49297;

        // Rome bounding box approximately
        const latMin = 41.82, latMax = 41.98;
        const lngMin = 12.35, lngMax = 12.60;

        const lat = latMin + ((seed % 1000) / 1000) * (latMax - latMin);
        const lng = lngMin + (((seed / 1000) % 1000) / 1000) * (lngMax - lngMin);

        return { lat, lng };
    },

    /**
     * Initialize the map
     */
    init() {
        // Create map
        this.map = L.map('map').setView(this.ROME_CENTER, this.DEFAULT_ZOOM);

        // Add OpenStreetMap tiles
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        }).addTo(this.map);

        // Create marker layer group
        this.markerLayer = L.layerGroup().addTo(this.map);

        // Update legend
        this.updateLegend('stage');

        return this;
    },

    /**
     * Create a colored circle marker
     */
    createMarker(intersection, colorBy = 'stage') {
        const coords = this.generateCoordinates(intersection);
        const color = this.getColor(intersection, colorBy);
        const hasIssues = intersection.inconsistencies && intersection.inconsistencies.length > 0;
        const isBlocked = intersection.installation && intersection.installation.blocked_conduits;

        // Create circle marker
        const marker = L.circleMarker([coords.lat, coords.lng], {
            radius: 8,
            fillColor: color,
            color: hasIssues ? '#f59e0b' : (isBlocked ? '#ef4444' : '#ffffff'),
            weight: hasIssues || isBlocked ? 3 : 2,
            opacity: 1,
            fillOpacity: 0.8
        });

        // Bind popup
        marker.bindPopup(this.createPopupContent(intersection));

        // Store reference to intersection
        marker.intersectionId = intersection.id;

        return marker;
    },

    /**
     * Get color based on coloring scheme
     */
    getColor(intersection, colorBy) {
        switch (colorBy) {
            case 'stage':
                return this.colors.stage[intersection.current_stage] || '#6b7280';
            case 'lotto':
                return this.colors.lotto[intersection.lotto] || '#6b7280';
            case 'system':
                return this.colors.system[intersection.system] || '#6b7280';
            case 'status':
                return this.colors.status[intersection.stage_status] || '#6b7280';
            default:
                return '#6b7280';
        }
    },

    /**
     * Create popup content for marker
     */
    createPopupContent(intersection) {
        const hasIssues = intersection.inconsistencies && intersection.inconsistencies.length > 0;
        const isBlocked = intersection.installation && intersection.installation.blocked_conduits;

        return `
            <div class="popup-content">
                <div class="popup-title">${intersection.name}</div>
                <div class="popup-info">
                    <span><strong>Code:</strong> ${intersection.id}</span>
                    <span><strong>Lotto:</strong> ${intersection.lotto}</span>
                    <span><strong>System:</strong> ${intersection.system}</span>
                    <span><strong>Radars:</strong> ${intersection.num_radars}</span>
                    <span><strong>Stage:</strong> ${intersection.current_stage}</span>
                    ${hasIssues ? '<span class="text-warning"><strong>Has inconsistencies</strong></span>' : ''}
                    ${isBlocked ? '<span class="text-danger"><strong>Blocked conduits</strong></span>' : ''}
                </div>
                <div class="popup-actions">
                    <button class="btn btn-primary btn-small" onclick="App.showIntersectionDetail('${intersection.id}')">
                        View Details
                    </button>
                </div>
            </div>
        `;
    },

    /**
     * Render markers on map
     */
    renderMarkers(intersections, colorBy = 'stage') {
        // Clear existing markers
        this.markerLayer.clearLayers();
        this.markers = [];

        // Add markers for each intersection
        intersections.forEach(intersection => {
            const marker = this.createMarker(intersection, colorBy);
            marker.addTo(this.markerLayer);
            this.markers.push(marker);
        });

        // Update legend
        this.updateLegend(colorBy);

        // Update stats
        this.updateStats(intersections);
    },

    /**
     * Update the legend based on color scheme
     */
    updateLegend(colorBy) {
        const legendContainer = document.getElementById('map-legend');
        if (!legendContainer) return;

        let legendHTML = '';
        const colorScheme = this.colors[colorBy];

        for (const [key, color] of Object.entries(colorScheme)) {
            const label = key.charAt(0).toUpperCase() + key.slice(1).replace('_', ' ');
            legendHTML += `
                <div class="legend-item">
                    <span class="legend-color" style="background-color: ${color}"></span>
                    <span>${label}</span>
                </div>
            `;
        }

        // Add special indicators
        legendHTML += `
            <div class="legend-item" style="margin-top: 0.5rem;">
                <span class="legend-color" style="background-color: #fff; border: 3px solid #f59e0b;"></span>
                <span>Has inconsistencies</span>
            </div>
            <div class="legend-item">
                <span class="legend-color" style="background-color: #fff; border: 3px solid #ef4444;"></span>
                <span>Blocked conduits</span>
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

        const stats = {
            total: intersections.length,
            radars: intersections.reduce((sum, i) => sum + (i.num_radars || 0), 0),
            blocked: intersections.filter(i => i.installation && i.installation.blocked_conduits).length,
            inconsistencies: intersections.filter(i => i.inconsistencies && i.inconsistencies.length > 0).length
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
     * Focus on a specific intersection
     */
    focusIntersection(id) {
        const intersection = DataManager.getIntersection(id);
        if (!intersection) return;

        const coords = this.generateCoordinates(intersection);
        this.map.setView([coords.lat, coords.lng], 16);

        // Find and open marker popup
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
