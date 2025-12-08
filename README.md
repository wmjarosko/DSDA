# Forza Telemetry Commentator

## Forza Telemetry Toolkit

This Python tool listens to the UDP telemetry stream from Forza Motorsport and Forza Horizon games. It offers two distinct ways to view your race data: a comprehensive Web Dashboard with data logging, or a lightweight Transparent Overlay that sits directly on top of your game window.

## Features

Mode 1: Web Dashboard & Logger

🎙️ Live Commentary: Analyzes game events in real-time and prints text commentary to the console (e.g., "Hard Braking!", "Suspension Bottomed Out!", "Overtake!").

🏎️ Web Dashboard: Hosts a local web server displaying live telemetry on any device (phone, tablet, second monitor).

Tire Health: Visual 2x2 grid showing vertical tire wear bars and live temperatures.

Suspension Alerts: Visual and text alerts for bottoming out.

📝 Auto-Logging: Automatically records full telemetry to CSV files. Recording starts on "Green Light" and stops when the race ends.

Mode 2: Transparent Windows Overlay

🖥️ Native Overlay: Draws a HUD directly over your game window on PC.

🖱️ Click-Through: The overlay is "transparent" to mouse clicks, so you can interact with the game underneath without the overlay stealing focus.

Always On Top: Stays visible even when playing in Windowed or Borderless Windowed modes.

Smart Positioning: Automatically aligns itself to the right side of your screen.

Live Gauges: Large Gear indicator, Speed, RPM, Position, Lap, and Tire Wear bars.

## Prerequisites

Python 3.x installed on your computer.

Forza Game: Compatible with Forza Motorsport 7, Forza Horizon 4, Forza Horizon 5, and the new Forza Motorsport (2023).

OS: Windows is required for Mode 2 (Overlay). Mode 1 (Web) works on Mac/Linux as well.

## Setup Guide

1. Configure the Game

You must enable "Data Out" in the game settings to broadcast telemetry.

Open your Forza game.

Navigate to Settings -> HUD & Gameplay.

Scroll down to the Data Out section.

Set Data Out to ON.

Set Data Out IP Address to the IP address of the machine that the script will run on, 127.0.0.1 if you want to use the overlay on top of Forza.

Set Data Out IP Port to 5300.

2. Run the Toolkit

Open your terminal or command prompt in the folder containing the script.

Run the master script:

python main.py


The script will ask you to select a mode:

=========================================
  FORZA TELEMETRY TOOLKIT
=========================================
1. Web Dashboard + CSV Logger + Commentary
2. Transparent Windows Overlay
=========================================
Select Mode (1 or 2):


## Usage Tips

For the Overlay (Mode 2)

Game Window Mode: For best results, set your Forza video settings to Windowed or Borderless Windowed. Exclusive Fullscreen may hide the overlay.

Position: The overlay automatically calculates your screen width and places itself on the right side.

Closing: To close the overlay, click into the terminal window running the script and press Ctrl+C. You cannot close it by clicking the overlay itself (because clicks pass through it!).

For the Web Dashboard (Mode 1)

Access: Open your web browser and go to http://localhost:8000/dashboard.html.

Mobile Access: Find your PC's local IP address (e.g., 192.168.1.50) and visit http://192.168.1.50:8000/dashboard.html on your phone to turn it into a dedicated race dash.

Logs: Check the script folder for race_log_YYYYMMDD-HHMMSS.csv files after your race finishes.

## Configuration

You can modify the configuration variables at the top of main.py if you need to change ports or overlay padding:

UDP_IP = "0.0.0.0"  
UDP_PORT = 5300     # Must match game settings
WEB_PORT = 8000     # Dashboard port
OVERLAY_Y = 50      # Distance from top of screen


## Troubleshooting

"Waiting for data...": Ensure the game is unpaused and you are driving. Ensure the Port in the script matches the Port in the game settings.

Overlay not showing: Ensure the game is not in "Exclusive Fullscreen" mode. Ensure you are running on Windows.

Click-through not working: This feature relies on Windows APIs. If it fails, check the console for error messages regarding ctypes.

License

Free to use and modify for personal projects.
