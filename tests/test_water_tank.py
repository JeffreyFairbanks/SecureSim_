# secure-sim/tests/test_water_tank.py
import sys
import os
import unittest

# Add the parent directory to path to allow imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from process_sim.water_tank import WaterTank


class TestWaterTank(unittest.TestCase):
    
    def setUp(self):
        self.tank = WaterTank(capacity=100.0, initial_level=50.0)
    
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


if __name__ == '__main__':
    unittest.main()