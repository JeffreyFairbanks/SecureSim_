# secure-sim/process_sim/water_tank.py
import threading
import random
import time


class WaterTank:
    """Simple water tank simulation with inflow and outflow rates"""
    def __init__(self, capacity=100.0, initial_level=10.0, random_outflow=False):
        self.capacity = capacity
        self.level = initial_level
        self.inflow = 0.0
        self.outflow = 0.0
        self.lock = threading.Lock()
        self.random_outflow = random_outflow
        self.random_outflow_thread = None
        
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
            return self.level

    def set_inflow(self, rate):
        """Set the inflow rate in units per second"""
        with self.lock:
            self.inflow = rate

    def set_outflow(self, rate):
        """Set the outflow rate in units per second"""
        with self.lock:
            self.outflow = rate

    def get_level(self):
        """Get the current water level"""
        with self.lock:
            return self.level
            
    def random_outflow_loop(self):
        """Thread that updates outflow with random values every 2 seconds"""
        while True:
            # Generate random outflow between 0 and 4
            random_value = random.randint(0, 4)
            
            # Update outflow rate
            with self.lock:
                self.outflow = float(random_value)
            
            # Wait for 2 seconds
            time.sleep(2)
    
    def start_random_outflow(self):
        """Start the random outflow thread"""
        self.random_outflow = True
        self.random_outflow_thread = threading.Thread(target=self.random_outflow_loop)
        self.random_outflow_thread.daemon = True
        self.random_outflow_thread.start()
        
    def stop_random_outflow(self):
        """Stop the random outflow"""
        self.random_outflow = False
