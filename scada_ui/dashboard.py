# week_1/scada_ui/dashboard.py
from flask import Flask, render_template_string, jsonify
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
                      <h5>Inflow Rate: <span id="inflow-rate">2.0</span> units/sec</h5>
                    </div>
                    <div class="col-md-6">
                      <h5>Outflow Rate: <span id="outflow-rate">2.0</span> units/sec</h5>
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
          const controlProgressElement = document.getElementById('control-progress');

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
                
                // Get real inflow/outflow values from API
                inflowRateElement.innerText = data.inflow.toFixed(1);
                outflowRateElement.innerText = data.outflow.toFixed(1);
                
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
        </script>
      </body>
    </html>
    """
    return render_template_string(html, level=water_level)


@app.route('/api/water-level')
def api_water_level():
    global history, timestamps, tank_inflow, tank_outflow
    
    return jsonify({
        'level': water_level,
        'history': history,
        'timestamps': timestamps,
        'inflow': tank_inflow,
        'outflow': tank_outflow
    })


def update_water_level(new_level, inflow=None, outflow=None):
    global water_level, history, timestamps, tank_inflow, tank_outflow
    water_level = new_level
    
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