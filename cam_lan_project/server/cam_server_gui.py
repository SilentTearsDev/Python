import cv2
import socket
import threading
import time
from io import BytesIO
from flask import Flask, Response
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk

# =========================
# Shared camera state
# =========================
camera = None
camera_index = 0
frame_lock = threading.Lock()
latest_frame = None
server_running = False
capture_running = False

selected_width = 1280
selected_height = 720
selected_fps = 30
server_port = 5000

app = Flask(__name__)


# =========================
# Utility
# =========================
def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # Doesn't need to actually reach internet, just picks the active interface
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    except Exception:
        ip = "127.0.0.1"
    finally:
        s.close()
    return ip


def detect_cameras(max_test=8):
    found = []
    for i in range(max_test):
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            ret, _ = cap.read()
            if ret:
                found.append(i)
        cap.release()
    return found


# =========================
# Camera capture loop
# =========================
def open_camera(index, width, height, fps):
    global camera
    if camera is not None:
        camera.release()
        camera = None

    cam = cv2.VideoCapture(index)
    if not cam.isOpened():
        return None

    cam.set(cv2.CAP_PROP_FRAME_WIDTH, width)
    cam.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
    cam.set(cv2.CAP_PROP_FPS, fps)
    return cam


def capture_loop():
    global latest_frame, capture_running, camera

    while capture_running:
        if camera is None:
            time.sleep(0.1)
            continue

        ok, frame = camera.read()
        if not ok:
            time.sleep(0.02)
            continue

        with frame_lock:
            latest_frame = frame

        time.sleep(0.001)


# =========================
# Flask MJPEG stream
# =========================
def mjpeg_generator():
    global latest_frame
    while server_running:
        frame = None
        with frame_lock:
            if latest_frame is not None:
                frame = latest_frame.copy()

        if frame is None:
            time.sleep(0.02)
            continue

        ok, buffer = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
        if not ok:
            continue

        jpg = buffer.tobytes()

        yield (
            b"--frame\r\n"
            b"Content-Type: image/jpeg\r\n\r\n" + jpg + b"\r\n"
        )

        time.sleep(0.01)


@app.route("/")
def index():
    ip = get_local_ip()
    return f"""
    <html>
    <head>
        <title>Omarchy Camera Stream</title>
        <style>
            body {{
                background: #111;
                color: white;
                font-family: Arial, sans-serif;
                text-align: center;
            }}
            img {{
                max-width: 95vw;
                border: 2px solid #444;
            }}
            .box {{
                margin-top: 20px;
            }}
        </style>
    </head>
    <body>
        <div class="box">
            <h2>Omarchy Camera Stream</h2>
            <p>Viewer URL: http://{ip}:{server_port}/video</p>
            <img src="/video">
        </div>
    </body>
    </html>
    """


@app.route("/video")
def video():
    return Response(
        mjpeg_generator(),
        mimetype="multipart/x-mixed-replace; boundary=frame"
    )


def run_flask():
    app.run(host="0.0.0.0", port=server_port, debug=False, threaded=True, use_reloader=False)


# =========================
# Tkinter GUI
# =========================
class CamServerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Cam LAN Server - Omarchy")
        self.root.geometry("1100x760")
        self.root.configure(bg="#111111")

        self.preview_label = None
        self.status_var = tk.StringVar(value="Idle")
        self.url_var = tk.StringVar(value="Not running")
        self.ip_var = tk.StringVar(value=f"LAN IP: {get_local_ip()}")

        self.server_thread = None
        self.preview_after_id = None

        self.build_ui()
        self.refresh_camera_list()
        self.update_preview()

    def build_ui(self):
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except:
            pass

        main = tk.Frame(self.root, bg="#111111")
        main.pack(fill="both", expand=True, padx=12, pady=12)

        left = tk.Frame(main, bg="#111111")
        left.pack(side="left", fill="y", padx=(0, 12))

        right = tk.Frame(main, bg="#111111")
        right.pack(side="left", fill="both", expand=True)

        title = tk.Label(left, text="Cam LAN Server", fg="white", bg="#111111", font=("Segoe UI", 18, "bold"))
        title.pack(anchor="w", pady=(0, 12))

        ip_label = tk.Label(left, textvariable=self.ip_var, fg="#cfcfcf", bg="#111111", font=("Segoe UI", 10))
        ip_label.pack(anchor="w", pady=(0, 12))

        # Camera selector
        tk.Label(left, text="Camera", fg="white", bg="#111111", font=("Segoe UI", 10, "bold")).pack(anchor="w")
        self.camera_combo = ttk.Combobox(left, state="readonly", width=28)
        self.camera_combo.pack(anchor="w", pady=(4, 8))

        ttk.Button(left, text="Refresh cameras", command=self.refresh_camera_list).pack(anchor="w", pady=(0, 14))

        # Resolution selector
        tk.Label(left, text="Resolution", fg="white", bg="#111111", font=("Segoe UI", 10, "bold")).pack(anchor="w")
        self.res_combo = ttk.Combobox(left, state="readonly", width=28, values=[
            "640x480",
            "1280x720",
            "1920x1080"
        ])
        self.res_combo.set("1280x720")
        self.res_combo.pack(anchor="w", pady=(4, 14))

        # FPS
        tk.Label(left, text="FPS", fg="white", bg="#111111", font=("Segoe UI", 10, "bold")).pack(anchor="w")
        self.fps_combo = ttk.Combobox(left, state="readonly", width=28, values=["15", "24", "30", "60"])
        self.fps_combo.set("30")
        self.fps_combo.pack(anchor="w", pady=(4, 14))

        # Port
        tk.Label(left, text="Port", fg="white", bg="#111111", font=("Segoe UI", 10, "bold")).pack(anchor="w")
        self.port_entry = ttk.Entry(left, width=30)
        self.port_entry.insert(0, "5000")
        self.port_entry.pack(anchor="w", pady=(4, 14))

        # Buttons
        self.start_btn = ttk.Button(left, text="Start server", command=self.start_server)
        self.start_btn.pack(anchor="w", fill="x", pady=(0, 8))

        self.stop_btn = ttk.Button(left, text="Stop server", command=self.stop_server)
        self.stop_btn.pack(anchor="w", fill="x", pady=(0, 16))

        # Status
        tk.Label(left, text="Status", fg="white", bg="#111111", font=("Segoe UI", 10, "bold")).pack(anchor="w")
        tk.Label(left, textvariable=self.status_var, fg="#d0d0d0", bg="#111111", justify="left", wraplength=280).pack(anchor="w", pady=(4, 10))

        tk.Label(left, text="Viewer URL", fg="white", bg="#111111", font=("Segoe UI", 10, "bold")).pack(anchor="w")
        tk.Label(left, textvariable=self.url_var, fg="#8fd3ff", bg="#111111", justify="left", wraplength=280).pack(anchor="w", pady=(4, 10))

        help_text = (
            "Use this on the Omarchy laptop.\n\n"
            "1. Plug in the webcam\n"
            "2. Refresh cameras\n"
            "3. Pick the camera\n"
            "4. Click Start server\n"
            "5. Open the shown URL on the Windows viewer"
        )
        tk.Label(left, text=help_text, fg="#aaaaaa", bg="#111111", justify="left").pack(anchor="w", pady=(16, 0))

        # Right side preview
        tk.Label(right, text="Local Preview", fg="white", bg="#111111", font=("Segoe UI", 14, "bold")).pack(anchor="w", pady=(0, 10))
        self.preview_label = tk.Label(right, bg="#222222", width=960, height=540)
        self.preview_label.pack(fill="both", expand=True)

    def refresh_camera_list(self):
        cams = detect_cameras()
        if not cams:
            self.camera_combo["values"] = []
            self.camera_combo.set("")
            self.status_var.set("No cameras found.")
            return

        values = [f"Camera {i}" for i in cams]
        self.camera_combo["values"] = values
        self.camera_combo.current(0)
        self.status_var.set(f"Found cameras: {', '.join(values)}")

    def parse_selected_camera(self):
        text = self.camera_combo.get().strip()
        if not text:
            return None
        try:
            return int(text.split()[-1])
        except:
            return None

    def parse_resolution(self):
        text = self.res_combo.get().strip()
        try:
            w, h = text.split("x")
            return int(w), int(h)
        except:
            return 1280, 720

    def start_server(self):
        global camera, camera_index, selected_width, selected_height, selected_fps
        global capture_running, server_running, server_port

        if server_running:
            messagebox.showinfo("Already running", "Server is already running.")
            return

        cam_index = self.parse_selected_camera()
        if cam_index is None:
            messagebox.showerror("No camera", "Pick a camera first.")
            return

        width, height = self.parse_resolution()

        try:
            fps = int(self.fps_combo.get().strip())
        except:
            fps = 30

        try:
            port = int(self.port_entry.get().strip())
        except:
            messagebox.showerror("Invalid port", "Port must be a number.")
            return

        camera_index = cam_index
        selected_width = width
        selected_height = height
        selected_fps = fps
        server_port = port

        cam = open_camera(camera_index, selected_width, selected_height, selected_fps)
        if cam is None:
            messagebox.showerror("Camera error", f"Could not open camera {camera_index}.")
            return

        camera = cam
        capture_running = True
        server_running = True

        threading.Thread(target=capture_loop, daemon=True).start()

        self.server_thread = threading.Thread(target=run_flask, daemon=True)
        self.server_thread.start()

        ip = get_local_ip()
        self.url_var.set(f"http://{ip}:{server_port}/video")
        self.status_var.set(
            f"Running\nCamera: {camera_index}\nResolution: {selected_width}x{selected_height}\nFPS: {selected_fps}\nPort: {server_port}"
        )

    def stop_server(self):
        global capture_running, server_running, camera, latest_frame

        if not server_running and not capture_running:
            self.status_var.set("Server already stopped.")
            return

        server_running = False
        capture_running = False
        latest_frame = None

        if camera is not None:
            camera.release()
            camera = None

        self.url_var.set("Not running")
        self.status_var.set("Stopped")

    def update_preview(self):
        frame = None
        with frame_lock:
            if latest_frame is not None:
                frame = latest_frame.copy()

        if frame is not None:
            # Convert BGR -> RGB
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            # Fit into preview area
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
        self.stop_server()
        if self.preview_after_id:
            self.root.after_cancel(self.preview_after_id)
        self.root.destroy()


def main():
    root = tk.Tk()
    app_gui = CamServerGUI(root)
    root.protocol("WM_DELETE_WINDOW", app_gui.on_close)
    root.mainloop()


if __name__ == "__main__":
    main()