import subprocess
import time
import os

def reproduce():
    print("Starting Forza Telemetry Tool in Mode 1...")
    # Use Popen to run it in background
    process = subprocess.Popen(['python3', 'main.py'],
                               stdin=subprocess.PIPE,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE,
                               text=True)

    try:
        # Provide choice '1'
        process.stdin.write('1\n')
        process.stdin.flush()

        print("Waiting for server to start...")
        time.sleep(3)

        print("Checking port 8000 binding...")
        try:
            output = subprocess.check_output(['ss', '-tuln'], text=True)
        except:
            output = subprocess.check_output(['netstat', '-tuln'], text=True)

        relevant_lines = [line for line in output.split('\n') if ':8000' in line]

        if not relevant_lines:
            print("Could not find port 8000 binding.")
        else:
            for line in relevant_lines:
                print(f"Binding: {line}")
                if '127.0.0.1:8000' in line:
                    print("SECURE: Bound to 127.0.0.1.")
                elif '0.0.0.0:8000' in line or '*:8000' in line:
                    print("VULNERABLE: Bound to all interfaces.")
    finally:
        print("Cleaning up...")
        process.terminate()
        process.wait()

if __name__ == "__main__":
    reproduce()
