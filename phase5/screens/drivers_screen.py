"""
screens/drivers_screen.py  –  Full CRUD for the driver table.
driver_id is auto-generated on Add – users never enter it manually.
"""

import customtkinter as ctk
from screens.base_screen import (BaseScreen, BG_MAIN, BG_NAV, BG_CARD, BG_ROW,
                                  ACCENT, ACCENT2, DANGER, BORDER,
                                  TEXT_PRI, TEXT_SEC, FONT_LBL, FONT_SM, FONT_H2)
import db_connection as db


class DriversScreen(BaseScreen):
    def __init__(self, parent):
        super().__init__(parent, "Drivers Management", "🧑‍✈️")
        self._sel_id = None
        self._build()

    def _build(self):
        toolbar = ctk.CTkFrame(self, fg_color=BG_NAV, corner_radius=0,
                               height=52, border_width=1, border_color=BORDER)
        toolbar.pack(fill="x")
        toolbar.pack_propagate(False)

        self.search_var = ctk.StringVar()
        self.search_var.trace_add("write", lambda *_: self._load())
        ctk.CTkEntry(toolbar, textvariable=self.search_var,
                     placeholder_text="🔍  Search driver…",
                     width=260, font=FONT_LBL, fg_color=BG_ROW,
                     border_color=BORDER, text_color=TEXT_PRI,
                     placeholder_text_color=TEXT_SEC,
                     corner_radius=8).pack(side="left", padx=16, pady=10)

        for text, cmd, color in [
            ("＋  Add Driver",   self._add,    ACCENT2),
            ("✏️  Edit Driver",  self._edit,   ACCENT),
            ("🗑  Delete",       self._delete, DANGER),
            ("🔄  Refresh",      self._load,   BG_ROW),
        ]:
            self.make_button(toolbar, text, cmd, color=color).pack(
                side="left", padx=4, pady=10)

        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=12, pady=12)
        body.columnconfigure(0, weight=2)
        body.columnconfigure(1, weight=1)
        body.rowconfigure(0, weight=1)

        left = self.make_card(body)
        left.grid(row=0, column=0, padx=(0, 8), sticky="nsew")
        cols = ["driver_id", "driver_fullname", "phone",
                "license_number", "total_trips", "upcoming_trips"]
        self.tree = self.make_tree(left, cols, heights=22)
        self.tree.bind("<<TreeviewSelect>>", self._on_select)

        right = self.make_card(body)
        right.grid(row=0, column=1, padx=(8, 0), sticky="nsew")
        self._build_detail(right)

        self._load()

    def _build_detail(self, parent):
        ctk.CTkLabel(parent, text="🧑‍✈️  Driver Schedule",
                     font=FONT_H2, text_color=TEXT_PRI).pack(
            anchor="w", padx=14, pady=(14, 6))

        self._detail_vars = {}
        for lbl in ["Name", "Phone", "License", "Total Trips", "Upcoming"]:
            r = ctk.CTkFrame(parent, fg_color="transparent")
            r.pack(fill="x", padx=14, pady=3)
            ctk.CTkLabel(r, text=f"{lbl}:", font=FONT_SM,
                         text_color=TEXT_SEC, width=90, anchor="w").pack(side="left")
            var = ctk.StringVar(value="—")
            ctk.CTkLabel(r, textvariable=var, font=FONT_LBL,
                         text_color=TEXT_PRI).pack(side="left")
            self._detail_vars[lbl] = var

        ctk.CTkFrame(parent, height=1, fg_color=BORDER).pack(
            fill="x", padx=14, pady=(12, 0))

        ctk.CTkLabel(parent, text="📅  Upcoming Trips",
                     font=FONT_H2, text_color=TEXT_PRI).pack(
            anchor="w", padx=14, pady=(12, 4))
        self.sched_tree = self.make_tree(
            parent, ["trip_id", "trip_date", "departure_time", "route_name"],
            heights=9)

    # ─── Data ──────────────────────────────────────────────────────────────────
    def _load(self, *_):
        s = f"%{self.search_var.get()}%"
        q = """
            SELECT d.driver_id, d.driver_fullname, d.phone, d.license_number,
                   COUNT(t.trip_id) AS total_trips,
                   COUNT(t.trip_id) FILTER (WHERE t.trip_date >= CURRENT_DATE)
                       AS upcoming_trips
            FROM driver d
            LEFT JOIN trip t ON t.driver_id = d.driver_id
            WHERE d.driver_fullname ILIKE %s OR d.phone ILIKE %s
                  OR d.license_number ILIKE %s
            GROUP BY d.driver_id, d.driver_fullname, d.phone, d.license_number
            ORDER BY upcoming_trips DESC, d.driver_fullname
        """
        rows = db.fetch_all(q, (s, s, s))
        self.populate_tree(self.tree, rows)

    def _on_select(self, _=None):
        sel = self.tree.selection()
        if not sel:
            return
        self._sel_id = int(self.tree.item(sel[0], "values")[0])
        row = db.fetch_one(
            """SELECT d.driver_fullname, d.phone, d.license_number,
                      COUNT(t.trip_id) AS total_trips,
                      COUNT(t.trip_id) FILTER (WHERE t.trip_date >= CURRENT_DATE)
                          AS upcoming_trips
               FROM driver d
               LEFT JOIN trip t ON t.driver_id = d.driver_id
               WHERE d.driver_id = %s
               GROUP BY d.driver_fullname, d.phone, d.license_number""",
            (self._sel_id,))
        if row:
            self._detail_vars["Name"].set(row["driver_fullname"] or "—")
            self._detail_vars["Phone"].set(row["phone"] or "—")
            self._detail_vars["License"].set(row["license_number"] or "—")
            self._detail_vars["Total Trips"].set(str(row["total_trips"]))
            self._detail_vars["Upcoming"].set(str(row["upcoming_trips"]))

        sched = db.fetch_all(
            """SELECT t.trip_id, t.trip_date, t.departure_time, r.route_name
               FROM trip t
               JOIN route r ON r.route_id = t.route_id
               WHERE t.driver_id = %s AND t.trip_date >= CURRENT_DATE
               ORDER BY t.trip_date, t.departure_time LIMIT 15""",
            (self._sel_id,))
        self.populate_tree(self.sched_tree, sched)

    # ─── CRUD ──────────────────────────────────────────────────────────────────
    def _add(self):
        dlg = _DriverDialog(self, mode="add")
        self.wait_window(dlg)
        self._load()

    def _edit(self):
        if not self._sel_id:
            self.error("Select a driver first.")
            return
        row = db.fetch_one("SELECT * FROM driver WHERE driver_id=%s", (self._sel_id,))
        dlg = _DriverDialog(self, mode="edit", existing=row)
        self.wait_window(dlg)
        self._load()

    def _delete(self):
        if not self._sel_id:
            self.error("Select a driver first.")
            return
        if not self.confirm(f"Delete driver ID {self._sel_id}? "
                            "Their trips will remain but driver_id will be set to NULL."):
            return
        try:
            db.execute_dml("UPDATE trip SET driver_id=NULL WHERE driver_id=%s",
                           (self._sel_id,))
            db.execute_dml("DELETE FROM driver WHERE driver_id=%s", (self._sel_id,))
            self.success("Driver deleted.")
            self._sel_id = None
            self._load()
        except Exception as e:
            self.error(str(e))


class _DriverDialog(ctk.CTkToplevel):
    def __init__(self, parent, mode, existing=None):
        super().__init__(parent)
        self.title("Add Driver" if mode == "add" else "Edit Driver")
        self.geometry("440x280")
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
        # Add mode: no ID field. Edit mode: read-only ID shown.
        fields = []
        if self._mode == "edit":
            fields.append(("Driver ID (read-only)", "driver_id",
                           str(ex.get("driver_id", "")), True))
        fields += [
            ("Full Name",      "driver_fullname", ex.get("driver_fullname", ""), False),
            ("Phone",          "phone",           ex.get("phone", ""),           False),
            ("License Number", "license_number",  ex.get("license_number", ""),  False),
        ]

        self._vars = {}
        for i, (lbl, key, default, disabled) in enumerate(fields):
            ctk.CTkLabel(form, text=lbl, font=FONT_LBL,
                         text_color=TEXT_SEC, anchor="w").grid(
                row=i, column=0, padx=14, pady=8, sticky="w")
            var = ctk.StringVar(value=default)
            ent = ctk.CTkEntry(form, textvariable=var, width=230, font=FONT_LBL,
                               fg_color=BG_ROW, border_color=BORDER,
                               text_color=TEXT_PRI, corner_radius=8)
            if disabled:
                ent.configure(state="disabled")
            ent.grid(row=i, column=1, padx=10, pady=8)
            self._vars[key] = var

        ctk.CTkButton(self, text="💾  Save",
                      font=ctk.CTkFont("Segoe UI", 14, "bold"),
                      fg_color=ACCENT2, hover_color="#1a8057",
                      text_color="#ffffff",
                      height=40, corner_radius=10,
                      command=self._save).pack(pady=12, padx=16, fill="x")

    def _save(self):
        from tkinter import messagebox
        v = {k: var.get().strip() for k, var in self._vars.items()}
        if not v.get("driver_fullname"):
            messagebox.showerror("Error", "Full Name is required.")
            return
        try:
            if self._mode == "add":
                row = db.fetch_one("SELECT COALESCE(MAX(driver_id),0)+1 AS nid FROM driver")
                new_id = row["nid"] if row else 1
                db.execute_dml(
                    "INSERT INTO driver (driver_id, driver_fullname, phone, "
                    "license_number) VALUES (%s,%s,%s,%s)",
                    (new_id, v["driver_fullname"],
                     v.get("phone") or None, v.get("license_number") or None))
                messagebox.showinfo("Success", f"Driver added (ID: {new_id})!")
            else:
                db.execute_dml(
                    "UPDATE driver SET driver_fullname=%s, phone=%s, "
                    "license_number=%s WHERE driver_id=%s",
                    (v["driver_fullname"], v.get("phone") or None,
                     v.get("license_number") or None,
                     int(v["driver_id"])))
                messagebox.showinfo("Success", "Driver updated!")
            self.destroy()
        except Exception as e:
            messagebox.showerror("DB Error", str(e))
