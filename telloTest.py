from djitellopy import Tello
import time

# Create Tello object
tello = Tello()

# Connect to the drone
tello.connect()

print(f"Battery: {tello.get_battery()}%")

# Take off
tello.takeoff()

# Land
tello.land()
tello.end()

print("Done!")
