"""
screens/trips_screen.py
Full CRUD for the trip table with dropdowns showing names (not IDs).
trip_id is auto-generated on Add – users never enter it manually.
"""

import customtkinter as ctk
import tkinter as tk
from screens.base_screen import (BaseScreen, BG_MAIN, BG_NAV, BG_CARD, BG_ROW,
                                  ACCENT, ACCENT2, DANGER, BORDER,
                                  TEXT_PRI, TEXT_SEC, FONT_H2, FONT_LBL, FONT_SM)
import db_connection as db


class TripsScreen(BaseScreen):
    def __init__(self, parent):
        super().__init__(parent, "Trips Management", "🚌")
        self._selected_trip_id = None
        self._build()

    def _build(self):
        # ── Toolbar ──────────────────────────────────────────────────────────
        toolbar = ctk.CTkFrame(self, fg_color=BG_NAV, corner_radius=0,
                               height=52, border_width=1, border_color=BORDER)
        toolbar.pack(fill="x")
        toolbar.pack_propagate(False)

        self.search_var = ctk.StringVar()
        self.search_var.trace_add("write", lambda *_: self._load())
        ctk.CTkEntry(toolbar, textvariable=self.search_var,
                     placeholder_text="🔍  Search by route or driver…",
                     width=280, font=FONT_LBL, fg_color=BG_ROW,
                     border_color=BORDER, text_color=TEXT_PRI,
                     placeholder_text_color=TEXT_SEC,
                     corner_radius=8).pack(side="left", padx=16, pady=10)

        for text, cmd, color in [
            ("＋  Add Trip",   self._open_add,   ACCENT2),
            ("✏️  Edit Trip",  self._open_edit,  ACCENT),
            ("🗑  Delete",     self._delete,      DANGER),
            ("🔄  Refresh",    self._load,        BG_ROW),
        ]:
            self.make_button(toolbar, text, cmd, color=color).pack(
                side="left", padx=4, pady=10)

        # ── Filter row ───────────────────────────────────────────────────────
        filt = ctk.CTkFrame(self, fg_color=BG_NAV, corner_radius=0,
                            height=44, border_width=1, border_color=BORDER)
        filt.pack(fill="x")
        filt.pack_propagate(False)

        ctk.CTkLabel(filt, text="Filter:", font=FONT_SM,
                     text_color=TEXT_SEC).pack(side="left", padx=12, pady=8)

        self._date_filter = ctk.StringVar(value="All")
        for val in ["All", "Today", "Future", "Past"]:
            ctk.CTkRadioButton(filt, text=val, variable=self._date_filter,
                               value=val, font=FONT_SM, text_color=TEXT_PRI,
                               fg_color=ACCENT,
                               command=self._load).pack(side="left", padx=8)

        # ── Table ────────────────────────────────────────────────────────────
        card = self.make_card(self)
        card.pack(fill="both", expand=True, padx=12, pady=12)

        cols = ["trip_id", "trip_date", "departure_time", "route_name",
                "driver_name", "vehicle", "capacity", "available_seats", "occupancy_pct"]
        self.tree = self.make_tree(card, cols, heights=22)
        self.tree.bind("<<TreeviewSelect>>", self._on_select)

        self.tree.tag_configure("full",   foreground="#e53e3e")
        self.tree.tag_configure("almost", foreground="#d97706")
        self.tree.tag_configure("ok",     foreground="#22a06b")

        self._load()

    # ─── Data ──────────────────────────────────────────────────────────────────
    def _load(self, *_):
        date_cond = {
            "Today":  "AND t.trip_date = CURRENT_DATE",
            "Future": "AND t.trip_date > CURRENT_DATE",
            "Past":   "AND t.trip_date < CURRENT_DATE",
        }.get(self._date_filter.get(), "")

        search = f"%{self.search_var.get()}%"
        q = (
            "SELECT t.trip_id, t.trip_date, t.departure_time, r.route_name,"
            " COALESCE(d.driver_fullname, '—') AS driver_name,"
            " t.plate_number AS vehicle, v.capacity, t.available_seats,"
            " ROUND(((v.capacity - t.available_seats)::numeric"
            "        / NULLIF(v.capacity,0)) * 100, 1) AS occupancy_pct"
            " FROM trip t"
            " JOIN route   r ON r.route_id = t.route_id"
            " JOIN vehicle v ON v.plate_number = t.plate_number"
            " LEFT JOIN driver d ON d.driver_id = t.driver_id"
            " WHERE (r.route_name ILIKE %s OR d.driver_fullname ILIKE %s)"
            f" {date_cond}"
            " ORDER BY t.trip_date DESC, t.departure_time DESC"
        )
        rows = db.fetch_all(q, (search, search))

        self.tree.delete(*self.tree.get_children())
        for i, row in enumerate(rows):
            base_tag = "odd" if i % 2 == 0 else "even"
            pct = float(row.get("occupancy_pct") or 0)
            occ_tag = "full" if pct >= 100 else ("almost" if pct >= 80 else "ok")
            vals = [row.get(c, "") for c in self.tree["columns"]]
            self.tree.insert("", "end", values=vals, tags=(base_tag, occ_tag))

    def _on_select(self, _=None):
        sel = self.tree.selection()
        if sel:
            self._selected_trip_id = int(self.tree.item(sel[0], "values")[0])

    # ─── ADD ───────────────────────────────────────────────────────────────────
    def _open_add(self):
        dlg = _TripDialog(self, mode="add")
        self.wait_window(dlg)
        self._load()

    # ─── EDIT ──────────────────────────────────────────────────────────────────
    def _open_edit(self):
        if not self._selected_trip_id:
            self.error("Select a trip first.")
            return
        row = db.fetch_one("SELECT * FROM trip WHERE trip_id=%s",
                           (self._selected_trip_id,))
        dlg = _TripDialog(self, mode="edit", existing=row)
        self.wait_window(dlg)
        self._load()

    # ─── DELETE ────────────────────────────────────────────────────────────────
    def _delete(self):
        if not self._selected_trip_id:
            self.error("Select a trip first.")
            return
        if not self.confirm(f"Delete trip ID {self._selected_trip_id}? "
                            "All registrations for this trip will also be removed."):
            return
        try:
            db.execute_dml("DELETE FROM registration WHERE trip_id=%s",
                           (self._selected_trip_id,))
            db.execute_dml("DELETE FROM trip WHERE trip_id=%s",
                           (self._selected_trip_id,))
            self.success("Trip deleted.")
            self._selected_trip_id = None
            self._load()
        except Exception as e:
            self.error(str(e))


# ─── Dialog ───────────────────────────────────────────────────────────────────
class _TripDialog(ctk.CTkToplevel):
    def __init__(self, parent, mode, existing=None):
        super().__init__(parent)
        self.title("Add Trip" if mode == "add" else "Edit Trip")
        self.geometry("520x460")
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

        # Route dropdown
        routes = db.get_routes()
        r_labels = [f"{r['route_id']} – {r['route_name']}" for r in routes]
        cur_r = next((f"{r['route_id']} – {r['route_name']}" for r in routes
                      if r["route_id"] == ex.get("route_id")), r_labels[0] if r_labels else "")
        self._route_var = ctk.StringVar(value=cur_r)

        # Vehicle dropdown
        vehicles = db.get_vehicles()
        v_labels = [f"{v['plate_number']} ({v['vehicle_type']})" for v in vehicles]
        cur_v = next((f"{v['plate_number']} ({v['vehicle_type']})" for v in vehicles
                      if v["plate_number"] == ex.get("plate_number")), v_labels[0] if v_labels else "")
        self._vehicle_var = ctk.StringVar(value=cur_v)

        # Driver dropdown
        drivers = db.get_drivers()
        d_labels = ["— (No Driver)"] + [f"{d['driver_id']} – {d['driver_fullname']}" for d in drivers]
        cur_d = next((f"{d['driver_id']} – {d['driver_fullname']}" for d in drivers
                      if d["driver_id"] == ex.get("driver_id")), "— (No Driver)")
        self._driver_var = ctk.StringVar(value=cur_d)

        # Simple fields – no trip_id in Add mode
        simple_fields = []
        if self._mode == "edit":
            simple_fields.append(("Trip ID (read-only)", "trip_id",
                                   str(ex.get("trip_id", "")), True))
        simple_fields += [
            ("Date (YYYY-MM-DD)",      "trip_date",        str(ex.get("trip_date", "")),       False),
            ("Departure Time (HH:MM)", "departure_time",   str(ex.get("departure_time", "")),  False),
            ("Initial Booked Seats",   "expected_pass",    "0",                                False),
        ]

        self._vars = {}
        row_idx = 0
        for lbl, key, default, disabled in simple_fields:
            ctk.CTkLabel(form, text=lbl, font=FONT_LBL,
                         text_color=TEXT_SEC, anchor="w").grid(
                row=row_idx, column=0, padx=14, pady=5, sticky="w")
            var = ctk.StringVar(value=default)
            ent = ctk.CTkEntry(form, textvariable=var, width=250, font=FONT_LBL,
                               fg_color=BG_ROW, border_color=BORDER,
                               text_color=TEXT_PRI, corner_radius=8)
            if disabled:
                ent.configure(state="disabled")
            ent.grid(row=row_idx, column=1, padx=10, pady=5)
            self._vars[key] = var
            row_idx += 1

        for lbl, var, choices in [
            ("Route",   self._route_var,   r_labels),
            ("Vehicle", self._vehicle_var, v_labels),
            ("Driver",  self._driver_var,  d_labels),
        ]:
            ctk.CTkLabel(form, text=lbl, font=FONT_LBL,
                         text_color=TEXT_SEC, anchor="w").grid(
                row=row_idx, column=0, padx=14, pady=5, sticky="w")
            ctk.CTkOptionMenu(form, values=choices, variable=var,
                              font=FONT_LBL, width=250,
                              fg_color=BG_ROW, button_color=ACCENT,
                              dropdown_fg_color=BG_CARD,
                              text_color=TEXT_PRI).grid(
                row=row_idx, column=1, padx=10, pady=5)
            row_idx += 1

        self._routes   = routes
        self._vehicles = vehicles
        self._drivers  = drivers

        ctk.CTkButton(self, text="💾  Save",
                      font=ctk.CTkFont("Segoe UI", 14, "bold"),
                      fg_color=ACCENT2, hover_color="#1a8057",
                      text_color="#ffffff",
                      height=40, corner_radius=10,
                      command=self._save).pack(pady=14, padx=16, fill="x")

    def _save(self):
        from tkinter import messagebox
        v = {k: var.get().strip() for k, var in self._vars.items()}

        route_raw = self._route_var.get()
        vehicle_raw = self._vehicle_var.get()
        if not route_raw or not vehicle_raw:
            messagebox.showerror("Error", "Route and Vehicle are required.")
            return

        route_id = int(route_raw.split(" – ")[0])
        plate = vehicle_raw.split(" (")[0]
        d_sel = self._driver_var.get()
        driver_id = None if d_sel.startswith("—") else int(d_sel.split(" – ")[0])

        veh = next((x for x in self._vehicles if x["plate_number"] == plate), None)
        capacity = veh["capacity"] if veh else 0

        try:
            expected = int(v.get("expected_pass", "0") or "0")
            if expected < 0 or expected > capacity:
                messagebox.showerror("Error",
                    f"Initial booked seats must be 0–{capacity}.")
                return
            available = capacity - expected

            if self._mode == "add":
                row = db.fetch_one("SELECT COALESCE(MAX(trip_id),0)+1 AS nid FROM trip")
                new_id = row["nid"] if row else 1
                db.execute_dml(
                    """INSERT INTO trip
                       (trip_id, trip_date, departure_time, available_seats,
                        route_id, plate_number, driver_id)
                       VALUES (%s,%s,%s,%s,%s,%s,%s)""",
                    (new_id, v["trip_date"], v["departure_time"],
                     available, route_id, plate, driver_id))
                messagebox.showinfo("Success", f"Trip added (ID: {new_id})!")
            else:
                db.execute_dml(
                    """UPDATE trip SET trip_date=%s, departure_time=%s,
                       route_id=%s, plate_number=%s, driver_id=%s
                       WHERE trip_id=%s""",
                    (v["trip_date"], v["departure_time"],
                     route_id, plate, driver_id, int(v["trip_id"])))
                messagebox.showinfo("Success", "Trip updated!")
            self.destroy()
        except Exception as e:
            messagebox.showerror("DB Error", str(e))
