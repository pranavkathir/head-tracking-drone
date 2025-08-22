import threading
import time
import serial
import keyboard
import tkinter as tk
from tkinter import ttk
from djitellopy import Tello

# =========================
# Settings
# =========================
SPEED = 35
SERIAL_PORT = 'COM3'
BAUD_RATE = 9600
RC_PERIOD = 0.1  # seconds, send RC keepalive at 10 Hz

# =========================
# Shared state (thread-safe via the GIL for simple types)
# =========================
last_command = "NEUTRAL"
rc_state = [0, 0, 0, 0]  # [lr, fb, ud, yaw]
flying = False
killed = False
running = True  # set False to stop background threads

# =========================
# Connect Arduino (Serial)
# =========================
try:
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
    time.sleep(2)  # let Arduino reset
    serial_ok = True
except Exception as e:
    print(f"[WARN] Could not open serial {SERIAL_PORT}: {e}")
    ser = None
    serial_ok = False

# =========================
# Connect Tello
# =========================
tello = Tello()
try:
    tello.connect()
    tello_ok = True
except Exception as e:
    print(f"[ERROR] Tello connect failed: {e}")
    tello_ok = False

# =========================
# Tkinter UI setup
# =========================
root = tk.Tk()
root.title("Hands-Free Drone Dashboard")
root.geometry("520x360")
root.configure(bg="#0f1220")

style = ttk.Style()
style.theme_use("clam")
style.configure("TLabel", background="#0f1220", foreground="#e8e8e8", font=("Segoe UI", 11))
style.configure("Header.TLabel", background="#0f1220", foreground="#00f5d4", font=("Segoe UI", 15, "bold"))
style.configure("Info.TLabel", background="#171a2c", foreground="#ffffff", font=("Segoe UI", 11))
style.configure("TButton", font=("Segoe UI", 11, "bold"))

header = ttk.Label(root, text="Hands-Free Drone Dashboard", style="Header.TLabel")
header.pack(pady=10)

frame = tk.Frame(root, bg="#171a2c")
frame.pack(padx=14, pady=10, fill="both", expand=True)

battery_label = ttk.Label(frame, text="Battery: -- %", style="Info.TLabel")
height_label  = ttk.Label(frame, text="Height: -- cm", style="Info.TLabel")
temp_label    = ttk.Label(frame, text="Temp: -- °C", style="Info.TLabel")
cmd_label     = ttk.Label(frame, text="Last Cmd: --", style="Info.TLabel")
rc_label      = ttk.Label(frame, text="RC: [0, 0, 0, 0]", style="Info.TLabel")
link_label    = ttk.Label(frame, text="Link: OK" if tello_ok else "Link: OFFLINE", style="Info.TLabel")

for i, w in enumerate([battery_label, height_label, temp_label, cmd_label, rc_label, link_label]):
    w.grid(row=i, column=0, sticky="w", padx=10, pady=6)

btn_row = tk.Frame(root, bg="#0f1220")
btn_row.pack(pady=6)

def safe_get(fn, fallback="--"):
    try:
        v = fn()
        return v if v is not None else fallback
    except Exception:
        return fallback

def update_dashboard():
    """Refresh GUI labels every 500 ms (safe telemetry)."""
    battery = safe_get(tello.get_battery, "--") if tello_ok else "--"
    height  = safe_get(tello.get_height,  "--") if tello_ok else "--"
    temp    = safe_get(tello.get_temperature, "--") if tello_ok else "--"

    battery_label.config(text=f"Battery: {battery}%")
    height_label.config(text=f"Height: {height} cm")
    temp_label.config(text=f"Temp: {temp} °C")
    cmd_label.config(text=f"Last Cmd: {last_command}")
    rc_label.config(text=f"RC: {rc_state}")
    link_label.config(text="Link: OK" if tello_ok else "Link: OFFLINE")

    root.after(500, update_dashboard)

# =========================
# Control actions
# =========================
def do_calibrate():
    if not serial_ok: return
    try:
        ser.write(b"CALIBRATE\n")
    except Exception as e:
        print(f"[WARN] CALIBRATE send failed: {e}")

def do_takeoff():
    global flying
    if not tello_ok or killed: return
    try:
        tello.takeoff()
        flying = True
    except Exception as e:
        print(f"[WARN] takeoff failed: {e}")

def do_land():
    global flying
    if not tello_ok: return
    try:
        tello.land()
        flying = False
        # Reset rc to neutral
        rc_state[0] = rc_state[1] = rc_state[2] = rc_state[3] = 0
    except Exception as e:
        print(f"[WARN] land failed: {e}")

def do_emergency():
    global killed, flying
    if not tello_ok: return
    try:
        tello.emergency()
    except Exception as e:
        print(f"[WARN] emergency failed: {e}")
    killed = True
    flying = False
    rc_state[0] = rc_state[1] = rc_state[2] = rc_state[3] = 0

# Buttons
cal_btn  = ttk.Button(btn_row, text="Calibrate", command=do_calibrate)
tkoff_btn= ttk.Button(btn_row, text="Takeoff",  command=do_takeoff)
land_btn = ttk.Button(btn_row, text="Land",     command=do_land)
emer_btn = ttk.Button(btn_row, text="EMERGENCY", command=do_emergency)

cal_btn.grid(row=0, column=0, padx=8)
tkoff_btn.grid(row=0, column=1, padx=8)
land_btn.grid(row=0, column=2, padx=8)
emer_btn.grid(row=0, column=3, padx=8)

hint = ttk.Label(root, text="Keyboard: C=Calibrate  T=Takeoff  L=Land  Ctrl+C=Emergency", style="TLabel")
hint.pack(pady=4)

# =========================
# Background threads
# =========================
def control_loop():
    """Read Arduino lines, map to RC, and honor keyboard overrides."""
    global last_command, rc_state, running, flying

    while running:
        # Keyboard overrides (optional, for convenience)
        if keyboard.is_pressed('c'):
            do_calibrate()
            time.sleep(0.25)  # debounce
        if keyboard.is_pressed('t'):
            do_takeoff()
            time.sleep(0.25)
        if keyboard.is_pressed('l'):
            do_land()
            time.sleep(0.25)

        # Read serial line safely
        if serial_ok and ser and ser.in_waiting:
            try:
                line = ser.readline().decode('utf-8', errors='ignore').strip()
            except Exception:
                line = ""

            if line:
                # Default neutral each message; set one axis per command
                lr, fb, ud, yaw = 0, 0, 0, 0

                if line == "NEUTRAL":
                    last_command = "NEUTRAL"
                elif line == "RIGHT":
                    lr = SPEED; last_command = "RIGHT"
                elif line == "LEFT":
                    lr = -SPEED; last_command = "LEFT"
                elif line == "FORWARD":
                    fb = SPEED; last_command = "FORWARD"
                elif line == "BACKWARD":
                    fb = -SPEED; last_command = "BACKWARD"
                elif line == "YAW_RIGHT":
                    yaw = 40; last_command = "YAW_RIGHT"
                elif line == "YAW_LEFT":
                    yaw = -40; last_command = "YAW_LEFT"
                elif line == "UP":
                    ud = SPEED; last_command = "UP"
                elif line == "DOWN":
                    ud = -SPEED; last_command = "DOWN"

                # Update shared rc_state (persist until next update)
                rc_state[0] = lr
                rc_state[1] = fb
                rc_state[2] = ud
                rc_state[3] = yaw

        time.sleep(0.01)

def rc_sender_loop():
    """Send rc_state to Tello at steady rate (keepalive & smooth control)."""
    global running
    while running:
        if tello_ok and not killed:
            try:
                tello.send_rc_control(rc_state[0], rc_state[1], rc_state[2], rc_state[3])
            except Exception as e:
                # If Wi-Fi hiccups, don't crash the app
                pass
        time.sleep(RC_PERIOD)

# =========================
# Clean shutdown
# =========================
def on_close():
    global running
    running = False
    try:
        if ser and ser.is_open:
            ser.close()
    except:
        pass
    try:
        if tello_ok:
            # Try to land if still flying
            if flying and not killed:
                try:
                    tello.land()
                except:
                    pass
            tello.end()
    except:
        pass
    root.destroy()

root.protocol("WM_DELETE_WINDOW", on_close)

# =========================
# Start everything
# =========================
threading.Thread(target=control_loop, daemon=True).start()
threading.Thread(target=rc_sender_loop, daemon=True).start()
update_dashboard()
root.mainloop()
