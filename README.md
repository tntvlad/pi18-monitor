# P18 Inverter Monitor

A web-based monitoring and control interface for P18 inverters.

![P18 Inverter Monitor](https://via.placeholder.com/800x400?text=P18+Inverter+Monitor)

## Overview

This project provides a simple yet powerful web interface for monitoring and controlling P18 inverters. It allows you to view real-time data, send commands, and manage inverter settings through an easy-to-use web dashboard.

## Features

- **Real-time Monitoring**: View live data from your inverter including:
  - System status and working mode
  - Power output and load information
  - Battery status (voltage, charge/discharge current, capacity)
  - Solar panel performance (PV voltage, power, MPPT status)

- **Command Interface**: Send commands directly to your inverter:
  - Get/set system time
  - Query working mode and status
  - Control load output
  - Factory reset

- **Setup Interface**: Configure your connection:
  - Automatic serial port detection
  - Connection testing
  - Port selection

- **RESTful API**: Complete API for integration with other systems:
  - System information endpoints
  - Real-time data endpoints
  - Time management
  - Energy statistics
  - Settings management
  - Command endpoints
  - Parallel system support

## Installation

### Prerequisites

- Python 3.6 or higher
- pySerial library
- Flask web framework

### Setup

There are two ways to set up the P18 Inverter Monitor:

#### Option 1: Using the Installation Script (Recommended)

1. Clone this repository:
   ```bash
   git clone https://github.com/tntvlad/p18-inverter-monitor.git
   cd p18-inverter-monitor
   ```

2. Make the installation script executable:
   ```bash
   chmod +x install.sh
   ```

3. Run the installation script:
   ```bash
   ./install.sh
   ```

The script will:
- Check for Python 3.7+ requirement
- Create and configure a Python virtual environment
- Install all required dependencies
- Add your user to the dialout group for serial port access
- Create a default configuration file
- Set up startup scripts for both development and production
- Create a systemd service file for running as a system service

To start the application, you have several options:

- Development mode:
  ```bash
  ./dev.sh
  ```

- Production mode with Flask:
  ```bash
  ./start.sh flask
  ```

- Production mode with Gunicorn (recommended):
  ```bash
  ./start.sh gunicorn
  ```

To run as a system service:
```bash
sudo cp p18-inverter-api.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable p18-inverter-api.service
sudo systemctl start p18-inverter-api.service
```

#### Option 2: Manual Setup

1. Clone this repository:
   ```bash
   git clone https://github.com/tntvlad/p18-inverter-monitor.git
   cd p18-inverter-monitor
   ```

2. Create and activate a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install required dependencies:
   ```bash
   pip install -r project/requirements.txt
   ```

4. Run the application:
   ```bash
   python -m project.app
   ```

5. Open your web browser and navigate to:
   ```
   http://localhost:5000
   ```

## Usage

### Web Interface

The web interface provides several cards for monitoring different aspects of your inverter:

- **Inverter Status**: View working mode and general status
- **Power Generation**: Monitor PV input and output power
- **Battery Status**: Check battery voltage, capacity, and charge/discharge current
- **Energy Statistics**: View energy production statistics
- **Error Logs**: Monitor any fault conditions

### Setup Page

Access the setup page by clicking the "Setup" link in the header:

1. The system will automatically scan for available serial ports
2. Select your inverter's port from the dropdown
3. Configure additional settings if needed
4. Click "Save Settings" to apply the configuration
5. Use "Test Connection" to verify communication with your inverter

## API Documentation

The application provides a comprehensive RESTful API for integration with other systems. See the [API Documentation](Doc/api_documentation.md) for complete details on all available endpoints.

### Main API Categories

#### System Information
- `GET /api/v1/inverter/info/protocol` - Get protocol ID
- `GET /api/v1/inverter/info/serial` - Get serial number
- `GET /api/v1/inverter/info/firmware` - Get firmware version
- `GET /api/v1/inverter/info/ratings` - Get rated information

#### Real-time Data
- `GET /api/v1/inverter/data/status` - Get general status
- `GET /api/v1/inverter/data/mode` - Get working mode
- `GET /api/v1/inverter/data/faults` - Get fault and warning status

#### Time Management
- `GET /api/v1/inverter/time/current` - Get current time
- `PUT /api/v1/inverter/time/current` - Set date time
- `GET /api/v1/inverter/time/charge-schedule` - Get AC charge time bucket
- `GET /api/v1/inverter/time/load-schedule` - Get AC load time bucket

#### Energy Statistics
- `GET /api/v1/inverter/energy/total` - Get total generated energy
- `GET /api/v1/inverter/energy/yearly/{year}` - Get yearly energy
- `GET /api/v1/inverter/energy/monthly/{year}/{month}` - Get monthly energy
- `GET /api/v1/inverter/energy/daily/{date}` - Get daily energy
- `DELETE /api/v1/inverter/energy/clear` - Clear energy data

#### Settings Management
- `GET /api/v1/inverter/settings/defaults` - Get default parameters
- `PUT /api/v1/inverter/settings/output-voltage` - Set output voltage

#### Commands
- `POST /api/v1/inverter/commands/load-output` - Enable/disable load output
- `POST /api/v1/inverter/commands/factory-reset` - Reset to factory defaults

#### Parallel System
- `GET /api/v1/inverter/parallel/{id}/info` - Get parallel system info
- `GET /api/v1/inverter/parallel/{id}/status` - Get parallel system status

### Debug Endpoints

The following endpoints are provided for debugging purposes only. Use with caution:

- `GET /api/command/{cmd}` - Send a direct command to the inverter and get the raw response
  - The `{cmd}` parameter is case-sensitive and should be in UPPERCASE
  - Example: `/api/command/GS` to get the general status raw response
  - Warning: Improper commands may affect inverter operation

- `POST /api/set_port` - Set the serial port to use
  - Request body: `{"port": "/dev/ttyUSB0"}`

- `PUT /api/set_time` - Legacy endpoint to set inverter time
  - Request body: `{"timestr": "230901153045"}`
  - Note: Use `/api/v1/inverter/time/current` instead

## Technical Details

### Communication Protocol

The application communicates with P18 inverters using a serial protocol:
- Baudrate: 2400
- Data bits: 8
- Parity: None
- Stop bits: 1

Commands are sent in the format: `^Pnnn<command><CRC><cr>` where:
- `^P` is the header
- `nnn` is the length
- `<command>` is the command string
- `<CRC>` is the CRC-16/MODBUS checksum
- `<cr>` is the carriage return character

Responses are typically in the format: `^Dnnn<data><CRC><cr>` where:
- `^D` is the header
- `nnn` is the length
- `<data>` is the response data
- `<CRC>` is the CRC-16/MODBUS checksum
- `<cr>` is the carriage return character

### Architecture

The application consists of several main components:
1. **P18InverterMonitor class**: Handles communication with the inverter
2. **Flask web application**: Provides the web interface
3. **RESTful API**: Provides programmatic access to inverter functions
4. **Frontend Dashboard**: Displays real-time data in a user-friendly format

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Acknowledgements

- Flask for the web framework
- PySerial for serial communication
- P18 Inverter protocol documentation
