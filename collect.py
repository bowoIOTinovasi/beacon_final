import sys
import os
import json
import time
import serial

import globals
import global_function
import globals_function as gf

import RPi.GPIO as GPIO

LOG_COLLECT = "log/code/log_collect.log"

def write_collect_log(msg):
    try:
        with open(LOG_COLLECT, "a") as f:
            f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} | {msg}\n")
    except Exception as e:
        print(f"Failed to write log: {e}")

class CollectProgram(object):
    '''
    CollectProgram bertugas menghandle komunikasi dengan sensor,
    menyimpan data dari sensor ke log, dan mengatur LED status koneksi.
    '''

    def __init__(self):
        self.gf = global_function.globalFunction("collect_program")
        self.raw_data = None
        self.led_green = 27
        self.led_red = 17
        gf.setup_led(self.led_green, self.led_red)
        self.connect_sensor()
        time.sleep(2)
        gf.write_collect_log("Setup Done")
        self.gf.dd("Setup Done")

    def main(self):
        gf.write_collect_log("Start Main Loop")
        self.gf.dd("Start Main")
        while True:
            raw = self.get_value()
            try:
                if raw:
                    log_Wifi = "log/data_raw_wifi/wifi_{}".format(self.gf.time_stamp_hour_only())
                    log_ble = "log/data_raw_ble/ble_{}".format(self.gf.time_stamp_hour_only())

                    if "ADDR" in str(raw) and "RSSI" in str(raw) and "SSID" in str(raw):
                        self.gf.write_log(log_Wifi, str(raw).replace("\n", ""))
                        gf.write_collect_log(f"Write WiFi log: {raw.strip()}")
                    elif "BLE" in str(raw) and "RSSI" in str(raw):
                        self.gf.write_log(log_ble, str(raw).replace("\n", ""))
                        gf.write_collect_log(f"Write BLE log: {raw.strip()}")
            except Exception as e:
                exc_type, exc_obj, exc_tb = sys.exc_info()
                fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                err_msg = f"main :: {exc_type} - {fname} - {exc_tb.tb_lineno} - {exc_obj}"
                self.gf.dd(err_msg)
                gf.write_collect_log(f"ERROR: {err_msg}")
            time.sleep(0.05)

    def connect_sensor(self):
        if globals.hardware:
            connected = False
            while not connected:
                find_serial = self.gf.get_port_id()
                for seri in find_serial:
                    if "usb-1a86_USB_Single_Serial_562B012422-if00" in find_serial[seri] or "usb-Silicon_Labs_CP2102_USB" in find_serial[seri]:
                        try:
                            self.gf.dd(f"Try to connect sensor :: {seri} :: {find_serial[seri]}")
                            gf.write_collect_log(f"Try to connect sensor :: {seri} :: {find_serial[seri]}")
                            self.raw_data = serial.Serial(
                                seri,
                                baudrate=115200,
                                timeout=1
                            )
                            self.raw_data.reset_input_buffer()
                            time.sleep(3)
                            connected = True
                            gf.led_status("green", self.led_green, self.led_red)
                            gf.write_collect_log("Sensor connected, LED green ON")
                            break
                        except Exception as e:
                            self.gf.dd(f"connect_sensor > {e}")
                            gf.write_collect_log(f"connect_sensor > {e}")
                            gf.led_status("red", self.led_green, self.led_red)
                if not connected:
                    gf.led_status("red", self.led_green, self.led_red)
                    gf.write_collect_log("Sensor not connected, LED red ON")
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
            self.gf.dd(err_msg)
            gf.write_collect_log(f"ERROR: {err_msg}")
            return None

if __name__ == "__main__":
    try:
        main = CollectProgram()
        main.main()
    except KeyboardInterrupt:
        gf.write_collect_log("Program stopped by user")
        GPIO.cleanup()
    except Exception as e:
        gf.write_collect_log(f"FATAL ERROR: {e}")
        GPIO.cleanup()
