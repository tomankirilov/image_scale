import json
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image

# ------------------------------
# Config loading/saving
# ------------------------------

CONFIG_FILE = Path(__file__).parent / "config.json"

def load_settings():
    """Attempt to load previous config, fallback to defaults if something goes wrong."""
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as conf_file:
                return json.load(conf_file)
        except Exception as err:
            # Might just be corrupt or half-written
            print("Failed to load config:", err)
    return {}

def save_settings():
    # Grabbing current UI values for persistence
    config_data = {
        "source": source_path.get(),
        "destination": dest_path.get(),
        "scale": scale_input.get(),
        "overwrite": overwrite_flag.get(),
        "resample": resample_choice.get(),
        "suffix": suffix_text.get(),
        "recursive": include_subdirs.get(),
    }

    with open(CONFIG_FILE, "w", encoding="utf-8") as out_file:
        json.dump(config_data, out_file, indent=2)


# ------------------------------
# Some global constants
# ------------------------------

RESAMPLING_OPTIONS = {
    "nearest": Image.NEAREST,
    "bilinear": Image.BILINEAR,
    "bicubic": Image.BICUBIC
}

IMAGE_EXTENSIONS = (".png", ".jpg", ".jpeg", ".tga")  # Might add more later


# ------------------------------
# UI helper functions
# ------------------------------

def browse_source():
    selected = filedialog.askdirectory()
    if selected:
        source_path.set(selected)

def browse_destination():
    selected = filedialog.askdirectory()
    if selected:
        dest_path.set(selected)

def apply_scale_from_preset(_=None):
    val = preset_option.get()
    if val.isdigit():
        scale_input.set(int(val))  # Setting directly from combo

def wipe_preset_if_manual(*_):  # Tkinter sends args we ignore
    preset_option.set("")  # Reset the dropdown if user manually changes scale


# ------------------------------
# Main operation
# ------------------------------

def run_scaling():
    save_settings()  # First, persist current config

    src_dir = Path(source_path.get())
    dst_dir = Path(dest_path.get())
    scale_factor = scale_input.get() / 100.0  # convert to 0-1
    allow_overwrite = overwrite_flag.get()
    is_recursive = include_subdirs.get()
    chosen_resample = RESAMPLING_OPTIONS[resample_choice.get()]
    suffix = suffix_text.get().strip()

    # Sanity checks
    if not src_dir.is_dir():
        messagebox.showerror("Error", "Source folder doesn't exist.")
        return
    if not dst_dir.is_dir():
        messagebox.showerror("Error", "Destination folder doesn't exist.")
        return
    if src_dir.resolve() == dst_dir.resolve():
        messagebox.showerror("Error", "Can't use the same folder for input and output.")
        return
    if scale_factor <= 0:
        messagebox.showerror("Error", "Scale must be more than 0%.")
        return

    # Gather images
    if is_recursive:
        image_files = [f for f in src_dir.rglob("*") if f.suffix.lower() in IMAGE_EXTENSIONS and f.is_file()]
    else:
        image_files = [f for f in src_dir.iterdir() if f.suffix.lower() in IMAGE_EXTENSIONS and f.is_file()]

    if not image_files:
        messagebox.showinfo("Info", "No images found.")
        return

    progress_bar["maximum"] = len(image_files)
    progress_bar["value"] = 0
    root.update_idletasks()

    total_ok = total_skipped = total_failed = 0

    for img_file in image_files:
        try:
            if is_recursive:
                rel_path = img_file.relative_to(src_dir)
                output_dir = dst_dir / rel_path.parent
            else:
                output_dir = dst_dir

            output_dir.mkdir(parents=True, exist_ok=True)

            output_filename = f"{img_file.stem}{suffix}{img_file.suffix}" if suffix else img_file.name
            target_path = output_dir / output_filename

            if target_path.exists() and not allow_overwrite:
                total_skipped += 1
            else:
                with Image.open(img_file) as im:
                    new_w = max(1, int(im.width * scale_factor))
                    new_h = max(1, int(im.height * scale_factor))
                    resized = im.resize((new_w, new_h), resample=chosen_resample)

                    # Slightly conservative save settings for JPEG
                    save_opts = {}
                    if im.format == "JPEG":
                        save_opts["quality"] = 95
                        save_opts["subsampling"] = 0

                    resized.save(target_path, format=im.format, **save_opts)
                    total_ok += 1

        except Exception as problem:
            # Would be better to log this somewhere
            total_failed += 1

        progress_bar["value"] += 1
        root.update_idletasks()

    # Wrap it up
    messagebox.showinfo("Done", f"Processed: {total_ok}\nSkipped: {total_skipped}\nErrors: {total_failed}")


# ------------------------------
# UI creation
# ------------------------------

root = tk.Tk()
root.title("Image Scaler")
root.resizable(False, False)

padding_opts = {"padx": 10, "pady": 5}

# Some basic layout control
root.columnconfigure(0, weight=0)
root.columnconfigure(1, weight=1)

# UI state variables
source_path = tk.StringVar()
dest_path = tk.StringVar()
scale_input = tk.IntVar(value=50)
preset_option = tk.StringVar()
overwrite_flag = tk.BooleanVar(value=False)
include_subdirs = tk.BooleanVar(value=True)
resample_choice = tk.StringVar(value="bicubic")
suffix_text = tk.StringVar()

scale_input.trace_add("write", wipe_preset_if_manual)

# Try loading settings from last time
prev_config = load_settings()
source_path.set(prev_config.get("source", ""))
dest_path.set(prev_config.get("destination", ""))
scale_input.set(prev_config.get("scale", 50))
overwrite_flag.set(prev_config.get("overwrite", False))
include_subdirs.set(prev_config.get("recursive", True))
resample_choice.set(prev_config.get("resample", "bicubic"))
suffix_text.set(prev_config.get("suffix", ""))

# Building the actual UI
ttk.Label(root, text="Source folder").grid(row=0, column=0, sticky="w", **padding_opts)
ttk.Entry(root, textvariable=source_path).grid(row=0, column=1, sticky="ew", **padding_opts)
ttk.Button(root, text="Browse", command=browse_source).grid(row=0, column=2, **padding_opts)

ttk.Label(root, text="Destination folder").grid(row=1, column=0, sticky="w", **padding_opts)
ttk.Entry(root, textvariable=dest_path).grid(row=1, column=1, sticky="ew", **padding_opts)
ttk.Button(root, text="Browse", command=browse_destination).grid(row=1, column=2, **padding_opts)

ttk.Label(root, text="Scale (%)").grid(row=2, column=0, sticky="w", **padding_opts)
ttk.Spinbox(root, from_=1, to=100, textvariable=scale_input, width=6).grid(
    row=2, column=1, sticky="w", **padding_opts
)

preset_combo = ttk.Combobox(
    root,
    textvariable=preset_option,
    values=["25", "50", "75", "100"],
    state="readonly",
    width=6,
)
preset_combo.grid(row=2, column=1, sticky="e", **padding_opts)
preset_combo.bind("<<ComboboxSelected>>", apply_scale_from_preset)

ttk.Label(root, text="Resampling").grid(row=3, column=0, sticky="w", **padding_opts)
ttk.Combobox(
    root,
    textvariable=resample_choice,
    values=list(RESAMPLING_OPTIONS.keys()),
    state="readonly",
    width=12,
).grid(row=3, column=1, sticky="w", **padding_opts)

ttk.Label(root, text="Filename suffix").grid(row=4, column=0, sticky="w", **padding_opts)
ttk.Entry(root, textvariable=suffix_text, width=20).grid(row=4, column=1, sticky="w", **padding_opts)

ttk.Checkbutton(root, text="Recursive (include subfolders)", variable=include_subdirs).grid(
    row=5, column=1, sticky="w", **padding_opts
)
ttk.Checkbutton(root, text="Overwrite existing files", variable=overwrite_flag).grid(
    row=6, column=1, sticky="w", **padding_opts
)

progress_bar = ttk.Progressbar(root, length=300, mode="determinate")
progress_bar.grid(row=7, column=0, columnspan=3, padx=10, pady=(10, 5))

ttk.Button(root, text="Run", command=run_scaling).grid(row=8, column=1, pady=10)

root.mainloop()
