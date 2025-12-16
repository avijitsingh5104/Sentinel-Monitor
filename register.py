import os
import json
import cv2
import face_recognition
import numpy as np
from crypto_utils import generate_rsa_keys, load_rsa_keys, encrypt_encoding

DATA_DIR = "data"
DB_PATH = os.path.join(DATA_DIR, "faces.json")

os.makedirs(DATA_DIR, exist_ok=True)

priv_path = os.path.join(DATA_DIR, "private.pem")
pub_path = os.path.join(DATA_DIR, "public.pem")
if not (os.path.exists(priv_path) and os.path.exists(pub_path)):
    print("No RSA keys found — generating new ones.")
    generate_rsa_keys(priv_path=priv_path, pub_path=pub_path)

private_key, public_key = load_rsa_keys(priv_path, pub_path)


def save_face(username: str, enc_dict: dict, meta: dict = None):
    if os.path.exists(DB_PATH):
        with open(DB_PATH, "r") as f:
            db = json.load(f)
    else:
        db = {"users": {}}
    db["users"][username] = {"encoding": enc_dict, "meta": meta or {}}
    with open(DB_PATH, "w") as f:
        json.dump(db, f, indent=2)
    print(f"[+] Saved {username} to {DB_PATH}")


def capture_face_and_register(username: str):
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        raise RuntimeError("Could not open camera.")
    print("Position yourself. Press SPACE to capture, ESC to cancel.")

    while True:
        ret, frame = cap.read()
        if not ret:
            continue
        cv2.imshow("Register", frame)
        k = cv2.waitKey(1) & 0xFF
        if k == 27:  # ESC
            break
        if k == 32:  # SPACE
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            boxes = face_recognition.face_locations(rgb)
            if len(boxes) == 0:
                print("No face detected. Try again.")
                continue
            encoding = face_recognition.face_encodings(rgb, [boxes[0]])[0]
            enc_dict = encrypt_encoding(np.array(encoding), public_key)
            save_face(username, enc_dict)
            print("Registered:", username)
            break
    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    uname = input("Enter username: ").strip()
    if uname:
        capture_face_and_register(uname)


