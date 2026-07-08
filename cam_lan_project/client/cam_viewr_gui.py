import threading
import time
import tkinter as tk
from tkinter import ttk, messagebox

import cv2
from PIL import Image, ImageTk


class CamViewerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Cam LAN Viewer - Windows")
        self.root.geometry("1100x760")
        self.root.configure(bg="#111111")

        self.cap = None
        self.running = False
        self.latest_frame = None
        self.frame_lock = threading.Lock()
        self.reader_thread = None
        self.preview_after_id = None

        self.status_var = tk.StringVar(value="Disconnected")

        self.build_ui()
        self.update_preview()

    def build_ui(self):
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except:
            pass

        main = tk.Frame(self.root, bg="#111111")
        main.pack(fill="both", expand=True, padx=12, pady=12)

        top = tk.Frame(main, bg="#111111")
        top.pack(fill="x", pady=(0, 12))

        tk.Label(top, text="Cam LAN Viewer", fg="white", bg="#111111", font=("Segoe UI", 18, "bold")).pack(anchor="w")

        row = tk.Frame(main, bg="#111111")
        row.pack(fill="x", pady=(0, 12))

        tk.Label(row, text="Stream URL:", fg="white", bg="#111111", font=("Segoe UI", 10, "bold")).pack(side="left", padx=(0, 8))

        self.url_entry = ttk.Entry(row, width=60)
        self.url_entry.pack(side="left", padx=(0, 8))
        self.url_entry.insert(0, "http://192.168.1.100:5000/video")

        ttk.Button(row, text="Connect", command=self.connect_stream).pack(side="left", padx=(0, 8))
        ttk.Button(row, text="Disconnect", command=self.disconnect_stream).pack(side="left", padx=(0, 8))

        tk.Label(main, textvariable=self.status_var, fg="#d0d0d0", bg="#111111").pack(anchor="w", pady=(0, 10))

        self.preview_label = tk.Label(main, bg="#222222")
        self.preview_label.pack(fill="both", expand=True)

        help_text = (
            "Put the Omarchy stream URL here, for example:\n"
            "http://192.168.1.123:5000/video\n\n"
            "Then click Connect."
        )
        tk.Label(main, text=help_text, fg="#aaaaaa", bg="#111111", justify="left").pack(anchor="w", pady=(10, 0))

    def connect_stream(self):
        if self.running:
            messagebox.showinfo("Already connected", "Viewer is already connected.")
            return

        url = self.url_entry.get().strip()
        if not url:
            messagebox.showerror("Missing URL", "Enter the stream URL first.")
            return

        cap = cv2.VideoCapture(url)
        if not cap.isOpened():
            messagebox.showerror("Connection failed", "Could not open the stream.")
            return

        self.cap = cap
        self.running = True
        self.status_var.set(f"Connected to {url}")

        self.reader_thread = threading.Thread(target=self.read_loop, daemon=True)
        self.reader_thread.start()

    def disconnect_stream(self):
        self.running = False
        if self.cap is not None:
            self.cap.release()
            self.cap = None
        self.status_var.set("Disconnected")

    def read_loop(self):
        while self.running and self.cap is not None:
            ok, frame = self.cap.read()
            if not ok:
                self.status_var.set("Stream read failed / disconnected")
                self.running = False
                break

            with self.frame_lock:
                self.latest_frame = frame

            time.sleep(0.001)

        if self.cap is not None:
            self.cap.release()
            self.cap = None

    def update_preview(self):
        frame = None
        with self.frame_lock:
            if self.latest_frame is not None:
                frame = self.latest_frame.copy()

        if frame is not None:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            preview_w = 960
            preview_h = 540
            h, w = frame.shape[:2]

            scale = min(preview_w / w, preview_h / h)
            new_w = max(1, int(w * scale))
            new_h = max(1, int(h * scale))
            frame = cv2.resize(frame, (new_w, new_h))

            img = Image.fromarray(frame)
            imgtk = ImageTk.PhotoImage(image=img)
            self.preview_label.imgtk = imgtk
            self.preview_label.configure(image=imgtk)

        self.preview_after_id = self.root.after(30, self.update_preview)

    def on_close(self):
        self.disconnect_stream()
        if self.preview_after_id:
            self.root.after_cancel(self.preview_after_id)
        self.root.destroy()


def main():
    root = tk.Tk()
    gui = CamViewerGUI(root)
    root.protocol("WM_DELETE_WINDOW", gui.on_close)
    root.mainloop()


if __name__ == "__main__":
    main()