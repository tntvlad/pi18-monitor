# P18 Inverter API Documentation

This document describes the REST API endpoints available for interacting with the P18 Inverter.

## Base URL

All API endpoints are relative to the base URL:

```
http://<inverter_ip>:5000
```

## API Versioning

The current API version is v1, which is included in all API paths.

## Authentication

Currently, the API does not require authentication.

---

## GET Endpoints (Data Retrieval)

These endpoints are used to retrieve data from the inverter without making any changes.

### System Information Endpoints

#### Get Protocol ID

```
GET /api/v1/inverter/info/protocol
```

Returns the protocol ID and version information.

**Response Example:**
```json
{
  "protocol_id": "18",
  "protocol_version": "1.0"
}
```

#### Get Serial Number

```
GET /api/v1/inverter/info/serial
```

Returns the inverter's serial number.

**Response Example:**
```json
{
  "serial_number": "9613221210129",
  "serial_length": 13
}
```

#### Get Firmware Version

```
GET /api/v1/inverter/info/firmware
```

Returns the firmware versions for the inverter's CPUs.

**Response Example:**
```json
{
  "main_cpu_version": "00072.70",
  "slave1_cpu_version": "00062.20",
  "slave2_cpu_version": "00000.00"
}
```

#### Get Machine Model

```
GET /api/v1/inverter/info/model
```

Returns the inverter's model information.

**Response Example:**
```json
{
  "model_code": "07",
  "model_name": "EASUN IGRID SV IV",
  "timestamp": "2025-09-09T22:30:21.478507"
}
```

#### Get Inverter Ratings

```
GET /api/v1/inverter/info/ratings
```

Returns the inverter's rated information including AC input/output specifications, battery parameters, and system configuration.

**Response Example:**
```json
{
  "ac_input": {
    "voltage": 230.0,
    "current": 24.3
  },
  "ac_output": {
    "voltage": 230.0,
    "frequency": 50.0,
    "current": 24.3,
    "apparent_power": 5600,
    "active_power": 5600
  },
  "battery": {
    "voltage": 48.0,
    "recharge_voltage": 47.0,
    "redischarge_voltage": 0.0,
    "under_voltage": 44.0,
    "bulk_voltage": 52.0,
    "float_voltage": 52.0,
    "type": "User"
  },
  "charging": {
    "max_ac_current": 2,
    "max_total_current": 60
  },
  "system": {
    "input_voltage_range": "Appliance",
    "output_priority": "Solar-Battery-Utility",
    "charger_priority": "Solar only",
    "parallel_max": 9,
    "machine_type": "Off-grid",
    "topology": "Transformer",
    "output_mode": "Phase 3 of 3",
    "solar_power_priority": "Battery-Load-Utility",
    "mppt_strings": 1
  },
  "raw_response": "2300,243,2300,500,243,5600,5600,480,470,000,440,520,520,2,002,060,0,1,2,9,1,0,4,1,1,0",
  "total_values": 26
}
```

### Real-time Data Endpoints

#### Get General Status

```
GET /api/v1/inverter/data/status
```

Returns the current status of the inverter including grid, output, battery, temperature, PV, and system status information.

**Response Example:**
```json
{
  "grid": {
    "voltage": 230.5,
    "frequency": 50.0
  },
  "output": {
    "voltage": 230.0,
    "frequency": 50.0,
    "apparent_power": 1200,
    "active_power": 1050,
    "load_percent": 18
  },
  "battery": {
    "voltage": 48.2,
    "voltage_scc1": 0.0,
    "voltage_scc2": 0.0,
    "discharge_current": 22,
    "charging_current": 0,
    "capacity_percent": 85
  },
  "temperature": {
    "heatsink": 38,
    "mppt1": 35,
    "mppt2": 0
  },
  "pv": {
    "pv1_power": 0,
    "pv2_power": 0,
    "pv1_voltage": 0.0,
    "pv2_voltage": 0.0
  },
  "status": {
    "configuration_changed": false,
    "mppt1_status": "normal",
    "mppt2_status": "normal",
    "load_connected": true,
    "battery_direction": "discharge",
    "dc_ac_direction": "DC-AC",
    "line_direction": "donothing"
  }
}
```

#### Get Working Mode

```
GET /api/v1/inverter/data/mode
```

Returns the current working mode of the inverter.

**Response Example:**
```json
{
  "mode": "battery",
  "mode_code": 3,
  "mode_description": "Battery mode"
}
```

#### Get Fault Status

```
GET /api/v1/inverter/data/faults
```

Returns any active faults or warnings from the inverter.

**Response Example:**
```json
{
  "fault_code": 0,
  "faults": {
    "line_fail": true,
    "output_short": false,
    "over_temperature": false,
    "fan_locked": false,
    "battery_voltage_high": false,
    "battery_low": false,
    "battery_under": false,
    "overload": false,
    "eeprom_fail": false,
    "power_limit": false,
    "pv1_voltage_high": false,
    "pv2_voltage_high": false,
    "mppt1_overload": false,
    "mppt2_overload": false,
    "battery_low_scc1": false,
    "battery_low_scc2": false
  }
}
```

### Time Management Endpoints

#### Get Current Time

```
GET /api/v1/inverter/time/current
```

Returns the current time from the inverter.

**Response Example:**
```json
{
  "datetime": "2025-09-09T22:30:21",
  "year": 2025,
  "month": 9,
  "day": 9,
  "hour": 22,
  "minute": 30,
  "second": 21,
  "timestamp": "2025-09-09T22:30:21.478507"
}
```

#### Get Charge Schedule

```
GET /api/v1/inverter/time/charge-schedule
```

Returns the AC charge schedule.

**Response Example:**
```json
{
  "start_time": "00:00",
  "end_time": "23:59",
  "enabled": true,
  "timestamp": "2025-09-09T22:30:21.478507"
}
```

#### Get Load Schedule

```
GET /api/v1/inverter/time/load-schedule
```

Returns the AC load schedule.

**Response Example:**
```json
{
  "start_time": "00:00",
  "end_time": "23:59",
  "enabled": true,
  "timestamp": "2025-09-09T22:30:21.478507"
}
```

### Energy Statistics Endpoints

#### Get Total Energy

```
GET /api/v1/inverter/energy/total
```

Returns the total energy generated by the inverter.

**Response Example:**
```json
{
  "total_energy_wh": 2358029,
  "total_energy_kwh": 2358.029,
  "unit": "kWh"
}
```

#### Get Yearly Energy

```
GET /api/v1/inverter/energy/yearly/{year}
```

Returns the energy generated during the specified year.

**Parameters:**
- `year`: The year to get energy data for (e.g., 2025)

**Response Example:**
```json
{
  "energy_wh": 1258000,
  "energy_kwh": 1258.0,
  "unit": "kWh",
  "year": 2025
}
```

#### Get Monthly Energy

```
GET /api/v1/inverter/energy/monthly/{year}/{month}
```

Returns the energy generated during the specified month.

**Parameters:**
- `year`: The year to get energy data for (e.g., 2025)
- `month`: The month to get energy data for (1-12)

**Response Example:**
```json
{
  "energy_wh": 125800,
  "energy_kwh": 125.8,
  "unit": "kWh",
  "year": 2025,
  "month": 9
}
```

#### Get Daily Energy

```
GET /api/v1/inverter/energy/daily/{date}
```

Returns the energy generated on the specified date.

**Parameters:**
- `date`: The date to get energy data for (format: YYYY-MM-DD)

**Response Example:**
```json
{
  "date": "2025-09-09",
  "energy_wh": 12580,
  "energy_kwh": 12.58,
  "unit": "kWh"
}
```

### Parallel System Endpoints

#### Get Parallel System Info

```
GET /api/v1/inverter/parallel/{id}/info
```

Returns information about a specific inverter in a parallel system.

**Parameters:**
- `id`: The ID of the inverter in the parallel system

**Response Example:**
```json
{
  "id": 1,
  "status": "online",
  "role": "master",
  "firmware_version": "1.0"
}
```

#### Get Parallel System Status

```
GET /api/v1/inverter/parallel/{id}/status
```

Returns the status of a specific inverter in a parallel system.

**Parameters:**
- `id`: The ID of the inverter in the parallel system

**Response Example:**
```json
{
  "id": 1,
  "output_voltage": 230.0,
  "output_frequency": 50.0,
  "output_power": 500,
  "load_percent": 10
}
```

---

## SET Endpoints (Configuration)

These endpoints are used to modify inverter settings or send commands.

### Time Management Endpoints

#### Set Current Time

```
PUT /api/v1/inverter/time/current
```

Sets the inverter's current time.

**Request Body:**
```json
{
  "datetime": "2025-09-09T22:30:21"
}
```

**Response Example:**
```json
{
  "status": "success",
  "datetime": "2025-09-09T22:30:21",
  "timestamp": "2025-09-09T22:30:21.478507"
}
```

### Settings Management Endpoints

#### Set Output Voltage

```
PUT /api/v1/inverter/settings/output-voltage
```

Sets the inverter's output voltage.

**Request Body:**
```json
{
  "voltage": 230.0
}
```

**Response Example:**
```json
{
  "status": "success",
  "message": "Output voltage set to 230.0V",
  "voltage": 230.0
}
```

### Command Endpoints

#### Set Load Output

```
POST /api/v1/inverter/commands/load-output
```

Enables or disables the load output.

**Request Body:**
```json
{
  "enabled": true
}
```

**Response Example:**
```json
{
  "status": "success",
  "message": "Load output enabled",
  "enabled": true
}
```

#### Factory Reset

```
POST /api/v1/inverter/commands/factory-reset
```

Resets the inverter to factory defaults.

**Response Example:**
```json
{
  "status": "success",
  "message": "Factory reset successful"
}
```

#### Clear Energy Data

```
DELETE /api/v1/inverter/energy/clear
```

Clears all energy data from the inverter.

**Response Example:**
```json
{
  "status": "success",
  "message": "All energy data cleared"
}
```

---

## Legacy Endpoints

These endpoints are maintained for backward compatibility and may be deprecated in future versions.

### Send Command

```
GET /api/command/{cmd}
```

Sends a raw command to the inverter.

**Parameters:**
- `cmd`: The command to send

**Response Example:**
```json
{
  "response": "^D00503"
}
```

### Set Port

```
POST /api/set_port
```

Sets the serial port to use for communication.

**Request Body:**
```json
{
  "port": "/dev/ttyUSB1"
}
```

**Response Example:**
```json
{
  "success": true
}
```

### Set Time (Legacy Format)

```
PUT /api/set_time
```

Sets the inverter time using legacy format.

**Request Body:**
```json
{
  "timestr": "250909223021"
}
```

**Response Example:**
```json
{
  "status": "success",
  "datetime": "2025-09-09T22:30:21",
  "timestamp": "2025-09-09T22:30:21.478507"
}
```