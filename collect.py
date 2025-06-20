import sys
import os
import json
import time
import serial

import globals
import global_function

if globals.hardware:
    import RPi.GPIO as GPIO

class CollectProgram(object):
    '''
    CollectProgram bertugas menghandle komunikasi dengan sensor,
    menyimpan data dari sensor ke log.
    '''

    def __init__(self):
        self.gf = global_function.globalFunction("collect_program")
        self.raw_data = None
        self.connect_sensor()
        time.sleep(2)
        self.gf.dd("Setup Done")

    def main(self):
        self.gf.dd("Start Main")
        while True:
            raw = self.get_value()
            try:
                if raw:
                    log_Wifi = "log/wifi/mac_{}".format(self.gf.time_stamp_hour_only())
                    log_ble = "log/ble/mac_{}".format(self.gf.time_stamp_hour_only())

                    if "ADDR" in str(raw) and "RSSI" in str(raw) and "SSID" in str(raw):
                        self.gf.write_log(log_Wifi, str(raw).replace("\n", ""))
                    elif "BLE" in str(raw) and "RSSI" in str(raw):
                        self.gf.write_log(log_ble, str(raw).replace("\n", ""))
            except Exception as e:
                exc_type, exc_obj, exc_tb = sys.exc_info()
                fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                self.gf.dd(f"main :: {exc_type} - {fname} - {exc_tb.tb_lineno} - {exc_obj}")
            time.sleep(0.05)

    def connect_sensor(self):
        if globals.hardware:
            while self.raw_data is None:
                find_serial = self.gf.get_port_id()
                for seri in find_serial:
                    if "usb-1a86_USB_Single_Serial_562B012422-if00" in find_serial[seri] or "usb-Silicon_Labs_CP2102_USB" in find_serial[seri]:
                        try:
                            self.gf.dd(f"Try to connect sensor :: {seri} :: {find_serial[seri]}")
                            self.raw_data = serial.Serial(
                                seri,
                                baudrate=115200,
                                timeout=1
                            )
                            self.raw_data.reset_input_buffer()
                            time.sleep(3)
                        except Exception as e:
                            self.gf.dd(f"connect_sensor > {e}")
                time.sleep(1)

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
            self.gf.dd(f"get_value :: {exc_type} - {fname} - {exc_tb.tb_lineno} - {exc_obj}")
            return None

if __name__ == "__main__":
    main = CollectProgram()
    main.main()
