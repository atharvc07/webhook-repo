/**
 * GitHub Webhook Tracker UI Logic
 */

// Function to format the date/time
function formatTimestamp(isoString) {
    if (!isoString) return "N/A";

    const date = new Date(isoString);

    // Format options for consistent display
    const options = {
        day: 'numeric',
        month: 'long',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        timeZoneName: 'short'
    };

    return date.toLocaleString('en-US', options);
}

// Function to fetch and render events
async function refreshEvents() {
    try {
        const response = await fetch('/events');
        if (!response.ok) throw new Error('Failed to fetch events');

        const events = await response.json();
        renderEvents(events);
    } catch (error) {
        console.error('Error fetching events:', error);
    }
}

// Function to generate the exact message based on event type
function generateEventMessage(event) {
    const { author, from_branch, to_branch, timestamp, action } = event;
    const formattedTime = formatTimestamp(timestamp);

    switch (action) {
        case 'PUSH':
            return `<strong>${author}</strong> pushed to <code>${to_branch}</code> on ${formattedTime}`;

        case 'PULL_REQUEST':
            return `<strong>${author}</strong> submitted a pull request from <code>${from_branch}</code> to <code>${to_branch}</code> on ${formattedTime}`;

        case 'MERGE':
            return `<strong>${author}</strong> merged branch <code>${from_branch}</code> to <code>${to_branch}</code> on ${formattedTime}`;

        default:
            return `${author} performed ${action} on ${formattedTime}`;
    }
}

// Function to update the DOM
function renderEvents(events) {
    const listElement = document.getElementById('events-list');

    if (events.length === 0) {
        listElement.innerHTML = '<div class="empty-state">No events found in the database.</div>';
        return;
    }

    // Clear and re-populate
    listElement.innerHTML = '';

    events.forEach(event => {
        const li = document.createElement('li');
        li.className = `event-card event-${event.action.toLowerCase()}`;

        const message = generateEventMessage(event);

        li.innerHTML = `
            <div class="event-message">${message}</div>
            <div class="event-meta">Req ID: ${event.request_id}</div>
        `;

        listElement.appendChild(li);
    });
}

// Initial fetch
refreshEvents();

// Polling interval: Every 15 seconds
setInterval(refreshEvents, 15000);

console.log('Event Tracker: Live polling started - 15s interval');
