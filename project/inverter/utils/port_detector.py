# inverter/utils/port_detector.py
"""Utility to detect and map inverters to serial ports"""
import serial
import time
import re
import os
import glob
import json
from datetime import datetime

class InverterPortDetector:
    """Class to detect and manage inverter-to-port mappings"""
    
    def __init__(self, config_file="inverter_ports.json"):
        """Initialize the detector with configuration file path"""
        self.config_file = config_file
        self.port_mappings = self._load_mappings()
        self.serial_config = {
            'baudrate': 2400,
            'bytesize': serial.EIGHTBITS,
            'parity': serial.PARITY_NONE,
            'stopbits': serial.STOPBITS_ONE,
            'timeout': 2,
            'write_timeout': 2
        }
    
    def _load_mappings(self):
        """Load saved port mappings from file"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}
    
    def save_mapping(self, port, inverter_info):
        """Save port to inverter mapping"""
        self.port_mappings[port] = inverter_info
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.port_mappings, f, indent=4)
            return True
        except Exception:
            return False
    
    def get_port_for_serial(self, serial_number):
        """Get the saved port for a specific inverter serial number"""
        for port, info in self.port_mappings.items():
            if info.get('serial_number') == serial_number:
                return port
        return None
    
    def scan_available_ports(self):
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
    
    def test_port_connection(self, port):
        """Test if an inverter is connected to the specified port"""
        try:
            ser = serial.Serial(port=port, **self.serial_config)
            try:
                # Send Protocol ID command
                frame = self.build_p18_command('PI')
                ser.reset_input_buffer()
                ser.reset_output_buffer()
                ser.write(frame)
                ser.flush()
                
                # Read response
                response = ""
                start_time = time.time()
                while (time.time() - start_time) < self.serial_config['timeout']:
                    char = ser.read(1)
                    if not char:
                        if response:  # If we have some response but hit a timeout
                            break
                        continue
                    response += char.decode('ascii', errors='ignore')
                    if response.endswith('\r'):
                        break
                    if len(response) > 100:
                        break
                
                # Check if we got a valid protocol ID response
                if response and response.startswith('^D'):
                    protocol_id = self.parse_protocol_id(response)
                    
                    # Try to get serial number
                    frame = self.build_p18_command('ID')
                    ser.reset_input_buffer()
                    ser.reset_output_buffer()
                    ser.write(frame)
                    ser.flush()
                    
                    id_response = ""
                    start_time = time.time()
                    while (time.time() - start_time) < self.serial_config['timeout']:
                        char = ser.read(1)
                        if not char:
                            if id_response:
                                break
                            continue
                        id_response += char.decode('ascii', errors='ignore')
                        if id_response.endswith('\r'):
                            break
                        if len(id_response) > 100:
                            break
                    
                    serial_number = None
                    if id_response and id_response.startswith('^D'):
                        serial_data = self.parse_serial_number(id_response)
                        if serial_data:
                            serial_number = serial_data.get('serial_number')
                    
                    # Try to get firmware version
                    frame = self.build_p18_command('VFW')
                    ser.reset_input_buffer()
                    ser.reset_output_buffer()
                    ser.write(frame)
                    ser.flush()
                    
                    fw_response = ""
                    start_time = time.time()
                    while (time.time() - start_time) < self.serial_config['timeout']:
                        char = ser.read(1)
                        if not char:
                            if fw_response:
                                break
                            continue
                        fw_response += char.decode('ascii', errors='ignore')
                        if fw_response.endswith('\r'):
                            break
                        if len(fw_response) > 100:
                            break
                    
                    firmware_version = "Unknown"
                    if fw_response and fw_response.startswith('^D'):
                        if ',' in fw_response:
                            firmware_version = fw_response.split(',')[0].replace('^D', '').strip()
                    
                    return {
                        "connected": True,
                        "protocol_id": protocol_id,
                        "serial_number": serial_number,
                        "firmware_version": firmware_version,
                        "last_detected": datetime.now().isoformat()
                    }
                return {"connected": False}
            finally:
                ser.close()
        except Exception as e:
            return {"connected": False, "error": str(e)}
    
    def parse_protocol_id(self, response):
        """Parse protocol ID from response"""
        try:
            if response and response.startswith('^D'):
                match = re.search(r'\^D(\d+)', response)
                if match:
                    protocol_id = match.group(1)
                    if len(protocol_id) > 3:
                        protocol_id = protocol_id[3:]
                    return protocol_id
            return None
        except Exception:
            return None
    
    def parse_serial_number(self, response):
        """Parse ID command response to extract serial number"""
        try:
            if response and response.startswith('^D'):
                if response.startswith('^D025'):
                    length_str = response[5:7]
                
                    if length_str.isdigit():
                        length = int(length_str)
                        serial_number = response[7:7+length]
                    
                        if serial_number and len(serial_number) == length:
                            return {
                                "serial_number": serial_number,
                                "serial_length": length
                            }
                
                    # Fallback: try to extract a fixed 14 characters
                    serial_number = response[7:21]
                    if serial_number:
                        return {
                            "serial_number": serial_number,
                            "serial_length": len(serial_number)
                        }
            return None
        except Exception:
            return None
    
    def detect_inverters(self):
        """Scan all available ports and detect inverters"""
        ports = self.scan_available_ports()
        results = {}
        
        for port in ports:
            result = self.test_port_connection(port)
            if result.get("connected"):
                results[port] = result
        
        return results
    
    def get_preferred_port(self, serial_number=None):
        """
        Get the preferred port for a specific inverter or any inverter
        
        If serial_number is provided, tries to find that specific inverter.
        Otherwise, returns the first available port with an inverter.
        """
        # First check if we have a saved mapping for this serial number
        if serial_number and serial_number in self.port_mappings:
            saved_port = self.get_port_for_serial(serial_number)
            if saved_port:
                # Verify the inverter is still connected to this port
                result = self.test_port_connection(saved_port)
                if result.get("connected") and result.get("serial_number") == serial_number:
                    return saved_port
        
        # If no saved mapping or the saved port is no longer valid,
        # scan for available inverters
        inverters = self.detect_inverters()
        
        if serial_number:
            # Look for the specific inverter
            for port, info in inverters.items():
                if info.get("serial_number") == serial_number:
                    # Save this mapping for future use
                    self.save_mapping(port, info)
                    return port
        elif inverters:
            # Return the first available inverter port
            port = next(iter(inverters))
            self.save_mapping(port, inverters[port])
            return port
        
        return None