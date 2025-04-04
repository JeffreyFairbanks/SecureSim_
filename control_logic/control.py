# secure-sim/control_logic/control.py
import time
import threading


class Controller:
    """Simple proportional controller for water tank level"""
    def __init__(self, tank, setpoint=50.0):
        self.tank = tank
        self.setpoint = setpoint
        self.running = True
        self.manual_control = False

    def set_manual_control(self, enabled):
        """Enable or disable automatic control"""
        self.manual_control = enabled

    def control_loop(self):
        """Main control loop that adjusts inflow to maintain setpoint"""
        while self.running:
            # Only control automatically if manual control is disabled
            if not self.manual_control:
                # Get current tank level
                current_level = self.tank.get_level()
                
                # Calculate error (difference from setpoint)
                error = self.setpoint - current_level
                
                # Simple proportional control
                kp = 0.1  # Proportional gain
                control_signal = kp * error
                
                # Adjust inflow based on control signal (limit between 0 and 5)
                new_inflow = max(0, min(5, control_signal + 2.5))
                self.tank.set_inflow(new_inflow)
                
                # Outflow is handled by random outflow feature if enabled
                # Otherwise use a constant outflow
                if not hasattr(self.tank, 'random_outflow') or not self.tank.random_outflow:
                    self.tank.set_outflow(1.0)
            
            # Sleep to control loop rate
            time.sleep(1)


    def start(self):
        """Start control loop in background thread"""
        thread = threading.Thread(target=self.control_loop)
        thread.daemon = True
        thread.start()
        return thread


    def stop(self):
        """Stop the control loop"""
        self.running = False
