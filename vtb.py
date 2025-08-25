#!/usr/bin/env python3
import os
import RPi.GPIO as GPIO
import pyaudio
import wave
import whisper
import time
import threading
import hbcvt

class ButtonSTTRecorder:
    def __init__(self, pin=26):
        self.pin, self.recording, self.audio_data = pin, False, []
        self.audio = pyaudio.PyAudio()
        self.stream, self.thread = None, None
        self.chunk, self.format, self.channels, self.rate = 4096, pyaudio.paInt16, 1, 16000
        self.device_index = None
        self.model = whisper.load_model("tiny")
        try: GPIO.cleanup()
        except: pass
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    def start(self):
        if not self.recording:
            self.recording, self.audio_data = True, []
            self.thread = threading.Thread(target=self.record)
            self.thread.start()

    def stop(self):
        if self.recording:
            self.recording = False
            if self.thread: self.thread.join()
            self.process()

    def record(self):
        try:
            self.stream = self.audio.open(format=self.format, channels=self.channels, rate=self.rate, input=True,
                                          input_device_index=self.device_index, frames_per_buffer=self.chunk)
            while self.recording: self.audio_data.append(self.stream.read(self.chunk, exception_on_overflow=False))
        except Exception as e: print(f"Error: {e}")
        finally:
            if self.stream: self.stream.stop_stream(); self.stream.close()

    def process(self):
        if not self.audio_data: return
        file_path = "temp.wav"
        try:
            with wave.open(file_path, 'wb') as wf:
                wf.setnchannels(self.channels); wf.setsampwidth(self.audio.get_sample_size(self.format))
                wf.setframerate(self.rate); wf.writeframes(b''.join(self.audio_data))
            text = self.model.transcribe(file_path, language="ko")["text"].strip()
            braille_cells = hbcvt.h2b.text(text)
            braille_binary = [''.join(map(str, cell)) for item in braille_cells if isinstance(item, list) for cell in item]
            with open("braille_result.txt", 'w', encoding='utf-8') as f: f.write('\n'.join(braille_binary))
        except Exception as e: print(f"Error: {e}")
        finally:
            if os.path.exists(file_path): os.remove(file_path)

    def run(self):
        last_state = GPIO.HIGH
        try:
            while True:
                current_state = GPIO.input(self.pin)
                if current_state != last_state:
                    if current_state == GPIO.LOW: self.start()
                    else: self.stop()
                    last_state = current_state
                time.sleep(0.05)
        except KeyboardInterrupt: self.cleanup()

    def cleanup(self):
        if self.recording: self.recording = False; self.thread.join()
        if self.stream: self.stream.stop_stream(); self.stream.close()
        if self.audio: self.audio.terminate()
        GPIO.cleanup()

def main():
    recorder = ButtonSTTRecorder()
    recorder.run()

if __name__ == "__main__":
    main()
