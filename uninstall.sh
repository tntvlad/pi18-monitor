#!/bin/bash

# P18 Inverter API Uninstallation Script
# This script removes the P18 Inverter API service and related components

echo "========================================================="
echo "P18 Inverter API Uninstallation"
echo "========================================================="

# Function to ask yes/no questions
ask_yes_no() {
    while true; do
        read -p "$1 (y/n): " answer
        case $answer in
            [Yy]* ) return 0;;
            [Nn]* ) return 1;;
            * ) echo "Please answer yes (y) or no (n).";;
        esac
    done
}

# Check if running as root or with sudo
if [ "$EUID" -ne 0 ]; then
    echo "Some operations require administrative privileges."
    if ask_yes_no "Do you want to continue with sudo?"; then
        echo "Continuing with sudo for system operations..."
    else
        echo "Exiting. Please run this script with sudo or as root for full functionality."
        exit 1
    fi
fi

# Stop and disable the service if it exists
if systemctl is-active --quiet p18-inverter-api.service; then
    echo "Stopping P18 Inverter API service..."
    sudo systemctl stop p18-inverter-api.service
fi

if systemctl is-enabled --quiet p18-inverter-api.service; then
    echo "Disabling P18 Inverter API service..."
    sudo systemctl disable p18-inverter-api.service
fi

# Remove the service file
if [ -f /etc/systemd/system/p18-inverter-api.service ]; then
    echo "Removing service file..."
    sudo rm /etc/systemd/system/p18-inverter-api.service
    sudo systemctl daemon-reload
    echo "Service file removed."
else
    echo "Service file not found. Skipping removal."
fi

# Ask about removing the virtual environment
if [ -d "venv" ]; then
    if ask_yes_no "Do you want to remove the virtual environment?"; then
        echo "Removing virtual environment..."
        rm -rf venv
        echo "Virtual environment removed."
    else
        echo "Keeping virtual environment."
    fi
else
    echo "Virtual environment not found. Skipping removal."
fi

# Ask about removing configuration files
if [ -f "config.ini" ]; then
    if ask_yes_no "Do you want to remove the configuration file (config.ini)?"; then
        echo "Removing configuration file..."
        rm config.ini
        echo "Configuration file removed."
    else
        echo "Keeping configuration file."
    fi
fi

# Ask about removing generated scripts
if [ -f "start.sh" ] || [ -f "dev.sh" ] || [ -f "wsgi.py" ]; then
    if ask_yes_no "Do you want to remove generated scripts (start.sh, dev.sh, wsgi.py)?"; then
        echo "Removing generated scripts..."
        [ -f "start.sh" ] && rm start.sh
        [ -f "dev.sh" ] && rm dev.sh
        [ -f "wsgi.py" ] && rm wsgi.py
        echo "Generated scripts removed."
    else
        echo "Keeping generated scripts."
    fi
fi

# Ask about removing the entire project
if ask_yes_no "Do you want to completely remove the P18 Inverter Monitor project directory?"; then
    echo "WARNING: This will delete ALL files in the current directory."
    if ask_yes_no "Are you ABSOLUTELY SURE you want to delete everything?"; then
        echo "Removing project directory..."
        cd ..
        rm -rf "$(basename "$(pwd)")"
        echo "Project directory removed."
        echo "Uninstallation complete!"
        exit 0
    fi
fi

echo "========================================================="
echo "Uninstallation completed!"
echo "The P18 Inverter API service has been removed from your system."
echo "========================================================="