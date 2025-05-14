from ultralytics import YOLO
import cv2
import pygame
import threading
import time

# Load YOLOv8 model
model = YOLO("yolov8n.pt")
PHONE_CLASS_ID = 67  # COCO class ID for "cell phone"

# Initialize pygame mixer
pygame.mixer.init()
alert_sound = pygame.mixer.Sound("static/sounds/alert.wav")

# Control sound playback frequency
last_played = 0
def play_alert():
    global last_played
    now = time.time()
    if now - last_played > 3:
        last_played = now
        threading.Thread(target=alert_sound.play, daemon=True).start()

# Start webcam
cap = cv2.VideoCapture(0)

while cap.isOpened():
    success, frame = cap.read()
    if not success:
        break

    results = model(frame)[0]

    for box in results.boxes:
        cls = int(box.cls[0])
        if cls == PHONE_CLASS_ID:
            play_alert()
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 2)
            cv2.putText(frame, "Phone", (x1, y1 - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 255), 2)

    cv2.imshow("Phone Detector", frame)
    if cv2.waitKey(1) & 0xFF == 27:
        break

cap.release()
cv2.destroyAllWindows()
