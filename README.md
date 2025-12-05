Forza Telemetry Commentator & Live Dashboard

This Python tool listens to the UDP telemetry stream from Forza Motorsport and Forza Horizon games. It interprets the raw physics data to provide a live "race commentary" in your console, hosts a real-time web dashboard, and automatically logs race data to CSV files for analysis.

Features

🎙️ Live Commentary: Analyzes game events in real-time and prints commentary to the console (e.g., "Hard Braking!", "Suspension Bottomed Out!", "Overtake!").

🏎️ Web Dashboard: Hosts a local web server displaying:

Speed (MPH) & RPM

Current Gear & Position

Lap Count & Fastest Lap

Tire Health: Visual 2x2 grid showing tire wear percentage and temperature for all four tires.

📝 Auto-Logging: Automatically starts recording telemetry to a CSV file when the race begins and stops when the race ends.

Suspension Monitoring: Detects and alerts if the suspension bottoms out ("CRUNCH!").

Prerequisites

Python 3.x installed on your computer.

A compatible Forza game (Forza Motorsport 7, Forza Horizon 4, Forza Horizon 5, or the new Forza Motorsport).

Setup Guide

1. Configure the Game

You must enable "Data Out" in the game settings to broadcast telemetry.

Open your Forza game.

Navigate to Settings -> HUD & Gameplay.

Scroll down to the Data Out section.

Set Data Out to ON.

Set Data Out IP Address to 127.0.0.1 (localhost).

Set Data Out IP Port to 5300.

2. Run the Script

Download or clone this repository.

Open your terminal or command prompt in the folder containing the script.

Run the script:

python race_commentator.py


Usage

Once the script is running, it will listen for data on port 5300.

The Console

Watch the terminal window for text commentary. The script filters out noise and only reports significant events like shifting, traction loss, jumps, and position changes.

The Web Dashboard

Open your web browser (on your PC, phone, or tablet connected to the same network) and navigate to:

http://localhost:8000/dashboard.html

Note: If accessing from a phone/tablet, replace localhost with your PC's local IP address (e.g., http://192.168.1.50:8000/dashboard.html).

Data Logging

When the race starts (Green Light), a file named race_log_YYYYMMDD-HHMMSS.csv is created.

Data is written row-by-row during the race.

When the race ends or you enter the pause menu, the file is saved and closed automatically.

Configuration

You can modify the configuration variables at the top of race_commentator.py if you need to use different ports or listen on specific network interfaces.

UDP_IP = "0.0.0.0"  # Listen on all interfaces
UDP_PORT = 5300     # Match this to your game settings
WEB_PORT = 8000     # Port for the web dashboard


Troubleshooting

"Waiting for data...": Ensure the game is unpaused and you are driving. Ensure the Port in the script matches the Port in the game settings.

Firewall: If you cannot connect to the dashboard from a phone, ensure your PC's firewall allows Python to accept incoming connections on port 8000.

Wrong Gear/RPM: The script assumes the standard "Dash" (V2) format. Ensure your game is sending the correct format (sometimes labeled as "Car Dash").

License

Free to use and modify for personal projects.