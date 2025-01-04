import os
import time
import io
import numpy as np
from datetime import datetime
from PIL import Image, ImageChops
import picamera
import subprocess

# Uchovávání posledního snímku pro detekci pohybu
last_frame = None
sensitivity_percentage = 20  # Nastavení citlivosti
last_saved_time = None

# Funkce pro ukládání snímků při detekci pohybu
def save_images_on_motion(initial_frame, changed_frame):
    timestamp = datetime.now().strftime('%Y%m%d_%H_%M')
    folder_path = os.path.join('templates', 'pic', timestamp)
    os.makedirs(folder_path, exist_ok=True)

    with open(os.path.join(folder_path, 'initial.jpg'), 'wb') as f:
        f.write(initial_frame)
    with open(os.path.join(folder_path, 'changed.jpg'), 'wb') as f:
        f.write(changed_frame)

    # Spuštění skriptu LEDm.py po zaznamenání a uložení snímků
    try:
        subprocess.run(["python3", "/opt/camera_stream/LEDm.py"], check=True)
        print("LEDm.py script executed successfully")
    except subprocess.CalledProcessError as e:
        print(f"Failed to execute LEDm.py: {e}")


# Funkce pro detekci pohybu
def detect_motion(current_frame):
    global last_frame, last_saved_time

    if last_frame is None:
        last_frame = current_frame
        return False

    img1 = Image.open(io.BytesIO(last_frame))
    img2 = Image.open(io.BytesIO(current_frame))
    diff = ImageChops.difference(img1, img2)
    total_pixels = img1.size[0] * img1.size[1]
    diff_np = np.array(diff)
    diff_pixels = np.sum(diff_np > 30)
    percentage_diff = (diff_pixels / total_pixels) * 100

    # Vypiš hodnoty do logu
    print(f"Sensitivity: {sensitivity_percentage}%")
    print(f"Image difference: {percentage_diff:.2f}%")

    if percentage_diff > sensitivity_percentage:
        current_time = datetime.now()
        if last_saved_time is None or (current_time - last_saved_time).total_seconds() >= 60:
            save_images_on_motion(last_frame, current_frame)
            last_saved_time = current_time

    last_frame = current_frame

# Funkce pro spuštění kamery a detekce na pozadí
def start_detection():
    with picamera.PiCamera() as camera:
        camera.resolution = (640, 460)
        camera.framerate = 90
        stream = io.BytesIO()

        for _ in camera.capture_continuous(stream, 'jpeg', use_video_port=True):
            stream.seek(0)
            current_frame = stream.read()
            detect_motion(current_frame)
            stream.seek(0)
            stream.truncate()
            time.sleep(0.1)  # Mírná prodleva pro snížení zátěže CPU

if __name__ == "__main__":
    start_detection()
