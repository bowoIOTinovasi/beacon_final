import json
import time
import os
from datetime import datetime, timedelta
import socket
import threading
import paho.mqtt.client as mqtt

CONFIG_FILE = "config.json"

def read_config():
    try:
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return {}

def write_config(cfg):
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump(cfg, f, indent=2)
    except Exception as e:
        print(f"Failed to write config: {e}")

def get_mac_ip(cfg):
    mac = cfg.get("mac_address", "-")
    ip = cfg.get("ip", "-")
    return mac, ip

def get_mqtt_server(cfg):
    return cfg.get("server", "localhost")

def get_status(cfg):
    return cfg.get("status", False)

def on_connect(client, userdata, flags, rc):
    print("Connected to MQTT broker with result code " + str(rc))
    client.subscribe("beacon/registration")

def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
        if payload.get("action") == "beacon_registered":
            mac = payload.get("id")
            ip = payload.get("ip")
            cfg = read_config()
            if cfg.get("mac_address") == mac and cfg.get("ip") == ip:
                cfg["status"] = True
                write_config(cfg)
                print("Device registered, status set to True in config.json")
    except Exception as e:
        print(f"Error in on_message: {e}")

def is_connected():
    try:
        socket.create_connection(("8.8.8.8", 53), timeout=2)
        return True
    except Exception:
        return False

def publish_status_loop(client):
    next_publish = datetime.now()
    while True:
        now = datetime.now()
        if now >= next_publish:
            cfg = read_config()
            mac, ip = get_mac_ip(cfg)
            status = get_status(cfg)
            timestamp = now.strftime("%Y-%m-%d %H:%M:%S")

            if status:
                payload = {
                    "action": "device_status",
                    "data": {
                        "id": mac,
                        "timestamp": timestamp,
                        "checker": ""
                    }
                }
            else:
                payload = {
                    "action": "new_beacon",
                    "data": {
                        "id": mac,
                        "ip": ip,
                        "connection": "LAN"
                    }
                }

            client.publish("beacon/status", json.dumps(payload))
            print(f"Published at {timestamp}: {payload}")

            next_publish = now + timedelta(seconds=60)

        time.sleep(0.5)  # Hindari CPU usage 100%

def main():
    while True:
        cfg = read_config()
        mqtt_server = get_mqtt_server(cfg)

        if not is_connected():
            print("No internet connection. Retrying in 10s...")
            time.sleep(10)
            continue

        client = mqtt.Client()
        client.on_connect = on_connect
        client.on_message = on_message

        try:
            client.connect(mqtt_server, 1883, 60)
        except Exception as e:
            print(f"MQTT connection failed: {e}")
            time.sleep(10)
            continue

        client.loop_start()

        try:
            status_thread = threading.Thread(target=publish_status_loop, args=(client,), daemon=True)
            status_thread.start()

            while True:
                time.sleep(1)  # Jaga thread utama tetap hidup
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"Error in main loop: {e}")
        finally:
            client.loop_stop()
            client.disconnect()
            time.sleep(5)

if __name__ == "__main__":
    main()
