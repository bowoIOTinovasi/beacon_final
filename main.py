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
    try:
        print(f"[{script_name}] Starting...")
        process = subprocess.Popen([sys.executable, script_name])
        process.wait()
        print(f"[{script_name}] Process exited.")
    except Exception as e:
        print(f"[{script_name}] Error: {e}")

def main():
    threads = {}
    while True:
        for script in SCRIPTS:
            # Cek apakah file script ada
            if not os.path.exists(script):
                print(f"Script {script} tidak ditemukan!")
                continue
            # Jika thread belum ada atau sudah mati, buat thread baru
            if script not in threads or not threads[script].is_alive():
                print(f"Restarting thread for {script}...")
                t = threading.Thread(target=run_script, args=(script,), daemon=True)
                t.start()
                threads[script] = t
        try:
            time.sleep(2)
        except KeyboardInterrupt:
            print("Exiting...")
            break

if __name__ == "__main__":
    main()
