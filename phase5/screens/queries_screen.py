"""
screens/queries_screen.py
Runs Phase-2 queries + Phase-4 stored procedures/functions.
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import scrolledtext
from screens.base_screen import (BaseScreen, BG_MAIN, BG_NAV, BG_CARD, BG_ROW,
                                  ACCENT, ACCENT2, DANGER, WARNING, BORDER,
                                  TEXT_PRI, TEXT_SEC, FONT_H2, FONT_LBL, FONT_SM)
import db_connection as db


class QueriesScreen(BaseScreen):
    def __init__(self, parent):
        super().__init__(parent, "Queries & Stored Procedures", "📊")
        self._build()

    def _build(self):
        body = ctk.CTkScrollableFrame(self, fg_color=BG_MAIN, corner_radius=0)
        body.pack(fill="both", expand=True, padx=0, pady=0)

        # ── Section A: Phase-2 Queries ────────────────────────────────────────
        sec_a = self._section(body, "📋  Phase 2 – SQL Queries")

        # Query 1A: Dashboard Routes
        q1_card = self.make_card(sec_a)
        q1_card.pack(fill="x", padx=0, pady=(0, 14))
        self._query_block(
            q1_card,
            title="Query 1A – Routes Dashboard (JOIN + GROUP BY)",
            description=(
                "Retrieves all routes with their region name, average duration, "
                "total distance and number of stops. Uses JOIN + GROUP BY."
            ),
            sql="""SELECT r.route_id, r.route_name, reg.regio_name,
       r.estimated_duration_minutes, r.total_distance_km,
       COUNT(rs.stop_id) AS total_stops
FROM route r
JOIN region reg ON r.region_id = reg.region_id
LEFT JOIN route_stop rs ON r.route_id = rs.route_id
GROUP BY r.route_id, r.route_name, reg.regio_name,
         r.estimated_duration_minutes, r.total_distance_km
ORDER BY r.route_id""",
            run_fn=self._run_q1a,
            cols=["route_id", "route_name", "regio_name",
                  "estimated_duration_minutes", "total_distance_km", "total_stops"],
        )

        # Query 6: AVG duration/distance per region
        q6_card = self.make_card(sec_a)
        q6_card.pack(fill="x", padx=0, pady=(0, 14))
        self._query_block(
            q6_card,
            title="Query 6 – Avg Duration & Distance per Region (AVG + HAVING)",
            description=(
                "Groups routes by region and calculates average duration and "
                "distance. HAVING filters regions that actually have routes."
            ),
            sql="""SELECT reg.regio_name, reg.terrain_type,
       COUNT(r.route_id) AS routes_count,
       ROUND(AVG(r.estimated_duration_minutes), 2) AS avg_duration,
       ROUND(AVG(r.total_distance_km)::numeric, 2)  AS avg_distance
FROM region reg
JOIN route r ON reg.region_id = r.region_id
GROUP BY reg.regio_name, reg.terrain_type
HAVING COUNT(r.route_id) > 0
ORDER BY avg_duration DESC""",
            run_fn=self._run_q6,
            cols=["regio_name", "terrain_type", "routes_count",
                  "avg_duration", "avg_distance"],
        )

        # ── Section B: Phase-4 Procedures & Functions ─────────────────────────
        sec_b = self._section(body, "⚙️  Phase 4 – Stored Procedures & Functions")

        # 1. get_route_dashboard (refcursor function)
        f1_card = self.make_card(sec_b)
        f1_card.pack(fill="x", padx=0, pady=(0, 14))
        self._proc_block(
            f1_card,
            title="Function: get_route_dashboard()",
            description=(
                "Returns a Ref Cursor with route dashboard data: route name, region, "
                "distance, duration, number of stops, and future trip count."
            ),
            run_label="▶  Run get_route_dashboard()",
            run_fn=self._run_get_route_dashboard,
            run_color=ACCENT,
            cols=["route_id", "route_name", "region_name",
                  "total_distance_km", "estimated_duration_minutes",
                  "stop_count", "future_trip_count"],
        )

        # 2. calculate_trip_occupancy (table function, needs trip_id input)
        f2_card = self.make_card(sec_b)
        f2_card.pack(fill="x", padx=0, pady=(0, 14))
        self._occupancy_block(f2_card)

        # 3. schedule_new_trip (procedure)
        p1_card = self.make_card(sec_b)
        p1_card.pack(fill="x", padx=0, pady=(0, 14))
        self._schedule_trip_block(p1_card)

        # 4. auto_assign_drivers (procedure, no args)
        p2_card = self.make_card(sec_b)
        p2_card.pack(fill="x", padx=0, pady=(0, 14))
        self._auto_assign_block(p2_card)

    # ── Section header helper ──────────────────────────────────────────────────
    def _section(self, parent, title):
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill="x", padx=20, pady=(18, 6))
        ctk.CTkLabel(frame, text=title,
                     font=ctk.CTkFont("Segoe UI", 18, "bold"),
                     text_color=ACCENT).pack(anchor="w")
        ctk.CTkFrame(frame, height=2, fg_color=ACCENT).pack(
            fill="x", pady=(4, 0))
        content = ctk.CTkFrame(parent, fg_color="transparent")
        content.pack(fill="x", padx=20, pady=4)
        return content

    # ── Generic query block ────────────────────────────────────────────────────
    def _query_block(self, card, title, description, sql, run_fn, cols):
        ctk.CTkLabel(card, text=title,
                     font=ctk.CTkFont("Segoe UI", 15, "bold"),
                     text_color=TEXT_PRI).pack(anchor="w", padx=16, pady=(12, 2))
        ctk.CTkLabel(card, text=description,
                     font=FONT_SM, text_color=TEXT_SEC,
                     wraplength=800, justify="left").pack(anchor="w", padx=16, pady=(0, 6))

        # SQL display
        sql_frame = ctk.CTkFrame(card, fg_color="#0d1117", corner_radius=8)
        sql_frame.pack(fill="x", padx=16, pady=(0, 8))
        ctk.CTkLabel(sql_frame, text=sql,
                     font=ctk.CTkFont("Courier New", 11),
                     text_color="#79c0ff", justify="left",
                     anchor="w").pack(padx=12, pady=8, anchor="w")

        btn_row = ctk.CTkFrame(card, fg_color="transparent")
        btn_row.pack(fill="x", padx=16, pady=(0, 8))
        run_btn = self.make_button(btn_row, "▶  Run Query", run_fn,
                                   color=ACCENT2, width=160)
        run_btn.pack(side="left")

        # Results tree
        result_frame = ctk.CTkFrame(card, fg_color="transparent")
        result_frame.pack(fill="x", padx=16, pady=(0, 12))
        tree = self.make_tree(result_frame, cols, heights=7)
        run_btn.configure(command=lambda: self._exec_and_show(run_fn, tree, cols))
        return tree

    def _exec_and_show(self, fn, tree, cols):
        try:
            rows = fn()
            self.populate_tree(tree, rows)
        except Exception as e:
            self.error(str(e))

    # ── Generic procedure block ────────────────────────────────────────────────
    def _proc_block(self, card, title, description, run_label, run_fn,
                    run_color, cols):
        ctk.CTkLabel(card, text=title,
                     font=ctk.CTkFont("Segoe UI", 15, "bold"),
                     text_color=TEXT_PRI).pack(anchor="w", padx=16, pady=(12, 2))
        ctk.CTkLabel(card, text=description,
                     font=FONT_SM, text_color=TEXT_SEC,
                     wraplength=800, justify="left").pack(
            anchor="w", padx=16, pady=(0, 8))

        btn_row = ctk.CTkFrame(card, fg_color="transparent")
        btn_row.pack(fill="x", padx=16, pady=(0, 8))
        run_btn = self.make_button(btn_row, run_label, lambda: None,
                                   color=run_color, width=260)
        run_btn.pack(side="left")

        result_frame = ctk.CTkFrame(card, fg_color="transparent")
        result_frame.pack(fill="x", padx=16, pady=(0, 12))
        tree = self.make_tree(result_frame, cols, heights=6)
        run_btn.configure(
            command=lambda: self._exec_and_show(run_fn, tree, cols))
        return tree

    # ── Occupancy block (needs trip_id input) ─────────────────────────────────
    def _occupancy_block(self, card):
        ctk.CTkLabel(card,
                     text="Function: calculate_trip_occupancy(trip_id)",
                     font=ctk.CTkFont("Segoe UI", 15, "bold"),
                     text_color=TEXT_PRI).pack(anchor="w", padx=16, pady=(12, 2))
        ctk.CTkLabel(card,
                     text=("Given a trip ID, returns capacity, available seats, "
                           "registered passengers, occupancy %, and status "
                           "(FULL / ALMOST FULL / AVAILABLE)."),
                     font=FONT_SM, text_color=TEXT_SEC,
                     wraplength=800).pack(anchor="w", padx=16, pady=(0, 8))

        inp_row = ctk.CTkFrame(card, fg_color="transparent")
        inp_row.pack(fill="x", padx=16, pady=(0, 8))
        ctk.CTkLabel(inp_row, text="Trip ID:", font=FONT_LBL,
                     text_color=TEXT_SEC).pack(side="left")
        self._occ_trip_var = ctk.StringVar()
        ctk.CTkEntry(inp_row, textvariable=self._occ_trip_var,
                     width=100, font=FONT_LBL, fg_color=BG_ROW,
                     border_color=BORDER, text_color=TEXT_PRI,
                     corner_radius=8).pack(side="left", padx=8)

        result_frame = ctk.CTkFrame(card, fg_color="transparent")
        result_frame.pack(fill="x", padx=16, pady=(0, 12))
        cols = ["trip_id", "capacity", "available_seats",
                "registered_passengers", "occupancy_percent", "status_text"]
        tree = self.make_tree(result_frame, cols, heights=3)

        self.make_button(inp_row, "▶  Calculate Occupancy",
                         lambda: self._run_occupancy(tree),
                         color=ACCENT, width=200).pack(side="left")

    def _run_occupancy(self, tree):
        tid = self._occ_trip_var.get().strip()
        if not tid:
            self.error("Enter a Trip ID.")
            return
        try:
            rows = db.call_table_function(
                "calculate_trip_occupancy(%s)", (int(tid),))
            self.populate_tree(tree, rows)
        except Exception as e:
            self.error(str(e))

    # ── schedule_new_trip block ────────────────────────────────────────────────
    def _schedule_trip_block(self, card):
        ctk.CTkLabel(card,
                     text="Procedure: schedule_new_trip(…)",
                     font=ctk.CTkFont("Segoe UI", 15, "bold"),
                     text_color=TEXT_PRI).pack(anchor="w", padx=16, pady=(12, 2))
        ctk.CTkLabel(card,
                     text=("Validates route, vehicle and driver, checks capacity, "
                           "then inserts a new trip with computed available seats."),
                     font=FONT_SM, text_color=TEXT_SEC,
                     wraplength=800).pack(anchor="w", padx=16, pady=(0, 8))

        form = ctk.CTkFrame(card, fg_color="transparent")
        form.pack(fill="x", padx=16, pady=(0, 6))

        labels = ["Trip ID", "Route ID", "Date (YYYY-MM-DD)",
                  "Departure (HH:MM)", "Expected Passengers",
                  "Plate Number", "Driver ID"]
        self._sched_vars = {}
        for i, lbl in enumerate(labels):
            r = i // 4
            c = (i % 4) * 2
            form.columnconfigure(c+1, weight=1)
            ctk.CTkLabel(form, text=f"{lbl}:", font=FONT_SM,
                         text_color=TEXT_SEC).grid(
                row=r, column=c, padx=(10, 4), pady=4, sticky="e")
            var = ctk.StringVar()
            ctk.CTkEntry(form, textvariable=var, width=130, font=FONT_LBL,
                         fg_color=BG_ROW, border_color=BORDER,
                         text_color=TEXT_PRI, corner_radius=8).grid(
                row=r, column=c+1, padx=(0, 10), pady=4, sticky="w")
            self._sched_vars[lbl] = var

        # Result message label
        self._sched_result = ctk.StringVar(value="")
        ctk.CTkLabel(card, textvariable=self._sched_result,
                     font=FONT_LBL, text_color=ACCENT2,
                     wraplength=800).pack(anchor="w", padx=16, pady=4)

        self.make_button(card, "▶  Schedule New Trip",
                         self._run_schedule_trip,
                         color=WARNING, width=220).pack(
            anchor="w", padx=16, pady=(0, 12))

    def _run_schedule_trip(self):
        v = self._sched_vars
        try:
            db.call_procedure("schedule_new_trip", (
                int(v["Trip ID"].get()),
                int(v["Route ID"].get()),
                v["Date (YYYY-MM-DD)"].get(),
                v["Departure (HH:MM)"].get(),
                int(v["Expected Passengers"].get()),
                v["Plate Number"].get(),
                int(v["Driver ID"].get()),
            ))
            self._sched_result.set(
                "✅ Trip scheduled successfully! Check the Trips screen.")
        except Exception as e:
            self._sched_result.set(f"❌ {e}")

    # ── auto_assign_drivers block ──────────────────────────────────────────────
    def _auto_assign_block(self, card):
        ctk.CTkLabel(card,
                     text="Procedure: auto_assign_drivers_to_future_trips()",
                     font=ctk.CTkFont("Segoe UI", 15, "bold"),
                     text_color=TEXT_PRI).pack(anchor="w", padx=16, pady=(12, 2))
        ctk.CTkLabel(card,
                     text=("Round-Robin auto assignment: iterates over all future "
                           "trips with no driver using an explicit cursor and assigns "
                           "available drivers in rotation."),
                     font=FONT_SM, text_color=TEXT_SEC,
                     wraplength=800).pack(anchor="w", padx=16, pady=(0, 8))

        self._assign_result = ctk.StringVar(value="")
        ctk.CTkLabel(card, textvariable=self._assign_result,
                     font=FONT_LBL, text_color=ACCENT2,
                     wraplength=800).pack(anchor="w", padx=16, pady=4)

        btn_row = ctk.CTkFrame(card, fg_color="transparent")
        btn_row.pack(fill="x", padx=16, pady=(0, 12))
        self.make_button(btn_row,
                         "▶  Run Auto-Assign Drivers",
                         self._run_auto_assign,
                         color="#9b59b6", width=240).pack(side="left")

        # Preview: trips still without driver
        ctk.CTkLabel(btn_row, text="  Trips without driver:",
                     font=FONT_SM, text_color=TEXT_SEC).pack(side="left", padx=8)
        self._no_driver_lbl = ctk.CTkLabel(btn_row, text="—",
                                            font=FONT_LBL, text_color=DANGER)
        self._no_driver_lbl.pack(side="left")
        self._refresh_no_driver()

        result_frame = ctk.CTkFrame(card, fg_color="transparent")
        result_frame.pack(fill="x", padx=16, pady=(0, 12))
        self._assign_tree = self.make_tree(
            result_frame,
            ["trip_id", "trip_date", "route_name", "driver_name"],
            heights=6)

    def _refresh_no_driver(self):
        try:
            row = db.fetch_one(
                "SELECT COUNT(*) AS cnt FROM trip "
                "WHERE trip_date >= CURRENT_DATE AND driver_id IS NULL")
            cnt = row["cnt"] if row else 0
            self._no_driver_lbl.configure(
                text=str(cnt),
                text_color=DANGER if cnt > 0 else ACCENT2)
        except Exception:
            pass

    def _run_auto_assign(self):
        if not self.confirm(
                "This will assign drivers (Round-Robin) to all future trips "
                "that currently have no driver. Proceed?"):
            return
        try:
            db.call_procedure("auto_assign_drivers_to_future_trips", [])
            self._assign_result.set(
                "✅ Drivers assigned! Refreshing assigned trips…")
            self._refresh_no_driver()
            rows = db.fetch_all(
                """SELECT t.trip_id, t.trip_date, r.route_name,
                          d.driver_fullname AS driver_name
                   FROM trip t
                   JOIN route r  ON r.route_id  = t.route_id
                   JOIN driver d ON d.driver_id = t.driver_id
                   WHERE t.trip_date >= CURRENT_DATE
                   ORDER BY t.trip_date
                   LIMIT 20""")
            self.populate_tree(self._assign_tree, rows)
        except Exception as e:
            self._assign_result.set(f"❌ {e}")

    # ── Phase-2 query runners ──────────────────────────────────────────────────
    @staticmethod
    def _run_q1a():
        return db.fetch_all("""
            SELECT r.route_id, r.route_name, reg.regio_name,
                   r.estimated_duration_minutes, r.total_distance_km,
                   COUNT(rs.stop_id) AS total_stops
            FROM route r
            JOIN region reg ON r.region_id = reg.region_id
            LEFT JOIN route_stop rs ON r.route_id = rs.route_id
            GROUP BY r.route_id, r.route_name, reg.regio_name,
                     r.estimated_duration_minutes, r.total_distance_km
            ORDER BY r.route_id
        """)

    @staticmethod
    def _run_q6():
        return db.fetch_all("""
            SELECT reg.regio_name, reg.terrain_type,
                   COUNT(r.route_id) AS routes_count,
                   ROUND(AVG(r.estimated_duration_minutes), 2) AS avg_duration,
                   ROUND(AVG(r.total_distance_km)::numeric, 2)  AS avg_distance
            FROM region reg
            JOIN route r ON reg.region_id = r.region_id
            GROUP BY reg.regio_name, reg.terrain_type
            HAVING COUNT(r.route_id) > 0
            ORDER BY avg_duration DESC
        """)

    @staticmethod
    def _run_get_route_dashboard():
        return db.call_refcursor_function(
            "SELECT get_route_dashboard()",
            'FETCH ALL FROM "route_dashboard_cursor"')
