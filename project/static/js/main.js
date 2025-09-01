// Main JavaScript for P18 Inverter Monitor

document.addEventListener('DOMContentLoaded', function() {
    // Elements to update
    const connectionStatus = document.getElementById('connection-status');
    const statusDisplay = document.getElementById('status-display');
    const powerDisplay = document.getElementById('power-display');
    const batteryDisplay = document.getElementById('battery-display');
    const energyDisplay = document.getElementById('energy-display');
    const errorsDisplay = document.getElementById('errors-display');
    
    // API base URL - adjust if needed
    const API_BASE = '/api/v1/inverter';
    
    // Show loading indicator
    function showLoading(element) {
        element.innerHTML = '<div class="loading"></div> Loading data...';
    }
    
    // Show error message
    function showError(element, message) {
        element.innerHTML = `<p class="error">Error: ${message}</p>`;
    }
    
    // Fetch inverter status
    function fetchStatus() {
        showLoading(statusDisplay);
        
        fetch(`${API_BASE}/data/status`)
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error! Status: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                // Update connection status
                connectionStatus.innerHTML = `<span class="status-online">● Connected</span>`;
                
                // Format and display status data
                let statusHTML = `
                    <div class="data-grid">
                        <div class="data-item">
                            <strong>Grid Voltage</strong>
                            ${data.grid.voltage} V
                        </div>
                        <div class="data-item">
                            <strong>Grid Frequency</strong>
                            ${data.grid.frequency} Hz
                        </div>
                        <div class="data-item">
                            <strong>Output Voltage</strong>
                            ${data.output.voltage} V
                        </div>
                        <div class="data-item">
                            <strong>Output Frequency</strong>
                            ${data.output.frequency} Hz
                        </div>
                        <div class="data-item">
                            <strong>Load</strong>
                            ${data.output.load_percent}%
                        </div>
                        <div class="data-item">
                            <strong>Working Mode</strong>
                            <span id="mode-indicator">${data.status.dc_ac_direction}</span>
                        </div>
                    </div>
                `;
                statusDisplay.innerHTML = statusHTML;
            })
            .catch(error => {
                connectionStatus.innerHTML = `<span class="status-offline">● Disconnected</span>`;
                showError(statusDisplay, error.message);
            });
    }
    
    // Fetch power generation data
    function fetchPowerData() {
        showLoading(powerDisplay);
        
        fetch(`${API_BASE}/data/status`)
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error! Status: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                let powerHTML = `
                    <div class="data-grid">
                        <div class="data-item">
                            <strong>PV1 Power</strong>
                            ${data.pv.pv1_power} W
                        </div>
                        <div class="data-item">
                            <strong>PV2 Power</strong>
                            ${data.pv.pv2_power} W
                        </div>
                        <div class="data-item">
                            <strong>PV1 Voltage</strong>
                            ${data.pv.pv1_voltage} V
                        </div>
                        <div class="data-item">
                            <strong>PV2 Voltage</strong>
                            ${data.pv.pv2_voltage} V
                        </div>
                        <div class="data-item">
                            <strong>MPPT1 Status</strong>
                            ${data.status.mppt1_status}
                        </div>
                        <div class="data-item">
                            <strong>MPPT2 Status</strong>
                            ${data.status.mppt2_status}
                        </div>
                    </div>
                `;
                powerDisplay.innerHTML = powerHTML;
            })
            .catch(error => {
                showError(powerDisplay, error.message);
            });
    }
    
    // Fetch battery status
    function fetchBatteryStatus() {
        showLoading(batteryDisplay);
        
        fetch(`${API_BASE}/data/status`)
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error! Status: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                let batteryHTML = `
                    <div class="data-grid">
                        <div class="data-item">
                            <strong>Voltage</strong>
                            ${data.battery.voltage} V
                        </div>
                        <div class="data-item">
                            <strong>Charging Current</strong>
                            ${data.battery.charging_current} A
                        </div>
                        <div class="data-item">
                            <strong>Discharging Current</strong>
                            ${data.battery.discharge_current} A
                        </div>
                        <div class="data-item">
                            <strong>Capacity</strong>
                            ${data.battery.capacity_percent}%
                        </div>
                        <div class="data-item">
                            <strong>Direction</strong>
                            ${data.status.battery_direction}
                        </div>
                        <div class="data-item">
                            <strong>SCC1 Voltage</strong>
                            ${data.battery.voltage_scc1} V
                        </div>
                    </div>
                `;
                batteryDisplay.innerHTML = batteryHTML;
            })
            .catch(error => {
                showError(batteryDisplay, error.message);
            });
    }
    
    // Fetch energy statistics
    function fetchEnergyStats() {
        showLoading(energyDisplay);
        
        // Get current date in YYYY-MM-DD format
        const today = new Date();
        const year = today.getFullYear();
        const month = String(today.getMonth() + 1).padStart(2, '0');
        const day = String(today.getDate()).padStart(2, '0');
        const dateString = `${year}-${month}-${day}`;
        
        // First get total energy
        fetch(`${API_BASE}/energy/total`)
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error! Status: ${response.status}`);
                }
                return response.json();
            })
            .then(totalData => {
                // Then get daily energy
                return fetch(`${API_BASE}/energy/daily/${dateString}`)
                    .then(response => {
                        if (!response.ok) {
                            throw new Error(`HTTP error! Status: ${response.status}`);
                        }
                        return response.json();
                    })
                    .then(dailyData => {
                        return { total: totalData, daily: dailyData };
                    });
            })
            .then(data => {
                let energyHTML = `
                    <div class="data-grid">
                        <div class="data-item">
                            <strong>Total Energy</strong>
                            ${data.total.total_energy_kwh} kWh
                        </div>
                        <div class="data-item">
                            <strong>Today's Energy</strong>
                            ${data.daily.energy_wh / 1000} kWh
                        </div>
                        <div class="data-item">
                            <strong>Date</strong>
                            ${data.daily.date}
                        </div>
                    </div>
                `;
                energyDisplay.innerHTML = energyHTML;
            })
            .catch(error => {
                showError(energyDisplay, error.message);
            });
    }
    
    // Fetch error logs
    function fetchErrorLogs() {
        showLoading(errorsDisplay);
        
        // Use the fault status endpoint
        fetch(`${API_BASE}/data/faults`)
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error! Status: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                if (data.fault_code === 0) {
                    errorsDisplay.innerHTML = '<p>No faults detected.</p>';
                    return;
                }
                
                let errorsHTML = `<p><strong>Fault Code:</strong> ${data.fault_code}</p>`;
                errorsHTML += '<div class="error-list">';
                
                // Check each fault flag
                for (const [key, value] of Object.entries(data.faults)) {
                    if (value) {
                        errorsHTML += `
                            <div class="error-entry error">
                                <p><strong>${key.replace(/_/g, ' ')}</strong></p>
                            </div>
                        `;
                    }
                }
                
                errorsHTML += '</div>';
                errorsDisplay.innerHTML = errorsHTML;
            })
            .catch(error => {
                showError(errorsDisplay, error.message);
            });
    }
    
    // Helper function to format datetime
    function formatDateTime(isoString) {
        if (!isoString) return 'Unknown';
        
        try {
            const date = new Date(isoString);
            return date.toLocaleString();
        } catch (e) {
            return isoString;
        }
    }
    
    // Initial data fetch
    fetchStatus();
    fetchPowerData();
    fetchBatteryStatus();
    fetchEnergyStats();
    fetchErrorLogs();
    
    // Set up periodic refresh
    setInterval(fetchStatus, 30000); // Every 30 seconds
    setInterval(fetchPowerData, 10000); // Every 10 seconds
    setInterval(fetchBatteryStatus, 15000); // Every 15 seconds
    setInterval(fetchEnergyStats, 60000); // Every minute
    setInterval(fetchErrorLogs, 60000); // Every minute
});