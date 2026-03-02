/**
 * GitHub Webhook Tracker Dashboard
 * Requirement #7: UI Robustness
 */

const loader = document.getElementById('loader');
const lastUpdatedText = document.getElementById('last-updated');
const eventsList = document.getElementById('events-list');

// Internal State
let isInitialLoad = true;

/**
 * Update the "Last Updated" text with current time
 */
function updateLastUpdated() {
    const now = new Date();
    lastUpdatedText.innerText = `Last updated: ${now.toLocaleTimeString()}`;
}

/**
 * Generate formatting for event messages based on exact requirement #5
 */
function generateEventHTML(event) {
    const { author, from_branch, to_branch, timestamp, action, request_id } = event;

    let message = "";
    switch (action) {
        case 'PUSH':
            message = `<strong>${author}</strong> pushed to <code>${to_branch}</code> on ${timestamp}`;
            break;
        case 'PULL_REQUEST':
            message = `<strong>${author}</strong> submitted a pull request from <code>${from_branch}</code> to <code>${to_branch}</code> on ${timestamp}`;
            break;
        case 'MERGE':
            message = `<strong>${author}</strong> merged branch <code>${from_branch}</code> to <code>${to_branch}</code> on ${timestamp}`;
            break;
        default:
            message = `<strong>${author}</strong> performed ${action} on ${timestamp}`;
    }

    return `
        <li class="event-card event-${action.toLowerCase()}">
            <div class="event-message">${message}</div>
            <div class="event-footer">
                <span>Request ID: ${request_id.$numberLong || request_id}</span>
            </div>
        </li>
    `;
}

/**
 * Fetch events from backend and update UI
 */
async function fetchEvents() {
    // Show loader
    loader.style.display = 'block';

    try {
        const response = await fetch('/events');

        const data = await response.json();

        // Handle database offline state (Requirement #8)
        if (data.error === "database_offline") {
            eventsList.innerHTML = `
                <div class="empty-state" style="color: #fca5a5;">
                    <div style="font-size: 1.5rem; margin-bottom: 0.5rem;">⚠️ Database Offline</div>
                    ${data.message}<br>
                    <small>Check your MONGO_URI and IP Whitelist.</small>
                </div>`;
            return;
        }

        // If data is an array (success) or has 'events' property
        const events = Array.isArray(data) ? data : (data.events || []);

        if (events.length === 0) {
            eventsList.innerHTML = '<div class="empty-state">Waiting for GitHub events... (Ready for push/pull requests)</div>';
        } else {
            eventsList.innerHTML = events.map(generateEventHTML).join('');
        }

        updateLastUpdated();
    } catch (error) {
        console.error('Polling Error:', error);
        if (isInitialLoad) {
            eventsList.innerHTML = `<div class="empty-state" style="color: var(--error-color)">Failed to connect to backend. Check console for details.</div>`;
        }
    } finally {
        // Hide loader after a short delay for smoother visual
        setTimeout(() => {
            loader.style.display = 'none';
        }, 500);
        isInitialLoad = false;
    }
}

// Start Polling (Requirement #7: Every 15 seconds)
fetchEvents();
setInterval(fetchEvents, 15000);

console.log("GitHub Webhook Tracker: Live Polling Started.");
