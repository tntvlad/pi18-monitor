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
        
    def connect(self):
        """Establish connection to the inverter"""
        try:
            if self.ser:
                self.ser.close()
            self.ser = serial.Serial(port=self.port, **self.serial_config)
            self.connected = True
            return True
        except Exception as e:
            self.error_log.append({
                'time': datetime.now().isoformat(),
                'code': 'E-CONN',
                'error': f"Connection error: {str(e)}"
            })
            self.connected = False
            return False
            
    def disconnect(self):
        """Close the serial connection"""
        if self.ser and self.ser.is_open:
            self.ser.close()
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
        """Send command to P18 inverter and get response"""
        if not self.connected:
            if not self.connect():
                return None, "Not connected to inverter"
                
        with self.lock:
            try:
                # Format and send command
                frame = self.build_p18_command(command)
                self.ser.reset_input_buffer()
                self.ser.reset_output_buffer()
                
                start_time = time.time()
                self.ser.write(frame)
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
                    if len(response) > 1000:
                        break
                
                if not response:
                    return None, "No response from inverter"
                    
                return response.strip(), None
                
            except Exception as e:
                self.error_log.append({
                    'time': datetime.now().isoformat(),
                    'code': 'E-CMD',
                    'error': f"Command error: {str(e)}"
                })
                return None, str(e)
                
    def parse_protocol_id(self, response):
        """Parse protocol ID from response"""
        try:
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
            if not response or not response.startswith('^D'):
                return None
            
            payload = response[5:-3]  # Remove header and CRC
            fields = payload.split(',')
            
            if len(fields) < 28:
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
        
    def parse_rated_info(self, response):
        """Parse PIRI command response to extract rated information"""
        try:
            if not response or not response.startswith('^D'):
                return None
        
            payload = response[5:-3]  # Remove header and CRC
            fields = payload.split(',')
        
            if len(fields) < 21:
                return None
        
            # Based on the screenshots, many values need to be divided by 10
            # to get the correct decimal representation
            return {
                "ac_input": {
                    "voltage": float(fields[0])/10,  # Unit: 0.1V
                    "current": float(fields[1])/10   # Unit: 0.1A
                },
                "ac_output": {
                    "voltage": float(fields[2])/10,  # Unit: 0.1V
                    "frequency": float(fields[3])/10,  # Unit: 0.1Hz
                    "current": float(fields[4])/10,  # Unit: 0.1A
                    "apparent_power": int(fields[5]),  # Unit: VA
                    "active_power": int(fields[6])   # Unit: W
                },
                "battery": {
                    "voltage": float(fields[7])/10,  # Unit: 0.1V
                    "recharge_voltage": float(fields[8])/10,  # Unit: 0.1V
                    "redischarge_voltage": float(fields[9])/10,  # Unit: 0.1V
                    "under_voltage": float(fields[10])/10,  # Unit: 0.1V
                    "bulk_voltage": float(fields[11])/10,  # Unit: 0.1V
                    "float_voltage": float(fields[12])/10,  # Unit: 0.1V
                    "type": self.battery_types.get(fields[13], "Unknown")
                },
                "charging": {
                    "max_ac_current": int(fields[14]),  # Unit: A
                    "max_total_current": int(fields[15])  # Unit: A
                },
                "system": {
                    "input_voltage_range": self.input_voltage_ranges.get(fields[16], "Unknown"),
                    "output_priority": self.output_priorities.get(fields[17], "Unknown"),
                    "charger_priority": self.charger_priorities.get(fields[18], "Unknown"),
                    "parallel_max": int(fields[19]),
                    "machine_type": self.machine_types.get(fields[20], "Unknown"),
                    "topology": self.topologies.get(fields[21], "Unknown") if len(fields) > 21 else "Unknown",
                    "output_mode": self.output_modes.get(fields[22], "Unknown") if len(fields) > 22 else "Unknown",
                    "solar_power_priority": self.solar_power_priorities.get(fields[23], "Unknown") if len(fields) > 23 else "Unknown",
                    "mppt_strings": int(fields[24]) if len(fields) > 24 and fields[24].isdigit() else 1
                }
            }
        except Exception as e:
            self.error_log.append({
                'time': datetime.now().isoformat(),
                'code': 'E-PARSE',
                'error': f"Rated info parse error: {str(e)}"
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