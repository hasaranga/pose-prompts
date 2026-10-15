# Pose Prompt Creator

A cross-platform desktop GUI application designed for AI image prompt authoring. It allows creators to browse reference poses, inspect detailed descriptive prompts, and dynamically combine them with customizable prompt modifiers and advanced modular prompt building blocks.

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
- **🎛️ Modular Prompt Modifiers:** Quick-toggle checklist of common modifiers (`extra_options.json`) that prepend to the beginning or append to the end of the prompt.
- **⚡ Advanced Prompt Builder:** Visual block-based prompt composition (`advanced_prompt_builder.py`):
  - Pick items from a structured hierarchical menu (`prompt_menu.json`).
  - Items appear as visual chips: drag `⠿` to reorder, click to customize, or click `✕` to remove.
  - Interactive parameter slots (`#`) with multi-select (e.g. choose multiple body parts for a single coherent sentence) or single-select choices.
  - Automatically appends in real time to the main window's prompt description.
  - Save and load your custom prompt design layouts.
- **📋 One-Click Copy:** Copy the complete assembled prompt directly to your clipboard for instant use in ComfyUI, Automatic1111, Forge, Flux, or other image generation pipelines.
- **📊 Real-Time Stats:** Live word and character counters update dynamically as you select poses, toggles, or advanced chips.
- **🖥️ Cross-Platform:** Runs seamlessly on **Windows**, **macOS**, and **Linux**.

---

## 📁 Repository Structure

```text
pose-prompts/
├── images/                     # Reference pose images (1.png, 2.png, ...)
├── extra_options.json          # Quick-toggle prompt modifiers (prepends/appends)
├── pose_prompts.json           # Base prompt mappings for reference poses
├── pose_prompt_gui.py          # Main desktop GUI application (Tkinter + Pillow)
├── advanced_prompt_builder.py  # Advanced visual block prompt builder (Tkinter)
├── prompt_menu.json            # Hierarchical menu & template configuration for Advanced Builder
├── requirements.txt            # Python package dependencies (Pillow)
└── README.md                   # Project documentation
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

### Main Application

Launch the main GUI application:

```bash
python pose_prompt_gui.py
```

#### Workflow:
1. **Pick a Pose:** In the **"Selected Pose"** box on the left, click **"🖼️ Browse Poses"** to select a reference pose.
2. **Add Extra Options:** Toggle any options in the middle **"Extra Options"** checklist to prepend or append prompt modifiers.
3. **Use the Advanced Builder:** Click **"⚡ Advanced builder"** below the pose thumbnail to open the visual builder window. Select items from the menu (`＋ Add ▾`) to add blocks, reorder them, or customize their parameters. The output dynamically appends to the main prompt textbox.
4. **Copy & Generate:** Click **"📋 Copy to Clipboard"** and paste directly into your AI image generator.

---

### Standalone Advanced Prompt Builder

You can also run the Advanced Prompt Builder as an independent standalone tool:

```bash
python advanced_prompt_builder.py
```

In standalone mode, it includes its own prompt output textbox and clipboard copy button.

---

## ⚙️ Customization

### 1. Adding or Editing Poses (`pose_prompts.json`)

Add your image file (e.g. `85.png`) into the `images/` directory and map it in `pose_prompts.json`:

```json
{
  "85.png": "Change the pose of the woman to an upright standing posture with arms raised overhead..."
}
```

---

### 2. Adding Quick-Toggle Modifiers (`extra_options.json`)

Edit `extra_options.json` to add checkboxes to the middle column of the main GUI. Each entry can prepend to `"top"` or append to `"bottom"`:

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

### 3. Customizing the Advanced Prompt Builder (`prompt_menu.json`)

The Advanced Prompt Builder is fully configurable via `prompt_menu.json`. You can define categories, subcategories, plain phrases, and dynamic templates with parameter slots (`#`).

#### Menu Hierarchy
Menus are defined using nested `categories` and `items`:

```json
{
  "categories": [
    {
      "name": "My Custom Category",
      "categories": [
        {
          "name": "Subcategory",
          "items": [ ... ]
        }
      ],
      "items": [ ... ]
    }
  ]
}
```

#### A. Plain Phrases
Items without `#` in their `template` are added as instant phrases:

```json
{
  "label": "Soft window light",
  "template": "Soft natural window light creates even illumination.",
  "group": "lighting"
}
```
> [!TIP]
> The optional `"group"` attribute enforces mutual exclusion. If an item shares a `group` with another selected item (e.g., lighting styles or skin tones), selecting it automatically replaces the existing one.

#### B. Dynamic Templates with Parameter Slots (`#`)
When a `template` contains one or more `#` characters, clicking the menu item opens an interactive options window:

##### Example 1: Multi-Select with Reusable Lists
By default, slots allow choosing multiple values (`multi: true`). When the user picks multiple items (e.g., `face` and `hands`), they are joined into a natural sentence (`"face and hands"`):

```json
{
  "label": "Has goosebumps on #...",
  "template": "slight visible goosebumps on #.",
  "list": "body_parts"
}
```

##### Example 2: Single-Select with Inline Options
Set `"multi": false` when only one option should be chosen:

```json
{
  "label": "Entire body matches skin of #...",
  "template": "entire body should have same skin tone and texture as her #.",
  "slots": [
    {
      "options": ["face", "hands", "legs", "arms", "chest"],
      "multi": false
    }
  ]
}
```

##### Example 3: Multiple Slots in One Template
You can specify multiple `#` placeholders:

```json
{
  "label": "Hair color and style...",
  "template": "Her hair is # and worn #.",
  "slots": [
    {
      "options": ["black", "dark brown", "blonde", "red"],
      "multi": false
    },
    {
      "options": ["loose", "in a ponytail", "in a bun", "in braids"],
      "multi": false
    }
  ]
}
```

> [!NOTE]
> Menu items that open an options window automatically show an ellipsis (`...`) at the end of their label in the GUI.

#### C. Expanding Shared Lists (`lists`)
Define reusable option pools under the root `"lists"` key to reference across multiple items:

```json
{
  "lists": {
    "body_parts": [
      "face", "cheeks", "jawline", "neck", "shoulders",
      "collarbone", "chest", "breasts", "stomach", "tummy",
      "back", "arms", "hands", "hips", "thighs", "legs", "feet"
    ]
  }
}
```

#### D. Live Reloading
You can edit `prompt_menu.json` in any text editor and click **"Reload JSON"** in the Advanced Prompt Builder window to immediately apply changes without restarting the application.

---

## 📄 License

Distributed under the MIT License.