# Water Tank Control System

A simulation of an industrial water tank control system with monitoring dashboard.

## Overview

This project provides a secure simulation environment for an industrial water tank control system.
It focuses on system modeling and control logic, providing:

1. A simulated water tank with inflow/outflow dynamics
2. Sensors (water level, pressure) and actuators (inflow valve, outflow valve)
3. Basic control logic to maintain water level setpoint
4. A web-based dashboard for monitoring and control
5. Emergency stop functionality

## Components

### Sensors
- **Water Level Sensor**: Measures the current water level in the tank (0-100 units)
- **Pressure Sensor**: Measures the water pressure in the tank (PSI)

### Actuators
- **Inflow Valve**: Controls the rate of water flowing into the tank (0-1 position)
- **Outflow Valve**: Controls the rate of water flowing out of the tank (0-1 position)

### Simulation Modes

#### Random Outflow Mode
The system can operate with random outflow variations to simulate real-world disturbances:

- Randomly changes outflow rate every 2 seconds (between 0-4 units/sec)
- Automatically adjusts outflow valve position (0-80% open)
- Visual dashboard indicators show real-time valve position changes
- Inflow valve automatically compensates to maintain target level
- Displays last outflow event message with timestamp

This mode helps simulate unpredictable external factors affecting the system, testing the controller's ability to compensate for disturbances.

## Installation

```bash
# Create and activate a virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate.bat

# Install dependencies
pip install -r requirements.txt
```

## Usage

Run the simulation:

```bash
python main.py
```

Then open your browser and go to: `http://127.0.0.1:5000/`

### Dashboard Visualization

The dashboard provides visual representations of the water tank system:

1. **Water Tank Visualization**: 
   - Animated water level display with scale markers
   - Real-time level value updates
   - Historical trend graph tracking level changes over time

2. **Valve Controls Display**:
   - Inflow valve position shown as percentage open (0-100%)
   - Outflow valve position shown as percentage open (0-100%)
   - Progress bar indicators showing valve opening
   - Real-time flow rate values for both inflow and outflow

3. **Sensor Readings**:
   - Pressure sensor readings with unit display (PSI)
   - Safety status indicators
   
4. **Control Messages**:
   - Live controller status messages showing control actions
   - Outflow event tracking for random disturbances
   - System status and emergency indicators

## Features

- **Physical Process Simulation**: Realistic water tank with inflow/outflow dynamics
- **Sensors and Actuators**: 
  - Water level sensor (measures water level from 0-100 units)
  - Pressure sensor (calculates pressure based on water level)
  - Inflow valve actuator (controlled by proportional controller)
  - Outflow valve actuator (can be set manually or operate in random mode)
- **Control Logic**: 
  - Proportional controller to maintain target water level setpoint
  - Dynamic adjustment of inflow valve based on level error
  - Random outflow simulation to model real-world disturbances
- **Advanced Monitoring Dashboard**: 
  - Real-time visualization of tank level with animated water display
  - Graphical valve position indicators showing opening percentage
  - Live pressure readings and historical trend graphs
  - Controller status and adjustment messages
  - Random outflow event tracking
- **Emergency Controls**: 
  - Emergency stop button with confirmation
  - Automatic valve control during emergency situations
  - System resumption with controlled restart
- **Safety Features**: 
  - Alerts when pressure or level exceeds safe thresholds
  - Automatic safety cutoffs during extreme conditions
  - Visual indicators for system status and warnings
- **Comprehensive Logging**: 
  - Detailed logging of system events and actuator changes
  - Anomaly detection and reporting
  - Time-stamped history of system parameters

## Project Structure

```
SecureSim_/
├── control_logic/   # Control system logic
│   └── control.py   # Proportional controller
├── data/            # Log files
├── process_sim/     # Water tank simulation with sensors and actuators
│   └── water_tank.py # Water tank model
├── scada_ui/        # Web dashboard
│   └── dashboard.py # Flask-based UI
├── tests/           # Unit tests
│   └── test_water_tank.py # Tests for water tank simulation
├── logging_defense.py # Logging utilities
├── main.py          # Main application
└── README.md        # Documentation
```