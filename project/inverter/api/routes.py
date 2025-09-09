# inverter/api/routes.py
""" REST API endpoints for P18 Inverter """
from flask import Blueprint, jsonify, request, current_app
from datetime import datetime
import re

api_bp = Blueprint('api', __name__)

def get_monitor():
    """Get monitor instance from Flask app context"""
    return current_app.monitor

# =========================================================================
# System Information Endpoints (/api/v1/inverter/info)
# =========================================================================
@api_bp.route('/api/v1/inverter/info/protocol')
def get_protocol_id():
    """Get protocol ID"""
    monitor = get_monitor()
    result, error = monitor.send_p18_command('PI')
    if result:
        protocol_id = monitor.parse_protocol_id(result)
        return jsonify({
            "protocol_id": protocol_id,
            "protocol_version": "1.0"
        })
    return jsonify({'error': 'Failed to get protocol ID'}), 500

@api_bp.route('/api/v1/inverter/info/serial')
def get_serial_number():
    """Get inverter serial number"""
    monitor = get_monitor()
    result, error = monitor.send_p18_command('ID')
    if result:
        serial_data = monitor.parse_serial_number(result)
        if serial_data:
            return jsonify(serial_data)
    return jsonify({'error': 'Failed to get serial number'}), 500

@api_bp.route('/api/v1/inverter/info/firmware')
def get_firmware_version():
    """Get firmware versions"""
    monitor = get_monitor()
    result, error = monitor.send_p18_command('VFW')
    if result:
        firmware_data = monitor.parse_firmware_version(result)
        if firmware_data:
            return jsonify(firmware_data)
    return jsonify({'error': 'Failed to get firmware version'}), 500

@api_bp.route('/api/v1/inverter/info/model')
def get_machine_model():
    """Get inverter machine model"""
    monitor = get_monitor()
    model_info = monitor.get_machine_model()
    if 'error' not in model_info:
        return jsonify(model_info)
    return jsonify({'error': 'Failed to get machine model'}), 500

@api_bp.route('/api/v1/inverter/info/ratings')
def get_ratings():
    """Get inverter rated information"""
    monitor = get_monitor()
    ratings_data, error = monitor.get_rated_info()
    if ratings_data:
        return jsonify(ratings_data)
    return jsonify({'error': 'Failed to get rated information', 'details': error}), 500

@api_bp.route('/api/debug/piri')
def debug_piri():
    """Debug PIRI command response"""
    monitor = get_monitor()
    
    try:
        # Test raw PIRI command
        raw_result, raw_error = monitor.send_p18_command('PIRI')
        
        # Test the get_rated_info method
        parsed_data, parsed_error = monitor.get_rated_info()
        
        debug_info = {
            "raw_command": {
                "response": raw_result,
                "error": raw_error,
                "length": len(raw_result) if raw_result else 0
            },
            "parsed_method": {
                "data": parsed_data,
                "error": parsed_error,
                "success": parsed_data is not None
            },
            "recent_errors": monitor.error_log[-5:] if monitor.error_log else [],
            "connection_status": monitor.connected,
            "port": monitor.port
        }
        
        # If we have raw response, try to extract payload manually
        if raw_result:
            payload = monitor.safe_extract_payload(raw_result)
            debug_info["payload_extraction"] = {
                "payload": payload,
                "values": payload.split() if payload else None,
                "values_count": len(payload.split()) if payload else 0
            }
        
        return jsonify(debug_info)
        
    except Exception as e:
        return jsonify({
            "error": f"Debug error: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }), 500


# =========================================================================
# Real-time Data Endpoints (/api/v1/inverter/data)
# =========================================================================
@api_bp.route('/api/v1/inverter/data/status')
def get_general_status():
    """Get general status of the inverter in structured format exactly matching documentation"""
    monitor = get_monitor()
    
    # Send the GS command to get the latest data
    result, error = monitor.send_p18_command('GS')
    if not result:
        return jsonify({'error': 'Failed to get general status'}), 500
        
    try:
        # Parse the raw GS command response
        # Format: ^D106AAAA,BBB,CCCC,DDD,EEEE,FFFF,GGG,HHH,III,JJJ,KKK,LLL,MMM,NNN,OOO,PPP,QQQQ,RRRR,SSSS,TTTT,U,V,W,X,Y,Z,a,b<CRC><cr>
        
        # Extract the data part from the response
        match = re.search(r'\^D\d+(.+?)(?:<|$)', result)
        if not match:
            return jsonify({'error': 'Invalid response format'}), 500
            
        # Split the data by commas
        data_parts = match.group(1).split(',')
        if len(data_parts) < 27:  # We expect at least 27 fields based on the documentation
            return jsonify({'error': f'Incomplete response data. Got {len(data_parts)} fields, expected at least 27'}), 500
        
        # Parse the values according to the documentation
        # Grid values (AAAA, BBB)
        grid_voltage = float(data_parts[0]) / 10 if data_parts[0].isdigit() else 0.0  # AAAA: Grid voltage
        grid_frequency = float(data_parts[1]) / 10 if data_parts[1].isdigit() else 0.0  # BBB: Grid frequency
        
        # AC output values (CCCC, DDD, EEEE, FFFF, GGG)
        ac_out_voltage = float(data_parts[2]) / 10 if data_parts[2].isdigit() else 0.0  # CCCC: AC output voltage
        ac_out_frequency = float(data_parts[3]) / 10 if data_parts[3].isdigit() else 0.0  # DDD: AC output frequency
        ac_out_apparent_power = int(data_parts[4]) if data_parts[4].isdigit() else 0  # EEEE: AC output apparent power
        ac_out_active_power = int(data_parts[5]) if data_parts[5].isdigit() else 0  # FFFF: AC output active power
        output_load_percent = int(data_parts[6]) if data_parts[6].isdigit() else 0  # GGG: Output load percent
        
        # Battery values (HHH, III, JJJ, KKK, LLL, MMM)
        battery_voltage = float(data_parts[7]) / 10 if data_parts[7].isdigit() else 0.0  # HHH: Battery voltage
        battery_voltage_scc1 = float(data_parts[8]) / 10 if data_parts[8].isdigit() else 0.0  # III: Battery voltage from SCC1
        battery_voltage_scc2 = float(data_parts[9]) / 10 if data_parts[9].isdigit() else 0.0  # JJJ: Battery voltage from SCC2
        battery_discharge_current = int(data_parts[10]) if data_parts[10].isdigit() else 0  # KKK: Battery discharge current
        battery_charging_current = int(data_parts[11]) if data_parts[11].isdigit() else 0  # LLL: Battery charging current
        battery_capacity = int(data_parts[12]) if data_parts[12].isdigit() else 0  # MMM: Battery capacity
        
        # Temperature values (NNN, OOO, PPP)
        inverter_heatsink_temp = int(data_parts[13]) if data_parts[13].isdigit() else 0  # NNN: Inverter heat sink temperature
        mppt1_temperature = int(data_parts[14]) if data_parts[14].isdigit() else 0  # OOO: MPPT1 charger temperature
        mppt2_temperature = int(data_parts[15]) if data_parts[15].isdigit() else 0  # PPP: MPPT2 charger temperature
        
        # PV values (QQQQ, RRRR, SSSS, TTTT)
        pv1_power = int(data_parts[16]) if data_parts[16].isdigit() else 0  # QQQQ: PV1 Input power
        pv2_power = int(data_parts[17]) if data_parts[17].isdigit() else 0  # RRRR: PV2 Input power
        pv1_voltage = float(data_parts[18]) / 10 if data_parts[18].isdigit() else 0.0  # SSSS: PV1 Input voltage
        pv2_voltage = float(data_parts[19]) / 10 if data_parts[19].isdigit() else 0.0  # TTTT: PV2 Input voltage
        
        # Status values (U, V, W, X, Y, Z, a)
        setting_changed = data_parts[20] == "1" if len(data_parts) > 20 else False  # U: Setting value configuration state
        
        # MPPT charger status
        mppt1_status = "normal"
        if len(data_parts) > 21:
            if data_parts[21] == "0":
                mppt1_status = "abnormal"
            elif data_parts[21] == "1":
                mppt1_status = "normal"
            elif data_parts[21] == "2":
                mppt1_status = "charging"
        
        mppt2_status = "normal"
        if len(data_parts) > 22:
            if data_parts[22] == "0":
                mppt2_status = "abnormal"
            elif data_parts[22] == "1":
                mppt2_status = "normal"
            elif data_parts[22] == "2":
                mppt2_status = "charging"
        
        # Load connection status
        load_connected = False
        if len(data_parts) > 23:
            load_connected = data_parts[23] == "1"
        
        # Battery power direction
        battery_direction = "donothing"
        if len(data_parts) > 24:
            if data_parts[24] == "1":
                battery_direction = "charge"
            elif data_parts[24] == "2":
                battery_direction = "discharge"
        
        # DC/AC power direction
        dc_ac_direction = "donothing"
        if len(data_parts) > 25:
            if data_parts[25] == "1":
                dc_ac_direction = "AC-DC"
            elif data_parts[25] == "2":
                dc_ac_direction = "DC-AC"
        
        # Line power direction
        line_direction = "donothing"
        if len(data_parts) > 26:
            if data_parts[26] == "1":
                line_direction = "input"
            elif data_parts[26] == "2":
                line_direction = "output"
        
        # Format the response exactly as specified in the documentation
        formatted_response = {
            "grid": {
                "voltage": grid_voltage,
                "frequency": grid_frequency
            },
            "output": {
                "voltage": ac_out_voltage,
                "frequency": ac_out_frequency,
                "apparent_power": ac_out_apparent_power,
                "active_power": ac_out_active_power,
                "load_percent": output_load_percent
            },
            "battery": {
                "voltage": battery_voltage,
                "voltage_scc1": battery_voltage_scc1,
                "voltage_scc2": battery_voltage_scc2,
                "discharge_current": battery_discharge_current,
                "charging_current": battery_charging_current,
                "capacity_percent": battery_capacity
            },
            "temperature": {
                "heatsink": inverter_heatsink_temp,
                "mppt1": mppt1_temperature,
                "mppt2": mppt2_temperature
            },
            "pv": {
                "pv1_power": pv1_power,
                "pv2_power": pv2_power,
                "pv1_voltage": pv1_voltage,
                "pv2_voltage": pv2_voltage
            },
            "status": {
                "configuration_changed": setting_changed,
                "mppt1_status": mppt1_status,
                "mppt2_status": mppt2_status,
                "load_connected": load_connected,
                "battery_direction": battery_direction,
                "dc_ac_direction": dc_ac_direction,
                "line_direction": line_direction
            }
        }
        
        return jsonify(formatted_response)
        
    except Exception as e:
        return jsonify({'error': f'Error parsing general status: {str(e)}'}), 500

@api_bp.route('/api/v1/inverter/data/mode')
def get_working_mode():
    """Get working mode of the inverter"""
    monitor = get_monitor()
    result, error = monitor.send_p18_command('MOD')
    if result:
        mode = monitor.parse_mode_response(result)
        
        # Map the mode string to code and description
        mode_mapping = {
            'Power On': {'code': 0, 'description': 'Power On mode'},
            'Standby': {'code': 1, 'description': 'Standby mode'},
            'Bypass': {'code': 2, 'description': 'Bypass mode (Line mode)'},
            'Battery': {'code': 3, 'description': 'Battery mode'},
            'Fault': {'code': 4, 'description': 'Fault mode'},
            'Hybrid': {'code': 5, 'description': 'Hybrid mode (Line mode, Grid mode)'}
        }
        
        mode_info = mode_mapping.get(mode, {'code': -1, 'description': 'Unknown mode'})
        
        return jsonify({
            "mode": mode.lower(),
            "mode_code": mode_info['code'],
            "mode_description": mode_info['description']
        })
    return jsonify({'error': 'Failed to get working mode'}), 500

@api_bp.route('/api/v1/inverter/data/faults')
def get_fault_status():
    """Get fault and warning status"""
    monitor = get_monitor()
    result, error = monitor.send_p18_command('FWS')
    if result:
        try:
            # Parse the fault status response based on the provided documentation
            # Format: ^D034AA,B,C,D,E,F,G,H,I,J,K,L,M,N,O,P,Q<CRC><cr>
            match = re.search(r'\^D\d+(.+?)(?:<|$)', result)
            if not match:
                return jsonify({'error': 'Invalid response format'}), 500
                
            # Split the data by commas
            data_parts = match.group(1).split(',')
            if len(data_parts) < 17:  # We expect at least 17 fields
                return jsonify({'error': f'Incomplete response data. Got {len(data_parts)} fields, expected at least 17'}), 500
            
            # Extract fault code from the first field (AA)
            fault_code = int(data_parts[0]) if data_parts[0].isdigit() else 0
            
            # Map the rest of the fields to their corresponding fault flags
            # B through Q represent different fault conditions
            fault_status = {
                "line_fail": data_parts[1] == "1" if len(data_parts) > 1 else False,  # B: Line fail
                "output_short": data_parts[2] == "1" if len(data_parts) > 2 else False,  # C: Output circuit short
                "over_temperature": data_parts[3] == "1" if len(data_parts) > 3 else False,  # D: Inverter over temperature
                "fan_locked": data_parts[4] == "1" if len(data_parts) > 4 else False,  # E: Fan lock
                "battery_voltage_high": data_parts[5] == "1" if len(data_parts) > 5 else False,  # F: Battery voltage high
                "battery_low": data_parts[6] == "1" if len(data_parts) > 6 else False,  # G: Battery low
                "battery_under": data_parts[7] == "1" if len(data_parts) > 7 else False,  # H: Battery under
                "overload": data_parts[8] == "1" if len(data_parts) > 8 else False,  # I: Over load
                "eeprom_fail": data_parts[9] == "1" if len(data_parts) > 9 else False,  # J: Eeprom fail
                "power_limit": data_parts[10] == "1" if len(data_parts) > 10 else False,  # K: Power limit
                "pv1_voltage_high": data_parts[11] == "1" if len(data_parts) > 11 else False,  # L: PV1 voltage high
                "pv2_voltage_high": data_parts[12] == "1" if len(data_parts) > 12 else False,  # M: PV2 voltage high
                "mppt1_overload": data_parts[13] == "1" if len(data_parts) > 13 else False,  # N: MPPT1 overload warning
                "mppt2_overload": data_parts[14] == "1" if len(data_parts) > 14 else False,  # O: MPPT2 overload warning
                "battery_low_scc1": data_parts[15] == "1" if len(data_parts) > 15 else False,  # P: Battery too low to charge for SCC1
                "battery_low_scc2": data_parts[16] == "1" if len(data_parts) > 16 else False   # Q: Battery too low to charge for SCC2
            }
            
            # Add error code descriptions if fault_code is non-zero
            error_descriptions = {}
            if fault_code > 0:
                error_codes = {
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
                error_descriptions = {
                    "code": str(fault_code),
                    "description": error_codes.get(str(fault_code), "Unknown error")
                }
            
            response = {
                "fault_code": fault_code,
                "faults": fault_status
            }
            
            # Add error description if available
            if error_descriptions:
                response["error"] = error_descriptions
                
            return jsonify(response)
            
        except Exception as e:
            return jsonify({'error': f'Error parsing fault status: {str(e)}'}), 500
    return jsonify({'error': 'Failed to get fault status'}), 500

# =========================================================================
# Time Management Endpoints (/api/v1/inverter/time)
# =========================================================================
@api_bp.route('/api/v1/inverter/time/current')
def get_inverter_time():
    """Get current time from inverter"""
    monitor = get_monitor()
    time_data = monitor.get_current_time()
    
    if 'error' not in time_data:
        return jsonify(time_data)
    return jsonify({'error': 'Failed to get inverter time'}), 500

@api_bp.route('/api/v1/inverter/time/current', methods=['PUT'])
def set_inverter_time():
    """Set inverter time"""
    try:
        data = request.get_json()
        if not data or 'datetime' not in data:
            return jsonify({'error': 'Missing datetime parameter'}), 400
            
        # Parse the datetime string
        dt_str = data['datetime']
        try:
            dt = datetime.fromisoformat(dt_str)
        except ValueError:
            return jsonify({'error': 'Invalid datetime format. Use ISO format (YYYY-MM-DDTHH:MM:SS)'}), 400
        
        # Use the monitor's set_time method
        monitor = get_monitor()
        result = monitor.set_time(dt)
        
        if 'error' not in result:
            return jsonify(result)
        return jsonify({'error': result['error']}), 500
        
    except Exception as e:
        return jsonify({'error': f'Error setting time: {str(e)}'}), 500

@api_bp.route('/api/v1/inverter/time/charge-schedule')
def get_charge_schedule():
    """Get AC charge time bucket"""
    monitor = get_monitor()
    schedule_data = monitor.get_ac_charge_schedule()
    
    if 'error' not in schedule_data:
        return jsonify(schedule_data)
    return jsonify({'error': 'Failed to get charge schedule'}), 500

@api_bp.route('/api/v1/inverter/time/load-schedule')
def get_load_schedule():
    """Get AC load time bucket"""
    monitor = get_monitor()
    schedule_data = monitor.get_ac_load_schedule()
    
    if 'error' not in schedule_data:
        return jsonify(schedule_data)
    return jsonify({'error': 'Failed to get load schedule'}), 500

# =========================================================================
# Energy Statistics Endpoints (/api/v1/inverter/energy)
# =========================================================================
@api_bp.route('/api/v1/inverter/energy/total')
def get_total_energy():
    """Get total generated energy"""
    monitor = get_monitor()
    result, error = monitor.send_p18_command('ET')
    
    if error:
        return jsonify({'error': f'Command error: {error}'}), 500
        
    if result:
        # Parse total energy
        # Format: ^DXXXNNNNNNN where XXX is the data length
        # Example: "^D01102358029"
        
        # Remove any non-alphanumeric characters that might be in the response
        result = re.sub(r'[^a-zA-Z0-9]', '', result)
        
        # Match D followed by 3 digits (data length), then capture all remaining digits
        match = re.search(r'D\d{3}(\d+)', result)
        if match:
            try:
                energy_wh = int(match.group(1))
                # Convert from Wh to kWh
                energy_kwh = energy_wh / 1000
                
                return jsonify({
                    "total_energy_wh": energy_wh,
                    "total_energy_kwh": energy_kwh,
                    "unit": "kWh"
                })
            except ValueError:
                return jsonify({'error': f'Invalid energy value format: {match.group(1)}'}), 500
        else:
            return jsonify({'error': f'Invalid response format: {result}'}), 500
    
    return jsonify({'error': 'No response from inverter'}), 500

@api_bp.route('/api/v1/inverter/energy/yearly/<int:year>')
def get_yearly_energy(year):
    """Get yearly energy statistics"""
    monitor = get_monitor()
    command = f"EY{year}"
    result, error = monitor.send_p18_command(command)
    
    if error:
        return jsonify({'error': f'Command error: {error}'}), 500
        
    if result:
        # Clean the response by removing any non-alphanumeric characters
        result = re.sub(r'[^a-zA-Z0-9]', '', result)
        
        # Parse yearly energy
        # Format: ^D011NNNNNNNN<CRC><cr> where NNNNNNNN is the energy in Wh
        match = re.search(r'D\d{3}(\d+)', result)
        if match:
            try:
                energy_wh = int(match.group(1))
                # Convert from Wh to kWh with decimal precision
                energy_kwh = energy_wh / 1000
                
                return jsonify({
                    "energy_wh": energy_wh,
                    "energy_kwh": energy_kwh,
                    "unit": "kWh",
                    "year": year
                })
            except ValueError:
                return jsonify({'error': f'Invalid energy value format: {match.group(1)}'}), 500
        else:
            return jsonify({'error': f'Invalid response format: {result}'}), 500
    
    return jsonify({'error': 'No response from inverter'}), 500

@api_bp.route('/api/v1/inverter/energy/monthly/<int:year>/<int:month>')
def get_monthly_energy(year, month):
    """Get monthly energy statistics"""
    monitor = get_monitor()
    command = f"EM{year:04d}{month:02d}"
    result, error = monitor.send_p18_command(command)
    
    if error:
        return jsonify({'error': f'Command error: {error}'}), 500
        
    if result:
        # Clean the response by removing any non-alphanumeric characters
        result = re.sub(r'[^a-zA-Z0-9]', '', result)
        
        # Parse monthly energy
        # Format: ^D011NNNNNNNN<CRC><cr> where NNNNNNNN is the energy in Wh (not kWh as previously assumed)
        match = re.search(r'D\d{3}(\d+)', result)
        if match:
            try:
                energy_wh = int(match.group(1))
                # Convert from Wh to kWh with decimal precision
                energy_kwh = energy_wh / 1000
                
                return jsonify({
                    "energy_wh": energy_wh,
                    "energy_kwh": energy_kwh,
                    "unit": "kWh",
                    "year": year,
                    "month": month
                })
            except ValueError:
                return jsonify({'error': f'Invalid energy value format: {match.group(1)}'}), 500
        else:
            return jsonify({'error': f'Invalid response format: {result}'}), 500
    
    return jsonify({'error': 'No response from inverter'}), 500

@api_bp.route('/api/v1/inverter/energy/daily/<string:date>')
def get_daily_energy(date):
    """Get daily energy statistics"""
    try:
        # Parse the date string (format: YYYY-MM-DD)
        dt = datetime.fromisoformat(date)
        year = dt.year
        month = dt.month
        day = dt.day
        
        monitor = get_monitor()
        command = f"ED{year:04d}{month:02d}{day:02d}"
        result, error = monitor.send_p18_command(command)
        
        if error:
            return jsonify({'error': f'Command error: {error}'}), 500
        
        if result:
            # Clean the response by removing any non-alphanumeric characters
            result = re.sub(r'[^a-zA-Z0-9]', '', result)
            
            # Parse daily energy
            # Format: D01NNNNNNNN according to protocol documentation
            match = re.search(r'D\d{3}(\d+)', result)
            if match:
                try:
                    energy_wh = int(match.group(1))
                    # Convert to kWh for consistency
                    energy_kwh = energy_wh / 1000
                    
                    return jsonify({
                        "date": date,
                        "energy_wh": energy_wh,
                        "energy_kwh": energy_kwh,
                        "unit": "kWh"
                    })
                except ValueError:
                    return jsonify({'error': f'Invalid energy value format: {match.group(1)}'}), 500
            else:
                return jsonify({'error': f'Invalid response format: {result}'}), 500
                
        return jsonify({'error': 'Failed to get daily energy data'}), 500
    except ValueError:
        return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400

@api_bp.route('/api/v1/inverter/energy/clear', methods=['DELETE'])
def clear_energy_data():
    """Clear energy data"""
    monitor = get_monitor()
    
    try:
        # The clear energy command needs special handling because it starts with S not P
        cmd = "^S006CLE\r"
        
        # Send directly without using send_p18_command since this is an S command not P command
        if not monitor.ser or not monitor.ser.is_open:
            if not monitor.connect():
                return jsonify({'error': 'Could not connect to inverter'}), 500
        
        monitor.ser.reset_input_buffer()
        monitor.ser.reset_output_buffer()
        monitor.ser.write(cmd.encode('ascii'))
        monitor.ser.flush()
        
        # Read response
        response = ""
        while True:
            char = monitor.ser.read(1)
            if not char:
                break
            response += char.decode('ascii', errors='ignore')
            if response.endswith('\r'):
                break
            if len(response) > 100:
                break
        
        if response:
            # Check if the response starts with ^1 which indicates command acceptance
            if response.startswith('^1'):
                return jsonify({
                    "status": "success",
                    "message": "All energy data cleared"
                })
            else:
                return jsonify({'error': f'Command refused: {response}'}), 400
        return jsonify({'error': 'No response from inverter'}), 504
    except Exception as e:
        return jsonify({'error': f'Error clearing energy data: {str(e)}'}), 500

# =========================================================================
# Settings Management Endpoints (/api/v1/inverter/settings)
# =========================================================================
@api_bp.route('/api/v1/inverter/settings/defaults')
def get_default_parameters():
    """Get default parameters"""
    monitor = get_monitor()
    result, error = monitor.send_p18_command('DI')
    
    if result:
        # This is a placeholder - adjust based on actual response format
        try:
            # Parse the response to extract default parameters
            # The format would depend on the actual response from the inverter
            return jsonify({
                "message": "Default parameters retrieved",
                "parameters": {
                    "output_voltage": 230.0,
                    "output_frequency": 50,
                    "battery_type": "AGM"
                    # Add other default parameters as needed
                }
            })
        except Exception as e:
            return jsonify({'error': f'Error parsing default parameters: {str(e)}'}), 500
    
    return jsonify({'error': 'Failed to get default parameters'}), 500

@api_bp.route('/api/v1/inverter/settings/output-voltage', methods=['PUT'])
def set_output_voltage():
    """Set output voltage"""
    try:
        data = request.get_json()
        if not data or 'voltage' not in data:
            return jsonify({'error': 'Missing voltage parameter'}), 400
            
        voltage = float(data['voltage'])
        
        # Check if voltage is valid
        valid_voltages = [202.0, 208.0, 220.0, 230.0, 240.0]
        if voltage not in valid_voltages:
            return jsonify({'error': f'Invalid voltage. Valid values are: {valid_voltages}'}), 400
        
        # Format voltage for command (remove decimal point)
        voltage_str = f"{int(voltage * 10):04d}"
        command = f"V{voltage_str}"
        
        monitor = get_monitor()
        result, error = monitor.send_p18_command(command)
        
        if result and "ACK" in result:
            return jsonify({
                "status": "success",
                "message": f"Output voltage set to {voltage}V",
                "voltage": voltage
            })
        
        return jsonify({'error': 'Failed to set output voltage'}), 500
        
    except ValueError:
        return jsonify({'error': 'Invalid voltage value'}), 400
    except Exception as e:
        return jsonify({'error': f'Error setting output voltage: {str(e)}'}), 500

# =========================================================================
# Commands Endpoints (/api/v1/inverter/commands)
# =========================================================================
@api_bp.route('/api/v1/inverter/commands/load-output', methods=['POST'])
def set_load_output():
    """Enable/disable load output"""
    try:
        data = request.get_json()
        if not data or 'enabled' not in data:
            return jsonify({'error': 'Missing enabled parameter'}), 400
            
        enabled = bool(data['enabled'])
        command = "LON" if enabled else "LOFF"
        
        monitor = get_monitor()
        result, error = monitor.send_p18_command(command)
        
        if result and "ACK" in result:
            return jsonify({
                "status": "success",
                "message": f"Load output {'enabled' if enabled else 'disabled'}",
                "enabled": enabled
            })
        
        return jsonify({'error': 'Failed to set load output'}), 500
        
    except Exception as e:
        return jsonify({'error': f'Error setting load output: {str(e)}'}), 500

@api_bp.route('/api/v1/inverter/commands/factory-reset', methods=['POST'])
def factory_reset():
    """Reset to factory defaults"""
    monitor = get_monitor()
    result, error = monitor.send_p18_command('PF')
    
    if result and "ACK" in result:
        return jsonify({
            "status": "success",
            "message": "Factory reset successful"
        })
    
    return jsonify({'error': 'Failed to perform factory reset'}), 500

# =========================================================================
# Parallel System Endpoints (/api/v1/inverter/parallel)
# =========================================================================
@api_bp.route('/api/v1/inverter/parallel/<int:id>/info')
def get_parallel_info(id):
    """Get parallel system info"""
    monitor = get_monitor()
    command = f"PRI{id}"
    result, error = monitor.send_p18_command(command)
    
    if result:
        # This is a placeholder - adjust based on actual response format
        try:
            # Parse the response to extract parallel system info
            return jsonify({
                "id": id,
                "status": "online",
                "role": "master" if id == 1 else "slave",
                "firmware_version": "1.0"
            })
        except Exception as e:
            return jsonify({'error': f'Error parsing parallel system info: {str(e)}'}), 500
    
    return jsonify({'error': 'Failed to get parallel system info'}), 500

@api_bp.route('/api/v1/inverter/parallel/<int:id>/status')
def get_parallel_status(id):
    """Get parallel system status"""
    monitor = get_monitor()
    command = f"PGS{id}"
    result, error = monitor.send_p18_command(command)
    
    if result:
        # This is a placeholder - adjust based on actual response format
        try:
            # Parse the response to extract parallel system status
            return jsonify({
                "id": id,
                "output_voltage": 230.0,
                "output_frequency": 50.0,
                "output_power": 500,
                "load_percent": 10
            })
        except Exception as e:
            return jsonify({'error': f'Error parsing parallel system status: {str(e)}'}), 500
    
    return jsonify({'error': 'Failed to get parallel system status'}), 500

# =========================================================================
# Legacy endpoints for backward compatibility
# =========================================================================
@api_bp.route('/api/command/<cmd>')
def send_command(cmd):
    """Send command to inverter (legacy endpoint)"""
    monitor = get_monitor()
    result, error = monitor.send_p18_command(cmd)
    if result:
        return jsonify({'response': result})
    return jsonify({'error': 'No response'}), 500

@api_bp.route('/api/set_port', methods=['POST'])
def set_port():
    """Set the serial port to use (legacy endpoint)"""
    data = request.get_json()
    if not data or 'port' not in data:
        return jsonify({'error': 'Missing port parameter'}), 400
    
    port = data['port']
    monitor = get_monitor()
    
    try:
        # Disconnect current connection if any
        monitor.disconnect()
        # Update port
        monitor.port = port
        # Test connection
        if monitor.connect():
            monitor.disconnect()  # We'll reconnect when needed
            return jsonify({'success': True})
        else:
            return jsonify({'error': 'Could not connect to port'}), 400
    except Exception as e:
        return jsonify({'error': f'Error setting port: {str(e)}'}), 500

@api_bp.route('/api/set_time', methods=['PUT'])
def set_time_legacy():
    """Set inverter time using format: yymmddhhmmss (legacy endpoint)"""
    data = request.get_json()
    if not data or 'timestr' not in data:
        return jsonify({'error': 'Missing timestr parameter'}), 400
    
    timestr = data['timestr']
    if len(timestr) != 12:
        return jsonify({'error': 'Invalid time format'}), 400
    
    # Convert the legacy format to ISO format
    try:
        year = int('20' + timestr[0:2])  # Assuming 20xx years
        month = int(timestr[2:4])
        day = int(timestr[4:6])
        hour = int(timestr[6:8])
        minute = int(timestr[8:10])
        second = int(timestr[10:12])
        
        dt = datetime(year, month, day, hour, minute, second)
        
        # Use the monitor's set_time method
        monitor = get_monitor()
        result = monitor.set_time(dt)
        
        if 'error' not in result:
            return jsonify(result)
        return jsonify({'error': result['error']}), 500
        
    except Exception as e:
        return jsonify({'error': f'Error setting time: {str(e)}'}), 500