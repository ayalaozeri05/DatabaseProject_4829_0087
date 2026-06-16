"""
screens/stops_screen.py
Full CRUD for the stop table + live map preview of each stop's location.
stop_id is auto-generated on Add – users never enter it manually.
"""

import customtkinter as ctk
from screens.base_screen import (BaseScreen, BG_MAIN, BG_NAV, BG_CARD, BG_ROW,
                                  ACCENT, ACCENT2, DANGER, BORDER,
                                  TEXT_PRI, TEXT_SEC, FONT_H2, FONT_LBL, FONT_SM)
import db_connection as db

try:
    import tkintermapview
    MAP_AVAILABLE = True
except ImportError:
    MAP_AVAILABLE = False


class StopsScreen(BaseScreen):
    def __init__(self, parent):
        super().__init__(parent, "Stops Management", "📍")
        self._sel_stop_id = None
        self._build()

    def _build(self):
        toolbar = ctk.CTkFrame(self, fg_color=BG_NAV, corner_radius=0,
                               height=52, border_width=1, border_color=BORDER)
        toolbar.pack(fill="x")
        toolbar.pack_propagate(False)

        self.search_var = ctk.StringVar()
        self.search_var.trace_add("write", lambda *_: self._load())
        ctk.CTkEntry(toolbar, textvariable=self.search_var,
                     placeholder_text="🔍  Search stop or site…",
                     width=260, font=FONT_LBL, fg_color=BG_ROW,
                     border_color=BORDER, text_color=TEXT_PRI,
                     placeholder_text_color=TEXT_SEC,
                     corner_radius=8).pack(side="left", padx=16, pady=10)

        for text, cmd, color in [
            ("＋  Add Stop",   self._add,    ACCENT2),
            ("✏️  Edit Stop",  self._edit,   ACCENT),
            ("🗑  Delete",     self._delete, DANGER),
            ("🔄  Refresh",    self._load,   BG_ROW),
        ]:
            self.make_button(toolbar, text, cmd, color=color).pack(
                side="left", padx=4, pady=10)

        import tkinter as tk
        paned = tk.PanedWindow(self, orient=tk.HORIZONTAL,
                               bg=BG_MAIN, sashwidth=6)
        paned.pack(fill="both", expand=True, padx=12, pady=12)

        # Left: table
        left = self.make_card(paned)
        paned.add(left, minsize=500)
        cols = ["stop_id", "stop_name", "address", "site_name",
                "site_type", "latitude", "longitude", "routes_count"]
        self.tree = self.make_tree(left, cols, heights=22)
        self.tree.bind("<<TreeviewSelect>>", self._on_select)

        # Right: map preview
        right = self.make_card(paned)
        paned.add(right, minsize=360)
        self._build_map(right)

        self._load()

    def _build_map(self, parent):
        ctk.CTkLabel(parent, text="🗺️  Stop Location",
                     font=FONT_H2, text_color=TEXT_PRI).pack(
            anchor="w", padx=14, pady=(14, 6))

        if MAP_AVAILABLE:
            self.map_widget = tkintermapview.TkinterMapView(
                parent, width=400, height=300, corner_radius=10)
            self.map_widget.pack(padx=10, pady=(0, 8), fill="x")
            self.map_widget.set_position(31.5, 34.75)
            self.map_widget.set_zoom(10)
        else:
            ctk.CTkLabel(parent, text="Install tkintermapview\nfor map preview",
                         text_color=TEXT_SEC, font=FONT_SM).pack(pady=20)
            self.map_widget = None

        ctk.CTkFrame(parent, height=1, fg_color=BORDER).pack(
            fill="x", padx=14, pady=(4, 0))

        ctk.CTkLabel(parent, text="ℹ️  Stop Info",
                     font=FONT_H2, text_color=TEXT_PRI).pack(
            anchor="w", padx=14, pady=(10, 4))

        self._detail_vars = {}
        for lbl in ["Stop Name", "Address", "Site", "Site Type",
                    "Lat / Lon", "Routes Through"]:
            r = ctk.CTkFrame(parent, fg_color="transparent")
            r.pack(fill="x", padx=14, pady=2)
            ctk.CTkLabel(r, text=f"{lbl}:", font=FONT_SM,
                         text_color=TEXT_SEC, width=110, anchor="w").pack(side="left")
            var = ctk.StringVar(value="—")
            ctk.CTkLabel(r, textvariable=var, font=FONT_LBL,
                         text_color=TEXT_PRI, anchor="w").pack(side="left")
            self._detail_vars[lbl] = var

    # ─── Data ──────────────────────────────────────────────────────────────────
    def _load(self, *_):
        s = f"%{self.search_var.get()}%"
        q = """
            SELECT s.stop_id, s.stop_name, s.address,
                   s.site_name, si.site_type,
                   ROUND(s.latitude::numeric,  5) AS latitude,
                   ROUND(s.longitude::numeric, 5) AS longitude,
                   COUNT(DISTINCT rs.route_id) AS routes_count
            FROM stop s
            LEFT JOIN site si ON si.site_name = s.site_name
            LEFT JOIN route_stop rs ON rs.stop_id = s.stop_id
            WHERE s.stop_name ILIKE %s OR s.site_name ILIKE %s
            GROUP BY s.stop_id, s.stop_name, s.address,
                     s.site_name, si.site_type, s.latitude, s.longitude
            ORDER BY s.stop_id
        """
        rows = db.fetch_all(q, (s, s))
        self.populate_tree(self.tree, rows)

    def _on_select(self, _=None):
        sel = self.tree.selection()
        if not sel:
            return
        vals = self.tree.item(sel[0], "values")
        self._sel_stop_id = int(vals[0])

        try:
            lat = float(vals[5])
            lon = float(vals[6])
            if MAP_AVAILABLE and self.map_widget:
                self.map_widget.delete_all_marker()
                self.map_widget.set_marker(lat, lon, text=vals[1])
                self.map_widget.set_position(lat, lon)
                self.map_widget.set_zoom(14)
        except (ValueError, IndexError):
            pass

        self._detail_vars["Stop Name"].set(vals[1])
        self._detail_vars["Address"].set(vals[2])
        self._detail_vars["Site"].set(vals[3])
        self._detail_vars["Site Type"].set(vals[4])
        self._detail_vars["Lat / Lon"].set(f"{vals[5]}, {vals[6]}")
        self._detail_vars["Routes Through"].set(str(vals[7]))

    # ─── CRUD ──────────────────────────────────────────────────────────────────
    def _add(self):
        dlg = _StopDialog(self, mode="add")
        self.wait_window(dlg)
        self._load()

    def _edit(self):
        if not self._sel_stop_id:
            self.error("Select a stop first.")
            return
        row = db.fetch_one("SELECT * FROM stop WHERE stop_id=%s",
                           (self._sel_stop_id,))
        dlg = _StopDialog(self, mode="edit", existing=row)
        self.wait_window(dlg)
        self._load()

    def _delete(self):
        if not self._sel_stop_id:
            self.error("Select a stop first.")
            return
        if not self.confirm(f"Delete stop ID {self._sel_stop_id}?"):
            return
        try:
            db.execute_dml("DELETE FROM route_stop WHERE stop_id=%s",
                           (self._sel_stop_id,))
            db.execute_dml("DELETE FROM stop WHERE stop_id=%s",
                           (self._sel_stop_id,))
            self.success("Stop deleted.")
            self._sel_stop_id = None
            self._load()
        except Exception as e:
            self.error(str(e))


class _StopDialog(ctk.CTkToplevel):
    def __init__(self, parent, mode, existing=None):
        super().__init__(parent)
        self.title("Add Stop" if mode == "add" else "Edit Stop")
        self.geometry("460x380")
        self.configure(fg_color=BG_MAIN)
        self.resizable(False, False)
        self.grab_set()
        self._mode = mode
        self._ex = existing or {}
        self._build()

    def _build(self):
        hdr = ctk.CTkFrame(self, fg_color=BG_CARD, corner_radius=0,
                            height=54, border_width=1, border_color=BORDER)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        ctk.CTkLabel(hdr, text=self.title(),
                     font=ctk.CTkFont("Segoe UI", 16, "bold"),
                     text_color=TEXT_PRI).pack(side="left", padx=20, pady=12)

        form = ctk.CTkFrame(self, fg_color=BG_CARD, corner_radius=12,
                            border_width=1, border_color=BORDER)
        form.pack(padx=16, pady=12, fill="both", expand=True)

        ex = self._ex
        # Add mode: no stop_id field. Edit mode: read-only.
        fields = []
        if self._mode == "edit":
            fields.append(("Stop ID (read-only)", "stop_id",
                           str(ex.get("stop_id", "")), True))
        fields += [
            ("Stop Name", "stop_name", ex.get("stop_name", ""), False),
            ("Address",   "address",   ex.get("address",   ""), False),
            ("Latitude",  "latitude",  str(ex.get("latitude",  "")), False),
            ("Longitude", "longitude", str(ex.get("longitude", "")), False),
        ]
        self._vars = {}
        for i, (lbl, key, default, disabled) in enumerate(fields):
            ctk.CTkLabel(form, text=lbl, font=FONT_LBL,
                         text_color=TEXT_SEC, anchor="w").grid(
                row=i, column=0, padx=14, pady=6, sticky="w")
            var = ctk.StringVar(value=default)
            ent = ctk.CTkEntry(form, textvariable=var, width=250, font=FONT_LBL,
                               fg_color=BG_ROW, border_color=BORDER,
                               text_color=TEXT_PRI, corner_radius=8)
            if disabled:
                ent.configure(state="disabled")
            ent.grid(row=i, column=1, padx=10, pady=6)
            self._vars[key] = var

        # Site dropdown
        sites = db.get_sites()
        s_names = [s["site_name"] for s in sites]
        cur_site = ex.get("site_name", s_names[0] if s_names else "")
        self._site_var = ctk.StringVar(value=cur_site)
        row_idx = len(fields)
        ctk.CTkLabel(form, text="Site", font=FONT_LBL,
                     text_color=TEXT_SEC, anchor="w").grid(
            row=row_idx, column=0, padx=14, pady=6, sticky="w")
        ctk.CTkOptionMenu(form, values=s_names,
                          variable=self._site_var,
                          font=FONT_LBL, width=250,
                          fg_color=BG_ROW, button_color=ACCENT,
                          dropdown_fg_color=BG_CARD,
                          text_color=TEXT_PRI).grid(
            row=row_idx, column=1, padx=10, pady=6)

        ctk.CTkButton(self, text="💾  Save",
                      font=ctk.CTkFont("Segoe UI", 14, "bold"),
                      fg_color=ACCENT2, hover_color="#1a8057",
                      text_color="#ffffff",
                      height=40, corner_radius=10,
                      command=self._save).pack(pady=12, padx=16, fill="x")

    def _save(self):
        from tkinter import messagebox
        v = {k: var.get().strip() for k, var in self._vars.items()}
        site = self._site_var.get()
        if not all([v.get("stop_name"), v.get("address"),
                    v.get("latitude"), v.get("longitude"), site]):
            messagebox.showerror("Error", "All fields are required.")
            return
        try:
            if self._mode == "add":
                row = db.fetch_one("SELECT COALESCE(MAX(stop_id),0)+1 AS nid FROM stop")
                new_id = row["nid"] if row else 1
                db.execute_dml(
                    "INSERT INTO stop (stop_id, stop_name, address, "
                    "latitude, longitude, site_name) "
                    "VALUES (%s,%s,%s,%s,%s,%s)",
                    (new_id, v["stop_name"], v["address"],
                     float(v["latitude"]), float(v["longitude"]), site))
                messagebox.showinfo("Success", f"Stop added (ID: {new_id})!")
            else:
                db.execute_dml(
                    "UPDATE stop SET stop_name=%s, address=%s, "
                    "latitude=%s, longitude=%s, site_name=%s "
                    "WHERE stop_id=%s",
                    (v["stop_name"], v["address"],
                     float(v["latitude"]), float(v["longitude"]), site,
                     int(v["stop_id"])))
                messagebox.showinfo("Success", "Stop updated!")
            self.destroy()
        except Exception as e:
            messagebox.showerror("DB Error", str(e))
