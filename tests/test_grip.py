import struct
import unittest
import sys
import os
from unittest.mock import patch

# Add parent directory to path to import main
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import TelemetryData, Commentator

class TestGrip(unittest.TestCase):
    def create_mock_packet(self, overrides=None):
        defaults = {
            'is_race_on': 1,
            'timestamp_ms': 1000,
            'max_rpm': 8000.0,
            'idle_rpm': 1000.0,
            'cur_rpm': 4000.0,
            'accel': (0.0, 0.0, 0.0),
            'velocity': (0.0, 0.0, 0.0),
            'angular_vel': (0.0, 0.0, 0.0),
            'orientation': (0.0, 0.0, 0.0),
            'norm_suspension': (0.5, 0.5, 0.5, 0.5),
            'tire_slip_ratio': (0.0, 0.0, 0.0, 0.0),
            'wheel_rotation': (0.0, 0.0, 0.0, 0.0),
            'rumble_strip': (0, 0, 0, 0),
            'puddle_depth': (0.0, 0.0, 0.0, 0.0),
            'surface_rumble': (0.0, 0.0, 0.0, 0.0),
            'slip_angle': (0.0, 0.0, 0.0, 0.0),
            'combined_slip': (0.0, 0.0, 0.0, 0.0),
            'susp_travel_meters': (0.0, 0.0, 0.0, 0.0),
            'car_ordinal': 123,
            'car_class': 1,
            'car_perf': 500,
            'drivetrain': 1,
            'cylinders': 6,
            'position': (0.0, 0.0, 0.0),
            'speed': 30.0, # ~67 mph
            'power': 200.0,
            'torque': 300.0,
            'tire_temp': (100.0, 100.0, 100.0, 100.0),
            'boost': 0.0,
            'fuel': 1.0,
            'dist': 1000.0,
            'best_lap': 0.0,
            'last_lap': 0.0,
            'cur_lap': 0.0,
            'cur_race_time': 10.0,
            'lap_number': 1,
            'race_pos': 1,
            'input_accel': 255,
            'input_brake': 0,
            'input_clutch': 0,
            'input_handbrake': 0,
            'input_gear': 3,
            'input_steer': 0,
            'driving_line': 0,
            'ai_brake_diff': 0,
        }

        if overrides:
            defaults.update(overrides)

        # Pack data
        data = b''
        data += struct.pack('<i', defaults['is_race_on'])
        data += struct.pack('<I', defaults['timestamp_ms'])
        data += struct.pack('<3f', defaults['max_rpm'], defaults['idle_rpm'], defaults['cur_rpm'])
        data += struct.pack('<3f', *defaults['accel'])
        data += struct.pack('<3f', *defaults['velocity'])
        data += struct.pack('<3f', *defaults['angular_vel'])
        data += struct.pack('<3f', *defaults['orientation'])
        data += struct.pack('<4f', *defaults['norm_suspension'])
        data += struct.pack('<4f', *defaults['tire_slip_ratio'])
        data += struct.pack('<4f', *defaults['wheel_rotation'])
        data += struct.pack('<4i', *defaults['rumble_strip'])
        data += struct.pack('<4f', *defaults['puddle_depth'])
        data += struct.pack('<4f', *defaults['surface_rumble'])
        data += struct.pack('<4f', *defaults['slip_angle'])
        data += struct.pack('<4f', *defaults['combined_slip'])
        data += struct.pack('<4f', *defaults['susp_travel_meters'])
        data += struct.pack('<5i', defaults['car_ordinal'], defaults['car_class'], defaults['car_perf'], defaults['drivetrain'], defaults['cylinders'])
        data += struct.pack('<3f', *defaults['position'])
        data += struct.pack('<f', defaults['speed'])
        data += struct.pack('<f', defaults['power'])
        data += struct.pack('<f', defaults['torque'])
        data += struct.pack('<4f', *defaults['tire_temp'])
        data += struct.pack('<7f', defaults['boost'], defaults['fuel'], defaults['dist'], defaults['best_lap'], defaults['last_lap'], defaults['cur_lap'], defaults['cur_race_time'])
        data += struct.pack('<H', defaults['lap_number'])
        data += struct.pack('<B', defaults['race_pos'])
        data += struct.pack('<5B', defaults['input_accel'], defaults['input_brake'], defaults['input_clutch'], defaults['input_handbrake'], defaults['input_gear'])
        data += struct.pack('<b', defaults['input_steer'])
        data += struct.pack('<b', defaults['driving_line'])
        data += struct.pack('<b', defaults['ai_brake_diff'])

        # Pad to 324 bytes (standard Dash)
        padding = b'\x00' * (324 - len(data))
        data += padding

        return data

    @patch('main.time.time')
    def test_grip_commentary(self, mock_time):
        mock_time.return_value = 100.0
        commentator = Commentator()

        # Test case: Combined slip near 1.0 (limit)
        # Using 0.95 which triggers > 0.9 check
        data = self.create_mock_packet({'combined_slip': (0.95, 0.95, 0.95, 0.95)})
        packet = TelemetryData(data)

        msg = commentator.get_commentary(packet)
        self.assertIsNotNone(msg)
        self.assertIn("AT THE LIMIT", msg)

        # Test case: Low slip (no commentary)
        mock_time.return_value = 101.0
        data2 = self.create_mock_packet({'combined_slip': (0.5, 0.5, 0.5, 0.5)})
        packet2 = TelemetryData(data2)

        msg2 = commentator.get_commentary(packet2)
        # Assuming no other events trigger
        self.assertIsNone(msg2)

if __name__ == '__main__':
    unittest.main()
