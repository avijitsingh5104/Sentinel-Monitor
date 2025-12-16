# futuristic_admin_panel.py
import tkinter as tk
from tkinter import messagebox, simpledialog, scrolledtext
import json, os, threading, subprocess, sys
from register import capture_face_and_register
import admin_auth
from PIL import Image, ImageTk, ImageDraw
import time

DATA_DIR = "data"
DB_PATH = os.path.join(DATA_DIR, "faces.json")
LOG_PATH = os.path.join(DATA_DIR, "logs.json")


# --- Utility Decorator for Threading ---
def threaded(func):
    def wrapper(*args, **kwargs):
        threading.Thread(target=func, args=args, kwargs=kwargs, daemon=True).start()
    return wrapper

class LoadingOverlay:
    """A simple animated loading overlay for background tasks."""
    def __init__(self, parent, text="Processing..."):
        self.top = tk.Toplevel(parent)
        self.top.title("Loading")
        self.top.geometry("400x200")
        self.top.configure(bg="#010118")
        self.top.resizable(False, False)
        self.top.transient(parent)
        self.top.grab_set()
        self.top.attributes("-topmost", True)

        tk.Label(
            self.top,
            text="⚙️",
            bg="#010118",
            fg="#00d9ff",
            font=("Arial", 40, "bold")
        ).pack(pady=10)

        self.label = tk.Label(
            self.top,
            text=text,
            bg="#010118",
            fg="#00d9ff",
            font=("Courier New", 14, "bold")
        )
        self.label.pack(pady=5)

        self.running = True
        self._animate()

    def _animate(self):
        if not self.running:
            return
        current = self.label.cget("text")
        if current.endswith("..."):
            new_text = current[:-3]
        else:
            new_text = current + "."
        self.label.config(text=new_text)
        self.top.after(400, self._animate)

    def close(self):
        self.running = False
        self.top.destroy()


# --- Circular Button Class ---
class CircularButton:
    def __init__(self, canvas, x, y, image_path, text, command,
                 bg="#0a1628", hover="#00d9ff", size=100, icon="⚡"):
        self.canvas = canvas
        self.command = command
        self.size = size
        self.bg = bg
        self.hover = hover
        self.text = text
        self.x = x
        self.y = y
        self.is_hovering = False

        self.outer_ring = self.canvas.create_oval(
            x - size - 5, y - size - 5, x + size + 5, y + size + 5,
            outline="#00d9ff", width=2, dash=(5, 5), tags="content"
        )
        self.circle = self.canvas.create_oval(
            x - size, y - size, x + size, y + size,
            fill=bg, outline="#00d9ff", width=3, tags="content"
        )

        try:
            img = Image.open(image_path).resize((70, 70), Image.Resampling.LANCZOS)
            img = self.make_circular(img)
            self.icon = ImageTk.PhotoImage(img)
            self.image_item = self.canvas.create_image(x, y - 10, image=self.icon, tags="content")
        except Exception:
            self.image_item = self.canvas.create_text(
                x, y - 10, text=icon, fill="#00d9ff", font=("Arial", 40), tags="content"
            )

        self.label = self.canvas.create_text(
            x, y + size - 50, text=text.upper(),
            fill="#00d9ff", font=("Courier New", 14, "bold"), tags="content"
        )

        for item in (self.circle, self.outer_ring, self.image_item, self.label):
            self.canvas.tag_bind(item, "<Enter>", self.on_hover)
            self.canvas.tag_bind(item, "<Leave>", self.on_leave)
            self.canvas.tag_bind(item, "<Button-1>", self.on_click)

        self.angle = 0
        self.animate_ring()

    def make_circular(self, img):
        mask = Image.new('L', img.size, 0)
        draw = ImageDraw.Draw(mask)
        draw.ellipse((0, 0) + img.size, fill=255)
        result = Image.new('RGBA', img.size)
        result.paste(img, mask=mask)
        return result

    def animate_ring(self):
        try:
            if self.is_hovering and self.canvas.find_withtag(self.outer_ring):
                self.angle = (self.angle + 5) % 360
                offset = int(self.angle / 10)
                self.canvas.itemconfig(self.outer_ring, dashoffset=offset)
            self.canvas.after(50, self.animate_ring)
        except:
            pass

    def on_hover(self, event):
        self.is_hovering = True
        self.canvas.itemconfig(self.circle, fill=self.hover, width=4)
        self.canvas.itemconfig(self.outer_ring, outline="#00ffff", width=3)
        self.canvas.itemconfig(self.label, fill="#00ffff")

    def on_leave(self, event):
        self.is_hovering = False
        self.canvas.itemconfig(self.circle, fill=self.bg, width=3)
        self.canvas.itemconfig(self.outer_ring, outline="#00d9ff", width=2)
        self.canvas.itemconfig(self.label, fill="#00d9ff")

    def on_click(self, event):
        orig = self.canvas.itemcget(self.circle, "fill")
        self.canvas.itemconfig(self.circle, fill="#ffffff")
        self.canvas.after(100, lambda: self.canvas.itemconfig(self.circle, fill=orig))
        if self.command:
            self.command()


# --- Main Admin Panel Class ---
class AdminPanel:
    def __init__(self, root):
        self.root = root
        self.root.attributes('-fullscreen', True)
        self.root.configure(bg="#010118")
        self.root.title("Admin Control Panel")

        self.canvas = tk.Canvas(root, bg="#010118", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.root.bind("<Escape>", lambda e: root.attributes('-fullscreen', False))
        self.root.bind("q", lambda e: root.quit())

        self.current_screen = "home"
        self.content_frame = None

        self.draw_tech_grid()
        self.root.update()

        self.width = self.root.winfo_screenwidth()
        self.height = self.root.winfo_screenheight()
        center_x = self.width // 2
        center_y = self.height // 2

        self.canvas.create_text(center_x, 80, text="🔐 ADMIN CONTROL PANEL",
                                fill="#00d9ff", font=("Arial", 36, "bold"), tags="header")

        self.status_dot = self.canvas.create_oval(center_x - 100, 140, center_x - 90, 150,
                                                  fill="#00ff00", outline="", tags="header")
        self.canvas.create_text(center_x - 40, 145, text="SYSTEM ONLINE",
                                fill="#00d9ff", font=("Courier New", 10, "bold"), tags="header")

        self.create_status_panel(center_x)
        self.show_home()
        self.animate_status()

    # --- Background Grid ---
    def draw_tech_grid(self):
        width = self.root.winfo_screenwidth()
        height = self.root.winfo_screenheight()
        grid_size = 50
        for x in range(0, width, grid_size):
            self.canvas.create_line(x, 0, x, height, fill="#003355", width=1, dash=(2, 4), tags="grid")
        for y in range(0, height, grid_size):
            self.canvas.create_line(0, y, width, y, fill="#003355", width=1, dash=(2, 4), tags="grid")

    # --- Status Footer ---
    def create_status_panel(self, cx):
        panel_y = self.height - 100
        self.canvas.create_rectangle(cx - 250, panel_y - 60, cx + 250, panel_y + 40,
                                     fill="#0a1628", outline="#00d9ff", width=2, tags="status_panel")
        self.canvas.create_text(cx - 220, panel_y - 45, text="SYSTEM STATUS", fill="#00d9ff",
                                font=("Arial", 14, "bold"), anchor="w", tags="status_panel")
        self.canvas.create_text(cx - 220, panel_y - 15, text="Core Systems:", fill="#888",
                                font=("Arial", 10), anchor="w", tags="status_panel")
        self.canvas.create_text(cx + 220, panel_y - 15, text="OPERATIONAL", fill="#00d9ff",
                                font=("Arial", 10, "bold"), anchor="e", tags="status_panel")
        self.canvas.create_text(cx - 220, panel_y + 10, text="Screen:", fill="#888",
                                font=("Arial", 10), anchor="w", tags="status_panel")
        self.screen_label = self.canvas.create_text(cx + 220, panel_y + 10, text="Home", fill="#00d9ff",
                                                    font=("Arial", 10, "bold"), anchor="e", tags="status_panel")

    def update_screen_label(self, name): self.canvas.itemconfig(self.screen_label, text=name)
    def animate_status(self):
        fill = "#00ff00" if self.canvas.itemcget(self.status_dot, "fill") == "#003300" else "#003300"
        self.canvas.itemconfig(self.status_dot, fill=fill)
        self.root.after(800, self.animate_status)

    # --- Navigation ---
    def clear_content(self):
        self.canvas.delete("content")
        if self.content_frame and self.content_frame.winfo_exists():
            self.content_frame.destroy()
            self.content_frame = None

    def slide_in(self, widget):
        start_x = self.width
        target_x = (self.width - 1200) // 2
        steps = 20
        widget.place(x=start_x, y=200, width=1200)

        def animate_step(step):
            if step <= steps and widget.winfo_exists():
                progress = step / steps
                ease_progress = 1 - pow(1 - progress, 3)
                current_x = start_x + (target_x - start_x) * ease_progress
                widget.place(x=current_x)
                self.root.after(20, lambda: animate_step(step + 1))
        animate_step(0)

    # --- HOME SCREEN ---
    def show_home(self):
        self.clear_content()
        self.current_screen = "home"
        self.update_screen_label("Home")

        cx, cy = self.width // 2, self.height // 2
        CircularButton(self.canvas, cx - 400, cy - 150, "", "Register", self.show_register, "#0a1628", "#00d9ff", 100, "➕")
        CircularButton(self.canvas, cx - 400, cy + 150, "", "Users", self.show_users, "#0a1628", "#00d9ff", 100, "👥")
        CircularButton(self.canvas, cx + 400, cy - 150, "", "View Logs", self.show_logs, "#0a1628", "#00d9ff", 100, "📜")
        CircularButton(self.canvas, cx + 400, cy + 150, "", "New Password", self.show_password, "#0a1628", "#00d9ff", 100, "🔑")
        CircularButton(self.canvas, cx, cy, "", "Run Monitor", self.show_monitor, "#361502", "#ff4500", 120, "▶")

    def create_back_button(self):
        back = tk.Button(self.content_frame, text="← BACK", command=self.show_home,
                         bg="#0a1628", fg="#00d9ff", font=("Courier New", 14, "bold"),
                         relief="flat", borderwidth=2, highlightbackground="#00d9ff",
                         highlightthickness=2, padx=20, pady=10, cursor="hand2")
        back.place(x=20, y=20)
        back.bind("<Enter>", lambda e: back.config(bg="#00d9ff", fg="#010118"))
        back.bind("<Leave>", lambda e: back.config(bg="#0a1628", fg="#00d9ff"))

    # --- REGISTER SCREEN (FIXED) ---
    def show_register(self):
        self.clear_content()
        self.current_screen = "register"
        self.update_screen_label("Registration")
        self.content_frame = tk.Frame(self.root, bg="#0a1628", highlightbackground="#00d9ff", highlightthickness=3)
        self.create_back_button()

        header = tk.Frame(self.content_frame, bg="#0a1628")
        header.pack(pady=30)
        tk.Label(header, text="➕", bg="#0a1628", fg="#00d9ff", font=("Arial", 32)).pack(side="left", padx=10)
        tk.Label(header, text="REGISTER NEW USER", bg="#0a1628", fg="#00d9ff",
                 font=("Courier New", 24, "bold")).pack(side="left")

        form = tk.Frame(self.content_frame, bg="#010118", highlightbackground="#00d9ff", highlightthickness=2)
        form.pack(padx=50, pady=20, fill="both", expand=True)

        tk.Label(form, text="USERNAME", bg="#010118", fg="#00d9ff",
                 font=("Courier New", 12, "bold")).pack(pady=(20, 5))
        uname_entry = tk.Entry(form, bg="#0a1628", fg="#00ffff", font=("Courier New", 14),
                               insertbackground="#00d9ff", relief="solid", borderwidth=2)
        uname_entry.pack(padx=50, fill="x")

        @threaded
        def do_register(uname, progress):
            try:
                capture_face_and_register(uname)
                progress.destroy()
                messagebox.showinfo("Success", f"User '{uname}' registered successfully.")
            except Exception as e:
                progress.destroy()
                messagebox.showerror("Error", str(e))

        def register_action():
            uname = uname_entry.get().strip()
            if not uname:
                messagebox.showerror("Error", "Please enter a username.")
                return
            progress = tk.Toplevel(self.root)
            progress.title("Registering...")
            progress.geometry("300x120")
            progress.configure(bg="#010118")
            tk.Label(progress, text=f"Capturing face for '{uname}'...", bg="#010118", fg="#00d9ff",
                     font=("Courier New", 12)).pack(pady=20)
            do_register(uname, progress)

        tk.Button(form, text="START REGISTRATION", command=register_action,
                  bg="#00d9ff", fg="#010118", font=("Courier New", 16, "bold"),
                  relief="flat", padx=20, pady=15, cursor="hand2").pack(padx=50, pady=20, fill="x")
        self.slide_in(self.content_frame)

    # --- USERS SCREEN (UNCHANGED) ---
    def show_users(self):
        self.clear_content()
        self.current_screen = "users"
        self.update_screen_label("User Management")
        self.content_frame = tk.Frame(self.root, bg="#0a1628", highlightbackground="#00d9ff", highlightthickness=3)
        self.create_back_button()

        header = tk.Frame(self.content_frame, bg="#0a1628")
        header.pack(pady=30)
        tk.Label(header, text="👥", bg="#0a1628", fg="#00d9ff", font=("Arial", 32)).pack(side="left", padx=10)
        tk.Label(header, text="MANAGE USERS", bg="#0a1628", fg="#00d9ff",
                 font=("Courier New", 24, "bold")).pack(side="left")

        users_container = tk.Frame(self.content_frame, bg="#010118",
                                   highlightbackground="#00d9ff", highlightthickness=2)
        users_container.pack(padx=50, pady=20, fill="both", expand=True)

        if not os.path.exists(DB_PATH):
            tk.Label(users_container, text="No users found", bg="#010118",
                     fg="#888", font=("Courier New", 16)).pack(pady=50)
        else:
            try:
                with open(DB_PATH) as f:
                    db = json.load(f)
                users = list(db.get("users", {}).keys())
                for uname in users:
                    row = tk.Frame(users_container, bg="#0a1628",
                                   highlightbackground="#00d9ff", highlightthickness=1)
                    row.pack(padx=20, pady=10, fill="x")
                    tk.Label(row, text="👤", bg="#0a1628", fg="#00d9ff", font=("Arial", 20)).pack(side="left", padx=10)
                    tk.Label(row, text=uname, bg="#0a1628", fg="#00ffff",
                             font=("Courier New", 14, "bold")).pack(side="left", padx=10)

                    def delete_user(u=uname):
                        if messagebox.askyesno("Confirm", f"Delete {u}?"):
                            try:
                                del db["users"][u]
                                with open(DB_PATH, "w") as f:
                                    json.dump(db, f, indent=2)
                                messagebox.showinfo("Deleted", f"{u} removed.")
                                self.show_users()
                            except Exception as e:
                                messagebox.showerror("Error", str(e))

                    tk.Button(row, text="❌ DELETE", command=delete_user,
                              bg="#ff0033", fg="white", font=("Arial", 10, "bold"),
                              relief="flat", padx=15, pady=5, cursor="hand2").pack(side="right", padx=10, pady=5)
            except Exception as e:
                tk.Label(users_container, text=f"Error: {e}", bg="#010118", fg="#ff0033",
                         font=("Courier New", 12)).pack(pady=50)

        self.slide_in(self.content_frame)

    # --- LOGS SCREEN (UNCHANGED) ---
    def show_logs(self):
        self.clear_content()
        self.current_screen = "logs"
        self.update_screen_label("Access Logs")
        self.content_frame = tk.Frame(self.root, bg="#0a1628",
                                      highlightbackground="#00d9ff", highlightthickness=3)
        self.create_back_button()

        header = tk.Frame(self.content_frame, bg="#0a1628")
        header.pack(pady=30)
        tk.Label(header, text="📜", bg="#0a1628", fg="#00d9ff", font=("Arial", 32)).pack(side="left", padx=10)
        tk.Label(header, text="ACCESS LOGS", bg="#0a1628", fg="#00d9ff",
                 font=("Courier New", 24, "bold")).pack(side="left", padx=20)

        def clear_logs():
            if messagebox.askyesno("Confirm", "Clear all logs?"):
                with open(LOG_PATH, "w") as f:
                    json.dump([], f)
                messagebox.showinfo("Cleared", "Logs cleared.")
                self.show_logs()

        tk.Button(header, text="🗑️ CLEAR LOGS", command=clear_logs, bg="#ff0033",
                  fg="white", font=("Arial", 12, "bold"), relief="flat",
                  padx=15, pady=8, cursor="hand2").pack(side="left", padx=20)

        logs_frame = tk.Frame(self.content_frame, bg="#010118",
                              highlightbackground="#00d9ff", highlightthickness=2)
        logs_frame.pack(padx=50, pady=20, fill="both", expand=True)

        txt = scrolledtext.ScrolledText(logs_frame, wrap="word", font=("Consolas", 11),
                                        bg="#0a1628", fg="#00ffff", insertbackground="#00ffff",
                                        relief="flat", borderwidth=0)
        txt.pack(fill="both", expand=True, padx=10, pady=10)

        if os.path.exists(LOG_PATH):
            try:
                with open(LOG_PATH) as f:
                    logs = json.load(f)
                if logs:
                    for entry in reversed(logs):
                        txt.insert("end", f"{entry['time']} - {entry['user']}\n")
                else:
                    txt.insert("end", "No log entries found.")
            except Exception as e:
                txt.insert("end", f"Error: {e}")
        else:
            txt.insert("end", "No logs yet.")

        txt.configure(state="disabled")
        self.slide_in(self.content_frame)

    # --- PASSWORD SCREEN (FIXED) ---
    def show_password(self):
        self.clear_content()
        self.current_screen = "password"
        self.update_screen_label("Security")
    
        self.content_frame = tk.Frame(self.root, bg="#0a1628",
                                     highlightbackground="#00d9ff",
                                     highlightthickness=3)
    
        self.create_back_button()
    
        header = tk.Frame(self.content_frame, bg="#0a1628")
        header.pack(pady=30)
    
        tk.Label(header, text="🔑", bg="#0a1628", fg="#00d9ff",
                font=("Arial", 32)).pack(side="left", padx=10)
        tk.Label(header, text="CHANGE PASSWORD", bg="#0a1628", fg="#00d9ff",
                font=("Courier New", 24, "bold")).pack(side="left")
    
        form_frame = tk.Frame(self.content_frame, bg="#010118",
                             highlightbackground="#00d9ff",
                             highlightthickness=2)
        form_frame.pack(padx=50, pady=20, fill="both", expand=True)
    
        # Current password
        tk.Label(form_frame, text="CURRENT PASSWORD", bg="#010118", fg="#00d9ff",
                font=("Courier New", 12, "bold")).pack(pady=(20, 5))
        current_entry = tk.Entry(form_frame, bg="#0a1628", fg="#00ffff",
                                font=("Courier New", 14), show="*",
                                insertbackground="#00d9ff",
                                relief="solid", borderwidth=2)
        current_entry.pack(padx=50, fill="x")
    
        # New password
        tk.Label(form_frame, text="NEW PASSWORD", bg="#010118", fg="#00d9ff",
                font=("Courier New", 12, "bold")).pack(pady=(20, 5))
        new_entry = tk.Entry(form_frame, bg="#0a1628", fg="#00ffff",
                            font=("Courier New", 14), show="*",
                            insertbackground="#00d9ff",
                            relief="solid", borderwidth=2)
        new_entry.pack(padx=50, fill="x")
    
        # Confirm password
        tk.Label(form_frame, text="CONFIRM NEW PASSWORD", bg="#010118", fg="#00d9ff",
                font=("Courier New", 12, "bold")).pack(pady=(20, 5))
        confirm_entry = tk.Entry(form_frame, bg="#0a1628", fg="#00ffff",
                                font=("Courier New", 14), show="*",
                                insertbackground="#00d9ff",
                                relief="solid", borderwidth=2)
        confirm_entry.pack(padx=50, fill="x")
    
        def change_password_action():
            current_pwd = current_entry.get()
            new_pwd = new_entry.get()
            confirm_pwd = confirm_entry.get()
        
            if not admin_auth.verify_password_dialog(self.root, entered_password=current_pwd):
                messagebox.showerror("Error", "Current password incorrect.")
                return
        
            ok = admin_auth.set_new_password(self.root, new_password=new_pwd, confirm_password=confirm_pwd)
            if ok:
                current_entry.delete(0, tk.END)
                new_entry.delete(0, tk.END)
                confirm_entry.delete(0, tk.END)
    
        update_btn = tk.Button(
            form_frame,
            text="UPDATE PASSWORD",
            command=change_password_action,
            bg="#00d9ff",
            fg="#010118",
            font=("Courier New", 16, "bold"),
            relief="flat",
            padx=20,
            pady=15,
            cursor="hand2"
        )
        update_btn.pack(padx=50, pady=30, fill="x")
    
        self.slide_in(self.content_frame)

    # --- MONITOR SCREEN (FIXED) ---
    def show_monitor(self):
        self.clear_content()
        self.current_screen = "monitor"
        self.update_screen_label("Live Monitor")
        self.content_frame = tk.Frame(self.root, bg="#0a1628",
                                      highlightbackground="#00d9ff", highlightthickness=3)
        self.create_back_button()

        header = tk.Frame(self.content_frame, bg="#0a1628")
        header.pack(pady=30)
        tk.Label(header, text="▶", bg="#0a1628", fg="#ff4500", font=("Arial", 32)).pack(side="left", padx=10)
        tk.Label(header, text="FACE RECOGNITION MONITOR", bg="#0a1628", fg="#00d9ff",
                 font=("Courier New", 24, "bold")).pack(side="left")
        
        @threaded
        def run_monitor():
            try:
                overlay = LoadingOverlay(self.root, "Starting Face Recognition Monitor...")
                subprocess.Popen([sys.executable, "monitor.py"])
                time.sleep(8) 
                overlay.close()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to start monitor:\n{e}")

        tk.Button(self.content_frame, text="▶ START MONITORING", command=run_monitor,
                  bg="#ff4500", fg="white", font=("Courier New", 16, "bold"),
                  relief="flat", padx=20, pady=15, cursor="hand2").pack(padx=50, pady=40, fill="x")
        self.slide_in(self.content_frame)


# --- Entry Point ---
def main():
    root = tk.Tk()
    root.withdraw()
    if not admin_auth.ensure_and_verify(root):
        root.destroy()
        return
    root.deiconify()
    app = AdminPanel(root)
    root.protocol("WM_DELETE_WINDOW", root.destroy)
    root.mainloop()


if __name__ == "__main__":
    main()
