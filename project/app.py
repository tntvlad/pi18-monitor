# Main Flask application
from flask import Flask, render_template, jsonify, request, redirect, url_for, flash
from flask_cors import CORS
import os
import json
import serial.tools.list_ports
from project.inverter.monitor import P18InverterMonitor
from project.inverter.api.routes import api_bp
from project.inverter.utils.port_detector import InverterPortDetector

def create_app(config=None):
    """Create and configure the Flask application"""
    app = Flask(__name__)
    
    # Enable CORS
    CORS(app)
    
    # Set secret key for sessions and flash messages
    app.secret_key = os.environ.get('SECRET_KEY', 'p18-inverter-monitor-secret-key')
    
    # Default configuration
    app.config.update(
        DEBUG=True,
        INVERTER_PORT=os.environ.get('INVERTER_PORT', '/dev/ttyUSB0'),
        INVERTER_BAUDRATE=int(os.environ.get('INVERTER_BAUDRATE', 2400)),
        INVERTER_TIMEOUT=int(os.environ.get('INVERTER_TIMEOUT', 1)),
        DASHBOARD_REFRESH_INTERVAL=int(os.environ.get('DASHBOARD_REFRESH_INTERVAL', 30)),
        LOG_LEVEL=os.environ.get('LOG_LEVEL', 'INFO'),
        CONFIG_FILE=os.environ.get('CONFIG_FILE', 'config.json'),
        INVERTER_SERIAL=os.environ.get('INVERTER_SERIAL', None)
    )
    
    # Load configuration from file if exists
    if os.path.exists(app.config['CONFIG_FILE']):
        try:
            with open(app.config['CONFIG_FILE'], 'r') as f:
                file_config = json.load(f)
                app.config.update(file_config)
        except Exception as e:
            app.logger.error(f"Error loading config file: {e}")
    
    # Override with provided config
    if config:
        app.config.update(config)
    
    # Initialize port detector
    app.port_detector = InverterPortDetector()
    
    # If INVERTER_SERIAL is set, try to find the port for that specific inverter
    if app.config['INVERTER_SERIAL']:
        preferred_port = app.port_detector.get_preferred_port(app.config['INVERTER_SERIAL'])
        if preferred_port:
            app.config['INVERTER_PORT'] = preferred_port
    
    # Initialize inverter monitor
    app.monitor = P18InverterMonitor(port=app.config['INVERTER_PORT'])
    
    # Register blueprints
    app.register_blueprint(api_bp)
    
    @app.route('/')
    def index():
        """Render the main dashboard page"""
        return render_template('index.html')
    
    @app.route('/setup', methods=['GET', 'POST'])
    def setup():
        """Setup page for configuring the inverter connection"""
        success_message = None
        error_message = None
        
        if request.method == 'POST':
            try:
                # Get form data
                port = request.form.get('port')
                baudrate = int(request.form.get('baudrate', 2400))
                timeout = int(request.form.get('timeout', 1))
                refresh_interval = int(request.form.get('refresh_interval', 30))
                log_level = request.form.get('log_level', 'INFO')
                inverter_serial = request.form.get('inverter_serial')
                
                # Update configuration
                app.config.update(
                    INVERTER_PORT=port,
                    INVERTER_BAUDRATE=baudrate,
                    INVERTER_TIMEOUT=timeout,
                    DASHBOARD_REFRESH_INTERVAL=refresh_interval,
                    LOG_LEVEL=log_level,
                    INVERTER_SERIAL=inverter_serial
                )
                
                # Save configuration to file
                config_to_save = {
                    'INVERTER_PORT': port,
                    'INVERTER_BAUDRATE': baudrate,
                    'INVERTER_TIMEOUT': timeout,
                    'DASHBOARD_REFRESH_INTERVAL': refresh_interval,
                    'LOG_LEVEL': log_level,
                    'INVERTER_SERIAL': inverter_serial
                }
                
                with open(app.config['CONFIG_FILE'], 'w') as f:
                    json.dump(config_to_save, f, indent=4)
                
                # If inverter serial is provided, save the port mapping
                if inverter_serial and port:
                    # Test connection to get inverter info
                    test_monitor = P18InverterMonitor(port=port)
                    if test_monitor.connect():
                        # Get serial number and protocol ID
                        result, _ = test_monitor.send_p18_command('ID')
                        serial_data = None
                        if result:
                            serial_data = test_monitor.parse_serial_number(result)
                        
                        # Get protocol ID
                        result, _ = test_monitor.send_p18_command('PI')
                        protocol_id = None
                        if result:
                            protocol_id = test_monitor.parse_protocol_id(result)
                        
                        # Get firmware version
                        firmware_version = "Unknown"
                        result, _ = test_monitor.send_p18_command('VFW')
                        if result and ',' in result:
                            firmware_version = result.split(',')[0].replace('^D', '').strip()
                        
                        # Save mapping
                        app.port_detector.save_mapping(port, {
                            "connected": True,
                            "protocol_id": protocol_id,
                            "serial_number": inverter_serial,
                            "firmware_version": firmware_version
                        })
                        
                        test_monitor.disconnect()
                
                # Reinitialize the monitor with new settings
                if hasattr(app, 'monitor'):
                    app.monitor.disconnect()
                app.monitor = P18InverterMonitor(port=port)
                
                success_message = "Settings saved successfully!"
            except Exception as e:
                error_message = f"Error saving settings: {str(e)}"
        
        return render_template('setup.html', 
                              config=app.config, 
                              success_message=success_message,
                              error_message=error_message)
    
    # API endpoint to test connection
    @app.route('/api/v1/inverter/test-connection', methods=['POST'])
    def test_connection():
        """Test connection to the inverter"""
        try:
            data = request.get_json()
            port = data.get('port', app.config['INVERTER_PORT'])
            
            # Create a temporary monitor for testing
            test_monitor = P18InverterMonitor(port=port)
            if not test_monitor.connect():
                return jsonify({'success': False, 'error': 'Failed to connect to inverter'})
            
            # Try to get protocol ID
            protocol_result, error = test_monitor.send_p18_command('PI')
            protocol_id = None
            if protocol_result:
                protocol_id = test_monitor.parse_protocol_id(protocol_result)
            
            # Try to get serial number
            serial_number = None
            serial_result, error = test_monitor.send_p18_command('ID')
            if serial_result:
                serial_data = test_monitor.parse_serial_number(serial_result)
                if serial_data:
                    serial_number = serial_data.get('serial_number')
            
            # Try to get firmware version
            firmware_version = "Unknown"
            firmware_result, error = test_monitor.send_p18_command('VFW')
            if firmware_result and ',' in firmware_result:
                firmware_version = firmware_result.split(',')[0].replace('^D', '').strip()
            
            # Close the test connection
            test_monitor.disconnect()
            
            return jsonify({
                'success': True, 
                'protocol_id': protocol_id,
                'serial_number': serial_number,
                'firmware_version': firmware_version
            })
            
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)})
    
    # API endpoint to list available serial ports
    @app.route('/api/v1/system/ports')
    def list_ports():
        """List available serial ports"""
        try:
            ports = []
            for port in serial.tools.list_ports.comports():
                ports.append({
                    'device': port.device,
                    'description': port.description,
                    'hwid': port.hwid
                })
            return jsonify({'ports': ports})
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    # API endpoint to scan for inverters
    @app.route('/api/v1/system/scan-inverters')
    def scan_inverters():
        """Scan for inverters on available ports"""
        try:
            inverters = app.port_detector.detect_inverters()
            return jsonify({'inverters': inverters})
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.errorhandler(404)
    def page_not_found(e):
        """Handle 404 errors"""
        return jsonify({"error": "Endpoint not found"}), 404
    
    @app.errorhandler(500)
    def server_error(e):
        """Handle 500 errors"""
        return jsonify({"error": "Internal server error"}), 500
    
    return app

if __name__ == '__main__':
    app = create_app()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)