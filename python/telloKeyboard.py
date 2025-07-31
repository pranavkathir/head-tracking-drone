import time
import keyboard
from djitellopy import Tello

# Create Tello object and connect
tello = Tello()
tello.connect()
print(f"Battery: {tello.get_battery()}%")

# Takeoff trigger
print("Ready to takeoff. Press 't'")
keyboard.wait('t')
tello.takeoff()
print("Takeoff!")

try:
    while True:
        # LAND if 'l' is pressed
        if keyboard.is_pressed('l'):
            print("Landing...")
            tello.send_rc_control(0, 0, 0, 0)
            tello.land()
            break  # exit loop after landing

        # Initialize RC values
        lr = 0  # left/right
        fb = 0  # forward/backward
        ud = 0  # up/down
        yaw = 0 # rotation

        # Movement keys
        if keyboard.is_pressed('w'):
            fb = 20
            print("Forward")
        elif keyboard.is_pressed('s'):
            fb = -20
            print("Backward")

        if keyboard.is_pressed('a'):
            lr = -20
            print("Left")
        elif keyboard.is_pressed('d'):
            lr = 20
            print("Right")

        if keyboard.is_pressed('q'):
            print("Neutral (hover)")

        # Send RC control every loop
        tello.send_rc_control(lr, fb, ud, yaw)

        time.sleep(0.1)  # small delay to avoid overloading the drone

except KeyboardInterrupt:
    print("\nEmergency stop by user.")
    tello.send_rc_control(0, 0, 0, 0)
    tello.land()

finally:
    tello.end()
