import sys
import os
import json
import time
import serial
import serial.tools.list_ports

import globals
import globals_function as gf

if globals.output:
    import RPi.GPIO as GPIO
    
CODE_LOG_FILE = "log/code/log_collect.log"

def auto_detect_serial_port(preferred_names=None):
    """
    Deteksi otomatis port serial yang cocok.
    preferred_names: list string, misal ['CP2102', 'CH340', 'FTDI', ...]
    Return: path port (str) atau None
    """
    ports = list(serial.tools.list_ports.comports())
    for port in ports:
        desc = f"{port.description} {port.hwid} {port.manufacturer or ''} {port.product or ''}"
        if preferred_names:
            for name in preferred_names:
                if name.lower() in desc.lower():
                    return port.device
        else:
            return port.device
    return None

class CollectProgram(object):
    '''
    CollectProgram bertugas menghandle komunikasi dengan sensor,
    menyimpan data dari sensor ke log, dan mengatur LED status koneksi.
    '''

    def __init__(self):
        self.raw_data = None
        self.led_green = 27
        self.led_red = 17
        gf.setup_led(self.led_green, self.led_red)
        self.connect_sensor()
        time.sleep(2)
        gf.write_log(CODE_LOG_FILE, "Setup Done")
        gf.dd("Setup Done")

    def main(self):
        gf.write_log(CODE_LOG_FILE, "Start Main Loop")
        gf.dd("Start Main")
        while True:
            raw = self.get_value()
            try:
                if raw:
                    log_Wifi = "log/data_raw_wifi/wifi_{}".format(gf.time_stamp_hour_only())
                    log_ble = "log/data_raw_ble/ble_{}".format(gf.time_stamp_hour_only())

                    if "ADDR" in str(raw) and "RSSI" in str(raw) and "SSID" in str(raw):
                        gf.write_log(log_Wifi, str(raw).replace("\n", ""))
                        gf.write_log(CODE_LOG_FILE, f"Write WiFi log: {raw.strip()}")
                    elif "BLE" in str(raw) and "RSSI" in str(raw):
                        gf.write_log(log_ble, str(raw).replace("\n", ""))
                        gf.write_log(CODE_LOG_FILE, f"Write BLE log: {raw.strip()}")
            except Exception as e:
                exc_type, exc_obj, exc_tb = sys.exc_info()
                fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                err_msg = f"main :: {exc_type} - {fname} - {exc_tb.tb_lineno} - {exc_obj}"
                gf.dd(err_msg)
                gf.write_log(CODE_LOG_FILE, f"ERROR: {err_msg}")
            time.sleep(0.05)

    def connect_sensor(self):
        if globals.hardware:
            connected = False
            while not connected:
                port = auto_detect_serial_port(['CP2102', 'CH340', 'FTDI', 'Silicon', 'USB'])
                if port:
                    try:
                        gf.dd(f"Try to connect sensor :: {port}")
                        gf.write_log(CODE_LOG_FILE, f"Try to connect sensor :: {port}")
                        self.raw_data = serial.Serial(
                            port,
                            baudrate=115200,
                            timeout=1
                        )
                        self.raw_data.reset_input_buffer()
                        time.sleep(3)
                        connected = True
                        gf.led_status("green", self.led_green, self.led_red)
                        gf.write_log(CODE_LOG_FILE, "Sensor connected, LED green ON")
                    except Exception as e:
                        gf.dd(f"connect_sensor > {e}")
                        gf.write_log(CODE_LOG_FILE, f"connect_sensor > {e}")
                        gf.led_status("red", self.led_green, self.led_red)
                else:
                    gf.led_status("red", self.led_green, self.led_red)
                    gf.write_log(CODE_LOG_FILE, "Sensor not connected, LED red ON")
                    time.sleep(2)

    def get_value(self):
        try:
            if globals.hardware and self.raw_data is not None:
                receiver = self.raw_data.readline().decode('ascii')
                return receiver
            else:
                return None
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            err_msg = f"get_value :: {exc_type} - {fname} - {exc_tb.tb_lineno} - {exc_obj}"
            gf.dd(err_msg)
            gf.write_log(CODE_LOG_FILE, f"ERROR: {err_msg}")
            return None

if __name__ == "__main__":
    try:
        main = CollectProgram()
        main.main()
    except KeyboardInterrupt:
        gf.write_log(CODE_LOG_FILE, "Program stopped by user")
        if globals.output:
            GPIO.cleanup()
    except Exception as e:
        gf.write_log(CODE_LOG_FILE, f"FATAL ERROR: {e}")
        if globals.output:
            GPIO.cleanup()
