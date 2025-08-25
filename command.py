#!/usr/bin/env python3
import serial
import time
import os
import RPi.GPIO as GPIO
import threading
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import glob

BAUD_RATE, PIN_A, PIN_B = 9600, 17, 27
file_to_watch = "braille_result.txt"
all_commands, current_index, command_block_size = [], 0, 3
ser, restart_flag = None, False

class BrailleFileHandler(FileSystemEventHandler):
    def on_modified(self, event):
        global restart_flag
        if not event.is_directory and event.src_path.endswith(file_to_watch):
            restart_flag = True

def find_arduino_port():
    ports = glob.glob('/dev/ttyACM*') + glob.glob('/dev/ttyUSB*')
    return ports[0] if ports else None

def reconnect_serial():
    global ser
    try:
        if ser and ser.is_open: ser.close()
        port = find_arduino_port()
        if not port: return False
        ser = serial.Serial(port, BAUD_RATE, timeout=1)
        time.sleep(2)
        return True
    except: return False

def send_commands_to_serial(block):
    global ser
    if not ser or not ser.is_open:
        if not reconnect_serial(): return False
    try:
        ser.write("".join(block).encode('utf-8'))
        return True
    except serial.SerialException:
        if reconnect_serial(): return send_commands_to_serial(block)
        return False
    except: return False

def reset_all_servos():
    if not ser or not ser.is_open: return False
    try:
        ser.write("AAA".encode('utf-8'))
        time.sleep(1)
        return True
    except: return False

def get_command_for_state(state: list[int]) -> str:
    val_b, val_c = state
    if val_b == 0: return "A" if val_c == 0 else "B"
    return "C" if val_c == 0 else "D"

def read_braille_data_from_file(filename="braille_result.txt"):
    if not os.path.exists(filename): return None
    commands = []
    try:
        with open(filename, "r", encoding="utf-8") as f:
            for line in f:
                bin = line.strip()
                if len(bin) == 6 and all(c in '01' for c in bin):
                    commands.append(get_command_for_state([int(bin[0]), int(bin[3])]))
                    commands.append(get_command_for_state([int(bin[1]), int(bin[4])]))
                    commands.append(get_command_for_state([int(bin[2]), int(bin[5])]))
    except: return None
    return commands

def on_button_a_pressed(channel):
    global current_index
    current_index = max(0, current_index - command_block_size)
    send_commands_to_serial(all_commands[current_index:current_index + command_block_size])

def on_button_b_pressed(channel):
    global current_index
    if len(all_commands) > 0:
        current_index = min(len(all_commands) - command_block_size, current_index + command_block_size)
    send_commands_to_serial(all_commands[current_index:current_index + command_block_size])

def setup_gpio():
    GPIO.cleanup()
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(PIN_A, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(PIN_B, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.add_event_detect(PIN_A, GPIO.FALLING, callback=on_button_a_pressed, bouncetime=200)
    GPIO.add_event_detect(PIN_B, GPIO.FALLING, callback=on_button_b_pressed, bouncetime=200)

def setup_file_monitor():
    observer = Observer()
    observer.schedule(BrailleFileHandler(), path='.', recursive=False)
    observer.start()
    return observer

def initialize_system():
    global all_commands, current_index, restart_flag
    restart_flag, current_index = False, 0
    all_commands = read_braille_data_from_file(file_to_watch)
    if not all_commands: return False
    reset_all_servos()
    send_commands_to_serial(all_commands[current_index:current_index + command_block_size])
    return True

def main():
    global ser, restart_flag
    SERIAL_PORT = find_arduino_port()
    if not SERIAL_PORT: return
    try:
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
        time.sleep(2)
        setup_gpio()
        observer = setup_file_monitor()
        if not initialize_system(): return
        while True:
            if restart_flag:
                if not initialize_system(): break
            time.sleep(0.1)
    except Exception as e:
        if isinstance(e, serial.SerialException): print(f"Serial error: {e}")
        elif isinstance(e, KeyboardInterrupt): print("\nShutting down...")
        else: print(f"An error occurred: {e}")
    finally:
        try:
            if 'observer' in locals(): observer.stop(); observer.join()
        except: pass
        if ser and ser.is_open: reset_all_servos(); ser.close()
        GPIO.cleanup()

if __name__ == "__main__":
    main()
