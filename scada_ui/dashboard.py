# week_1/scada_ui/dashboard.py
from flask import Flask, render_template_string, jsonify, request
import threading
import time
import re
from datetime import datetime

app = Flask(__name__)


# Global variables to store water level and flow rates
water_level = 10.0
actual_water_level = 10.0
tank_inflow = 0.0
tank_outflow = 0.0
pressure = 1.0  # Initial pressure value
inflow_valve_position = 0.0  # Initial inflow valve position (0-1)
outflow_valve_position = 0.0  # Initial outflow valve position (0-1)
controller_status = "Initializing controller"  # Controller status message
outflow_status = "Random outflow enabled - varies automatically"  # Outflow status message
current_time = datetime.now().strftime('%H:%M:%S')
timestamps = [current_time] * 5  # Pre-populate with initial timestamps
history = [water_level] * 5  # Pre-populate with initial water level
MAX_HISTORY = 30  # Set history size to 30 data points

# Clear log file at startup to remove old events
def clear_old_log_entries():
    try:
        with open('data/simulation.log', 'w') as f:
            f.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')},000:INFO:Log file cleared for new session.\n")
    except Exception as e:
        print(f"Error clearing log file: {e}")

# Clear log at startup
clear_old_log_entries()


@app.route('/')
def dashboard():
    html = """
    <!DOCTYPE html>
    <html>
      <head>
        <title>Week 1 - Water Tank Simulation</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/css/bootstrap.min.css" rel="stylesheet">
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <style>
          body {
            background-color: #f8f9fa;
          }
          .dashboard-container {
            max-width: 1000px;
            margin: 50px auto;
            padding: 20px;
            background-color: white;
            border-radius: 10px;
            box-shadow: 0 0 15px rgba(0,0,0,0.1);
          }
          .tank-container {
            margin: 20px auto;
            width: 200px;
            height: 300px;
            border: 5px solid #343a40;
            border-top: 2px solid #343a40;
            border-radius: 0 0 15px 15px;
            position: relative;
            overflow: hidden;
          }
          .water {
            background: linear-gradient(to bottom, #4dabf7 0%, #3a8bd8 100%);
            width: 100%;
            position: absolute;
            bottom: 0;
            transition: height 0.5s ease-in-out;
          }
          .tank-markers {
            position: absolute;
            width: 100%;
            height: 100%;
          }
          .tank-marker {
            position: absolute;
            width: 10px;
            height: 1px;
            background-color: rgba(0,0,0,0.2);
            left: 0;
          }
          .tank-marker-label {
            position: absolute;
            left: -25px;
            font-size: 12px;
          }
          .card {
            margin-bottom: 20px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.05);
          }
          .refresh-time {
            font-size: 12px;
            color: #6c757d;
          }
          .chart-container {
            position: relative;
            height: 300px;
          }
        </style>
      </head>
      <body>
        <div class="container dashboard-container">
          <div class="row mb-3">
            <div class="col text-center">
              <h1 class="fw-bold text-primary">Water Tank Control System</h1>
              <p class="text-secondary">Week 1 - System Modeling & Control Logic</p>
              <p class="refresh-time">Last updated: <span id="update-time"></span></p>
              <div class="d-flex justify-content-center">
                <button id="emergency-stop" class="btn btn-danger btn-lg mt-2 me-2">
                  <span class="fs-4">⚠️ EMERGENCY STOP</span>
                </button>
                <button id="resume-operation" class="btn btn-success btn-lg mt-2 ms-2" disabled>
                  <span class="fs-4">▶️ RESUME OPERATION</span>
                </button>
              </div>
              <div class="alert mt-3" id="system-status-alert" role="alert">
                System Status: <strong id="system-status">Running</strong>
              </div>
            </div>
          </div>
          
          <div class="row">
            <div class="col-md-6">
              <div class="card">
                <div class="card-header bg-primary text-white">
                  <h5 class="mb-0">Water Tank Level</h5>
                </div>
                <div class="card-body text-center">
                  <div class="tank-container">
                    <div class="tank-markers" id="tank-markers"></div>
                    <div class="water" id="water-level"></div>
                  </div>
                  <h3 class="mt-3"><span id="level-value" class="text-primary">{{ level }}</span> units</h3>
                </div>
              </div>
            </div>

            <div class="col-md-6">
              <div class="card">
                <div class="card-header bg-primary text-white d-flex justify-content-between">
                  <h5 class="mb-0">Level History</h5>
                  <small class="text-white">Showing <span id="history-points">0</span> data points</small>
                </div>
                <div class="card-body">
                  <div class="chart-container">
                    <canvas id="chart"></canvas>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div class="row mt-4">
            <div class="col-md-12">
              <div class="card">
                <div class="card-header bg-success text-white">
                  <h5 class="mb-0">System Status</h5>
                </div>
                <div class="card-body">
                  <div class="row">
                    <div class="col-md-6">
                      <div class="card mb-3 border-primary">
                        <div class="card-header bg-primary text-white">
                          <h5 class="mb-0">Inflow Valve</h5>
                        </div>
                        <div class="card-body">
                          <div class="d-flex align-items-center mb-2">
                            <h5 class="mb-0 me-2">Flow Rate:</h5>
                            <h5 class="mb-0 text-primary"><span id="inflow-rate">1.10</span> units/sec</h5>
                          </div>
                          <div class="d-flex align-items-center mb-3">
                            <h5 class="mb-0 me-2">Valve Position:</h5>
                            <h5 class="mb-0 text-primary"><span id="inflow-valve">0.22</span></h5>
                          </div>
                          <div class="progress" style="height: 30px;">
                            <div id="inflow-valve-indicator" class="progress-bar bg-primary" role="progressbar" 
                                style="width: 22%;" aria-valuenow="22" aria-valuemin="0" aria-valuemax="100">
                              22% Open
                            </div>
                          </div>
                          <div class="mt-2 text-center">
                            <small class="text-muted">Last adjustment: <span id="inflow-message">Adjusting inflow valve based on level error of -13.98</span></small>
                          </div>
                        </div>
                      </div>
                    </div>
                    <div class="col-md-6">
                      <div class="card mb-3 border-danger">
                        <div class="card-header bg-danger text-white">
                          <h5 class="mb-0">Outflow Valve</h5>
                        </div>
                        <div class="card-body">
                          <div class="d-flex align-items-center mb-2">
                            <h5 class="mb-0 me-2">Flow Rate:</h5>
                            <h5 class="mb-0 text-danger"><span id="outflow-rate">1.00</span> units/sec</h5>
                          </div>
                          <div class="d-flex align-items-center mb-3">
                            <h5 class="mb-0 me-2">Valve Position:</h5>
                            <h5 class="mb-0 text-danger"><span id="outflow-valve">0.20</span></h5>
                          </div>
                          <div class="progress" style="height: 30px;">
                            <div id="outflow-valve-indicator" class="progress-bar bg-danger" role="progressbar" 
                                style="width: 20%;" aria-valuenow="20" aria-valuemin="0" aria-valuemax="100">
                              20% Open
                            </div>
                          </div>
                          <div class="mt-2 text-center">
                            <small class="text-muted" id="outflow-message">Random outflow enabled - varies automatically</small>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                  <div class="row">
                    <div class="col-md-12">
                      <div class="card mb-3 border-success">
                        <div class="card-header bg-success text-white">
                          <h5 class="mb-0">Pressure Sensor</h5>
                        </div>
                        <div class="card-body">
                          <div class="d-flex align-items-center justify-content-center">
                            <h4 class="mb-0 text-success"><span id="pressure-value">1.0</span> psi</h4>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                  <div class="mt-3">
                    <div class="progress" style="height: 25px;">
                      <div id="control-progress" class="progress-bar progress-bar-striped progress-bar-animated" 
                           role="progressbar" style="width: 50%;" aria-valuenow="50" aria-valuemin="0" aria-valuemax="100">
                        Control at 50%
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <script>
          // Initial water level rendering
          const waterLevel = {{ level }};
          const levelElement = document.getElementById('level-value');
          const waterElement = document.getElementById('water-level');
          const updateTimeElement = document.getElementById('update-time');
          const historyPointsElement = document.getElementById('history-points');
          const inflowRateElement = document.getElementById('inflow-rate');
          const outflowRateElement = document.getElementById('outflow-rate');
          const inflowValveElement = document.getElementById('inflow-valve');
          const outflowValveElement = document.getElementById('outflow-valve');
          const inflowValveIndicator = document.getElementById('inflow-valve-indicator');
          const outflowValveIndicator = document.getElementById('outflow-valve-indicator');
          const inflowMessageElement = document.getElementById('inflow-message');
          const outflowMessageElement = document.getElementById('outflow-message');
          const pressureElement = document.getElementById('pressure-value');
          const controlProgressElement = document.getElementById('control-progress');
          const systemStatusEl = document.getElementById('system-status');
          const systemStatusAlert = document.getElementById('system-status-alert');

          // Create tank markers for main tank
          const tankMarkers = document.getElementById('tank-markers');
          for (let i = 0; i <= 10; i++) {
            const marker = document.createElement('div');
            marker.className = 'tank-marker';
            marker.style.bottom = `${i * 10}%`;

            const label = document.createElement('div');
            label.className = 'tank-marker-label';
            label.style.bottom = `${i * 10}%`;
            label.innerText = (10 - i) * 10;

            tankMarkers.appendChild(marker);
            tankMarkers.appendChild(label);
          }

          // Initialize empty chart
          const ctx = document.getElementById('chart').getContext('2d');
          const chart = new Chart(ctx, {
            type: 'line',
            data: {
              labels: Array(30).fill(''),
              datasets: [
                {
                  label: 'Water Level',
                  data: Array(30).fill(null),
                  borderColor: '#4dabf7',
                  tension: 0.2,
                  fill: true,
                  backgroundColor: 'rgba(77, 171, 247, 0.1)'
                }
              ]
            },
            options: {
              responsive: true,
              maintainAspectRatio: false,
              scales: {
                y: {
                  beginAtZero: true,
                  max: 100,
                  title: {
                    display: true,
                    text: 'Water Level (units)'
                  }
                },
                x: {
                  title: {
                    display: true,
                    text: 'Time'
                  },
                  ticks: {
                    maxRotation: 45,
                    minRotation: 45
                  }
                }
              },
              animation: {
                duration: 500
              },
              plugins: {
                tooltip: {
                  callbacks: {
                    title: function(tooltipItems) {
                      return tooltipItems[0].label || 'Unknown time';
                    }
                  }
                }
              }
            }
          });

          // Update function
          function updateDashboard() {
            fetch('/api/water-level')
              .then(response => response.json())
              .then(data => {
                // Update main water level display
                const newLevel = data.level;
                const height = Math.min(Math.max(newLevel, 0), 100);
                
                // Update main display
                waterElement.style.height = `${height}%`;
                levelElement.innerText = newLevel.toFixed(2);
                
                // Update time
                const currentTime = new Date().toLocaleTimeString();
                updateTimeElement.innerText = currentTime;
                
                // Get real inflow/outflow and pressure values from API
                inflowRateElement.innerText = data.inflow.toFixed(2);
                outflowRateElement.innerText = data.outflow.toFixed(2);
                
                // Update valve positions
                const inflowValvePos = data.inflow_valve_position;
                const outflowValvePos = data.outflow_valve_position;
                
                inflowValveElement.innerText = inflowValvePos.toFixed(2);
                outflowValveElement.innerText = outflowValvePos.toFixed(2);
                
                // Update valve position indicators
                const inflowPercent = Math.round(inflowValvePos * 100);
                const outflowPercent = Math.round(outflowValvePos * 100);
                
                inflowValveIndicator.style.width = `${inflowPercent}%`;
                inflowValveIndicator.innerText = `${inflowPercent}% Open`;
                inflowValveIndicator.setAttribute('aria-valuenow', inflowPercent);
                
                outflowValveIndicator.style.width = `${outflowPercent}%`;
                outflowValveIndicator.innerText = `${outflowPercent}% Open`;
                outflowValveIndicator.setAttribute('aria-valuenow', outflowPercent);
                
                // Display controller message from API
                inflowMessageElement.innerText = data.controller_message || 'No controller status';
                
                // Display outflow message from API
                outflowMessageElement.innerText = data.outflow_message || 'Random outflow enabled';
                
                pressureElement.innerText = data.pressure.toFixed(1);
                
                // Update system status display
                systemStatusEl.innerText = data.system_status || "Running";
                systemStatusAlert.className = data.is_emergency || data.system_status === "Emergency Stop" 
                    ? 'alert alert-danger mt-3' 
                    : 'alert alert-success mt-3';
                
                // Update button states based on system status
                const emergencyStopBtn = document.getElementById('emergency-stop');
                const resumeOperationBtn = document.getElementById('resume-operation');
                
                if (data.is_emergency || data.system_status === 'Emergency Stop') {
                  emergencyStopBtn.disabled = true;
                  resumeOperationBtn.disabled = false;
                  
                  // Show emergency status on progress bar
                  controlProgressElement.className = "progress-bar progress-bar-striped progress-bar-animated bg-danger";
                  controlProgressElement.style.width = "100%";
                  controlProgressElement.innerText = "EMERGENCY SHUTDOWN ACTIVE";
                } else {
                  emergencyStopBtn.disabled = false;
                  resumeOperationBtn.disabled = true;
                  
                  // Simulate control activity (just visual feedback for week 1)
                  const controlPct = Math.min(100, Math.max(0, 50 + (newLevel - 50) * 2));
                  controlProgressElement.style.width = `${controlPct}%`;
                  controlProgressElement.innerText = `Control at ${Math.round(controlPct)}%`;
                  
                  if (controlPct > 70) {
                    controlProgressElement.className = "progress-bar progress-bar-striped progress-bar-animated bg-danger";
                  } else if (controlPct < 30) {
                    controlProgressElement.className = "progress-bar progress-bar-striped progress-bar-animated bg-warning";
                  } else {
                    controlProgressElement.className = "progress-bar progress-bar-striped progress-bar-animated bg-success";
                  }
                }

                // Update history counter
                historyPointsElement.innerText = data.history.length;

                // Update chart with dataset and timestamps
                chart.data.datasets[0].data = data.history;
                chart.data.labels = data.timestamps;
                chart.update();
              });
          }

          // Initial rendering
          waterElement.style.height = `${Math.min(Math.max(waterLevel, 0), 100)}%`;
          updateTimeElement.innerText = new Date().toLocaleTimeString();

          // Periodic updates
          setInterval(updateDashboard, 1000);
          
          // Emergency stop button functionality
          document.getElementById('emergency-stop').addEventListener('click', function() {
            if (confirm('Are you sure you want to activate the EMERGENCY STOP?')) {
              fetch('/api/emergency-stop', {
                method: 'POST',
                headers: {
                  'Content-Type': 'application/json'
                },
                body: JSON.stringify({action: 'emergency_stop'})
              }).then(response => response.json())
                .then(data => {
                  console.log('Emergency stop response:', data);
                  alert('Emergency stop activated!');
                  // Visual feedback
                  document.body.style.backgroundColor = '#ffe6e6';
                  
                  // Update button state
                  this.disabled = true;
                  document.getElementById('resume-operation').disabled = false;
                  
                  // Add a system status message
                  const statusEl = document.getElementById('control-progress');
                  statusEl.className = "progress-bar progress-bar-striped progress-bar-animated bg-danger";
                  statusEl.style.width = "100%";
                  statusEl.innerText = "EMERGENCY SHUTDOWN IN PROGRESS";
                  
                  // Update system status display
                  const systemStatusEl = document.getElementById('system-status');
                  const systemStatusAlert = document.getElementById('system-status-alert');
                  systemStatusEl.innerText = "Emergency Stop";
                  systemStatusAlert.className = 'alert alert-danger mt-3';
                })
                .catch(error => {
                  console.error('Error:', error);
                  alert('Failed to activate emergency stop!');
                });
            }
          });
          
          // Resume operation button functionality
          document.getElementById('resume-operation').addEventListener('click', function() {
            if (confirm('Are you sure you want to RESUME OPERATIONS?')) {
              fetch('/api/resume-operation', {
                method: 'POST',
                headers: {
                  'Content-Type': 'application/json'
                },
                body: JSON.stringify({action: 'resume_operation'})
              }).then(response => response.json())
                .then(data => {
                  console.log('Resume operation response:', data);
                  alert('System operations resumed!');
                  // Visual feedback
                  document.body.style.backgroundColor = '#f8f9fa';
                  
                  // Update button state
                  this.disabled = true;
                  document.getElementById('emergency-stop').disabled = false;
                  
                  // Add a system status message
                  const statusEl = document.getElementById('control-progress');
                  statusEl.className = "progress-bar progress-bar-striped progress-bar-animated bg-success";
                  statusEl.style.width = "50%";
                  statusEl.innerText = "Control at 50%";
                  
                  // Update system status display
                  const systemStatusEl = document.getElementById('system-status');
                  const systemStatusAlert = document.getElementById('system-status-alert');
                  systemStatusEl.innerText = "Running";
                  systemStatusAlert.className = 'alert alert-success mt-3';
                })
                .catch(error => {
                  console.error('Error:', error);
                  alert('Failed to resume operations!');
                });
            }
          });
        </script>
      </body>
    </html>
    """
    return render_template_string(html, level=water_level)


@app.route('/api/water-level')
def api_water_level():
    global history, timestamps, tank_inflow, tank_outflow, system_status, is_emergency, pressure
    global inflow_valve_position, outflow_valve_position, controller_status, outflow_status
    
    return jsonify({
        'level': water_level,
        'history': history,
        'timestamps': timestamps,
        'inflow': tank_inflow,
        'outflow': tank_outflow,
        'system_status': system_status,
        'is_emergency': is_emergency,
        'pressure': pressure,
        'inflow_valve_position': inflow_valve_position,
        'outflow_valve_position': outflow_valve_position,
        'controller_message': controller_status,
        'outflow_message': outflow_status
    })


# Emergency stop is now handled directly in main.py


# Add system status variables
system_status = "Running"
is_emergency = False

def update_water_level(new_level, inflow=None, outflow=None, emergency_state=False, new_pressure=None, 
                     new_inflow_valve=None, new_outflow_valve=None, controller_message=None, outflow_message=None):
    global water_level, history, timestamps, tank_inflow, tank_outflow, controller_status, outflow_status
    global system_status, is_emergency, pressure, inflow_valve_position, outflow_valve_position
    
    water_level = new_level
    
    # Update pressure if provided, otherwise calculate from water level
    if new_pressure is not None:
        pressure = new_pressure
    else:
        # Simple pressure calculation (similar to the one in water_tank.py)
        pressure = new_level * 0.1
    
    # Update valve positions if provided
    if new_inflow_valve is not None:
        inflow_valve_position = new_inflow_valve
    else:
        # Calculate valve position from flow rate
        inflow_valve_position = min(1.0, max(0.0, inflow / 5.0)) if inflow is not None else inflow_valve_position
        
    if new_outflow_valve is not None:
        outflow_valve_position = new_outflow_valve
    else:
        # Calculate valve position from flow rate
        outflow_valve_position = min(1.0, max(0.0, outflow / 5.0)) if outflow is not None else outflow_valve_position
    
    # Update controller message if provided
    if controller_message is not None:
        controller_status = controller_message
        
    # Update outflow message if provided
    if outflow_message is not None:
        outflow_status = outflow_message
        
    # Update emergency flag and system status
    is_emergency = emergency_state
    if emergency_state:
        system_status = "Emergency Stop"
    else:
        system_status = "Running"
    
    # Update flow rates if provided
    if inflow is not None:
        tank_inflow = inflow
    if outflow is not None:
        tank_outflow = outflow

    # Add timestamp for this data point
    current_time = datetime.now().strftime('%H:%M:%S')
    timestamps.append(current_time)
    
    # Add to history and maintain maximum size
    history.append(new_level)
    
    if len(history) > MAX_HISTORY:
        history = history[-MAX_HISTORY:]
        timestamps = timestamps[-MAX_HISTORY:]


def run_dashboard():
    app.run(debug=True, use_reloader=False)


def start_dashboard():
    thread = threading.Thread(target=run_dashboard)
    thread.daemon = True
    thread.start()
    return thread