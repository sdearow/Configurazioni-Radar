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
        this.renderFunnelChart(intersections);
        this.renderCompletenessChart(intersections);
        this.renderBlockingAnalysis(intersections);
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
     * Render Stage Funnel Chart - shows flow from Installation to Validation
     */
    renderFunnelChart(intersections) {
        const ctx = document.getElementById('chart-funnel');
        if (!ctx) return;

        if (this.charts.funnel) {
            this.charts.funnel.destroy();
        }

        const stages = ['installation', 'configuration', 'connection', 'validation'];
        const stageLabels = ['Installazione', 'Configurazione', 'Connessione', 'Validazione'];

        // Count completed at each stage
        const completedCounts = stages.map(stage => {
            return intersections.filter(i => {
                const status = i[stage]?.status || i[`${stage}_status`] || 'not_started';
                return status === 'completed';
            }).length;
        });

        // Count in_progress at each stage
        const inProgressCounts = stages.map(stage => {
            return intersections.filter(i => {
                const status = i[stage]?.status || i[`${stage}_status`] || 'not_started';
                return status === 'in_progress';
            }).length;
        });

        // Count blocked at each stage
        const blockedCounts = stages.map(stage => {
            return intersections.filter(i => {
                const status = i[stage]?.status || i[`${stage}_status`] || 'not_started';
                return status === 'blocked';
            }).length;
        });

        this.charts.funnel = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: stageLabels,
                datasets: [
                    {
                        label: 'Completato',
                        data: completedCounts,
                        backgroundColor: this.colors.status.completed,
                        borderRadius: 4
                    },
                    {
                        label: 'In Corso',
                        data: inProgressCounts,
                        backgroundColor: this.colors.status.in_progress,
                        borderRadius: 4
                    },
                    {
                        label: 'Bloccato',
                        data: blockedCounts,
                        backgroundColor: this.colors.status.blocked,
                        borderRadius: 4
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                aspectRatio: 2,
                onClick: (event, elements) => {
                    if (elements.length > 0) {
                        const element = elements[0];
                        const stage = stages[element.index];
                        const status = ['completed', 'in_progress', 'blocked'][element.datasetIndex];
                        this.drillDown(stage, status);
                    }
                },
                plugins: {
                    title: {
                        display: true,
                        text: 'Flusso Avanzamento per Fase',
                        font: { size: 14 }
                    },
                    legend: {
                        position: 'bottom',
                        labels: { boxWidth: 12, padding: 8, font: { size: 10 } }
                    },
                    tooltip: {
                        callbacks: {
                            afterLabel: () => 'Clicca per vedere dettagli'
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        title: { display: true, text: 'Intersezioni' }
                    }
                }
            }
        });
    },

    /**
     * Render Data Completeness Chart
     */
    renderCompletenessChart(intersections) {
        const ctx = document.getElementById('chart-completeness');
        if (!ctx) return;

        if (this.charts.completeness) {
            this.charts.completeness.destroy();
        }

        // Run validation to get completeness scores
        if (typeof DataValidator !== 'undefined') {
            DataValidator.validateAll();
            const scores = DataValidator.completenessScores;

            // Group by completeness range
            const ranges = {
                'Ottimo (80-100%)': 0,
                'Buono (60-79%)': 0,
                'Medio (40-59%)': 0,
                'Basso (0-39%)': 0
            };

            Object.values(scores).forEach(s => {
                if (s.overall >= 80) ranges['Ottimo (80-100%)']++;
                else if (s.overall >= 60) ranges['Buono (60-79%)']++;
                else if (s.overall >= 40) ranges['Medio (40-59%)']++;
                else ranges['Basso (0-39%)']++;
            });

            const labels = Object.keys(ranges);
            const data = Object.values(ranges);

            this.charts.completeness = new Chart(ctx, {
                type: 'doughnut',
                data: {
                    labels: labels,
                    datasets: [{
                        data: data,
                        backgroundColor: ['#22c55e', '#3b82f6', '#f59e0b', '#ef4444'],
                        borderWidth: 2,
                        borderColor: '#ffffff'
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: true,
                    aspectRatio: 1.5,
                    cutout: '50%',
                    onClick: (event, elements) => {
                        if (elements.length > 0) {
                            const idx = elements[0].index;
                            const ranges = [[80, 100], [60, 79], [40, 59], [0, 39]];
                            this.drillDownCompleteness(ranges[idx][0], ranges[idx][1]);
                        }
                    },
                    plugins: {
                        title: {
                            display: true,
                            text: 'Completezza Dati',
                            font: { size: 14 }
                        },
                        legend: {
                            position: 'right',
                            labels: { boxWidth: 12, padding: 6, font: { size: 10 } }
                        },
                        tooltip: {
                            callbacks: {
                                afterLabel: () => 'Clicca per vedere dettagli'
                            }
                        }
                    }
                }
            });
        }
    },

    /**
     * Render Blocking Analysis Chart
     */
    renderBlockingAnalysis(intersections) {
        const ctx = document.getElementById('chart-blocking');
        if (!ctx) return;

        if (this.charts.blocking) {
            this.charts.blocking.destroy();
        }

        // Analyze blocking reasons
        const blockingReasons = {};
        intersections.forEach(i => {
            const inst = i.installation || {};
            if (inst.status === 'blocked' || inst.blocked_conduits) {
                let reason = inst.soluzione_bloccati || inst.disp_inst_bloccati || 'Motivo non specificato';
                // Truncate long reasons
                if (reason.length > 40) reason = reason.substring(0, 37) + '...';
                blockingReasons[reason] = (blockingReasons[reason] || 0) + 1;
            }
        });

        // Sort by count and take top 8
        const sorted = Object.entries(blockingReasons)
            .sort((a, b) => b[1] - a[1])
            .slice(0, 8);

        if (sorted.length === 0) {
            ctx.parentElement.innerHTML = '<p class="no-data">Nessuna intersezione bloccata</p>';
            return;
        }

        const labels = sorted.map(([reason]) => reason);
        const data = sorted.map(([, count]) => count);

        this.charts.blocking = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Intersezioni Bloccate',
                    data: data,
                    backgroundColor: '#ef4444',
                    borderRadius: 4
                }]
            },
            options: {
                indexAxis: 'y',
                responsive: true,
                maintainAspectRatio: true,
                aspectRatio: 1.5,
                onClick: (event, elements) => {
                    if (elements.length > 0) {
                        const reason = labels[elements[0].index];
                        this.drillDownBlocking(reason);
                    }
                },
                plugins: {
                    title: {
                        display: true,
                        text: 'Analisi Blocchi per Motivo',
                        font: { size: 14 }
                    },
                    legend: { display: false },
                    tooltip: {
                        callbacks: {
                            afterLabel: () => 'Clicca per vedere dettagli'
                        }
                    }
                },
                scales: {
                    x: {
                        beginAtZero: true,
                        title: { display: true, text: 'Conteggio' }
                    },
                    y: {
                        ticks: {
                            font: { size: 9 },
                            callback: function(value) {
                                const label = this.getLabelForValue(value);
                                return label.length > 25 ? label.substring(0, 22) + '...' : label;
                            }
                        }
                    }
                }
            }
        });
    },

    /**
     * Render Lotto Comparison Chart (progress by lotto)
     */
    renderLottoComparison(intersections) {
        const ctx = document.getElementById('chart-lotto-comparison');
        if (!ctx) return;

        if (this.charts.lottoComparison) {
            this.charts.lottoComparison.destroy();
        }

        const stages = ['installation', 'configuration', 'connection', 'validation'];
        const lottos = ['M9.1', 'M9.2'];

        const datasets = lottos.map((lotto, idx) => {
            const lottoIntersections = intersections.filter(i => i.lotto === lotto);
            const total = lottoIntersections.length;

            const completedPcts = stages.map(stage => {
                const completed = lottoIntersections.filter(i => {
                    const status = i[stage]?.status || 'not_started';
                    return status === 'completed';
                }).length;
                return total > 0 ? Math.round((completed / total) * 100) : 0;
            });

            return {
                label: lotto,
                data: completedPcts,
                backgroundColor: this.colors.lotto[lotto],
                borderRadius: 4
            };
        });

        this.charts.lottoComparison = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: ['Installazione', 'Configurazione', 'Connessione', 'Validazione'],
                datasets: datasets
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                aspectRatio: 2,
                plugins: {
                    title: {
                        display: true,
                        text: 'Confronto Avanzamento Lotto 1 vs Lotto 2 (%)',
                        font: { size: 14 }
                    },
                    legend: {
                        position: 'bottom',
                        labels: { boxWidth: 12, padding: 8, font: { size: 10 } }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100,
                        title: { display: true, text: '% Completato' }
                    }
                }
            }
        });
    },

    /**
     * Render System Comparison Chart
     */
    renderSystemComparison(intersections) {
        const ctx = document.getElementById('chart-system-comparison');
        if (!ctx) return;

        if (this.charts.systemComparison) {
            this.charts.systemComparison.destroy();
        }

        const stages = ['installation', 'configuration', 'connection', 'validation'];
        const systems = ['Omnia', 'Tmacs'];

        const datasets = systems.map(system => {
            const systemIntersections = intersections.filter(i =>
                (i.system || '').toUpperCase() === system.toUpperCase()
            );
            const total = systemIntersections.length;

            const completedPcts = stages.map(stage => {
                const completed = systemIntersections.filter(i => {
                    const status = i[stage]?.status || 'not_started';
                    return status === 'completed';
                }).length;
                return total > 0 ? Math.round((completed / total) * 100) : 0;
            });

            return {
                label: system,
                data: completedPcts,
                backgroundColor: this.colors.system[system],
                borderRadius: 4
            };
        });

        this.charts.systemComparison = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: ['Installazione', 'Configurazione', 'Connessione', 'Validazione'],
                datasets: datasets
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                aspectRatio: 2,
                plugins: {
                    title: {
                        display: true,
                        text: 'Confronto Avanzamento Omnia vs Tmacs (%)',
                        font: { size: 14 }
                    },
                    legend: {
                        position: 'bottom',
                        labels: { boxWidth: 12, padding: 8, font: { size: 10 } }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100,
                        title: { display: true, text: '% Completato' }
                    }
                }
            }
        });
    },

    /**
     * Drill-down: show intersections filtered by stage and status
     */
    drillDown(stage, status) {
        const intersections = DataManager.getIntersections();
        const filtered = intersections.filter(i => {
            const s = i[stage]?.status || i[`${stage}_status`] || 'not_started';
            return s === status;
        });

        this.showDrillDownModal(
            `${stage.charAt(0).toUpperCase() + stage.slice(1)} - ${this.statusLabels[status]}`,
            filtered
        );
    },

    /**
     * Drill-down: show intersections by completeness range
     */
    drillDownCompleteness(minPct, maxPct) {
        if (typeof DataValidator === 'undefined') return;

        const scores = DataValidator.completenessScores;
        const intersections = DataManager.getIntersections();

        const filtered = intersections.filter(i => {
            const score = scores[i.id]?.overall || 0;
            return score >= minPct && score <= maxPct;
        });

        this.showDrillDownModal(
            `Completezza Dati: ${minPct}% - ${maxPct}%`,
            filtered,
            scores
        );
    },

    /**
     * Drill-down: show intersections by blocking reason
     */
    drillDownBlocking(reason) {
        const intersections = DataManager.getIntersections();
        const filtered = intersections.filter(i => {
            const inst = i.installation || {};
            const fullReason = inst.soluzione_bloccati || inst.disp_inst_bloccati || 'Motivo non specificato';
            return fullReason.includes(reason.replace('...', ''));
        });

        this.showDrillDownModal(`Blocco: ${reason}`, filtered);
    },

    /**
     * Show drill-down modal with filtered intersections
     */
    showDrillDownModal(title, intersections, scores = null) {
        // Create or get modal
        let modal = document.getElementById('drilldown-modal');
        if (!modal) {
            modal = document.createElement('div');
            modal.id = 'drilldown-modal';
            modal.className = 'modal';
            modal.innerHTML = `
                <div class="modal-content" style="max-width: 900px;">
                    <div class="modal-header">
                        <h3 id="drilldown-title"></h3>
                        <button class="modal-close" onclick="document.getElementById('drilldown-modal').classList.remove('active')">&times;</button>
                    </div>
                    <div class="modal-body" id="drilldown-body"></div>
                </div>
            `;
            document.body.appendChild(modal);
        }

        document.getElementById('drilldown-title').textContent = `${title} (${intersections.length} intersezioni)`;

        const tbody = intersections.map(i => {
            const scoreDisplay = scores && scores[i.id]
                ? `<span class="completeness-badge" style="background: ${this.getCompletenessColor(scores[i.id].overall)}">${scores[i.id].overall}%</span>`
                : '';

            return `
                <tr>
                    <td>${i.id}</td>
                    <td>${i.name || '-'}</td>
                    <td>${i.lotto || '-'}</td>
                    <td>${i.system || '-'}</td>
                    <td><span class="status-badge status-${i.installation?.status || 'not_started'}">${i.installation?.status || '-'}</span></td>
                    <td><span class="status-badge status-${i.configuration?.status || 'not_started'}">${i.configuration?.status || '-'}</span></td>
                    <td><span class="status-badge status-${i.connection?.status || 'not_started'}">${i.connection?.status || '-'}</span></td>
                    <td><span class="status-badge status-${i.validation?.status || 'not_started'}">${i.validation?.status || '-'}</span></td>
                    ${scores ? `<td>${scoreDisplay}</td>` : ''}
                    <td><button class="btn btn-small btn-primary" onclick="App.showIntersectionDetail('${i.id}'); document.getElementById('drilldown-modal').classList.remove('active');">Dettagli</button></td>
                </tr>
            `;
        }).join('');

        document.getElementById('drilldown-body').innerHTML = `
            <div style="max-height: 500px; overflow-y: auto;">
                <table class="data-table">
                    <thead>
                        <tr>
                            <th>ID</th>
                            <th>Nome</th>
                            <th>Lotto</th>
                            <th>Sistema</th>
                            <th>Inst.</th>
                            <th>Config.</th>
                            <th>Conn.</th>
                            <th>Valid.</th>
                            ${scores ? '<th>Compl.</th>' : ''}
                            <th>Azioni</th>
                        </tr>
                    </thead>
                    <tbody>${tbody}</tbody>
                </table>
            </div>
            <div style="margin-top: 1rem; text-align: right;">
                <button class="btn btn-secondary" onclick="ChartsManager.exportDrillDown('${title}')">Esporta Excel</button>
            </div>
        `;

        // Store for export
        this.lastDrillDown = { title, intersections, scores };

        modal.classList.add('active');
    },

    /**
     * Get color based on completeness score
     */
    getCompletenessColor(score) {
        if (score >= 80) return '#22c55e';
        if (score >= 60) return '#3b82f6';
        if (score >= 40) return '#f59e0b';
        return '#ef4444';
    },

    /**
     * Export drill-down data to Excel
     */
    exportDrillDown(title) {
        if (!this.lastDrillDown) return;

        const { intersections, scores } = this.lastDrillDown;
        const rows = [];

        // Header
        const header = ['ID', 'Nome', 'Lotto', 'Sistema', 'Installazione', 'Configurazione', 'Connessione', 'Validazione'];
        if (scores) header.push('Completezza %');
        rows.push(header);

        // Data
        intersections.forEach(i => {
            const row = [
                i.id,
                i.name || '',
                i.lotto || '',
                i.system || '',
                i.installation?.status || 'not_started',
                i.configuration?.status || 'not_started',
                i.connection?.status || 'not_started',
                i.validation?.status || 'not_started'
            ];
            if (scores && scores[i.id]) {
                row.push(scores[i.id].overall);
            }
            rows.push(row);
        });

        // Export using ExportManager if available
        if (typeof ExportManager !== 'undefined' && ExportManager.exportToExcel) {
            ExportManager.exportArrayToExcel(rows, `drilldown_${title.replace(/[^a-z0-9]/gi, '_')}`);
        } else {
            // Fallback: download as CSV
            const csv = rows.map(r => r.join(',')).join('\n');
            const blob = new Blob([csv], { type: 'text/csv' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `drilldown_${title.replace(/[^a-z0-9]/gi, '_')}.csv`;
            a.click();
        }
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
