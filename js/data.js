/**
 * Data Management Module
 * Handles loading, saving, and manipulating intersection and task data
 */

const DataManager = {
    intersections: [],
    tasks: [],
    summary: null,

    // Storage keys
    STORAGE_KEY_INTERSECTIONS: 'radar_intersections',
    STORAGE_KEY_TASKS: 'radar_tasks',
    STORAGE_KEY_HISTORY: 'radar_history',

    /**
     * Initialize data - load from localStorage, embedded data, or JSON file
     */
    async init() {
        // Try to load from localStorage first
        const storedIntersections = localStorage.getItem(this.STORAGE_KEY_INTERSECTIONS);
        const storedTasks = localStorage.getItem(this.STORAGE_KEY_TASKS);

        if (storedIntersections) {
            this.intersections = JSON.parse(storedIntersections);
            console.log('Loaded intersections from localStorage');
        } else {
            // Load from embedded data or JSON file
            await this.loadFromFile();
        }

        if (storedTasks) {
            this.tasks = JSON.parse(storedTasks);
            console.log('Loaded tasks from localStorage');
        } else {
            this.tasks = [];
        }

        // Load summary from embedded data or calculate it
        if (typeof EMBEDDED_DATA !== 'undefined' && EMBEDDED_DATA.summary) {
            this.summary = EMBEDDED_DATA.summary;
        } else {
            try {
                const response = await fetch('data/summary.json');
                this.summary = await response.json();
            } catch (e) {
                this.summary = this.calculateSummary();
            }
        }

        return this;
    },

    /**
     * Load data from embedded data or JSON file
     */
    async loadFromFile() {
        // First try embedded data (works with file:// protocol)
        if (typeof EMBEDDED_DATA !== 'undefined' && EMBEDDED_DATA.intersections) {
            this.intersections = EMBEDDED_DATA.intersections;
            console.log(`Loaded ${this.intersections.length} intersections from embedded data`);
            return;
        }

        // Fall back to fetch (works with http:// protocol)
        try {
            const response = await fetch('data/intersections.json');
            this.intersections = await response.json();
            console.log(`Loaded ${this.intersections.length} intersections from file`);
        } catch (e) {
            console.error('Error loading intersections:', e);
            this.intersections = [];
        }
    },

    /**
     * Save data to localStorage
     */
    save() {
        localStorage.setItem(this.STORAGE_KEY_INTERSECTIONS, JSON.stringify(this.intersections));
        localStorage.setItem(this.STORAGE_KEY_TASKS, JSON.stringify(this.tasks));
        console.log('Data saved to localStorage');
    },

    /**
     * Get all intersections
     */
    getIntersections() {
        return this.intersections;
    },

    /**
     * Get intersection by ID
     */
    getIntersection(id) {
        return this.intersections.find(i => i.id === id);
    },

    /**
     * Update intersection
     */
    updateIntersection(id, updates) {
        const index = this.intersections.findIndex(i => i.id === id);
        if (index !== -1) {
            // Add to history
            const oldData = { ...this.intersections[index] };
            this.intersections[index] = {
                ...this.intersections[index],
                ...updates,
                updated_at: new Date().toISOString()
            };

            // Log change to history
            if (!this.intersections[index].history) {
                this.intersections[index].history = [];
            }
            this.intersections[index].history.push({
                date: new Date().toISOString(),
                action: 'Updated',
                changes: updates
            });

            this.save();
            return this.intersections[index];
        }
        return null;
    },

    /**
     * Filter intersections
     */
    filterIntersections(filters) {
        return this.intersections.filter(intersection => {
            // Filter by Lotto
            if (filters.lotto && filters.lotto.length > 0) {
                if (!filters.lotto.includes(intersection.lotto)) return false;
            }

            // Filter by System
            if (filters.system && filters.system.length > 0) {
                if (!filters.system.includes(intersection.system)) return false;
            }

            // Filter by overall status
            if (filters.overallStatus) {
                if (intersection.overall_status !== filters.overallStatus) return false;
            }

            // Filter by issues (data issues)
            if (filters.hasIssues) {
                if (!intersection.inconsistencies || intersection.inconsistencies.length === 0) return false;
            }

            // Filter by active tasks
            if (filters.showActiveTasks) {
                const hasTasks = this.tasks.some(t =>
                    t.intersection_id === intersection.id &&
                    (t.status === 'pending' || t.status === 'in_progress')
                );
                if (!hasTasks) return false;
            }

            // Filter by search term
            if (filters.search) {
                const searchLower = filters.search.toLowerCase();
                const nameMatch = (intersection.name || '').toLowerCase().includes(searchLower);
                const idMatch = (intersection.id || '').toLowerCase().includes(searchLower);
                if (!nameMatch && !idMatch) return false;
            }

            return true;
        });
    },

    /**
     * Get summary statistics
     */
    getSummary() {
        if (this.summary) return this.summary;
        return this.calculateSummary();
    },

    /**
     * Get intersections with issues (renamed from inconsistencies)
     */
    getIssues() {
        return this.intersections
            .filter(i => i.inconsistencies && i.inconsistencies.length > 0)
            .map(i => ({
                intersection: i,
                issues: i.inconsistencies
            }));
    },

    /**
     * Get intersections with inconsistencies (alias for backward compatibility)
     */
    getInconsistencies() {
        return this.getIssues();
    },

    /**
     * Calculate summary statistics
     */
    calculateSummary() {
        const summary = {
            total_intersections: this.intersections.length,
            total_radars: this.intersections.reduce((sum, i) => sum + (i.num_radars || 0), 0),
            by_lotto: {},
            by_system: {},
            by_stage: {},
            inconsistencies: {
                total: 0,
                by_type: {}
            }
        };

        this.intersections.forEach(intersection => {
            // By Lotto
            const lotto = intersection.lotto || 'Unknown';
            if (!summary.by_lotto[lotto]) {
                summary.by_lotto[lotto] = { intersections: 0, radars: 0 };
            }
            summary.by_lotto[lotto].intersections++;
            summary.by_lotto[lotto].radars += intersection.num_radars || 0;

            // By System
            const system = intersection.system || 'Unknown';
            if (!summary.by_system[system]) {
                summary.by_system[system] = { intersections: 0, radars: 0 };
            }
            summary.by_system[system].intersections++;
            summary.by_system[system].radars += intersection.num_radars || 0;

            // By Stage
            const stage = intersection.current_stage || 'unknown';
            if (!summary.by_stage[stage]) {
                summary.by_stage[stage] = 0;
            }
            summary.by_stage[stage]++;

            // Inconsistencies
            if (intersection.inconsistencies) {
                intersection.inconsistencies.forEach(inc => {
                    summary.inconsistencies.total++;
                    if (!summary.inconsistencies.by_type[inc.type]) {
                        summary.inconsistencies.by_type[inc.type] = 0;
                    }
                    summary.inconsistencies.by_type[inc.type]++;
                });
            }
        });

        return summary;
    },

    // Task Management

    /**
     * Get all tasks
     */
    getTasks() {
        return this.tasks;
    },

    /**
     * Get task by ID
     */
    getTask(id) {
        return this.tasks.find(t => t.id === id);
    },

    /**
     * Add new task
     */
    addTask(task) {
        const newTask = {
            id: 'TASK-' + Date.now(),
            ...task,
            status: task.status || 'pending',
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString()
        };
        this.tasks.push(newTask);
        this.save();
        return newTask;
    },

    /**
     * Update task
     */
    updateTask(id, updates) {
        const index = this.tasks.findIndex(t => t.id === id);
        if (index !== -1) {
            this.tasks[index] = {
                ...this.tasks[index],
                ...updates,
                updated_at: new Date().toISOString()
            };
            this.save();
            return this.tasks[index];
        }
        return null;
    },

    /**
     * Delete task
     */
    deleteTask(id) {
        const index = this.tasks.findIndex(t => t.id === id);
        if (index !== -1) {
            this.tasks.splice(index, 1);
            this.save();
            return true;
        }
        return false;
    },

    /**
     * Filter tasks
     */
    filterTasks(filters) {
        return this.tasks.filter(task => {
            if (filters.status && task.status !== filters.status) return false;
            if (filters.assignee && task.assignee !== filters.assignee) return false;
            if (filters.intersection_id && task.intersection_id !== filters.intersection_id) return false;
            return true;
        });
    },

    // Export/Import

    /**
     * Export all data as JSON
     */
    exportJSON() {
        return JSON.stringify({
            intersections: this.intersections,
            tasks: this.tasks,
            exported_at: new Date().toISOString()
        }, null, 2);
    },

    /**
     * Import data from JSON
     */
    importJSON(jsonString) {
        try {
            const data = JSON.parse(jsonString);
            if (data.intersections) {
                this.intersections = data.intersections;
            }
            if (data.tasks) {
                this.tasks = data.tasks;
            }
            this.save();
            return true;
        } catch (e) {
            console.error('Error importing JSON:', e);
            return false;
        }
    },

    /**
     * Create backup
     */
    createBackup() {
        const backup = {
            intersections: this.intersections,
            tasks: this.tasks,
            backup_date: new Date().toISOString()
        };
        const blob = new Blob([JSON.stringify(backup, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `radar_backup_${new Date().toISOString().split('T')[0]}.json`;
        a.click();
        URL.revokeObjectURL(url);
    },

    /**
     * Restore from backup
     */
    async restoreBackup(file) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onload = (e) => {
                try {
                    const data = JSON.parse(e.target.result);
                    if (data.intersections) {
                        this.intersections = data.intersections;
                    }
                    if (data.tasks) {
                        this.tasks = data.tasks;
                    }
                    this.save();
                    resolve(true);
                } catch (err) {
                    reject(err);
                }
            };
            reader.onerror = reject;
            reader.readAsText(file);
        });
    },

    /**
     * Reset to original data
     */
    async reset() {
        localStorage.removeItem(this.STORAGE_KEY_INTERSECTIONS);
        localStorage.removeItem(this.STORAGE_KEY_TASKS);
        await this.loadFromFile();
        this.tasks = [];
        this.save();
    }
};
