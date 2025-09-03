#!/bin/bash

# P18 Inverter API Installation Script
# This script installs and configures the P18 Inverter API application

echo "========================================================="
echo "P18 Inverter API Installation"
echo "========================================================="

# Check for Python 3.7+
echo "Checking Python version..."
if command -v python3 &>/dev/null; then
    PYTHON_VERSION=$(python3 --version | awk '{print $2}')
    echo "Found Python $PYTHON_VERSION"
    
    # Extract major and minor version
    MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
    MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)
    
    if [ "$MAJOR" -lt 3 ] || ([ "$MAJOR" -eq 3 ] && [ "$MINOR" -lt 7 ]); then
        echo "Error: Python 3.7 or higher is required"
        exit 1
    fi
else
    echo "Error: Python 3 not found. Please install Python 3.7 or higher"
    exit 1
fi

# Create virtual environment
echo "Creating Python virtual environment..."
python3 -m venv venv
if [ $? -ne 0 ]; then
    echo "Error: Failed to create virtual environment"
    exit 1
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate
if [ $? -ne 0 ]; then
    echo "Error: Failed to activate virtual environment"
    exit 1
fi

# Install dependencies
echo "Installing dependencies from project/requirements.txt..."
pip install --upgrade pip
pip install -r project/requirements.txt

# Check if user is in dialout group (for serial port access)
if groups | grep -q '\bdialout\b'; then
    echo "User is in dialout group"
else
    echo "Adding user to dialout group for serial port access..."
    sudo usermod -a -G dialout $USER
    echo "NOTE: You may need to log out and back in for group changes to take effect"
fi

# Create configuration file
echo "Creating default configuration..."
if [ ! -f "config.ini" ]; then
    cat > config.ini << EOF
[serial]
port = /dev/ttyUSB0
baudrate = 2400
timeout = 5

[server]
host = 0.0.0.0
port = 5000
debug = False
EOF
    echo "Created default config.ini"
else
    echo "config.ini already exists, keeping existing configuration"
fi

# Create WSGI entry point for Gunicorn
echo "Creating WSGI entry point for Gunicorn..."
cat > wsgi.py << EOF
"""WSGI entry point for Gunicorn"""
import sys
import os

# Add the project's parent directory to the Python path
# This ensures that both 'project' and 'project.inverter' can be imported
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the Flask app
from project.app import create_app

# Create the application instance
application = create_app()

# For compatibility with some WSGI servers
app = application

if __name__ == "__main__":
    application.run()
EOF

# Create startup script with options for different servers
echo "Creating startup scripts..."
cat > start.sh << EOF
#!/bin/bash
source venv/bin/activate
export FLASK_APP=project/app.py
export FLASK_ENV=production

# Default to Flask development server
SERVER=\${1:-flask}

case \$SERVER in
  flask)
    echo "Starting with Flask development server..."
    python -m flask run --host=0.0.0.0 --port=5000
    ;;
  gunicorn)
    echo "Starting with Gunicorn production server..."
    gunicorn -b 0.0.0.0:5000 -w 4 wsgi:app
    ;;
  *)
    echo "Unknown server: \$SERVER"
    echo "Usage: ./start.sh [flask|gunicorn]"
    exit 1
    ;;
esac
EOF
chmod +x start.sh

# Create development startup script
echo "Creating development startup script..."
cat > dev.sh << EOF
#!/bin/bash
source venv/bin/activate
export FLASK_APP=project/app.py
export FLASK_ENV=development
export FLASK_DEBUG=1
python -m flask run --host=0.0.0.0 --port=5000
EOF
chmod +x dev.sh

# Ask user if they want to install the systemd service
echo ""
echo "Would you like to install the P18 Inverter API as a system service? (y/n)"
read -r install_service

if [[ "$install_service" =~ ^[Yy]$ ]]; then
    # Get the current user and directory for the service file
    CURRENT_USER=$(whoami)
    CURRENT_DIR=$(pwd)
    
    # Ask user which server to use
    echo ""
    echo "Which server would you like to use?"
    echo "1) Gunicorn (recommended for production)"
    echo "2) Flask built-in server (simpler, better for development)"
    read -r server_choice
    
    # Create the service file based on the user's choice
    echo "Creating systemd service file..."
    
    if [[ "$server_choice" == "2" ]]; then
        # Flask built-in server
        sudo bash -c "cat > /etc/systemd/system/p18-inverter-api.service << EOF
[Unit]
Description=P18 Inverter API Service
After=network.target

[Service]
Type=simple
User=$CURRENT_USER
WorkingDirectory=$CURRENT_DIR
ExecStart=$CURRENT_DIR/venv/bin/python -m flask run --host=0.0.0.0 --port=5000
Environment=\"FLASK_APP=project/app.py\"
Environment=\"FLASK_ENV=production\"
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF"
        echo "Service configured to use Flask's built-in server."
    else
        # Default to Gunicorn
        sudo bash -c "cat > /etc/systemd/system/p18-inverter-api.service << EOF
[Unit]
Description=P18 Inverter API Service
After=network.target

[Service]
Type=simple
User=$CURRENT_USER
WorkingDirectory=$CURRENT_DIR
ExecStart=$CURRENT_DIR/venv/bin/gunicorn --workers=2 --bind=0.0.0.0:5000 wsgi:app
Environment=\"FLASK_APP=project/app.py\"
Environment=\"FLASK_ENV=production\"
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF"
        echo "Service configured to use Gunicorn."
    fi
    
    # Reload systemd, enable and start the service
    echo "Enabling and starting the service..."
    sudo systemctl daemon-reload
    sudo systemctl enable p18-inverter-api.service
    sudo systemctl start p18-inverter-api.service
    
    # Check service status
    echo "Service status:"
    sudo systemctl status p18-inverter-api.service
    
    echo ""
    echo "The P18 Inverter API service has been installed and started."
    echo "You can manage it with the following commands:"
    echo "  sudo systemctl start p18-inverter-api.service"
    echo "  sudo systemctl stop p18-inverter-api.service"
    echo "  sudo systemctl restart p18-inverter-api.service"
    echo "  sudo systemctl status p18-inverter-api.service"
    echo ""
    echo "To view logs:"
    echo "  sudo journalctl -u p18-inverter-api.service -f"
else
    echo ""
    echo "Service installation skipped."
    echo "You can manually start the application using:"
    echo "  ./start.sh gunicorn    # For production with Gunicorn"
    echo "  ./start.sh flask       # For production with Flask"
    echo "  ./dev.sh               # For development with Flask"
fi

echo "========================================================="
echo "Installation complete!"
echo "The API will be available at: http://localhost:5000"
echo "========================================================="