# overlay.py
import tkinter as tk
from PIL import Image, ImageTk, ImageFilter, ImageGrab, ImageEnhance
import time

class LockOverlay:
    def __init__(self, blur_radius=15):
        # Fullscreen overlay window
        self.root = tk.Tk()
        self.root.attributes("-fullscreen", True)
        self.root.attributes("-topmost", True)
        self.root.overrideredirect(True)
        self.root.attributes("-alpha", 0.0)  # start fully transparent

        # Grab current screen and blur + darken it
        screenshot = ImageGrab.grab()
        blurred = screenshot.filter(ImageFilter.GaussianBlur(radius=blur_radius))
        darkened = ImageEnhance.Brightness(blurred).enhance(0.3)

        self.bg_img = ImageTk.PhotoImage(darkened)

        # Canvas setup
        self.canvas = tk.Canvas(self.root, width=self.bg_img.width(), height=self.bg_img.height(), highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.canvas.create_image(0, 0, image=self.bg_img, anchor="nw")

        # Lock text
        self.text_id = self.canvas.create_text(
            self.bg_img.width() // 2,
            self.bg_img.height() // 2,
            text="ACCESS LOCKED",
            font=("Segoe UI", 64, "bold"),
            fill="#ff3333"
        )

        # Small subtitle
        self.subtext_id = self.canvas.create_text(
            self.bg_img.width() // 2,
            self.bg_img.height() // 2 + 70,
            text="Unauthorized User Detected",
            font=("Segoe UI", 28),
            fill="#ffffff"
        )

        self.visible = False

    def show(self):
        """Fade in with pulsing effect."""
        if self.visible:
            return
        self.visible = True
        self.root.deiconify()

        # Fade in
        for i in range(0, 100, 8):
            self.root.attributes("-alpha", i / 100)
            self.root.update()
            time.sleep(0.02)

        # Pulse text while visible
        pulse_count = 0
        while self.visible and pulse_count < 10:
            self.canvas.itemconfig(self.text_id, fill="#ff5555")
            self.root.update()
            time.sleep(0.2)
            self.canvas.itemconfig(self.text_id, fill="#ff0000")
            self.root.update()
            time.sleep(0.2)
            pulse_count += 1

    def hide(self):
        """Fade out and hide overlay."""
        if not self.visible:
            return
        # Smooth fade out
        for i in range(100, -1, -10):
            self.root.attributes("-alpha", i / 100)
            self.root.update()
            time.sleep(0.02)
        self.root.withdraw()
        self.visible = False
