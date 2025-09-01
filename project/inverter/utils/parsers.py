# inverter/utils/parsers.py
""" Utility functions for parsing inverter responses """
import re

def parse_p18_response(response):
    """Generic P18 response parser"""
    if not response or not response.startswith('^D'):
        return None
        
    # Extract length and payload
    match = re.match(r'^D(\d{3})(.+?)(?:<|$)', response)
    if match:
        length = int(match.group(1))
        payload = match.group(2)
        return {
            'length': length,
            'payload': payload,
            'raw': response
        }
    return None

def parse_comma_separated_values(payload, field_names):
    """Parse comma-separated response into dictionary"""
    values = payload.split(',')
    result = {}
    for i, name in enumerate(field_names):
        if i < len(values):
            result[name] = values[i]
    return result

def parse_hex_status(hex_value):
    """Parse hex status value into binary flags"""
    try:
        # Convert hex to binary
        binary = bin(int(hex_value, 16))[2:].zfill(8)
        return {
            'bit0': binary[0] == '1',
            'bit1': binary[1] == '1',
            'bit2': binary[2] == '1',
            'bit3': binary[3] == '1',
            'bit4': binary[4] == '1',
            'bit5': binary[5] == '1',
            'bit6': binary[6] == '1',
            'bit7': binary[7] == '1'
        }
    except ValueError:
        return {
            'bit0': False,
            'bit1': False,
            'bit2': False,
            'bit3': False,
            'bit4': False,
            'bit5': False,
            'bit6': False,
            'bit7': False
        }

def parse_qpigs_response(response):
    """Parse QPIGS command response"""
    parsed = parse_p18_response(response)
    if not parsed:
        return None
        
    # Define field names for QPIGS response
    field_names = [
        'ac_in_voltage', 'ac_in_frequency', 'ac_out_voltage',
        'ac_out_frequency', 'ac_apparent_power', 'ac_active_power',
        'load_percent', 'bus_voltage', 'battery_voltage', 'battery_charge_current',
        'battery_capacity', 'inverter_heat_sink_temp', 'pv_input_current',
        'pv_input_voltage', 'battery_scc_voltage', 'battery_discharge_current',
        'device_status'
    ]
    
    return parse_comma_separated_values(parsed['payload'], field_names)

def parse_qmod_response(response):
    """Parse QMOD command response"""
    parsed = parse_p18_response(response)
    if not parsed:
        return None
        
    mode_code = parsed['payload']
    mode_name = {
        'P': 'Power on mode',
        'S': 'Standby mode',
        'L': 'Line mode',
        'B': 'Battery mode',
        'F': 'Fault mode',
        'H': 'Power saving mode'
    }.get(mode_code, 'Unknown mode')
    
    return {
        'mode_code': mode_code,
        'mode_name': mode_name
    }

def parse_qpiri_response(response):
    """Parse QPIRI command response (rated information)"""
    parsed = parse_p18_response(response)
    if not parsed:
        return None
        
    field_names = [
        'grid_rating_voltage', 'grid_rating_current', 'ac_output_rating_voltage',
        'ac_output_rating_frequency', 'ac_output_rating_current', 'ac_output_rating_apparent_power',
        'ac_output_rating_active_power', 'battery_rating_voltage', 'battery_recharge_voltage',
        'battery_under_voltage', 'battery_bulk_voltage', 'battery_float_voltage',
        'battery_type', 'max_ac_charging_current', 'max_charging_current',
        'input_voltage_range', 'output_source_priority', 'charger_source_priority',
        'parallel_max_num', 'machine_type', 'topology', 'output_mode',
        'battery_redischarge_voltage', 'pv_ok_condition', 'pv_power_balance'
    ]
    
    return parse_comma_separated_values(parsed['payload'], field_names)

def parse_qflag_response(response):
    """Parse QFLAG command response (flag status)"""
    parsed = parse_p18_response(response)
    if not parsed:
        return None
        
    if len(parsed['payload']) < 10:
        return None
        
    return {
        'buzzer': parsed['payload'][0] == 'E',
        'overload_bypass': parsed['payload'][1] == 'E',
        'power_saving': parsed['payload'][2] == 'E',
        'lcd_timeout': parsed['payload'][3] == 'E',
        'overload_restart': parsed['payload'][4] == 'E',
        'over_temp_restart': parsed['payload'][5] == 'E',
        'backlight': parsed['payload'][6] == 'E',
        'alarm_on_primary_source_interrupt': parsed['payload'][7] == 'E',
        'fault_code_record': parsed['payload'][8] == 'E',
        'raw_flags': parsed['payload']
    }

def parse_id_response(response):
    """Parse ID command response (serial number)"""
    parsed = parse_p18_response(response)
    if not parsed or len(parsed['payload']) < 2:
        return None
        
    try:
        length = int(parsed['payload'][:2])
        serial = parsed['payload'][2:2+length]
        return {
            'serial_number': serial,
            'serial_length': length
        }
    except (ValueError, IndexError):
        return None

def parse_error_message(error_code):
    """Parse error code into human-readable message"""
    error_messages = {
        'E01': 'Fan is locked',
        'E02': 'Over temperature',
        'E03': 'Battery voltage is too high',
        'E04': 'Battery voltage is too low',
        'E05': 'Output short circuited or over temperature',
        'E06': 'Output voltage is abnormal',
        'E07': 'Overload time out',
        'E08': 'Bus voltage is too high',
        'E09': 'Bus soft start failed',
        'E10': 'PV over current',
        'E11': 'PV over voltage',
        'E12': 'DC over current',
        'E13': 'Battery discharge over current',
        'E51': 'Over current inverter',
        'E52': 'Bus soft start failed',
        'E53': 'Inverter soft start failed',
        'E55': 'DC voltage over in AC output',
        'E56': 'Battery connection open',
        'E57': 'Current sensor failed',
        'E58': 'Output voltage too low',
        'E59': 'PV voltage over limitation'
    }
    
    return error_messages.get(error_code, f'Unknown error: {error_code}')