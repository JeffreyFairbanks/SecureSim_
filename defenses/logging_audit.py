#!/usr/bin/env python3
"""
Enhanced Logging and Audit Defense

This defense module provides enhanced logging capabilities beyond the basic 
logging_defense.py with additional security features:
1. Detailed event logging with cryptographic signatures
2. Comprehensive audit trails for all system operations
3. Time-synchronized event recording
"""

import logging
import hashlib
import os
import json
import time
import hmac
import datetime
from collections import deque

# Create a secure key for log signatures (in production, this would be stored securely)
# This is a simple implementation for demonstration purposes
SECRET_KEY = b'secure_sim_hmac_key_2023'

# In-memory circular buffer for recent events (quick access for dashboard)
recent_events = deque(maxlen=100)

# Initialize custom logger
audit_logger = logging.getLogger('audit')

def setup_audit_logging():
    """Initialize enhanced audit logging system"""
    # Create data directory if needed
    os.makedirs('data/audit', exist_ok=True)
    
    # Configure audit logging to dedicated file with high detail
    audit_handler = logging.FileHandler('data/audit/audit_log.json')
    audit_formatter = logging.Formatter('%(asctime)s:%(levelname)s:%(message)s')
    audit_handler.setFormatter(audit_formatter)
    
    audit_logger.addHandler(audit_handler)
    audit_logger.setLevel(logging.INFO)
    
    # Log initialization event
    log_event("SYSTEM", "Audit logging initialized", "system_start")
    return True

def create_signature(data):
    """Create HMAC signature for log data to ensure integrity"""
    # Convert data to string if it's not already
    if not isinstance(data, str):
        data = json.dumps(data)
    
    # Create signature using HMAC-SHA256
    signature = hmac.new(
        SECRET_KEY, 
        data.encode('utf-8'), 
        hashlib.sha256
    ).hexdigest()
    
    return signature

def log_event(source, message, event_type, details=None):
    """Log a security event with signature for integrity verification"""
    timestamp = datetime.datetime.now().isoformat()
    
    # Structured log entry
    log_entry = {
        "timestamp": timestamp,
        "source": source,
        "event_type": event_type,
        "message": message,
        "details": details or {}
    }
    
    # Create signature for log entry
    signature = create_signature(log_entry)
    log_entry["signature"] = signature
    
    # Add to in-memory buffer for quick access
    recent_events.append(log_entry)
    
    # Write to log file
    audit_logger.info(json.dumps(log_entry))
    
    # Print to console for debugging
    print(f"[AUDIT] {timestamp} - {source} - {event_type}: {message}")
    
    return log_entry

def log_sensor_reading(sensor_name, value, unit="units"):
    """Log a sensor reading with verification signature"""
    return log_event(
        source="SENSOR", 
        message=f"{sensor_name} reading: {value} {unit}", 
        event_type="sensor_reading",
        details={
            "sensor": sensor_name,
            "value": value,
            "unit": unit,
            "reading_time": time.time()
        }
    )

def log_control_action(action_name, parameter, value):
    """Log a control action with verification signature"""
    return log_event(
        source="CONTROL", 
        message=f"Control action: {action_name} - {parameter}={value}", 
        event_type="control_action",
        details={
            "action": action_name,
            "parameter": parameter,
            "value": value,
            "action_time": time.time()
        }
    )

def log_system_state(tank_level, pressure, inflow, outflow, inflow_valve, outflow_valve):
    """Log complete system state for audit purposes"""
    return log_event(
        source="SYSTEM", 
        message=f"System state: Level={tank_level:.2f}, Pressure={pressure:.2f}", 
        event_type="system_state",
        details={
            "tank_level": tank_level,
            "pressure": pressure,
            "inflow_rate": inflow,
            "outflow_rate": outflow,
            "inflow_valve_position": inflow_valve,
            "outflow_valve_position": outflow_valve,
            "state_time": time.time()
        }
    )

def log_security_event(event_name, severity, details=None):
    """Log a security-related event with appropriate severity"""
    return log_event(
        source="SECURITY", 
        message=f"Security event ({severity}): {event_name}", 
        event_type="security_event",
        details={
            "event_name": event_name,
            "severity": severity,
            "details": details or {},
            "event_time": time.time()
        }
    )

def get_recent_events(count=10, event_type=None):
    """Get recent events from in-memory buffer, optionally filtered by type"""
    if event_type:
        filtered_events = [e for e in recent_events if e["event_type"] == event_type]
        return list(filtered_events)[-count:]
    return list(recent_events)[-count:]

def verify_log_integrity(log_entry):
    """Verify the integrity of a log entry using its signature"""
    if "signature" not in log_entry:
        return False
    
    signature = log_entry.pop("signature")
    calculated_signature = create_signature(log_entry)
    log_entry["signature"] = signature  # Restore the signature
    
    return signature == calculated_signature