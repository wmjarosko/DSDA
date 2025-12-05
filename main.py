import socket
import struct
import time
import os
import threading
import json
import csv
from http.server import HTTPServer, BaseHTTPRequestHandler

# --- CONFIGURATION ---
UDP_IP = "0.0.0.0" 
UDP_PORT = 5300
WEB_PORT = 8000 # Port for the web dashboard

# --- SHARED STATE ---
current_telemetry = {
    "rpm": 0, "speed": 0, "gear": "N", "position": 0, 
    "lap": 0, "best_lap": 0.0, "track_id": 0, "race_on": False,
    "tire_wear": [100.0, 100.0, 100.0, 100.0], # FL, FR, RL, RR
    "tire_temp": [0, 0, 0, 0] # FL, FR, RL, RR
}

TRACK_NAMES = {} 

# --- EMBEDDED HTML DASHBOARD ---
# Updated CSS for 2x2 Grid and Temperature display
DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Race Telemetry Dashboard</title>
    <style>
        body {
            background-color: #121212;
            color: #ffffff;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            height: 100vh;
        }
        
        .container {
            display: grid;
            grid-template-columns: 1fr 1fr 1fr;
            gap: 20px;
            width: 90%;
            max-width: 1000px;
        }

        .card {
            background-color: #1e1e1e;
            border-radius: 15px;
            padding: 20px;
            text-align: center;
            box-shadow: 0 4px 6px rgba(0,0,0,0.3);
            border: 1px solid #333;
            display: flex;
            flex-direction: column;
            justify-content: center;
        }

        .label {
            color: #888;
            font-size: 0.9rem;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 5px;
        }

        .value {
            font-size: 2.5rem;
            font-weight: bold;
        }

        /* Specific Highlight Styles */
        #gear-val { color: #00e5ff; font-size: 4rem; }
        #speed-val { color: #ffea00; }
        #best-lap-val { color: #00e676; } 
        
        /* 2x2 Tire Grid Layout */
        .tire-grid {
            display: grid;
            grid-template-columns: 1fr 1fr; /* 2 columns */
            grid-template-rows: 1fr 1fr;    /* 2 rows */
            gap: 15px;
            margin-top: 10px;
            justify-items: center;
        }
        
        .tire-box {
            background: #2a2a2a;
            padding: 10px;
            border-radius: 5px;
            display: flex;
            flex-direction: column;
            align-items: center;
            width: 100%;
            box-sizing: border-box;
            position: relative;
        }
        
        .tire-header {
            display: flex;
            justify-content: space-between;
            width: 100%;
            font-size: 0.8rem;
            color: #aaa;
            margin-bottom: 5px;
        }
        
        .tire-temp {
            font-size: 0.9rem;
            font-weight: bold;
            color: #fff;
        }
        
        .tire-val { 
            font-size: 0.8rem; 
            font-weight: bold; 
            margin-top: 5px;
            color: #ccc;
        }
        
        /* Vertical Bar Container */
        .tire-bar-bg { 
            background: #444; 
            width: 20px; 
            height: 50px; 
            border-radius: 3px; 
            position: relative; 
            overflow: hidden; 
            border: 1px solid #555;
        }
        /* Vertical Bar Fill */
        .tire-bar { 
            width: 100%; 
            height: 100%; 
            background: #00e676; 
            position: absolute;
            bottom: 0; 
            left: 0;
            transition: height 0.2s, background-color 0.2s; 
        }

        /* RPM Bar */
        #rpm-bar-container {
            grid-column: 1 / -1;
            background: #333;
            height: 30px;
            border-radius: 15px;
            overflow: hidden;
            margin-top: 10px;
            position: relative;
        }
        #rpm-bar {
            height: 100%;
            width: 0%;
            background: linear-gradient(90deg, #4caf50, #ffeb3b, #f44336);
            transition: width 0.1s linear;
        }
        .status-off { color: #555; }
        .status-on { color: #00e676; }

    </style>
</head>
<body>

    <div style="margin-bottom: 20px;">
        <span id="status-icon" class="status-off">●</span> 
        <span id="status-text">WAITING FOR DATA...</span>
    </div>

    <div class="container">
        <!-- Gear (Spans 2 Rows on Left) -->
        <div class="card" style="grid-row: span 2;">
            <div class="label">Gear</div>
            <div class="value" id="gear-val">-</div>
        </div>

        <!-- Speed -->
        <div class="card">
            <div class="label">Speed (MPH)</div>
            <div class="value" id="speed-val">0</div>
        </div>

        <!-- RPM Text -->
        <div class="card">
            <div class="label">RPM</div>
            <div class="value" id="rpm-val">0</div>
        </div>

        <!-- Position -->
        <div class="card">
            <div class="label">Position</div>
            <div class="value" id="pos-val">-</div>
        </div>

        <!-- Lap -->
        <div class="card">
            <div class="label">Lap</div>
            <div class="value" id="lap-val">-</div>
        </div>
        
        <!-- Best Lap -->
        <div class="card">
            <div class="label">Fastest Lap</div>
            <div class="value" id="best-lap-val">--:--</div>
        </div>

        <!-- Tire Wear & Temp Card (Spans bottom row center/right) -->
        <div class="card" style="grid-column: span 2;">
            <div class="label">Tire Condition (Wear / Temp)</div>
            <div class="tire-grid">
                <!-- FL -->
                <div class="tire-box">
                    <div class="tire-header">
                        <span>FL</span>
                        <span class="tire-temp" id="tire-fl-temp">0°</span>
                    </div>
                    <div class="tire-bar-bg"><div class="tire-bar" id="tire-fl-bar"></div></div>
                    <span class="tire-val" id="tire-fl-val">100%</span>
                </div>
                <!-- FR -->
                <div class="tire-box">
                    <div class="tire-header">
                        <span>FR</span>
                        <span class="tire-temp" id="tire-fr-temp">0°</span>
                    </div>
                    <div class="tire-bar-bg"><div class="tire-bar" id="tire-fr-bar"></div></div>
                    <span class="tire-val" id="tire-fr-val">100%</span>
                </div>
                <!-- RL -->
                <div class="tire-box">
                    <div class="tire-header">
                        <span>RL</span>
                        <span class="tire-temp" id="tire-rl-temp">0°</span>
                    </div>
                    <div class="tire-bar-bg"><div class="tire-bar" id="tire-rl-bar"></div></div>
                    <span class="tire-val" id="tire-rl-val">100%</span>
                </div>
                <!-- RR -->
                <div class="tire-box">
                    <div class="tire-header">
                        <span>RR</span>
                        <span class="tire-temp" id="tire-rr-temp">0°</span>
                    </div>
                    <div class="tire-bar-bg"><div class="tire-bar" id="tire-rr-bar"></div></div>
                    <span class="tire-val" id="tire-rr-val">100%</span>
                </div>
            </div>
        </div>

        <!-- RPM Bar -->
        <div id="rpm-bar-container">
            <div id="rpm-bar"></div>
        </div>
    </div>

    <script>
        function formatTime(seconds) {
            if (!seconds || seconds <= 0) return "--:--";
            let min = Math.floor(seconds / 60);
            let sec = Math.floor(seconds % 60);
            let ms = Math.floor((seconds * 1000) % 1000);
            return `${min}:${sec.toString().padStart(2, '0')}.${ms.toString().padStart(3, '0')}`;
        }

        function updateTire(id, pct, temp) {
            const elVal = document.getElementById(id + '-val');
            const elBar = document.getElementById(id + '-bar');
            const elTemp = document.getElementById(id + '-temp');
            
            elVal.innerText = pct.toFixed(0) + '%';
            elTemp.innerText = temp + '°';
            
            // For vertical bars, we update HEIGHT
            elBar.style.height = pct + '%';

            // Wear Color Logic
            if (pct > 70) elBar.style.backgroundColor = '#00e676'; // Green
            else if (pct > 40) elBar.style.backgroundColor = '#ffea00'; // Yellow
            else elBar.style.backgroundColor = '#f44336'; // Red
            
            // Temp Color Logic (Rough Estimates)
            if (temp > 220) elTemp.style.color = '#f44336'; // Hot
            else if (temp < 100) elTemp.style.color = '#00e5ff'; // Cold
            else elTemp.style.color = '#fff'; // Normal
        }

        async function fetchData() {
            try {
                const response = await fetch('/data');
                const data = await response.json();

                if (data.race_on) {
                    document.getElementById('status-icon').className = 'status-on';
                    document.getElementById('status-text').innerText = "RACE ACTIVE";
                } else {
                    document.getElementById('status-icon').className = 'status-off';
                    document.getElementById('status-text').innerText = "PAUSED / MENU";
                }

                document.getElementById('gear-val').innerText = data.gear;
                document.getElementById('speed-val').innerText = data.speed;
                document.getElementById('rpm-val').innerText = data.rpm;
                document.getElementById('pos-val').innerText = data.position;
                document.getElementById('lap-val').innerText = data.lap;
                document.getElementById('best-lap-val').innerText = formatTime(data.best_lap);

                // Update Tires
                if (data.tire_wear && data.tire_temp) {
                    updateTire('tire-fl', data.tire_wear[0], data.tire_temp[0]);
                    updateTire('tire-fr', data.tire_wear[1], data.tire_temp[1]);
                    updateTire('tire-rl', data.tire_wear[2], data.tire_temp[2]);
                    updateTire('tire-rr', data.tire_wear[3], data.tire_temp[3]);
                }

                let maxRpm = data.max_rpm || 8000; 
                let pct = (data.rpm / maxRpm) * 100;
                document.getElementById('rpm-bar').style.width = pct + '%';

            } catch (error) {
                console.error("Error fetching data:", error);
            }
        }

        setInterval(fetchData, 100);
    </script>
</body>
</html>
"""

class TelemetryData:
    def __init__(self, data):
        self.valid = False
        if len(data) < 311: return
        self.valid = True
        
        # Unpack Data
        self.is_race_on = struct.unpack("<i", data[0:4])[0]
        self.timestamp_ms = struct.unpack("<I", data[4:8])[0]
        (self.max_rpm, self.idle_rpm, self.cur_rpm) = struct.unpack("<3f", data[8:20])
        self.accel = struct.unpack("<3f", data[20:32])
        self.velocity = struct.unpack("<3f", data[32:44])
        self.angular_vel = struct.unpack("<3f", data[44:56])
        self.orientation = struct.unpack("<3f", data[56:68])
        self.norm_suspension = struct.unpack("<4f", data[68:84])
        self.tire_slip_ratio = struct.unpack("<4f", data[84:100])
        self.wheel_rotation = struct.unpack("<4f", data[100:116])
        self.rumble_strip = struct.unpack("<4i", data[116:132])
        self.puddle_depth = struct.unpack("<4f", data[132:148])
        self.surface_rumble = struct.unpack("<4f", data[148:164])
        self.slip_angle = struct.unpack("<4f", data[164:180])
        self.combined_slip = struct.unpack("<4f", data[180:196])
        self.susp_travel_meters = struct.unpack("<4f", data[196:212])
        (self.car_ordinal, self.car_class, self.car_perf, self.drivetrain, self.cylinders) = struct.unpack("<5i", data[212:232])
        self.position = struct.unpack("<3f", data[232:244])
        self.speed = struct.unpack("<f", data[244:248])[0]
        self.power = struct.unpack("<f", data[248:252])[0]
        self.torque = struct.unpack("<f", data[252:256])[0]
        self.tire_temp = struct.unpack("<4f", data[256:272])
        (self.boost, self.fuel, self.dist, self.best_lap, self.last_lap, self.cur_lap, self.cur_race_time) = struct.unpack("<7f", data[272:300])
        self.lap_number = struct.unpack("<H", data[300:302])[0]
        self.race_pos = struct.unpack("<B", data[302:303])[0]
        (self.input_accel, self.input_brake, self.input_clutch, self.input_handbrake, self.input_gear) = struct.unpack("<5B", data[303:308])
        self.input_steer = struct.unpack("<b", data[308:309])[0]
        self.driving_line = struct.unpack("<b", data[309:310])[0]
        self.ai_brake_diff = struct.unpack("<b", data[310:311])[0]
        self.tire_wear = struct.unpack("<4f", data[311:327])
        self.track_ordinal = struct.unpack("<i", data[327:331])[0]

    def to_dict(self):
        """Converts all attributes to a dictionary for CSV logging"""
        return vars(self).copy()

class Commentator:
    """
    Analyzes telemetry data to generate commentary strings.
    """
    def __init__(self):
        self.last_comment_time = 0
        self.last_gear = 11 
        self.was_race_on = 0
        self.max_speed_hit = 0.0
        self.last_race_pos = 0

    def get_gear_display(self, gear_val):
        if gear_val == 0: return "R"
        if gear_val == 11: return "N" 
        return str(gear_val)

    def get_commentary(self, packet):
        current_time = time.time()
        if current_time - self.last_comment_time < 0.2: return None

        msgs = []
        priority = False 

        # Race State
        if packet.is_race_on and not self.was_race_on:
            msgs.append("🟢 GREEN LIGHT! The race has started!")
            priority = True
        elif not packet.is_race_on and self.was_race_on:
            msgs.append("⏸️ Race paused or in menus.")
        self.was_race_on = packet.is_race_on

        if not packet.is_race_on: return msgs[0] if msgs else None

        # Position
        if self.last_race_pos == 0 and packet.race_pos > 0: self.last_race_pos = packet.race_pos
        if packet.race_pos != self.last_race_pos and packet.race_pos > 0:
            if packet.race_pos < self.last_race_pos:
                msgs.append(f"⬆️ OVERTAKE! Moved up to P{packet.race_pos}!")
                priority = True
            else:
                msgs.append(f"⬇️ LOST POSITION! Dropped to P{packet.race_pos}.")
            self.last_race_pos = packet.race_pos

        # RPM
        rpm_percent = 0
        if packet.max_rpm > 0: rpm_percent = packet.cur_rpm / packet.max_rpm
        if rpm_percent > 0.95: msgs.append(f"🔴 REDLINING! Engine screaming at {int(packet.cur_rpm)} RPM!")
        
        # Gears
        if packet.input_gear != self.last_gear:
            if packet.input_gear != 11:
                display_gear = self.get_gear_display(packet.input_gear)
                msgs.append(f"⚙️ Shifted to Gear {display_gear}")
                priority = True
            self.last_gear = packet.input_gear

        # Events
        if packet.input_handbrake > 0: msgs.append("⚓ Handbrake pulled!")
        if packet.input_brake > 200: msgs.append("🛑 HARD BRAKING!")
        
        max_slip = max([abs(x) for x in packet.tire_slip_ratio])

        # Combined Slip (Lateral + Longitudinal)
        # 1.0 is the theoretical limit of grip circle
        max_combined_slip = max([abs(x) for x in packet.combined_slip])

        if max_slip > 1.2:
            msgs.append("💨 BURNOUT / DRIFT! Massive loss of traction!")
            priority = True
        elif max_combined_slip > 0.9 and max_combined_slip < 1.1:
             msgs.append("🤏 AT THE LIMIT! Edge of grip circle.")
        elif max_slip > 0.8:
            msgs.append("⚠️ Tires struggling for grip...")

        max_puddle = max(packet.puddle_depth)
        if max_puddle > 0.5: msgs.append("💦 SPLASH! Hit a deep puddle!"); priority = True
            
        if any(x > 0.98 for x in packet.norm_suspension): msgs.append("💥 CRUNCH! Suspension bottomed out!"); priority = True

        mph = packet.speed * 2.23694
        if all(x < 0.1 for x in packet.norm_suspension) and mph > 20: msgs.append("🚀 AIRBORNE! All four wheels off the ground!"); priority = True

        if msgs:
            self.last_comment_time = current_time
            return " | ".join(msgs)
        return None

# --- WEB SERVER HANDLER ---
class TelemetryRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/data':
            # Serve JSON Data
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(current_telemetry).encode())
        
        elif self.path == '/' or self.path == '/dashboard.html':
            # Serve Embedded HTML
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(DASHBOARD_HTML.encode('utf-8'))
        
        else:
            self.send_error(404, "File not found")

    def log_message(self, format, *args):
        return

def start_web_server():
    server = HTTPServer(("", WEB_PORT), TelemetryRequestHandler)
    print(f"🌐 Web Dashboard active at http://localhost:{WEB_PORT}/")
    server.serve_forever()

# --- MAIN LOOP ---
def main():
    # Start Web Server in a separate thread
    web_thread = threading.Thread(target=start_web_server)
    web_thread.daemon = True
    web_thread.start()

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((UDP_IP, UDP_PORT))
    
    print(f"🎧 Listening for UDP telemetry on {UDP_IP}:{UDP_PORT}...")
    
    commentator = Commentator()
    
    csv_file = None
    csv_writer = None
    racing_active = False

    try:
        while True:
            data, addr = sock.recvfrom(1024) 
            packet = TelemetryData(data)
            
            if not packet.valid: continue

            # --- 1. UPDATE WEB DATA ---
            # Update the global dictionary for the web thread to read
            gear_str = commentator.get_gear_display(packet.input_gear)
            mph = packet.speed * 2.23694
            
            # Convert wear (0=New, 1=Worn) to Percentage Remaining (100 -> 0)
            tire_health = []
            for wear in packet.tire_wear:
                remaining = (1.0 - wear) * 100
                tire_health.append(max(0, min(100, remaining)))

            current_telemetry["rpm"] = int(packet.cur_rpm)
            current_telemetry["max_rpm"] = int(packet.max_rpm)
            current_telemetry["speed"] = round(mph, 1)
            current_telemetry["gear"] = gear_str
            current_telemetry["position"] = packet.race_pos
            current_telemetry["lap"] = packet.lap_number + 1 # 0-indexed usually
            current_telemetry["best_lap"] = packet.best_lap
            current_telemetry["race_on"] = bool(packet.is_race_on)
            current_telemetry["tire_wear"] = tire_health
            
            # Update Tire Temp (Round to Integer)
            current_telemetry["tire_temp"] = [int(t) for t in packet.tire_temp]

            # --- 2. LOGGING LOGIC ---
            if packet.is_race_on:
                if not racing_active:
                    # RACE STARTED: Open new log file
                    racing_active = True
                    timestamp = time.strftime("%Y%m%d-%H%M%S")
                    filename = f"race_log_{timestamp}.csv"
                    print(f"\n📝 Race started! Logging to {filename}")
                    
                    csv_file = open(filename, 'w', newline='')
                    packet_dict = packet.to_dict()
                    csv_writer = csv.DictWriter(csv_file, fieldnames=packet_dict.keys())
                    csv_writer.writeheader()
                
                # Write data row
                if csv_writer:
                    csv_writer.writerow(packet.to_dict())
            
            else:
                if racing_active:
                    # RACE STOPPED: Close file
                    racing_active = False
                    if csv_file:
                        print("📝 Race finished. Log file saved.\n")
                        csv_file.close()
                        csv_file = None
                        csv_writer = None

            # --- 3. COMMENTARY ---
            comment = commentator.get_commentary(packet)
            if comment:
                print(f"[{time.strftime('%H:%M:%S')}] {comment}")

    except KeyboardInterrupt:
        if csv_file: csv_file.close()
        print("\n🛑 Stopped.")

if __name__ == "__main__":
    main()