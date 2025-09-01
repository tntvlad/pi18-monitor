// Setup page JavaScript

document.addEventListener('DOMContentLoaded', function() {
    const testButton = document.getElementById('test-connection');
    const testResult = document.getElementById('test-result');
    const serialPortsContainer = document.getElementById('serial-ports');
    const portInput = document.getElementById('port');
    
    // Simple spinner HTML
    const spinnerHtml = '<img src="/static/img/simple-spinner.svg" alt="Loading..." class="simple-spinner">';
    
    // Test connection to the inverter
    testButton.addEventListener('click', function() {
        // Show loading state on the button only
        const originalButtonText = testButton.textContent;
        testButton.disabled = true;
        testButton.innerHTML = spinnerHtml + ' Testing...';
        
        // Clear previous test results
        testResult.innerHTML = '';
        
        // Get current port value from input
        const port = portInput.value;
        
        // Send test request to API
        fetch('/api/v1/inverter/test-connection', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ port: port })
        })
        .then(response => response.json())
        .then(data => {
            // Restore button
            testButton.disabled = false;
            testButton.innerHTML = originalButtonText;
            
            // Show result
            if (data.success) {
                testResult.className = 'test-result success';
                testResult.innerHTML = `
                    <p><strong>Connection successful!</strong></p>
                    <p>Protocol ID: ${data.protocol_id || 'N/A'}</p>
                    <p>Firmware Version: ${data.firmware_version || 'N/A'}</p>
                `;
            } else {
                testResult.className = 'test-result error';
                testResult.innerHTML = `
                    <p><strong>Connection failed</strong></p>
                    <p>Error: ${data.error || 'Unknown error'}</p>
                    <p>Please check your port settings and ensure the inverter is powered on.</p>
                `;
            }
        })
        .catch(error => {
            // Restore button
            testButton.disabled = false;
            testButton.innerHTML = originalButtonText;
            
            // Show error
            testResult.className = 'test-result error';
            testResult.innerHTML = `
                <p><strong>Connection test error</strong></p>
                <p>Error: ${error.message}</p>
                <p>Please check your network connection and try again.</p>
            `;
        });
    });
    
    // Fetch available serial ports
    function fetchAvailablePorts() {
        // Show loading state
        serialPortsContainer.innerHTML = spinnerHtml + ' Scanning for available ports...';
        
        fetch('/api/v1/system/ports')
            .then(response => response.json())
            .then(data => {
                if (data.ports && data.ports.length > 0) {
                    let portsHTML = '<ul class="port-list">';
                    data.ports.forEach(port => {
                        const isSelected = portInput.value === port.device;
                        portsHTML += `
                            <li class="port-item ${isSelected ? 'selected' : ''}" data-port="${port.device}">
                                <strong>${port.device}</strong>
                                ${port.description ? `<br><small>${port.description}</small>` : ''}
                            </li>
                        `;
                    });
                    portsHTML += '</ul>';
                    serialPortsContainer.innerHTML = portsHTML;
                    
                    // Add click event to port items
                    document.querySelectorAll('.port-item').forEach(item => {
                        item.addEventListener('click', function() {
                            const port = this.getAttribute('data-port');
                            portInput.value = port;
                            
                            // Update selected state
                            document.querySelectorAll('.port-item').forEach(p => {
                                p.classList.remove('selected');
                            });
                            this.classList.add('selected');
                        });
                    });
                } else {
                    serialPortsContainer.innerHTML = '<p>No serial ports detected. Please connect your device and refresh the page.</p>';
                }
            })
            .catch(error => {
                serialPortsContainer.innerHTML = `<p class="error">Error scanning ports: ${error.message}</p>`;
            });
    }
    
    // Initial port scan
    fetchAvailablePorts();
    
    // Add refresh button for ports
    const refreshButton = document.createElement('button');
    refreshButton.className = 'btn secondary';
    refreshButton.textContent = 'Refresh Ports';
    refreshButton.style.marginTop = '1rem';
    refreshButton.addEventListener('click', function() {
        const originalButtonText = refreshButton.textContent;
        refreshButton.disabled = true;
        refreshButton.innerHTML = spinnerHtml + ' Refreshing...';
        
        fetchAvailablePorts();
        
        // Re-enable after a short delay
        setTimeout(function() {
            refreshButton.disabled = false;
            refreshButton.innerHTML = originalButtonText;
        }, 1000);
    });
    serialPortsContainer.parentNode.appendChild(refreshButton);
});