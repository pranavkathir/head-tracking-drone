Head-Controlled Drone

****

Control a drone using real-time head movements with Arduino IMU and Python.
This project reads head orientation (pitch, roll, yaw) and converts it into live flight commands.

Demo:

Coming Soon

Features:

- Real-time drone control via head tracking
- Two-way communication between Arduino and Python
- Live telemetry (attitude, battery, link status) to Python dashboard
- Supports directional movement using pitch, roll, and yaw input

Tech Stack:

- Hardware: Arduino Nano, MPU6050 (gyro/IMU), WiFi-enabled drone (e.g., Tello)
- Languages: Python, C++ (Arduino)

How It Works:

- Arduino IMU reads head orientation and sends pitch/roll/yaw over serial
- Python parses IMU data and maps orientation to movement commands
- Drone receives flight commands and responds in real time
- Telemetry is streamed back to a dashboard for monitoring status

- Comms: Serial over USB (Arduino ↔ Python)
