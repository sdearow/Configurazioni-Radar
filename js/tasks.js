/**
 * Tasks Module
 * Handles task management functionality with stage/substage selection
 * and batch task creation
 */

const TasksManager = {
    currentFilter: {
        status: '',
        assignee: ''
    },

    // Batch task selection
    batchSelectedIntersections: new Set(),

    // Stage substages definition
    substages: {
        installation: [
            'Planimetrie ricevute',
            'Passaggio cavi',
            'Planimetria scavi inviata a RSM',
            'Installazione sensori',
            'Cablaggio regolatore',
            'Screenshot',
            'Completato',
            'Documentazione inviata',
            'Data completamento'
        ],
        configuration: [
            'Configurazione base',
            'Configurazione Definitiva - Assegnata',
            'Configurazione Definitiva - Da Verificare',
            'Configurazione Definitiva - Implementata in sito'
        ],
        connection: [
            'SPOT STATUS',
            'AUT STATUS',
            'Tabella Interfaccia UTC',
            'Connessione UTC attiva',
            'Verifica comunicazione'
        ],
        validation: [
            'Data lake sending',
            'Verifica dati di traffic',
            'Interfaccia Visum/Optima',
            'Validazione finale'
        ]
    },

    assignees: [
        { id: 'GT', name: 'Giacomo Tuffanelli' },
        { id: 'AV', name: 'Alessandro Vangi' },
        { id: 'MC', name: 'Marisdea Castiglione' },
        { id: 'FM', name: 'Francesco Masucci' },
        { id: 'ENG', name: 'Engin' },
        { id: 'Sonet', name: 'Sonet' },
        { id: 'M9.2', name: 'Lotto M9.2' },
        { id: 'Swarco', name: 'Swarco' },
        { id: 'Semaforica', name: 'Semaforica' }
    ],

    /**
     * Initialize tasks module
     */
    init() {
        this.bindEvents();
        return this;
    },

    /**
     * Bind event listeners
     */
    bindEvents() {
        // Add task button
        const addBtn = document.getElementById('add-task-btn');
        if (addBtn) {
            addBtn.addEventListener('click', () => this.openTaskModal());
        }

        // Batch task button
        const batchBtn = document.getElementById('batch-task-btn');
        if (batchBtn) {
            batchBtn.addEventListener('click', () => this.openBatchTaskModal());
        }

        // Save task button
        const saveBtn = document.getElementById('save-task-btn');
        if (saveBtn) {
            saveBtn.addEventListener('click', () => this.saveTask());
        }

        // Save batch tasks button
        const saveBatchBtn = document.getElementById('save-batch-tasks-btn');
        if (saveBatchBtn) {
            saveBatchBtn.addEventListener('click', () => this.saveBatchTasks());
        }

        // Stage selection - update substage options
        const stageSelect = document.getElementById('task-stage');
        if (stageSelect) {
            stageSelect.addEventListener('change', (e) => {
                this.updateSubstageOptions(e.target.value, 'task-substage');
            });
        }

        // Batch stage selection
        const batchStageSelect = document.getElementById('batch-task-stage');
        if (batchStageSelect) {
            batchStageSelect.addEventListener('change', (e) => {
                this.updateSubstageOptions(e.target.value, 'batch-task-substage');
            });
        }

        // Modal close buttons
        document.querySelectorAll('.modal-close').forEach(btn => {
            btn.addEventListener('click', () => {
                const modal = btn.closest('.modal');
                if (modal) modal.classList.remove('active');
            });
        });
    },

    /**
     * Update substage options based on selected stage
     */
    updateSubstageOptions(stage, selectId) {
        const select = document.getElementById(selectId);
        if (!select) return;

        const substages = this.substages[stage] || [];

        select.innerHTML = '<option value="">Select substage...</option>' +
            substages.map(s => `<option value="${s}">${s}</option>`).join('');
    },

    /**
     * Render tasks in columns
     */
    render() {
        const tasks = DataManager.getTasks();

        // Filter tasks
        let filteredTasks = tasks;
        if (this.currentFilter.status) {
            filteredTasks = filteredTasks.filter(t => t.status === this.currentFilter.status);
        }
        if (this.currentFilter.assignee) {
            filteredTasks = filteredTasks.filter(t => t.assignee === this.currentFilter.assignee);
        }

        // Group by status
        const pending = filteredTasks.filter(t => t.status === 'pending');
        const inProgress = filteredTasks.filter(t => t.status === 'in_progress');
        const completed = filteredTasks.filter(t => t.status === 'completed');

        // Render columns
        this.renderColumn('tasks-todo', pending);
        this.renderColumn('tasks-in-progress', inProgress);
        this.renderColumn('tasks-completed', completed);
    },

    /**
     * Render a single column of tasks
     */
    renderColumn(containerId, tasks) {
        const container = document.getElementById(containerId);
        if (!container) return;

        if (tasks.length === 0) {
            container.innerHTML = '<div class="text-muted" style="text-align: center; padding: 1rem;">No tasks</div>';
            return;
        }

        container.innerHTML = tasks.map(task => this.createTaskCard(task)).join('');

        // Bind click events
        container.querySelectorAll('.task-card').forEach(card => {
            card.addEventListener('click', () => {
                this.openTaskModal(card.dataset.taskId);
            });
        });

        // Status change dropdown
        container.querySelectorAll('.task-status-select').forEach(select => {
            select.addEventListener('click', (e) => e.stopPropagation());
            select.addEventListener('change', (e) => {
                const taskId = e.target.dataset.taskId;
                this.updateTaskStatus(taskId, e.target.value);
            });
        });

        // Delete button
        container.querySelectorAll('.task-delete-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                this.deleteTask(btn.dataset.taskId);
            });
        });
    },

    /**
     * Create task card HTML
     */
    createTaskCard(task) {
        const assignee = this.assignees.find(a => a.id === task.assignee);
        const assigneeName = assignee ? assignee.name : task.assignee || 'Unassigned';

        const intersection = task.intersection_id ?
            DataManager.getIntersection(task.intersection_id) : null;

        const stageBadge = task.stage ?
            `<span class="badge badge-${task.stage}">${this.capitalizeFirst(task.stage)}</span>` : '';

        const substageText = task.substage ?
            `<span class="task-substage">${task.substage}</span>` : '';

        return `
            <div class="task-card priority-${task.priority || 'medium'}" data-task-id="${task.id}">
                <div class="task-header">
                    <div class="task-title">${this.escapeHtml(task.title)}</div>
                    <button class="btn btn-small task-delete-btn" data-task-id="${task.id}" title="Delete">&times;</button>
                </div>
                ${stageBadge ? `<div class="task-stage">${stageBadge} ${substageText}</div>` : ''}
                <div class="task-meta">
                    ${assigneeName ? `<span>${assigneeName}</span>` : ''}
                </div>
                ${intersection ? `<div class="task-location">@ ${intersection.name}</div>` : ''}
                <div class="task-actions">
                    <select class="task-status-select" data-task-id="${task.id}">
                        <option value="pending" ${task.status === 'pending' ? 'selected' : ''}>To Do</option>
                        <option value="in_progress" ${task.status === 'in_progress' ? 'selected' : ''}>In Progress</option>
                        <option value="completed" ${task.status === 'completed' ? 'selected' : ''}>Completed</option>
                    </select>
                </div>
            </div>
        `;
    },

    /**
     * Open task modal (create or edit)
     */
    openTaskModal(taskId = null) {
        const modal = document.getElementById('task-modal');
        const title = document.getElementById('task-modal-title');

        // Populate intersection dropdown
        this.populateIntersectionSelect('task-intersection');

        // Reset form
        document.getElementById('task-title').value = '';
        document.getElementById('task-description').value = '';
        document.getElementById('task-intersection').value = '';
        document.getElementById('task-stage').value = '';
        document.getElementById('task-substage').innerHTML = '<option value="">Select substage...</option>';
        document.getElementById('task-priority').value = 'medium';
        document.getElementById('task-assignee').value = '';

        if (taskId) {
            // Edit mode
            const task = DataManager.getTask(taskId);
            if (!task) return;

            title.textContent = 'Edit Task';
            document.getElementById('task-title').value = task.title || '';
            document.getElementById('task-description').value = task.description || '';
            document.getElementById('task-intersection').value = task.intersection_id || '';
            document.getElementById('task-stage').value = task.stage || '';
            if (task.stage) {
                this.updateSubstageOptions(task.stage, 'task-substage');
                document.getElementById('task-substage').value = task.substage || '';
            }
            document.getElementById('task-priority').value = task.priority || 'medium';
            document.getElementById('task-assignee').value = task.assignee || '';

            modal.dataset.taskId = taskId;
        } else {
            // Create mode
            title.textContent = 'Add Task';
            delete modal.dataset.taskId;
        }

        modal.classList.add('active');
    },

    /**
     * Open batch task modal
     */
    openBatchTaskModal() {
        const modal = document.getElementById('batch-task-modal');
        if (!modal) return;

        // Clear selections
        this.batchSelectedIntersections.clear();

        // Populate intersection list
        this.populateBatchIntersectionList();

        // Reset form fields
        document.getElementById('batch-task-stage').value = '';
        document.getElementById('batch-task-title').value = '';
        document.getElementById('batch-task-description').value = '';
        document.getElementById('batch-task-assignee').value = '';

        // Update count
        this.updateBatchSelectedCount();

        modal.classList.add('active');
    },

    /**
     * Populate batch intersection list
     */
    populateBatchIntersectionList() {
        const container = document.getElementById('batch-intersection-list');
        if (!container) return;

        const intersections = DataManager.getIntersections();

        container.innerHTML = intersections.map(i => `
            <label class="batch-intersection-item">
                <input type="checkbox" value="${i.id}" class="batch-intersection-checkbox">
                <span class="batch-intersection-info">
                    <strong>${i.id}</strong> - ${i.name || 'Unknown'}
                    <span class="batch-intersection-meta">${i.lotto || ''} | ${i.system || ''}</span>
                </span>
            </label>
        `).join('');

        // Bind checkbox events
        container.querySelectorAll('.batch-intersection-checkbox').forEach(checkbox => {
            checkbox.addEventListener('change', (e) => {
                if (e.target.checked) {
                    this.batchSelectedIntersections.add(e.target.value);
                } else {
                    this.batchSelectedIntersections.delete(e.target.value);
                }
                this.updateBatchSelectedCount();
            });
        });
    },

    /**
     * Select all batch intersections
     */
    selectAllBatch() {
        const checkboxes = document.querySelectorAll('.batch-intersection-checkbox');
        checkboxes.forEach(cb => {
            cb.checked = true;
            this.batchSelectedIntersections.add(cb.value);
        });
        this.updateBatchSelectedCount();
    },

    /**
     * Select none batch intersections
     */
    selectNoneBatch() {
        const checkboxes = document.querySelectorAll('.batch-intersection-checkbox');
        checkboxes.forEach(cb => {
            cb.checked = false;
        });
        this.batchSelectedIntersections.clear();
        this.updateBatchSelectedCount();
    },

    /**
     * Update batch selected count
     */
    updateBatchSelectedCount() {
        const countEl = document.getElementById('batch-selected-count');
        if (countEl) {
            countEl.textContent = this.batchSelectedIntersections.size;
        }
    },

    /**
     * Populate intersection select dropdown
     */
    populateIntersectionSelect(selectId) {
        const select = document.getElementById(selectId);
        if (!select) return;

        const intersections = DataManager.getIntersections();

        select.innerHTML = '<option value="">None</option>' +
            intersections.map(i => `<option value="${i.id}">${i.id} - ${i.name || 'Unknown'}</option>`).join('');
    },

    /**
     * Save task (create or update)
     */
    saveTask() {
        const modal = document.getElementById('task-modal');
        const taskId = modal.dataset.taskId;

        const taskData = {
            title: document.getElementById('task-title').value,
            description: document.getElementById('task-description').value,
            intersection_id: document.getElementById('task-intersection').value || null,
            stage: document.getElementById('task-stage').value || null,
            substage: document.getElementById('task-substage').value || null,
            priority: document.getElementById('task-priority').value,
            assignee: document.getElementById('task-assignee').value || null
        };

        if (!taskData.title) {
            alert('Title is required');
            return;
        }

        if (taskId) {
            // Update existing task
            DataManager.updateTask(taskId, taskData);
        } else {
            // Create new task
            DataManager.addTask(taskData);
        }

        // Close modal and refresh
        modal.classList.remove('active');
        this.render();
    },

    /**
     * Save batch tasks
     */
    saveBatchTasks() {
        const title = document.getElementById('batch-task-title').value;
        const description = document.getElementById('batch-task-description').value;
        const stage = document.getElementById('batch-task-stage').value || null;
        const assignee = document.getElementById('batch-task-assignee').value || null;

        if (!title) {
            alert('Title is required');
            return;
        }

        if (this.batchSelectedIntersections.size === 0) {
            alert('Please select at least one intersection');
            return;
        }

        // Create a task for each selected intersection
        this.batchSelectedIntersections.forEach(intersectionId => {
            DataManager.addTask({
                title: title,
                description: description,
                intersection_id: intersectionId,
                stage: stage,
                assignee: assignee,
                priority: 'medium',
                status: 'pending'
            });
        });

        // Close modal and refresh
        document.getElementById('batch-task-modal').classList.remove('active');
        this.render();

        alert(`Created ${this.batchSelectedIntersections.size} tasks successfully!`);
    },

    /**
     * Update task status
     */
    updateTaskStatus(taskId, newStatus) {
        DataManager.updateTask(taskId, { status: newStatus });
        this.render();
    },

    /**
     * Delete task
     */
    deleteTask(taskId) {
        if (confirm('Are you sure you want to delete this task?')) {
            DataManager.deleteTask(taskId);
            this.render();
        }
    },

    /**
     * Create task from intersection (quick add)
     */
    createTaskForIntersection(intersectionId, defaultTitle = '', stage = null) {
        const intersection = DataManager.getIntersection(intersectionId);
        if (!intersection) return;

        // Pre-fill form
        this.openTaskModal();
        document.getElementById('task-title').value = defaultTitle || `Work on ${intersection.name}`;
        document.getElementById('task-intersection').value = intersectionId;
        if (stage) {
            document.getElementById('task-stage').value = stage;
            this.updateSubstageOptions(stage, 'task-substage');
        }
    },

    /**
     * Capitalize first letter
     */
    capitalizeFirst(str) {
        return str.charAt(0).toUpperCase() + str.slice(1);
    },

    /**
     * Escape HTML to prevent XSS
     */
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
};
