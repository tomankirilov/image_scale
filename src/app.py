import json
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image

# -------------------------------------------------
# Config persistence
# -------------------------------------------------

CONFIG_PATH = Path(__file__).parent / "config.json"


def load_config():
    if CONFIG_PATH.exists():
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def save_config():
    data = {
        "source": source_var.get(),
        "destination": dest_var.get(),
        "scale": scale_var.get(),
        "overwrite": overwrite_var.get(),
        "resample": resample_var.get(),
        "suffix": suffix_var.get(),
        "recursive": recursive_var.get(),
    }
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


# -------------------------------------------------
# Constants
# -------------------------------------------------

RESAMPLE_MAP = {
    "nearest": Image.NEAREST,
    "bilinear": Image.BILINEAR,
    "bicubic": Image.BICUBIC,
}

SUPPORTED_EXTENSIONS = (".png", ".jpg", ".jpeg", ".tga")


# -------------------------------------------------
# UI callbacks
# -------------------------------------------------

def choose_source():
    path = filedialog.askdirectory()
    if path:
        source_var.set(path)


def choose_destination():
    path = filedialog.askdirectory()
    if path:
        dest_var.set(path)


def apply_preset(event=None):
    value = preset_var.get()
    if value.isdigit():
        scale_var.set(int(value))


def clear_preset_on_manual_scale(*_):
    preset_var.set("")


def on_run():
    save_config()

    src_root = Path(source_var.get())
    dst_root = Path(dest_var.get())
    scale = scale_var.get() / 100.0
    overwrite = overwrite_var.get()
    recursive = recursive_var.get()
    resample = RESAMPLE_MAP[resample_var.get()]
    suffix = suffix_var.get().strip()

    if not src_root.is_dir():
        messagebox.showerror("Error", "Invalid source folder.")
        return

    if not dst_root.is_dir():
        messagebox.showerror("Error", "Invalid destination folder.")
        return

    if src_root.resolve() == dst_root.resolve():
        messagebox.showerror(
            "Error", "Source and destination folders must be different."
        )
        return

    if scale <= 0:
        messagebox.showerror("Error", "Scale must be greater than 0%.")
        return

    # Choose traversal mode
    if recursive:
        files = [
            f for f in src_root.rglob("*")
            if f.is_file() and f.suffix.lower() in SUPPORTED_EXTENSIONS
        ]
    else:
        files = [
            f for f in src_root.iterdir()
            if f.is_file() and f.suffix.lower() in SUPPORTED_EXTENSIONS
        ]

    if not files:
        messagebox.showinfo("Info", "No supported images found.")
        return

    progress["maximum"] = len(files)
    progress["value"] = 0
    root.update_idletasks()

    processed = skipped = errors = 0

    for file in files:
        try:
            if recursive:
                relative = file.relative_to(src_root)
                out_dir = dst_root / relative.parent
            else:
                out_dir = dst_root

            out_dir.mkdir(parents=True, exist_ok=True)

            out_name = (
                f"{file.stem}{suffix}{file.suffix}"
                if suffix else file.name
            )
            out_path = out_dir / out_name

            if out_path.exists() and not overwrite:
                skipped += 1
            else:
                with Image.open(file) as img:
                    new_size = (
                        max(1, int(img.width * scale)),
                        max(1, int(img.height * scale)),
                    )

                    resized = img.resize(new_size, resample=resample)

                    save_kwargs = {}
                    if img.format == "JPEG":
                        save_kwargs["quality"] = 95
                        save_kwargs["subsampling"] = 0

                    resized.save(out_path, format=img.format, **save_kwargs)
                    processed += 1

        except Exception:
            errors += 1

        progress["value"] += 1
        root.update_idletasks()

    messagebox.showinfo(
        "Done",
        f"Processed: {processed}\nSkipped: {skipped}\nErrors: {errors}",
    )


# -------------------------------------------------
# UI setup
# -------------------------------------------------

root = tk.Tk()
root.title("Image Scaler")
root.resizable(False, False)

root.columnconfigure(0, weight=0)
root.columnconfigure(1, weight=1)
root.columnconfigure(2, weight=0)

padding = {"padx": 10, "pady": 5}

source_var = tk.StringVar()
dest_var = tk.StringVar()
scale_var = tk.IntVar(value=50)
preset_var = tk.StringVar()
overwrite_var = tk.BooleanVar(value=False)
recursive_var = tk.BooleanVar(value=True)
resample_var = tk.StringVar(value="bicubic")
suffix_var = tk.StringVar()

scale_var.trace_add("write", clear_preset_on_manual_scale)

config = load_config()
source_var.set(config.get("source", ""))
dest_var.set(config.get("destination", ""))
scale_var.set(config.get("scale", 50))
overwrite_var.set(config.get("overwrite", False))
recursive_var.set(config.get("recursive", True))
resample_var.set(config.get("resample", "bicubic"))
suffix_var.set(config.get("suffix", ""))

ttk.Label(root, text="Source folder").grid(row=0, column=0, sticky="w", **padding)
ttk.Entry(root, textvariable=source_var).grid(row=0, column=1, sticky="ew", **padding)
ttk.Button(root, text="Browse", command=choose_source).grid(row=0, column=2, **padding)

ttk.Label(root, text="Destination folder").grid(row=1, column=0, sticky="w", **padding)
ttk.Entry(root, textvariable=dest_var).grid(row=1, column=1, sticky="ew", **padding)
ttk.Button(root, text="Browse", command=choose_destination).grid(row=1, column=2, **padding)

ttk.Label(root, text="Scale (%)").grid(row=2, column=0, sticky="w", **padding)
ttk.Spinbox(root, from_=1, to=100, textvariable=scale_var, width=6).grid(
    row=2, column=1, sticky="w", **padding
)

preset_box = ttk.Combobox(
    root,
    textvariable=preset_var,
    values=["25", "50", "75", "100"],
    state="readonly",
    width=6,
)
preset_box.grid(row=2, column=1, sticky="e", **padding)
preset_box.bind("<<ComboboxSelected>>", apply_preset)

ttk.Label(root, text="Resampling").grid(row=3, column=0, sticky="w", **padding)
ttk.Combobox(
    root,
    textvariable=resample_var,
    values=["nearest", "bilinear", "bicubic"],
    state="readonly",
    width=12,
).grid(row=3, column=1, sticky="w", **padding)

ttk.Label(root, text="Filename suffix").grid(row=4, column=0, sticky="w", **padding)
ttk.Entry(root, textvariable=suffix_var, width=20).grid(
    row=4, column=1, sticky="w", **padding
)

ttk.Checkbutton(
    root, text="Recursive (include subfolders)", variable=recursive_var
).grid(row=5, column=1, sticky="w", **padding)

ttk.Checkbutton(
    root, text="Overwrite existing files", variable=overwrite_var
).grid(row=6, column=1, sticky="w", **padding)

progress = ttk.Progressbar(root, length=300, mode="determinate")
progress.grid(row=7, column=0, columnspan=3, padx=10, pady=(10, 5))

ttk.Button(root, text="Run", command=on_run).grid(row=8, column=1, pady=10)

root.mainloop()
