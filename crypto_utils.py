import io
import numpy as np
import base64
from typing import Any, Dict

from Crypto.Cipher import AES, PKCS1_OAEP
from Crypto.PublicKey import RSA
from Crypto.Random import get_random_bytes

def generate_rsa_keys(bits: int = 2048, priv_path="data/private.pem", pub_path="data/public.pem"):
    key = RSA.generate(bits)
    private_key = key.export_key()
    public_key = key.publickey().export_key()
    with open(priv_path, "wb") as f:
        f.write(private_key)
    with open(pub_path, "wb") as f:
        f.write(public_key)
    print(f"[+] RSA keys saved to {priv_path}, {pub_path}")


def load_rsa_keys(priv_path="data/private.pem", pub_path="data/public.pem"):
    with open(priv_path, "rb") as f:
        private_key = RSA.import_key(f.read())
    with open(pub_path, "rb") as f:
        public_key = RSA.import_key(f.read())
    return private_key, public_key

def pad(data: bytes) -> bytes:
    pad_len = 16 - (len(data) % 16)
    return data + bytes([pad_len]) * pad_len


def unpad(data: bytes) -> bytes:
    return data[:-data[-1]]

def encrypt_encoding(arr: np.ndarray, public_key: RSA.RsaKey) -> Dict[str, Any]:
    bio = io.BytesIO()
    np.save(bio, arr, allow_pickle=False)
    bio.seek(0)
    raw = bio.read()

    aes_key = get_random_bytes(16)
    iv = get_random_bytes(16)
    cipher_aes = AES.new(aes_key, AES.MODE_CBC, iv)
    ct_bytes = cipher_aes.encrypt(pad(raw))

    cipher_rsa = PKCS1_OAEP.new(public_key)
    enc_aes_key = cipher_rsa.encrypt(aes_key)

    return {
        "aes_key": base64.b64encode(enc_aes_key).decode(),
        "iv": base64.b64encode(iv).decode(),
        "cipher": base64.b64encode(ct_bytes).decode(),
        "shape": arr.shape,
        "dtype": str(arr.dtype),
    }


def decrypt_encoding(enc_dict: Dict[str, Any], private_key: RSA.RsaKey) -> np.ndarray:
    enc_aes_key = base64.b64decode(enc_dict["aes_key"])
    iv = base64.b64decode(enc_dict["iv"])
    ct = base64.b64decode(enc_dict["cipher"])

    cipher_rsa = PKCS1_OAEP.new(private_key)
    aes_key = cipher_rsa.decrypt(enc_aes_key)

    cipher_aes = AES.new(aes_key, AES.MODE_CBC, iv)
    raw = unpad(cipher_aes.decrypt(ct))

    bio = io.BytesIO(raw)
    arr = np.load(bio, allow_pickle=False)
    return arr
