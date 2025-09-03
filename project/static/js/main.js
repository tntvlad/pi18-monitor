// Main JavaScript for P18 Inverter Monitor

document.addEventListener('DOMContentLoaded', function() {
    // Elements to update
    const connectionStatus = document.getElementById('connection-status');
    const systemInfoDisplay = document.getElementById('system-info-display');
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
    
    // Improved system information fetching
    function fetchSystemInfo() {
        // Get references to the specific elements we need to update
        const machineModelElement = document.querySelector('#system-information .data-item:nth-child(1) .value');
        const modelCodeElement = document.querySelector('#system-information .data-item:nth-child(2) .value');
        const serialNumberElement = document.querySelector('#system-information .data-item:nth-child(3) .value');
        const mainCpuVersionElement = document.querySelector('#system-information .data-item:nth-child(4) .value');
        
        // Fetch model info
        fetch(`${API_BASE}/info/model`)
            .then(response => response.json())
            .then(data => {
                if (data && data.model_name) {
                    machineModelElement.textContent = data.model_name;
                    modelCodeElement.textContent = data.model_code || 'Unknown';
                    
                    // Update connection status with model info
                    connectionStatus.innerHTML = `<span class="status-online">● Connected</span> | ${data.model_name}`;
                }
            })
            .catch(error => {
                console.error("Error fetching model info:", error);
                // Don't update the UI with an error, keep existing value
            });
        
        // Fetch serial number independently
        fetch(`${API_BASE}/info/serial`)
            .then(response => response.json())
            .then(data => {
                if (data && data.serial_number) {
                    serialNumberElement.textContent = data.serial_number;
                }
            })
            .catch(error => {
                console.error("Error fetching serial number:", error);
                // Don't update the UI with an error, keep existing value
            });
        
        // Fetch firmware version independently
        fetch(`${API_BASE}/info/firmware`)
            .then(response => response.json())
            .then(data => {
                if (data && data.main_cpu_version) {
                    mainCpuVersionElement.textContent = data.main_cpu_version || '0000';
                    
                    // Update other firmware version elements if they exist
                    const slave1Element = document.querySelector('#system-information .data-item:nth-child(5) .value');
                    const slave2Element = document.querySelector('#system-information .data-item:nth-child(6) .value');
                    
                    if (slave1Element && data.slave1_cpu_version) {
                        slave1Element.textContent = data.slave1_cpu_version;
                    }
                    
                    if (slave2Element && data.slave2_cpu_version) {
                        slave2Element.textContent = data.slave2_cpu_version;
                    }
                }
            })
            .catch(error => {
                console.error("Error fetching firmware version:", error);
                // Don't update the UI with an error, keep existing value
            });
    }
    
    // Fetch inverter status
    function fetchStatus() {
        // Get references to the specific elements we need to update
        const gridVoltageElement = document.querySelector('#inverter-status .data-item:nth-child(1) .value');
        const gridFrequencyElement = document.querySelector('#inverter-status .data-item:nth-child(2) .value');
        const outputVoltageElement = document.querySelector('#inverter-status .data-item:nth-child(3) .value');
        const outputFrequencyElement = document.querySelector('#inverter-status .data-item:nth-child(4) .value');
        
        fetch(`${API_BASE}/data/status`)
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error! Status: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                // Update connection status if not already updated by system info
                if (!connectionStatus.innerHTML.includes('Connected')) {
                    connectionStatus.innerHTML = `<span class="status-online">● Connected</span>`;
                }
                
                // Update grid voltage and frequency
                if (gridVoltageElement && data.grid) {
                    gridVoltageElement.textContent = `${data.grid.voltage || 0} V`;
                }
                
                if (gridFrequencyElement && data.grid) {
                    gridFrequencyElement.textContent = `${data.grid.frequency || 0} Hz`;
                }
                
                // Update output voltage and frequency
                if (outputVoltageElement && data.output) {
                    outputVoltageElement.textContent = `${data.output.voltage || 0} V`;
                }
                
                if (outputFrequencyElement && data.output) {
                    outputFrequencyElement.textContent = `${data.output.frequency || 0} Hz`;
                }
            })
            .catch(error => {
                console.error("Error fetching status:", error);
                // Don't update the UI with an error, keep existing values
            });
    }
    
    // Fetch power generation data
    function fetchPowerData() {
        // Get references to the specific elements we need to update
        const pv1PowerElement = document.querySelector('#power-generation .data-item:nth-child(1) .value');
        const pv2PowerElement = document.querySelector('#power-generation .data-item:nth-child(2) .value');
        const pv1VoltageElement = document.querySelector('#power-generation .data-item:nth-child(3) .value');
        const pv2VoltageElement = document.querySelector('#power-generation .data-item:nth-child(4) .value');
        
        fetch(`${API_BASE}/data/status`)
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error! Status: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                if (pv1PowerElement && data.pv) {
                    pv1PowerElement.textContent = `${data.pv.pv1_power || 0} W`;
                }
                
                if (pv2PowerElement && data.pv) {
                    pv2PowerElement.textContent = `${data.pv.pv2_power || 0} W`;
                }
                
                if (pv1VoltageElement && data.pv) {
                    pv1VoltageElement.textContent = `${data.pv.pv1_voltage || 0} V`;
                }
                
                if (pv2VoltageElement && data.pv) {
                    pv2VoltageElement.textContent = `${data.pv.pv2_voltage || 0} V`;
                }
            })
            .catch(error => {
                console.error("Error fetching power data:", error);
                // Don't update the UI with an error, keep existing values
            });
    }
    
    // Fetch battery status
    function fetchBatteryStatus() {
        // Get references to the specific elements we need to update
        const batteryVoltageElement = document.querySelector('#battery-status .data-item:nth-child(1) .value');
        const batteryCapacityElement = document.querySelector('#battery-status .data-item:nth-child(2) .value');
        const chargingCurrentElement = document.querySelector('#battery-status .data-item:nth-child(3) .value');
        const dischargingCurrentElement = document.querySelector('#battery-status .data-item:nth-child(4) .value');
        
        fetch(`${API_BASE}/data/status`)
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error! Status: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                if (batteryVoltageElement && data.battery) {
                    batteryVoltageElement.textContent = `${data.battery.voltage || 0} V`;
                }
                
                if (batteryCapacityElement && data.battery) {
                    batteryCapacityElement.textContent = `${data.battery.capacity_percent || 0}%`;
                }
                
                if (chargingCurrentElement && data.battery) {
                    chargingCurrentElement.textContent = `${data.battery.charging_current || 0} A`;
                }
                
                if (dischargingCurrentElement && data.battery) {
                    dischargingCurrentElement.textContent = `${data.battery.discharge_current || 0} A`;
                }
            })
            .catch(error => {
                console.error("Error fetching battery status:", error);
                // Don't update the UI with an error, keep existing values
            });
    }
    
    // Fetch energy statistics
    function fetchEnergyStats() {
        // Get references to the specific elements we need to update
        const totalEnergyElement = document.querySelector('#energy-statistics .data-item:nth-child(1) .value');
        const todaysEnergyElement = document.querySelector('#energy-statistics .data-item:nth-child(2) .value');
        const monthlyEnergyElement = document.querySelector('#energy-statistics .data-item:nth-child(3) .value');
        const yearlyEnergyElement = document.querySelector('#energy-statistics .data-item:nth-child(4) .value');
        
        // Get current date in YYYY-MM-DD format
        const today = new Date();
        const year = today.getFullYear();
        const month = String(today.getMonth() + 1).padStart(2, '0');
        const day = String(today.getDate()).padStart(2, '0');
        const dateString = `${year}-${month}-${day}`;
        
        // First get total energy
        fetch(`${API_BASE}/energy/total`)
            .then(response => response.json())
            .then(data => {
                if (totalEnergyElement && data.total_energy_kwh !== undefined) {
                    totalEnergyElement.textContent = `${data.total_energy_kwh} kWh`;
                }
            })
            .catch(error => {
                console.error("Error fetching total energy:", error);
                // Don't update the UI with an error, keep existing value
            });
            
        // Get daily energy
        fetch(`${API_BASE}/energy/daily/${dateString}`)
            .then(response => response.json())
            .then(data => {
                if (todaysEnergyElement && data.energy_wh !== undefined) {
                    todaysEnergyElement.textContent = `${(data.energy_wh / 1000).toFixed(3)} kWh`;
                }
            })
            .catch(error => {
                console.error("Error fetching daily energy:", error);
                // Don't update the UI with an error, keep existing value
            });
            
        // Get monthly energy
        fetch(`${API_BASE}/energy/monthly/${year}/${month}`)
            .then(response => response.json())
            .then(data => {
                if (monthlyEnergyElement && data.energy_wh !== undefined) {
                    monthlyEnergyElement.textContent = `${(data.energy_wh / 1000).toFixed(3)} kWh`;
                }
            })
            .catch(error => {
                console.error("Error fetching monthly energy:", error);
                // Don't update the UI with an error, keep existing value
            });
            
        // Get yearly energy
        fetch(`${API_BASE}/energy/yearly/${year}`)
            .then(response => response.json())
            .then(data => {
                if (yearlyEnergyElement && data.energy_wh !== undefined) {
                    yearlyEnergyElement.textContent = `${(data.energy_wh / 1000).toFixed(3)} kWh`;
                }
            })
            .catch(error => {
                console.error("Error fetching yearly energy:", error);
                // Don't update the UI with an error, keep existing value
            });
    }
    
    // Fetch error logs
    function fetchErrorLogs() {
        // Use the fault status endpoint
        fetch(`${API_BASE}/data/faults`)
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error! Status: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                if (errorsDisplay) {
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
                }
            })
            .catch(error => {
                console.error("Error fetching fault data:", error);
                // Don't update the UI with an error, keep existing values
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
    
    // Function to handle refresh button click
    function setupRefreshButton() {
        const refreshButton = document.querySelector('.refresh-button');
        if (refreshButton) {
            refreshButton.addEventListener('click', function() {
                fetchSystemInfo();
                fetchStatus();
                fetchPowerData();
                fetchBatteryStatus();
                fetchEnergyStats();
                fetchErrorLogs();
            });
        }
    }
    
    // Initial data fetch
    fetchSystemInfo();
    fetchStatus();
    fetchPowerData();
    fetchBatteryStatus();
    fetchEnergyStats();
    fetchErrorLogs();
    setupRefreshButton();
    
    // Set up periodic refresh
    setInterval(fetchStatus, 30000); // Every 30 seconds
    setInterval(fetchPowerData, 10000); // Every 10 seconds
    setInterval(fetchBatteryStatus, 15000); // Every 15 seconds
    setInterval(fetchEnergyStats, 60000); // Every minute
    setInterval(fetchErrorLogs, 60000); // Every minute
    setInterval(fetchSystemInfo, 300000); // Every 5 minutes (model info doesn't change often)
});