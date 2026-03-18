import unittest
import sys
import os
import json
from unittest.mock import patch, MagicMock

# Add parent directory to path to import main
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import TelemetryRequestHandler, current_telemetry, DASHBOARD_HTML

class TestTelemetryRequestHandler(unittest.TestCase):
    def setUp(self):
        # Create a mock request and client address
        self.mock_request = MagicMock()
        self.mock_client_address = ('127.0.0.1', 12345)
        self.mock_server = MagicMock()

        # We don't want the handler to actually handle the request in __init__
        # so we patch handle() which is called by BaseRequestHandler.__init__
        patcher = patch('http.server.BaseHTTPRequestHandler.handle')
        self.mock_handle = patcher.start()
        self.addCleanup(patcher.stop)

        # Initialize the handler
        self.handler = TelemetryRequestHandler(self.mock_request, self.mock_client_address, self.mock_server)

        # Replace wfile with a mock so we can capture writes
        self.handler.wfile = MagicMock()

        # Replace methods that send to the socket
        self.handler.send_response = MagicMock()
        self.handler.send_header = MagicMock()
        self.handler.end_headers = MagicMock()
        self.handler.send_error = MagicMock()

    def test_do_GET_data(self):
        # Set the path
        self.handler.path = '/data'

        # Populate current_telemetry with some dummy data
        current_telemetry['speed'] = 100.0
        current_telemetry['gear'] = '3'

        # Call the method
        self.handler.do_GET()

        # Assertions
        self.handler.send_response.assert_called_once_with(200)

        # send_header could be called multiple times
        self.handler.send_header.assert_any_call('Content-type', 'application/json')
        self.handler.send_header.assert_any_call('Access-Control-Allow-Origin', '*')

        self.handler.end_headers.assert_called_once()

        # Verify that wfile.write was called with the correct JSON payload
        expected_json = json.dumps(current_telemetry).encode()
        self.handler.wfile.write.assert_called_once_with(expected_json)

    def test_do_GET_root(self):
        self.handler.path = '/'

        self.handler.do_GET()

        self.handler.send_response.assert_called_once_with(200)
        self.handler.send_header.assert_called_once_with('Content-type', 'text/html')
        self.handler.end_headers.assert_called_once()
        self.handler.wfile.write.assert_called_once_with(DASHBOARD_HTML.encode('utf-8'))

    def test_do_GET_dashboard(self):
        self.handler.path = '/dashboard.html'

        self.handler.do_GET()

        self.handler.send_response.assert_called_once_with(200)
        self.handler.send_header.assert_called_once_with('Content-type', 'text/html')
        self.handler.end_headers.assert_called_once()
        self.handler.wfile.write.assert_called_once_with(DASHBOARD_HTML.encode('utf-8'))

    def test_do_GET_not_found(self):
        self.handler.path = '/nonexistent'

        self.handler.do_GET()

        self.handler.send_error.assert_called_once_with(404)
        self.handler.send_response.assert_not_called()
        self.handler.wfile.write.assert_not_called()

if __name__ == '__main__':
    unittest.main()
