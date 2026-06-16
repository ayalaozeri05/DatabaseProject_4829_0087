"""
screens/base_screen.py
Shared base class + reusable UI helpers for all screens.
Light theme – matches modern TransRoute Planner design.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import customtkinter as ctk

# ─── Palette ──────────────────────────────────────────────────────────────────
ACCENT   = "#5b5fcf"   # indigo
ACCENT2  = "#22a06b"   # green
DANGER   = "#e53e3e"   # red
WARNING  = "#d97706"   # amber
BG_MAIN  = "#f0f2f7"   # page background
BG_NAV   = "#ffffff"   # navbar / header
BG_CARD  = "#ffffff"   # card background
BG_ROW   = "#f7f8fa"   # entry / alt-row background
BORDER   = "#e2e8f0"   # subtle border
TEXT_PRI = "#1a202c"   # near-black primary text
TEXT_SEC = "#718096"   # medium-gray secondary text

# BG_MID / BG_DARK kept as aliases so old imports don't crash
BG_MID  = BG_NAV
BG_DARK = BG_MAIN

# Font spec tuples – safe to define at module level (no Tk needed)
FONT_H1  = ("Segoe UI", 22, "bold")
FONT_H2  = ("Segoe UI", 16, "bold")
FONT_LBL = ("Segoe UI", 13)
FONT_SM  = ("Segoe UI", 11)

# ─── Treeview style ──────────────────────────────────────────────────────────
_STYLE_APPLIED = False

def _apply_tree_style():
    global _STYLE_APPLIED
    if _STYLE_APPLIED:
        return
    style = ttk.Style()
    style.theme_use("clam")
    style.configure("Custom.Treeview",
        background="#ffffff",
        foreground=TEXT_PRI,
        fieldbackground="#ffffff",
        rowheight=32,
        borderwidth=0,
        relief="flat",
        font=("Segoe UI", 11),
    )
    style.configure("Custom.Treeview.Heading",
        background="#f7f8fa",
        foreground=ACCENT,
        relief="flat",
        font=("Segoe UI", 11, "bold"),
        padding=(8, 6),
    )
    style.map("Custom.Treeview",
        background=[("selected", ACCENT)],
        foreground=[("selected", "#ffffff")],
    )
    style.map("Custom.Treeview.Heading",
        background=[("active", "#eef0fb")],
    )
    _STYLE_APPLIED = True


# ─── Base Screen ──────────────────────────────────────────────────────────────
class BaseScreen(ctk.CTkFrame):
    """All screens inherit from this."""

    def __init__(self, parent, title: str, icon: str = ""):
        super().__init__(parent, fg_color=BG_MAIN, corner_radius=0)
        _apply_tree_style()
        self._build_header(icon, title)

    def _build_header(self, icon: str, title: str):
        hdr = ctk.CTkFrame(self, fg_color=BG_CARD, corner_radius=0,
                            height=64, border_width=1, border_color=BORDER)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        ctk.CTkLabel(hdr, text=f"{icon}  {title}",
                     font=FONT_H1, text_color=TEXT_PRI).pack(
            side="left", padx=28, pady=14)

    # ── Reusable widgets ──────────────────────────────────────────────────────

    def make_card(self, parent, **kwargs):
        defaults = dict(fg_color=BG_CARD, corner_radius=14,
                        border_width=1, border_color=BORDER)
        defaults.update(kwargs)
        return ctk.CTkFrame(parent, **defaults)

    def make_button(self, parent, text, command, color=ACCENT, **kw):
        kw.setdefault("height", 36)
        hover = self._darken(color) if color not in (BG_CARD, BG_NAV) else "#eef0fb"
        txt_color = "#ffffff" if color not in (BG_CARD, BG_NAV, BG_ROW) else TEXT_PRI
        return ctk.CTkButton(parent, text=text, command=command,
                             fg_color=color, hover_color=hover,
                             text_color=txt_color,
                             font=FONT_LBL, corner_radius=8, **kw)

    def make_entry(self, parent, placeholder="", width=200):
        return ctk.CTkEntry(parent, placeholder_text=placeholder,
                            width=width, font=FONT_LBL,
                            fg_color=BG_ROW,
                            border_color=BORDER,
                            text_color=TEXT_PRI,
                            placeholder_text_color=TEXT_SEC,
                            corner_radius=8)

    def make_label(self, parent, text, color=TEXT_PRI, bold=False, size=13):
        font = ("Segoe UI", size, "bold" if bold else "normal")
        return ctk.CTkLabel(parent, text=text, font=font, text_color=color)

    def make_dropdown(self, parent, values, width=200, command=None):
        return ctk.CTkOptionMenu(parent, values=values, width=width,
                                 font=FONT_LBL,
                                 fg_color=BG_ROW,
                                 button_color=ACCENT,
                                 button_hover_color=self._darken(ACCENT),
                                 text_color=TEXT_PRI,
                                 dropdown_fg_color=BG_CARD,
                                 dropdown_hover_color="#eef0fb",
                                 dropdown_text_color=TEXT_PRI,
                                 corner_radius=8,
                                 command=command)

    def make_tree(self, parent, columns: list, heights=14):
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill="both", expand=True, padx=0, pady=0)

        tree = ttk.Treeview(frame, columns=columns, show="headings",
                            style="Custom.Treeview", height=heights,
                            selectmode="browse")

        vsb = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
        hsb = ttk.Scrollbar(frame, orient="horizontal", command=tree.xview)
        tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        hsb.pack(side="bottom", fill="x")
        vsb.pack(side="right", fill="y")
        tree.pack(side="left", fill="both", expand=True)

        col_w = max(80, 900 // max(len(columns), 1))
        for col in columns:
            tree.heading(col, text=col, anchor="w")
            tree.column(col, width=col_w, minwidth=60, anchor="w")

        tree.tag_configure("odd",  background="#ffffff")
        tree.tag_configure("even", background="#f7f8fa")
        return tree

    def populate_tree(self, tree, rows):
        tree.delete(*tree.get_children())
        cols = tree["columns"]
        for i, row in enumerate(rows):
            values = [row.get(c, "") for c in cols]
            tag = "odd" if i % 2 == 0 else "even"
            tree.insert("", "end", values=values, tags=(tag,))

    @staticmethod
    def _darken(hex_color: str) -> str:
        try:
            r = max(0, int(hex_color[1:3], 16) - 25)
            g = max(0, int(hex_color[3:5], 16) - 25)
            b = max(0, int(hex_color[5:7], 16) - 25)
            return f"#{r:02x}{g:02x}{b:02x}"
        except Exception:
            return hex_color

    # ── Notification helpers ──────────────────────────────────────────────────

    @staticmethod
    def success(msg: str):
        messagebox.showinfo("✅ Success", msg)

    @staticmethod
    def error(msg: str):
        messagebox.showerror("❌ Error", msg)

    @staticmethod
    def confirm(msg: str) -> bool:
        return messagebox.askyesno("⚠️ Confirm", msg)
