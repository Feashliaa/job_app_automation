/**
 * Job Search Dashboard
 **/

class JobApp {
    constructor() {
        this.allJobs = [];
        this.sortState = { key: null, direction: 'asc' };
        this.filterState = { title: '', company: '', location: '', status: '' };
        this.choices = null;
        this.debounceTimer = null;

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
        this.refreshJobs(); // Initial load
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

        document.getElementById('queryBtn').addEventListener('click', () => this.refreshJobs());

        document.getElementById('event-handler').addEventListener('click', () => this.handleBatch());
        document.getElementById('process-fab').addEventListener('click', () => this.handleBatch());

        // Filter toggle
        document.querySelector('.filter-toggle').addEventListener('click', () => {
            const toggle = document.querySelector('.filter-toggle');
            const controls = document.getElementById('filter-controls');
            const expanded = toggle.getAttribute('aria-expanded') === 'true';
            controls.style.display = expanded ? 'none' : 'flex';
            toggle.setAttribute('aria-expanded', !expanded);
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

        // Sorting
        document.querySelectorAll('.job-table thead th').forEach(th => {
            th.addEventListener('click', () => this.handleSort(th));
        });

        // Handle Resume Parsing
        document.getElementById("resumeForm").addEventListener("submit", async (e) => {
            e.preventDefault(); // stops redirect
            const fileInput = document.getElementById("resumeFile");
            const formData = new FormData();
            formData.append("resumeFile", fileInput.files[0]);

            const res = await fetch("/resume_parse", { method: "POST", body: formData });
            const data = await res.json();
            console.log("Parsed resume:", data);
        });

    }

    async handleSubmit(e) {
        e.preventDefault();

        const datePosted = document.getElementById('date-posted').value?.trim();
        const experienceLevel = document.getElementById('experience').value?.trim();
        const jobTitle = this.choices.getValue(true);
        const location = document.getElementById('location').value?.trim();

        if (!datePosted || !experienceLevel || !jobTitle) {
            this.showToast('All fields are required.', 'danger');
            return;
        }

        const payload = { datePosted, experienceLevel, jobTitle, location };

        try {
            const res = await fetch('/add_job_request', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            if (!res.ok) throw new Error('Submission failed');

            const data = await res.json();
            this.allJobs = data.jobs || [];
            document.getElementById('jobForm').reset();
            this.choices.clearInput();
            this.showToast('Job search submitted successfully.', 'success');
            this.render();
        } catch (err) {
            this.showToast('Failed to submit job search.', 'danger');
            console.error(err);
        }
    }

    async refreshJobs() {
        const btn = document.getElementById('queryBtn');
        btn.disabled = true;
        try {
            const res = await fetch('/refresh_jobs');
            const data = await res.json();
            this.allJobs = data.jobs || [];
            this.render();
        } catch (err) {
            this.showToast('Failed to load jobs.', 'danger');
            console.error(err);
        } finally {
            btn.disabled = false;
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

    getFilteredAndSortedJobs() {
        let jobs = [...this.allJobs];

        // Filter
        jobs = jobs.filter(job => {
            return (!this.filterState.title || (job.JobTitle?.toLowerCase().includes(this.filterState.title.toLowerCase()))) &&
                (!this.filterState.company || (job.Company?.toLowerCase().includes(this.filterState.company.toLowerCase()))) &&
                (!this.filterState.location || (job.Location?.toLowerCase().includes(this.filterState.location.toLowerCase()))) &&
                (!this.filterState.status || job.Status === this.filterState.status);
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
        const actions = ['remove', 'apply'];
        const btn = document.getElementById('event-handler');
        btn.disabled = true;
        btn.textContent = 'Processing...';

        try {
            for (const action of actions) {
                const checked = document.querySelectorAll(`.${action}-checkbox:checked`);
                const urls = Array.from(checked).map(cb => cb.dataset.jobId).filter(Boolean);
                if (!urls.length) continue;

                const res = await fetch(`/${action}_jobs`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ jobURLs: urls })
                });

                if (!res.ok) throw new Error(`Failed to ${action} jobs`);
            }

            await this.refreshJobs();
            this.showToast('All selected jobs processed successfully!', 'success');
        } catch (err) {
            this.showToast('Error while processing selected jobs.', 'danger');
            console.error(err);
        } finally {
            btn.disabled = false;
            btn.textContent = 'Handle Selected Jobs';
        }
    }

    showToast(message, type = 'primary') {
        const toast = document.getElementById('job-toast');
        const body = document.getElementById('toast-message');
        toast.className = `toast align-items-center text-white bg-${type} border-0`;
        body.textContent = message;
        new bootstrap.Toast(toast).show();
    }
}

// Initialize App
document.addEventListener('DOMContentLoaded', () => {
    const app = new JobApp();
    app.init();
});