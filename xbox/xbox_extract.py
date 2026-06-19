import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
import subprocess
import threading
import os
import platform

# Change this to where extract-xiso is located
EXTRACT_XISO = "./extract-xiso"


def open_folder(path):
    if platform.system() == "Windows":
        os.startfile(path)
    elif platform.system() == "Darwin":
        subprocess.run(["open", path])
    else:
        subprocess.run(["xdg-open", path])


def select_iso():
    filename = filedialog.askopenfilename(
        title="Select Xbox ISO",
        filetypes=[("ISO Files", "*.iso"), ("All Files", "*.*")]
    )

    if filename:
        iso_path.delete(0, tk.END)
        iso_path.insert(0, filename)


def extract_game():
    iso = iso_path.get()

    if not iso:
        messagebox.showerror("Error", "Please select an ISO file.")
        return

    threading.Thread(
        target=run_extract,
        args=(iso,),
        daemon=True
    ).start()


def run_extract(iso):
    output_box.delete("1.0", tk.END)

    iso_name = os.path.splitext(os.path.basename(iso))[0]
    export_folder = os.path.join(os.path.dirname(iso), iso_name)

    cmd = [EXTRACT_XISO, "-x", iso]

    output_box.insert(tk.END, f"Running: {' '.join(cmd)}\n\n")

    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )

        for line in process.stdout:
            output_box.insert(tk.END, line)
            output_box.see(tk.END)

        process.wait()

        output_box.insert(
            tk.END,
            f"\nFinished!\nOpening folder:\n{export_folder}\n"
        )

        if os.path.exists(export_folder):
            open_folder(export_folder)
        else:
            open_folder(os.path.dirname(iso))

    except Exception as e:
        output_box.insert(tk.END, f"\nERROR:\n{e}\n")


root = tk.Tk()
root.title("Xbox ISO Extractor")
root.geometry("800x500")

frame = tk.Frame(root)
frame.pack(fill="x", padx=10, pady=10)

iso_path = tk.Entry(frame)
iso_path.pack(side="left", fill="x", expand=True)

browse_btn = tk.Button(frame, text="Browse ISO", command=select_iso)
browse_btn.pack(side="left", padx=5)

extract_btn = tk.Button(root, text="Extract", command=extract_game)
extract_btn.pack(pady=5)

output_box = scrolledtext.ScrolledText(root)
output_box.pack(fill="both", expand=True, padx=10, pady=10)

root.mainloop()