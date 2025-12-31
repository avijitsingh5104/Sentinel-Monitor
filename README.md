# Sentinel-Monitor
Sentinel Monitor is a Python-based intelligent security system designed to prevent unauthorized access to a computer system. It uses face recognition, secure authentication, and real-time monitoring to detect unauthorized users and immediately protect the screen using a locking/overlay mechanism.

- The system is suitable for:

- Personal computers
- 💠 Shared systems in offices or labs
- 💠 Examination environments
- 💠 Sensitive workstations

---

## 🎯 Objectives

- 🚫 Prevent unauthorized access using face recognition.
- 🖥️ Provide a secure admin-controlled interface.
- 🕵️ Detect intrusions in real time.
- 🛡️ Protect system visibility using screen overlay.
- 🔒 Secure sensitive data using encryption.

---

## 📂 Project Structure
sentinel-monitor/ 
|-- admin_auth.py # Admin authentication logic 
|-- admin_panel.py # GUI-based admin control panel 
|-- monitor.py # Real-time face monitoring engine 
|-- overlay.py # Screen lock / blur overlay 
|-- register.py # User face registration module 
|-- crypto_utils.py # Encryption & key management 
|-- welcome_anim_runner.py # Startup animation / splash screen 
|-- data/ 
│------ admin_auth.json # ElGamal public key
│------ elgamal_priv.json # ElGamal private key
│------ faces.json # Stored facial encodings 
│------ public.pem # RSA public key 
│------ private.pem # RSA private key
|-- README.md
|-- LICENSE

---

## 🧠 Module Descriptions

### 🔐 admin_auth.py

- Handles administrator authentication
- Verifies encrypted credentials
- Controls access to system-level operations

### 🧑‍💼 admin_panel.py (Frontend)

- Graphical interface for administrators:
- Login screen
- Start/stop monitoring
- User registration access
- System status overview
- Security configuration options

### 🧠 monitor.py

- Core monitoring engine:
- Captures real-time camera feed
- Detects and matches faces
- Triggers security response on mismatch

### 🖥️ overlay.py

- Displays full-screen overlay when intrusion is detected
- Prevents screen interaction and visibility

### 🧑‍💻 register.py

- Registers new users
- Captures facial data
- Stores face encodings securely

### 🔐 crypto_utils.py

- RSA key generation
- Encryption and decryption utilities
- Protects credentials and stored data

### 🎬 welcome_anim_runner.py

- Displays a startup animation or splash screen
- Enhances user experience


