import os
import subprocess
import io
import time
from flask import Flask, render_template, request, redirect, url_for, session, Response, jsonify, send_from_directory
from datetime import datetime
from picamera import PiCamera

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Globální příznak pro zastavení streamu
stop_stream = False

# Přihlašovací údaje
USERNAME = 'admin'
PASSWORD = 'picam'

# Funkce pro zastavení služby motion.service
def stop_motion_service():
    try:
        subprocess.run(["systemctl", "stop", "motion.service"], check=True)
        print("motion.service stopped")
    except subprocess.CalledProcessError as e:
        print(f"Failed to stop motion.service: {e}")

# Funkce pro spuštění služby motion.service
def start_motion_service():
    try:
        subprocess.run(["systemctl", "start", "motion.service"], check=True)
        print("motion.service started")
    except subprocess.CalledProcessError as e:
        print(f"Failed to start motion.service: {e}")

# Funkce pro zjištění stavu služby motion.service
def check_motion_service_status():
    try:
        result = subprocess.run(["systemctl", "is-active", "--quiet", "motion.service"])
        return result.returncode == 0  # 0 znamená, že služba běží
    except subprocess.CalledProcessError:
        return False

# Funkce pro generování streamu z kamery
def generate_frames():
    global stop_stream
    try:
        # Inicializace kamery
        camera = PiCamera()
        camera.resolution = (640, 460)
        camera.framerate = 24
        stream = io.BytesIO()

        # Streamování, dokud není požadováno zastavení
        for _ in camera.capture_continuous(stream, format='jpeg', use_video_port=True):
            if stop_stream:  # Zastavení streamu, když je příznak nastaven na True
                break
            stream.seek(0)
            frame = stream.read()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
            stream.seek(0)
            stream.truncate()
    except Exception as e:
        print(f"Error in camera streaming: {e}")
    finally:
        camera.close()  # Uvolnění kamery po ukončení streamu

# Endpoint pro spuštění streamu a zastavení detekce pohybu
@app.route('/video_feed')
def video_feed():
    global stop_stream
    stop_stream = False  # Povolení streamování při přístupu na stránku
    stop_motion_service()  # Zastavení služby motion.service při přístupu ke streamu
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

# Endpoint pro zastavení streamu
@app.route('/stop_stream')
def stop_stream_func():
    global stop_stream
    stop_stream = True  # Zastavení streamování
    return "Stream stopped", 200

# Endpoint pro znovuspuštění detekce pohybu při opuštění stránky
@app.route('/start_motion')
def start_motion():
    time.sleep(3)  # Krátká prodleva před spuštěním služby
    start_motion_service()  # Spuštění služby motion.service při opuštění streamu
    print("motion.service started after leaving stream.html")
    return "Motion detection service started", 200

# Endpoint pro uložení aktuálního snímku
@app.route('/take_photo', methods=['POST'])
def take_photo():
    try:
        timestamp = datetime.now().strftime('%Y%m%d_%H_%M')
        folder_path = os.path.join('/opt/camera_stream/templates/pic/shots', timestamp)
        os.makedirs(folder_path, exist_ok=True)

        with PiCamera() as camera:
            camera.resolution = (640, 480)
            stream = io.BytesIO()
            camera.capture(stream, format='jpeg')
            stream.seek(0)
            photo_path = os.path.join(folder_path, 'photo.jpg')
            with open(photo_path, 'wb') as f:
                f.write(stream.read())
        
        return "Photo taken and saved", 200
    except Exception as e:
        print(f"Error taking photo: {e}")
        return "Failed to take photo", 500

# Endpoint pro přijímání heartbeat signálů
@app.route('/heartbeat', methods=['POST'])
def heartbeat():
    # Tento endpoint je volán pravidelně z klienta (stream.html) jako heartbeat signál.
    # Pokud stránka je aktivní, nepodnikne se žádná akce.
    return "OK", 200

# Endpoint pro zobrazení posledních změn
@app.route('/last')
def last():
    changes = []
    pic_folder = os.path.join('templates', 'pic')
    for folder in sorted(os.listdir(pic_folder), reverse=True):
        timestamp = folder.replace("_", ":")
        changes.append({
            'timestamp': timestamp,
            'folder': folder
        })
    return render_template('last.html', changes=changes)

# Endpoint pro zobrazení uložených snímků
@app.route('/pic/<path:filename>')
def download_file(filename):
    return send_from_directory('templates/pic', filename)

# Endpoint pro spuštění Python skriptu LED.py
@app.route('/run_led', methods=['POST'])
def run_led():
    try:
        subprocess.run(["python3", "/opt/camera_stream/LED.py"], check=True)
        return "LED script OK", 200
    except subprocess.CalledProcessError:
        return "Failed to execute LED script!", 500

# Endpoint pro získání informací o systému a pohybu
@app.route('/get_info', methods=['GET'])
def get_info():
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with open('/proc/uptime', 'r') as f:
        uptime_seconds = float(f.readline().split()[0])
        uptime = time.strftime('%H:%M:%S', time.gmtime(uptime_seconds))

    temp = subprocess.check_output(["vcgencmd", "measure_temp"]).decode("UTF-8").replace("temp=", "").strip()

    return jsonify({
        "current_time": current_time,
        "uptime": uptime,
        "temperature": temp
    })

# Endpoint pro přihlášení
@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if username == USERNAME and password == PASSWORD:
            session['logged_in'] = True
            return redirect(url_for('index'))
        else:
            error = "Nesprávné údaje"

    return render_template('login.html', error=error)


# Endpoint pro odhlášení
@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    start_motion_service()  # Spustí detekci při odhlášení uživatele
    return redirect(url_for('login'))

# Domovská stránka
@app.route('/')
def index():
    if 'logged_in' in session and session['logged_in']:
        return render_template('stream.html')
    return redirect(url_for('login'))

# Zajištění, že služba motion.service bude spuštěna při spuštění aplikace
def ensure_motion_service_running():
    if not check_motion_service_status():
        start_motion_service()

if __name__ == "__main__":
    ensure_motion_service_running()  # Ujistíme se, že motion.service běží při spuštění aplikace
    app.run(host='192.168.1.10', port=5433, debug=True)
