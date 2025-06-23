import time
import os

try:
    import RPi.GPIO as GPIO
except ImportError:
    GPIO = None  # Agar tidak error saat testing di non-RPi

def write_log(log_path, msg):
    """
    Menyimpan log ke file yang ditentukan.
    """
    try:
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        with open(log_path, "a") as f:
            f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} | {msg}\n")
    except Exception as e:
        print(f"Failed to write log: {e}")

def setup_led(led_green=27, led_red=17):
    if GPIO is None:
        return
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(led_green, GPIO.OUT)
    GPIO.setup(led_red, GPIO.OUT)
    led_status("red", led_green, led_red)

def led_status(color, led_green=27, led_red=17):
    if GPIO is None:
        return
    if color == "green":
        GPIO.output(led_green, GPIO.LOW)
        GPIO.output(led_red, GPIO.HIGH)
    elif color == "red":
        GPIO.output(led_green, GPIO.HIGH)
        GPIO.output(led_red, GPIO.LOW)
