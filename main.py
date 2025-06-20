import threading
import subprocess
import time
import sys
import os

SCRIPTS = [
    "collect.py",
    "process.py",
    "sender.py"
]

def run_script(script_name):
    while True:
        try:
            print(f"[{script_name}] Starting...")
            # Gunakan sys.executable agar python path sesuai environment
            process = subprocess.Popen([sys.executable, script_name])
            process.wait()
            print(f"[{script_name}] Process exited. Restarting in 2 seconds...")
        except Exception as e:
            print(f"[{script_name}] Error: {e}")
        time.sleep(2)  # Delay sebelum restart

def main():
    threads = []
    for script in SCRIPTS:
        if not os.path.exists(script):
            print(f"Script {script} tidak ditemukan!")
            continue
        t = threading.Thread(target=run_script, args=(script,), daemon=True)
        t.start()
        threads.append(t)
    # Keep main thread alive
    try:
        while True:
            time.sleep(10)
    except KeyboardInterrupt:
        print("Exiting...")

if __name__ == "__main__":
    main()
