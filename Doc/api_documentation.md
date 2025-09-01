1. System Information (/api/v1/inverter/info) ✅ Complete

## 1.1 Get Protocol ID ✅ Complete
- Legacy Command: PI
- HTTP Method: GET
- Endpoint: /api/v1/inverter/info/protocol
- Raw Command: ^P005PI<CRC><cr>
- Raw Response: ^D00518<CRC><cr>
- Response:
  ```json
  {
    "protocol_id": "18",
    "protocol_version": "1.0"
  }
  ```

## 1.2 Get Serial Number ✅ Complete
- Legacy Command: ID
- HTTP Method: GET
- Endpoint: /api/v1/inverter/info/serial
- Raw Command: ^P005ID<CRC><cr>
- Raw Response: ^D025LLXXXXXXXXXXXXXXXXXXXX<CRC><cr>
- Response:
  ```json
  {
    "serial_number": "01234567890123",
    "serial_length": 14
  }
  ```

## 1.3 Get Firmware Version ✅ Complete
- Legacy Command: VFW
- HTTP Method: GET
- Endpoint: /api/v1/inverter/info/firmware
- Raw Command: ^P006VFW<CRC><cr>
- Raw Response: ^D020aaaaa,bbbbb,ccccc<CRC><cr>
- Response:
  ```json
  {
    "main_cpu_version": "00001",
    "slave1_cpu_version": "00001",
    "slave2_cpu_version": "00001"
  }
  ```

## 1.4 Get Rated Information ✅ Complete
- Legacy Command: PIRI
- HTTP Method: GET
- Endpoint: /api/v1/inverter/info/ratings
- Raw Command: ^P007PIRI<CRC><cr>
- Response:
  ```json
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
  ```

2. Real-time Data (/api/v1/inverter/data) ✅ Complete

## 2.1 Get General Status ✅ Complete
- Legacy Command: GS
- HTTP Method: GET
- Endpoint: /api/v1/inverter/data/status
- Raw Command: ^P005GS<CRC><cr>
- Response:
  ```json
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
  ```

## 2.2 Get Working Mode ✅ Complete
- Legacy Command: MOD
- HTTP Method: GET
- Endpoint: /api/v1/inverter/data/mode
- Raw Command: ^P006MOD<CRC><cr>
- Response:
  ```json
  {
    "mode": "hybrid",
    "mode_code": 5,
    "mode_description": "Hybrid mode (Line mode, Grid mode)"
  }
  ```

## 2.3 Get Fault and Warning Status ✅ Complete
- Legacy Command: FWS
- HTTP Method: GET
- Endpoint: /api/v1/inverter/data/faults
- Raw Command: ^P005FWS<CRC><cr>
- Raw Response: ^D034AA,B,C,D,E,F,G,H,I,J,K,L,M,N,O,P,Q<CRC><cr>
- Response:
  ```json
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
  ```
  
  When a fault is detected, the response includes an error description:
  ```json
  {
    "fault_code": 1,
    "faults": {
      "line_fail": false,
      "output_short": false,
      "over_temperature": false,
      "fan_locked": true,
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
    },
    "error": {
      "code": "1",
      "description": "Fan is locked"
    }
  }
  ```
  🔒 Error Codes Reference

```json
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
```

3. Time Management (/api/v1/inverter/time) 🔘 In Progress

## 3.1 Get Current Time 🔘 In Progress
- Legacy Command: T
- HTTP Method: GET
- Endpoint: /api/v1/inverter/time/current
- Raw Command: ^P004T<CRC><cr>
- Raw Response: ^D017YYYYMMDDHHMMSS<CRC><cr>
- Response:
  ```json
  {
    "datetime": "2024-08-31T18:30:45",
    "year": 2024,
    "month": 8,
    "day": 31,
    "hour": 18,
    "minute": 30,
    "second": 45
  }
  ```

## 3.2 Set Date Time 🔘 In Progress
- Legacy Command: DAT
- HTTP Method: PUT
- Endpoint: /api/v1/inverter/time/current
- Raw Command: ^S018DATyymmddhhffss<cr>
- Request Body:
  ```json
  {
    "datetime": "2024-08-31T18:30:45"
  }
  ```
- Response:
  ```json
  {
    "status": "success",
    "datetime": "2024-08-31T18:30:45"
  }
  ```

## 3.3 Get AC Charge Time Bucket 🔘 In Progress
- Legacy Command: ACCT
- HTTP Method: GET
- Endpoint: /api/v1/inverter/time/charge-schedule
- Raw Command: ^P007ACCT<CRC><cr>
- Raw Response: ^D008HHMMHHMME<CRC><cr> (HH=hour, MM=minute, E=enabled)
- Response:
  ```json
  {
    "start_time": "00:00",
    "end_time": "23:59",
    "enabled": true
  }
  ```

## 3.4 Get AC Load Time Bucket 🔘 In Progress
- Legacy Command: ACLT
- HTTP Method: GET
- Endpoint: /api/v1/inverter/time/load-schedule
- Raw Command: ^P007ACLT<CRC><cr>
- Raw Response: ^D008HHMMHHMME<CRC><cr> (HH=hour, MM=minute, E=enabled)
- Response:
  ```json
  {
    "start_time": "00:00",
    "end_time": "23:59",
    "enabled": true
  }
  ```

4. Energy Statistics (/api/v1/inverter/energy) 🔘 In Progress

## 4.1 Get Total Generated Energy ✅ Complete
- Legacy Command: ET
- HTTP Method: GET
- Endpoint: /api/v1/inverter/energy/total
- Raw Command: ^P005ET<CRC><cr>
- Raw Response: ^D011NNNNNNNN<CRC><cr>
- Response:
  ```json
  {
    "total_energy_kwh": 12345678,
    "unit": "kWh"
  }
  ```

## 4.2 Get Yearly Energy 🔘 In Progress
- Legacy Command: EY
- HTTP Method: GET
- Endpoint: /api/v1/inverter/energy/yearly/{year}
- Raw Command: ^P009EYyyyy<CRC><cr>
- Raw Response: ^DXXXYYYY:NNNNNNNN<CRC><cr>
- Response:
  ```json
  {
    "year": 2024,
    "energy_kwh": 3650,
    "unit": "kWh"
  }
  ```

## 4.3 Get Monthly Energy 🔘 In Progress
- Legacy Command: EM
- HTTP Method: GET
- Endpoint: /api/v1/inverter/energy/monthly/{year}/{month}
- Raw Command: ^P011EMyyyymm<CRC><cr>
- Raw Response: ^DXXXYYYYMM:NNNNNNNN<CRC><cr>
- Response:
  ```json
  {
    "year": 2024,
    "month": 8,
    "energy_kwh": 300,
    "unit": "kWh"
  }
  ```

## 4.4 Get Daily Energy ✅ Complete
- Legacy Command: ED
- HTTP Method: GET
- Endpoint: /api/v1/inverter/energy/daily/{date}
- Raw Command: ^P013EDyyyymmdd<CRC><cr>
- Raw Response: ^DXXXYYYYMMDD:NNNNNNNN<CRC><cr>
- Response:
  ```json
  {
    "date": "2024-08-31",
    "energy_wh": 10000,
    "unit": "Wh"
  }
  ```

## 4.5 Clear Energy Data 🔘 In Progress
- Legacy Command: CLE
- HTTP Method: DELETE
- Endpoint: /api/v1/inverter/energy/clear
- Raw Command: ^S006CLE<cr>
- Response:
  ```json
  {
    "status": "success",
    "message": "All energy data cleared"
  }
  ```

5. Settings Management (/api/v1/inverter/settings) 🔘 In Progress

## 5.1 Get Default Parameters 🔘 In Progress
- Legacy Command: DI
- HTTP Method: GET
- Endpoint: /api/v1/inverter/settings/defaults
- Raw Command: ^P005DI<CRC><cr>
- Response:
  ```json
  {
    "message": "Default parameters retrieved",
    "parameters": {
      "output_voltage": 230.0,
      "output_frequency": 50,
      "battery_type": "AGM"
    }
  }
  ```

## 5.2 Set Output Voltage 🔘 In Progress
- Legacy Command: V
- HTTP Method: PUT
- Endpoint: /api/v1/inverter/settings/output-voltage
- Raw Command: ^S008Vnnnn<CRC><cr>
- Request Body:
  ```json
  {
    "voltage": 230.0
  }
  ```
- Valid values: 202.0, 208.0, 220.0, 230.0, 240.0
- Response:
  ```json
  {
    "status": "success",
    "message": "Output voltage set to 230.0V",
    "voltage": 230.0
  }
  ```

## 5.3 Set Output Frequency ❌ Not Implemented
- Legacy Command: F50/F60
- HTTP Method: PUT
- Endpoint: /api/v1/inverter/settings/output-frequency
- Request Body:
  ```json
  {
    "frequency": 50
  }
  ```
- Valid values: 50, 60

## 5.4 Set Battery Type ❌ Not Implemented
- Legacy Command: PBT
- HTTP Method: PUT
- Endpoint: /api/v1/inverter/settings/battery-type
- Request Body:
  ```json
  {
    "type": "AGM"
  }
  ```
- Valid values: "AGM", "Flooded", "User"

## 5.5 Set Charging Current ❌ Not Implemented
- Legacy Command: MCHGC
- HTTP Method: PUT
- Endpoint: /api/v1/inverter/settings/charge-current
- Request Body:
  ```json
  {
    "max_charge_current": 60,
    "max_ac_charge_current": 30
  }
  ```

## 5.6 Set Charging Voltage ❌ Not Implemented
- Legacy Command: MCHGV
- HTTP Method: PUT
- Endpoint: /api/v1/inverter/settings/charge-voltage
- Request Body:
  ```json
  {
    "bulk_voltage": 56.4,
    "float_voltage": 54.0
  }
  ```

## 5.7 Set Priority Settings ❌ Not Implemented
- Legacy Command: POP/PCP/PSP
- HTTP Method: PUT
- Endpoint: /api/v1/inverter/settings/priorities
- Request Body:
  ```json
  {
    "output_priority": "Solar-Battery-Utility",
    "charger_priority": "Solar first",
    "solar_power_priority": "Load-Battery-Utility"
  }
  ```

6. Commands (/api/v1/inverter/commands) 🔘 In Progress

## 6.1 Enable/Disable Load Output 🔘 In Progress
- Legacy Command: LON/LOFF
- HTTP Method: POST
- Endpoint: /api/v1/inverter/commands/load-output
- Raw Command: ^P006LON<CRC><cr> or ^P007LOFF<CRC><cr>
- Request Body:
  ```json
  {
    "enabled": true
  }
  ```
- Response:
  ```json
  {
    "status": "success",
    "message": "Load output enabled",
    "enabled": true
  }
  ```

## 6.2 Reset to Defaults 🔘 In Progress
- Legacy Command: PF
- HTTP Method: POST
- Endpoint: /api/v1/inverter/commands/factory-reset
- Raw Command: ^P005PF<CRC><cr>
- Response:
  ```json
  {
    "status": "success",
    "message": "Factory reset successful"
  }
  ```

## 6.3 Enable/Disable Features ❌ Not Implemented
- Legacy Command: P
- HTTP Method: POST
- Endpoint: /api/v1/inverter/commands/features
- Request Body:
  ```json
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
  ```

7. Parallel System (/api/v1/inverter/parallel) 🔘 In Progress

## 7.1 Get Parallel System Info 🔘 In Progress
- Legacy Command: PRI
- HTTP Method: GET
- Endpoint: /api/v1/inverter/parallel/{id}/info
- Raw Command: ^P006PRIn<CRC><cr> (where n is the inverter ID)
- Response:
  ```json
  {
    "id": 1,
    "status": "online",
    "role": "master",
    "firmware_version": "1.0"
  }
  ```

## 7.2 Get Parallel System Status 🔘 In Progress
- Legacy Command: PGS
- HTTP Method: GET
- Endpoint: /api/v1/inverter/parallel/{id}/status
- Raw Command: ^P006PGSn<CRC><cr> (where n is the inverter ID)
- Response:
  ```json
  {
    "id": 1,
    "output_voltage": 230.0,
    "output_frequency": 50.0,
    "output_power": 500,
    "load_percent": 10
  }
  ```

## 7.3 Set Parallel Configuration ❌ Not Implemented
- Legacy Command: POPM
- HTTP Method: PUT
- Endpoint: /api/v1/inverter/parallel/config

8. Debug Endpoints (Legacy)

## 8.1 Direct Command ⚠️ For Debugging Only
- HTTP Method: GET
- Endpoint: /api/command/{cmd}
- Description: Send a direct command to the inverter and get the raw response
- Note: The {cmd} parameter is case-sensitive and should be in UPPERCASE
- Example: `/api/command/GS` to get the general status raw response
- Response:
  ```json
  {
    "response": "^D106..."
  }
  ```
- Warning: Use with caution as improper commands may affect inverter operation

## 8.2 Set Serial Port ⚠️ For Debugging Only
- HTTP Method: POST
- Endpoint: /api/set_port
- Request Body:
  ```json
  {
    "port": "/dev/ttyUSB0"
  }
  ```
- Response:
  ```json
  {
    "success": true
  }
  ```

## 8.3 Set Time (Legacy) ⚠️ For Debugging Only
- HTTP Method: PUT
- Endpoint: /api/set_time
- Request Body:
  ```json
  {
    "timestr": "230901153045"
  }
  ```
- Note: This is a legacy endpoint. Use /api/v1/inverter/time/current instead.

