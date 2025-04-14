# SecureSim/main.py
import time
import argparse
import os
from process_sim.water_tank import WaterTank
from control_logic.control import Controller
from logging_defense import setup_logging, log_anomaly, setup_console_logging, stop_console_logging
from scada_ui.dashboard import start_dashboard, update_water_level, app, api_get_true_water_level, print_levels
from defenses.logging_audit import setup_audit_logging, log_event, log_security_event, log_sensor_reading, log_control_action, log_system_state
from defenses.anomaly_detection import AnomalyDetector
from defenses.command_authentication import CommandAuthenticator, system_state_validator
security_imports_available = True

# Global security components
anomaly_detector = None
command_authenticator = None
security_active = False


def simulation_loop(tank):
    """Enhanced simulation loop with optional security defenses"""
    global emergency_stop_flag, security_active, anomaly_detector
    
    try:
        while True:  # Run indefinitely, handle emergency stop within the loop
            # Check if in emergency stop mode
            if emergency_stop_flag:
                # Still update the UI with current level during emergency stop
                current_level = tank.update(dt=1)
                current_pressure = tank.get_pressure()
                inflow_valve = tank.get_inflow_valve_position()
                outflow_valve = tank.get_outflow_valve_position()
                outflow_message = tank.get_last_outflow_event()
                
                # Security: Log system state during emergency if security is active
                if security_active:
                    log_system_state(
                        current_level, current_pressure, 
                        tank.inflow, tank.outflow,
                        inflow_valve, outflow_valve
                    )
                    log_event("SYSTEM", "System in emergency stop mode", "emergency_state")
                
                update_water_level(current_level, 
                                  tank.inflow, 
                                  tank.outflow, 
                                  emergency_state=True, 
                                  new_pressure=current_pressure,
                                  new_inflow_valve=inflow_valve,
                                  new_outflow_valve=outflow_valve,
                                  controller_message="EMERGENCY STOP ACTIVE - Controller disabled",
                                  outflow_message=outflow_message)
                time.sleep(1)
                continue
                
            # Normal operation mode
            # Update water tank state
            current_level = tank.update(dt=1)
            current_pressure = tank.get_pressure()
            inflow_valve = tank.get_inflow_valve_position()
            outflow_valve = tank.get_outflow_valve_position()
            
            # Log water level, pressure, and valve positions
            print(f"Water Tank Level: {current_level:.1f}, Pressure: {current_pressure:.1f} psi")
            print(f"Valve Positions - Inflow: {inflow_valve:.2f}, Outflow: {outflow_valve:.2f}")
            
            # Get controller message
            if simulation_controller:
                controller_message = simulation_controller.get_last_message()
            else:
                controller_message = "No active controller"
                
            # Get last outflow event message
            outflow_message = tank.get_last_outflow_event()
            
            # Security: Enhanced logging and anomaly detection if enabled
            if security_active:
                # Enhanced logging
                log_sensor_reading("water_level", current_level, "units")
                log_sensor_reading("pressure", current_pressure, "psi")
                log_system_state(
                    current_level, current_pressure, 
                    tank.inflow, tank.outflow,
                    inflow_valve, outflow_valve
                )
                
                # Anomaly detection
                if anomaly_detector:
                    reported_level = current_level
                    # Dashboard might report a different level during attack
                    try:
                        from scada_ui.dashboard import water_level as reported_level
                    except ImportError:
                        reported_level = current_level
                    
                    # Use reported level and actual level for anomaly detection
                    anomaly_detected, anomaly_details = anomaly_detector.update(
                        reported_level, current_pressure, tank.inflow, tank.outflow
                    )
                    
                    if anomaly_detected:
                        print(f"[SECURITY] Anomaly detected: {anomaly_details}")
                        log_security_event("Anomaly detected", "WARNING", anomaly_details)
                        
                        # If significant discrepancy between reported and actual level, could be an attack
                        if abs(reported_level - current_level) > 5.0:
                            log_security_event("Possible false data injection attack", "HIGH", {
                                "reported_level": reported_level,
                                "actual_level": current_level,
                                "difference": reported_level - current_level
                            })
                
            # Update UI with all sensor readings, actuator positions, and messages
            update_water_level(current_level, 
                              tank.inflow, 
                              tank.outflow, 
                              emergency_state=False, 
                              new_pressure=current_pressure,
                              new_inflow_valve=inflow_valve,
                              new_outflow_valve=outflow_valve,
                              controller_message=controller_message,
                              outflow_message=outflow_message)
                              
            # Debug print the levels for comparison
            print_levels()
            
            # Basic safety checks
            if current_level <= 0 or current_level >= tank.capacity:
                log_anomaly(f"Tank level out of bounds: {current_level}")
                if security_active:
                    log_security_event("Tank level out of bounds", "HIGH", {"level": current_level})
                
            # Check pressure threshold (assuming maximum safe pressure is 9 psi)
            if current_pressure > 9.0:
                log_anomaly(f"Pressure exceeded safe threshold: {current_pressure:.1f} psi")
                if security_active:
                    log_security_event("Pressure threshold exceeded", "HIGH", {"pressure": current_pressure})
                
            # Check if tank has exploded
            if hasattr(tank, 'has_exploded') and tank.has_exploded:
                emergency_stop_flag = True
                system_status = "CATASTROPHIC FAILURE: TANK EXPLOSION"
                log_anomaly("CATASTROPHIC FAILURE: Tank has exploded due to excessive pressure!")
                if security_active:
                    log_security_event("Tank explosion", "CRITICAL", {"pressure": current_pressure})
                
                # Allow Ctrl+C to work during explosion
                try:
                    time.sleep(1)  # Short sleep to allow interruption
                except KeyboardInterrupt:
                    print("Explosion simulation terminated by user.")
                    return
            
            try:
                time.sleep(1)
            except KeyboardInterrupt:
                print("Simulation terminated by user.")
                return
    except KeyboardInterrupt:
        print("Simulation terminated by user.")
        return


# Global variables for control functionality
emergency_stop_flag = False
simulation_controller = None
simulation_tank = None
system_status = "Running"


# Emergency stop and resume handlers for Flask
@app.route('/api/emergency-stop', methods=['POST'])
def handle_emergency_stop():
    global emergency_stop_flag, simulation_controller, simulation_tank, system_status
    global security_active, command_authenticator
    from flask import jsonify, request
    
    # Security: Command authentication for emergency stop if security is active
    if security_active and command_authenticator:
        try:
            # Get system state for validation
            system_state = {
                "tank_level": simulation_tank.get_level() if simulation_tank else 0,
                "pressure": simulation_tank.get_pressure() if simulation_tank else 0,
                "current_inflow": simulation_tank.inflow if simulation_tank else 0,
                "current_outflow": simulation_tank.outflow if simulation_tank else 0,
                "is_emergency": emergency_stop_flag
            }
            
            # Create signed command
            command = "emergency_stop"
            parameters = {}
            user = request.json.get("user", "operator") if request.json else "operator"
            
            # Check if command is authenticated
            authenticated, reason = command_authenticator.authenticate_command(
                command_authenticator.sign_command(command, parameters, user),
                system_state
            )
            
            if not authenticated:
                log_security_event("Unauthorized emergency stop attempt", "HIGH", {
                    "user": user,
                    "reason": reason
                })
                return jsonify({
                    'status': 'error', 
                    'message': f'Authentication failed: {reason}'
                }), 403
            
            # Command is authenticated, log the action
            log_control_action("emergency_stop", "activate", True)
        except Exception as e:
            print(f"Error in command authentication: {e}")
            # Continue with emergency stop even if authentication fails
            if security_active:
                log_security_event("Authentication error during emergency stop", "HIGH", {"error": str(e)})
    
    print("EMERGENCY STOP ACTIVATED VIA API")
    log_anomaly("Emergency stop button activated via dashboard")
    
    # Security: Log the emergency stop event with enhanced logging if enabled
    if security_active:
        log_event("CONTROL", "Emergency stop activated", "emergency_action")
    
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
    global security_active, command_authenticator
    from flask import jsonify, request
    
    if not emergency_stop_flag:
        # Already running
        return jsonify({'status': 'warning', 'message': 'System already running'})
    
    # Security: Command authentication for resume operation if security is active
    if security_active and command_authenticator:
        try:
            # Get system state for validation
            system_state = {
                "tank_level": simulation_tank.get_level() if simulation_tank else 0,
                "pressure": simulation_tank.get_pressure() if simulation_tank else 0,
                "current_inflow": simulation_tank.inflow if simulation_tank else 0,
                "current_outflow": simulation_tank.outflow if simulation_tank else 0,
                "is_emergency": emergency_stop_flag
            }
            
            # Create signed command
            command = "resume_operation"
            parameters = {}
            user = request.json.get("user", "operator") if request.json else "operator"
            
            # Check if command is authenticated
            authenticated, reason = command_authenticator.authenticate_command(
                command_authenticator.sign_command(command, parameters, user),
                system_state
            )
            
            if not authenticated:
                if security_active:
                    log_security_event("Unauthorized resume operation attempt", "HIGH", {
                        "user": user,
                        "reason": reason
                    })
                return jsonify({
                    'status': 'error', 
                    'message': f'Authentication failed: {reason}'
                }), 403
            
            # Command is authenticated, log the action
            if security_active:
                log_control_action("resume_operation", "activate", True)
        except Exception as e:
            print(f"Error in command authentication: {e}")
            # Continue with resume operation even if authentication fails
            if security_active:
                log_security_event("Authentication error during resume operation", "HIGH", {"error": str(e)})
    
    print("RESUMING OPERATIONS VIA API")
    log_anomaly("System operations resumed via dashboard")
    
    # Security: Log the resume operation event with enhanced logging if enabled
    if security_active:
        log_event("CONTROL", "System operations resumed", "emergency_action")
    
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
    global system_status, security_active
    from flask import jsonify
    
    return jsonify({
        'status': system_status,
        'emergency_stop': emergency_stop_flag,
        'security_active': security_active
    })


# Add new API endpoint for security status
@app.route('/api/security-status')
def get_security_status():
    global security_active, anomaly_detector
    from flask import jsonify
    
    # Get anomaly detector status if available
    anomaly_status = "Not active"
    if security_active and anomaly_detector:
        try:
            anomaly_status = anomaly_detector.get_status_report()
        except Exception as e:
            anomaly_status = f"Error: {str(e)}"
    
    return jsonify({
        'security_active': security_active,
        'anomaly_detection': anomaly_status
    })


def initialize_security(active=True):
    """Initialize all security components"""
    global security_active, anomaly_detector, command_authenticator, security_imports_available
    
    if not security_imports_available:
        print("[SECURITY] Security imports not available. Make sure the 'defenses' package is installed.")
        print("[SECURITY] Try running: 'python -c \"import sys; print(sys.path)\"' to check your Python path")
        print("[SECURITY] The current directory should be in the path")
        return False
    
    print(f"[SECURITY] {'Activating' if active else 'Deactivating'} security systems")
    
    # Only initialize if activating
    if active:
        try:
            # Create data directories if needed
            os.makedirs('data', exist_ok=True)
            os.makedirs('data/audit', exist_ok=True)
            os.makedirs('data/evaluation', exist_ok=True)
            
            print("[SECURITY] 1. Setting up audit logging...")
            # Initialize enhanced logging
            setup_audit_logging()
            log_event("SYSTEM", "Security systems initializing", "system_init")
            
            print("[SECURITY] 2. Initializing anomaly detection...")
            # Initialize anomaly detection
            anomaly_detector = AnomalyDetector()
            
            print("[SECURITY] 3. Setting up command authentication...")
            # Initialize command authentication
            command_authenticator = CommandAuthenticator()
            command_authenticator.set_validation_callback(system_state_validator)
            
            # Log successful initialization
            log_event("SYSTEM", "Security systems initialized successfully", "system_init")
            security_active = True
            print("[SECURITY] Security systems activated successfully")
        except Exception as e:
            print(f"[SECURITY] Error initializing security systems: {e}")
            import traceback
            traceback.print_exc()
            security_active = False
    else:
        security_active = False
        anomaly_detector = None
        command_authenticator = None
        print("[SECURITY] Security systems deactivated")
    
    return security_active


def main():
    global simulation_controller, simulation_tank, emergency_stop_flag, system_status, security_active
    
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description='SecureSim - Industrial Control System Security Simulator')
    parser.add_argument('--random_outflow', action='store_true', help="enable random outflow events")
    parser.add_argument('--security', action='store_true', help="enable enhanced security features")
    args = parser.parse_args()
    
    # Initialize logging
    console_log_file = setup_console_logging()
    setup_logging()
    
    # Initialize security if requested
    if args.security:
        initialize_security(True)
        print("[MAIN] Enhanced security features enabled")
    
    # Reset global state
    emergency_stop_flag = False
    system_status = "Running"
    
    # Initialize the water tank simulation
    tank = WaterTank(capacity=100.0, initial_level=10.0, random_outflow=args.random_outflow)
    simulation_tank = tank
    
    # Set the true water level access function for the API
    api_get_true_water_level.getter = lambda: tank.get_level()
    
    # Start the control logic
    controller = Controller(tank, setpoint=50.0)
    simulation_controller = controller
    controller.start()
    
    # Security: Log controller initiation
    if security_active:
        log_event("SYSTEM", "Controller started", "system_init", 
                 {"setpoint": controller.setpoint})
    
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
        
        # Security: Log system shutdown
        if security_active:
            log_event("SYSTEM", "System shutting down", "system_shutdown")


if __name__ == "__main__":
    main()