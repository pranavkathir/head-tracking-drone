from ultralytics import YOLO
from djitellopy import Tello
import cv2

# Load model
model = YOLO("yolov8n.pt")

# Connect to drone
tello = Tello()
tello.connect()
tello.streamon()

try:
    while True:
        frame = tello.get_frame_read().frame
        results = model(frame)[0]

        for box in results.boxes:
            cls = int(box.cls[0])
            label = model.names[cls]
            conf = box.conf[0]
            x1, y1, x2, y2 = map(int, box.xyxy[0])

            # Draw box
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0,255,0), 2)
            cv2.putText(frame, f"{label} {conf:.2f}", (x1, y1 - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,255,0), 2)

        cv2.imshow("Tello + YOLOv8", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

finally:
    tello.streamoff()
    tello.end()
    cv2.destroyAllWindows()
