"""
screens/passengers_screen.py
Full CRUD for passenger + registration tables.
Registration status changes fire the DB triggers automatically.
IDs are auto-generated (MAX+1) – users never enter them manually.
"""

import customtkinter as ctk
from screens.base_screen import (BaseScreen, BG_MAIN, BG_NAV, BG_CARD, BG_ROW,
                                  ACCENT, ACCENT2, DANGER, WARNING, BORDER,
                                  TEXT_PRI, TEXT_SEC, FONT_H2, FONT_LBL, FONT_SM)
import db_connection as db

STATUS_OPTS = ["Confirmed", "Pending", "Cancelled", "Waitlisted"]
STATUS_COLORS = {
    "Confirmed":  "#22a06b",
    "Pending":    "#d97706",
    "Cancelled":  "#e53e3e",
    "Waitlisted": "#7c3aed",
}


class PassengersScreen(BaseScreen):
    def __init__(self, parent):
        super().__init__(parent, "Passengers & Registrations", "👤")
        self._sel_pass_id = None
        self._sel_reg_id  = None
        self._build()

    def _build(self):
        toolbar = ctk.CTkFrame(self, fg_color=BG_NAV, corner_radius=0,
                               height=52, border_width=1, border_color=BORDER)
        toolbar.pack(fill="x")
        toolbar.pack_propagate(False)

        self.search_var = ctk.StringVar()
        self.search_var.trace_add("write", lambda *_: self._load_passengers())
        ctk.CTkEntry(toolbar, textvariable=self.search_var,
                     placeholder_text="🔍  Search passenger…",
                     width=240, font=FONT_LBL, fg_color=BG_ROW,
                     border_color=BORDER, text_color=TEXT_PRI,
                     placeholder_text_color=TEXT_SEC,
                     corner_radius=8).pack(side="left", padx=16, pady=10)

        for text, cmd, color in [
            ("＋  Add Passenger",   self._add_passenger,    ACCENT2),
            ("✏️  Edit Passenger",  self._edit_passenger,   ACCENT),
            ("🗑  Delete Passenger",self._delete_passenger, DANGER),
            ("🔄  Refresh",         self._load_passengers,  BG_ROW),
        ]:
            self.make_button(toolbar, text, cmd, color=color).pack(
                side="left", padx=3, pady=10)

        # ── Split layout ─────────────────────────────────────────────────────
        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=12, pady=12)
        body.columnconfigure(0, weight=1)
        body.columnconfigure(1, weight=2)
        body.rowconfigure(0, weight=1)

        # Left: passenger list
        left = self.make_card(body)
        left.grid(row=0, column=0, padx=(0, 8), sticky="nsew")
        ctk.CTkLabel(left, text="👤  Passengers",
                     font=FONT_H2, text_color=TEXT_PRI).pack(
            anchor="w", padx=14, pady=(12, 4))
        self.pass_tree = self.make_tree(
            left, ["pass_id", "pass_fullname", "phone", "registrations"],
            heights=22)
        self.pass_tree.bind("<<TreeviewSelect>>", self._on_pass_select)

        # Right: registrations for selected passenger
        right = self.make_card(body)
        right.grid(row=0, column=1, padx=(8, 0), sticky="nsew")
        self._build_right(right)

        self._load_passengers()

    def _build_right(self, parent):
        hdr = ctk.CTkFrame(parent, fg_color="transparent")
        hdr.pack(fill="x", padx=14, pady=(12, 4))
        ctk.CTkLabel(hdr, text="📋  Registrations",
                     font=FONT_H2, text_color=TEXT_PRI).pack(side="left")

        btn_frame = ctk.CTkFrame(hdr, fg_color="transparent")
        btn_frame.pack(side="right")
        for text, cmd, color in [
            ("＋  Register",      self._add_registration,    ACCENT2),
            ("✏️  Update Status", self._update_status,       ACCENT),
            ("🗑  Cancel Reg",    self._delete_registration, DANGER),
        ]:
            self.make_button(btn_frame, text, cmd, color=color,
                             width=130, height=30).pack(side="left", padx=3)

        cols = ["reg_id", "trip_date", "departure_time", "route_name",
                "boarding_stop", "dropoff_stop", "status"]
        self.reg_tree = self.make_tree(parent, cols, heights=14)

        for status, color in STATUS_COLORS.items():
            self.reg_tree.tag_configure(status.lower(), foreground=color)

        self.reg_tree.bind("<<TreeviewSelect>>", self._on_reg_select)

    # ─── Passenger data ────────────────────────────────────────────────────────
    def _load_passengers(self, *_):
        s = f"%{self.search_var.get()}%"
        q = """
            SELECT p.pass_id, p.pass_fullname, p.phone,
                   COUNT(r.reg_id) AS registrations
            FROM passenger p
            LEFT JOIN registration r ON r.pass_id = p.pass_id
            WHERE p.pass_fullname ILIKE %s OR p.phone ILIKE %s
            GROUP BY p.pass_id, p.pass_fullname, p.phone
            ORDER BY p.pass_fullname
        """
        rows = db.fetch_all(q, (s, s))
        self.populate_tree(self.pass_tree, rows)

    def _on_pass_select(self, _=None):
        sel = self.pass_tree.selection()
        if not sel:
            return
        self._sel_pass_id = int(self.pass_tree.item(sel[0], "values")[0])
        self._load_registrations()

    # ─── Registration data ────────────────────────────────────────────────────
    def _load_registrations(self):
        if not self._sel_pass_id:
            return
        q = """
            SELECT reg.reg_id,
                   t.trip_date,
                   t.departure_time,
                   r.route_name,
                   COALESCE(sb.stop_name, '—') AS boarding_stop,
                   COALESCE(sd.stop_name, '—') AS dropoff_stop,
                   COALESCE(reg.status, '—')   AS status
            FROM registration reg
            JOIN trip t    ON t.trip_id   = reg.trip_id
            JOIN route r   ON r.route_id  = t.route_id
            LEFT JOIN stop sb ON sb.stop_id = reg.boarding_stop_id
            LEFT JOIN stop sd ON sd.stop_id = reg.dropoff_stop_id
            WHERE reg.pass_id = %s
            ORDER BY t.trip_date DESC
        """
        rows = db.fetch_all(q, (self._sel_pass_id,))

        self.reg_tree.delete(*self.reg_tree.get_children())
        for i, row in enumerate(rows):
            base_tag  = "odd" if i % 2 == 0 else "even"
            status_tag = (row.get("status") or "").lower()
            vals = [row.get(c, "") for c in self.reg_tree["columns"]]
            self.reg_tree.insert("", "end", values=vals,
                                 tags=(base_tag, status_tag))

    def _on_reg_select(self, _=None):
        sel = self.reg_tree.selection()
        if sel:
            self._sel_reg_id = int(self.reg_tree.item(sel[0], "values")[0])

    # ─── Passenger CRUD ───────────────────────────────────────────────────────
    def _add_passenger(self):
        dlg = _PassengerDialog(self, mode="add")
        self.wait_window(dlg)
        self._load_passengers()

    def _edit_passenger(self):
        if not self._sel_pass_id:
            self.error("Select a passenger first.")
            return
        row = db.fetch_one("SELECT * FROM passenger WHERE pass_id=%s",
                           (self._sel_pass_id,))
        dlg = _PassengerDialog(self, mode="edit", existing=row)
        self.wait_window(dlg)
        self._load_passengers()

    def _delete_passenger(self):
        if not self._sel_pass_id:
            self.error("Select a passenger first.")
            return
        if not self.confirm(
                f"Delete passenger ID {self._sel_pass_id} and all their registrations?"):
            return
        try:
            db.execute_dml("DELETE FROM registration WHERE pass_id=%s",
                           (self._sel_pass_id,))
            db.execute_dml("DELETE FROM passenger WHERE pass_id=%s",
                           (self._sel_pass_id,))
            self.success("Passenger deleted.")
            self._sel_pass_id = None
            self._load_passengers()
        except Exception as e:
            self.error(str(e))

    # ─── Registration CRUD ────────────────────────────────────────────────────
    def _add_registration(self):
        if not self._sel_pass_id:
            self.error("Select a passenger first.")
            return
        dlg = _RegistrationDialog(self, mode="add", pass_id=self._sel_pass_id)
        self.wait_window(dlg)
        self._load_registrations()
        self._load_passengers()

    def _update_status(self):
        if not self._sel_reg_id:
            self.error("Select a registration first.")
            return
        dlg = _StatusDialog(self, reg_id=self._sel_reg_id)
        self.wait_window(dlg)
        self._load_registrations()

    def _delete_registration(self):
        if not self._sel_reg_id:
            self.error("Select a registration first.")
            return
        if not self.confirm(f"Cancel registration #{self._sel_reg_id}?"):
            return
        try:
            db.execute_dml("UPDATE registration SET status='Cancelled' "
                           "WHERE reg_id=%s", (self._sel_reg_id,))
            db.execute_dml("DELETE FROM registration WHERE reg_id=%s",
                           (self._sel_reg_id,))
            self.success("Registration deleted. Seat returned to trip.")
            self._sel_reg_id = None
            self._load_registrations()
            self._load_passengers()
        except Exception as e:
            self.error(str(e))


# ─── Dialogs ──────────────────────────────────────────────────────────────────
class _PassengerDialog(ctk.CTkToplevel):
    def __init__(self, parent, mode, existing=None):
        super().__init__(parent)
        self.title("Add Passenger" if mode == "add" else "Edit Passenger")
        self.geometry("420x260")
        self.configure(fg_color=BG_MAIN)
        self.resizable(False, False)
        self.grab_set()
        self._mode = mode
        self._ex = existing or {}
        self._build()

    def _build(self):
        # Header
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
        # In add mode: no ID field (auto-generated).
        # In edit mode: show read-only ID.
        fields = []
        if self._mode == "edit":
            fields.append(("Passenger ID (read-only)", "pass_id",
                           str(ex.get("pass_id", "")), True))
        fields += [
            ("Full Name",  "pass_fullname", ex.get("pass_fullname", ""), False),
            ("Phone",      "phone",         ex.get("phone", ""),         False),
        ]

        self._vars = {}
        for i, (lbl, key, default, disabled) in enumerate(fields):
            ctk.CTkLabel(form, text=lbl, font=FONT_LBL,
                         text_color=TEXT_SEC, anchor="w").grid(
                row=i, column=0, padx=14, pady=8, sticky="w")
            var = ctk.StringVar(value=default)
            ent = ctk.CTkEntry(form, textvariable=var, width=220, font=FONT_LBL,
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
        if not v.get("pass_fullname"):
            messagebox.showerror("Error", "Full Name is required.")
            return
        try:
            if self._mode == "add":
                # Auto-generate ID
                row = db.fetch_one("SELECT COALESCE(MAX(pass_id),0)+1 AS nid FROM passenger")
                new_id = row["nid"] if row else 1
                db.execute_dml(
                    "INSERT INTO passenger (pass_id, pass_fullname, phone) "
                    "VALUES (%s,%s,%s)",
                    (new_id, v["pass_fullname"], v.get("phone") or None))
                messagebox.showinfo("Success", f"Passenger added (ID: {new_id})!")
            else:
                db.execute_dml(
                    "UPDATE passenger SET pass_fullname=%s, phone=%s "
                    "WHERE pass_id=%s",
                    (v["pass_fullname"], v.get("phone") or None,
                     int(v["pass_id"])))
                messagebox.showinfo("Success", "Passenger updated!")
            self.destroy()
        except Exception as e:
            messagebox.showerror("DB Error", str(e))


class _RegistrationDialog(ctk.CTkToplevel):
    """Register a passenger to a trip. reg_id is auto-generated."""
    def __init__(self, parent, mode, pass_id):
        super().__init__(parent)
        self.title("New Registration")
        self.geometry("480x340")
        self.configure(fg_color=BG_MAIN)
        self.resizable(False, False)
        self.grab_set()
        self._pass_id = pass_id
        self._build()

    def _build(self):
        hdr = ctk.CTkFrame(self, fg_color=BG_CARD, corner_radius=0,
                            height=54, border_width=1, border_color=BORDER)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        ctk.CTkLabel(hdr, text="📋  Register for a Trip",
                     font=ctk.CTkFont("Segoe UI", 16, "bold"),
                     text_color=TEXT_PRI).pack(side="left", padx=20, pady=12)

        form = ctk.CTkFrame(self, fg_color=BG_CARD, corner_radius=12,
                            border_width=1, border_color=BORDER)
        form.pack(padx=16, pady=12, fill="both", expand=True)

        trips  = db.get_trips()
        stops  = db.get_stops()
        t_lbls = [f"{t['trip_id']} – {t['label']}" for t in trips]
        s_lbls = ["— (None)"] + [f"{s['stop_id']} – {s['stop_name']}"
                                   for s in stops]

        self._trip_var    = ctk.StringVar(value=t_lbls[0] if t_lbls else "")
        self._board_var   = ctk.StringVar(value=s_lbls[0])
        self._dropoff_var = ctk.StringVar(value=s_lbls[0])
        self._status_var  = ctk.StringVar(value="Confirmed")

        rows = [
            ("Trip",           "dropdown", self._trip_var,    t_lbls),
            ("Boarding Stop",  "dropdown", self._board_var,   s_lbls),
            ("Drop-off Stop",  "dropdown", self._dropoff_var, s_lbls),
            ("Status",         "dropdown", self._status_var,  STATUS_OPTS),
        ]
        for i, (lbl, wtype, var, opts) in enumerate(rows):
            ctk.CTkLabel(form, text=lbl, font=FONT_LBL,
                         text_color=TEXT_SEC, anchor="w").grid(
                row=i, column=0, padx=14, pady=6, sticky="w")
            ctk.CTkOptionMenu(form, values=opts, variable=var,
                              font=FONT_LBL, width=260,
                              fg_color=BG_ROW, button_color=ACCENT,
                              dropdown_fg_color=BG_CARD,
                              text_color=TEXT_PRI).grid(
                row=i, column=1, padx=10, pady=6)

        self._trips = trips
        self._stops = stops

        ctk.CTkButton(self, text="✅  Register",
                      font=ctk.CTkFont("Segoe UI", 14, "bold"),
                      fg_color=ACCENT2, hover_color="#1a8057",
                      text_color="#ffffff",
                      height=40, corner_radius=10,
                      command=self._save).pack(pady=12, padx=16, fill="x")

    def _save(self):
        from tkinter import messagebox
        try:
            trip_raw = self._trip_var.get()
            if not trip_raw:
                messagebox.showerror("Error", "No trips available.")
                return
            trip_id = int(trip_raw.split(" – ")[0])
            board_s = self._board_var.get()
            drop_s  = self._dropoff_var.get()
            board_id = None if board_s.startswith("—") else int(board_s.split(" – ")[0])
            drop_id  = None if drop_s.startswith("—") else int(drop_s.split(" – ")[0])
            status   = self._status_var.get()

            # Auto-generate reg_id
            row = db.fetch_one("SELECT COALESCE(MAX(reg_id),0)+1 AS nid FROM registration")
            new_id = row["nid"] if row else 1

            db.execute_dml(
                """INSERT INTO registration
                   (reg_id, status, pass_id, trip_id, boarding_stop_id, dropoff_stop_id)
                   VALUES (%s,%s,%s,%s,%s,%s)""",
                (new_id, status, self._pass_id, trip_id, board_id, drop_id))
            messagebox.showinfo("Success",
                f"Registration saved (ID: {new_id})! Seat count updated by trigger.")
            self.destroy()
        except Exception as e:
            messagebox.showerror("DB Error", str(e))


class _StatusDialog(ctk.CTkToplevel):
    """Update registration status (triggers fire on UPDATE)."""
    def __init__(self, parent, reg_id):
        super().__init__(parent)
        self.title(f"Update Status – Reg #{reg_id}")
        self.geometry("380x220")
        self.configure(fg_color=BG_MAIN)
        self.resizable(False, False)
        self.grab_set()
        self._reg_id = reg_id
        self._build()

    def _build(self):
        hdr = ctk.CTkFrame(self, fg_color=BG_CARD, corner_radius=0,
                            height=54, border_width=1, border_color=BORDER)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        ctk.CTkLabel(hdr, text=f"Update Status – Reg #{self._reg_id}",
                     font=ctk.CTkFont("Segoe UI", 15, "bold"),
                     text_color=TEXT_PRI).pack(side="left", padx=20, pady=12)

        body = ctk.CTkFrame(self, fg_color=BG_CARD, corner_radius=12,
                            border_width=1, border_color=BORDER)
        body.pack(padx=16, pady=12, fill="both", expand=True)

        cur = db.fetch_one("SELECT status FROM registration WHERE reg_id=%s",
                           (self._reg_id,))
        cur_status = cur["status"] if cur else "Confirmed"
        self._status_var = ctk.StringVar(value=cur_status or "Confirmed")

        ctk.CTkLabel(body, text="New Status:", font=FONT_LBL,
                     text_color=TEXT_SEC).pack(anchor="w", padx=14, pady=(14, 4))
        ctk.CTkOptionMenu(body, values=STATUS_OPTS,
                          variable=self._status_var,
                          font=FONT_LBL, width=280,
                          fg_color=BG_ROW, button_color=ACCENT,
                          dropdown_fg_color=BG_CARD,
                          text_color=TEXT_PRI).pack(padx=14, pady=4)
        ctk.CTkLabel(body,
                     text="⚡ The DB trigger will automatically update available seats.",
                     font=FONT_SM, text_color=TEXT_SEC,
                     wraplength=320).pack(pady=6, padx=14)

        ctk.CTkButton(self, text="💾  Save Status",
                      font=ctk.CTkFont("Segoe UI", 14, "bold"),
                      fg_color=ACCENT2, hover_color="#1a8057",
                      text_color="#ffffff",
                      height=40, corner_radius=10,
                      command=self._save).pack(pady=12, padx=16, fill="x")

    def _save(self):
        from tkinter import messagebox
        try:
            db.execute_dml(
                "UPDATE registration SET status=%s WHERE reg_id=%s",
                (self._status_var.get(), self._reg_id))
            messagebox.showinfo("Success",
                "Status updated! Trigger adjusted available seats.")
            self.destroy()
        except Exception as e:
            messagebox.showerror("DB Error", str(e))
