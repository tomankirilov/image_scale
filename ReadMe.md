# Image Scaler Tool

<img width="400" height="325" alt="image" src="https://github.com/user-attachments/assets/1a930afc-7da9-4e85-b8e2-623cea46442e" />


A small Windows desktop utility for batch scaling images (PNG / JPG / TGA).
## Features:
- Recursive or flat folder processing
- Scale presets + custom scale
- Resampling modes (nearest / bilinear / bicubic)
- Optional filename suffix
- Overwrite control
- Progress bar
- Persistent settings
- Portable one-folder EXE build
---
## Requirements
- Windows
- Python 3.10+
## Edit the app:
- **Create virtual environment**
  py -m venv venv
- **Activate venv**
    - venv\Scripts\activate
- **Install dependencies**
    - pip install -r requirements.txt
- **Run the app (development)**
    - python src/app.py
- **Build the EXE (one-folder, portable)**
    - pyinstaller --windowed src/app.py
