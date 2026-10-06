# Pose Prompt Creator

A cross-platform desktop GUI application designed for AI image prompt authoring. It allows creators to browse reference poses, inspect detailed descriptive prompts, and dynamically combine them with customizable prompt modifiers.

---

> [!CAUTION]
> ### ⚠️ Responsible Use & Ethical Disclaimer
> **DO NOT USE WITH REAL PERSONS.**
>
> This tool and its associated prompts, presets, and options are intended **strictly for fictional, synthetic, or AI-generated characters and digital artwork**.
>
> - **Never use this software to generate, edit, depict, or manipulate images of real, living individuals or non-consenting persons.**
> - **Strictly prohibited** for deepfakes, non-consensual imagery (NCII), impersonation, defamation, harassment, or any depiction of minors.
> - Users are solely responsible for adhering to applicable laws, ethical standards, and the acceptable use policies of their image generation models/services.

---

## ✨ Features

- **🖼️ Visual Pose Gallery:** Browse reference poses in an interactive, responsive grid modal with thumbnail previews.
- **📝 Pre-Configured Pose Prompts:** Bundled with detailed descriptive prompts tailored for diffusion models (`pose_prompts.json`).
- **🎛️ Modular Prompt Modifiers:** Toggle customizable prompt additions (`extra_options.json`) that automatically prepend to the beginning or append to the end of the prompt.
- **📋 One-Click Copy:** Copy the complete assembled prompt directly to your clipboard for instant use in ComfyUI, Automatic1111, Forge, Flux, or other image generation pipelines.
- **📊 Real-Time Stats:** Live word and character counters update as you select poses and toggles.
- **🖥️ Cross-Platform:** Runs seamlessly on **Windows**, **macOS**, and **Linux**.

---

## 📁 Repository Structure

```text
PosePrompt/
├── images/                 # Reference pose images (1.png, 2.png, ...)
├── extra_options.json      # Customizable prompt modifiers (prepends/appends)
├── pose_prompts.json       # Base prompt mappings for reference poses
├── pose_prompt_gui.py      # Main desktop GUI application (Tkinter + Pillow)
├── requirements.txt        # Python package dependencies
└── README.md               # Project documentation
```

---

## 🚀 Getting Started

### Prerequisites

- **Python 3.10+**
- Standard Tkinter support:
  - **Windows & macOS:** Tkinter is bundled with the standard Python installer.
  - **Linux (Debian/Ubuntu):** Install Tkinter via apt:
    ```bash
    sudo apt update && sudo apt install python3-tk
    ```

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/hasaranga/pose-prompts.git
   cd pose-prompts
   ```

2. **(Optional) Create and activate a virtual environment:**
   ```bash
   # Windows (PowerShell)
   python -m venv venv
   .\venv\Scripts\Activate.ps1

   # Linux / macOS
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

---

## 💻 Usage

Launch the GUI application by running:

```bash
python pose_prompt_gui.py
```

### Workflow:
1. Click **"🖼️ Select Pose"** to open the pose picker dialog.
2. Select any pose thumbnail to load its reference preview and base prompt description.
3. Check any desired options in the **"Extra Options"** checklist to prepend or append specific details.
4. Click **"📋 Copy to Clipboard"** and paste directly into your image generation interface.

---

## ⚙️ Customization

### Adding or Editing Poses
Add your image file (e.g. `81.png`) into the `images/` directory and add the corresponding prompt entry in `pose_prompts.json`:
```json
{
  "81.png": "detailed description of the pose..."
}
```

### Adding Extra Options
Edit `extra_options.json` to configure custom modifiers. Each modifier can be positioned at the `top` (prepended) or `bottom` (appended) of the base prompt:
```json
{
  "cinematic lighting": {
    "append": "bottom",
    "text": "cinematic dramatic volumetric lighting."
  },
  "masterpiece quality": {
    "append": "top",
    "text": "masterpiece, best quality, highly detailed."
  }
}
```

---

## 📄 License

Distributed under the MIT License.