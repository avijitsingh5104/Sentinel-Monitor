# animations.py
import tkinter as tk
from PIL import Image, ImageTk, ImageGrab, ImageEnhance
import time

class WelcomeOverlay:
    def __init__(self, username, duration=2.5):
        # create Tk root for this process
        self.root = tk.Tk()
        self.root.attributes("-fullscreen", True)
        self.root.attributes("-topmost", True)
        self.root.overrideredirect(True)

        # capture screen and darken it
        screenshot = ImageGrab.grab()
        darkened = ImageEnhance.Brightness(screenshot).enhance(0.28)

        # store PhotoImage on self to avoid GC
        self.bg_img = ImageTk.PhotoImage(darkened)

        # canvas
        self.canvas = tk.Canvas(self.root,
                                width=self.bg_img.width(),
                                height=self.bg_img.height(),
                                highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.canvas.create_image(0, 0, image=self.bg_img, anchor="nw")

        # welcome text (you can tweak font, size)
        self.text_id = self.canvas.create_text(
            self.bg_img.width() // 2,
            self.bg_img.height() // 2,
            text=f"Welcome, {username}!",
            font=("Segoe UI", 64, "bold"),
            fill="#00ff99"
        )

        # optional: small subtext
        self.canvas.create_text(
            self.bg_img.width() // 2,
            self.bg_img.height() // 2 + 80,
            text="Access granted",
            font=("Segoe UI", 26),
            fill="white"
        )

        self.duration = duration

    def show(self):
        # fade-in
        for i in range(0, 101, 8):
            self.root.attributes("-alpha", i/100)
            self.root.update()
            time.sleep(0.02)

        # optionally add a simple pulsing/text scale
        # (lightweight: scale text by changing font size)
        # pause for duration
        start = time.time()
        while time.time() - start < self.duration:
            # pulse effect: small sinusoidal size variation
            # keep it simple to avoid heavy CPU in animation
            self.root.update()
            time.sleep(0.02)

        # fade-out
        for i in range(100, -1, -8):
            self.root.attributes("-alpha", i/100)
            self.root.update()
            time.sleep(0.02)

        self.root.destroy()
