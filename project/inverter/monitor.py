# inverter/monitor.py
""" P18 Inverter Monitor - Core functionality """
import serial
import time
import threading
import re
from datetime import datetime
import glob
import os

class P18InverterMonitor:
    def __init__(self, port="/dev/ttyUSB1"):
        self.port = port
        self.serial_config = {
            'baudrate': 2400,
            'bytesize': serial.EIGHTBITS,
            'parity': serial.PARITY_NONE,
            'stopbits': serial.STOPBITS_ONE,
            'timeout': 3,
            'write_timeout': 3
        }
        self.ser = None
        self.connected = False
        self.lock = threading.Lock()
        self.last_values = {}
        self.error_log = []
        self.connection_attempts = 0
        self.max_connection_attempts = 3
        self.last_connection_time = 0
        self.connection_cooldown = 2  # seconds
        
        # Status mappings
        self.working_modes = {
            '0': 'Power On', '1': 'Standby', '2': 'Bypass',
            '3': 'Battery', '4': 'Fault', '5': 'Hybrid'
        }
        self.mppt_status = {
            '0': 'Abnormal', '1': 'Normal', '2': 'Charging'
        }
        # Battery and system configuration mappings
        self.battery_types = {
            '0': 'AGM', '1': 'Flooded', '2': 'User', '3': 'Lithium', '4': 'Pylontech'
        }
        self.input_voltage_ranges = {
            '0': 'Appliance', '1': 'UPS'
        }
        self.output_priorities = {
            '0': 'Solar-Utility-Battery', '1': 'Solar-Battery-Utility', '2': 'Utility-Solar-Battery'
        }
        self.charger_priorities = {
            '0': 'Solar first', '1': 'Solar and Utility', '2': 'Solar only'
        }
        self.machine_types = {
            '0': 'Grid-tie', '1': 'Off-grid', '2': 'Hybrid'
        }
        self.topologies = {
            '0': 'Transformer', '1': 'Transformerless'
        }
        self.output_modes = {
            '0': 'Single', '1': 'Parallel', '2': 'Phase 1 of 3', '3': 'Phase 2 of 3', '4': 'Phase 3 of 3'
        }
        self.solar_power_priorities = {
            '0': 'Load-Battery-Utility', '1': 'Battery-Load-Utility'
        }
        
        # Try to connect on initialization
        self.connect()
        
    def connect(self):
        """Establish connection to the inverter with retry logic"""
        # Check if we've tried too recently
        current_time = time.time()
        if (current_time - self.last_connection_time) < self.connection_cooldown:
            time.sleep(0.5)  # Small delay to avoid hammering the port
            
        self.last_connection_time = current_time
        
        # Don't try to reconnect if we're already connected
        if self.ser and self.ser.is_open:
            self.connected = True
            return True
            
        # Try alternative ports if main port fails repeatedly
        ports_to_try = [self.port]
        
        # If we've failed multiple times, try other ports
        if self.connection_attempts >= 2:
            if self.port == "/dev/ttyUSB0":
                ports_to_try.append("/dev/ttyUSB1")
            elif self.port == "/dev/ttyUSB1":
                ports_to_try.append("/dev/ttyUSB0")
                
        for port in ports_to_try:
            try:
                # Close existing connection if any
                if self.ser:
                    try:
                        self.ser.close()
                    except:
                        pass
                
                # Open new connection
                self.ser = serial.Serial(port=port, **self.serial_config)
                self.connected = True
                self.connection_attempts = 0  # Reset counter on success
                
                # If we connected to an alternative port, update our port
                if port != self.port:
                    print(f"Connected to alternative port: {port}")
                    self.port = port
                    
                return True
            except Exception as e:
                self.error_log.append({
                    'time': datetime.now().isoformat(),
                    'code': 'E-CONN',
                    'error': f"Connection error on {port}: {str(e)}"
                })
                
        # Increment connection attempt counter
        self.connection_attempts += 1
        self.connected = False
        return False
            
    def disconnect(self):
        """Close the serial connection"""
        if self.ser and self.ser.is_open:
            try:
                self.ser.close()
            except:
                pass
        self.connected = False
        
    def calculate_crc16_modbus(self, data):
        """Calculate CRC-16/MODBUS"""
        crc = 0xFFFF
        for byte in data:
            crc ^= byte
            for _ in range(8):
                if crc & 0x0001:
                    crc = (crc >> 1) ^ 0xA001
                else:
                    crc >>= 1
        return crc

    def build_p18_command(self, command):
        """Build P18 protocol frame"""
        payload_length = len(command)
        total_length = payload_length + 2 + 1
        frame_start = f"^P{total_length:03d}{command}"
        frame_bytes = frame_start.encode('ascii')
        crc = self.calculate_crc16_modbus(frame_bytes)
        complete_frame = frame_bytes + bytes([(crc >> 8) & 0xFF, crc & 0xFF, 0x0D])
        return complete_frame
        
    def send_p18_command(self, command):
        """Send command to P18 inverter and get response with retry logic"""
        # Try to connect if not connected
        if not self.connected:
            if not self.connect():
                return None, "Not connected to inverter"
                
        # Use a lock to prevent multiple threads from accessing the serial port simultaneously
        with self.lock:
            max_retries = 2
            for attempt in range(max_retries + 1):
                try:
                    # Format and send command
                    frame = self.build_p18_command(command)
                    self.ser.reset_input_buffer()
                    self.ser.reset_output_buffer()
                    
                    self.ser.write(frame)
                    self.ser.flush()
                    
                    # Read response
                    response = ""
                    start_time = time.time()
                    while (time.time() - start_time) < self.serial_config['timeout']:
                        char = self.ser.read(1)
                        if not char:
                            if response:  # If we have some response but hit a timeout
                                break
                            continue
                        response += char.decode('ascii', errors='ignore')
                        if response.endswith('\r'):
                            break
                        if len(response) > 1000:
                            break
                    
                    if not response and attempt < max_retries:
                        # Try reconnecting
                        self.disconnect()
                        if not self.connect():
                            continue  # Skip to next retry
                    elif response:
                        return response.strip(), None
                        
                except Exception as e:
                    self.error_log.append({
                        'time': datetime.now().isoformat(),
                        'code': 'E-CMD',
                        'error': f"Command error: {str(e)}"
                    })
                    
                    if attempt < max_retries:
                        # Try reconnecting
                        self.disconnect()
                        if not self.connect():
                            continue  # Skip to next retry
                    else:
                        return None, str(e)
            
            # If we get here, all retries failed
            return None, "No response from inverter after multiple attempts"

    def validate_p18_response(self, response):
        """
        Validate P18 protocol response format and length

        Args:
            response (str): The response string from the inverter
    
        Returns:
            tuple: (is_valid, error_message)
        """
        if not response:
            return False, "Empty response"
    
        if not response.startswith('^D'):
            return False, f"Invalid response format: {response[:10]}... (does not start with ^D)"
    
        # Extract the length field (3 digits after ^D)
        match = re.search(r'^\^D(\d{3})', response)
        if not match:
            return False, f"Invalid response format: {response[:10]}... (missing length field)"
    
        try:
        # Get the declared length from the response
            declared_length = int(match.group(1))
    
            # Calculate the expected total length
            # Total response length = 2(^D) + 3(length) + declared_length
            # The declared length already includes CRC and ending char
            expected_total_length = 5 + declared_length
    
            # Check if the actual response length matches the expected length
            actual_length = len(response)  # Don't strip CR/LF as they're part of the length
        
            # Allow a small margin of error (±2 characters) to account for possible CR/LF variations
            if abs(actual_length - expected_total_length) > 2:
                return False, f"Length mismatch: declared={declared_length}, expected_total={expected_total_length}, actual={actual_length}"
        
            # Check if response ends with \r
            if not response.endswith('\r'):
                # This is a warning, not a fatal error
                self.error_log.append({
                    'time': datetime.now().isoformat(),
                    'code': 'W-PROTO',
                    'error': f"Response should end with carriage return (\\r)"
                })
        
            return True, None
        
        except Exception as e:
            return False, f"Validation error: {str(e)}"

    def safe_extract_payload(self, response):
        """
        Safely extract the payload from a P18 protocol response

        Args:
            response (str): The response string from the inverter
    
        Returns:
            str or None: The payload if valid, None if invalid
        """
        # For debugging
        self.error_log.append({
            'time': datetime.now().isoformat(),
            'code': 'DEBUG',
            'error': f"Processing response: {response}"
        })
    
        is_valid, error = self.validate_p18_response(response)
        if not is_valid:
            self.error_log.append({
                'time': datetime.now().isoformat(),
                'code': 'E-PROTO',
                'error': f"Protocol error: {error}"
            })
            # Continue anyway, try to extract what we can
    
        try:
            # Extract the length field (3 digits after ^D)
            match = re.search(r'^\^D(\d{3})', response)
            if not match:
                return None
        
            # The payload starts after ^D and the 3-digit length
            payload_start = 5  # ^D + 3 digits = 5 characters
        
            # Try to find the end of the payload by looking for CRC characters
            # CRC is typically 2 bytes before the ending \r
            if response.endswith('\r'):
                payload_end = len(response) - 3  # -3 for CRC(2) + CR(1)
            else:
                # If no CR, assume CRC is the last 2 characters
                payload_end = len(response) - 2
        
            # Ensure we don't have negative length
            if payload_end <= payload_start:
                payload_end = len(response)
        
            payload = response[payload_start:payload_end]
        
            # For debugging
            self.error_log.append({
                'time': datetime.now().isoformat(),
                'code': 'DEBUG',
                'error': f"Extracted payload: {payload}"
            })
        
            return payload
    
        except Exception as e:
            self.error_log.append({
                'time': datetime.now().isoformat(),
                'code': 'E-EXTRACT',
                'error': f"Payload extraction error: {str(e)}"
            })
        
            # Try a simpler approach as fallback
            try:
                # Just extract everything between ^DXXX and the last 3 characters
                if len(response) > 8:  # Minimum length for a valid response
                    simple_payload = response[5:-3]
                    return simple_payload
            except:
                pass
        
            return None
        
    def parse_protocol_id(self, response):
        """Parse protocol ID from response"""
        try:
            payload = self.safe_extract_payload(response)
            if payload:
                return payload
                
            # Fallback to old method if safe_extract_payload fails
            if response and response.startswith('^D'):
                # From the screenshot, the response format is ^D00518<CRC><cr>
                # Extract the numeric part after ^D
                match = re.search(r'\^D(\d+)', response)
                if match:
                    protocol_id = match.group(1)
                    # Remove the length part (first 3 digits) if present
                    if len(protocol_id) > 3:
                        protocol_id = protocol_id[3:]
                    return protocol_id
            return None
        except Exception as e:
            self.error_log.append({
                'time': datetime.now().isoformat(),
                'code': 'E-PARSE',
                'error': f"Protocol ID parse error: {str(e)}"
            })
            return None
        
    def parse_general_status(self, response):
        """Parse GS command response"""
        try:
            payload = self.safe_extract_payload(response)
            if not payload:
                return None
                
            fields = payload.split(',')
            
            if len(fields) < 28:
                self.error_log.append({
                    'time': datetime.now().isoformat(),
                    'code': 'E-PARSE',
                    'error': f"General status parse error: insufficient fields ({len(fields)})"
                })
                return None
            
            return {
                'ac_out_voltage': f"{float(fields[2])/10:.1f}",
                'ac_out_frequency': f"{float(fields[3])/10:.1f}",
                'ac_active_power': fields[5],
                'load_percent': fields[6],
                'battery_voltage': f"{float(fields[7])/10:.1f}",
                'battery_charge_current': fields[11],
                'battery_discharge_current': fields[10],
                'battery_capacity': fields[12],
                'pv1_power': fields[16],
                'pv2_power': fields[17],
                'pv1_voltage': f"{float(fields[18])/10:.1f}",
                'pv2_voltage': f"{float(fields[19])/10:.1f}",
                'mppt1_status': self.mppt_status.get(fields[21], 'Unknown'),
                'mppt2_status': self.mppt_status.get(fields[22], 'Unknown'),
            }
        except Exception as e:
            self.error_log.append({
                'time': datetime.now().isoformat(),
                'code': 'E-PARSE',
                'error': f"General status parse error: {str(e)}"
            })
            return None
        
    def parse_mode_response(self, response):
        """Parse MOD command response to extract working mode"""
        try:
            payload = self.safe_extract_payload(response)
            if payload and payload.startswith('MOD,'):
                mode_code = payload.split(',')[1]
                return self.working_modes.get(mode_code, 'Unknown')
                
            # Fallback to old method if safe_extract_payload fails or format is different
            # Check for the standard format first (^D005MOD,XX)
            if response and response.startswith('^D'):
                # Try to extract the mode code using regex
                mode_match = re.search(r'\^D\d+MOD,(\d+)', response)
                if mode_match:
                    mode_code = mode_match.group(1)
                    return self.working_modes.get(mode_code, 'Unknown')
                
                # If standard format fails, try the alternative format (^D0050XX)
                mode_match = re.search(r'\^D\d+(\d+)', response)
                if mode_match:
                    mode_code = mode_match.group(1)
                    return self.working_modes.get(mode_code, 'Unknown')
            
            # For the format ^D0050XY where XY is the mode code
            if response and response.startswith('^D005'):
                mode_code = response[6:7]  # Extract just one digit for the mode
                return self.working_modes.get(mode_code, 'Unknown')
            
            # For the format shown in screenshot (^D00503Y)
            if response and len(response) >= 8 and response.startswith('^D005'):
                mode_code = response[6:7]  # Extract just the digit at position 6
                return self.working_modes.get(mode_code, 'Unknown')
            
            return 'Unknown'
        except Exception as e:
            self.error_log.append({
                'time': datetime.now().isoformat(),
                'code': 'E-PARSE',
                'error': f"Mode parse error: {str(e)}"
            })
            return 'Unknown'
        
    def parse_serial_number(self, response):
        """Parse ID command response to extract serial number"""
        try:
            payload = self.safe_extract_payload(response)
            if payload:
                # If the payload contains the length and serial number directly
                if len(payload) >= 2 and payload[0:2].isdigit():
                    length = int(payload[0:2])
                    serial_number = payload[2:2+length]
                    
                    if serial_number and len(serial_number) == length:
                        return {
                            "serial_number": serial_number,
                            "serial_length": length
                        }
                
                # Fallback: try to use the entire payload as the serial number
                if payload:
                    return {
                        "serial_number": payload,
                        "serial_length": len(payload)
                    }
                    
            # Fallback to old method if safe_extract_payload fails
            if response and response.startswith('^D'):
                # Format from screenshot: ^D025149613221210129700000V
                # Where 14 is the length of the serial number
                # And 9613221210129 is the actual serial number
            
                if response.startswith('^D025'):
                    # Extract the length indicator (first 2 digits after ^D025)
                    length_str = response[5:7]
                
                    # If length is valid, extract that many characters as the serial number
                    if length_str.isdigit():
                        length = int(length_str)
                        serial_number = response[7:7+length]
                    
                        if serial_number and len(serial_number) == length:
                            return {
                                "serial_number": serial_number,
                                "serial_length": length
                            }
                
                    # Fallback: try to extract a fixed 14 characters as seen in your example
                    serial_number = response[7:21]  # Extract 14 characters after the length indicator
                    if serial_number:
                        return {
                            "serial_number": serial_number,
                            "serial_length": len(serial_number)
                        }
            return None
        except Exception as e:
            self.error_log.append({
                'time': datetime.now().isoformat(),
                'code': 'E-PARSE',
                'error': f"Serial number parse error: {str(e)}"
            })
            return None
        
    def parse_firmware_version(self, response):
        """Parse VFW command response to extract firmware versions"""
        try:
            payload = self.safe_extract_payload(response)
            if payload:
                versions = payload.split(',')
                
                if len(versions) >= 3:
                    return {
                        "main_cpu_version": versions[0],
                        "slave1_cpu_version": versions[1],
                        "slave2_cpu_version": versions[2]
                    }
                    
            # Fallback to old method if safe_extract_payload fails
            if response and response.startswith('^D'):
                # Extract the firmware versions
                payload = response[5:-3]  # Remove header and CRC
                versions = payload.split(',')
                
                if len(versions) >= 3:
                    return {
                        "main_cpu_version": versions[0],
                        "slave1_cpu_version": versions[1],
                        "slave2_cpu_version": versions[2]
                    }
            return None
        except Exception as e:
            self.error_log.append({
                'time': datetime.now().isoformat(),
                'code': 'E-PARSE',
                'error': f"Firmware version parse error: {str(e)}"
            })
            return None
        

    def get_rated_info(self):
        """Get rated information using PIRI command"""
        try:
            response, error = self.send_p18_command("PIRI")
            if error:
                return None, error
        
            if not response:
                return None, "No response from inverter"
        
            # Parse the PIRI response
            parsed_data = self.parse_rated_info(response)
            if parsed_data is None:
                return None, "Failed to parse PIRI response"
        
            # Cache the result
            self.last_values['rated_info'] = {
                'data': parsed_data,
                'timestamp': datetime.now().isoformat()
            }
        
            return parsed_data, None
        
        except Exception as e:
            error_msg = f"Error getting rated information: {str(e)}"
            self.error_log.append({
                'time': datetime.now().isoformat(),
                'code': 'E-PIRI',
                'error': error_msg
            })
            return None, error_msg

    def parse_rated_info(self, response):
        """Parse rated information from PIRI response"""
        try:
            # Log the raw response for debugging
            self.error_log.append({
                'time': datetime.now().isoformat(),
                'code': 'DEBUG-PIRI',
                'error': f"Raw PIRI response: {response}"
            })
        
            # First, try to extract the payload using the safe method
            payload = self.safe_extract_payload(response)
        
            # If that fails, try a more direct approach
            if payload is None:
                # Extract everything after ^DXXX where XXX is the length
                match = re.search(r'\^D\d{3}(.*?)(?:<|$)', response)
                if match:
                    payload = match.group(1)
                else:
                    self.error_log.append({
                        'time': datetime.now().isoformat(),
                        'code': 'E-PIRI-FORMAT',
                        'error': f"Could not extract PIRI payload from response: {response}"
                    })
                    return None
        
            # Try to split by commas first (as seen in your debug output)
            if ',' in payload:
                values = payload.split(',')
                self.error_log.append({
                    'time': datetime.now().isoformat(),
                    'code': 'DEBUG-PIRI',
                    'error': f"Using comma-separated format, found {len(values)} values"
                })
            else:
                # If no commas, fall back to space separation
                values = payload.split()
                self.error_log.append({
                    'time': datetime.now().isoformat(),
                    'code': 'DEBUG-PIRI',
                    'error': f"Using space-separated format, found {len(values)} values"
                })
        
            # Parse all the values with proper error handling
            try:
                # Create a default structure
                parsed_data = {
                    "ac_input": {
                        "voltage": 230.0,
                        "current": 30.0
                    },
                    "ac_output": {
                        "voltage": 230.0,
                        "frequency": 50.0,
                        "current": 30.0,
                        "apparent_power": 6000,
                        "active_power": 6000
                    },
                    "battery": {
                        "voltage": 48.0,
                        "recharge_voltage": 46.0,
                        "redischarge_voltage": 54.0,
                        "under_voltage": 42.0,
                        "bulk_voltage": 56.4,
                        "float_voltage": 54.0,
                        "type": "Unknown"
                    },
                    "charging": {
                        "max_ac_current": 60,
                        "max_total_current": 80
                    },
                    "system": {
                        "input_voltage_range": "Appliance",
                        "output_priority": "Solar-Utility-Battery",
                        "charger_priority": "Solar first",
                        "parallel_max": 9,
                        "machine_type": "Hybrid"
                    },
                    "raw_response": payload,
                    "total_values": len(values)
                }
            
                # Fill in values that we have with proper decimal point handling
                try:
                    # AC input values with decimal point
                    if len(values) > 0: parsed_data["ac_input"]["voltage"] = float(values[0]) / 10
                    if len(values) > 1: parsed_data["ac_input"]["current"] = float(values[1]) / 10
                
                    # AC output values with decimal point
                    if len(values) > 2: parsed_data["ac_output"]["voltage"] = float(values[2]) / 10
                    if len(values) > 3: parsed_data["ac_output"]["frequency"] = float(values[3]) / 10
                    if len(values) > 4: parsed_data["ac_output"]["current"] = float(values[4]) / 10
                    if len(values) > 5: parsed_data["ac_output"]["apparent_power"] = int(float(values[5]))
                    if len(values) > 6: parsed_data["ac_output"]["active_power"] = int(float(values[6]))
                
                    # Battery values with decimal point
                    if len(values) > 7: parsed_data["battery"]["voltage"] = float(values[7]) / 10
                    if len(values) > 8: parsed_data["battery"]["recharge_voltage"] = float(values[8]) / 10
                    if len(values) > 9: parsed_data["battery"]["redischarge_voltage"] = float(values[9]) / 10
                    if len(values) > 10: parsed_data["battery"]["under_voltage"] = float(values[10]) / 10
                    if len(values) > 11: parsed_data["battery"]["bulk_voltage"] = float(values[11]) / 10
                    if len(values) > 12: parsed_data["battery"]["float_voltage"] = float(values[12]) / 10
                
                    # Other values without decimal point
                    if len(values) > 13: parsed_data["battery"]["type"] = self.battery_types.get(values[13], f"Unknown ({values[13]})")
                    if len(values) > 14: parsed_data["charging"]["max_ac_current"] = int(float(values[14]))
                    if len(values) > 15: parsed_data["charging"]["max_total_current"] = int(float(values[15]))
                    if len(values) > 16: parsed_data["system"]["input_voltage_range"] = self.input_voltage_ranges.get(values[16], f"Unknown ({values[16]})")
                    if len(values) > 17: parsed_data["system"]["output_priority"] = self.output_priorities.get(values[17], f"Unknown ({values[17]})")
                    if len(values) > 18: parsed_data["system"]["charger_priority"] = self.charger_priorities.get(values[18], f"Unknown ({values[18]})")
                    if len(values) > 19: parsed_data["system"]["parallel_max"] = int(float(values[19]))
                    if len(values) > 20: parsed_data["system"]["machine_type"] = self.machine_types.get(values[20], f"Unknown ({values[20]})")
                
                    # Add optional fields if they exist
                    if len(values) > 21:
                        parsed_data["system"]["topology"] = self.topologies.get(values[21], f"Unknown ({values[21]})")
                
                    if len(values) > 22:
                        parsed_data["system"]["output_mode"] = self.output_modes.get(values[22], f"Unknown ({values[22]})")
                
                    if len(values) > 23:
                        parsed_data["system"]["solar_power_priority"] = self.solar_power_priorities.get(values[23], f"Unknown ({values[23]})")
                
                    if len(values) > 24:
                        parsed_data["system"]["mppt_strings"] = int(float(values[24]))
                
                    return parsed_data
                
                except (ValueError, IndexError) as e:
                    self.error_log.append({
                        'time': datetime.now().isoformat(),
                        'code': 'E-PIRI-VALUE',
                        'error': f"Error parsing specific PIRI value: {str(e)}, continuing with partial data"
                    })
                    # Return what we have even if some values couldn't be parsed
                    return parsed_data
            
            except Exception as e:
                self.error_log.append({
                    'time': datetime.now().isoformat(),
                    'code': 'E-PIRI-PARSE',
                    'error': f"Error parsing PIRI values: {str(e)}, Raw payload: {payload}"
                })
                return None
        
        except Exception as e:
            self.error_log.append({
                'time': datetime.now().isoformat(),
                'code': 'E-PIRI-GENERAL',
                'error': f"General PIRI parse error: {str(e)}"
            })
            return None
            
    def get_machine_model(self):
        """Query the inverter for machine model information"""
        result, error = self.send_p18_command('GMN')
        if result:
            model_info = self.parse_machine_model(result)
            if model_info:
                return model_info
        return {'error': error or 'Unknown error', 'timestamp': datetime.now().isoformat()}

    def parse_machine_model(self, response):
        """Parse GMN command response to extract machine model information"""
        try:
            payload = self.safe_extract_payload(response)
            if payload and len(payload) >= 2:
                model_code = payload[:2]  # Extract the 2-character model code
                
                # Define model mapping based on the image provided
                model_mapping = {
                    "00": "INFINISOLAR V",
                    "01": "INFINISOAR V LV",
                    "02": "INFINISOLAR V II",
                    "03": "INFINISOLAR V II 15KW(3 phase)",
                    "04": "INFINISOLAR V III",
                    "05": "INFINISOLAR V II LV",
                    "06": "INFINISOLAR V II WP",
                    "07": "EASUN IGRID SV IV",
                    "08": "INFINISOLAR V II TWIN",
                    "09": "INFINISOLAR V III TWIN",
                    "11": "INFINISOLAR V II WP TWIN",
                    "12": "INFINISOLAR V IV TWIN"
                }
                
                model_name = model_mapping.get(model_code, "Unknown model")
                
                return {
                    "model_code": model_code,
                    "model_name": model_name,
                    "timestamp": datetime.now().isoformat()
                }
                
            # Fallback to old method if safe_extract_payload fails
            if response and response.startswith('^D'):
                # Format from image: ^D005AA<CRC><cr>
                # Where AA is the model code
                if len(response) >= 7:
                    model_code = response[5:7]  # Extract the 2-character model code
                    
                    # Define model mapping based on the image provided
                    model_mapping = {
                        "00": "INFINISOLAR V",
                        "01": "INFINISOAR V LV",
                        "02": "INFINISOLAR V II",
                        "03": "INFINISOLAR V II 15KW(3 phase)",
                        "04": "INFINISOLAR V III",
                        "05": "INFINISOLAR V II LV",
                        "06": "INFINISOLAR V II WP",
                        "07": "EASUN IGRID SV IV",
                        "08": "INFINISOLAR V II TWIN",
                        "09": "INFINISOLAR V III TWIN",
                        "11": "INFINISOLAR V II WP TWIN",
                        "12": "INFINISOLAR V IV TWIN"
                    }
                    
                    model_name = model_mapping.get(model_code, "Unknown model")
                    
                    return {
                        "model_code": model_code,
                        "model_name": model_name,
                        "timestamp": datetime.now().isoformat()
                    }
            return None
        except Exception as e:
            self.error_log.append({
                'time': datetime.now().isoformat(),
                'code': 'E-PARSE',
                'error': f"Machine model parse error: {str(e)}"
            })
            return None
            
    def get_current_time(self):
        """Query the inverter for current time"""
        result, error = self.send_p18_command('T')
        if result:
            time_data = self.parse_time_response(result)
            if time_data:
                return time_data
        return {'error': error or 'Unknown error', 'timestamp': datetime.now().isoformat()}
        
    def parse_time_response(self, response):
        """Parse T command response to extract current time
        
        Format: ^D017YYYYMMDDHHMMSS<CRC><cr>
        Example: ^D01720160214201314<CRC><cr> means 2016-02-14 20:13:14
        """
        try:
            payload = self.safe_extract_payload(response)
            if payload and len(payload) >= 14:
                year = payload[0:4]
                month = payload[4:6]
                day = payload[6:8]
                hour = payload[8:10]
                minute = payload[10:12]
                second = payload[12:14]
                
                # Format as ISO datetime string
                datetime_str = f"{year}-{month}-{day}T{hour}:{minute}:{second}"
                
                return {
                    "datetime": datetime_str,
                    "year": int(year),
                    "month": int(month),
                    "day": int(day),
                    "hour": int(hour),
                    "minute": int(minute),
                    "second": int(second),
                    "timestamp": datetime.now().isoformat()
                }
                
            # Fallback to old method if safe_extract_payload fails
            if response and response.startswith('^D'):
                # Extract the time string (YYYYMMDDHHMMSS)
                # The response should be like ^D017YYYYMMDDHHMMSS<CRC><cr>
                match = re.search(r'\^D\d{3}(\d{4})(\d{2})(\d{2})(\d{2})(\d{2})(\d{2})', response)
                if match:
                    year = match.group(1)
                    month = match.group(2)
                    day = match.group(3)
                    hour = match.group(4)
                    minute = match.group(5)
                    second = match.group(6)
                    
                    # Format as ISO datetime string
                    datetime_str = f"{year}-{month}-{day}T{hour}:{minute}:{second}"
                    
                    return {
                        "datetime": datetime_str,
                        "year": int(year),
                        "month": int(month),
                        "day": int(day),
                        "hour": int(hour),
                        "minute": int(minute),
                        "second": int(second),
                        "timestamp": datetime.now().isoformat()
                    }
            return None
        except Exception as e:
            self.error_log.append({
                'time': datetime.now().isoformat(),
                'code': 'E-PARSE',
                'error': f"Time parse error: {str(e)}"
            })
            return None
            
    def set_time(self, dt):
        """Set the inverter time
        
        Args:
            dt (datetime): The datetime object to set
            
        Returns:
            dict: Result of the operation
        """
        try:
            # Format time string for command (yymmddhhmmss)
            time_str = dt.strftime("%y%m%d%H%M%S")
            
            # The set time command needs special handling because it starts with S not P
            cmd = f"^S018DAT{time_str}\r"
            
            # Send directly without using send_p18_command since this is an S command not P command
            if not self.ser or not self.ser.is_open:
                if not self.connect():
                    return {'error': 'Could not connect to inverter', 'timestamp': datetime.now().isoformat()}
            
            with self.lock:
                try:
                    self.ser.reset_input_buffer()
                    self.ser.reset_output_buffer()
                    self.ser.write(cmd.encode('ascii'))
                    self.ser.flush()
                    
                    # Read response
                    response = ""
                    while True:
                        char = self.ser.read(1)
                        if not char:
                            break
                        response += char.decode('ascii', errors='ignore')
                        if response.endswith('\r'):
                            break
                        if len(response) > 100:
                            break
                    
                    if response:
                        if response.startswith('^1'):
                            return {
                                "status": "success",
                                "datetime": dt.isoformat(),
                                "timestamp": datetime.now().isoformat()
                            }
                        else:
                            return {'error': f'Command refused: {response}', 'timestamp': datetime.now().isoformat()}
                    return {'error': 'No response from inverter', 'timestamp': datetime.now().isoformat()}
                except Exception as e:
                    self.error_log.append({
                        'time': datetime.now().isoformat(),
                        'code': 'E-TIME',
                        'error': f"Time setting error: {str(e)}"
                    })
                    return {'error': str(e), 'timestamp': datetime.now().isoformat()}
        except Exception as e:
            self.error_log.append({
                'time': datetime.now().isoformat(),
                'code': 'E-TIME',
                'error': f"Time setting error: {str(e)}"
            })
            return {'error': str(e), 'timestamp': datetime.now().isoformat()}
            
    def get_ac_charge_schedule(self):
        """Get AC charge time bucket"""
        result, error = self.send_p18_command('ACCT')
        if result:
            schedule_data = self.parse_schedule_response(result)
            if schedule_data:
                return schedule_data
        return {
            "start_time": "00:00",
            "end_time": "23:59",
            "enabled": True,
            "timestamp": datetime.now().isoformat()
        }
        
    def get_ac_load_schedule(self):
        """Get AC load time bucket"""
        result, error = self.send_p18_command('ACLT')
        if result:
            schedule_data = self.parse_schedule_response(result)
            if schedule_data:
                return schedule_data
        return {
            "start_time": "00:00",
            "end_time": "23:59",
            "enabled": True,
            "timestamp": datetime.now().isoformat()
        }
        
    def parse_schedule_response(self, response):
        """Parse schedule response (ACCT or ACLT)
        
        Format: ^D008HHMMHHMME<CRC><cr>
        Where:
        - First HHMM is start time
        - Second HHMM is end time
        - E is enabled flag (1=enabled, 0=disabled)
        """
        try:
            payload = self.safe_extract_payload(response)
            if payload and len(payload) >= 9:
                start_hour = payload[0:2]
                start_minute = payload[2:4]
                end_hour = payload[4:6]
                end_minute = payload[6:8]
                enabled = payload[8] == '1'
                
                return {
                    "start_time": f"{start_hour}:{start_minute}",
                    "end_time": f"{end_hour}:{end_minute}",
                    "enabled": enabled,
                    "timestamp": datetime.now().isoformat()
                }
                
            # Fallback to old method if safe_extract_payload fails
            if response and response.startswith('^D'):
                # Extract the schedule data
                match = re.search(r'\^D\d{3}(\d{2})(\d{2})(\d{2})(\d{2})(\d)', response)
                if match:
                    start_hour = match.group(1)
                    start_minute = match.group(2)
                    end_hour = match.group(3)
                    end_minute = match.group(4)
                    enabled = match.group(5) == '1'
                    
                    return {
                        "start_time": f"{start_hour}:{start_minute}",
                        "end_time": f"{end_hour}:{end_minute}",
                        "enabled": enabled,
                        "timestamp": datetime.now().isoformat()
                    }
            return None
        except Exception as e:
            self.error_log.append({
                'time': datetime.now().isoformat(),
                'code': 'E-PARSE',
                'error': f"Schedule parse error: {str(e)}"
            })
            return None
        
    def get_status(self):
        """Get current inverter status"""
        # Get working mode
        mode_result, mode_error = self.send_p18_command('MOD')
        if mode_result:
            working_mode = self.parse_mode_response(mode_result)
        else:
            working_mode = 'Unknown'

        # Get general status
        result, error = self.send_p18_command('GS')
        if result:
            # Parse the status response
            status_data = self.parse_general_status(result)
            if status_data:
                status_data['working_mode'] = working_mode
                status_data['timestamp'] = datetime.now().isoformat()
                self.last_values.update(status_data)
                return status_data
        return {'error': error or 'Unknown error', 'timestamp': datetime.now().isoformat()}
        
    def get_power_data(self):
        """Get power generation data"""
        result, error = self.send_p18_command('GS')
        if result:
            # Parse the power data from response
            status_data = self.parse_general_status(result)
            if status_data:
                power_data = {
                    'current_power': float(status_data.get('pv1_power', 0)) + float(status_data.get('pv2_power', 0)),
                    'pv1_power': status_data.get('pv1_power', 0),
                    'pv2_power': status_data.get('pv2_power', 0),
                    'pv1_voltage': status_data.get('pv1_voltage', 0),
                    'pv2_voltage': status_data.get('pv2_voltage', 0),
                    'daily_yield': 0,  # Need to calculate from historical data
                    'total_yield': 0,  # Need separate command for this
                    'timestamp': datetime.now().isoformat()
                }
                self.last_values.update(power_data)
                return power_data
        return {'error': error or 'Unknown error', 'timestamp': datetime.now().isoformat()}
        
    def get_error_logs(self):
        """Get error logs from the inverter"""
        return {
            'errors': self.error_log,
            'count': len(self.error_log),
            'last_error_time': self.error_log[-1]['time'] if self.error_log else None
        }
        
    def scan_serial_ports(self):
        """Scan for available USB serial ports"""
        if os.name == 'nt':  # Windows
            ports = []
            for i in range(256):
                try:
                    port = f'COM{i}'
                    s = serial.Serial(port)
                    s.close()
                    ports.append(port)
                except (OSError, serial.SerialException):
                    pass
            return ports
        else:  # Linux/Unix
            return glob.glob('/dev/ttyUSB*') + glob.glob('/dev/ttyACM*')
    
    def update_data(self):
        """Update inverter data"""
        # Get working mode
        result, _ = self.send_p18_command('MOD')
        if result:
            working_mode = self.parse_mode_response(result)
        else:
            working_mode = 'Unknown'

        # Get general status
        result, _ = self.send_p18_command('GS')
        if result:
            data = self.parse_general_status(result)
            if data:
                data['working_mode'] = working_mode
                data['last_update'] = datetime.now().isoformat()
                with self.lock:
                    self.last_values.update(data)
                return True
        return False