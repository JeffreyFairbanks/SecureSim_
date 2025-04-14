#!/usr/bin/env python3
"""
Anomaly Detection Defense

This defense module implements basic anomaly detection for the water tank system:
1. Statistical analysis of sensor data to detect unusual patterns
2. Physics-based validation to ensure readings follow expected physical laws
3. Correlation checks between sensor readings
4. Pattern detection for replay attack identification
"""

import numpy as np
import time
from collections import deque

class AnomalyDetector:
    """Anomaly detection system for water tank simulation"""
    def __init__(self, window_size=30):
        # History window size for monitoring trends
        self.window_size = window_size
        
        # Data storage
        self.level_history = deque(maxlen=window_size)
        self.pressure_history = deque(maxlen=window_size)
        self.inflow_history = deque(maxlen=window_size)
        self.outflow_history = deque(maxlen=window_size)
        self.timestamp_history = deque(maxlen=window_size)
        
        # Pattern detection for replay attacks
        self.pattern_store = []
        self.pattern_length = 5
        
        # Detection thresholds
        self.rate_of_change_threshold = 5.0  # Maximum expected change in level per second
        self.pressure_correlation_threshold = 0.7  # Expected correlation between level and pressure
        self.physics_violation_threshold = 0.5  # Allowable error in physics model
        
        # Anomaly status flags
        self.anomalies_detected = {
            "rate_of_change": False,
            "correlation": False,
            "physics": False,
            "replay_pattern": False
        }
        
        # Callback for when anomaly is detected
        self.anomaly_callback = None
    
    def set_anomaly_callback(self, callback):
        """Set callback function to be called when an anomaly is detected"""
        self.anomaly_callback = callback
    
    def update(self, level, pressure, inflow, outflow):
        """Update detector with new sensor readings"""
        # Record current time
        current_time = time.time()
        
        # Add new readings to history
        self.level_history.append(level)
        self.pressure_history.append(pressure)
        self.inflow_history.append(inflow)
        self.outflow_history.append(outflow)
        self.timestamp_history.append(current_time)
        
        # Reset anomaly flags
        self.anomalies_detected = {
            "rate_of_change": False,
            "correlation": False,
            "physics": False,
            "replay_pattern": False
        }
        
        # Only perform checks if we have enough history
        if len(self.level_history) >= 2:
            self._check_rate_of_change()
            self._check_physics_model()
            
        if len(self.level_history) >= self.pattern_length:
            self._check_replay_patterns()
            self._check_sensor_correlation()
        
        # Return whether any anomalies were detected
        any_anomaly = any(self.anomalies_detected.values())
        if any_anomaly and self.anomaly_callback:
            self.anomaly_callback(self.anomalies_detected)
            
        return any_anomaly, self.anomalies_detected
    
    def _check_rate_of_change(self):
        """Check if water level is changing at an unrealistic rate"""
        level_change = abs(self.level_history[-1] - self.level_history[-2])
        time_change = abs(self.timestamp_history[-1] - self.timestamp_history[-2])
        
        if time_change > 0:
            rate = level_change / time_change
            if rate > self.rate_of_change_threshold:
                self.anomalies_detected["rate_of_change"] = True
                if self.anomaly_callback:
                    detail = f"Abnormal level change: {level_change:.2f} units in {time_change:.2f} seconds"
                    return detail
        return None
    
    def _check_physics_model(self): # we know what the water should be because of our dt
        """Verify that water level changes match the expected physics model"""
        if len(self.level_history) < 2:
            return None
            
        dt = self.timestamp_history[-1] - self.timestamp_history[-2]
        previous_level = self.level_history[-2]
        current_level = self.level_history[-1]
        
        # Calculate expected level based on inflow/outflow
        inflow = self.inflow_history[-2]  # Use previous inflow
        outflow = self.outflow_history[-2]  # Use previous outflow
        
        # Expected change based on simple physics model: level change = (inflow - outflow) * dt
        expected_change = (inflow - outflow) * dt
        expected_level = previous_level + expected_change
        
        # Calculate error between expected and actual
        model_error = abs(expected_level - current_level)
        
        if model_error > self.physics_violation_threshold:
            self.anomalies_detected["physics"] = True
            if self.anomaly_callback:
                detail = f"Physics model violation: Expected={expected_level:.2f}, Actual={current_level:.2f}"
                return detail
        return None
    
    def _check_sensor_correlation(self): # pressure checks
        """Check if pressure and level readings are correlated as expected"""
        if len(self.level_history) < 5:
            return None
            
        # Convert deques to numpy arrays for correlation calculation
        level_array = np.array(list(self.level_history))
        pressure_array = np.array(list(self.pressure_history))
        
        # Calculate correlation coefficient
        try:
            correlation = np.corrcoef(level_array, pressure_array)[0, 1]
            
            if correlation < self.pressure_correlation_threshold:
                self.anomalies_detected["correlation"] = True
                if self.anomaly_callback:
                    detail = f"Low sensor correlation: {correlation:.2f} (threshold: {self.pressure_correlation_threshold})"
                    return detail
        except:
            # If correlation cannot be calculated, ignore this check
            pass
        
        return None
    
    def _check_replay_patterns(self):
        """Check for repeating patterns in sensor data that might indicate replay attack"""
        # Need enough data for pattern detection
        if len(self.level_history) < self.pattern_length * 2:
            return None
            
        # Get current pattern (last N readings)
        current_pattern = list(self.level_history)[-self.pattern_length:]
        
        # Store patterns for future comparison
        self.pattern_store.append(current_pattern)
        if len(self.pattern_store) > 10:  # Keep only recent patterns
            self.pattern_store.pop(0)
        
        # Compare with older patterns (skip the most recent one)
        for i, old_pattern in enumerate(self.pattern_store[:-1]):
            # Check similarity to old pattern
            similarity = self._calculate_pattern_similarity(current_pattern, old_pattern)
            
            # High similarity with an old pattern suggests replay
            if similarity > 0.9:  # 90% similarity threshold
                self.anomalies_detected["replay_pattern"] = True
                if self.anomaly_callback:
                    detail = f"Potential replay attack: Pattern similarity {similarity:.2f} with pattern from {i} cycles ago"
                    return detail
        
        return None
        
    def _calculate_pattern_similarity(self, pattern1, pattern2):
        """Calculate similarity between two patterns (0.0 to 1.0)"""
        if len(pattern1) != len(pattern2):
            return 0.0
            
        # Convert to numpy arrays
        array1 = np.array(pattern1)
        array2 = np.array(pattern2)
        
        # Calculate normalized difference
        diff = np.abs(array1 - array2)
        max_val = max(np.max(array1), np.max(array2))
        if max_val == 0:
            return 1.0  # Avoid division by zero
            
        # Calculate similarity (1.0 = identical, 0.0 = completely different)
        similarity = 1.0 - np.mean(diff) / max_val
        return similarity
    
    def get_status_report(self):
        """Get a status report of the anomaly detector"""
        return {
            "anomalies": self.anomalies_detected,
            "history_size": len(self.level_history),
            "latest_level": self.level_history[-1] if self.level_history else None,
            "latest_pressure": self.pressure_history[-1] if self.pressure_history else None
        }

# Standalone test function
def test_anomaly_detector():
    """Simple test for the anomaly detector"""
    detector = AnomalyDetector()
    
    # Normal behavior
    for i in range(10):
        level = 50.0 + i * 0.5
        pressure = level * 0.1
        inflow = 2.0
        outflow = 1.5
        result, details = detector.update(level, pressure, inflow, outflow)
        print(f"Normal update {i}: Anomaly detected? {result}")
    
    # Abnormal rate of change
    result, details = detector.update(70.0, 7.0, 2.0, 1.5)
    print(f"Abnormal change: Anomaly detected? {result}, Details: {details}")
    
    # Physics violation
    result, details = detector.update(65.0, 6.5, 2.0, 10.0)
    print(f"Physics violation: Anomaly detected? {result}, Details: {details}")

if __name__ == "__main__":
    test_anomaly_detector()