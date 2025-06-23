import os
import sys
import time
import json
import statistics
from datetime import datetime, timedelta

import globals
import globals_function as gf

CODE_LOG_FILE = "log/code/log_process.log"

DATA_WIFI_DIR = "data_raw_wifi"
DATA_BLE_DIR = "data_raw_ble"
DATA_FINAL_DIR = "data_final"

def parse_log_file(filepath, is_ble=False):
    """
    Parse log file menjadi dict {mac: [ {dt, rssi}, ... ]}
    """
    result = {}
    try:
        with open(filepath, "r") as f:
            lines = f.readlines()
        for line in lines:
            line = line.strip()
            if not line:
                continue
            try:
                base_data = line.split(" - ")
                date_time_from_data = base_data[0]
                split_base_data = line.split(",")
                if is_ble:
                    if "BLE=" in split_base_data[0] and "RSSI=" in split_base_data[1]:
                        mac = split_base_data[0].split("=")[1]
                        rssi = int(split_base_data[1].split("=")[1])
                    else:
                        continue
                else:
                    if "ADDR=" in split_base_data[0] and "RSSI=" in split_base_data[2]:
                        mac = split_base_data[0].split("=")[1]
                        rssi = int(split_base_data[2].split("=")[1])
                    else:
                        continue
                if mac not in result:
                    result[mac] = []
                result[mac].append({"dt": date_time_from_data, "rssi": rssi})
            except Exception:
                continue
    except Exception as e:
        gf.dd(f"parse_log_file error: {e}")
    return result

def calc_dwelling(mac_data):
    """
    Hitung dwelling time (detik) untuk setiap mac.
    Return: dict {mac: dwelling_time}
    """
    from datetime import datetime
    result = {}
    for mac, records in mac_data.items():
        if len(records) < 2:
            continue
        try:
            t0 = datetime.strptime(records[0]["dt"], "%Y-%m-%d %H:%M:%S")
            t1 = datetime.strptime(records[-1]["dt"], "%Y-%m-%d %H:%M:%S")
            duration = int((t1 - t0).total_seconds())
            result[mac] = duration
        except Exception:
            continue
    return result

def classify_dwelling(dwelling_dict):
    """
    Klasifikasikan dwelling time ke 3 kategori.
    Return: [count_0_30, count_31_300, count_301_up]
    """
    a, b, c = 0, 0, 0
    for dur in dwelling_dict.values():
        if dur <= 30:
            a += 1
        elif 31 <= dur <= 300:
            b += 1
        elif dur > 300:
            c += 1
    return [a, b, c]

def process_for_hour(hour_str):
    dt_str = f"{hour_str}:00:00"
    wifi_file = None
    ble_file = None
    for fname in os.listdir(DATA_WIFI_DIR):
        if hour_str in fname:
            wifi_file = os.path.join(DATA_WIFI_DIR, fname)
            break
    for fname in os.listdir(DATA_BLE_DIR):
        if hour_str in fname:
            ble_file = os.path.join(DATA_BLE_DIR, fname)
            break

    wifi_mac_data = parse_log_file(wifi_file) if wifi_file else {}
    wifi_dwelling = calc_dwelling(wifi_mac_data)
    dwelling_count_wifi = classify_dwelling(wifi_dwelling)
    total_wifi = sum(dwelling_count_wifi)

    ble_mac_data = parse_log_file(ble_file, is_ble=True) if ble_file else {}
    ble_dwelling = calc_dwelling(ble_mac_data)
    dwelling_count_ble = classify_dwelling(ble_dwelling)
    total_ble = sum(dwelling_count_ble)

    ip_addr = getattr(globals, "ip", "-")
    mac_addr = getattr(globals, "mac_address", "-")

    final_data = {
        "action": "send_data",
        "data": {
            "id": mac_addr,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "ip": ip_addr,
            "dt": dt_str,
            "total_wifi": total_wifi,
            "total_ble": total_ble,
            "dwelling_wifi": 0,
            "dwelling_ble": 0,
            "dwelling_count_wifi": dwelling_count_wifi,
            "dwelling_count_ble": dwelling_count_ble
        }
    }

    os.makedirs(DATA_FINAL_DIR, exist_ok=True)
    final_filename = f"final_{hour_str}.log"
    final_path = os.path.join(DATA_FINAL_DIR, final_filename)
    with open(final_path, "w") as f:
        json.dump(final_data, f, indent=2)
    gf.write_log(CODE_LOG_FILE, f"Saved final data to {final_path}")

def get_all_hours_from_raw():
    """Ambil semua jam unik dari file di data_raw_wifi dan data_raw_ble"""
    hours = set()
    for folder in [DATA_WIFI_DIR, DATA_BLE_DIR]:
        for fname in os.listdir(folder):
            if len(fname) >= 13:
                # Ambil pattern yyyy-mm-dd HH dari nama file
                try:
                    parts = fname.split("_")
                    if len(parts) >= 2:
                        date_part = parts[-1].replace(".log", "")
                        hour_str = date_part[:13].replace("-", " ")
                        # Cek format
                        datetime.strptime(hour_str, "%Y %m %d %H")
                        hour_str = hour_str.replace(" ", "-")
                        hour_str = hour_str.replace("-", " ", 2)
                        hours.add(hour_str)
                except Exception:
                    continue
    return sorted(hours)

def get_all_final_hours():
    """Ambil semua jam unik yang sudah ada di data_final"""
    hours = set()
    for fname in os.listdir(DATA_FINAL_DIR):
        if fname.startswith("final_") and fname.endswith(".log"):
            hour_str = fname.replace("final_", "").replace(".log", "")
            hours.add(hour_str)
    return hours

if __name__ == "__main__":
    try:
        while True:
            now = datetime.now()
            # Jalankan hanya pada jam 00:00 dan 12:00
            if now.hour in [0, 12] and now.minute == 0:
                all_hours = get_all_hours_from_raw()
                final_hours = get_all_final_hours()
                for hour_str in all_hours:
                    if hour_str not in final_hours:
                        process_for_hour(hour_str)
                time.sleep(60)  # Hindari double eksekusi dalam 1 menit
            else:
                time.sleep(30)
    except KeyboardInterrupt:
        gf.write_log(CODE_LOG_FILE, "Program stopped by user")
    except Exception as e:
        gf.write_log(CODE_LOG_FILE, f"FATAL ERROR: {e}")
