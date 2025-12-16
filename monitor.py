import os, json, time
import cv2, numpy as np
import face_recognition
from animations import WelcomeOverlay
from crypto_utils import load_rsa_keys, decrypt_encoding
from overlay import LockOverlay
import subprocess
import sys

def show_animation(name):
    overlay = WelcomeOverlay(name)
    overlay.show()

DATA_DIR = "data"
DB_PATH = os.path.join(DATA_DIR, "faces.json")
priv_path = os.path.join(DATA_DIR, "private.pem")
pub_path = os.path.join(DATA_DIR, "public.pem")

if not (os.path.exists(priv_path) and os.path.exists(pub_path)):
    raise RuntimeError("RSA keys not found. Run register.py first.")
if not os.path.exists(DB_PATH):
    raise RuntimeError("No registered users. Run register.py first.")

private_key, public_key = load_rsa_keys(priv_path, pub_path)

with open(DB_PATH, "r") as f:
    db = json.load(f)

names, encodings = [], []
for uname, info in db["users"].items():
    arr = decrypt_encoding(info["encoding"], private_key)
    names.append(uname)
    encodings.append(arr)

print("Loaded users:", names)

overlay = LockOverlay(blur_radius=15)
overlay_visible = False

cap = cv2.VideoCapture(0)
if not cap.isOpened():
    raise RuntimeError("Could not open camera.")

authorized = False
last_seen_time = 0
GRACE_SECONDS = 2.0
TOLERANCE = 0.5

LOG_PATH = os.path.join(DATA_DIR, "logs.json")

def log_access(username):
    entry = {"user": username, "time": time.strftime("%Y-%m-%d %H:%M:%S")}
    if os.path.exists(LOG_PATH):
        with open(LOG_PATH, "r") as f:
            logs = json.load(f)
    else:
        logs = []
    logs.append(entry)
    with open(LOG_PATH, "w") as f:
        json.dump(logs, f, indent=2)

try:
    while True:
        ret, frame = cap.read()
        if not ret:
            print("[!] Failed to grab frame")
            break

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        boxes = face_recognition.face_locations(rgb, model="hog")
        encs = face_recognition.face_encodings(rgb, boxes)

        matched, matched_name = False, None
        for e in encs:
            if len(encodings) == 0:
                continue
            dists = face_recognition.face_distance(encodings, e)
            best_idx = np.argmin(dists)
            best_dist = float(dists[best_idx])
            print(f"[*] Distances: {dists}, best={best_dist:.3f}")  

            if best_dist < TOLERANCE:
                matched, matched_name = True, names[best_idx]
                break

        current_time = time.time()
        if matched:
            last_seen_time = current_time
            if not authorized:
                print(f"[+] Authorized: {matched_name} (dist < {TOLERANCE})")
                log_access(matched_name)
                script_dir = os.path.abspath(os.path.dirname(__file__))
                runner_path = os.path.join(script_dir, "welcome_anim_runner.py")
                try:
                    subprocess.Popen([sys.executable, runner_path, matched_name])
                except Exception as e:
                    print("[!] Failed to launch welcome animation:", e)
            authorized = True

            if overlay_visible:
                overlay.hide()        
                overlay_visible = False
        else:
            if authorized and (current_time - last_seen_time) < GRACE_SECONDS:
                print("[~] Grace period active, staying unlocked")
            else:
                if authorized:
                    print("[-] Locking screen (no face match)")
                authorized = False

                if not overlay_visible:
                    overlay.show()     
                    overlay_visible = True

        for (top, right, bottom, left) in boxes:
            color = (0, 255, 0) if matched else (0, 0, 255)
            cv2.rectangle(frame, (left, top), (right, bottom), color, 2)

        cv2.imshow("Camera Preview (press q to quit)", frame)
        if cv2.waitKey(30) & 0xFF == ord('q'):
            break

finally:
    cap.release()
    cv2.destroyAllWindows()
    if overlay_visible:
        overlay.hide()
