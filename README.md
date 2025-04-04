# Water Tank Control System (Week 1)

A simulation of an industrial water tank control system with monitoring dashboard.

## Overview

This is the Week 1 submission for the securesim industrial control system project.
It focuses on system modeling and control logic, providing:

1. A simulated water tank with inflow/outflow dynamics
2. Basic control logic to maintain water level setpoint
3. A web-based dashboard for monitoring

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

## Features

- **Physical Process Simulation**: Realistic water tank with inflow/outflow dynamics
- **Control Logic**: Proportional controller to maintain target level
- **Real-time Dashboard**: Web interface showing tank level, history chart, and system status
- **Event Logging**: Basic logging of system events and anomalies

## Project Structure

```
week_1/
├── control_logic/   # Control system logic
├── data/            # Log files
├── process_sim/     # Water tank simulation
├── scada_ui/        # Web dashboard
├── tests/           # Unit tests
├── main.py          # Main application
└── README.md        # Documentation
```