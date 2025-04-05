# secure-sim/process_sim/water_tank.py
import threading
import random
import time


class WaterTank:
    """Simple water tank simulation with inflow and outflow rates"""
    def __init__(self, capacity=100.0, initial_level=10.0, random_outflow=True):
        self.capacity = capacity
        self.level = initial_level
        self.inflow = 0.0  # Controlled by inflow valve actuator
        self.outflow = 0.0  # Controlled by outflow valve actuator
        self.inflow_valve_position = 0.0  # 0.0 (closed) to 1.0 (fully open)
        self.outflow_valve_position = 0.0  # 0.0 (closed) to 1.0 (fully open)
        self.lock = threading.Lock()
        self.random_outflow = random_outflow
        self.random_outflow_thread = None
        self.pressure = 0.0  # Initialize pressure value
        self.last_outflow_event = "No outflow events yet"
        
        # Start random outflow thread if enabled
        if random_outflow:
            self.start_random_outflow()

    def update(self, dt=1.0):
        """Update water level based on inflow and outflow rates"""
        with self.lock:
            # Calculate level change
            change = self.inflow - self.outflow
            self.level += change * dt
            
            # Ensure level stays within bounds
            self.level = max(0, min(self.capacity, self.level))
            
            # Update pressure (simple calculation based on water level)
            self.pressure = self.level * 0.1  # Simplified pressure calculation
            return self.level

    def set_inflow(self, rate):
        """Set the inflow rate in units per second by adjusting the inflow valve actuator"""
        with self.lock:
            self.inflow = rate
            # Convert rate to valve position (0-5 flow rate maps to 0-1 valve position)
            self.inflow_valve_position = min(1.0, max(0.0, rate / 5.0))
            print(f"Inflow valve adjusted to {self.inflow_valve_position:.2f} position ({rate:.2f} units/sec)")

    def set_outflow(self, rate):
        """Set the outflow rate in units per second by adjusting the outflow valve actuator"""
        with self.lock:
            self.outflow = rate
            # Convert rate to valve position (0-5 flow rate maps to 0-1 valve position)
            self.outflow_valve_position = min(1.0, max(0.0, rate / 5.0))
            print(f"Outflow valve adjusted to {self.outflow_valve_position:.2f} position ({rate:.2f} units/sec)")

    def get_level(self):
        """Get the current water level"""
        with self.lock:
            return self.level
            
    def get_pressure(self):
        """Get the current pressure reading"""
        with self.lock:
            return self.pressure
            
    def get_inflow_valve_position(self):
        """Get the current inflow valve position (0.0 = closed, 1.0 = fully open)"""
        with self.lock:
            return self.inflow_valve_position
            
    def get_outflow_valve_position(self):
        """Get the current outflow valve position (0.0 = closed, 1.0 = fully open)"""
        with self.lock:
            return self.outflow_valve_position
            
    def get_last_outflow_event(self):
        """Get the last outflow event message"""
        with self.lock:
            return self.last_outflow_event
            
    def random_outflow_loop(self):
        """Thread that updates outflow with random values every 2 seconds"""
        while True:
            # Generate random outflow between 0 and 4
            random_value = random.randint(0, 4)
            
            # Update outflow rate and valve position
            with self.lock:
                self.outflow = float(random_value)
                self.outflow_valve_position = min(1.0, max(0.0, self.outflow / 5.0))
                self.last_outflow_event = f"Random outflow changed to {self.outflow:.2f} units/sec ({self.outflow_valve_position:.2f} valve position)"
                print(f"RANDOM OUTFLOW EVENT: Valve adjusted to {self.outflow_valve_position:.2f} position ({self.outflow:.2f} units/sec)")
            
            # Wait for 2 seconds
            time.sleep(4)
    
    def start_random_outflow(self):
        """Start the random outflow thread"""
        self.random_outflow = True
        self.random_outflow_thread = threading.Thread(target=self.random_outflow_loop)
        self.random_outflow_thread.daemon = True
        self.random_outflow_thread.start()
        
    def stop_random_outflow(self):
        """Stop the random outflow"""
        self.random_outflow = False
