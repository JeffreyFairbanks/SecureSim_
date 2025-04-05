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
        self.critical_pressure = 30.0  # Critical pressure threshold in psi
        self.has_exploded = False  # Tank explosion state
        self.pressure_increasing = False  # Flag to simulate pressure increase
        self.pressure_increase_rate = 1.0  # PSI per second when increasing
        
        # Start random outflow thread if enabled
        if random_outflow:
            self.start_random_outflow()

    def update(self, dt=1.0):
        """Update water level based on inflow and outflow rates"""
        with self.lock:
            # If tank has exploded, no further updates
            if self.has_exploded:
                self.level = 0.0  # Tank is empty after explosion
                return self.level
            
            # Calculate level change
            change = self.inflow - self.outflow
            self.level += change * dt
            
            # Ensure level stays within bounds
            self.level = max(0, min(self.capacity, self.level))
            
            # Check if tank is at maximum capacity
            if self.level >= self.capacity:
                # Start runaway pressure increase
                self.pressure_increasing = True
                print(f"WARNING: Tank at maximum capacity! Pressure building...")
            
            # Update pressure
            if self.pressure_increasing:
                # Pressure increases independently of level when tank is at max capacity
                self.pressure += self.pressure_increase_rate * dt
                print(f"DANGER: Pressure rising! Current pressure: {self.pressure:.1f} psi")
                
                # Check if pressure exceeds critical threshold
                if self.pressure >= self.critical_pressure and not self.has_exploded:
                    self.tank_explosion()
            else:
                # Normal pressure calculation based on water level
                self.pressure = self.level * 0.1  # Simplified pressure calculation
            
            return self.level
            
    def tank_explosion(self):
        """Simulate tank explosion when pressure exceeds critical threshold"""
        with self.lock:
            self.has_exploded = True
            self.level = 0  # Tank empties completely
            self.inflow = 0  # Inflow stops
            self.outflow = 0  # Outflow stops
            self.inflow_valve_position = 0
            self.outflow_valve_position = 0
            
            print("\n" + "!" * 80)
            print("!!! CATASTROPHIC FAILURE: TANK EXPLOSION !!!")
            print("Tank has exploded due to excessive pressure!")
            print("All systems offline. Tank contents lost.")
            print("!" * 80 + "\n")
            
            # Notify the dashboard of the explosion
            try:
                # Avoid importing main.py which would cause circular imports
                from scada_ui.dashboard import update_tank_explosion_status
                update_tank_explosion_status(True)
            except ImportError:
                print("Failed to notify dashboard of explosion")
            
            # Don't hang the program - allow normal termination
            import sys
            import threading
            
            # Create a shutdown timer to terminate the program after a brief delay
            def emergency_shutdown():
                print("\nSYSTEM SHUTDOWN: Emergency exit initiated due to catastrophic failure...")
                # Give the user 5 seconds to see what happened then exit
                time.sleep(5)
                sys.exit(1)
            
            # Run the emergency shutdown in a separate thread to not block main thread
            shutdown_thread = threading.Thread(target=emergency_shutdown)
            shutdown_thread.daemon = True  # Daemon thread will exit when main thread exits
            shutdown_thread.start()

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
