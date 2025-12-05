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
        # If the game sends V1 ('Sled'), it will be 232 bytes.
        if len(data) < 311: 
            # Not enough data for the full Dash format
            return

        self.valid = True
        
        # Create a struct format string based on the user prompt
        # < = little-endian (standard for PC/Xbox)
        # i = S32, I = U32, f = F32, H = U16, B = U8, b = S8
        
        # 1. Sled / V1 Base Data (First 232 bytes)
        # 12 Integers/Floats mixed
        # IsRaceOn(i), TimestampMS(I), MaxRPM(f), IdleRPM(f), CurRPM(f)
        # AccelX/Y/Z(3f), VelX/Y/Z(3f), AngVelX/Y/Z(3f), YawPitchRoll(3f)
        # NormSusp(4f), SlipRatio(4f), WheelSpeed(4f), RumbleStrip(4i), Puddle(4f), SurfRumble(4f)
        # SlipAngle(4f), CombSlip(4f), SuspTravel(4f)
        # CarOrdinal(i), CarClass(i), CarPerf(i), DriveTrain(i), Cylinders(i)
        
        # 2. Dash / V2 Specific Data
        # PosX/Y/Z(3f), Speed(f), Power(f), Torque(f), TireTemp(4f)
        # Boost(f), Fuel(f), Dist(f), BestLap(f), LastLap(f), CurLap(f), CurRaceTime(f)
        # LapNum(H), RacePos(B), Accel(B), Brake(B), Clutch(B), HandBrake(B), Gear(B), Steer(b)
        # Line(b), AIBrake(b)
        # TireWear(4f) - NOTE: Parsing varies here slightly by game version, 
        # usually there is padding. We will unpack strictly based on prompt list.
        # TrackOrdinal(i)

        fmt = "<iIffffffffffffffffffffffffffffffffffffffffffffffffffffiiiiifffffffffffffffffffffHBBBBBBbbbfiii"
        
        # Note: The format string above is an approximation. 
        # To be robust, we unpack chunks to handle potential padding differences in specific games.
        
        # --- PARSING ---
        # Sled Portion
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
            
        # Dash Portion
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

class Commentator:
    def __init__(self):
        self.last_comment_time = 0
        self.last_gear = 0
        self.was_race_on = 0
        self.max_speed_hit = 0.0

    def get_commentary(self, packet):
        """
        Analyzes the packet and returns a string if an interesting event occurs.
        Returns None if nothing interesting is happening to avoid spam.
        """
        current_time = time.time()
        
        # Don't spam comments faster than every 0.5 seconds unless critical
        if current_time - self.last_comment_time < 0.2:
            return None

        msgs = []
        priority = False # If true, print immediately

        # 1. Race State
        if packet.is_race_on and not self.was_race_on:
            msgs.append("🟢 GREEN LIGHT! The race has started!")
            priority = True
        elif not packet.is_race_on and self.was_race_on:
            msgs.append("⏸️ Race paused or in menus.")
        self.was_race_on = packet.is_race_on

        if not packet.is_race_on:
            return msgs[0] if msgs else None

        # 2. Engine & Speed
        mph = packet.speed * 2.23694
        if mph > self.max_speed_hit:
            self.max_speed_hit = mph
        
        rpm_percent = 0
        if packet.max_rpm > 0:
            rpm_percent = packet.cur_rpm / packet.max_rpm

        if rpm_percent > 0.95:
            msgs.append(f"🔴 REDLINING! Engine screaming at {int(packet.cur_rpm)} RPM!")
        
        # 3. Gears
        if packet.input_gear != self.last_gear:
            msgs.append(f"⚙️ Shifted to Gear {packet.input_gear}")
            self.last_gear = packet.input_gear
            priority = True

        # 4. Inputs
        if packet.input_handbrake > 0:
            msgs.append("⚓ Handbrake pulled!")
            priority = True
        
        if packet.input_brake > 200:
             # Check if locking up (Wheel rotation vs Speed)
             msgs.append("🛑 HARD BRAKING!")

        # 5. Traction & Slip (Index 2 is Rear Left, 3 is Rear Right usually)
        # Slip Ratio > 1.0 means loss of traction
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

        # 6. Environment
        max_puddle = max(packet.puddle_depth)
        if max_puddle > 0.5:
            msgs.append("💦 SPLASH! Hit a deep puddle!")
            priority = True
        
        rumble_count = sum([1 for x in packet.rumble_strip if x > 0])
        if rumble_count > 0:
            msgs.append("〰️ Rattling over the rumble strips.")

        # 7. Air
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
        return (f"POS: {packet.race_pos} | LAP: {packet.lap_number} | "
                f"GEAR: {packet.input_gear} | MPH: {mph:.1f} | RPM: {int(packet.cur_rpm)}")


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
