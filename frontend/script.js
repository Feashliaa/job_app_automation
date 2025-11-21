/**
 * Job Search Dashboard
 **/

class JobApp {
    constructor() {
        this.allJobs = [];
        this.sortState = { key: null, direction: 'asc' };
        this.filterState = { title: '', company: '', location: '', status: '', salary: '' };
        this.choices = null;
        this.debounceTimer = null;
        this.loggedIn = false;
        this.lastToastMessage = null;
        this.lastToastTime = 0;

        // Column config matches original table
        this.columns = [
            { key: 'JobTitle', label: 'Job Title' },
            { key: 'Company', label: 'Company' },
            { key: 'Location', label: 'Location' },
            { key: 'Salary', label: 'Salary', render: job => this.escape(job.Salary || 'N/A') },
            {
                key: 'URL',
                label: 'Job URL',
                render: job => job.URL
                    ? `<a href="${this.escape(job.URL)}" target="_blank" class="btn btn-sm btn-outline-primary" title="Open job">Link</a>`
                    : ''
            },
            { key: 'JobScore', label: 'Job Score', render: job => this.escape(job.JobScore || 'N/A') },
            {
                key: 'Status',
                label: 'Job Status',
                render: job => {
                    const status = job.Status || '';
                    const cls = status.toLowerCase() || 'secondary';
                    return `<span class="badge bg-secondary ${cls}">${this.escape(status)}</span>`;
                }
            },
            { key: 'DateFound', label: 'Date Found', render: job => this.escape(job.DateFound || '') },
            {
                key: 'Remove',
                label: 'Remove',
                render: job => `<input type="checkbox" class="form-check-input checkbox-lg remove-checkbox" data-job-id="${this.escape(job.URL || '')}">`
            },
            {
                key: 'Apply',
                label: 'Apply',
                render: job => `<input type="checkbox" class="form-check-input checkbox-lg apply-checkbox" data-job-id="${this.escape(job.URL || '')}">`
            }
        ];

        this.keyMap = Object.fromEntries(
            this.columns.map(col => [col.label, col.key])
        );
    }

    // Safe HTML escaping
    escape(str) {
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    }

    init() {
        this.setupChoices();
        this.setupEventListeners();
        this.checkSession();
    }

    setupChoices() {
        const el = document.getElementById('job-title');
        this.choices = new Choices(el, {
            searchEnabled: true,
            searchChoices: true,
            addItems: true,
            addChoices: true,
            duplicateItemsAllowed: false,
            shouldSort: false,
            removeItemButton: true,
            placeholderValue: '--Choose--',
            searchPlaceholderValue: 'Type or select a job title',
            itemSelectText: '',
            maxItemCount: 1
        });
        el.addEventListener('focus', () => this.choices.showDropdown());
    }

    setupEventListeners() {
        const form = document.getElementById('jobForm');
        form.addEventListener('submit', e => this.handleSubmit(e));

        document.getElementById('refresh').addEventListener('click', () => {
            this.setUIBusy(true);
            // check if logged in
            if (!this.loggedIn) {
                this.showToast('Please log in first.', 'danger');
                return;
            }

            try {
                this.refreshJobs(false);
            } catch (err) {
                this.showToast('Failed to refresh jobs.', 'danger');
                console.error(err);
            } finally {
                this.setUIBusy(false);
            }
        });

        document.getElementById('event-handler').addEventListener('click', () => this.handleBatch());
        document.getElementById('process-fab').addEventListener('click', () => this.handleBatch());

        // Filter toggle
        document.querySelector('.filter-toggle').addEventListener('click', () => {
            const toggle = document.querySelector('.filter-toggle');
            const controls = document.getElementById('filter-controls');
            const expanded = toggle.getAttribute('aria-expanded') === 'true';

            // open/close styles
            controls.style.display = expanded ? 'none' : 'flex';
            toggle.setAttribute('aria-expanded', !expanded);

            if (expanded) {
                toggle.classList.remove('open');
            } else {
                toggle.classList.add('open');
            }
        });

        // Filter inputs (debounced)
        document.querySelectorAll('.filter-controls input, .filter-controls select').forEach(input => {
            input.addEventListener('input', () => {
                const key = input.id.replace('filter-', '');
                this.filterState[key] = input.value.trim();
                this.debounceRender();
            });
        });

        // Clear filters
        document.querySelector('.clear-filters').addEventListener('click', () => {
            this.filterState = { title: '', company: '', location: '', status: '' };
            document.querySelectorAll('.filter-controls input, .filter-controls select').forEach(i => i.value = '');
            this.render();
        });

        // Sorting (disable sort for Apply and Remove columns)
        document.querySelectorAll('.job-table thead th').forEach(th => {
            const label = th.textContent.trim();
            if (label === 'Apply' || label === 'Remove') {
                th.classList.add('no-sort');
                return;
            }
            th.addEventListener('click', () => this.handleSort(th));
        });

        // Handle Resume Parsing
        document.getElementById("resumeForm").addEventListener("submit", async (e) => {
            e.preventDefault(); // stops redirect

            // check if logged in
            if (!this.loggedIn) {
                this.showToast('Please log in first.', 'danger');
                return;
            }

            const fileInput = document.getElementById("resumeFile");
            if (!fileInput.files || fileInput.files.length === 0) {
                this.showToast('Please Select a Resume to Parse.', 'danger')
                return;
            }

            const formData = new FormData();
            formData.append("resumeFile", fileInput.files[0]);

            try {
                const res = await fetch("/resume_handler", { method: "POST", body: formData });
                const data = await res.json();
                console.log("Parsed resume: ", data);
                this.showToast('Resume uploaded and parsed successfully.', 'success');
            } catch (err) {
                console.error("Error uploading resume: ", err);
            }
        });

        // Auth dropdown handlers
        const authForm = document.getElementById('authForm');
        const registerBtn = document.getElementById('registerBtn');
        const logoutBtn = document.getElementById('logoutBtn');

        authForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const email = document.getElementById('email').value.trim();
            const password = document.getElementById('password').value.trim();

            if (!email || !password) {
                this.showToast('Email and password required.', 'danger');
                return;
            }

            this.setUIBusy(true);

            try {
                const res = await fetch('/login', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ email, password }),
                    credentials: 'include'
                });
                if (!res.ok) throw new Error('Login failed');
                const data = await res.json();
                this.showToast(`Welcome, ${data.user || 'User'}.`, 'success');
                document.getElementById('authDropdown').textContent = 'Logged In';
                logoutBtn.style.display = 'block';
                this.loggedIn = true;
                await this.refreshJobs(true)
            } catch (err) {
                this.showToast('Invalid credentials.', 'danger');
                console.error(err);
            } finally {
                this.setUIBusy(false);
            }
        });

        registerBtn.addEventListener('click', async () => {
            const email = document.getElementById('email').value.trim();
            const password = document.getElementById('password').value.trim();

            if (!email || !password) {
                this.showToast('Email and password required.', 'danger');
                return;
            }

            this.setUIBusy(true);

            try {
                const res = await fetch('/register', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ email, password }),
                    credentials: 'include'
                });
                if (!res.ok) throw new Error('Registration failed');
                const data = await res.json();
                this.showToast(`Account created for ${data.user || 'user'}.`, 'success');
                document.getElementById('authDropdown').textContent = 'Logged In';
                this.loggedIn = true;
                logoutBtn.style.display = 'block';
            } catch (err) {
                this.showToast('Registration failed.', 'danger');
                console.error(err);
            } finally {
                this.setUIBusy(false);
            }
        });

        logoutBtn.addEventListener('click', async () => {
            const res = await fetch('/logout', { method: 'POST', credentials: 'include' });
            if (res.ok) {
                this.showToast('Logged out successfully.', 'success');
                document.getElementById('authDropdown').textContent = 'Login / Register';
                logoutBtn.style.display = 'none';
                authForm.reset();
                this.allJobs = [];
                this.render();
            }
        });
    }

    setUIBusy(isBusy) {
        const controls = [
            '#searchBtn',
            '#refresh',
            '#event-handler',
            '#process-fab',
            '#resumeSubmit',
            '.clear-filters',
            '#registerBtn',
            '#logoutBtn',
        ];
        controls.forEach(sel => {
            const el = document.querySelector(sel);
            if (el) el.disabled = isBusy;
        });
        document.body.style.cursor = isBusy ? 'wait' : 'default';
    }

    async checkSession() {
        try {
            const res = await fetch('/session_status', { credentials: 'include' });
            const data = await res.json();
            const logoutBtn = document.getElementById('logoutBtn');
            this.loggedIn = data.logged_in;
            if (data.logged_in) {
                document.getElementById('authDropdown').textContent = 'Logged In';
                logoutBtn.style.display = 'block';
                await this.refreshJobs(false);
            } else {
                document.getElementById('authDropdown').textContent = 'Login / Register';
                logoutBtn.style.display = 'none';
            }
        } catch (err) {
            console.error('Error checking session status:', err);
        }
    }

    async handleSubmit(e) {
        e.preventDefault();

        // check if logged in
        if (!this.loggedIn) {
            this.showToast('Please log in first.', 'danger');
            return;
        }

        // Gather form data
        const datePosted = document.getElementById('date-posted').value?.trim();
        const experienceLevel = document.getElementById('experience').value?.trim();
        const jobTitle = this.choices.getValue(true);
        const location = document.getElementById('location').value?.trim();

        if (!datePosted || !experienceLevel || !jobTitle) {
            this.showToast('All fields are required.', 'danger');
            return;
        }
        const payload = { datePosted, experienceLevel, jobTitle, location };

        // Disable UI during submission
        this.setUIBusy(true);
        this.showLoadingToast('Searching . . . . . . .');

        try {
            const res = await fetch('/add_job_request', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload),
                credentials: 'include'
            });
            if (!res.ok) throw new Error('Submission failed');

            const data = await res.json();
            this.allJobs = data.jobs || [];

            // Reset form
            document.getElementById('jobForm').reset();
            this.choices.clearInput();
            this.render();

            // Success toast
            this.showToast('Job search submitted successfully!', 'success');
        } catch (err) {
            this.showToast('Failed to submit job search.', 'danger');
            console.error(err);
        }
        finally {
            // Re-enable UI
            this.setUIBusy(false);
        }
    }

    async refreshJobs(silent = false) {
        this.setUIBusy(true);
        try {
            const res = await fetch('/refresh_jobs', {
                credentials: 'include'
            });
            const data = await res.json();
            this.allJobs = data.jobs || [];
            this.render();
            if (!silent) this.showToast('Job listings updated.', 'success');
        } catch (err) {
            if (!silent) this.showToast('Failed to load jobs.', 'danger');
            console.error(err);
        } finally {
            this.setUIBusy(false);
        }
    }

    debounceRender() {
        clearTimeout(this.debounceTimer);
        this.debounceTimer = setTimeout(() => this.render(), 300);
    }

    handleSort(th) {
        const label = th.textContent.trim();
        const key = this.keyMap[label];
        if (!key) return;

        if (this.sortState.key === key) {
            this.sortState.direction = this.sortState.direction === 'asc' ? 'desc' : 'asc';
        } else {
            this.sortState.key = key;
            this.sortState.direction = 'asc';
        }
        this.render();
    }

    parseSalary(salaryString) {
        if (!salaryString) return null;

        // Remove $, commas, whitespace
        let s = salaryString.replace(/\$/g, '').replace(/,/g, '').trim().toLowerCase();

        // Detect hourly or yearly
        const isHourly = s.includes('/hr');
        const isYearly = s.includes('/yr') || s.includes('/year');

        // Extract numeric part before /hr or /yr
        let parts = s.split('/')[0];
        let range = parts.split('-').map(x => x.trim());

        const convert = (val) => {
            if (!val) return null;
            if (val.includes('k')) return parseFloat(val) * 1000;
            return parseFloat(val);
        };

        let min = convert(range[0]);
        let max = convert(range[1] ?? range[0]);

        if (min == null || isNaN(min)) return null;

        // Normalize hourly → yearly
        if (isHourly) {
            min *= 2080;
            max *= 2080;
        }

        return { min, max };
    }

    getFilteredAndSortedJobs() {
        let jobs = [...this.allJobs];

        const salaryFilter = this.filterState.salary
            ? parseInt(this.filterState.salary, 10)
            : null;

        // Filter
        jobs = jobs.filter(job => {
            // Text filters
            const matchesText =
                (!this.filterState.title ||
                    job.JobTitle?.toLowerCase().includes(this.filterState.title.toLowerCase())) &&
                (!this.filterState.company ||
                    job.Company?.toLowerCase().includes(this.filterState.company.toLowerCase())) &&
                (!this.filterState.location ||
                    job.Location?.toLowerCase().includes(this.filterState.location.toLowerCase())) &&
                (!this.filterState.status ||
                    job.Status === this.filterState.status);

            if (!matchesText) return false;

            // Salary filter
            if (salaryFilter) {
                const parsed = this.parseSalary(job.Salary);
                if (!parsed) return false;

                // allow match if salary range reaches user's minimum
                if (parsed.max < salaryFilter) return false;
            }

            return true;
        });

        // Prioritize "New"
        jobs.sort((a, b) => {
            if (a.Status === 'New' && b.Status !== 'New') return -1;
            if (a.Status !== 'New' && b.Status === 'New') return 1;
            return 0;
        });

        // User sort
        if (this.sortState.key) {
            const { key, direction } = this.sortState;
            const asc = direction === 'asc';

            if (key === 'Status') {
                const order = { 'New': 0, 'Applied': 1, 'Interview': 2, 'Rejected': 3, 'Ignored': 4 };
                jobs.sort((a, b) => {
                    const aVal = order[a[key]] ?? 99;
                    const bVal = order[b[key]] ?? 99;
                    return asc ? aVal - bVal : bVal - aVal;
                });
            } else {
                jobs.sort((a, b) => {
                    const aVal = (a[key] ?? '').toString();
                    const bVal = (b[key] ?? '').toString();
                    return (aVal > bVal ? 1 : -1) * (asc ? 1 : -1);
                });
            }
        }
        return jobs;
    }

    render() {
        const jobs = this.getFilteredAndSortedJobs();
        const tbody = document.querySelector('#results tbody');
        const results = document.getElementById('results');

        tbody.innerHTML = '';

        if (jobs.length === 0) {
            const row = document.createElement('tr');
            const cell = document.createElement('td');
            cell.colSpan = this.columns.length;
            cell.textContent = 'No job applications found.';
            cell.style.textAlign = 'center';
            cell.style.padding = '2rem';
            row.appendChild(cell);
            tbody.appendChild(row);
            results.style.display = 'block';
            this.updateSortIndicators();
            return;
        }

        jobs.forEach(job => {
            const row = document.createElement('tr');
            row.innerHTML = this.columns.map(col => {
                const value = col.render ? col.render(job) : this.escape(job[col.key] || '');
                const classes = [];
                if (['Remove', 'Apply'].includes(col.key)) classes.push('checkbox-cell');
                if (col.key === 'Remove') classes.push('remove');
                if (col.key === 'Apply') classes.push('apply');
                return `<td class="${classes.join(' ')}" data-label="${col.label}">${value}</td>`;
            }).join('');
            tbody.appendChild(row);
        });

        results.style.display = 'block';
        this.updateSortIndicators();
    }

    updateSortIndicators() {
        document.querySelectorAll('.job-table thead th').forEach(th => {
            th.classList.remove('sorted-asc', 'sorted-desc');
            const label = th.textContent.trim();
            const key = this.keyMap[label];
            if (key === this.sortState.key) {
                th.classList.add(this.sortState.direction === 'asc' ? 'sorted-asc' : 'sorted-desc');
            }
        });
    }

    async handleBatch() {
        this.setUIBusy(true);
        try {
            // if there are no jobs rendered at all
            if (!this.allJobs || this.allJobs.length === 0) {
                this.showToast('No jobs available to process.', 'warning');
                return;
            }

            // gather all checked boxes
            const selected = document.querySelectorAll('.remove-checkbox:checked, .apply-checkbox:checked');
            if (selected.length === 0) {
                this.showToast('Please select at least one job first.', 'warning');
                return;
            }

            // proceed only when there are selections
            const actions = ['remove', 'apply'];
            for (const action of actions) {
                const checked = document.querySelectorAll(`.${action}-checkbox:checked`);
                const urls = Array.from(checked).map(cb => cb.dataset.jobId).filter(Boolean);
                if (!urls.length) continue;

                const res = await fetch(`/${action}_jobs`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ jobURLs: urls }),
                    credentials: 'include'
                });

                if (!res.ok) throw new Error(`Failed to ${action} jobs`);
            }

            await this.refreshJobs(true);
            this.showToast('All selected jobs processed successfully!', 'success');
        } catch (err) {
            this.showToast('Error while processing selected jobs.', 'danger');
            console.error(err);
        } finally {
            this.setUIBusy(false);
        }
    }

    showLoadingToast(message = 'Loading, please wait...') {
        const toastEl = document.getElementById('job-toast');
        const body = document.getElementById('toast-message');
        if (!toastEl) return { hide: () => { } };

        // hard cancel any running transition
        toastEl.classList.remove('show');
        toastEl.offsetHeight;

        // force cleanup of any instance
        const existingInstance = bootstrap.Toast.getInstance(toastEl);
        if (existingInstance) {
            try { existingInstance.dispose(); } catch { }
        }

        // Style for loading spinner toast
        toastEl.className = 'toast align-items-center text-white bg-secondary border-0';
        body.innerHTML = `
        <div class="d-flex align-items-center gap-2">
            <div class="spinner-border spinner-border-sm text-light" role="status"></div>
            <span>${message}</span>
        </div>`;

        // Show the toast
        const toastInstance = bootstrap.Toast.getOrCreateInstance(toastEl, { autohide: false });
        toastInstance.show();

        // Return controller for hiding it later
        return {
            hide: () => {
                const instance = bootstrap.Toast.getInstance(toastEl);
                if (instance && toastEl.classList.contains('show')) instance.hide();
            }
        };
    }

    showToast(message, type = 'primary') {

        const now = Date.now();
        if (this.lastToastMessage === message && (now - this.lastToastTime) < 2000) {
            return; // skip showing the same message within 2 seconds
        }
        this.lastToastMessage = message;
        this.lastToastTime = now;

        const toastEl = document.getElementById('job-toast');
        const body = document.getElementById('toast-message');
        if (!toastEl) return { hide: () => { } };

        // hard cancel any running transition
        toastEl.classList.remove('show');
        toastEl.offsetHeight;

        // force cleanup of any instance
        const existingInstance = bootstrap.Toast.getInstance(toastEl);
        if (existingInstance) {
            try { existingInstance.dispose(); } catch { }
        }

        // Reset class and set color
        toastEl.className = `toast align-items-center text-white bg-${type} border-0`;
        body.textContent = message;

        // Display toast with short delay
        const toastInstance = bootstrap.Toast.getOrCreateInstance(toastEl, { autohide: true, delay: 4000 });
        toastInstance.show();

        return {
            hide: () => {
                const instance = bootstrap.Toast.getInstance(toastEl);
                if (instance && toastEl.classList.contains('show')) instance.hide();
            }
        };
    }
}

// Initialize App
document.addEventListener('DOMContentLoaded', () => {
    const app = new JobApp();
    app.init();
});