"""
screens/routes_screen.py
Full CRUD for the route table + interactive map showing route stops.
route_id is auto-generated on Add; created_date defaults to today.
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import ttk
from datetime import date
from screens.base_screen import (BaseScreen, BG_MAIN, BG_NAV, BG_CARD, BG_ROW,
                                  ACCENT, ACCENT2, DANGER, BORDER,
                                  TEXT_PRI, TEXT_SEC, FONT_H2, FONT_LBL, FONT_SM)
import db_connection as db

try:
    import tkintermapview
    MAP_AVAILABLE = True
except ImportError:
    MAP_AVAILABLE = False


class RoutesScreen(BaseScreen):
    def __init__(self, parent):
        super().__init__(parent, "Routes Management", "🗺️")
        self._selected_route_id = None
        self._build()

    # ─── Main layout ──────────────────────────────────────────────────────────
    def _build(self):
        toolbar = ctk.CTkFrame(self, fg_color=BG_NAV, corner_radius=0,
                               height=52, border_width=1, border_color=BORDER)
        toolbar.pack(fill="x")
        toolbar.pack_propagate(False)

        self.search_var = ctk.StringVar()
        self.search_var.trace_add("write", lambda *_: self._load_routes())
        ctk.CTkEntry(toolbar, textvariable=self.search_var,
                     placeholder_text="🔍  Search routes…",
                     width=260, font=FONT_LBL,
                     fg_color=BG_ROW, border_color=BORDER,
                     text_color=TEXT_PRI, placeholder_text_color=TEXT_SEC,
                     corner_radius=8).pack(side="left", padx=16, pady=10)

        for text, cmd, color in [
            ("＋  Add Route",    self._open_add_dialog,   ACCENT2),
            ("✏️  Edit Route",   self._open_edit_dialog,  ACCENT),
            ("🗑  Delete Route", self._delete_selected,   DANGER),
            ("🔄  Refresh",      self._load_routes,        BG_ROW),
        ]:
            self.make_button(toolbar, text, cmd, color=color).pack(
                side="left", padx=4, pady=10)

        # ── Paned area: table left, map right ────────────────────────────────
        paned = tk.PanedWindow(self, orient=tk.HORIZONTAL,
                               bg=BG_MAIN, sashwidth=6, sashrelief="flat",
                               handlesize=0)
        paned.pack(fill="both", expand=True, padx=12, pady=12)

        left = ctk.CTkFrame(paned, fg_color=BG_CARD, corner_radius=12,
                            border_width=1, border_color=BORDER)
        paned.add(left, minsize=480)

        cols = ["route_id", "route_name", "region_name", "start_location",
                "end_location", "distance_km", "duration_min", "stops", "future_trips"]
        self.tree = self.make_tree(left, cols, heights=18)
        self.tree.bind("<<TreeviewSelect>>", self._on_select)

        right = ctk.CTkFrame(paned, fg_color=BG_CARD, corner_radius=12,
                             border_width=1, border_color=BORDER)
        paned.add(right, minsize=400)
        self._build_right_panel(right)

        self._load_routes()

    def _build_right_panel(self, parent):
        ctk.CTkLabel(parent, text="📍  Route Map",
                     font=FONT_H2, text_color=TEXT_PRI).pack(
            anchor="w", padx=14, pady=(12, 4))

        if MAP_AVAILABLE:
            self.map_widget = tkintermapview.TkinterMapView(
                parent, width=480, height=300, corner_radius=10)
            self.map_widget.pack(padx=10, pady=(0, 6), fill="x")
            self.map_widget.set_position(31.5, 34.75)
            self.map_widget.set_zoom(8)
        else:
            ctk.CTkLabel(parent,
                         text="(Install tkintermapview for live map)",
                         text_color=TEXT_SEC, font=FONT_SM).pack(pady=8)
            self.map_widget = None

        ctk.CTkFrame(parent, height=1, fg_color=BORDER).pack(
            fill="x", padx=14, pady=(4, 0))
        ctk.CTkLabel(parent, text="🛑  Stops in Route",
                     font=FONT_H2, text_color=TEXT_PRI).pack(
            anchor="w", padx=14, pady=(10, 4))

        self.stops_tree = self.make_tree(
            parent, ["order", "stop_name", "address", "arrival_time"], heights=8)

    # ─── Data loading ─────────────────────────────────────────────────────────
    def _load_routes(self, *_):
        q = """
            SELECT r.route_id,
                   r.route_name,
                   reg.regio_name          AS region_name,
                   r.start_location,
                   r.end_location,
                   r.total_distance_km     AS distance_km,
                   r.estimated_duration_minutes AS duration_min,
                   COALESCE(rs.stop_count, 0)::int  AS stops,
                   COALESCE(t.future_trips, 0)::int  AS future_trips
            FROM route r
            LEFT JOIN region reg ON reg.region_id = r.region_id
            LEFT JOIN (
                SELECT route_id, COUNT(*) AS stop_count FROM route_stop GROUP BY route_id
            ) rs ON rs.route_id = r.route_id
            LEFT JOIN (
                SELECT route_id, COUNT(*) AS future_trips
                FROM trip WHERE trip_date >= CURRENT_DATE GROUP BY route_id
            ) t ON t.route_id = r.route_id
            WHERE r.route_name ILIKE %s OR reg.regio_name ILIKE %s
            ORDER BY r.route_id
        """
        search = f"%{self.search_var.get()}%"
        rows = db.fetch_all(q, (search, search))
        self.populate_tree(self.tree, rows)

    def _on_select(self, _event=None):
        sel = self.tree.selection()
        if not sel:
            return
        vals = self.tree.item(sel[0], "values")
        self._selected_route_id = int(vals[0])
        self._load_route_stops(self._selected_route_id)

    def _load_route_stops(self, route_id: int):
        q = """
            SELECT rs.stop_order  AS "order",
                   s.stop_name,
                   s.address,
                   rs.estimated_arrival_time AS arrival_time,
                   s.latitude, s.longitude
            FROM route_stop rs
            JOIN stop s ON s.stop_id = rs.stop_id
            WHERE rs.route_id = %s
            ORDER BY rs.stop_order
        """
        rows = db.fetch_all(q, (route_id,))
        self.populate_tree(self.stops_tree, rows)

        if MAP_AVAILABLE and self.map_widget and rows:
            self.map_widget.delete_all_marker()
            coords = [(r["latitude"], r["longitude"]) for r in rows
                      if r["latitude"] and r["longitude"]]
            if coords:
                for i, (lat, lon) in enumerate(coords):
                    self.map_widget.set_marker(lat, lon, text=f"Stop {i+1}")
                if len(coords) > 1:
                    self.map_widget.set_path(coords)
                mid_lat = sum(c[0] for c in coords) / len(coords)
                mid_lon = sum(c[1] for c in coords) / len(coords)
                self.map_widget.set_position(mid_lat, mid_lon)
                self.map_widget.set_zoom(11)

    # ─── ADD ──────────────────────────────────────────────────────────────────
    def _open_add_dialog(self):
        dlg = _RouteDialog(self, title="Add New Route", mode="add")
        self.wait_window(dlg)
        self._load_routes()

    # ─── EDIT ─────────────────────────────────────────────────────────────────
    def _open_edit_dialog(self):
        if not self._selected_route_id:
            self.error("Please select a route first.")
            return
        row = db.fetch_one(
            "SELECT * FROM route WHERE route_id=%s", (self._selected_route_id,))
        dlg = _RouteDialog(self, title="Edit Route",
                           mode="edit", existing=row)
        self.wait_window(dlg)
        self._load_routes()

    # ─── DELETE ───────────────────────────────────────────────────────────────
    def _delete_selected(self):
        if not self._selected_route_id:
            self.error("Please select a route first.")
            return
        if not self.confirm(
                f"Delete route ID {self._selected_route_id}? "
                "This will also remove its route_stop entries."):
            return
        try:
            db.execute_dml("DELETE FROM route_stop WHERE route_id=%s",
                           (self._selected_route_id,))
            db.execute_dml("DELETE FROM route WHERE route_id=%s",
                           (self._selected_route_id,))
            self.success("Route deleted successfully.")
            self._selected_route_id = None
            self._load_routes()
        except Exception as e:
            self.error(str(e))


# ─── Add / Edit Dialog ────────────────────────────────────────────────────────
class _RouteDialog(ctk.CTkToplevel):
    def __init__(self, parent, title, mode, existing=None):
        super().__init__(parent)
        self.title(title)
        self.geometry("540x430")
        self.configure(fg_color=BG_MAIN)
        self.resizable(False, False)
        self.grab_set()
        self._mode = mode
        self._existing = existing or {}
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

        ex = self._existing
        regions   = db.get_regions()
        reg_names = [f"{r['region_id']} – {r['regio_name']}" for r in regions]

        # Build field list – no route_id in Add; no created_date (auto-set to today)
        fields = []
        if self._mode == "edit":
            fields.append(("Route ID (read-only)", "route_id",
                           str(ex.get("route_id", "")), True))
        fields += [
            ("Route Name",       "route_name",                  ex.get("route_name", ""),                          False),
            ("Start Location",   "start_location",              ex.get("start_location", ""),                      False),
            ("End Location",     "end_location",                ex.get("end_location", ""),                        False),
            ("Distance (km)",    "total_distance_km",           str(ex.get("total_distance_km", "")),              False),
            ("Duration (min)",   "estimated_duration_minutes",  str(ex.get("estimated_duration_minutes", "")),     False),
        ]

        self._vars = {}
        for row_i, (lbl, key, default, disabled) in enumerate(fields):
            ctk.CTkLabel(form, text=lbl, font=FONT_LBL,
                         text_color=TEXT_SEC, anchor="w").grid(
                row=row_i, column=0, padx=16, pady=5, sticky="w")
            var = ctk.StringVar(value=default)
            ent = ctk.CTkEntry(form, textvariable=var, width=270,
                               font=FONT_LBL, fg_color=BG_ROW,
                               border_color=BORDER, text_color=TEXT_PRI,
                               corner_radius=8)
            if disabled:
                ent.configure(state="disabled")
            ent.grid(row=row_i, column=1, padx=10, pady=5)
            self._vars[key] = var

        # Region dropdown
        ctk.CTkLabel(form, text="Region", font=FONT_LBL,
                     text_color=TEXT_SEC, anchor="w").grid(
            row=len(fields), column=0, padx=16, pady=5, sticky="w")
        cur_rid = ex.get("region_id", "")
        cur_name = next(
            (f"{r['region_id']} – {r['regio_name']}" for r in regions
             if r["region_id"] == cur_rid), reg_names[0] if reg_names else "")
        self._region_var = ctk.StringVar(value=cur_name)
        ctk.CTkOptionMenu(form, values=reg_names,
                          variable=self._region_var,
                          font=FONT_LBL, width=270,
                          fg_color=BG_ROW, button_color=ACCENT,
                          dropdown_fg_color=BG_CARD,
                          text_color=TEXT_PRI).grid(
            row=len(fields), column=1, padx=10, pady=5)
        self._regions = regions

        ctk.CTkButton(self, text="💾  Save",
                      font=ctk.CTkFont("Segoe UI", 14, "bold"),
                      fg_color=ACCENT2, hover_color="#1a8057",
                      text_color="#ffffff",
                      height=40, corner_radius=10,
                      command=self._save).pack(pady=14, padx=16, fill="x")

    def _save(self):
        from tkinter import messagebox
        v = {k: var.get().strip() for k, var in self._vars.items()}
        sel = self._region_var.get()
        try:
            region_id = int(sel.split(" – ")[0])
        except Exception:
            region_id = None

        required = [v.get("route_name"), v.get("start_location"),
                    v.get("end_location"), v.get("total_distance_km"),
                    v.get("estimated_duration_minutes"), region_id]
        if not all(required):
            messagebox.showerror("Error", "All fields are required.")
            return
        try:
            if self._mode == "add":
                row = db.fetch_one("SELECT COALESCE(MAX(route_id),0)+1 AS nid FROM route")
                new_id = row["nid"] if row else 1
                today = str(date.today())   # auto-set created_date
                db.execute_dml(
                    """INSERT INTO route
                       (route_id, route_name, start_location, end_location,
                        total_distance_km, estimated_duration_minutes,
                        created_date, region_id)
                       VALUES (%s,%s,%s,%s,%s,%s,%s,%s)""",
                    (new_id, v["route_name"], v["start_location"],
                     v["end_location"], float(v["total_distance_km"]),
                     int(v["estimated_duration_minutes"]),
                     today, region_id))
                messagebox.showinfo("Success", f"Route added (ID: {new_id})!")
            else:
                db.execute_dml(
                    """UPDATE route SET
                       route_name=%s, start_location=%s, end_location=%s,
                       total_distance_km=%s, estimated_duration_minutes=%s,
                       region_id=%s
                       WHERE route_id=%s""",
                    (v["route_name"], v["start_location"], v["end_location"],
                     float(v["total_distance_km"]),
                     int(v["estimated_duration_minutes"]),
                     region_id, int(v["route_id"])))
                messagebox.showinfo("Success", "Route updated!")
            self.destroy()
        except Exception as e:
            messagebox.showerror("DB Error", str(e))
