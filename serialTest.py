import serial
import time
import keyboard

ser = serial.Serial('COM3', 9600, timeout=1)

time.sleep(2)  # Give time for Arduino to reset after serial connection

print("Arduino Connected!\n")

# CALIBRATION

print("Ready to Calibrate. When positioned, please press 'c' ")
keyboard.wait('c')
ser.write(b'CALIBRATE\n')

print("Calibrated. Ready to takeoff, please press 't'")
keyboard.wait('t')
# takeoff

try:
    while True:
            
        if (keyboard.is_pressed('l')):
            print("land")
            continue

        
        if ser.in_waiting:

            line = ser.readline().decode('utf-8').strip() #reads the line, decodes it into a string, strips whitespace
        # if not line: #only prints un-empty lines
        #     continue
        # print(line)

        


            if (line == "NEUTRAL"):
                print("Neutral")
            elif (line == "RIGHT"):
                print("Right")
            elif (line == "LEFT"):
                print("Left")
            elif (line == "FORWARD"):
                print("Forward")
            elif (line == "BACKWARD"):
                print("Backward")


               
except KeyboardInterrupt:
    print("\nStopped by user.")
finally:
    
    ser.close()



# try:
#     while True:
#         if (keyboard.is_pressed('q')):
#             print("pressed")
#             time.sleep(.5)

# except KeyboardInterrupt:
#     print("stop")