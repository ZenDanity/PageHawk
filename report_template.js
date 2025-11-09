// PageHawk Report Template - JavaScript
// This file will contain all the interactive functionality

// ===========================
// Global State
// ===========================

let reportData = {
    ips: []
};

let flattenedVisits = [];
let currentView = 'overview';
let selectedScreenshot = null;

// ===========================
// Data Transformation
// ===========================

function flattenVisitsData(data) {
    /**
     * Convert the new nested structure to a flat array for easier processing
     * Input: {ips: [{ip, url, ports: [{port_num: {data}}]}]}
     * Output: [{ip, url, port, response, visited_first, ...}]
     */
    const flattened = [];
    
    if (!data || !data.ips) {
        return flattened;
    }
    
    data.ips.forEach(ipEntry => {
        const ip = ipEntry.ip;
        const url = ipEntry.url;
        
        if (ipEntry.ports && Array.isArray(ipEntry.ports)) {
            ipEntry.ports.forEach(portEntry => {
                // Each portEntry is an object with one key (the port number)
                for (const [portNum, portData] of Object.entries(portEntry)) {
                    flattened.push({
                        ip: ip,
                        url: url,
                        port: portNum,
                        response: portData.response,
                        visited_first: portData.visited_first,
                        visited_last: portData.visited_last,
                        user_agent: portData.user_agent,
                        screenshot_path_full: portData.screenshot_path_full,
                        screenshot_path_relative: portData.screenshot_path_relative,
                        screenshot_pathname: portData.screenshot_pathname,
                        screenshot_filename: portData.screenshot_filename
                    });
                }
            });
        }
    });
    
    return flattened;
}

// ===========================
// Initialization
// ===========================

document.addEventListener('DOMContentLoaded', function() {
    initNavigation();
    initCollapseToggle();
    initImageModal();
    
    // Load data from embedded json_data variable
    if (typeof json_data !== 'undefined') {
        reportData = json_data;
        // Flatten the nested structure for easier processing
        flattenedVisits = flattenVisitsData(reportData);
        updateReport();
    } else {
        initPlaceholders();
        console.error('No data available');
    }
});

// ===========================
// Navigation
// ===========================

function initNavigation() {
    const navItems = document.querySelectorAll('.nav-item');
    
    navItems.forEach(item => {
        item.addEventListener('click', function() {
            const view = this.getAttribute('data-view');
            switchView(view);
        });
    });
}

function switchView(view) {
    currentView = view;
    
    // Update nav items
    document.querySelectorAll('.nav-item').forEach(item => {
        item.classList.remove('active');
        if (item.getAttribute('data-view') === view) {
            item.classList.add('active');
        }
    });
    
    // Update content sections
    document.querySelectorAll('.content-section').forEach(section => {
        section.classList.remove('active');
    });
    
    document.getElementById(`${view}-section`).classList.add('active');
}

// ===========================
// Collapse Toggle Functions
// ===========================

function initCollapseToggle() {
    const toggleBtn = document.getElementById('collapse-toggle');
    const screenshotPanel = document.querySelector('.screenshot-panel');
    
    if (toggleBtn && screenshotPanel) {
        toggleBtn.addEventListener('click', function() {
            screenshotPanel.classList.toggle('collapsed');
        });
    }
}

// ===========================
// Image Modal Functions
// ===========================

function initImageModal() {
    const modal = document.getElementById('image-modal');
    const modalBackdrop = document.getElementById('modal-backdrop');
    const modalClose = document.getElementById('modal-close');
    const modalImage = document.getElementById('modal-image');
    
    // Close modal on backdrop click
    if (modalBackdrop) {
        modalBackdrop.addEventListener('click', closeModal);
    }
    
    // Close modal on close button click
    if (modalClose) {
        modalClose.addEventListener('click', closeModal);
    }
    
    // Close modal on image click
    if (modalImage) {
        modalImage.addEventListener('click', closeModal);
    }
    
    // Close modal on escape key
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            closeModal();
        }
    });
}

function openModal(imageSrc) {
    const modal = document.getElementById('image-modal');
    const modalImage = document.getElementById('modal-image');
    
    if (modal && modalImage) {
        modalImage.src = imageSrc;
        modal.classList.add('active');
        document.body.style.overflow = 'hidden';
    }
}

function closeModal() {
    const modal = document.getElementById('image-modal');
    
    if (modal) {
        modal.classList.remove('active');
        document.body.style.overflow = '';
    }
}

// ===========================
// Overview Section Functions
// ===========================

function initPlaceholders() {
    // Placeholder content - will be replaced with actual data
    console.log('Placeholders initialized');
}

function loadScreenshots(visits) {
    const grid = document.getElementById('screenshot-grid');
    grid.innerHTML = '';
    
    // Filter visits with screenshots
    const withScreenshots = visits.filter(v => v.screenshot_filename);
    
    withScreenshots.forEach((visit, index) => {
        const thumb = document.createElement('div');
        thumb.className = 'screenshot-thumbnail';
        const screenshotPath = `${visit.screenshot_pathname}/${visit.screenshot_filename}`;
        
        // Display URL if available, otherwise IP:port
        const displayTarget = visit.url ? visit.url : `${visit.ip}:${visit.port}`;
        
        // Determine protocol based on response status and port
        const port = parseInt(visit.port);
        const response = parseInt(visit.response);
        let protocol = 'HTTP';
        let protocolClass = 'protocol-http';
        
        // Check if HTTPS was used (port 443 or response indicates HTTPS)
        if (port === 443 || visit.screenshot_filename.includes('https')) {
            protocol = 'HTTPS';
            protocolClass = 'protocol-https';
        }
        
        // Determine status indicator (green for success, red for error)
        const statusClass = (response >= 200 && response < 400) ? 'status-success' : 'status-error';
        
        thumb.innerHTML = `
            <img src="${screenshotPath}" alt="${displayTarget}">
            <div class="thumb-overlay-top-left">
                <span class="status-indicator ${statusClass}"></span>
                <span class="${protocolClass}">${protocol}</span>
            </div>
            <div class="thumb-overlay-top-right">${visit.port}</div>
            <div class="thumb-overlay-bottom">${displayTarget}</div>
        `;
        
        thumb.addEventListener('click', () => {
            const screenshotPanel = document.querySelector('.screenshot-panel');
            // If panel is collapsed, select screenshot first (updates details), then open modal
            if (screenshotPanel && screenshotPanel.classList.contains('collapsed')) {
                selectScreenshot(visit, index);
                openModal(screenshotPath);
            } else {
                selectScreenshot(visit, index);
            }
        });
        grid.appendChild(thumb);
    });
}

function selectScreenshot(visit, index) {
    selectedScreenshot = visit;
    
    // Update thumbnail highlights
    document.querySelectorAll('.screenshot-thumbnail').forEach((thumb, i) => {
        thumb.classList.toggle('active', i === index);
    });
    
    // Update viewer
    const viewer = document.getElementById('screenshot-viewer');
    const screenshotPath = `${visit.screenshot_pathname}/${visit.screenshot_filename}`;
    
    // Display URL if available, otherwise IP:port
    const displayTarget = visit.url ? visit.url : `${visit.ip}:${visit.port}`;
    viewer.innerHTML = `<img src="${screenshotPath}" alt="${displayTarget}">`;
    
    // Add click handler to the big image to open modal
    const bigImage = viewer.querySelector('img');
    if (bigImage) {
        bigImage.addEventListener('click', function() {
            openModal(screenshotPath);
        });
    }
    
    // Update details panel
    updateDetailsPanel(visit);
}

function updateDetailsPanel(visit) {
    const detailsContent = document.getElementById('details-content');
    
    const statusClass = getStatusClass(visit.response);
    
    // Build IP/URL display
    const ipDisplay = visit.ip || '-';
    const urlDisplay = visit.url || '-';
    const ipLinkUrl = visit.ip ? `http://${visit.ip}:${visit.port}` : '#';
    const urlLinkUrl = visit.url ? (visit.url.startsWith('http') ? visit.url : `http://${visit.url}`) : '#';
    
    detailsContent.innerHTML = `
        <div class="detail-row">
            <div class="detail-label">IP / URL</div>
            <div class="detail-value">
                ${visit.ip ? `<a href="${ipLinkUrl}" target="_blank" style="color: var(--accent-cyan); text-decoration: none;">${ipDisplay}</a>` : ipDisplay}
                <br>
                ${visit.url ? `<a href="${urlLinkUrl}" target="_blank" style="color: var(--accent-cyan); text-decoration: none;">${urlDisplay}</a>` : urlDisplay}
            </div>
        </div>
        <div class="detail-row detail-row-split">
            <div class="detail-split-left">
                <div class="detail-label">Port</div>
                <div class="detail-value">${visit.port}</div>
            </div>
            <div class="detail-split-right">
                <div class="detail-label">Response Code</div>
                <div class="detail-value ${statusClass}">${visit.response}</div>
            </div>
        </div>
        <div class="detail-row">
            <div class="detail-label">First Visit</div>
            <div class="detail-value">${visit.visited_first || 'N/A'}</div>
        </div>
        <div class="detail-row">
            <div class="detail-label">Last Visit</div>
            <div class="detail-value">${visit.visited_last || 'N/A'}</div>
        </div>
        <div class="detail-row">
            <div class="detail-label">User Agent</div>
            <div class="detail-value">${visit.user_agent || 'N/A'}</div>
        </div>
        <div class="detail-row">
            <div class="detail-label">Screenshot</div>
            <div class="detail-value">${visit.screenshot_filename || 'N/A'}</div>
        </div>
    `;
}

function getStatusClass(response) {
    const resp = parseInt(response);
    if (!isNaN(resp)) {
        if (resp >= 200 && resp < 300) return 'success';
        if (resp >= 400) return 'danger';
    }
    return '';
}

// ===========================
// Table Section Functions
// ===========================

function loadTable(visits) {
    const tbody = document.getElementById('table-body');
    tbody.innerHTML = '';
    
    visits.forEach(visit => {
        const row = document.createElement('tr');
        const statusClass = getStatusClass(visit.response);
        const statusBadge = `<span class="status-badge ${statusClass}">${visit.response}</span>`;
        
        // Display target (URL or IP:port)
        const targetDisplay = visit.url ? visit.url : visit.ip;
        const portDisplay = visit.url ? (visit.port || '-') : visit.port;
        
        // Screenshot indicator with color
        const screenshotIndicator = visit.screenshot_filename 
            ? '<span class="screenshot-yes">✓</span>' 
            : '<span class="screenshot-no">✗</span>';
        
        row.innerHTML = `
            <td>${targetDisplay}</td>
            <td>${portDisplay}</td>
            <td>${statusBadge}</td>
            <td>${visit.visited_first || 'N/A'}</td>
            <td>${visit.visited_last || 'N/A'}</td>
            <td>${visit.user_agent || 'N/A'}</td>
            <td>${screenshotIndicator}</td>
        `;
        
        tbody.appendChild(row);
    });
    
    initTableFeatures();
}

function initTableFeatures() {
    // Search functionality
    const searchInput = document.getElementById('table-search');
    if (searchInput) {
        searchInput.addEventListener('input', function(e) {
            filterTable(e.target.value);
        });
    }
    
    // Sortable columns
    const sortableHeaders = document.querySelectorAll('.data-table th.sortable');
    sortableHeaders.forEach(header => {
        header.addEventListener('click', function() {
            const column = this.getAttribute('data-column');
            sortTable(column);
        });
    });
    
    // Export JSON Full - export the original nested data structure
    const jsonFullBtn = document.getElementById('export-json-full');
    if (jsonFullBtn) {
        jsonFullBtn.addEventListener('click', function() {
            const content = JSON.stringify(reportData, null, 2);
            downloadFile(content, 'pagehawk-full-data.json', 'json');
        });
    }
    
    // Export JSON Current View - export only visible rows from table
    const jsonCurrentBtn = document.getElementById('export-json-current');
    if (jsonCurrentBtn) {
        jsonCurrentBtn.addEventListener('click', function() {
            const visibleData = getVisibleTableData();
            const content = JSON.stringify(visibleData, null, 2);
            downloadFile(content, 'pagehawk-current-view.json', 'json');
        });
    }
    
    // Export CSV Full - export all flattened data as CSV
    const csvFullBtn = document.getElementById('export-csv-full');
    if (csvFullBtn) {
        csvFullBtn.addEventListener('click', function() {
            const content = generateCSVFromData(flattenedVisits);
            downloadFile(content, 'pagehawk-full-data.csv', 'csv');
        });
    }
    
    // Export CSV Current View - export only visible rows as CSV
    const csvCurrentBtn = document.getElementById('export-csv-current');
    if (csvCurrentBtn) {
        csvCurrentBtn.addEventListener('click', function() {
            const visibleData = getVisibleTableData();
            const content = generateCSVFromData(visibleData);
            downloadFile(content, 'pagehawk-current-view.csv', 'csv');
        });
    }
}

function getVisibleTableData() {
    // Get all visible rows from the table
    const visibleRows = [];
    const rows = document.querySelectorAll('#table-body tr');
    
    rows.forEach((row, index) => {
        // Check if row is visible (not filtered out)
        if (row.style.display !== 'none') {
            // Get the corresponding data from flattenedVisits
            visibleRows.push(flattenedVisits[index]);
        }
    });
    
    return visibleRows;
}

function generateCSVFromData(data) {
    // Create CSV header
    const headers = ['Target', 'Port', 'Response', 'First Visit', 'Last Visit', 'User Agent', 'Screenshot'];
    let csv = headers.join(',') + '\n';
    
    // Add data rows
    data.forEach(visit => {
        const target = visit.url || visit.ip;
        const port = visit.port || '-';
        const response = visit.response || '-';
        const firstVisit = visit.visited_first || 'N/A';
        const lastVisit = visit.visited_last || 'N/A';
        const userAgent = visit.user_agent || 'N/A';
        const screenshot = visit.screenshot_filename || 'N/A';
        
        // Escape fields that might contain commas or quotes
        const escapeCSV = (field) => {
            const str = String(field);
            if (str.includes(',') || str.includes('"') || str.includes('\n')) {
                return `"${str.replace(/"/g, '""')}"`;
            }
            return str;
        };
        
        const row = [
            escapeCSV(target),
            escapeCSV(port),
            escapeCSV(response),
            escapeCSV(firstVisit),
            escapeCSV(lastVisit),
            escapeCSV(userAgent),
            escapeCSV(screenshot)
        ].join(',');
        
        csv += row + '\n';
    });
    
    return csv;
}

function filterTable(searchTerm) {
    const rows = document.querySelectorAll('#table-body tr');
    const term = searchTerm.toLowerCase();
    
    rows.forEach(row => {
        const text = row.textContent.toLowerCase();
        row.style.display = text.includes(term) ? '' : 'none';
    });
}

function sortTable(column) {
    // Table sorting logic will be implemented here
    console.log('Sort by:', column);
}

// ===========================
// Outputs Section Functions
// ===========================

function generateOutputs(visits) {
    // Helper function to get unique targets (IP or URL)
    const getTarget = (visit) => visit.url || visit.ip;
    
    // 1. All Targets (without ports) - unique targets only
    const allTargetsNoPorts = [...new Set(visits.map(v => getTarget(v)))].join('\n');
    document.getElementById('output-all-targets-no-ports').value = allTargetsNoPorts;
    
    // 2. All Targets (with ports) - target:port format
    const allTargetsWithPorts = visits.map(v => `${getTarget(v)}:${v.port}`).join('\n');
    document.getElementById('output-all-targets-with-ports').value = allTargetsWithPorts;
    
    // 3. All Targets With Screenshots (without ports) - unique targets only
    const screenshotsNoPorts = [...new Set(
        visits.filter(v => v.screenshot_filename).map(v => getTarget(v))
    )].join('\n');
    document.getElementById('output-screenshots-no-ports').value = screenshotsNoPorts;
    
    // 4. All Targets With Screenshots (with ports) - target:port format
    const screenshotsWithPorts = visits
        .filter(v => v.screenshot_filename)
        .map(v => `${getTarget(v)}:${v.port}`)
        .join('\n');
    document.getElementById('output-screenshots-with-ports').value = screenshotsWithPorts;
    
    // 5. Unreachable Targets - just targets (unique)
    const unreachable = [...new Set(
        visits
            .filter(v => {
                const resp = parseInt(v.response);
                return isNaN(resp) || resp >= 400;
            })
            .map(v => getTarget(v))
    )].join('\n');
    document.getElementById('output-unreachable').value = unreachable;
    
    initOutputButtons();
}

function initOutputButtons() {
    // Copy buttons
    document.querySelectorAll('.copy-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const outputId = this.getAttribute('data-output');
            const textarea = document.getElementById(`output-${outputId}`);
            
            // Modern clipboard API
            navigator.clipboard.writeText(textarea.value).then(() => {
                // Visual feedback
                const originalText = this.textContent;
                this.textContent = '✓ Copied!';
                setTimeout(() => {
                    this.textContent = originalText;
                }, 2000);
            }).catch(err => {
                // Fallback to old method
                textarea.select();
                document.execCommand('copy');
                const originalText = this.textContent;
                this.textContent = '✓ Copied!';
                setTimeout(() => {
                    this.textContent = originalText;
                }, 2000);
            });
        });
    });
    
    // Format buttons (JSON, CSV, TXT)
    document.querySelectorAll('.format-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const format = this.getAttribute('data-format');
            const outputId = this.getAttribute('data-output');
            const textarea = document.getElementById(`output-${outputId}`);
            const currentContent = textarea.value;
            
            // Check if output has ports or not based on outputId
            const hasPort = outputId.includes('with-ports');
            
            let convertedContent = '';
            
            if (format === 'json') {
                // Convert to JSON array format
                const lines = currentContent.split('\n').filter(line => line.trim());
                convertedContent = JSON.stringify(lines, null, 2);
            } else if (format === 'csv') {
                // Convert to CSV format
                const lines = currentContent.split('\n').filter(line => line.trim());
                if (hasPort) {
                    // With ports: url;port format
                    convertedContent = 'url;port\n';
                    lines.forEach(line => {
                        const lastColonIndex = line.lastIndexOf(':');
                        if (lastColonIndex !== -1) {
                            const url = line.substring(0, lastColonIndex);
                            const port = line.substring(lastColonIndex + 1);
                            convertedContent += `${url};${port}\n`;
                        } else {
                            convertedContent += `${line};\n`;
                        }
                    });
                } else {
                    // Without ports: just url column
                    convertedContent = 'url\n';
                    lines.forEach(line => {
                        convertedContent += `${line}\n`;
                    });
                }
            } else if (format === 'txt') {
                // TXT is just the current content
                convertedContent = currentContent;
            }
            
            // Download the file
            const filename = `pagehawk-${outputId}.${format}`;
            downloadFile(convertedContent, filename, format);
        });
    });
}

function downloadFile(content, filename, format) {
    const mimeTypes = {
        'json': 'application/json',
        'txt': 'text/plain',
        'csv': 'text/csv'
    };
    
    const blob = new Blob([content], { type: mimeTypes[format] || 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}

// ===========================
// Data Loading
// ===========================

function loadReportData() {
    // This will be replaced with actual data loading
    // For now, using placeholder data
    
    // Simulate loading data
    fetch('pagehawk_results.json')
        .then(response => response.json())
        .then(data => {
            reportData = data;
            updateReport();
        })
        .catch(error => {
            console.error('Error loading report data:', error);
        });
}

function updateReport() {
    // Update stats
    updateStats(flattenedVisits);
    
    // Load screenshots in overview
    loadScreenshots(flattenedVisits);
    
    // Load table
    loadTable(flattenedVisits);
    
    // Generate outputs
    generateOutputs(flattenedVisits);
}

function updateStats(visits) {
    const total = visits.length;
    const accessible = visits.filter(v => {
        const resp = parseInt(v.response);
        return !isNaN(resp) && resp >= 200 && resp < 400;
    }).length;
    const unreachable = total - accessible;
    
    document.getElementById('total-scanned').textContent = total;
    document.getElementById('accessible').textContent = accessible;
    document.getElementById('unreachable').textContent = unreachable;
}

// ===========================
// Utility Functions
// ===========================

function formatTimestamp(timestamp) {
    if (!timestamp) return 'N/A';
    return timestamp;
}

// Export functions for external use
window.PageHawk = {
    loadReportData,
    updateReport,
    switchView,
    selectScreenshot
};
