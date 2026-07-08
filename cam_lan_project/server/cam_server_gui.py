import cv2
import socket
import threading
import time
import subprocess
import re
import tkinter as tk
from tkinter import ttk, messagebox
from flask import Flask, Response
from PIL import Image, ImageTk

# =========================
# Shared state
# =========================
camera = None
camera_info_list = []   # list of dicts: {"name": ..., "index": ..., "path": ...}
frame_lock = threading.Lock()
latest_frame = None

server_running = False
capture_running = False
server_port = 5000

selected_camera_index = None
selected_width = 1280
selected_height = 720
selected_fps = 15

app = Flask(__name__)


# =========================
# Utility
# =========================
def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    except Exception:
        ip = "127.0.0.1"
    finally:
        s.close()
    return ip


def parse_v4l2_devices():
    """
    Parses output of:
        v4l2-ctl --list-devices

    Returns a list like:
    [
        {"name": "GENERAL WEBCAM", "index": 3, "path": "/dev/video3"},
        {"name": "Integrated Camera", "index": 0, "path": "/dev/video0"},
    ]

    Prefers the first /dev/videoX entry under each device block.
    """
    devices = []

    try:
        result = subprocess.run(
            ["v4l2-ctl", "--list-devices"],
            capture_output=True,
            text=True,
            check=True
        )
        output = result.stdout
    except Exception:
        return []

    lines = output.splitlines()
    current_name = None
    current_video_paths = []

    def flush_current():
        nonlocal current_name, current_video_paths, devices
        if current_name and current_video_paths:
            first_path = current_video_paths[0]
            m = re.search(r"/dev/video(\d+)", first_path)
            if m:
                idx = int(m.group(1))
                devices.append({
                    "name": current_name.strip(),
                    "index": idx,
                    "path": first_path.strip()
                })
        current_name = None
        current_video_paths = []

    for raw_line in lines:
        line = raw_line.rstrip()

        # Device name line usually doesn't start with tab/spaces
        if line and not line.startswith("\t") and not line.startswith(" "):
            flush_current()
            current_name = line.rstrip(":")
        else:
            path = line.strip()
            if path.startswith("/dev/video"):
                current_video_paths.append(path)

    flush_current()

    return devices


def test_camera(index):
    """
    Test if a camera can be opened and read with V4L2 + MJPG.
    """
    cap = cv2.VideoCapture(index, cv2.CAP_V4L2)
    if not cap.isOpened():
        return False

    # Try forcing MJPG for old webcams
    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
    ok, _ = cap.read()
    cap.release()
    return ok


def detect_cameras():
    """
    Detect cameras from v4l2-ctl and keep only working ones.
    """
    raw_devices = parse_v4l2_devices()
    found = []

    for dev in raw_devices:
        idx = dev["index"]
        if test_camera(idx):
            found.append(dev)

    return found


def open_camera(index, width, height, fps):
    """
    Open the camera using V4L2 and try to force MJPG.
    """
    global camera

    if camera is not None:
        camera.release()
        camera = None

    cam = cv2.VideoCapture(index, cv2.CAP_V4L2)
    if not cam.isOpened():
        return None

    # Old USB webcams often work best with MJPG
    cam.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))

    cam.set(cv2.CAP_PROP_FRAME_WIDTH, width)
    cam.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
    cam.set(cv2.CAP_PROP_FPS, fps)

    # Warm up camera
    ok = False
    for _ in range(10):
        ok, _ = cam.read()
        if ok:
            break
        time.sleep(0.05)

    if not ok:
        cam.release()
        return None

    return cam


# =========================
# Capture loop
# =========================
def capture_loop():
    global latest_frame, capture_running, camera

    while capture_running:
        if camera is None:
            time.sleep(0.05)
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

        ok, buffer = cv2.imencode(
            ".jpg",
            frame,
            [int(cv2.IMWRITE_JPEG_QUALITY), 80]
        )
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
                padding: 20px;
            }}
            img {{
                max-width: 95vw;
                border: 2px solid #444;
                border-radius: 8px;
            }}
            .box {{
                margin-top: 20px;
            }}
            .small {{
                color: #aaa;
                font-size: 14px;
            }}
        </style>
    </head>
    <body>
        <div class="box">
            <h2>Omarchy Camera Stream</h2>
            <p>Viewer URL:</p>
            <p><b>http://{ip}:{server_port}/video</b></p>
            <p class="small">Open this on the Windows laptop viewer.</p>
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
    app.run(
        host="0.0.0.0",
        port=server_port,
        debug=False,
        threaded=True,
        use_reloader=False
    )


# =========================
# GUI
# =========================
class CamServerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Cam LAN Server - Omarchy")
        self.root.geometry("1200x780")
        self.root.configure(bg="#111111")

        self.server_thread = None
        self.preview_after_id = None

        self.status_var = tk.StringVar(value="Idle")
        self.url_var = tk.StringVar(value="Not running")
        self.ip_var = tk.StringVar(value=f"LAN IP: {get_local_ip()}")

        self.build_ui()
        self.refresh_camera_list()
        self.update_preview()

    def build_ui(self):
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except Exception:
            pass

        main = tk.Frame(self.root, bg="#111111")
        main.pack(fill="both", expand=True, padx=12, pady=12)

        left = tk.Frame(main, bg="#111111")
        left.pack(side="left", fill="y", padx=(0, 12))

        right = tk.Frame(main, bg="#111111")
        right.pack(side="left", fill="both", expand=True)

        # Title
        tk.Label(
            left,
            text="Cam LAN Server",
            fg="white",
            bg="#111111",
            font=("Segoe UI", 18, "bold")
        ).pack(anchor="w", pady=(0, 12))

        tk.Label(
            left,
            textvariable=self.ip_var,
            fg="#cfcfcf",
            bg="#111111",
            font=("Segoe UI", 10)
        ).pack(anchor="w", pady=(0, 12))

        # Camera
        tk.Label(
            left,
            text="Camera",
            fg="white",
            bg="#111111",
            font=("Segoe UI", 10, "bold")
        ).pack(anchor="w")

        self.camera_combo = ttk.Combobox(left, state="readonly", width=42)
        self.camera_combo.pack(anchor="w", pady=(4, 8))

        ttk.Button(left, text="Refresh cameras", command=self.refresh_camera_list).pack(anchor="w", pady=(0, 14))

        # Resolution
        tk.Label(
            left,
            text="Resolution",
            fg="white",
            bg="#111111",
            font=("Segoe UI", 10, "bold")
        ).pack(anchor="w")

        self.res_combo = ttk.Combobox(
            left,
            state="readonly",
            width=42,
            values=[
                "640x480",
                "1280x720",
                "1920x1080"
            ]
        )
        self.res_combo.set("1280x720")
        self.res_combo.pack(anchor="w", pady=(4, 14))

        # FPS
        tk.Label(
            left,
            text="FPS",
            fg="white",
            bg="#111111",
            font=("Segoe UI", 10, "bold")
        ).pack(anchor="w")

        self.fps_combo = ttk.Combobox(
            left,
            state="readonly",
            width=42,
            values=["15", "24", "30", "60"]
        )
        self.fps_combo.set("15")
        self.fps_combo.pack(anchor="w", pady=(4, 14))

        # Port
        tk.Label(
            left,
            text="Port",
            fg="white",
            bg="#111111",
            font=("Segoe UI", 10, "bold")
        ).pack(anchor="w")

        self.port_entry = ttk.Entry(left, width=45)
        self.port_entry.insert(0, "5000")
        self.port_entry.pack(anchor="w", pady=(4, 14))

        # Buttons
        self.start_btn = ttk.Button(left, text="Start server", command=self.start_server)
        self.start_btn.pack(anchor="w", fill="x", pady=(0, 8))

        self.stop_btn = ttk.Button(left, text="Stop server", command=self.stop_server)
        self.stop_btn.pack(anchor="w", fill="x", pady=(0, 16))

        # Status
        tk.Label(
            left,
            text="Status",
            fg="white",
            bg="#111111",
            font=("Segoe UI", 10, "bold")
        ).pack(anchor="w")

        tk.Label(
            left,
            textvariable=self.status_var,
            fg="#d0d0d0",
            bg="#111111",
            justify="left",
            wraplength=320
        ).pack(anchor="w", pady=(4, 10))

        tk.Label(
            left,
            text="Viewer URL",
            fg="white",
            bg="#111111",
            font=("Segoe UI", 10, "bold")
        ).pack(anchor="w")

        tk.Label(
            left,
            textvariable=self.url_var,
            fg="#8fd3ff",
            bg="#111111",
            justify="left",
            wraplength=320
        ).pack(anchor="w", pady=(4, 10))

        help_text = (
            "Recommended for your webcam:\n"
            "- GENERAL WEBCAM (/dev/video3)\n"
            "- 1280x720 or 640x480\n"
            "- 15 FPS first\n\n"
            "Usage:\n"
            "1. Plug in webcam\n"
            "2. Refresh cameras\n"
            "3. Pick GENERAL WEBCAM\n"
            "4. Start server\n"
            "5. Open shown URL on Windows viewer"
        )

        tk.Label(
            left,
            text=help_text,
            fg="#aaaaaa",
            bg="#111111",
            justify="left"
        ).pack(anchor="w", pady=(16, 0))

        # Preview
        tk.Label(
            right,
            text="Local Preview",
            fg="white",
            bg="#111111",
            font=("Segoe UI", 14, "bold")
        ).pack(anchor="w", pady=(0, 10))

        self.preview_label = tk.Label(right, bg="#222222")
        self.preview_label.pack(fill="both", expand=True)

    def refresh_camera_list(self):
        global camera_info_list
        camera_info_list = detect_cameras()

        if not camera_info_list:
            self.camera_combo["values"] = []
            self.camera_combo.set("")
            self.status_var.set("No working cameras found.")
            return

        display_values = [
            f'{cam["name"]} ({cam["path"]})'
            for cam in camera_info_list
        ]

        self.camera_combo["values"] = display_values

        # Prefer GENERAL WEBCAM if present
        preferred_index = 0
        for i, cam in enumerate(camera_info_list):
            if "GENERAL WEBCAM" in cam["name"].upper():
                preferred_index = i
                break

        self.camera_combo.current(preferred_index)

        found_names = ", ".join(display_values)
        self.status_var.set(f"Found cameras:\n{found_names}")

    def get_selected_camera_info(self):
        idx = self.camera_combo.current()
        if idx < 0 or idx >= len(camera_info_list):
            return None
        return camera_info_list[idx]

    def parse_resolution(self):
        text = self.res_combo.get().strip()
        try:
            w, h = text.split("x")
            return int(w), int(h)
        except Exception:
            return 1280, 720

    def start_server(self):
        global camera, capture_running, server_running
        global selected_camera_index, selected_width, selected_height, selected_fps, server_port

        if server_running:
            messagebox.showinfo("Already running", "Server is already running.")
            return

        cam_info = self.get_selected_camera_info()
        if cam_info is None:
            messagebox.showerror("No camera", "Pick a camera first.")
            return

        width, height = self.parse_resolution()

        try:
            fps = int(self.fps_combo.get().strip())
        except Exception:
            fps = 15

        try:
            port = int(self.port_entry.get().strip())
        except Exception:
            messagebox.showerror("Invalid port", "Port must be a number.")
            return

        selected_camera_index = cam_info["index"]
        selected_width = width
        selected_height = height
        selected_fps = fps
        server_port = port

        cam = open_camera(selected_camera_index, selected_width, selected_height, selected_fps)
        if cam is None:
            messagebox.showerror(
                "Camera error",
                f"Could not open camera {cam_info['name']} ({cam_info['path']}).\n"
                f"Try 640x480 at 15 FPS."
            )
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
            "Running\n"
            f"Camera: {cam_info['name']} ({cam_info['path']})\n"
            f"Index: {selected_camera_index}\n"
            f"Resolution: {selected_width}x{selected_height}\n"
            f"FPS: {selected_fps}\n"
            f"Port: {server_port}"
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
        self.stop_server()
        if self.preview_after_id:
            self.root.after_cancel(self.preview_after_id)
        self.root.destroy()


def main():
    root = tk.Tk()
    gui = CamServerGUI(root)
    root.protocol("WM_DELETE_WINDOW", gui.on_close)
    root.mainloop()


if __name__ == "__main__":
    main()