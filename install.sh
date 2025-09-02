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
    gunicorn -b 0.0.0.0:5000 -w 4 'project.app:create_app()'
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

# Create service file for systemd
echo "Creating systemd service file..."
cat > p18-inverter-api.service << EOF
[Unit]
Description=P18 Inverter API Service
After=network.target

[Service]
Type=simple
User=$(whoami)
WorkingDirectory=$(pwd)
ExecStart=$(pwd)/venv/bin/gunicorn -b 0.0.0.0:5000 -w 4 'project.app:create_app()'
Environment="FLASK_APP=project/app.py"
Environment="FLASK_ENV=production"
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

echo "To install as a system service, run:"
echo "sudo cp p18-inverter-api.service /etc/systemd/system/"
echo "sudo systemctl daemon-reload"
echo "sudo systemctl enable p18-inverter-api.service"
echo "sudo systemctl start p18-inverter-api.service"

echo "========================================================="
echo "Installation complete!"
echo ""
echo "To start the application in production mode with Flask:"
echo "  ./start.sh flask"
echo ""
echo "To start the application in production mode with Gunicorn (recommended):"
echo "  ./start.sh gunicorn"
echo ""
echo "To start the application in development mode:"
echo "  ./dev.sh"
echo ""
echo "The API will be available at: http://localhost:5000"
echo "API documentation available at: http://localhost:5000/docs"
echo "========================================================="