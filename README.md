# Sentinel-Monitor
Sentinel Monitor is a Python-based intelligent security system designed to prevent unauthorized access to a computer system. It uses face recognition, secure authentication, and real-time monitoring to detect unauthorized users and immediately protect the screen using a locking/overlay mechanism.

The system is suitable for:

- Personal computers
- Shared systems in offices or labs
- Examination environments
- Sensitive workstations

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
├── admin_auth.py              # Handles admin authentication
├── admin_panel.py             # GUI control panel
├── monitor.py                 # Real-time monitoring logic
├── overlay.py                 # Screen lock / overlay
├── register.py                # User face registration
├── crypto_utils.py            # Encryption utilities
│
├── data/
│   ├── faces.json             # Stored face encodings
│   ├── private.pem            # Private encryption key
│   └── public.pem             # Public encryption key
│
├── README.md
└── LICENSE

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


