/**
 * Browser-based Geocoding Module
 * Uses Nominatim API to geocode intersection names
 */

const Geocoder = {
    REQUEST_DELAY: 1100, // 1.1 seconds between requests (Nominatim rate limit)
    isRunning: false,
    results: {
        high: [],
        medium: [],
        low: [],
        failed: []
    },

    /**
     * Extract street names from intersection name
     */
    extractStreetNames(intersectionName) {
        // Remove the ID prefix (e.g., "101-")
        let name = intersectionName.replace(/^\d+-/, '');

        // Split by common separators
        const parts = name.split(/[\/\\&\-–—]/);

        const streets = [];
        const prefixes = ['via ', 'viale ', 'piazza ', 'piazzale ', 'largo ',
                         'corso ', 'vicolo ', 'lungotevere ', 'circonvallazione ',
                         'c.so ', 'p.za ', 'p.le '];

        for (let part of parts) {
            part = part.trim();
            if (!part) continue;

            // Check if it already has a street prefix
            const hasPrefix = prefixes.some(p => part.toLowerCase().startsWith(p));

            if (hasPrefix) {
                // Expand abbreviations
                part = part.replace(/^C\.so\s/i, 'Corso ');
                part = part.replace(/^P\.za\s/i, 'Piazza ');
                part = part.replace(/^P\.le\s/i, 'Piazzale ');
                streets.push(part);
            } else {
                streets.push(`Via ${part}`);
            }
        }

        return streets;
    },

    /**
     * Check if coordinates are within Rome bounds
     */
    isInRome(lat, lng) {
        return lat >= 41.65 && lat <= 42.05 &&
               lng >= 12.20 && lng <= 12.80;
    },

    /**
     * Search Nominatim API
     */
    async nominatimSearch(query) {
        try {
            const response = await fetch(
                `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(query)}&limit=1&countrycodes=it`,
                {
                    headers: {
                        'Accept': 'application/json'
                    }
                }
            );

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }

            const data = await response.json();
            if (data && data.length > 0) {
                return data[0];
            }
        } catch (e) {
            console.error(`Geocoding error for "${query}":`, e);
        }
        return null;
    },

    /**
     * Geocode a single intersection
     */
    async geocodeIntersection(streets) {
        // Strategy 1: Search for intersection of two streets
        if (streets.length >= 2) {
            const query = `${streets[0]} & ${streets[1]}, Roma, Italy`;
            const result = await this.nominatimSearch(query);
            if (result && this.isInRome(parseFloat(result.lat), parseFloat(result.lon))) {
                return {
                    lat: parseFloat(result.lat),
                    lng: parseFloat(result.lon),
                    confidence: 'high',
                    query: query,
                    display_name: result.display_name || ''
                };
            }
        }

        // Strategy 2: Search for first street
        if (streets.length > 0) {
            const query = `${streets[0]}, Roma, Italy`;
            const result = await this.nominatimSearch(query);
            if (result && this.isInRome(parseFloat(result.lat), parseFloat(result.lon))) {
                return {
                    lat: parseFloat(result.lat),
                    lng: parseFloat(result.lon),
                    confidence: streets.length === 1 ? 'medium' : 'low',
                    query: query,
                    display_name: result.display_name || ''
                };
            }
        }

        // Strategy 3: Try without "Via" prefix
        if (streets.length > 0) {
            const streetName = streets[0].replace(/^Via\s/i, '').replace(/^Viale\s/i, '');
            const query = `${streetName}, Roma, Italy`;
            const result = await this.nominatimSearch(query);
            if (result && this.isInRome(parseFloat(result.lat), parseFloat(result.lon))) {
                return {
                    lat: parseFloat(result.lat),
                    lng: parseFloat(result.lon),
                    confidence: 'low',
                    query: query,
                    display_name: result.display_name || ''
                };
            }
        }

        return null;
    },

    /**
     * Delay helper
     */
    delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    },

    /**
     * Run batch geocoding for all intersections
     */
    async runBatchGeocoding(progressCallback) {
        if (this.isRunning) {
            alert('Geocoding already in progress!');
            return;
        }

        this.isRunning = true;
        this.results = { high: [], medium: [], low: [], failed: [] };

        const intersections = DataManager.getIntersections();
        const toGeocode = intersections.filter(i =>
            !i.coordinates_manual &&
            (!i.coordinates || i.geocode_confidence !== 'high')
        );

        console.log(`Starting geocoding for ${toGeocode.length} intersections...`);

        for (let i = 0; i < toGeocode.length; i++) {
            const intersection = toGeocode[i];
            const name = intersection.name || intersection.id;

            if (progressCallback) {
                progressCallback(i + 1, toGeocode.length, name);
            }

            console.log(`[${i + 1}/${toGeocode.length}] ${name}`);

            const streets = this.extractStreetNames(name);
            console.log(`  Streets: ${streets.join(', ')}`);

            const result = await this.geocodeIntersection(streets);

            if (result) {
                // Update intersection
                DataManager.updateIntersection(intersection.id, {
                    coordinates: { lat: result.lat, lng: result.lng },
                    geocode_confidence: result.confidence,
                    geocode_query: result.query,
                    geocode_display: result.display_name.substring(0, 100)
                });

                this.results[result.confidence].push(name);
                console.log(`  -> ${result.confidence.toUpperCase()}: ${result.lat.toFixed(5)}, ${result.lng.toFixed(5)}`);
            } else {
                this.results.failed.push(name);
                console.log(`  -> FAILED`);
            }

            // Rate limiting
            if (i < toGeocode.length - 1) {
                await this.delay(this.REQUEST_DELAY);
            }
        }

        this.isRunning = false;

        // Return summary
        return {
            total: toGeocode.length,
            high: this.results.high.length,
            medium: this.results.medium.length,
            low: this.results.low.length,
            failed: this.results.failed.length,
            failedNames: this.results.failed
        };
    },

    /**
     * Geocode a single intersection by ID
     */
    async geocodeSingle(intersectionId) {
        const intersection = DataManager.getIntersection(intersectionId);
        if (!intersection) return null;

        const name = intersection.name || intersection.id;
        const streets = this.extractStreetNames(name);

        const result = await this.geocodeIntersection(streets);

        if (result) {
            DataManager.updateIntersection(intersectionId, {
                coordinates: { lat: result.lat, lng: result.lng },
                geocode_confidence: result.confidence,
                geocode_query: result.query,
                geocode_display: result.display_name.substring(0, 100)
            });
        }

        return result;
    }
};
