#!/usr/bin/env python3
"""
Command Authentication Defense

This defense module provides authentication for control commands:
1. Digital signatures for control commands
2. Rate limiting to prevent rapid manipulation
3. Command validation based on system state
4. Permission-based control mechanisms
"""

import time
import hashlib
import hmac
import json
import threading
from collections import deque

# Secure signature key (in production, this would be stored securely)
# This is a simple implementation for demonstration purposes
COMMAND_KEY = b'tank_control_command_hmac_key'

class CommandAuthenticator:
    """Authenticate and validate control commands"""
    def __init__(self):
        # Command rate limiting
        self.command_history = deque(maxlen=20)
        self.rate_limit_window = 10  # seconds
        self.rate_limit_max_commands = 5  # max commands per window
        
        # Permission levels
        self.permission_levels = {
            "operator": ["set_inflow", "set_outflow", "emergency_stop", "resume_operation"],
            "maintenance": ["set_inflow", "set_outflow", "emergency_stop", "resume_operation"],
            "admin": ["set_inflow", "set_outflow", "emergency_stop", "resume_operation", "change_setpoint"]
        }
        
        # Valid command ranges
        self.command_limits = {
            "set_inflow": {"min": 0.0, "max": 5.0},
            "set_outflow": {"min": 0.0, "max": 5.0},
            "change_setpoint": {"min": 10.0, "max": 90.0}
        }
        
        # Lock for thread safety
        self.lock = threading.Lock()
        
        # Command validation callback
        self.validation_callback = None
        
        # Authenticate all commands by default
        self.authentication_required = True
    
    def set_validation_callback(self, callback):
        """Set callback for additional command validation"""
        self.validation_callback = callback
    
    def toggle_authentication(self, enabled):
        """Enable or disable authentication requirement"""
        self.authentication_required = enabled
        return self.authentication_required
    
    def sign_command(self, command_name, parameters, user="operator"):
        """Sign a command with current timestamp and HMAC signature"""
        # Create command structure
        command = {
            "command": command_name,
            "parameters": parameters,
            "user": user,
            "timestamp": time.time()
        }
        
        # Create signature
        command_str = json.dumps(command, sort_keys=True)
        signature = hmac.new(
            COMMAND_KEY, 
            command_str.encode('utf-8'), 
            hashlib.sha256
        ).hexdigest()
        
        # Add signature to command
        signed_command = command.copy()
        signed_command["signature"] = signature
        
        return signed_command
    
    def verify_signature(self, signed_command):
        """Verify the signature of a command"""
        if not self.authentication_required:
            return True
            
        if "signature" not in signed_command:
            return False
            
        # Extract signature
        original_signature = signed_command["signature"]
        command_copy = signed_command.copy()
        command_copy.pop("signature")
        
        # Calculate expected signature
        command_str = json.dumps(command_copy, sort_keys=True)
        expected_signature = hmac.new(
            COMMAND_KEY, 
            command_str.encode('utf-8'), 
            hashlib.sha256
        ).hexdigest()
        
        # Compare signatures
        return original_signature == expected_signature
    
    def check_rate_limit(self, command_name, user):
        """Check if command exceeds rate limits"""
        with self.lock:
            current_time = time.time()
            
            # Add command to history
            self.command_history.append({
                "command": command_name,
                "user": user,
                "time": current_time
            })
            
            # Count commands in rate limit window
            window_start = current_time - self.rate_limit_window
            commands_in_window = sum(1 for cmd in self.command_history 
                                    if cmd["time"] >= window_start and cmd["command"] == command_name)
            
            # Check if rate limit exceeded
            return commands_in_window <= self.rate_limit_max_commands
    
    def check_permission(self, command_name, user):
        """Check if user has permission to execute command"""
        if user not in self.permission_levels:
            return False
            
        return command_name in self.permission_levels[user]
    
    def validate_command_limits(self, command_name, parameters):
        """Validate command parameters are within allowed limits"""
        if command_name not in self.command_limits:
            return True  # No limits defined for this command
            
        limits = self.command_limits[command_name]
        
        # Get the parameter value (assume first parameter or parameter itself)
        param_value = parameters
        if isinstance(parameters, dict) and len(parameters) > 0:
            # Get the first parameter's value
            param_value = next(iter(parameters.values()))
        
        # Check parameter is within limits
        try:
            value = float(param_value)
            return value >= limits["min"] and value <= limits["max"]
        except (ValueError, TypeError):
            return False
    
    def authenticate_command(self, signed_command, system_state=None):
        """Authenticate and validate a command, returns (success, reason)"""
        # Extract command details
        if not isinstance(signed_command, dict):
            return False, "Invalid command format"
            
        command_name = signed_command.get("command")
        parameters = signed_command.get("parameters", {})
        user = signed_command.get("user", "operator")
        
        # Verify signature if authentication is required
        if self.authentication_required:
            if not self.verify_signature(signed_command):
                return False, "Invalid signature"
        
        # Check rate limits
        if not self.check_rate_limit(command_name, user):
            return False, "Rate limit exceeded"
        
        # Check permissions
        if not self.check_permission(command_name, user):
            return False, "Permission denied"
        
        # Validate command parameters
        if not self.validate_command_limits(command_name, parameters):
            return False, "Parameter out of allowed range"
        
        # Call additional validation callback if provided
        if self.validation_callback and system_state:
            is_valid, reason = self.validation_callback(command_name, parameters, system_state)
            if not is_valid:
                return False, reason
        
        return True, "Command authenticated"

# System-state validation function example
def system_state_validator(command_name, parameters, system_state):
    """Validate commands based on current system state"""
    # Emergency stop can always be executed
    if command_name == "emergency_stop":
        return True, "Emergency stop allowed"
    
    # If system is in emergency state, only resume_operation is allowed
    if system_state.get("is_emergency", False):
        if command_name != "resume_operation":
            return False, "System in emergency state, command not allowed"
    
    # If tank level is too high, don't allow increasing inflow
    if command_name == "set_inflow":
        inflow = float(parameters.get("rate", 0))
        if system_state.get("tank_level", 0) > 90 and inflow > system_state.get("current_inflow", 0):
            return False, "Tank level too high, cannot increase inflow"
    
    # If tank level is too low, don't allow increasing outflow
    if command_name == "set_outflow":
        outflow = float(parameters.get("rate", 0))
        if system_state.get("tank_level", 0) < 10 and outflow > system_state.get("current_outflow", 0):
            return False, "Tank level too low, cannot increase outflow"
    
    return True, "Command validated"

# Example usage
def test_command_authenticator():
    """Simple test for the command authenticator"""
    authenticator = CommandAuthenticator()
    
    # Set system state validation callback
    authenticator.set_validation_callback(system_state_validator)
    
    # Sign a command
    signed_cmd = authenticator.sign_command("set_inflow", {"rate": 2.5}, user="operator")
    print("Signed command:", signed_cmd)
    
    # Authenticate the command
    system_state = {
        "tank_level": 50.0,
        "pressure": 5.0,
        "current_inflow": 1.0,
        "current_outflow": 1.0,
        "is_emergency": False
    }
    
    success, reason = authenticator.authenticate_command(signed_cmd, system_state)
    print(f"Authentication result: {success}, Reason: {reason}")
    
    # Test rate limiting
    for i in range(7):
        signed_cmd = authenticator.sign_command("set_inflow", {"rate": 2.5}, user="operator")
        success, reason = authenticator.authenticate_command(signed_cmd, system_state)
        print(f"Command {i+1} - Success: {success}, Reason: {reason}")
    
    # Test parameter validation
    signed_cmd = authenticator.sign_command("set_inflow", {"rate": 10.0}, user="operator")
    success, reason = authenticator.authenticate_command(signed_cmd, system_state)
    print(f"Invalid parameter - Success: {success}, Reason: {reason}")
    
    # Test emergency state
    system_state["is_emergency"] = True
    signed_cmd = authenticator.sign_command("set_inflow", {"rate": 2.5}, user="operator")
    success, reason = authenticator.authenticate_command(signed_cmd, system_state)
    print(f"Emergency state - Success: {success}, Reason: {reason}")
    
    # Emergency stop always works
    signed_cmd = authenticator.sign_command("emergency_stop", {}, user="operator")
    success, reason = authenticator.authenticate_command(signed_cmd, system_state)
    print(f"Emergency stop - Success: {success}, Reason: {reason}")

if __name__ == "__main__":
    test_command_authenticator()