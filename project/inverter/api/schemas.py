# inverter/api/schemas.py
""" API response schemas for consistent formatting """
from datetime import datetime

def format_inverter_status(raw_data):
    """Format general status data"""
    return {
        "grid": {
            "voltage": float(raw_data.get('ac_in_voltage', '0')),
            "frequency": float(raw_data.get('ac_in_frequency', '0'))
        },
        "output": {
            "voltage": float(raw_data.get('ac_out_voltage', '0')),
            "frequency": float(raw_data.get('ac_out_frequency', '0')),
            "apparent_power": int(raw_data.get('ac_apparent_power', '0')),
            "active_power": int(raw_data.get('ac_active_power', '0')),
            "load_percent": int(raw_data.get('load_percent', '0'))
        },
        "battery": {
            "voltage": float(raw_data.get('battery_voltage', '0')),
            "charge_current": float(raw_data.get('battery_charge_current', '0')),
            "discharge_current": float(raw_data.get('battery_discharge_current', '0')),
            "capacity": int(raw_data.get('battery_capacity', '0')),
            "scc_voltage": float(raw_data.get('battery_scc_voltage', '0'))
        },
        "pv": {
            "input_voltage": float(raw_data.get('pv_input_voltage', '0')),
            "input_current": float(raw_data.get('pv_input_current', '0'))
        },
        "system": {
            "bus_voltage": float(raw_data.get('bus_voltage', '0')),
            "heat_sink_temperature": float(raw_data.get('inverter_heat_sink_temp', '0')),
            "status": parse_device_status(raw_data.get('device_status', '00000000'))
        },
        "timestamp": datetime.now().isoformat()
    }

def parse_device_status(status_bits):
    """Parse device status bits into readable format"""
    if not status_bits or len(status_bits) < 8:
        return {"raw_status": "unknown"}
    
    try:
        # Convert to binary representation
        bits = bin(int(status_bits, 16))[2:].zfill(8)
        
        return {
            "raw_status": status_bits,
            "scc_charging": bits[0] == '1',
            "ac_charging": bits[1] == '1',
            "battery_voltage_steady": bits[2] == '1',
            "battery_voltage_low": bits[3] == '1',
            "load_enabled": bits[4] == '1',
            "steady_mode": bits[5] == '1',
            "scc_charging_enabled": bits[6] == '1',
            "ac_charging_enabled": bits[7] == '1'
        }
    except ValueError:
        return {"raw_status": status_bits}

def format_error_response(message, code=500):
    """Format error responses consistently"""
    return {
        "error": {
            "message": message,
            "code": code,
            "timestamp": datetime.now().isoformat()
        }
    }

def format_power_data(data):
    """Format power generation data"""
    return {
        "power": {
            "current_watts": float(data.get('current_power', 0)),
            "daily_kwh": float(data.get('daily_yield', 0)),
            "total_kwh": float(data.get('total_yield', 0))
        },
        "electrical": {
            "voltage": float(data.get('voltage', 0)),
            "current": float(data.get('current', 0))
        },
        "timestamp": data.get('timestamp', datetime.now().isoformat())
    }

def format_battery_status(data):
    """Format battery status data"""
    return {
        "voltage": float(data.get('voltage', 0)),
        "charge_current": float(data.get('charge_current', 0)),
        "discharge_current": float(data.get('discharge_current', 0)),
        "capacity_percent": int(data.get('capacity', 0)),
        "temperature": float(data.get('temperature', 0)) if 'temperature' in data else None,
        "health": {
            "status": get_battery_health_status(data),
            "cycles": int(data.get('cycles', 0)) if 'cycles' in data else None
        },
        "timestamp": data.get('timestamp', datetime.now().isoformat())
    }

def get_battery_health_status(data):
    """Determine battery health status based on capacity and voltage"""
    capacity = int(data.get('capacity', 0))
    voltage = float(data.get('voltage', 0))
    
    if capacity > 80:
        return "good"
    elif capacity > 50:
        return "fair"
    elif capacity > 20:
        return "poor"
    else:
        return "critical"

def format_error_logs(data):
    """Format error logs data"""
    formatted_errors = []
    
    for error in data.get('errors', []):
        formatted_errors.append({
            "code": error.get('code', 'unknown'),
            "message": error.get('message', 'Unknown error'),
            "timestamp": error.get('time', datetime.now().isoformat()),
            "severity": get_error_severity(error.get('code', 'unknown'))
        })
    
    return {
        "errors": formatted_errors,
        "count": len(formatted_errors),
        "last_error_time": data.get('last_error_time')
    }

def get_error_severity(error_code):
    """Determine error severity based on error code"""
    critical_errors = ['E001', 'E002', 'E003']
    warnings = ['W001', 'W002', 'W003']
    
    if error_code in critical_errors:
        return "critical"
    elif error_code in warnings:
        return "warning"
    else:
        return "info"