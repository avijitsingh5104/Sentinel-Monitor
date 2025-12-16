import os
import json
from tkinter import simpledialog, messagebox
from Crypto.PublicKey import ElGamal
from Crypto.Random import get_random_bytes
from Crypto.Cipher import AES
from Crypto.Util.number import bytes_to_long, long_to_bytes
from Crypto.Random.random import StrongRandom
from math import gcd
import hashlib
import threading
import tkinter as tk
import traceback

DATA_DIR = "data"
AUTH_PATH = os.path.join(DATA_DIR, "admin_auth.json")
ELG_PRIV_PATH = os.path.join(DATA_DIR, "elgamal_priv.json")
os.makedirs(DATA_DIR, exist_ok=True)


def _save_json_atomic(path, obj):
    tmp = path + ".tmp"
    try:
        with open(tmp, "w") as f:
            json.dump(obj, f, indent=2)
        os.replace(tmp, path)
        return True
    except Exception:
        if os.path.exists(tmp):
            try:
                os.unlink(tmp)
            except:
                pass
        return False


def elgamal_encrypt(pub, m_int):
    p, g, y = int(pub.p), int(pub.g), int(pub.y)
    rand = StrongRandom()
    while True:
        k = rand.randrange(1, p - 1)
        if gcd(k, p - 1) == 1:
            break
    c1 = pow(g, k, p)
    c2 = (m_int * pow(y, k, p)) % p
    return c1, c2


def elgamal_decrypt(priv, c1, c2):
    s = pow(c1, priv.x, priv.p)
    s_inv = pow(s, -1, priv.p)
    m_int = (c2 * s_inv) % priv.p
    return m_int


def set_new_password(root, new_password=None, confirm_password=None):
    """Set a new admin password (supports both GUI dialog and direct input)."""
    if new_password is None or confirm_password is None:
        new_password = simpledialog.askstring("Set Admin Password", "Enter new admin password:", show="*", parent=root)
        if not new_password or len(new_password) < 4:
            messagebox.showerror("Error", "Password must be at least 4 characters long.", parent=root)
            return False
        confirm_password = simpledialog.askstring("Confirm Password", "Confirm new admin password:", show="*", parent=root)
        if confirm_password is None or new_password != confirm_password:
            messagebox.showerror("Error", "Passwords do not match.", parent=root)
            return False
    else:
        if len(new_password) < 4:
            messagebox.showerror("Error", "Password must be at least 4 characters long.", parent=root)
            return False
        if new_password != confirm_password:
            messagebox.showerror("Error", "Passwords do not match.", parent=root)
            return False

    pwd1 = new_password

    try:
        for path in [AUTH_PATH, ELG_PRIV_PATH]:
            if os.path.exists(path):
                os.remove(path)
    except Exception as e:
        messagebox.showwarning("Warning", f"Failed to remove old auth files: {e}", parent=root)

    progress = tk.Toplevel(root)
    progress.title("Please wait")
    progress.geometry("300x120")
    progress.configure(bg="white")
    tk.Label(progress, text="🔐 Generating encryption keys...", bg="white").pack(pady=20)
    status_lbl = tk.Label(progress, text="This may take ~10 seconds.", bg="white", fg="gray")
    status_lbl.pack()
    progress.grab_set()

    done = {"ok": False, "error": None}

    def worker():
        try:
            password_bytes = pwd1.encode("utf-8")

            elg_key = ElGamal.generate(512, get_random_bytes)
            pub = elg_key.publickey()

            aes_key = get_random_bytes(32)
            aes_cipher = AES.new(aes_key, AES.MODE_GCM)
            ciphertext, tag = aes_cipher.encrypt_and_digest(password_bytes)
            nonce = aes_cipher.nonce

            rand = StrongRandom()
            p, g, y = int(pub.p), int(pub.g), int(pub.y)
            while True:
                k = rand.randrange(1, p - 1)
                if gcd(k, p - 1) == 1:
                    break
            c1 = pow(g, k, p)
            c2 = (bytes_to_long(aes_key) * pow(y, k, p)) % p

            auth_obj = {
                "elgamal_pub": {
                    "p": format(int(p), "x"),
                    "g": format(int(g), "x"),
                    "y": format(int(y), "x")
                },
                "enc_aes_key": {
                    "c1": format(int(c1), "x"),
                    "c2": format(int(c2), "x")
                },
                "aes_enc": {
                    "nonce": nonce.hex(),
                    "ciphertext": ciphertext.hex(),
                    "tag": tag.hex()
                }
            }

            if not _save_json_atomic(AUTH_PATH, auth_obj):
                raise RuntimeError("Failed to save authentication data")

            priv_obj = {"p": format(int(p), "x"), "g": format(int(g), "x"), "x": format(int(elg_key.x), "x")}
            if not _save_json_atomic(ELG_PRIV_PATH, priv_obj):
                raise RuntimeError("Failed to save private key data")

            try:
                os.chmod(ELG_PRIV_PATH, 0o600)
            except Exception:
                pass

            done["ok"] = True
        except Exception as e:
            done["error"] = e
            traceback.print_exc()

    t = threading.Thread(target=worker, daemon=True)
    t.start()

    def poll_worker():
        if t.is_alive():
            txt = status_lbl.cget("text")
            status_lbl.config(text=("Working" if txt.endswith("...") else txt + "."))
            root.after(300, poll_worker)
        else:
            progress.destroy()
            if done["ok"]:
                messagebox.showinfo("Success", "Admin password created and saved.", parent=root)
            else:
                messagebox.showerror("Error", f"Failed to set password:\n{done['error']}", parent=root)

    poll_worker()
    return True


def _load_auth():
    if not os.path.exists(AUTH_PATH) or not os.path.exists(ELG_PRIV_PATH):
        return None
    try:
        with open(AUTH_PATH, "r") as f:
            auth = json.load(f)
        with open(ELG_PRIV_PATH, "r") as f:
            priv = json.load(f)
        return auth, priv
    except:
        return None


def verify_password_dialog(root, entered_password=None, max_tries=3):
    loaded = _load_auth()
    if loaded is None:
        messagebox.showerror("Error", "Authentication data not found.", parent=root)
        return False
    auth, priv = loaded
    try:
        p = int(priv["p"], 16)
        g = int(priv["g"], 16)
        x = int(priv["x"], 16)
        y = pow(g, x, p)

        class ElGamalPriv:
            def __init__(self, p, g, y, x):
                self.p, self.g, self.y, self.x = p, g, y, x

        elg_priv = ElGamalPriv(p, g, y, x)
        c1 = int(auth["enc_aes_key"]["c1"], 16)
        c2 = int(auth["enc_aes_key"]["c2"], 16)
        m_int = elgamal_decrypt(elg_priv, c1, c2)
        aes_key = long_to_bytes(m_int)
        if len(aes_key) != 32:
            messagebox.showerror("Error", "Decrypted AES key invalid length", parent=root)
            return False

        nonce = bytes.fromhex(auth["aes_enc"]["nonce"])
        ciphertext = bytes.fromhex(auth["aes_enc"]["ciphertext"])
        tag = bytes.fromhex(auth["aes_enc"]["tag"])
        cipher = AES.new(aes_key, AES.MODE_GCM, nonce=nonce)
        stored_password = cipher.decrypt_and_verify(ciphertext, tag)

    except Exception as e:
        messagebox.showerror("Error", f"Failed to load authentication data: {e}", parent=root)
        return False

    # Direct check if entered from GUI field
    if entered_password is not None:
        return entered_password.encode("utf-8") == stored_password

    # Fallback dialog path
    for attempt in range(max_tries):
        entry = simpledialog.askstring("Admin Login", "Enter admin password:", show="*", parent=root)
        if entry is None:
            return False
        if entry.encode("utf-8") == stored_password:
            return True
        remaining = max_tries - attempt - 1
        if remaining > 0:
            messagebox.showwarning("Wrong password", f"Incorrect password. {remaining} tries left.", parent=root)
        else:
            messagebox.showerror("Access Denied", "Maximum attempts exceeded.", parent=root)
    return False


def change_password(root):
    if not verify_password_dialog(root):
        return False
    return set_new_password(root)


def ensure_and_verify(root):
    loaded = _load_auth()
    if loaded is None:
        return set_new_password(root)
    return verify_password_dialog(root)


def is_admin_configured():
    return _load_auth() is not None
