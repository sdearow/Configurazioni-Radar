/**
 * Charts Module
 * Handles Chart.js visualizations for the dashboard
 * Updated for 4 independent stages with individual status tracking
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
            completed: '#22c55e',      // Green
            in_progress: '#3b82f6',    // Blue
            blocked: '#ef4444',        // Red
            not_started: '#9ca3af'     // Grey
        }
    },

    statusLabels: {
        completed: 'Completed',
        in_progress: 'In Progress',
        blocked: 'Blocked',
        not_started: 'Not Started'
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
        this.updateStageProgressCards(intersections);
        this.updateOverallProgress(intersections);
        this.renderCompactLottoChart(intersections);
        this.renderCompactSystemChart(intersections);
        this.renderStageStatusChart(intersections);
    },

    /**
     * Calculate status counts for a specific stage
     */
    getStageStatusCounts(intersections, stageName) {
        const counts = {
            completed: 0,
            in_progress: 0,
            blocked: 0,
            not_started: 0
        };

        intersections.forEach(i => {
            // Support both nested format (i.installation.status) and flat format (i.installation_status)
            let status = 'not_started';
            if (i[stageName] && i[stageName].status) {
                status = i[stageName].status;
            } else if (i[`${stageName}_status`]) {
                status = i[`${stageName}_status`];
            }

            if (counts.hasOwnProperty(status)) {
                counts[status]++;
            } else {
                counts.not_started++;
            }
        });

        return counts;
    },

    /**
     * Update stage progress cards with per-stage status breakdown
     */
    updateStageProgressCards(intersections) {
        const total = intersections.length;
        if (total === 0) return;

        const stages = ['installation', 'configuration', 'connection', 'validation'];

        stages.forEach(stage => {
            const counts = this.getStageStatusCounts(intersections, stage);
            const completedPct = Math.round((counts.completed / total) * 100);
            const inProgressPct = Math.round((counts.in_progress / total) * 100);
            const blockedPct = Math.round((counts.blocked / total) * 100);
            const notStartedPct = 100 - completedPct - inProgressPct - blockedPct;

            // Update progress bar segments
            const container = document.getElementById(`progress-${stage}`);
            if (container) {
                container.innerHTML = `
                    <div class="progress-segment completed" style="width: ${completedPct}%" title="Completed: ${counts.completed}"></div>
                    <div class="progress-segment in-progress" style="width: ${inProgressPct}%" title="In Progress: ${counts.in_progress}"></div>
                    <div class="progress-segment blocked" style="width: ${blockedPct}%" title="Blocked: ${counts.blocked}"></div>
                    <div class="progress-segment not-started" style="width: ${notStartedPct}%" title="Not Started: ${counts.not_started}"></div>
                `;
            }

            // Update status breakdown text
            const valueEl = document.getElementById(`progress-${stage}-value`);
            if (valueEl) {
                valueEl.innerHTML = `
                    <span class="status-count completed">${counts.completed}</span>
                    <span class="status-count in-progress">${counts.in_progress}</span>
                    <span class="status-count blocked">${counts.blocked}</span>
                    <span class="status-count not-started">${counts.not_started}</span>
                `;
            }
        });
    },

    /**
     * Update overall progress (Fully Working = all 4 stages completed)
     */
    updateOverallProgress(intersections) {
        const total = intersections.length;
        if (total === 0) return;

        // Helper to get status (supports both nested and flat formats)
        const getStatus = (i, stage) => {
            if (i[stage] && i[stage].status) return i[stage].status;
            return i[`${stage}_status`] || 'not_started';
        };

        // Count fully working intersections (all 4 stages completed)
        const fullyWorking = intersections.filter(i =>
            getStatus(i, 'installation') === 'completed' &&
            getStatus(i, 'configuration') === 'completed' &&
            getStatus(i, 'connection') === 'completed' &&
            getStatus(i, 'validation') === 'completed'
        ).length;

        const percentage = Math.round((fullyWorking / total) * 100);

        // Update circular progress
        const circle = document.getElementById('overall-progress-circle');
        if (circle) {
            const circumference = 2 * Math.PI * 45; // radius = 45
            const offset = circumference - (percentage / 100) * circumference;
            circle.style.strokeDasharray = circumference;
            circle.style.strokeDashoffset = offset;
        }

        // Update percentage text
        const pctEl = document.getElementById('overall-progress-pct');
        if (pctEl) {
            pctEl.textContent = `${percentage}%`;
        }

        // Update count text
        const countEl = document.getElementById('overall-progress-count');
        if (countEl) {
            countEl.textContent = `${fullyWorking} / ${total}`;
        }
    },

    /**
     * Render compact Lotto chart
     */
    renderCompactLottoChart(intersections) {
        const ctx = document.getElementById('chart-lotto');
        if (!ctx) return;

        if (this.charts.lotto) {
            this.charts.lotto.destroy();
        }

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
        const colors = labels.map(l => this.colors.lotto[l] || '#6b7280');

        this.charts.lotto = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: labels,
                datasets: [{
                    data: intersectionCounts,
                    backgroundColor: colors,
                    borderWidth: 2,
                    borderColor: '#ffffff'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                aspectRatio: 1.5,
                cutout: '60%',
                plugins: {
                    legend: {
                        position: 'right',
                        labels: {
                            boxWidth: 12,
                            padding: 8,
                            font: { size: 11 }
                        }
                    },
                    tooltip: {
                        callbacks: {
                            label: (context) => {
                                const lotto = labels[context.dataIndex];
                                return `${lotto}: ${data[lotto].intersections} intersections, ${data[lotto].radars} radars`;
                            }
                        }
                    }
                }
            }
        });
    },

    /**
     * Render compact System chart
     */
    renderCompactSystemChart(intersections) {
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
                maintainAspectRatio: true,
                aspectRatio: 1.5,
                cutout: '60%',
                plugins: {
                    legend: {
                        position: 'right',
                        labels: {
                            boxWidth: 12,
                            padding: 8,
                            font: { size: 11 }
                        }
                    }
                }
            }
        });
    },

    /**
     * Render stage status chart (stacked horizontal bars)
     */
    renderStageStatusChart(intersections) {
        const ctx = document.getElementById('chart-stage-status');
        if (!ctx) return;

        if (this.charts.stageStatus) {
            this.charts.stageStatus.destroy();
        }

        const stages = ['installation', 'configuration', 'connection', 'validation'];
        const statuses = ['completed', 'in_progress', 'blocked', 'not_started'];

        // Calculate data for each stage
        const data = {};
        stages.forEach(stage => {
            data[stage] = this.getStageStatusCounts(intersections, stage);
        });

        const datasets = statuses.map(status => ({
            label: this.statusLabels[status],
            data: stages.map(stage => data[stage][status]),
            backgroundColor: this.colors.status[status],
            borderWidth: 0
        }));

        this.charts.stageStatus = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: stages.map(s => s.charAt(0).toUpperCase() + s.slice(1)),
                datasets: datasets
            },
            options: {
                indexAxis: 'y',
                responsive: true,
                maintainAspectRatio: true,
                aspectRatio: 2,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            boxWidth: 12,
                            padding: 8,
                            font: { size: 10 }
                        }
                    }
                },
                scales: {
                    x: {
                        stacked: true,
                        beginAtZero: true,
                        grid: { display: false }
                    },
                    y: {
                        stacked: true,
                        grid: { display: false }
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
