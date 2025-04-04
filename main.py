# week_1/main.py
import time
import argparse
from process_sim.water_tank import WaterTank
from control_logic.control import Controller
from logging_defense import setup_logging, log_anomaly, setup_console_logging, stop_console_logging
from scada_ui.dashboard import start_dashboard, update_water_level, app


def simulation_loop(tank):
    """Simplified simulation loop for Week 1"""
    global emergency_stop_flag
    
    while True:  # Run indefinitely, handle emergency stop within the loop
        # Check if in emergency stop mode
        if emergency_stop_flag:
            # Still update the UI with current level during emergency stop
            current_level = tank.update(dt=1)
            update_water_level(current_level, tank.inflow, tank.outflow, emergency_state=True)
            time.sleep(1)
            continue
            
        # Normal operation mode
        # Update water tank state
        current_level = tank.update(dt=1)
        
        # Log water level
        print(f"Water Tank Level: {current_level:.1f}")
        
        # Update UI with level and flow rates
        update_water_level(current_level, tank.inflow, tank.outflow, emergency_state=False)
        
        # Basic safety check
        if current_level <= 0 or current_level >= tank.capacity:
            log_anomaly(f"Tank level out of bounds: {current_level}")
        
        time.sleep(1)


# Global variables for control functionality
emergency_stop_flag = False
simulation_controller = None
simulation_tank = None
system_status = "Running"

# Emergency stop and resume handlers for Flask
@app.route('/api/emergency-stop', methods=['POST'])
def handle_emergency_stop():
    global emergency_stop_flag, simulation_controller, simulation_tank, system_status
    from flask import jsonify, request
    
    print("EMERGENCY STOP ACTIVATED VIA API")
    log_anomaly("Emergency stop button activated via dashboard")
    
    # Set the flag to stop the simulation
    emergency_stop_flag = True
    system_status = "Emergency Stop"
    
    # Stop controller and drain the tank
    if simulation_controller:
        simulation_controller.stop()
        print("Controller stopped")
    
    if simulation_tank:
        # Set inflow to 0 and a high outflow to drain the tank
        simulation_tank.set_inflow(0.0)
        simulation_tank.set_outflow(5.0)
        print("Tank draining: inflow=0, outflow=5.0")
        log_anomaly("Emergency stop activated: Draining tank and stopping control systems")
    
    # Make sure the changes are applied immediately
    if simulation_tank:
        simulation_tank.update(dt=1)
    
    return jsonify({'status': 'success', 'message': 'Emergency stop activated', 'system_status': system_status})


@app.route('/api/resume-operation', methods=['POST'])
def handle_resume_operation():
    global emergency_stop_flag, simulation_controller, simulation_tank, system_status
    from flask import jsonify, request
    
    if not emergency_stop_flag:
        # Already running
        return jsonify({'status': 'warning', 'message': 'System already running'})
    
    print("RESUMING OPERATIONS VIA API")
    log_anomaly("System operations resumed via dashboard")
    
    # Reset the emergency flag
    emergency_stop_flag = False
    system_status = "Running"
    
    # Restart controller
    if simulation_controller:
        # Create a new controller or restart existing one
        simulation_controller.running = True
        simulation_controller.start()
        print("Controller restarted")
    
    # Reset tank flows to normal operation
    if simulation_tank:
        # Initialize with modest inflow to start building up level again
        simulation_tank.set_inflow(2.0)
        simulation_tank.set_outflow(1.0)
        print("Tank flows reset: inflow=2.0, outflow=1.0")
        log_anomaly("System restarted: Resuming normal operations")
    
    return jsonify({'status': 'success', 'message': 'Operations resumed', 'system_status': system_status})


@app.route('/api/system-status')
def get_system_status():
    global system_status
    from flask import jsonify
    
    return jsonify({
        'status': system_status,
        'emergency_stop': emergency_stop_flag
    })

def main():
    global simulation_controller, simulation_tank, emergency_stop_flag, system_status
    
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description='Water Tank Simulation - Week 1')
    args = parser.parse_args()
    
    # Initialize logging
    console_log_file = setup_console_logging()
    setup_logging()
    
    # Reset global state
    emergency_stop_flag = False
    system_status = "Running"
    
    # Initialize the water tank simulation with random outflow
    tank = WaterTank(capacity=100.0, initial_level=10.0, random_outflow=False)
    simulation_tank = tank
    
    # Start the control logic
    controller = Controller(tank, setpoint=50.0)
    simulation_controller = controller
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