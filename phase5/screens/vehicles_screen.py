"""
screens/vehicles_screen.py  –  Full CRUD for the vehicle table.
"""

import customtkinter as ctk
from screens.base_screen import (BaseScreen, BG_MAIN, BG_NAV, BG_CARD, BG_ROW,
                                  ACCENT, ACCENT2, DANGER, BORDER,
                                  TEXT_PRI, TEXT_SEC, FONT_LBL, FONT_SM)
import db_connection as db


class VehiclesScreen(BaseScreen):
    def __init__(self, parent):
        super().__init__(parent, "Vehicles Management", "🚗")
        self._sel_plate = None
        self._build()

    def _build(self):
        toolbar = ctk.CTkFrame(self, fg_color=BG_NAV, corner_radius=0,
                               height=52, border_width=1, border_color=BORDER)
        toolbar.pack(fill="x")
        toolbar.pack_propagate(False)

        self.search_var = ctk.StringVar()
        self.search_var.trace_add("write", lambda *_: self._load())
        ctk.CTkEntry(toolbar, textvariable=self.search_var,
                     placeholder_text="🔍  Search by plate or type…",
                     width=260, font=FONT_LBL, fg_color=BG_ROW,
                     border_color=BORDER, text_color=TEXT_PRI,
                     placeholder_text_color=TEXT_SEC,
                     corner_radius=8).pack(side="left", padx=16, pady=10)

        for text, cmd, color in [
            ("＋  Add Vehicle",   self._add,    ACCENT2),
            ("✏️  Edit Vehicle",  self._edit,   ACCENT),
            ("🗑  Delete",        self._delete, DANGER),
            ("🔄  Refresh",       self._load,   BG_ROW),
        ]:
            self.make_button(toolbar, text, cmd, color=color).pack(
                side="left", padx=4, pady=10)

        # ── Two-pane layout ──────────────────────────────────────────────────
        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=12, pady=12)
        body.columnconfigure(0, weight=2)
        body.columnconfigure(1, weight=1)
        body.rowconfigure(0, weight=1)

        # Left: vehicle table
        left = self.make_card(body)
        left.grid(row=0, column=0, padx=(0, 8), pady=0, sticky="nsew")
        cols = ["plate_number", "vehicle_type", "capacity", "total_trips",
                "regions_assigned"]
        self.tree = self.make_tree(left, cols, heights=22)
        self.tree.bind("<<TreeviewSelect>>", self._on_select)

        # Right: detail card
        right = self.make_card(body)
        right.grid(row=0, column=1, padx=(8, 0), pady=0, sticky="nsew")
        self._build_detail(right)

        self._load()

    def _build_detail(self, parent):
        ctk.CTkLabel(parent, text="🚗  Vehicle Detail",
                     font=ctk.CTkFont("Segoe UI", 16, "bold"),
                     text_color=TEXT_PRI).pack(anchor="w", padx=14, pady=(14, 6))

        self._detail_vars = {}
        for lbl in ["Plate Number", "Vehicle Type", "Capacity",
                    "Total Trips", "Future Trips"]:
            row = ctk.CTkFrame(parent, fg_color="transparent")
            row.pack(fill="x", padx=14, pady=3)
            ctk.CTkLabel(row, text=f"{lbl}:", font=FONT_SM,
                         text_color=TEXT_SEC, width=120, anchor="w").pack(side="left")
            var = ctk.StringVar(value="—")
            ctk.CTkLabel(row, textvariable=var, font=FONT_LBL,
                         text_color=TEXT_PRI, anchor="w").pack(side="left")
            self._detail_vars[lbl] = var

        ctk.CTkLabel(parent, text="🗓  Recent Trips",
                     font=ctk.CTkFont("Segoe UI", 14, "bold"),
                     text_color=TEXT_PRI).pack(anchor="w", padx=14, pady=(16, 4))
        self.detail_tree = self.make_tree(
            parent, ["trip_id", "trip_date", "route_name", "available_seats"],
            heights=8)

    # ─── Data ──────────────────────────────────────────────────────────────────
    def _load(self, *_):
        s = f"%{self.search_var.get()}%"
        q = """
            SELECT v.plate_number, v.vehicle_type, v.capacity,
                   COUNT(DISTINCT t.trip_id) AS total_trips,
                   STRING_AGG(DISTINCT reg.regio_name, ', ') AS regions_assigned
            FROM vehicle v
            LEFT JOIN trip t ON t.plate_number = v.plate_number
            LEFT JOIN region_vehicle rv ON rv.plate_number = v.plate_number
            LEFT JOIN region reg ON reg.region_id = rv.region_id
            WHERE v.plate_number ILIKE %s OR v.vehicle_type ILIKE %s
            GROUP BY v.plate_number, v.vehicle_type, v.capacity
            ORDER BY total_trips DESC
        """
        rows = db.fetch_all(q, (s, s))
        self.populate_tree(self.tree, rows)

    def _on_select(self, _=None):
        sel = self.tree.selection()
        if not sel:
            return
        self._sel_plate = self.tree.item(sel[0], "values")[0]
        self._load_detail(self._sel_plate)

    def _load_detail(self, plate):
        row = db.fetch_one(
            """SELECT v.plate_number, v.vehicle_type, v.capacity,
                      COUNT(t.trip_id) AS total_trips,
                      COUNT(t.trip_id) FILTER (WHERE t.trip_date >= CURRENT_DATE)
                          AS future_trips
               FROM vehicle v
               LEFT JOIN trip t ON t.plate_number = v.plate_number
               WHERE v.plate_number = %s
               GROUP BY v.plate_number, v.vehicle_type, v.capacity""",
            (plate,))
        if row:
            self._detail_vars["Plate Number"].set(row["plate_number"])
            self._detail_vars["Vehicle Type"].set(row["vehicle_type"])
            self._detail_vars["Capacity"].set(str(row["capacity"]))
            self._detail_vars["Total Trips"].set(str(row["total_trips"]))
            self._detail_vars["Future Trips"].set(str(row["future_trips"]))

        trips = db.fetch_all(
            """SELECT t.trip_id, t.trip_date, r.route_name, t.available_seats
               FROM trip t
               JOIN route r ON r.route_id = t.route_id
               WHERE t.plate_number = %s
               ORDER BY t.trip_date DESC LIMIT 10""", (plate,))
        self.populate_tree(self.detail_tree, trips)

    # ─── CRUD ──────────────────────────────────────────────────────────────────
    def _add(self):
        dlg = _VehicleDialog(self, mode="add")
        self.wait_window(dlg)
        self._load()

    def _edit(self):
        if not self._sel_plate:
            self.error("Select a vehicle first.")
            return
        row = db.fetch_one("SELECT * FROM vehicle WHERE plate_number=%s",
                           (self._sel_plate,))
        dlg = _VehicleDialog(self, mode="edit", existing=row)
        self.wait_window(dlg)
        self._load()

    def _delete(self):
        if not self._sel_plate:
            self.error("Select a vehicle first.")
            return
        if not self.confirm(f"Delete vehicle {self._sel_plate}?"):
            return
        try:
            db.execute_dml("DELETE FROM region_vehicle WHERE plate_number=%s",
                           (self._sel_plate,))
            db.execute_dml("DELETE FROM vehicle WHERE plate_number=%s",
                           (self._sel_plate,))
            self.success("Vehicle deleted.")
            self._sel_plate = None
            self._load()
        except Exception as e:
            self.error(str(e))


class _VehicleDialog(ctk.CTkToplevel):
    def __init__(self, parent, mode, existing=None):
        super().__init__(parent)
        self.title("Add Vehicle" if mode == "add" else "Edit Vehicle")
        self.geometry("440x300")
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
        fields = [
            ("Plate Number",  "plate_number",  ex.get("plate_number", "")),
            ("Vehicle Type",  "vehicle_type",  ex.get("vehicle_type", "")),
            ("Capacity",      "capacity",      str(ex.get("capacity", ""))),
        ]
        self._vars = {}
        for i, (lbl, key, default) in enumerate(fields):
            ctk.CTkLabel(form, text=lbl, font=FONT_LBL,
                         text_color=TEXT_SEC, anchor="w").grid(
                row=i, column=0, padx=14, pady=8, sticky="w")
            var = ctk.StringVar(value=default)
            ent = ctk.CTkEntry(form, textvariable=var, width=230, font=FONT_LBL,
                               fg_color=BG_ROW, border_color=BORDER,
                               text_color=TEXT_PRI, corner_radius=8)
            if self._mode == "edit" and key == "plate_number":
                ent.configure(state="disabled")
            ent.grid(row=i, column=1, padx=10, pady=8)
            self._vars[key] = var

        ctk.CTkButton(self, text="💾  Save",
                      font=ctk.CTkFont("Segoe UI", 14, "bold"),
                      fg_color=ACCENT2, hover_color="#1a8057",
                      text_color="#ffffff",
                      height=40, corner_radius=10,
                      command=self._save).pack(pady=14, padx=16, fill="x")

    def _save(self):
        from tkinter import messagebox
        v = {k: var.get().strip() for k, var in self._vars.items()}
        if not all(v.values()):
            messagebox.showerror("Error", "All fields are required.")
            return
        try:
            if self._mode == "add":
                db.execute_dml(
                    "INSERT INTO vehicle (plate_number, vehicle_type, capacity) "
                    "VALUES (%s,%s,%s)",
                    (v["plate_number"], v["vehicle_type"], int(v["capacity"])))
                messagebox.showinfo("Success", "Vehicle added!")
            else:
                db.execute_dml(
                    "UPDATE vehicle SET vehicle_type=%s, capacity=%s "
                    "WHERE plate_number=%s",
                    (v["vehicle_type"], int(v["capacity"]),
                     self._ex["plate_number"]))
                messagebox.showinfo("Success", "Vehicle updated!")
            self.destroy()
        except Exception as e:
            messagebox.showerror("DB Error", str(e))
