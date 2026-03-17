import unittest
from unittest.mock import MagicMock, patch
import sys
import os

# Add parent directory to path to import main
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mock TKINTER_AVAILABLE and other windows-specific things before importing OverlayApp
with patch('main.TKINTER_AVAILABLE', True), \
     patch('ctypes.windll', create=True), \
     patch('tkinter.Tk', MagicMock()), \
     patch('tkinter.Frame', MagicMock()), \
     patch('tkinter.Label', MagicMock()), \
     patch('tkinter.Canvas', MagicMock()):
    from main import OverlayApp

class TestOverlay(unittest.TestCase):

    @patch('main.tk.Tk')
    @patch('main.ctypes.windll', create=True)
    def test_format_time(self, mock_windll, mock_tk):
        # Mock the root object
        mock_root = MagicMock()
        mock_root.winfo_screenwidth.return_value = 1920

        # Instantiate OverlayApp - we need to mock internal methods that call tkinter/ctypes
        with patch.object(OverlayApp, 'setup_ui'), \
             patch.object(OverlayApp, 'make_click_through'), \
             patch.object(OverlayApp, 'udp_loop'), \
             patch.object(OverlayApp, 'update_ui'):
            app = OverlayApp(mock_root)

        # Test Cases
        self.assertEqual(app.format_time(None), "--:--")
        self.assertEqual(app.format_time(0), "--:--")
        self.assertEqual(app.format_time(-5), "--:--")

        # 1 minute, 1 second, 500ms
        self.assertEqual(app.format_time(61.5), "1:01.500")

        # 59.999 seconds
        self.assertEqual(app.format_time(59.999), "0:59.999")

        # Exactly 1 hour (3600 seconds) - though Dash usually gives lap times
        # 3600 / 60 = 60 minutes
        self.assertEqual(app.format_time(3600.0), "60:00.000")

if __name__ == '__main__':
    unittest.main()
