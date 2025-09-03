# In Progress Features

1. System Information (/api/v1/inverter/info) ✅ Complete

## 1.1 Get Protocol ID ✅ Complete
- Legacy Command: PI
- HTTP Method: GET
- Endpoint: /api/v1/inverter/info/protocol
- Raw Command: ^P005PI<CRC><cr>
- Raw Response: ^D00518<CRC><cr>
- Response:
  {
    "protocol_id": "18",
    "protocol_version": "1.0"
  }

## 1.2 Get Serial Number ✅ Complete
- Legacy Command: ID
- HTTP Method: GET
- Endpoint: /api/v1/inverter/info/serial
- Raw Command: ^P005ID<CRC><cr>
- Raw Response: ^D025LLXXXXXXXXXXXXXXXXXXXX<CRC><cr>
- Response:
  {
    "serial_number": "01234567890123",
    "serial_length": 14
  }

## 1.3 Get Firmware Version ✅ Complete
- Legacy Command: VFW
- HTTP Method: GET
- Endpoint: /api/v1/inverter/info/firmware
- Raw Command: ^P006VFW<CRC><cr>
- Raw Response: ^D020aaaaa,bbbbb,ccccc<CRC><cr>
- Response:
  {
    "main_cpu_version": "00001",
    "slave1_cpu_version": "00001",
    "slave2_cpu_version": "00001"
  }

## 1.4 Get Machine Model ✅ Complete
- Legacy Command: GMN
- HTTP Method: GET
- Endpoint: /api/v1/inverter/info/model
- Raw Command: ^P006GMN<CRC><cr>
- Raw Response: ^D005AA<CRC><cr>
- Response:
  {
    "model_code": "02",
    "model_name": "INFINISOLAR V II",
    "timestamp": "2025-09-03T11:57:52.396Z"
  }

## 1.5 Get Rated Information ✅ Complete
- Legacy Command: PIRI
- HTTP Method: GET
- Endpoint: /api/v1/inverter/info/ratings
- Raw Command: ^P007PIRI<CRC><cr>
- Response:
  {
    "ac_input": {
      "voltage": 230.0,
      "current": 21.7
    },
    "ac_output": {
      "voltage": 230.0,
      "frequency": 50.0,
      "current": 21.7,
      "apparent_power": 5000,
      "active_power": 5000
    },
    "battery": {
      "voltage": 48.0,
      "recharge_voltage": 46.0,
      "redischarge_voltage": 54.0,
      "under_voltage": 42.0,
      "bulk_voltage": 56.4,
      "float_voltage": 54.0,
      "type": "AGM"
    },
    "charging": {
      "max_ac_current": 60,
      "max_total_current": 80
    },
    "system": {
      "input_voltage_range": "Appliance",
      "output_priority": "Solar-Utility-Battery",
      "charger_priority": "Solar first",
      "parallel_max": 6,
      "machine_type": "Off-grid",
      "topology": "Transformer",
      "output_mode": "Single",
      "solar_power_priority": "Battery-Load-Utility",
      "mppt_strings": 2
    }
  }

2. Real-time Data (/api/v1/inverter/data) ✅ Complete

## 2.1 Get General Status ✅ Complete
- Legacy Command: GS
- HTTP Method: GET
- Endpoint: /api/v1/inverter/data/status
- Raw Command: ^P005GS<CRC><cr>
- Response:
  {
    "grid": {
      "voltage": 230.0,
      "frequency": 50.0
    },
    "output": {
      "voltage": 230.0,
      "frequency": 50.0,
      "apparent_power": 500,
      "active_power": 400,
      "load_percent": 10
    },
    "battery": {
      "voltage": 48.5,
      "voltage_scc1": 0.0,
      "voltage_scc2": 0.0,
      "discharge_current": 0,
      "charging_current": 10,
      "capacity_percent": 100
    },
    "temperature": {
      "heatsink": 45,
      "mppt1": 0,
      "mppt2": 0
    },
    "pv": {
      "pv1_power": 1000,
      "pv2_power": 1000,
      "pv1_voltage": 120.0,
      "pv2_voltage": 120.0
    },
    "status": {
      "configuration_changed": false,
      "mppt1_status": "charging",
      "mppt2_status": "charging",
      "load_connected": true,
      "battery_direction": "charge",
      "dc_ac_direction": "DC-AC",
      "line_direction": "input"
    }
  }

## 2.2 Get Working Mode ✅ Complete
- Legacy Command: MOD
- HTTP Method: GET
- Endpoint: /api/v1/inverter/data/mode
- Raw Command: ^P006MOD<CRC><cr>
- Response:
  {
    "mode": "hybrid",
    "mode_code": 5,
    "mode_description": "Hybrid mode (Line mode, Grid mode)"
  }

## 2.3 Get Fault and Warning Status ✅ Complete
- Legacy Command: FWS
- HTTP Method: GET
- Endpoint: /api/v1/inverter/data/faults
- Raw Command: ^P005FWS<CRC><cr>
- Response:
  {
    "fault_code": 0,
    "faults": {
      "line_fail": false,
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

3. Time Management (/api/v1/inverter/time) ✅ Complete

## 3.1 Get Current Time ✅ Complete
- Legacy Command: T
- HTTP Method: GET
- Endpoint: /api/v1/inverter/time/current
- Raw Command: ^P004T<CRC><cr>
- Raw Response: ^D017YYYYMMDDHHMMSS<CRC><cr>
- Response:
  {
    "datetime": "2024-08-31T18:30:45",
    "year": 2024,
    "month": 8,
    "day": 31,
    "hour": 18,
    "minute": 30,
    "second": 45,
    "timestamp": "2025-09-03T12:21:43.279Z"
  }

## 3.2 Set Date Time ✅ Complete
- Legacy Command: DAT
- HTTP Method: PUT
- Endpoint: /api/v1/inverter/time/current
- Raw Command: ^S018DATyymmddhhffss<cr>
- Request Body:
  {
    "datetime": "2024-08-31T18:30:45"
  }
- Response:
  {
    "status": "success",
    "datetime": "2024-08-31T18:30:45",
    "timestamp": "2025-09-03T12:21:43.279Z"
  }

## 3.3 Get AC Charge Time Bucket ✅ Complete
- Legacy Command: ACCT
- HTTP Method: GET
- Endpoint: /api/v1/inverter/time/charge-schedule
- Raw Response: ^D008HHMMHHMME<CRC><cr>
- Response:
  {
    "start_time": "00:00",
    "end_time": "23:59",
    "enabled": true,
    "timestamp": "2025-09-03T12:21:43.279Z"
  }

## 3.4 Get AC Load Time Bucket ✅ Complete
- Legacy Command: ACLT
- HTTP Method: GET
- Endpoint: /api/v1/inverter/time/load-schedule
- Raw Response: ^D008HHMMHHMME<CRC><cr>
- Response:
  {
    "start_time": "00:00",
    "end_time": "23:59",
    "enabled": true,
    "timestamp": "2025-09-03T12:21:43.279Z"
  }

4. Energy Statistics (/api/v1/inverter/energy) ✅ Complete

## 4.1 Get Total Generated Energy ✅ Complete
- Legacy Command: ET
- HTTP Method: GET
- Endpoint: /api/v1/inverter/energy/total
- Raw Command: ^P005ET<CRC><cr>
- Response:
  {
    "total_energy_kwh": 12345678,
    "unit": "kWh"
  }

## 4.2 Get Yearly Energy ✅ Complete
- Legacy Command: EY
- HTTP Method: GET
- Endpoint: /api/v1/inverter/energy/yearly/{year}
- Raw Command: ^P009EYyyyy<CRC><cr>
- Response:
  {
    "energy_kwh": 3650,
    "unit": "kWh",
    "year": 2024
  }

## 4.3 Get Monthly Energy ✅ Complete
- Legacy Command: EM
- HTTP Method: GET
- Endpoint: /api/v1/inverter/energy/monthly/{year}/{month}
- Raw Command: ^P011EMyyyymm<cr>
- Response:
  {
    "energy_kwh": 300,
    "unit": "kWh",
    "year": 2024,
    "month": 8
  }

## 4.4 Get Daily Energy ✅ Complete
- Legacy Command: ED
- HTTP Method: GET
- Endpoint: /api/v1/inverter/energy/daily/{date}
- Raw Command: ^P013EDyyyymmdd<cr>
- Response:
  {
    "date": "2024-08-31",
    "energy_wh": 10000,
    "energy_kwh": 10.0,
    "unit": "Wh"
  }

## 4.5 Clear Energy Data ✅ Complete
- Legacy Command: CLE
- HTTP Method: DELETE
- Endpoint: /api/v1/inverter/energy/clear
- Raw Command: ^S006CLE<cr>
- Response:
  {
    "status": "success",
    "message": "All energy data cleared"
  }

5. Settings Management (/api/v1/inverter/settings) 🔘 In Progress

## 5.1 Get Default Parameters 🔘 In Progress
- Legacy Command: DI
- HTTP Method: GET
- Endpoint: /api/v1/inverter/settings/defaults

## 5.2 Set Output Voltage 🔘 In Progress
- Legacy Command: V
- HTTP Method: PUT
- Endpoint: /api/v1/inverter/settings/output-voltage
- Raw Command: ^S008Vnnnn<CRC><cr>
- Request Body:
  {
    "voltage": 230.0
  }
- Valid values: 202.0, 208.0, 220.0, 230.0, 240.0

## 5.3 Set Output Frequency ❌ Not Done
- Legacy Command: F50/F60
- HTTP Method: PUT
- Endpoint: /api/v1/inverter/settings/output-frequency
- Request Body:
  {
    "frequency": 50
  }
- Valid values: 50, 60

## 5.4 Set Battery Type ❌ Not Done
- Legacy Command: PBT
- HTTP Method: PUT
- Endpoint: /api/v1/inverter/settings/battery-type
- Request Body:
  {
    "type": "AGM"
  }
- Valid values: "AGM", "Flooded", "User"

## 5.5 Set Charging Current ❌ Not Done
- Legacy Command: MCHGC
- HTTP Method: PUT
- Endpoint: /api/v1/inverter/settings/charge-current
- Request Body:
  {
    "max_charge_current": 60,
    "max_ac_charge_current": 30
  }

## 5.6 Set Charging Voltage ❌ Not Done
- Legacy Command: MCHGV
- HTTP Method: PUT
- Endpoint: /api/v1/inverter/settings/charge-voltage
- Request Body:
  {
    "bulk_voltage": 56.4,
    "float_voltage": 54.0
  }

## 5.7 Set Priority Settings ❌ Not Done
- Legacy Command: POP/PCP/PSP
- HTTP Method: PUT
- Endpoint: /api/v1/inverter/settings/priorities
- Request Body:
  {
    "output_priority": "Solar-Battery-Utility",
    "charger_priority": "Solar first",
    "solar_power_priority": "Load-Battery-Utility"
  }

6. Commands (/api/v1/inverter/commands) 🔘 In Progress

## 6.1 Enable/Disable Load Output 🔘 In Progress
- Legacy Command: LON
- HTTP Method: POST
- Endpoint: /api/v1/inverter/commands/load-output
- Request Body:
  {
    "enabled": true
  }

## 6.2 Reset to Defaults 🔘 In Progress
- Legacy Command: PF
- HTTP Method: POST
- Endpoint: /api/v1/inverter/commands/factory-reset

## 6.3 Enable/Disable Features ❌ Not Done
- Legacy Command: P
- HTTP Method: POST
- Endpoint: /api/v1/inverter/commands/features
- Request Body:
  {
    "buzzer": true,
    "overload_bypass": false,
    "lcd_timeout": true,
    "overload_restart": true,
    "overtemp_restart": true,
    "backlight": true,
    "alarm_on_interrupt": false,
    "fault_record": true
  }

7. Parallel System (/api/v1/inverter/parallel) 🔘 In Progress

## 7.1 Get Parallel System Info 🔘 In Progress
- Legacy Command: PRI
- HTTP Method: GET
- Endpoint: /api/v1/inverter/parallel/{id}/info

## 7.2 Get Parallel System Status 🔘 In Progress
- Legacy Command: PGS
- HTTP Method: GET
- Endpoint: /api/v1/inverter/parallel/{id}/status

## 7.3 Set Parallel Configuration ❌ Not Done
- Legacy Command: POPM
- HTTP Method: PUT
- Endpoint: /api/v1/inverter/parallel/config

🔒 Error Codes Reference

{
  "error_codes": {
    "1": "Fan is locked",
    "2": "Over temperature",
    "3": "Battery voltage is too high",
    "4": "Battery voltage is too low",
    "5": "Output short circuited or Over temperature",
    "6": "Output voltage is too high",
    "7": "Over load time out",
    "8": "Bus voltage is too high",
    "9": "Bus soft start failed",
    "11": "Main relay failed",
    "51": "Over current inverter",
    "52": "Bus soft start failed",
    "53": "Inverter soft start failed",
    "54": "Self-test failed",
    "55": "Over DC voltage on output of inverter",
    "56": "Battery connection is open",
    "57": "Current sensor failed",
    "58": "Output voltage is too low",
    "60": "Inverter negative power",
    "71": "Parallel version different",
    "72": "Output circuit failed",
    "80": "CAN communication failed",
    "81": "Parallel host line lost",
    "82": "Parallel synchronized signal lost",
    "83": "Parallel battery voltage detect different",
    "84": "Parallel Line voltage or frequency detect different",
    "85": "Parallel Line input current unbalanced",
    "86": "Parallel output setting different"
  }
}