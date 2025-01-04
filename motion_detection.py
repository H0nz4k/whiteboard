import os
import time
import io
import numpy as np
from datetime import datetime
from PIL import Image, ImageChops, ImageEnhance
import picamera
import subprocess
from collections import deque
import requests  # Pro odesílání notifikací

# Nastavení citlivosti, času ignorování pohybu a odesílání upozornění
sensitivity_percentage = 55  # Čím vyšší číslo, tím větší změna je potřeba pro detekci
pixel_threshold = 150  # Počet pixelů, které se musí změnit, aby byla změna považována za významnou
ignore_motion_duration = 3   # Počet sekund ignorování pohybu po detekci
motion_end_delay = 2  # Počet sekund, kdy po ukončení pohybu ukládáme snímek
send_notifications = False     # Pokud je True, budou odesílány notifikace
ntfy_topic = "picam"           # Zadej název svého kanálu
ntfy_url = f"https://ntfy.sh/{ntfy_topic}"  # URL kanálu pro notifikace
link_url = "http://91.139.94.3:31415/notif" # URL pro otevření po kliknutí na notifikaci

brightness_threshold = 80  # Minimální hodnota průměrného jasu, pod kterou bude snímek ignorován

# Funkce pro odeslání notifikace na telefon
def send_notification():
    if send_notifications:
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')  # Získání aktuálního času
        headers = {
            "Title": "Detekce pohybu",  # Správně naformátovaný titulek
            "Priority": "high",  # Priorita notifikace
            "Content-Type": "text/plain; charset=utf-8",
            "Click": link_url  # Přidání odkazu, který se otevře po kliknutí na notifikaci
        }
        message = f"Něco nového na boardu, check it!\nČas změny: {current_time}"  # Přidání času do zprávy
        try:
            response = requests.post(ntfy_url, data=message.encode('utf-8'), headers=headers)
            if response.status_code == 200:
                print("Notifikace byla úspěšně odeslána.")
            else:
                print(f"Chyba při odesílání notifikace: {response.status_code}")
        except Exception as e:
            print(f"Chyba při odesílání notifikace: {e}")

# Uchovávání snímků pro detekci pohybu
last_frame = None
stored_frame = None
stored_frame_time = None
last_saved_time = None
last_motion_time = None  # Čas poslední detekce pohybu
motion_detected = False  # Příznak, že je detekován pohyb
motion_end_time = None  # Čas, kdy pohyb ustal

# Uchovávání posledních 5 stabilních snímků před pohybem
stable_frame_buffer = deque(maxlen=5)  # Uchová maximálně 5 snímků před detekcí pohybu

# Funkce pro výpočet průměrného jasu snímku
def calculate_brightness(image):
    grayscale = image.convert('L')
    brightness = np.array(grayscale).mean()
    return brightness

# Normalizace jasu snímků na podobnou úroveň
def normalize_brightness(image, target_brightness):
    current_brightness = calculate_brightness(image)
    brightness_ratio = target_brightness / current_brightness
    enhancer = ImageEnhance.Brightness(image)
    return enhancer.enhance(brightness_ratio)

# Funkce pro oříznutí obrazu pomocí Pillow
def crop_image(image_data, left, upper, right, lower):
    image = Image.open(io.BytesIO(image_data))
    cropped_image = image.crop((left, upper, right, lower))
    byte_array = io.BytesIO()
    cropped_image.save(byte_array, format='JPEG')
    return byte_array.getvalue()

# Funkce pro ukládání snímků při detekci pohybu
def save_images_on_motion(initial_frame, changed_frame):
    timestamp = datetime.now().strftime('%Y%m%d_%H_%M')
    folder_path = os.path.join('templates', 'pic', timestamp)
    os.makedirs(folder_path, exist_ok=True)

    with open(os.path.join(folder_path, 'initial.jpg'), 'wb') as f:
        f.write(initial_frame)
    with open(os.path.join(folder_path, 'changed.jpg'), 'wb') as f:
        f.write(changed_frame)

    try:
        subprocess.run(["python3", "/opt/camera_stream/LEDm.py"], check=True)
        print("LEDm.py script executed successfully")
    except subprocess.CalledProcessError as e:
        print(f"Failed to execute LEDm.py: {e}")

    send_notification()

# Funkce pro detekci pohybu s ořezáváním obrazu
def detect_motion(current_frame):
    global last_frame, stored_frame, stored_frame_time, last_saved_time, last_motion_time
    global motion_detected, motion_end_time
    current_time = time.time()

    left, upper, right, lower = 100, 250, 620, 600  # Upravené souřadnice podle app.py
    cropped_frame = crop_image(current_frame, left, upper, right, lower)

    # Check if the frame is too dark (almost black) and ignore it
    img_for_brightness_check = Image.open(io.BytesIO(cropped_frame))
    brightness = calculate_brightness(img_for_brightness_check)
    if brightness < brightness_threshold:  # Threshold for black frame
        print(f"Brightness below threshold ({brightness} < {brightness_threshold}), skipping detection.")
        return  # Skip this frame if it's too dark

    last_frame = cropped_frame

    if motion_detected:
        if (current_time - last_motion_time) > ignore_motion_duration:
            motion_detected = False
            motion_end_time = current_time

    if not motion_detected:
        if motion_end_time and (current_time - motion_end_time) >= motion_end_delay:
            if stable_frame_buffer:
                print("Pohyb ustal, ukládám původní a změněné snímky.")
                save_images_on_motion(stable_frame_buffer[0], stable_frame_buffer[-1])
            motion_end_time = None

    if stored_frame is None or (current_time - stored_frame_time) >= 10:
        if stored_frame is not None:
            img1 = Image.open(io.BytesIO(stored_frame))
            img2 = Image.open(io.BytesIO(cropped_frame))

            # Normalizace jasu mezi snímky
            target_brightness = calculate_brightness(img1)
            img1 = normalize_brightness(img1, target_brightness)
            img2 = normalize_brightness(img2, target_brightness)

            diff = ImageChops.difference(img1, img2)
            total_pixels = img1.size[0] * img1.size[1]
            diff_np = np.array(diff)
            diff_pixels = np.sum(diff_np > 30)
            percentage_diff = (diff_pixels / total_pixels) * 100

            print(f"Sensitivity: {sensitivity_percentage}%")
            print(f"Image difference: {percentage_diff:.2f}%")
            print(f"Počet změněných pixelů: {diff_pixels}")

            if percentage_diff > sensitivity_percentage and diff_pixels > pixel_threshold:
                last_motion_time = current_time
                motion_detected = True
                stable_frame_buffer.append(cropped_frame)

        if not motion_detected:
            stable_frame_buffer.append(cropped_frame)
        stored_frame = cropped_frame
        stored_frame_time = current_time

# Funkce pro spuštění kamery a detekce na pozadí
def start_detection():
    with picamera.PiCamera() as camera:
        camera.resolution = (1080, 720)
        camera.framerate = 2  # Snížení na 2 snímky za sekundu
        stream = io.BytesIO()

        for _ in camera.capture_continuous(stream, 'jpeg', use_video_port=True):
            stream.seek(0)
            current_frame = stream.read()
            detect_motion(current_frame)
            stream.seek(0)
            stream.truncate()
            time.sleep(0.5)

if __name__ == "__main__":
    start_detection()
