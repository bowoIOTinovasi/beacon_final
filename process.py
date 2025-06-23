import os
import sys
import time
import json
import statistics

import globals
import globals_function as gf

CODE_LOG_FILE = "log/code/log_process.log"

class ProcessProgram(object):
    '''
    Program ini bertugas memproses data log WiFi dan BLE,
    baik untuk counting mode maupun indoor tracking mode.
    '''

    def __init__(self):
        self.pass_counting_noise = 3600
        self.menit_trigger_count = 1
        gf.write_log(CODE_LOG_FILE, "Process Setup Done")
        gf.dd("Process Setup Done")

    def main(self):
        gf.write_log(CODE_LOG_FILE, "Start Main Loop")
        gf.dd("Start Main")
        while True:
            try:
                if not globals.indoortracking_mode:
                    self.counting_mode()
                else:
                    self.indoor_tracking_mode()
                time.sleep(2)
            except Exception as e:
                exc_type, exc_obj, exc_tb = sys.exc_info()
                fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                err_msg = f"main :: {exc_type} - {fname} - {exc_tb.tb_lineno} - {exc_obj}"
                gf.dd(err_msg)
                gf.write_log(CODE_LOG_FILE, f"ERROR: {err_msg}")
                time.sleep(2)

    def counting_mode(self):
        # Cek file log wifi yang belum diproses
        list_wifi = self.check_data_before_process()
        if not list_wifi:
            return

        for list_wifi_file in list_wifi:
            # Proses WiFi
            list_wifi_sorted = self.sort_data_and_save_to_variable_wifi(list_wifi_file)
            count_total_wifi, list_mac_wifi, obj_mac_wifi, dwelling_wifi, dwelling_wifi_mean = self.count_wifi(list_wifi_sorted, list_wifi_file, list_wifi)
            dwelling_count_wifi, _ = self.get_dwelling_count(obj_mac_wifi)

            # Simpan hasil WiFi
            clean0 = list_wifi_file.replace("log/wifi/", "")
            clean1 = clean0.replace(".log", f":{self.minute_only()}:{self.second_only()}")
            date_time = clean1.replace("mac_", "")
            nam = list_wifi_file.replace("log/wifi/", "log/wifi_result/")
            name = nam.replace(".log", "")
            content = {
                "date_time": date_time,
                "total_wifi": count_total_wifi,
                "dwelling_wifi": dwelling_wifi,
                "dwelling_wifi_mean": dwelling_wifi_mean,
                "dwelling_count_wifi": dwelling_count_wifi,
                "list_wifi": list_mac_wifi
            }
            content_time = {
                "duration": obj_mac_wifi
            }
            gf.write_log(name, json.dumps(content))
            gf.write_log(name, json.dumps(content_time))

            # Proses BLE (jika ada file BLE yang sesuai)
            try:
                list_ble_file = list_wifi_file.replace("log/wifi/", "log/ble/")
                list_ble_sorted = self.sort_data_and_save_to_variable_ble(list_ble_file)
                count_total_ble, list_mac_ble, obj_mac_ble, dwelling_ble, dwelling_ble_mean = self.count_ble(list_ble_sorted)
                dwelling_count_ble, _ = self.get_dwelling_count(obj_mac_ble)

                clean0 = list_ble_file.replace("log/ble/", "")
                clean1 = clean0.replace(".log", f":01:01")
                date_time_ble = clean1.replace("mac_", "")
                nam_ble = list_ble_file.replace("log/ble/", "log/ble_result/")
                name_ble = nam_ble.replace(".log", "")
                content_ble = {
                    "date_time": date_time_ble,
                    "total_ble": count_total_ble,
                    "dwelling_ble": dwelling_ble,
                    "dwelling_ble_mean": dwelling_ble_mean,
                    "dwelling_count_ble": dwelling_count_ble,
                    "list_ble": list_mac_ble
                }
                content_time_ble = {
                    "duration": obj_mac_ble
                }
                gf.write_log(name_ble, json.dumps(content_ble))
                gf.write_log(name_ble, json.dumps(content_time_ble))
            except Exception as e:
                gf.dd(f"counting_mode BLE :: {e}")

            # (Optional) update global status, dsb, sesuai kebutuhan Anda

    def check_data_before_process(self):
        # Mirip sniff_process.py, cek file log wifi yang belum diproses
        list_files = []
        wifi_result = self.list_file_in_folder("log/wifi_result")
        try:
            if wifi_result:
                list_wifis = self.list_file_in_folder("log/wifi")
                if len(list_wifis) > 0:
                    for log_wifi in list_wifis:
                        log_file_wifi = log_wifi.replace("log/wifi", "log/wifi_result")
                        if not log_file_wifi in wifi_result:
                            convert = self.menit_trigger_count * 60
                            convert_min = convert - 10
                            if self.minute_only_to_seconds() >= convert_min and self.minute_only_to_seconds() <= convert:
                                if not gf.time_stamp_hour_only() in log_wifi:
                                    gf.dd(f"BLE -> {log_wifi}")
                                    list_files.append(log_wifi)
            else:
                list_wifis = self.list_file_in_folder("log/wifi")
                if len(list_wifis) > 0:
                    for log_wifi in list_wifis:
                        if not gf.time_stamp_hour_only() in log_wifi:
                            gf.dd(f"WiFi -> {log_wifi}")
                            list_files.append(log_wifi)
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            gf.dd(f"check_data_before_process :: {exc_type} - {fname} - {exc_tb.tb_lineno} - {exc_obj}")
        return list_files

    # --- Helper functions ---
    def list_file_in_folder(self, folder):
        try:
            return [os.path.join(folder, f) for f in os.listdir(folder) if os.path.isfile(os.path.join(folder, f))]
        except Exception:
            return []

    def minute_only(self):
        return time.strftime("%M")

    def second_only(self):
        return time.strftime("%S")

    def minute_only_to_seconds(self):
        return int(time.strftime("%M")) * 60 + int(time.strftime("%S"))

    # --- Data parsing and counting (adaptasi dari sniff_process.py) ---
    def sort_data_and_save_to_variable_wifi(self, list_wifi_name):
        result_wifi = {}
        gf.dd(f"Wifi Name - {list_wifi_name}")
        try:
            with open(list_wifi_name, "r") as f:
                read_data = f.read()
        except Exception:
            return result_wifi
        if read_data:
            data_split_by_enter = read_data.split("\n")
            for data in data_split_by_enter:
                base_data = data.split(" - ")
                date_time_from_data = base_data[0] if base_data else None
                mac_address_from_data = None
                rssi_from_data = None
                split_base_data = data.split(",")
                try:
                    if "ADDR=" in split_base_data[0] and "RSSI=" in split_base_data[2]:
                        split_mac = split_base_data[0].split("=")
                        mac = split_mac[1]
                        if len(mac) >= 16:
                            mac_address_from_data = mac
                        split_rssi = split_base_data[2].split("=")
                        rssi_negatif = split_rssi[1][0:3]
                        if rssi_negatif:
                            try:
                                rssi_neg = int(rssi_negatif) * -1
                                rssi_from_data = int(rssi_neg)
                            except:
                                rssi_from_data = ""
                except Exception:
                    pass
                if date_time_from_data and mac_address_from_data and rssi_from_data:
                    dump_data = []
                    save_data = {
                        "dt": date_time_from_data,
                        "rssi": rssi_from_data
                    }
                    if not mac_address_from_data in result_wifi:
                        dump_data.append(save_data)
                        result_wifi[mac_address_from_data] = dump_data
                    else:
                        dump_data = result_wifi[mac_address_from_data]
                        dump_data.append(save_data)
                        result_wifi[mac_address_from_data] = dump_data
        return result_wifi

    def sort_data_and_save_to_variable_ble(self, list_ble_name):
        result_ble = {}
        gf.dd(f"ble Name - {list_ble_name}")
        try:
            with open(list_ble_name, "r") as f:
                read_data = f.read()
        except Exception:
            return result_ble
        if read_data:
            data_split_by_enter = read_data.split("\n")
            for data in data_split_by_enter:
                base_data = data.split(" - ")
                date_time_from_data = base_data[0] if base_data else None
                mac_address_from_data = None
                rssi_from_data = None
                split_base_data = data.split(",")
                try:
                    if "BLE=" in split_base_data[0] and "RSSI=" in split_base_data[1]:
                        split_mac = split_base_data[0].split("=")
                        mac = split_mac[1]
                        if len(mac) >= 16:
                            mac_address_from_data = mac
                        split_rssi = split_base_data[1].split("=")
                        rssi_negatif = split_rssi[1][0:3]
                        if rssi_negatif:
                            try:
                                rssi_neg = int(rssi_negatif) * -1
                                rssi_from_data = int(rssi_neg)
                            except:
                                rssi_from_data = ""
                except Exception:
                    pass
                if date_time_from_data and mac_address_from_data and rssi_from_data:
                    dump_data = []
                    save_data = {
                        "dt": date_time_from_data,
                        "rssi": rssi_from_data
                    }
                    if not mac_address_from_data in result_ble:
                        dump_data.append(save_data)
                        result_ble[mac_address_from_data] = dump_data
                    else:
                        dump_data = result_ble[mac_address_from_data]
                        dump_data.append(save_data)
                        result_ble[mac_address_from_data] = dump_data
        return result_ble

    def count_wifi(self, list_wifi_sorted, list_wifi_file, list_wifi):
        # Implementasi mirip sniff_process.py, bisa diadaptasi sesuai kebutuhan
        # Untuk ringkas, return dummy
        return 0, [], {}, 0, 0

    def count_ble(self, list_ble_sorted):
        # Implementasi mirip sniff_process.py, bisa diadaptasi sesuai kebutuhan
        # Untuk ringkas, return dummy
        return 0, [], {}, 0, 0

    def get_dwelling_count(self, obj_mac):
        # Implementasi mirip sniff_process.py, bisa diadaptasi sesuai kebutuhan
        # Untuk ringkas, return dummy
        return [0, 0, 0], 0

    def indoor_tracking_mode(self):
        # Implementasi sesuai kebutuhan Anda
        pass

if __name__ == "__main__":
    try:
        main = ProcessProgram()
        main.main()
    except KeyboardInterrupt:
        gf.write_log(CODE_LOG_FILE, "Program stopped by user")
    except Exception as e:
        gf.write_log(CODE_LOG_FILE, f"FATAL ERROR: {e}")
