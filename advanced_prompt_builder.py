#!/usr/bin/env python3
"""Advanced Prompt Builder (tkinter, standard library only).

Click "+ Add" (or right-click the panel) to open a popup menu, pick items, and the
chosen items appear as removable rectangles. Items whose template contains '#'
ask you to choose values that replace the '#'.
Menu content lives in prompt_menu.json (same folder, or pass a path as argument).
"""
import json
import sys
import tkinter as tk
from pathlib import Path
from tkinter import ttk, messagebox, filedialog

CONFIG = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).with_name("prompt_menu.json")


def join_values(vals):
    if len(vals) <= 1:
        return "".join(vals)
    return ", ".join(vals[:-1]) + " and " + vals[-1]


def norm_slot(spec, lists):
    if isinstance(spec, str):
        spec = {"list": spec}
    elif isinstance(spec, list):
        spec = {"options": spec}
    opts = spec.get("options") or lists.get(spec.get("list"), [])
    return {"options": list(opts), "multi": spec.get("multi", True)}


class Item:
    def __init__(self, path, spec, lists):
        self.path = path
        self.template = spec["template"]
        self.label = spec.get("label") or self.template
        self.group = spec.get("group")
        n = self.template.count("#")
        raw = spec.get("slots")
        if raw is None:
            raw = [spec.get("list") or spec.get("options") or []] * n
        self.slots = [norm_slot(s, lists) for s in raw][:n]
        while len(self.slots) < n:
            self.slots.append(self.slots[-1] if self.slots else {"options": [], "multi": True})
        if self.slots and not (self.label.endswith("...") or self.label.endswith("…")):
            self.label = self.label + "..."


class Chip:
    def __init__(self, item):
        self.item = item
        self.values = [[] for _ in item.slots]

    @property
    def complete(self):
        return all(self.values)

    def render(self, missing="[…]"):
        parts = self.item.template.split("#")
        out = parts[0]
        for i, tail in enumerate(parts[1:]):
            out += (join_values(self.values[i]) or missing) + tail
        return out


class AdvancedPromptBuilderCore:
    def setup_ui(self, on_change=None, show_textbox=True, config_path=None):
        self.config_path = Path(config_path) if config_path else CONFIG
        self.on_change = on_change
        self.show_textbox = show_textbox

        self.title("Advanced Prompt Builder")
        self.geometry("800x760" if show_textbox else "800x460")
        self.chips, self.labels, self.frames = [], [], []
        self.items = {}
        self.drag_chip = None
        self.indicator = None
        self.prefix = self.suffix = ""
        self.menu = tk.Menu(self, tearoff=0)

        top = ttk.Frame(self, padding=(10, 10, 10, 0))
        top.pack(fill="x")
        self.add_btn = ttk.Button(top, text="＋ Add ▾", command=self.show_menu_at_button)
        self.add_btn.pack(side="left")
        ttk.Button(top, text="Clear all", command=self.clear).pack(side="left", padx=6)
        ttk.Button(top, text="Reload JSON", command=self.load).pack(side="left")
        ttk.Button(top, text="Save design…", command=self.save_design).pack(side="left", padx=(12, 0))
        ttk.Button(top, text="Load design…", command=self.load_design).pack(side="left", padx=6)
        self.bind("<Control-s>", lambda e: self.save_design())
        self.bind("<Control-o>", lambda e: self.load_design())
        self.status = ttk.Label(top, text="Drag ⠿ to reorder · click a rectangle to edit · ✕ removes it")
        self.status.pack(side="left", padx=10)

        panel = ttk.LabelFrame(self, text="Selected", padding=4)
        panel.pack(fill="both", expand=True, padx=10, pady=8)
        self.canvas = tk.Canvas(panel, highlightthickness=0, height=300)
        sb = ttk.Scrollbar(panel, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)
        self.inner = tk.Frame(self.canvas)
        self.win = self.canvas.create_window((0, 0), window=self.inner, anchor="nw")
        self.inner.bind("<Configure>", lambda e: self.update_scrollregion())
        self.canvas.bind("<Configure>", self.on_canvas_resize)
        self.canvas.bind("<Enter>", lambda e: self.bind_wheel(True))
        self.canvas.bind("<Leave>", lambda e: self.bind_wheel(False))
        for w in (self.canvas, self.inner):
            for ev in ("<Button-3>", "<Button-2>", "<Control-Button-1>"):
                w.bind(ev, lambda e: self.show_menu(e.x_root, e.y_root))

        if self.show_textbox:
            bar = ttk.Frame(self, padding=(10, 0))
            bar.pack(fill="x")
            ttk.Button(bar, text="Copy to clipboard", command=self.copy).pack(side="left")
            self.out = tk.Text(self, wrap="word", height=9, font=("TkDefaultFont", 11))
            self.out.pack(fill="both", padx=10, pady=8)
        else:
            self.out = None

        self.load()

    # ---------- JSON / menu ----------
    def load(self):
        cfg = getattr(self, "config_path", CONFIG)
        try:
            data = json.loads(cfg.read_text(encoding="utf-8"))
        except Exception as e:
            messagebox.showerror("Cannot read JSON", f"{cfg}\n\n{e}")
            return
        self.lists = data.get("lists", {})
        self.prefix, self.suffix = data.get("prefix", ""), data.get("suffix", "")
        self.menu.destroy()
        self.menu = tk.Menu(self, tearoff=0)
        self.items = {}
        try:
            self.build_menu(self.menu, data, [])
        except Exception as e:
            messagebox.showerror("Problem in JSON structure", str(e))
        for chip in self.chips:  # pick up edited item definitions
            new = self.items.get(chip.item.path)
            if new:
                chip.item = new
                chip.values = self.fit_values(chip.values, new)
        self.rebuild()
        self.status.config(text="Drag ⠿ to reorder · click a rectangle to edit · ✕ removes it")

    @staticmethod
    def fit_values(values, item):
        vals = [list(v) for v in values][:len(item.slots)]
        while len(vals) < len(item.slots):
            vals.append([])
        return vals

    # ---------- save / load design ----------
    def designs_dir(self):
        cfg = getattr(self, "config_path", CONFIG)
        d = cfg.parent / "designs"
        return d if d.is_dir() else cfg.parent

    def save_design(self):
        if not self.chips:
            messagebox.showinfo("Nothing to save", "Add some items first.")
            return
        cfg = getattr(self, "config_path", CONFIG)
        d = cfg.parent / "designs"
        d.mkdir(exist_ok=True)
        path = filedialog.asksaveasfilename(
            title="Save design", initialdir=d, defaultextension=".json",
            filetypes=[("Design files", "*.json")])
        if not path:
            return
        data = {"version": 1,
                "chips": [{"path": c.item.path, "values": c.values} for c in self.chips]}
        try:
            Path(path).write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        except OSError as e:
            messagebox.showerror("Cannot save", str(e))
            return
        self.status.config(text=f"Saved {Path(path).name}")

    def load_design(self):
        path = filedialog.askopenfilename(
            title="Load design", initialdir=self.designs_dir(),
            filetypes=[("Design files", "*.json")])
        if not path:
            return
        if self.chips and not messagebox.askyesno("Load design", "Replace the current selection?"):
            return
        try:
            data = json.loads(Path(path).read_text(encoding="utf-8"))
            entries = data["chips"]
        except Exception as e:
            messagebox.showerror("Cannot load", f"{path}\n\n{e}")
            return
        chips, missing = [], []
        for ent in entries:
            item = self.items.get(ent.get("path"))
            if not item:
                missing.append(str(ent.get("path")))
                continue
            chip = Chip(item)
            chip.values = self.fit_values(ent.get("values", []), item)
            chips.append(chip)
        self.chips = chips
        self.rebuild()
        msg = f"Loaded {Path(path).name}"
        if missing:
            msg += f" ({len(missing)} item(s) no longer in the menu skipped)"
            messagebox.showwarning("Some items skipped", "Not found in the current menu JSON:\n\n" + "\n".join(missing))
        self.status.config(text=msg)

    def build_menu(self, menu, node, path):
        for sub in node.get("categories", []):
            m = tk.Menu(menu, tearoff=0)
            menu.add_cascade(label=sub["name"], menu=m)
            self.build_menu(m, sub, path + [sub["name"]])
        for spec in node.get("items", []):
            item = Item("/".join(path + [spec.get("label") or spec["template"]]), spec, self.lists)
            self.items[item.path] = item
            menu.add_command(label=item.label, command=lambda it=item: self.add_item(it))

    def show_menu(self, x, y):
        try:
            self.menu.tk_popup(x, y)
        finally:
            self.menu.grab_release()

    def show_menu_at_button(self):
        self.show_menu(self.add_btn.winfo_rootx(), self.add_btn.winfo_rooty() + self.add_btn.winfo_height())

    # ---------- chips ----------
    def add_item(self, item):
        same = next((c for c in self.chips if c.item.path == item.path), None)
        if same:
            if item.slots:
                self.edit_chip(same)
            return
        swap = next((c for c in self.chips if item.group and c.item.group == item.group), None)
        if swap:
            backup = (swap.item, swap.values)
            swap.item, swap.values = item, [[] for _ in item.slots]
            chip = swap
        else:
            backup = None
            chip = Chip(item)
            self.chips.append(chip)
        if item.slots:
            res = self.ask_values(chip)
            if res is None:  # cancelled
                if backup:
                    chip.item, chip.values = backup
                else:
                    self.chips.remove(chip)
            else:
                chip.values = res
        self.rebuild()

    def edit_chip(self, chip):
        res = self.ask_values(chip)
        if res is not None:
            chip.values = res
            self.rebuild()

    def remove(self, chip):
        self.chips.remove(chip)
        self.rebuild()

    def clear(self):
        self.chips.clear()
        self.rebuild()

    def rebuild(self):
        for w in self.inner.winfo_children():
            w.destroy()
        self.labels, self.frames = [], []
        for chip in self.chips:
            bg = "#e8f0fe" if chip.complete else "#fde8e8"
            f = tk.Frame(self.inner, bg=bg, highlightthickness=1, highlightbackground="#9aa5b1", bd=0)
            f.pack(fill="x", padx=4, pady=3)
            x = tk.Label(f, text="✕", bg=bg, fg="#b00020", cursor="hand2", font=("TkDefaultFont", 12, "bold"))
            x.pack(side="right", padx=8)
            x.bind("<Button-1>", lambda e, c=chip: self.remove(c))
            h = tk.Label(f, text="⠿", bg=bg, fg="#667085", cursor="fleur", font=("TkDefaultFont", 14))
            h.pack(side="left", padx=(8, 0))
            h.bind("<ButtonPress-1>", lambda e, c=chip: self.drag_start(c))
            h.bind("<B1-Motion>", lambda e: self.drag_move())
            h.bind("<ButtonRelease-1>", lambda e: self.drag_end())
            lbl = tk.Label(f, text=chip.render(), bg=bg, fg="black", anchor="w", justify="left",
                           wraplength=max(200, self.canvas.winfo_width() - 90))
            lbl.pack(side="left", fill="x", expand=True, padx=8, pady=5)
            if chip.item.slots:
                lbl.configure(cursor="hand2")
                lbl.bind("<Button-1>", lambda e, c=chip: self.edit_chip(c))
            self.labels.append(lbl)
            self.frames.append(f)
        self.refresh_output()

    # ---------- drag to reorder ----------
    def pointer_y(self):
        return self.inner.winfo_pointery() - self.inner.winfo_rooty()

    def drop_index(self):
        y = self.pointer_y()
        for i, f in enumerate(self.frames):
            if y < f.winfo_y() + f.winfo_height() / 2:
                return i
        return len(self.frames)

    def drag_start(self, chip):
        self.drag_chip = chip
        self.indicator = tk.Frame(self.inner, bg="#1a73e8", height=3)

    def drag_move(self):
        if not self.drag_chip:
            return
        idx = self.drop_index()
        if idx < len(self.frames):
            y = self.frames[idx].winfo_y() - 2
        else:
            last = self.frames[-1]
            y = last.winfo_y() + last.winfo_height() + 1
        self.indicator.place(x=0, y=y, relwidth=1)
        self.indicator.lift()
        cy = self.canvas.winfo_pointery() - self.canvas.winfo_rooty()  # auto-scroll near edges
        if not self.can_scroll():
            return
        if cy < 24:
            self.canvas.yview_scroll(-1, "units")
        elif cy > self.canvas.winfo_height() - 24:
            self.canvas.yview_scroll(1, "units")

    def drag_end(self):
        chip, self.drag_chip = self.drag_chip, None
        if not chip:
            return
        idx = self.drop_index()
        if self.indicator:
            self.indicator.destroy()
            self.indicator = None
        old = self.chips.index(chip)
        self.chips.pop(old)
        if idx > old:
            idx -= 1
        self.chips.insert(idx, chip)
        self.rebuild()

    def update_scrollregion(self):
        # Scroll region is never smaller than the visible area, so short lists can't be
        # scrolled (scrolling a too-small region is what made the chips jump to the middle).
        w = self.canvas.winfo_width()
        h = max(self.inner.winfo_reqheight(), self.canvas.winfo_height())
        self.canvas.configure(scrollregion=(0, 0, w, h))
        if self.inner.winfo_reqheight() <= self.canvas.winfo_height():
            self.canvas.yview_moveto(0)

    def can_scroll(self):
        return self.inner.winfo_reqheight() > self.canvas.winfo_height()

    def on_canvas_resize(self, e):
        self.canvas.itemconfig(self.win, width=e.width)
        self.update_scrollregion()
        for l in self.labels:
            l.configure(wraplength=max(200, e.width - 90))

    def bind_wheel(self, on):
        for ev in ("<MouseWheel>", "<Button-4>", "<Button-5>"):
            if on:
                self.bind_all(ev, self.on_wheel)
            else:
                self.unbind_all(ev)

    def on_wheel(self, e):
        if e.num == 4:
            d = -1
        elif e.num == 5:
            d = 1
        else:
            d = -1 if e.delta > 0 else 1
        if self.can_scroll():
            self.canvas.yview_scroll(d, "units")

    # ---------- output ----------
    def get_output_text(self):
        parts = []
        for c in self.chips:
            if c.complete:
                s = c.render().strip()
                if s:
                    s = s[0].upper() + s[1:]
                    parts.append(s if s[-1] in ".!?" else s + ".")
        return " ".join(p for p in [self.prefix] + parts + [self.suffix] if p)

    def refresh_output(self):
        text = self.get_output_text()
        if hasattr(self, "out") and self.out is not None:
            self.out.delete("1.0", "end")
            self.out.insert("1.0", text)
        if hasattr(self, "on_change") and callable(self.on_change):
            self.on_change(text)

    def copy(self):
        text = self.get_output_text()
        self.clipboard_clear()
        self.clipboard_append(text)
        self.update()
        self.status.config(text="Copied!")

    # ---------- value picker dialog ----------
    def ask_values(self, chip):
        item = chip.item
        dlg = tk.Toplevel(self)
        dlg.title(item.label.rstrip(".").rstrip("…").strip() if item.label else "Options")
        dlg.transient(self)
        dlg.geometry(f"+{self.winfo_rootx() + 60}+{self.winfo_rooty() + 60}")
        result = {"value": None}
        body = ttk.Frame(dlg, padding=10)
        body.pack(fill="both", expand=True)
        ttk.Label(body, text=item.template, foreground="gray", wraplength=480).pack(anchor="w")

        entries = []
        for si, slot in enumerate(item.slots):
            title = "Choose one" if not slot["multi"] else "Choose one or more"
            if len(item.slots) > 1:
                title = f"# {si + 1}: {title}"
            box = ttk.LabelFrame(body, text=title, padding=6)
            box.pack(fill="x", pady=4)
            grid = ttk.Frame(box)
            grid.pack(fill="x")
            chosen = chip.values[si]
            opts = slot["options"] + [v for v in chosen if v not in slot["options"]]
            longest = max([len(o) for o in opts] or [0])
            cols = 1 if longest > 45 else (3 if longest < 18 else 2)
            ent = {"multi": slot["multi"], "grid": grid, "rows": [], "single": tk.StringVar(), "cols": cols}
            entries.append(ent)
            for o in opts:
                self.add_choice(ent, o, o in chosen)
            row = ttk.Frame(box)
            row.pack(fill="x", pady=(6, 0))
            ttk.Label(row, text="Custom:").pack(side="left")
            e = ttk.Entry(row)
            e.pack(side="left", fill="x", expand=True, padx=4)

            def add_custom(ent=ent, e=e):
                t = e.get().strip()
                if t and t not in [r[0] for r in ent["rows"]]:
                    self.add_choice(ent, t, True)
                e.delete(0, "end")

            ttk.Button(row, text="Add", command=add_custom).pack(side="left")
            e.bind("<Return>", lambda ev, f=add_custom: f())

        def ok():
            res = []
            for ent in entries:
                if ent["multi"]:
                    res.append([t for t, v in ent["rows"] if v.get()])
                else:
                    s = ent["single"].get()
                    res.append([s] if s else [])
            result["value"] = res
            dlg.destroy()

        btns = ttk.Frame(body)
        btns.pack(fill="x", pady=(8, 0))
        ttk.Button(btns, text="OK", command=ok).pack(side="right")
        ttk.Button(btns, text="Cancel", command=dlg.destroy).pack(side="right", padx=6)
        dlg.bind("<Escape>", lambda e: dlg.destroy())
        dlg.wait_visibility()
        dlg.grab_set()
        self.wait_window(dlg)
        return result["value"]

    @staticmethod
    def add_choice(ent, text, selected):
        i = len(ent["rows"])
        if ent["multi"]:
            var = tk.BooleanVar(value=selected)
            w = ttk.Checkbutton(ent["grid"], text=text, variable=var)
        else:
            var = ent["single"]
            if selected:
                var.set(text)
            w = ttk.Radiobutton(ent["grid"], text=text, variable=var, value=text)
        w.grid(row=i // ent["cols"], column=i % ent["cols"], sticky="w", padx=6, pady=1)
        ent["rows"].append((text, var))


class AdvancedPromptBuilderWindow(tk.Toplevel, AdvancedPromptBuilderCore):
    def __init__(self, master=None, on_change=None, show_textbox=False, config_path=None):
        super().__init__(master)
        self.setup_ui(on_change=on_change, show_textbox=show_textbox, config_path=config_path)
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def on_close(self):
        self.withdraw()


class App(tk.Tk, AdvancedPromptBuilderCore):
    def __init__(self):
        super().__init__()
        self.setup_ui(on_change=None, show_textbox=True)


if __name__ == "__main__":
    App().mainloop()
