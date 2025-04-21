"""
SecureSim Defense Mechanisms

This package contains security defense mechanisms for the water tank SCADA system:

1. logging_audit.py - Enhanced logging and auditing
2. anomaly_detection.py - Statistical and physics-based anomaly detection
3. command_authentication.py - Command authentication and validation
"""

from defenses.logging_audit import setup_audit_logging, log_event, log_security_event
from defenses.anomaly_detection import AnomalyDetector
from defenses.command_authentication import CommandAuthenticator, system_state_validator

__all__ = [
    'setup_audit_logging', 'log_event', 'log_security_event',
    'AnomalyDetector',
    'CommandAuthenticator', 'system_state_validator'
]