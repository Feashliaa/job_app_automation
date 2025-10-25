/*
Job Search Class Definition, and all functions for handling backend and front end requests
*/

class JobSearch {
    constructor(datePosted, experienceLevel, jobTitle, location) {
        this.datePosted = datePosted;
        this.experienceLevel = experienceLevel;
        this.jobTitle = jobTitle;
        this.location = location;
    }
}

class JobList {
    constructor() {
        this.jobs = [];
    }

    addJob(job) {
        this.jobs.push(job);
    }
    removeJob(index) {
        this.jobs.splice(index, 1);
    }
    getJobs() {
        return this.jobs;
    }
    findJobByTitle(title) {
        return this.jobs.filter(job => job.jobTitle.toLowerCase().includes(title.toLowerCase()));
    }
}

// Create a global JobList instance
const jobList = new JobList();
let allJobs = []; // store the latest fetched jobs globally, used in filter

let filterState = {
    title: '',
    company: '',
    location: '',
    status: '',
};

// Handle form submission
document.addEventListener("DOMContentLoaded", () => {
    const jobForm = document.getElementById("jobForm");

    const eventButton = document.getElementById("event-handler");

    jobForm.addEventListener("submit", (event) => {
        event.preventDefault();
        const datePosted = document.getElementById("date-posted").value;
        const experienceLevel = document.getElementById("experience").value;
        const jobTitle = document.getElementById("job-title").value;
        const location = document.getElementById("location").value;

        try {
            if (!datePosted || !experienceLevel || !jobTitle) {
                throw new Error("All fields are required.");
            }
        } catch (error) {
            console.log("Error in form submission:");
            console.error(error.message);
            return;
        }

        // if passes validation, create a new job parameter searching object
        const newJob = new JobSearch(datePosted, experienceLevel, jobTitle, location);

        // Add job to the list
        jobList.addJob(newJob);

        // Send the job object to the backend
        sendJobToBackend(newJob);

        jobForm.reset();
    });

    document.getElementById("queryBtn").addEventListener("click", async () => {
        console.log("Query button clicked — fetching from backend...");

        try {
            const response = await fetch("/refresh_jobs");
            const data = await response.json();
            // Store jobs globally and render with filter applied
            allJobs = data.jobs || [];
            renderJobs();
        } catch (err) {
            console.error("Error fetching jobs:", err);
        }
    });

    document.getElementById("event-handler")
    .addEventListener("click", handleAllSelected);

    document.addEventListener("change", (event) => {
        if (event.target.id === "showIgnored") {
            renderJobs();
        }
    });

    const filterToggle = document.querySelector('.filter-toggle');
    const filterControls = document.getElementById('filter-controls');

    filterToggle.addEventListener('click', () => {
        const isExpanded = filterToggle.getAttribute('aria-expanded') === 'true';
        filterControls.style.display = isExpanded ? 'none' : 'flex';
        filterToggle.setAttribute('aria-expanded', !isExpanded);
    });

    // Add event listeners for filter inputs
    const filterInputs = document.querySelectorAll('.filter-controls input, .filter-controls select');
    filterInputs.forEach(input => {
        input.addEventListener('input', () => {
            filterState[input.id.replace('filter-', '')] = input.value;
            renderJobs();
        });
    });

    // Clear filters
    document.querySelector('.clear-filters').addEventListener('click', () => {
        filterState = { title: '', company: '', location: '', status: '', dateFrom: '', dateTo: '' };
        document.querySelectorAll('.filter-controls input, .filter-controls select').forEach(input => {
            input.value = '';
        });
        renderJobs();
    });
});

// send the object to the backend, app.py
async function sendJobToBackend(job) {
    console.log("Job JSON:", job);
    try {
        const response = await fetch('/add_job_request', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(job)
        });
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        const data = await response.json();
        console.log('Response from backend:', JSON.stringify(data, null, 2));

        allJobs = data.jobs || [];

        renderJobs();
    } catch (error) {
        console.error('Error in Send to Backend:', error);
    }
}

function updateResultsTable(jobData) {
    const resultsDiv = document.getElementById("results");
    const tbody = resultsDiv.querySelector("tbody");
    tbody.innerHTML = ""; // Clear existing rows
    const jobs = jobData.jobs || [];

    const columns = [
        { key: "JobTitle", label: "Job Title" },
        { key: "Company", label: "Company" },
        { key: "Location", label: "Location" },
        {
            key: "URL", label: "Job URL", render: job => job.URL ? `
            <a href="${job.URL}" target="_blank" class="btn btn-sm btn-outline-primary" title="Open job">🔗 Link </a> ` : ""
        },
        { key: "Status", label: "Job Status", render: job => `<span class="badge bg-secondary ${job.Status?.toLowerCase() || ''}">${job.Status || ''}</span>` },
        { key: "DateFound", label: "Date Found", render: job => job.DateFound ? new Date(job.DateFound).toLocaleDateString() : "" },
        { key: "Remove", label: "Remove", render: job => `<input type="checkbox" class="form-check-input remove-checkbox" data-job-id="${job.URL || ''}">` },
        { key: "Apply", label: "Apply", render: job => `<input type="checkbox" class="form-check-input apply-checkbox" data-job-id="${job.URL || ''}">` }
    ];

    try {
        if (!jobs || jobs.length === 0) {
            throw new Error("No job data available to display.");
        }

        resultsDiv.style.display = "block";

        jobs.forEach(job => {
            const row = document.createElement("tr");
            row.innerHTML = columns
                .map(col => {
                    const value = col.render ? col.render(job) : job[col.key] || "";
                    const classes = [];
                    if (col.key === "Remove" || col.key === "Apply") classes.push("checkbox-cell");
                    if (col.key === "Remove") classes.push("remove");
                    if (col.key === "Apply") classes.push("apply");
                    return `<td class="${classes.join(" ")}" data-label="${col.label}">${value}</td>`;
                })
                .join("");
            tbody.appendChild(row);
        });
    } catch (error) {
        console.warn("Error in updating results table:", error.message);
        resultsDiv.style.display = "block";
        const row = document.createElement("tr");
        const cell = document.createElement("td");
        cell.colSpan = columns.length;
        cell.textContent = "No job applications found.";
        row.appendChild(cell);
        tbody.appendChild(row);
    }
}

// Renders the table, optionally filtering out ignored jobs
function renderJobs() {
    const filteredJobs = allJobs.filter(job => {
        const titleMatch = filterState.title
            ? job.JobTitle?.toLowerCase().includes(filterState.title.toLowerCase())
            : true;
        const companyMatch = filterState.company
            ? job.Company?.toLowerCase().includes(filterState.company.toLowerCase())
            : true;
        const locationMatch = filterState.location
            ? job.Location?.toLowerCase().includes(filterState.location.toLowerCase())
            : true;
        const statusMatch = filterState.status
            ? job.Status === filterState.status
            : true;

        return titleMatch && companyMatch && locationMatch && statusMatch;
    });
    updateResultsTable({ jobs: filteredJobs });
}

async function handleAllSelected() {
    const actions = ["remove", "apply"];
    const button = document.getElementById("event-handler");
    button.disabled = true;
    button.textContent = "Processing...";

    try {
        for (const action of actions) {
            const checkboxes = document.querySelectorAll(`.${action}-checkbox:checked`);
            const jobs = Array.from(checkboxes).map(cb => cb.dataset.jobId).filter(Boolean);
            if (jobs.length === 0) continue;

            if (action === "remove" &&
                !confirm(`Are you sure you want to remove ${jobs.length} job(s)?`)) {
                continue;
            }

            const response = await fetch(`/${action}_jobs`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ jobURLs: jobs })
            });

            if (!response.ok) throw new Error(`Failed to ${action} jobs.`);

            console.log(`Completed ${action} for ${jobs.length} jobs.`);
        }

        const refresh = await fetch("/refresh_jobs");
        updateResultsTable(await refresh.json());
        alert("All selected jobs processed successfully!");
    } catch (err) {
        console.error("Error processing jobs:", err);
        alert("Error while processing selected jobs.");
    } finally {
        button.disabled = false;
        button.textContent = "Handle Selected Jobs";
    }
}
