# API package initialization
"""
API module for P18 Inverter Monitor

This module contains the API endpoints for interacting with the P18 inverter.
"""
from flask import Blueprint

api_bp = Blueprint('api', __name__)

# Import routes to register them with the blueprint
from . import routes