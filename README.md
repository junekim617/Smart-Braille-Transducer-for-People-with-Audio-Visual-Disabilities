# Smart-Braille-Transducer-for-People-with-Audio-Visual-Disabilities

The Braille System is a real-time, voice-to-braille conversion and display system. It uses a Raspberry Pi to listen to spoken language, convert it to Korean braille, and then send the corresponding commands to an Arduino connected to a physical braille display. The system is designed to be user-friendly, allowing for hands-free operation through button presses.

Key Features
1) Voice-to-Text (STT): Captures audio input and converts it to text using a local Whisper model.
2) Text-to-Braille Conversion: Converts the recognized Korean text into braille cells.
3) Physical Braille Display: Sends commands to a connected Arduino board to control servos, which in turn manipulate a physical braille display.
4) Seamless Operation: A dedicated launcher script manages and monitors the entire system, automatically restarting services if they fail.


Components and Architecture

1. startup_launcher.sh
This is the main orchestration script. It ensures the entire system runs smoothly by:
Starting the two core services (vtb.py and command.py).
Logging all activities to a dedicated log file (/var/log/braille_system.log).
Monitoring the services and automatically restarting them if they crash.
Gracefully shutting down all processes upon receiving a termination signal (e.g., Ctrl+C).

2. vtb.py (Voice-to-Braille Service)
This Python script handles the voice input and braille conversion logic.
Voice Recognition: It uses the Whisper library to transcribe audio captured from a connected microphone.
Korean Braille Conversion: The hbcvt library is used to convert the transcribed Korean text into braille format.
File Output: The resulting braille data is saved as a series of binary codes (0s and 1s) in the braille_result.txt file.

3. command.py (Braille Reader Service)
This Python script acts as the bridge between the digital braille data and the physical hardware.
File Monitoring: It uses watchdog to continuously monitor the braille_result.txt file. When the file is updated by vtb.py, it triggers a new process.
GPIO Button Control: It sets up GPIO pins on the Raspberry Pi to handle two button inputs. One button is used to navigate forward through the braille commands, and the other is used to navigate backward.
Serial Communication: It establishes a serial connection with the Arduino to send commands.
Braille Command Transmission: It reads the braille data from braille_result.txt and sends the appropriate commands (e.g., 'A', 'B', 'C', 'D') to the Arduino to control the servo motors.

5. motor.ino (Arduino Code)
This is the firmware that runs on the Arduino board.
Serial Input: It listens for incoming commands sent from the Raspberry Pi via the serial port.
Servo Control: It receives command characters ('A', 'B', 'C', 'D') and maps them to specific angles to control three servo motors.
Physical Display: The servos physically move a braille cell, allowing a user to read the converted text through touch.
