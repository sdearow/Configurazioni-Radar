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

    // Rome area reference coordinates for better placement
    romeAreas: {
        // Major streets and their approximate coordinates
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

    // Generate coordinates based on intersection name
    generateCoordinates(intersection) {
        // If coordinates are already set, use them
        if (intersection.coordinates) {
            return intersection.coordinates;
        }

        const name = (intersection.name || '').toLowerCase();
        const code = parseInt(intersection.id) || 0;

        // Try to match area from name
        let baseCoords = this.romeAreas.default;
        for (const [area, coords] of Object.entries(this.romeAreas)) {
            if (name.includes(area)) {
                baseCoords = coords;
                break;
            }
        }

        // Add small deterministic offset based on code to spread markers
        const offsetLat = ((code * 7919) % 1000) / 100000 - 0.005;
        const offsetLng = ((code * 104729) % 1000) / 100000 - 0.005;

        return {
            lat: baseCoords.lat + offsetLat,
            lng: baseCoords.lng + offsetLng
        };
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
