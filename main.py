# week_1/main.py
import time
import argparse
from process_sim.water_tank import WaterTank
from control_logic.control import Controller
from logging_defense import setup_logging, log_anomaly, setup_console_logging, stop_console_logging
from scada_ui.dashboard import start_dashboard, update_water_level


def simulation_loop(tank):
    """Simplified simulation loop for Week 1"""
    # Flag to track if we've completed a full demo cycle
    
    while True:
        # Update water tank state
        current_level = tank.update(dt=1)
        
        # Log water level
        print(f"Water Tank Level: {current_level:.1f}")
        
        # Update UI with level and flow rates
        update_water_level(current_level, tank.inflow, tank.outflow)
        
        # Basic safety check
        if current_level <= 0 or current_level >= tank.capacity:
            log_anomaly(f"Tank level out of bounds: {current_level}")
        
        time.sleep(1)


def main():
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description='Water Tank Simulation - Week 1')
    args = parser.parse_args()
    
    # Initialize logging
    console_log_file = setup_console_logging()
    setup_logging()
    
    # Initialize the water tank simulation with random outflow
    tank = WaterTank(capacity=100.0, initial_level=10.0, random_outflow=False)
    
    # Start the control logic
    controller = Controller(tank, setpoint=50.0)
    controller.start()
    
    # Start the dashboard UI
    start_dashboard()
    
    # Run the main simulation loop
    try:
        simulation_loop(tank)
    except KeyboardInterrupt:
        print("Simulation terminated by user.")
    finally:
        controller.stop()
        stop_console_logging(console_log_file)


if __name__ == "__main__":
    main()