import socket
import struct
import time
import os

# --- CONFIGURATION ---
UDP_IP = "0.0.0.0" # Listen on all available interfaces
UDP_PORT = 5300    # Default Forza Data Out port
# NOTE: In your game settings, ensure "Data Out" is set to ON
# and the IP address is set to the IP of this computer (or 127.0.0.1 if running on same PC)

class TelemetryData:
    """
    Parses the binary buffer based on the provided structure.
    Based on the standard 'Dash' format (V2).
    """
    def __init__(self, data):
        self.valid = False
        
        # The V2 'Dash' packet is typically 324 bytes. 
        # The parser logic specifically checks for the Dash format size requirement (>= 311 bytes).
        # Sled / V1 packets (232 bytes) are ignored by this parser as they lack the 'Dash' specific fields.
        if len(data) < 311: 
            return

        self.valid = True
        

        # --- PARSING ---
        # Sled Portion (First 232 bytes)
        self.is_race_on = struct.unpack("<i", data[0:4])[0]
        self.timestamp_ms = struct.unpack("<I", data[4:8])[0]
        
        # Engine
        (self.max_rpm, self.idle_rpm, self.cur_rpm) = struct.unpack("<3f", data[8:20])
        
        # Physics Vectors
        self.accel = struct.unpack("<3f", data[20:32])
        self.velocity = struct.unpack("<3f", data[32:44])
        self.angular_vel = struct.unpack("<3f", data[44:56])
        self.orientation = struct.unpack("<3f", data[56:68]) # Yaw, Pitch, Roll
        
        # Wheels/Suspension (FL, FR, RL, RR)
        self.norm_suspension = struct.unpack("<4f", data[68:84])
        self.tire_slip_ratio = struct.unpack("<4f", data[84:100])
        self.wheel_rotation = struct.unpack("<4f", data[100:116])
        self.rumble_strip = struct.unpack("<4i", data[116:132])
        self.puddle_depth = struct.unpack("<4f", data[132:148])
        self.surface_rumble = struct.unpack("<4f", data[148:164])
        self.slip_angle = struct.unpack("<4f", data[164:180])
        self.combined_slip = struct.unpack("<4f", data[180:196])
        self.susp_travel_meters = struct.unpack("<4f", data[196:212])
        
        # Car Info
        (self.car_ordinal, self.car_class, self.car_perf, self.drivetrain, self.cylinders) = \
            struct.unpack("<5i", data[212:232])
            
        # Dash Portion (Specific to V2)
        self.position = struct.unpack("<3f", data[232:244])
        self.speed = struct.unpack("<f", data[244:248])[0] # m/s
        self.power = struct.unpack("<f", data[248:252])[0] # Watts
        self.torque = struct.unpack("<f", data[252:256])[0] # Nm
        self.tire_temp = struct.unpack("<4f", data[256:272])
        
        (self.boost, self.fuel, self.dist, self.best_lap, self.last_lap, 
         self.cur_lap, self.cur_race_time) = struct.unpack("<7f", data[272:300])
         
        self.lap_number = struct.unpack("<H", data[300:302])[0]
        self.race_pos = struct.unpack("<B", data[302:303])[0]
        
        # Inputs (0-255)
        (self.input_accel, self.input_brake, self.input_clutch, self.input_handbrake, self.input_gear) = \
            struct.unpack("<5B", data[303:308])
            
        self.input_steer = struct.unpack("<b", data[308:309])[0]
        self.driving_line = struct.unpack("<b", data[309:310])[0]
        self.ai_brake_diff = struct.unpack("<b", data[310:311])[0]
        
        # Tail
        self.tire_wear = struct.unpack("<4f", data[311:327])
        self.track_ordinal = struct.unpack("<i", data[327:331])[0]

class Commentator:
    """
    Analyzes telemetry data to generate commentary strings.
    """
    def __init__(self):
        self.last_comment_time = 0
        self.last_gear = 11 # Start assuming neutral/unknown
        self.was_race_on = 0
        self.max_speed_hit = 0.0
        self.last_race_pos = 0

    def get_gear_display(self, gear_val):
        if gear_val == 0: return "R"
        if gear_val == 11: return "N" # Treating 11 as Neutral based on user logs
        return str(gear_val)

    def get_commentary(self, packet):
        """
        Analyzes the packet and returns a string if an interesting event occurs.
        Returns None if nothing interesting is happening to avoid spam.
        """
        current_time = time.time()
        
        # Don't spam comments faster than every 0.2 seconds
        if current_time - self.last_comment_time < 0.2:
            return None

        msgs = []
        priority = False # If true, indicates an event we really want to print immediately

        # 1. Race State
        if packet.is_race_on and not self.was_race_on:
            msgs.append("🟢 GREEN LIGHT! The race has started!")
            priority = True
        elif not packet.is_race_on and self.was_race_on:
            msgs.append("⏸️ Race paused or in menus.")
        self.was_race_on = packet.is_race_on

        if not packet.is_race_on:
            return msgs[0] if msgs else None

        # 2. Position Ranking Changes
        # Initialize last_race_pos if it's 0 (start of script/race)
        if self.last_race_pos == 0 and packet.race_pos > 0:
            self.last_race_pos = packet.race_pos
            
        if packet.race_pos != self.last_race_pos and packet.race_pos > 0:
            if packet.race_pos < self.last_race_pos:
                msgs.append(f"⬆️ OVERTAKE! Moved up to P{packet.race_pos}!")
                priority = True
            else:
                msgs.append(f"⬇️ LOST POSITION! Dropped to P{packet.race_pos}.")
            self.last_race_pos = packet.race_pos

        # 3. Engine & Speed
        mph = packet.speed * 2.23694
        if mph > self.max_speed_hit:
            self.max_speed_hit = mph
        
        rpm_percent = 0
        if packet.max_rpm > 0:
            rpm_percent = packet.cur_rpm / packet.max_rpm

        if rpm_percent > 0.95:
            msgs.append(f"🔴 REDLINING! Engine screaming at {int(packet.cur_rpm)} RPM!")
        
        # 4. Gears
        # Logic: We only announce shifting to actual drive gears or reverse.
        # We ignore shifting 'to' 11 (Neutral) to prevent spam during the shift action.
        if packet.input_gear != self.last_gear:
            # Check if this is a "real" gear engagement we want to announce
            # We skip 11 (Neutral) for commentary
            if packet.input_gear != 11:
                display_gear = self.get_gear_display(packet.input_gear)
                msgs.append(f"⚙️ Shifted to Gear {display_gear}")
                priority = True
            
            # We still update last_gear so we know when we leave Neutral later
            self.last_gear = packet.input_gear

        # 5. Inputs
        if packet.input_handbrake > 0:
            msgs.append("⚓ Handbrake pulled!")
            priority = True
        
        if packet.input_brake > 200:
             # Check if locking up (Wheel rotation vs Speed)
             msgs.append("🛑 HARD BRAKING!")

        # 6. Traction & Slip (Index 2 is Rear Left, 3 is Rear Right usually)
        # Slip Ratio > 1.0 means loss of traction
        max_slip = max([abs(x) for x in packet.tire_slip_ratio])
        if max_slip > 1.2:
            msgs.append("💨 BURNOUT / DRIFT! Massive loss of traction!")
            priority = True
        elif max_slip > 0.8:
            msgs.append("⚠️ Tires struggling for grip...")

        # 7. Environment
        max_puddle = max(packet.puddle_depth)
        if max_puddle > 0.5:
            msgs.append("💦 SPLASH! Hit a deep puddle!")
            priority = True
        
        rumble_count = sum([1 for x in packet.rumble_strip if x > 0])
        if rumble_count > 0:
            msgs.append("〰️ Rattling over the rumble strips.")

        # 8. Air
        # If all 4 suspension values are fully extended (approx 0.0 or close to it depending on normalization)
        # Using normalized: 0.0f = max stretch
        if all(x < 0.1 for x in packet.norm_suspension) and mph > 20:
            msgs.append("🚀 AIRBORNE! All four wheels off the ground!")
            priority = True

        if msgs:
            self.last_comment_time = current_time
            return " | ".join(msgs)
        
        return None

    def get_dashboard_str(self, packet):
        """Returns a string for a constant dashboard update"""
        mph = packet.speed * 2.23694
        gear_str = self.get_gear_display(packet.input_gear)
        return (f"POS: {packet.race_pos} | LAP: {packet.lap_number} | "
                f"GEAR: {gear_str} | MPH: {mph:.1f} | RPM: {int(packet.cur_rpm)}")


def main():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((UDP_IP, UDP_PORT))
    
    print(f"🎧 Listening for UDP telemetry on {UDP_IP}:{UDP_PORT}...")
    print("Ensure your game 'Data Out' setting matches this port.")
    print("waiting for data...\n")

    commentator = Commentator()

    try:
        while True:
            data, addr = sock.recvfrom(1024) # buffer size is 1024 bytes
            packet = TelemetryData(data)
            
            if not packet.valid:
                continue

            # Clear console line for the 'Dashboard' (optional, or just print log)
            # print(f"\r{commentator.get_dashboard_str(packet)}", end="")

            # Get Event Commentary
            comment = commentator.get_commentary(packet)
            if comment:
                print(f"[{time.strftime('%H:%M:%S')}] {comment}")

    except KeyboardInterrupt:
        print("\n🛑 Stopped.")

if __name__ == "__main__":
    main()
