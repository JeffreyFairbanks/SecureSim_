
# SecureSim: Industrial Control System Security Simulator

A realistic simulation platform for industrial water tank control systems with built-in cybersecurity attack capabilities and visualization.

## Overview

SecureSim provides an educational environment for understanding SCADA/ICS security vulnerabilities. It combines a realistic water tank model with controls, a monitoring dashboard, and attack simulations for security training and testing.

### Security Testing Features

This simulation includes a simple but realistic **replay attack** capability that demonstrates a common SCADA system vulnerability:

- **Record and Replay**: Records normal system operation patterns and replays them while hiding actual system changes
- **Dual Visualization**: Dashboard shows both reported (manipulated) and actual values side-by-side
- **Real-time Comparison**: Track divergence between reported and actual system state
- **Educational Platform**: Ideal for cybersecurity training, demonstrations, and research

### Core Functionality

The system provides:

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
# Clone the repository
git clone https://github.com/yourusername/SecureSim.git
cd SecureSim

# Create and activate a virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate.bat

# Install dependencies
pip install -r requirements.txt
```

## Basic Usage

Start the water tank simulation with standard behavior:

```bash
python main.py
```

Start with random outflow variations (more realistic):

```bash
python main.py --random-outflow
```

Once running, open your browser and visit: `http://127.0.0.1:5000/`

For attack simulation instructions, see the "Running the Replay Attack Simulation" section below.

## Running the Replay Attack Simulation

The system includes a simplified SCADA replay attack implementation that demonstrates a common industrial control system vulnerability.

### Step 1: Start the Simulation

Start the water tank simulation with random outflow enabled:

```bash
python main.py --random-outflow
```

### Step 2: Record Normal System Behavior

In a separate terminal, record normal system behavior:

```bash
python attacks/simple_replay.py record --duration 30
```

This will record 30 seconds of normal system operation and save it to the `data/recorded_data.json` file.

### Step 3: Launch the Replay Attack

After recording is complete, launch the replay attack:

```bash
python attacks/simple_replay.py replay
```

This will replay the recorded data in a loop, causing the dashboard to show repeated patterns of normal operation while the actual system continues to change.

## Project Structure

```
SecureSim_/
├── attacks/         # Attack simulations
│   ├── simple_replay.py # Simplified SCADA replay attack
│   └── replay_attack.py # Advanced replay attack implementation
├── control_logic/   # Control system logic
│   └── control.py   # Proportional controller
├── data/            # Log files and attack recordings
├── process_sim/     # Physical process simulation
│   └── water_tank.py # Water tank model with sensors/actuators
├── scada_ui/        # Dashboard interface
│   └── dashboard.py # Flask-based visualization UI
├── tests/           # Unit tests
│   └── test_water_tank.py # Tests for water tank simulation
├── logging_defense.py # Logging and anomaly detection
├── main.py          # Main application
└── README.md        # Documentation
```