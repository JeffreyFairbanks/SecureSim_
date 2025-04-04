# secure-sim/tests/test_water_tank.py
import sys
import os
import unittest

# Add the parent directory to path to allow imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from process_sim.water_tank import WaterTank


class TestWaterTank(unittest.TestCase):
    
    def setUp(self):
        self.tank = WaterTank(capacity=100.0, initial_level=50.0, random_outflow=False)
    
    def test_initialization(self):
        """Test that the tank initializes with correct values"""
        self.assertEqual(self.tank.capacity, 100.0)
        self.assertEqual(self.tank.level, 50.0)
        self.assertEqual(self.tank.inflow, 0.0)
        self.assertEqual(self.tank.outflow, 0.0)
    
    def test_update_level(self):
        """Test that the tank level updates correctly with inflow/outflow"""
        self.tank.set_inflow(5.0)
        self.tank.set_outflow(2.0)
        
        # Net change should be +3.0 per time unit
        new_level = self.tank.update(dt=1.0)
        self.assertEqual(new_level, 53.0)
        
        # Another update should add another 3.0
        new_level = self.tank.update(dt=1.0)
        self.assertEqual(new_level, 56.0)
    
    def test_level_clamping(self):
        """Test that the tank level doesn't exceed capacity or go below zero"""
        # Test max capacity
        self.tank.level = 95.0
        self.tank.set_inflow(10.0)
        self.tank.set_outflow(0.0)
        
        new_level = self.tank.update(dt=1.0)
        self.assertEqual(new_level, 100.0)  # Should be clamped at capacity
        
        # Test minimum level
        self.tank.level = 5.0
        self.tank.set_inflow(0.0)
        self.tank.set_outflow(10.0)
        
        new_level = self.tank.update(dt=1.0)
        self.assertEqual(new_level, 0.0)  # Should be clamped at zero
    
    def test_pressure_sensor(self):
        """Test that the pressure sensor works correctly"""
        # Set a known level
        self.tank.level = 50.0
        # Call update to recalculate pressure based on the level
        self.tank.update(dt=0.0)  # Use dt=0 to avoid changing the level
        
        # Pressure should be level * 0.1 according to our calculation
        self.assertEqual(self.tank.get_pressure(), 5.0)
        
        # Test pressure with a different level
        self.tank.level = 80.0
        self.tank.update(dt=0.0)  # Use dt=0 to avoid changing the level
        self.assertEqual(self.tank.get_pressure(), 8.0)
    
    def test_valve_positions(self):
        """Test that valve positions are calculated correctly"""
        # Test inflow valve
        self.tank.set_inflow(2.5)  # 50% of max 5.0
        self.assertEqual(self.tank.get_inflow_valve_position(), 0.5)
        
        # Test max inflow valve position
        self.tank.set_inflow(5.0)  # 100% of max 5.0
        self.assertEqual(self.tank.get_inflow_valve_position(), 1.0)
        
        # Test min inflow valve position
        self.tank.set_inflow(0.0)  # 0% of max 5.0
        self.assertEqual(self.tank.get_inflow_valve_position(), 0.0)
        
        # Test outflow valve
        self.tank.set_outflow(2.5)  # 50% of max 5.0
        self.assertEqual(self.tank.get_outflow_valve_position(), 0.5)
        
        # Test values exceeding max
        self.tank.set_inflow(10.0)  # 200% of max 5.0
        self.assertEqual(self.tank.get_inflow_valve_position(), 1.0)  # Should be clamped at 1.0
    
    def test_random_outflow(self):
        """Test that random outflow mode works correctly"""
        # Create a new tank with random outflow enabled
        tank = WaterTank(capacity=100.0, initial_level=50.0, random_outflow=True)
        
        # Check that random_outflow flag is set
        self.assertTrue(tank.random_outflow)
        
        # Check that the random_outflow_thread is created and running
        self.assertIsNotNone(tank.random_outflow_thread)
        self.assertTrue(tank.random_outflow_thread.is_alive())
        
        # Check that outflow events are tracked
        self.assertIsNotNone(tank.last_outflow_event)
        
        # Stop random outflow
        tank.stop_random_outflow()
        
        # Check that random_outflow flag is unset
        self.assertFalse(tank.random_outflow)


if __name__ == '__main__':
    unittest.main()