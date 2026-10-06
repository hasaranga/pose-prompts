import json
from pathlib import Path
import sys
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk


BASE_DIR = Path(__file__).parent.resolve()
IMAGES_DIR = BASE_DIR / "images"
PROMPTS_JSON = BASE_DIR / "pose_prompts.json"
OPTIONS_JSON = BASE_DIR / "extra_options.json"


def get_system_font_family() -> str:
    """Return the standard sans-serif UI font for the current OS."""
    if sys.platform == "darwin":
        return "Helvetica Neue"
    elif sys.platform.startswith("linux"):
        return "DejaVu Sans"
    return "Segoe UI"


FONT_FAMILY = get_system_font_family()


def natural_sort_key(filename: str):
    """Sort filenames with numeric stems in natural order (1.png before 10.png)."""
    stem = Path(filename).stem
    return int(stem) if stem.isdigit() else stem


def load_prompts() -> dict[str, str]:
    """Load prompts from pose_prompts.json."""
    if PROMPTS_JSON.exists():
        try:
            with open(PROMPTS_JSON, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Warning: Failed to load {PROMPTS_JSON.name}: {e}")
    return {}


def load_extra_options() -> dict[str, str]:
    """Load optional prompt suffixes from extra_options.json."""
    if OPTIONS_JSON.exists():
        try:
            with open(OPTIONS_JSON, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Warning: Failed to load {OPTIONS_JSON.name}: {e}")
    return {}


def center_window(window: tk.Tk | tk.Toplevel, width: int, height: int):
    """Position a window at the center of the display screen."""
    window.update_idletasks()
    sw = window.winfo_screenwidth()
    sh = window.winfo_screenheight()
    x = max(0, (sw - width) // 2)
    y = max(0, (sh - height) // 2)
    window.geometry(f"{width}x{height}+{x}+{y}")


def scroll_canvas(canvas: tk.Canvas, event):
    """Cross-platform mousewheel scrolling for Windows, Linux, and macOS."""
    if getattr(event, "num", None) == 4:
        canvas.yview_scroll(-2, "units")
    elif getattr(event, "num", None) == 5:
        canvas.yview_scroll(2, "units")
    elif getattr(event, "delta", 0):
        if sys.platform == "darwin":
            delta = int(-1 * event.delta)
        else:
            delta = int(-1 * (event.delta / 120))
        canvas.yview_scroll(delta, "units")


class PosePickerModal(tk.Toplevel):
    """Modal dialog displaying a scrollable grid of image thumbnails."""

    def __init__(self, parent, image_filenames: list[str], on_select_callback):
        super().__init__(parent)
        self.title("Select Pose Image")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self.image_filenames = image_filenames
        self.on_select_callback = on_select_callback
        self.thumbnail_images: dict[str, ImageTk.PhotoImage] = {}
        self.hovered_card: tk.Frame | None = None

        # Center modal on the display screen
        center_window(self, 760, 560)

        self._build_ui()
        self.bind("<MouseWheel>", self._on_mousewheel)
        self.bind("<Button-4>", lambda e: self.canvas.yview_scroll(-2, "units"))
        self.bind("<Button-5>", lambda e: self.canvas.yview_scroll(2, "units"))

    def _build_ui(self):
        # Header bar (no filter)
        header_frame = ttk.Frame(self, padding=(16, 12))
        header_frame.pack(fill=tk.X)

        title_lbl = ttk.Label(
            header_frame,
            text=f"Available Poses ({len(self.image_filenames)} total)",
            font=(FONT_FAMILY, 11, "bold"),
        )
        title_lbl.pack(side=tk.LEFT)

        inst_lbl = ttk.Label(
            header_frame,
            text="Click any thumbnail to select",
            font=(FONT_FAMILY, 9, "italic"),
            foreground="#666666",
        )
        inst_lbl.pack(side=tk.RIGHT)

        ttk.Separator(self, orient=tk.HORIZONTAL).pack(fill=tk.X)

        # Canvas with Scrollbar
        container = ttk.Frame(self)
        container.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        self.canvas = tk.Canvas(container, highlightthickness=0, bg="#f5f5f7")
        self.scrollbar = ttk.Scrollbar(
            container, orient=tk.VERTICAL, command=self.canvas.yview
        )
        self.scroll_frame = tk.Frame(self.canvas, bg="#f5f5f7")

        self.scroll_window = self.canvas.create_window(
            (0, 0), window=self.scroll_frame, anchor="nw"
        )

        self.scroll_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")),
        )
        self.canvas.bind("<Configure>", self._on_canvas_configure)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self._populate_grid()

    def _on_canvas_configure(self, event):
        self.canvas.itemconfig(self.scroll_window, width=event.width)

    def _on_mousewheel(self, event):
        scroll_canvas(self.canvas, event)

    def _set_card_state(self, card: tk.Frame, active: bool):
        bg_color = "#e3f2fd" if active else "#ffffff"
        relief = tk.SOLID if active else tk.RIDGE
        try:
            card.config(bg=bg_color, relief=relief)
            for child in card.winfo_children():
                child.config(bg=bg_color)
        except tk.TclError:
            pass

    def _on_card_enter(self, card: tk.Frame):
        if self.hovered_card and self.hovered_card != card:
            self._set_card_state(self.hovered_card, active=False)
        self.hovered_card = card
        self._set_card_state(card, active=True)

    def _on_card_leave(self, card: tk.Frame):
        # Check if cursor is still within the bounds of the card
        try:
            px = card.winfo_pointerx() - card.winfo_rootx()
            py = card.winfo_pointery() - card.winfo_rooty()
            if 0 <= px < card.winfo_width() and 0 <= py < card.winfo_height():
                return
        except tk.TclError:
            pass

        if self.hovered_card == card:
            self._set_card_state(card, active=False)
            self.hovered_card = None

    def _populate_grid(self):
        for child in self.scroll_frame.winfo_children():
            child.destroy()

        columns = 5

        for idx, fname in enumerate(self.image_filenames):
            r = idx // columns
            c = idx % columns

            card = tk.Frame(
                self.scroll_frame,
                bg="#ffffff",
                relief=tk.RIDGE,
                bd=1,
                padx=6,
                pady=6,
                cursor="hand2",
            )
            card.grid(row=r, column=c, padx=6, pady=6, sticky="nsew")

            photo = self._get_thumbnail(fname, (96, 96))
            if photo:
                img_lbl = tk.Label(
                    card, image=photo, bg="#ffffff", cursor="hand2"
                )
                img_lbl.image = photo  # keep reference
                img_lbl.pack()
            else:
                img_lbl = tk.Label(
                    card, text="[No Image]", bg="#ffffff", cursor="hand2"
                )
                img_lbl.pack(pady=20)

            text_lbl = tk.Label(
                card,
                text=fname,
                font=(FONT_FAMILY, 9, "bold"),
                bg="#ffffff",
                fg="#333333",
                cursor="hand2",
            )
            text_lbl.pack(pady=(4, 0))

            # Bind hover & click events on card and all child widgets
            for w in (card, img_lbl, text_lbl):
                w.bind("<Enter>", lambda e, c=card: self._on_card_enter(c))
                w.bind("<Leave>", lambda e, c=card: self._on_card_leave(c))
                w.bind("<Button-1>", lambda e, f=fname: self._select_and_close(f))

        for col in range(columns):
            self.scroll_frame.columnconfigure(col, weight=1)

    def _get_thumbnail(self, fname: str, size: tuple[int, int]) -> ImageTk.PhotoImage | None:
        if fname in self.thumbnail_images:
            return self.thumbnail_images[fname]

        img_path = IMAGES_DIR / fname
        if not img_path.exists():
            return None

        try:
            im = Image.open(img_path)
            im.thumbnail(size, Image.LANCZOS)
            photo = ImageTk.PhotoImage(im)
            self.thumbnail_images[fname] = photo
            return photo
        except Exception as e:
            print(f"Error loading image {fname}: {e}")
            return None

    def _select_and_close(self, fname: str):
        self.on_select_callback(fname)
        self.destroy()


class PosePromptGUI:
    """Main application window for selecting poses and generating prompts."""

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Pose Prompt Creator")
        self.root.minsize(980, 520)
        self.root.resizable(True, True)
        center_window(self.root, 1180, 620)

        # Apply ttk theme (native aqua on macOS, vista/clam on Windows/Linux)
        self.style = ttk.Style()
        for theme in ("aqua", "vista", "clam", "default"):
            if theme in self.style.theme_names():
                self.style.theme_use(theme)
                break

        # Load data
        self.prompts = load_prompts()
        self.extra_options = load_extra_options()
        self.image_filenames = self._get_sorted_images()

        self.selected_image: str | None = None
        self.current_preview_photo: ImageTk.PhotoImage | None = None
        self.option_vars: dict[str, tk.BooleanVar] = {}
        self._copy_timer = None

        self._build_ui()

    def _get_sorted_images(self) -> list[str]:
        """Return image filenames ordered by prompts list or numeric filename."""
        if self.prompts:
            ordered = [f for f in self.prompts.keys() if (IMAGES_DIR / f).exists()]
            if ordered:
                return ordered

        if IMAGES_DIR.exists():
            files = [
                f.name
                for f in IMAGES_DIR.glob("*")
                if f.suffix.lower() in (".png", ".jpg", ".jpeg", ".webp")
            ]
            files.sort(key=natural_sort_key)
            return files

        return []

    def _build_ui(self):
        # Top toolbar
        top_bar = ttk.Frame(self.root, padding=(16, 12))
        top_bar.pack(fill=tk.X)

        self.btn_select_pose = ttk.Button(
            top_bar,
            text="🖼️ Select Pose",
            command=self.open_pose_picker,
        )
        self.btn_select_pose.pack(side=tk.LEFT)

        self.lbl_selected_title = ttk.Label(
            top_bar,
            text="No pose selected. Click 'Select Pose' to pick an image.",
            font=(FONT_FAMILY, 10, "italic"),
            foreground="#555555",
        )
        self.lbl_selected_title.pack(side=tk.LEFT, padx=(16, 0))

        ttk.Separator(self.root, orient=tk.HORIZONTAL).pack(fill=tk.X)

        # Main content area (Three columns)
        content_pane = ttk.Frame(self.root, padding=16)
        content_pane.pack(fill=tk.BOTH, expand=True)

        content_pane.columnconfigure(0, weight=0, minsize=220)
        content_pane.columnconfigure(1, weight=1, minsize=300)
        content_pane.columnconfigure(2, weight=2, minsize=400)
        content_pane.rowconfigure(0, weight=1)

        # Column 0: Thumbnail preview (Selected Pose)
        col_preview = ttk.Frame(content_pane)
        col_preview.grid(row=0, column=0, sticky="nsew", padx=(0, 16))
        col_preview.columnconfigure(0, weight=1)

        preview_group = ttk.LabelFrame(col_preview, text="Selected Pose", padding=12)
        preview_group.pack(fill=tk.X)
        preview_group.columnconfigure(0, weight=1)

        canvas_container = tk.Frame(preview_group, bg="#eceff1")
        canvas_container.pack(pady=4)

        self.canvas_preview = tk.Canvas(
            canvas_container,
            width=190,
            height=190,
            bg="#eceff1",
            highlightthickness=1,
            highlightbackground="#cfd8dc",
        )
        self.canvas_preview.pack()

        # Placeholder text in canvas
        self.placeholder_text_id = self.canvas_preview.create_text(
            95,
            95,
            text="[No Image Selected]",
            font=(FONT_FAMILY, 9),
            fill="#78909c",
            justify=tk.CENTER,
        )

        # Close button directly on top-right of thumbnail preview
        self.btn_close_canvas = tk.Button(
            self.canvas_preview,
            text="✕",
            font=(FONT_FAMILY, 9, "bold"),
            bg="#e53935",
            fg="#ffffff",
            activebackground="#c62828",
            activeforeground="#ffffff",
            bd=0,
            padx=5,
            pady=1,
            cursor="hand2",
            relief=tk.FLAT,
            command=self.clear_selected_pose,
        )
        # Initially hidden when no image is selected
        self.btn_close_canvas.place_forget()

        self.lbl_preview_fname = ttk.Label(
            preview_group,
            text="",
            font=(FONT_FAMILY, 9, "bold"),
            anchor="center",
            wraplength=190,
        )
        self.lbl_preview_fname.pack(fill=tk.X, pady=(6, 4))

        self.btn_clear_pose = ttk.Button(
            preview_group,
            text="✕ Remove Selection",
            command=self.clear_selected_pose,
            state=tk.DISABLED,
        )
        self.btn_clear_pose.pack(fill=tk.X, pady=(2, 6))

        self.btn_browse_pose = ttk.Button(
            preview_group,
            text="🖼️ Browse Poses",
            command=self.open_pose_picker,
        )
        self.btn_browse_pose.pack(fill=tk.X, pady=(2, 0))

        # Column 1: Extra Options (Middle column, same height as Prompt Description)
        col_options = ttk.Frame(content_pane)
        col_options.grid(row=0, column=1, sticky="nsew", padx=(0, 16))
        col_options.columnconfigure(0, weight=1)
        col_options.rowconfigure(1, weight=1)

        header_options = ttk.Frame(col_options)
        header_options.grid(row=0, column=0, sticky="ew", pady=(0, 6))

        lbl_options_heading = ttk.Label(
            header_options,
            text="Extra Options:",
            font=(FONT_FAMILY, 10, "bold"),
        )
        lbl_options_heading.pack(side=tk.LEFT)

        # Scrollable checklist container matching prompt textbox height
        options_container = tk.Frame(col_options, relief=tk.SOLID, bd=1, bg="#ffffff")
        options_container.grid(row=1, column=0, sticky="nsew")

        self.canvas_options = tk.Canvas(
            options_container,
            highlightthickness=0,
            bg="#ffffff",
        )
        self.scrollbar_options = ttk.Scrollbar(
            options_container,
            orient=tk.VERTICAL,
            command=self.canvas_options.yview,
        )
        self.options_inner_frame = tk.Frame(self.canvas_options, bg="#ffffff")

        self.options_scroll_window = self.canvas_options.create_window(
            (0, 0), window=self.options_inner_frame, anchor="nw"
        )

        self.options_inner_frame.bind(
            "<Configure>",
            lambda e: self.canvas_options.configure(
                scrollregion=self.canvas_options.bbox("all")
            ),
        )
        self.canvas_options.bind(
            "<Configure>",
            lambda e: self.canvas_options.itemconfig(
                self.options_scroll_window, width=e.width
            ),
        )
        self.canvas_options.configure(yscrollcommand=self.scrollbar_options.set)

        self.scrollbar_options.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas_options.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        for w in (self.canvas_options, self.options_inner_frame):
            w.bind("<MouseWheel>", self._on_options_mousewheel)
            w.bind("<Button-4>", lambda e: self.canvas_options.yview_scroll(-2, "units"))
            w.bind("<Button-5>", lambda e: self.canvas_options.yview_scroll(2, "units"))

        if self.extra_options:
            for opt_key in self.extra_options.keys():
                var = tk.BooleanVar(value=False)
                self.option_vars[opt_key] = var
                cb = ttk.Checkbutton(
                    self.options_inner_frame,
                    text=opt_key,
                    variable=var,
                    command=self.update_prompt_text,
                )
                cb.pack(anchor="w", pady=3, fill=tk.X, padx=8)
                cb.bind("<MouseWheel>", self._on_options_mousewheel)
                cb.bind("<Button-4>", lambda e: self.canvas_options.yview_scroll(-2, "units"))
                cb.bind("<Button-5>", lambda e: self.canvas_options.yview_scroll(2, "units"))
        else:
            no_opt_lbl = ttk.Label(
                self.options_inner_frame,
                text="No extra options found in extra_options.json.",
                font=(FONT_FAMILY, 9, "italic"),
                foreground="#777777",
            )
            no_opt_lbl.pack(anchor="w", padx=8, pady=8)

        # Bottom Bar for Extra Options: Deselect all & count
        bottom_options = ttk.Frame(col_options, padding=(0, 10, 0, 0))
        bottom_options.grid(row=2, column=0, sticky="ew")

        self.btn_deselect_all = ttk.Button(
            bottom_options,
            text="Deselect All",
            command=self.deselect_all_options,
        )
        self.btn_deselect_all.pack(side=tk.LEFT)

        self.lbl_selected_options_count = ttk.Label(
            bottom_options,
            text="0 selected",
            font=(FONT_FAMILY, 9),
            foreground="#666666",
        )
        self.lbl_selected_options_count.pack(side=tk.RIGHT)

        # Column 2: Prompt Description (Right column)
        col_prompt = ttk.Frame(content_pane)
        col_prompt.grid(row=0, column=2, sticky="nsew")
        col_prompt.columnconfigure(0, weight=1)
        col_prompt.rowconfigure(1, weight=1)

        header_prompt = ttk.Frame(col_prompt)
        header_prompt.grid(row=0, column=0, sticky="ew", pady=(0, 6))

        lbl_prompt_heading = ttk.Label(
            header_prompt,
            text="Prompt Description:",
            font=(FONT_FAMILY, 10, "bold"),
        )
        lbl_prompt_heading.pack(side=tk.LEFT)

        # Multiline readonly Textbox with scrollbar
        text_container = ttk.Frame(col_prompt)
        text_container.grid(row=1, column=0, sticky="nsew")

        self.txt_prompt = tk.Text(
            text_container,
            wrap=tk.WORD,
            font=(FONT_FAMILY, 10),
            bg="#ffffff",
            fg="#1a1a1a",
            relief=tk.SOLID,
            bd=1,
            padx=10,
            pady=10,
            state=tk.DISABLED,
        )
        scrollbar_prompt = ttk.Scrollbar(
            text_container, orient=tk.VERTICAL, command=self.txt_prompt.yview
        )
        self.txt_prompt.configure(yscrollcommand=scrollbar_prompt.set)

        scrollbar_prompt.pack(side=tk.RIGHT, fill=tk.Y)
        self.txt_prompt.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Bottom Bar: Copy button & status feedback
        bottom_bar = ttk.Frame(col_prompt, padding=(0, 10, 0, 0))
        bottom_bar.grid(row=2, column=0, sticky="ew")

        self.btn_copy = ttk.Button(
            bottom_bar,
            text="📋 Copy to Clipboard",
            command=self.copy_prompt_to_clipboard,
        )
        self.btn_copy.pack(side=tk.LEFT)

        self.lbl_status = tk.Label(
            bottom_bar,
            text="",
            font=(FONT_FAMILY, 9, "bold"),
            fg="#2e7d32",
        )
        self.lbl_status.pack(side=tk.LEFT, padx=(12, 0))

        self.lbl_stats = ttk.Label(
            bottom_bar,
            text="",
            font=(FONT_FAMILY, 9),
            foreground="#666666",
        )
        self.lbl_stats.pack(side=tk.RIGHT)

    def _on_options_mousewheel(self, event):
        scroll_canvas(self.canvas_options, event)

    def deselect_all_options(self):
        """Uncheck all extra options and update prompt text."""
        for var in self.option_vars.values():
            var.set(False)
        self.update_prompt_text()

    def clear_selected_pose(self):
        """Remove current pose selection, clear preview, and update prompt text."""
        self.selected_image = None
        self.current_preview_photo = None

        self.canvas_preview.delete("all")
        self.btn_close_canvas.place_forget()
        cx = self.canvas_preview.winfo_width() // 2 or 95
        cy = self.canvas_preview.winfo_height() // 2 or 95
        self.placeholder_text_id = self.canvas_preview.create_text(
            cx,
            cy,
            text="[No Image Selected]",
            font=(FONT_FAMILY, 9),
            fill="#78909c",
            justify=tk.CENTER,
        )

        self.lbl_preview_fname.config(text="")
        self.lbl_selected_title.config(
            text="No pose selected. Click 'Select Pose' to pick an image.",
            font=(FONT_FAMILY, 10, "italic"),
            foreground="#555555",
        )
        self.btn_clear_pose.config(state=tk.DISABLED)

        self.update_prompt_text()

    def open_pose_picker(self):
        """Open modal window to browse and select pose thumbnail."""
        if not self.image_filenames:
            messagebox.showwarning(
                "No Images",
                f"No images found in {IMAGES_DIR}. Please check the images folder.",
            )
            return

        PosePickerModal(
            parent=self.root,
            image_filenames=self.image_filenames,
            on_select_callback=self.on_pose_selected,
        )

    def on_pose_selected(self, fname: str):
        """Callback when user picks an image from modal."""
        self.selected_image = fname
        self.lbl_selected_title.config(
            text=f"Selected: {fname}",
            font=(FONT_FAMILY, 10, "bold"),
            foreground="#1565c0",
        )
        self.lbl_preview_fname.config(text=fname)
        self.btn_clear_pose.config(state=tk.NORMAL)

        # Update thumbnail preview
        img_path = IMAGES_DIR / fname
        if img_path.exists():
            try:
                im = Image.open(img_path)
                im.thumbnail((186, 186), Image.LANCZOS)
                self.current_preview_photo = ImageTk.PhotoImage(im)

                self.canvas_preview.delete("all")
                cx = self.canvas_preview.winfo_width() // 2 or 95
                cy = self.canvas_preview.winfo_height() // 2 or 95
                self.canvas_preview.create_image(
                    cx, cy, image=self.current_preview_photo, anchor=tk.CENTER
                )
                # Show close button at top-right corner of preview
                self.btn_close_canvas.place(relx=1.0, rely=0.0, anchor="ne", x=-4, y=4)
                self.btn_close_canvas.lift()
            except Exception as e:
                print(f"Error updating preview: {e}")

        self.update_prompt_text()

    def update_prompt_text(self):
        """Combine base prompt with selected extra options and update textbox.

        If append option is 'top': text is added to top of prompt with space at end of text.
        If append option is 'bottom': text is added to end of prompt with space only at start of text.
        """
        top_chunks = []
        bottom_chunks = []

        for opt_key, var in self.option_vars.items():
            if var.get():
                opt_info = self.extra_options.get(opt_key, {})
                if isinstance(opt_info, dict):
                    append_pos = str(opt_info.get("append", "bottom")).strip().lower()
                    text = str(opt_info.get("text", "")).strip()
                else:
                    append_pos = "bottom"
                    text = str(opt_info).strip()

                if text:
                    if append_pos == "top":
                        # 'top' will add space into end of text
                        top_chunks.append(text + " ")
                    else:
                        # 'bottom' will add space only to start of the text. not the end.
                        bottom_chunks.append(" " + text)

        top_str = "".join(top_chunks)
        bottom_str = "".join(bottom_chunks)

        base_prompt = ""
        if self.selected_image:
            base_prompt = self.prompts.get(
                self.selected_image,
                f"No prompt description available for {self.selected_image}.",
            ).strip()

        parts = []
        if top_str:
            parts.append(top_str)

        if base_prompt:
            parts.append(base_prompt)

        if bottom_str:
            # If nothing preceded bottom_str, strip leading space so text doesn't start with space
            if not top_str and not base_prompt:
                parts.append(bottom_str.lstrip())
            # If top_str was added but no base_prompt, top_str already ends with " "
            elif top_str and not base_prompt:
                parts.append(bottom_str.lstrip())
            else:
                parts.append(bottom_str)

        final_prompt = "".join(parts)
        self._set_textbox_content(final_prompt)

        words = len(final_prompt.split()) if final_prompt else 0
        chars = len(final_prompt)
        self.lbl_stats.config(text=f"{words} words | {chars} chars")

        selected_count = sum(1 for v in self.option_vars.values() if v.get())
        if hasattr(self, "lbl_selected_options_count"):
            self.lbl_selected_options_count.config(text=f"{selected_count} selected")

    def _set_textbox_content(self, text: str):
        """Safely set readonly multiline textbox content."""
        self.txt_prompt.config(state=tk.NORMAL)
        self.txt_prompt.delete("1.0", tk.END)
        self.txt_prompt.insert(tk.END, text)
        self.txt_prompt.config(state=tk.DISABLED)

    def copy_prompt_to_clipboard(self):
        """Copy current textbox prompt to the system clipboard."""
        text = self.txt_prompt.get("1.0", "end-1c")
        if not text.strip():
            messagebox.showinfo(
                "Copy Prompt",
                "No prompt text to copy. Please select a pose or options first.",
            )
            return

        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        self.root.update()

        self.lbl_status.config(text="✓ Copied to clipboard!")
        if self._copy_timer:
            self.root.after_cancel(self._copy_timer)
        self._copy_timer = self.root.after(
            2200, lambda: self.lbl_status.config(text="")
        )


def main():
    root = tk.Tk()
    app = PosePromptGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
