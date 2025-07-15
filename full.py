import serial
import time
import keyboard
from djitellopy import Tello

speed = 35

# Setup serial connection to Arduino
ser = serial.Serial('COM3', 9600, timeout=1)
time.sleep(2)  # Arduino reset delay

print("Arduino Connected!\n")

# Create Tello drone object and connect
tello = Tello()
tello.connect()
print(f"Battery: {tello.get_battery()}%")

# Calibration phase
print("Ready to Calibrate. When positioned, please press 'c' ")
keyboard.wait('c')
ser.write(b'CALIBRATE\n')
print("Calibration command sent to Arduino.")

print("Calibrated. Ready to takeoff, please press 't'")
keyboard.wait('t')
tello.takeoff()
print("Drone has taken off!")

try:
    while True:
        # Landing command
        if keyboard.is_pressed('l'):
            print("Landing...")
            tello.land()
            tello.end()
            break  # exit loop after landing
        
        # Read Arduino serial for tilt commands
        if ser.in_waiting:
            line = ser.readline().decode('utf-8').strip()

            if line == "NEUTRAL":
                tello.send_rc_control(0, 0, 0, 0)
                print("Neutral")

            elif line == "RIGHT":
                tello.send_rc_control(speed, 0, 0, 0)
                print("Right")

            elif line == "LEFT":
                tello.send_rc_control(-speed, 0, 0, 0)
                print("Left")

            elif line == "FORWARD":
                tello.send_rc_control(0, speed, 0, 0)
                print("Forward")

            elif line == "BACKWARD":
                tello.send_rc_control(0, -speed, 0, 0)
                print("Backward")

        time.sleep(0.05)  # small delay for smoother command timing

except KeyboardInterrupt:
    print("\nEmergency Stop (Ctrl+C) detected! Landing drone...")
    try:
        tello.land()
    except Exception as e:
        print(f"Error during landing: {e}")
    finally:
        try:
            tello.end()
        except:
            pass
        ser.close()
    print("Cleanup complete. Program exited safely.")

finally:
    if ser.is_open:
        ser.close()
    try:
        tello.end()
    except:
        pass
