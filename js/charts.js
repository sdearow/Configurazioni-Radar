/**
 * Charts Module
 * Handles Chart.js visualizations for the dashboard
 */

const ChartsManager = {
    charts: {},

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
            pending: '#94a3b8',
            in_progress: '#3b82f6',
            completed: '#22c55e',
            blocked: '#ef4444'
        }
    },

    /**
     * Initialize all charts
     */
    init() {
        // Charts will be created when dashboard tab is shown
        return this;
    },

    /**
     * Render all dashboard charts
     */
    renderDashboard(intersections) {
        this.updateProgressBars(intersections);
        this.renderLottoChart(intersections);
        this.renderSystemChart(intersections);
        this.renderStageChart(intersections);
        this.renderStatusChart(intersections);
    },

    /**
     * Update progress bars
     */
    updateProgressBars(intersections) {
        const total = intersections.length;
        if (total === 0) return;

        const stages = {
            installation: 0,
            configuration: 0,
            connection: 0,
            validation: 0
        };

        // Count intersections that have reached or passed each stage
        intersections.forEach(intersection => {
            const stage = intersection.current_stage;
            const stageOrder = ['installation', 'configuration', 'connection', 'validation'];
            const stageIndex = stageOrder.indexOf(stage);

            // Mark previous stages as complete
            for (let i = 0; i <= stageIndex; i++) {
                if (i < stageIndex || intersection.stage_status === 'completed') {
                    stages[stageOrder[i]]++;
                }
            }
        });

        // For installation, count those that have moved past it
        const pastInstallation = intersections.filter(i =>
            ['configuration', 'connection', 'validation'].includes(i.current_stage)
        ).length;

        const pastConfiguration = intersections.filter(i =>
            ['connection', 'validation'].includes(i.current_stage)
        ).length;

        const pastConnection = intersections.filter(i =>
            ['validation'].includes(i.current_stage)
        ).length;

        const completed = intersections.filter(i =>
            i.current_stage === 'validation' && i.stage_status === 'completed'
        ).length;

        // Update bars
        this.updateProgressBar('installation', pastInstallation, total);
        this.updateProgressBar('configuration', pastConfiguration, total);
        this.updateProgressBar('connection', pastConnection, total);
        this.updateProgressBar('validation', completed, total);
    },

    /**
     * Update a single progress bar
     */
    updateProgressBar(stage, count, total) {
        const percentage = total > 0 ? Math.round((count / total) * 100) : 0;
        const fill = document.getElementById(`progress-${stage}`);
        const value = document.getElementById(`progress-${stage}-value`);

        if (fill) {
            fill.style.width = `${percentage}%`;
        }
        if (value) {
            value.textContent = `${percentage}% (${count}/${total})`;
        }
    },

    /**
     * Render Lotto chart
     */
    renderLottoChart(intersections) {
        const ctx = document.getElementById('chart-lotto');
        if (!ctx) return;

        // Destroy existing chart
        if (this.charts.lotto) {
            this.charts.lotto.destroy();
        }

        // Calculate data
        const data = {};
        intersections.forEach(i => {
            const lotto = i.lotto || 'Unknown';
            if (!data[lotto]) {
                data[lotto] = { intersections: 0, radars: 0 };
            }
            data[lotto].intersections++;
            data[lotto].radars += i.num_radars || 0;
        });

        const labels = Object.keys(data);
        const intersectionCounts = labels.map(l => data[l].intersections);
        const radarCounts = labels.map(l => data[l].radars);
        const colors = labels.map(l => this.colors.lotto[l] || '#6b7280');

        this.charts.lotto = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [
                    {
                        label: 'Intersections',
                        data: intersectionCounts,
                        backgroundColor: colors.map(c => c + '80'),
                        borderColor: colors,
                        borderWidth: 1
                    },
                    {
                        label: 'Radars',
                        data: radarCounts,
                        backgroundColor: colors.map(c => c + '40'),
                        borderColor: colors,
                        borderWidth: 1
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom'
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });
    },

    /**
     * Render System chart
     */
    renderSystemChart(intersections) {
        const ctx = document.getElementById('chart-system');
        if (!ctx) return;

        if (this.charts.system) {
            this.charts.system.destroy();
        }

        const data = {};
        intersections.forEach(i => {
            const system = i.system || 'Unknown';
            if (!data[system]) {
                data[system] = 0;
            }
            data[system]++;
        });

        const labels = Object.keys(data);
        const counts = labels.map(l => data[l]);
        const colors = labels.map(l => this.colors.system[l] || '#6b7280');

        this.charts.system = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: labels,
                datasets: [{
                    data: counts,
                    backgroundColor: colors,
                    borderWidth: 2,
                    borderColor: '#ffffff'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom'
                    }
                }
            }
        });
    },

    /**
     * Render Stage chart
     */
    renderStageChart(intersections) {
        const ctx = document.getElementById('chart-stage');
        if (!ctx) return;

        if (this.charts.stage) {
            this.charts.stage.destroy();
        }

        const data = {
            installation: 0,
            configuration: 0,
            connection: 0,
            validation: 0
        };

        intersections.forEach(i => {
            const stage = i.current_stage || 'installation';
            if (data.hasOwnProperty(stage)) {
                data[stage]++;
            }
        });

        const labels = Object.keys(data).map(s => s.charAt(0).toUpperCase() + s.slice(1));
        const counts = Object.values(data);
        const colors = Object.keys(data).map(s => this.colors.stage[s]);

        this.charts.stage = new Chart(ctx, {
            type: 'pie',
            data: {
                labels: labels,
                datasets: [{
                    data: counts,
                    backgroundColor: colors,
                    borderWidth: 2,
                    borderColor: '#ffffff'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom'
                    }
                }
            }
        });
    },

    /**
     * Render Status breakdown chart
     */
    renderStatusChart(intersections) {
        const ctx = document.getElementById('chart-status');
        if (!ctx) return;

        if (this.charts.status) {
            this.charts.status.destroy();
        }

        // Group by stage and status
        const data = {};
        const stages = ['installation', 'configuration', 'connection', 'validation'];
        const statuses = ['pending', 'in_progress', 'completed', 'blocked'];

        stages.forEach(stage => {
            data[stage] = {
                pending: 0,
                in_progress: 0,
                completed: 0,
                blocked: 0
            };
        });

        intersections.forEach(i => {
            const stage = i.current_stage || 'installation';
            const status = i.stage_status || 'pending';
            if (data[stage] && data[stage].hasOwnProperty(status)) {
                data[stage][status]++;
            }
        });

        const datasets = statuses.map(status => ({
            label: status.charAt(0).toUpperCase() + status.slice(1).replace('_', ' '),
            data: stages.map(stage => data[stage][status]),
            backgroundColor: this.colors.status[status]
        }));

        this.charts.status = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: stages.map(s => s.charAt(0).toUpperCase() + s.slice(1)),
                datasets: datasets
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom'
                    }
                },
                scales: {
                    x: {
                        stacked: true
                    },
                    y: {
                        stacked: true,
                        beginAtZero: true
                    }
                }
            }
        });
    },

    /**
     * Destroy all charts (cleanup)
     */
    destroyAll() {
        Object.values(this.charts).forEach(chart => {
            if (chart) {
                chart.destroy();
            }
        });
        this.charts = {};
    }
};
