/**
 * Tasks Module
 * Handles task management functionality
 */

const TasksManager = {
    currentFilter: {
        status: '',
        assignee: ''
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

        // Task form save
        const saveBtn = document.getElementById('task-save');
        if (saveBtn) {
            saveBtn.addEventListener('click', () => this.saveTask());
        }

        // Filter changes
        const statusFilter = document.getElementById('task-filter-status');
        if (statusFilter) {
            statusFilter.addEventListener('change', (e) => {
                this.currentFilter.status = e.target.value;
                this.render();
            });
        }

        const assigneeFilter = document.getElementById('task-filter-assignee');
        if (assigneeFilter) {
            assigneeFilter.addEventListener('change', (e) => {
                this.currentFilter.assignee = e.target.value;
                this.render();
            });
        }
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
        this.renderColumn('tasks-pending', pending);
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
    },

    /**
     * Create task card HTML
     */
    createTaskCard(task) {
        const assignee = this.assignees.find(a => a.id === task.assignee);
        const assigneeName = assignee ? assignee.name : task.assignee || 'Unassigned';

        const intersection = task.intersection_id ?
            DataManager.getIntersection(task.intersection_id) : null;

        const dueDate = task.due_date ?
            new Date(task.due_date).toLocaleDateString('it-IT') : '';

        return `
            <div class="task-card priority-${task.priority || 'medium'}" data-task-id="${task.id}">
                <div class="task-title">${this.escapeHtml(task.title)}</div>
                <div class="task-meta">
                    ${assigneeName ? `<span>${assigneeName}</span>` : ''}
                    ${dueDate ? `<span>${dueDate}</span>` : ''}
                </div>
                ${intersection ? `<div class="task-meta"><span>@ ${intersection.name}</span></div>` : ''}
            </div>
        `;
    },

    /**
     * Open task modal (create or edit)
     */
    openTaskModal(taskId = null) {
        const modal = document.getElementById('task-modal');
        const title = document.getElementById('task-modal-title');
        const form = document.getElementById('task-form');

        // Populate intersection dropdown
        this.populateIntersectionSelect();

        if (taskId) {
            // Edit mode
            const task = DataManager.getTask(taskId);
            if (!task) return;

            title.textContent = 'Edit Task';
            document.getElementById('task-title').value = task.title || '';
            document.getElementById('task-description').value = task.description || '';
            document.getElementById('task-intersection').value = task.intersection_id || '';
            document.getElementById('task-assignee').value = task.assignee || '';
            document.getElementById('task-due-date').value = task.due_date || '';
            document.getElementById('task-priority').value = task.priority || 'medium';

            form.dataset.taskId = taskId;
        } else {
            // Create mode
            title.textContent = 'Add Task';
            form.reset();
            delete form.dataset.taskId;
        }

        modal.classList.add('active');
    },

    /**
     * Populate intersection select dropdown
     */
    populateIntersectionSelect() {
        const select = document.getElementById('task-intersection');
        if (!select) return;

        const intersections = DataManager.getIntersections();

        select.innerHTML = '<option value="">None</option>' +
            intersections.map(i => `<option value="${i.id}">${i.id} - ${i.name}</option>`).join('');
    },

    /**
     * Save task (create or update)
     */
    saveTask() {
        const form = document.getElementById('task-form');
        const taskId = form.dataset.taskId;

        const taskData = {
            title: document.getElementById('task-title').value,
            description: document.getElementById('task-description').value,
            intersection_id: document.getElementById('task-intersection').value || null,
            assignee: document.getElementById('task-assignee').value || null,
            due_date: document.getElementById('task-due-date').value || null,
            priority: document.getElementById('task-priority').value
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
        document.getElementById('task-modal').classList.remove('active');
        this.render();
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
    createTaskForIntersection(intersectionId, defaultTitle = '') {
        const intersection = DataManager.getIntersection(intersectionId);
        if (!intersection) return;

        // Pre-fill form
        document.getElementById('task-title').value = defaultTitle || `Work on ${intersection.name}`;
        document.getElementById('task-intersection').value = intersectionId;

        this.openTaskModal();
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
