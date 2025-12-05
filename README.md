# Forza Telemetry Commentator

A Python script that listens to UDP telemetry data from **Forza Motorsport** and **Forza Horizon** games and generates real-time commentary on your driving.

---

## **Features**

-   **Real-time Analysis**: Parses high-frequency UDP telemetry packets.
-   **Event Commentary**: Detects and comments on:
    -   Race Start/Stop events
    -   Gear shifts
    -   Redlining (High RPM)
    -   Hard braking and Handbrake usage
    -   Loss of traction (Burnouts/Drifting)
    -   Environmental interactions (Puddles, Rumble strips)
    -   Airborne moments (Jumps)

---

## **Prerequisites**

-   Python 3.x
-   A compatible Forza game (Forza Motorsport 7, Forza Horizon 4/5, Forza Motorsport (2023)) running on Xbox or PC.

---

## **Configuration**

### **Game Settings**

1.  Open your Forza game.
2.  Navigate to **Settings** -> **HUD & Gameplay**.
3.  Scroll down to **Data Out**.
4.  Set **Data Out** to **ON**.
5.  Set **Data Out IP Address** to the IP address of the computer running this script.
    -   If running on the same PC as the game, you can try `127.0.0.1` (localhost).
    -   If running on a separate device (e.g., laptop listening to Xbox), use your computer's local network IP (e.g., `192.168.1.x`).
6.  Set **Data Out IP Port** to `5300` (matches the default in the script).
7.  Set **Data Out Packet Format** to **"Dash"** (or "Car Dash"). The script is designed for the Dash format (V2).

### **Script Settings**

You can modify the `UDP_IP` and `UDP_PORT` variables at the top of `main.py` if you need to use a different configuration.

```python
UDP_IP = "0.0.0.0" # Listen on all available interfaces
UDP_PORT = 5300    # Default Forza Data Out port
```

---

## **Usage**

1.  Clone this repository or download `main.py`.
2.  Open a terminal or command prompt.
3.  Run the script:

    ```bash
    python main.py
    ```

4.  Start driving in the game. You should see commentary messages appear in the console as you drive.

---

## **Troubleshooting**

-   **No Output**:
    -   Verify the IP address and Port match exactly in both the game and the script.
    -   Check your firewall settings to ensure Python is allowed to receive UDP packets on port 5300.
    -   Ensure the game is not paused. Telemetry stops when paused.
-   **"Sled" vs "Dash"**:
    -   This script requires the **"Dash"** packet format. If you selected "Sled" in the game settings, the script will ignore the packets (as they are smaller and lack required data).

---

## **License**

MIT License
