"""
screens/dashboard_screen.py
Home dashboard: live stats cards + quick-action buttons + recent trips list.
"""

import customtkinter as ctk
from screens.base_screen import (BaseScreen, BG_MAIN, BG_NAV, BG_CARD,
                                  BG_ROW, ACCENT, ACCENT2, DANGER, WARNING,
                                  BORDER, TEXT_PRI, TEXT_SEC,
                                  FONT_H2, FONT_LBL, FONT_SM)
import db_connection as db


class DashboardScreen(BaseScreen):
    def __init__(self, parent):
        super().__init__(parent, "Dashboard", "🏠")
        self._build()

    def _build(self):
        # ── scrollable body ────────────────────────────────────────────────
        body = ctk.CTkScrollableFrame(self, fg_color=BG_MAIN, corner_radius=0)
        body.pack(fill="both", expand=True, padx=0, pady=0)

        # ── Stats row ──────────────────────────────────────────────────────
        stats_frame = ctk.CTkFrame(body, fg_color="transparent")
        stats_frame.pack(fill="x", padx=24, pady=(20, 0))

        stat_defs = [
            ("🗺️", "Routes",       "SELECT COUNT(*) AS n FROM route",           ACCENT),
            ("🚌", "Trips",        "SELECT COUNT(*) AS n FROM trip",             ACCENT2),
            ("🚗", "Vehicles",     "SELECT COUNT(*) AS n FROM vehicle",          WARNING),
            ("🧑‍✈️", "Drivers",     "SELECT COUNT(*) AS n FROM driver",           "#9b59b6"),
            ("👤", "Passengers",   "SELECT COUNT(*) AS n FROM passenger",        "#e67e22"),
            ("📍", "Stops",        "SELECT COUNT(*) AS n FROM stop",             "#1abc9c"),
        ]
        for i, (icon, label, q, color) in enumerate(stat_defs):
            stats_frame.columnconfigure(i, weight=1, uniform="stat")
            val = self._fetch_count(q)
            self._stat_card(stats_frame, icon, label, val, color).grid(
                row=0, column=i, padx=8, pady=0, sticky="nsew")

        # ── Two-column row: Recent Trips + Route Coverage ──────────────────
        mid = ctk.CTkFrame(body, fg_color="transparent")
        mid.pack(fill="both", expand=True, padx=24, pady=16)
        mid.columnconfigure(0, weight=3)
        mid.columnconfigure(1, weight=2)

        self._recent_trips_card(mid)
        self._occupancy_card(mid)

        # ── Bottom: Today's stats bar ──────────────────────────────────────
        self._today_bar(body)

    # ── Stat card ──────────────────────────────────────────────────────────────
    def _stat_card(self, parent, icon, label, value, color):
        card = self.make_card(parent, fg_color=BG_CARD)
        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(padx=16, pady=14, fill="both")

        accent_bar = ctk.CTkFrame(inner, width=4, height=50,
                                  fg_color=color, corner_radius=2)
        accent_bar.pack(side="left", padx=(0, 12))

        right = ctk.CTkFrame(inner, fg_color="transparent")
        right.pack(side="left", fill="both", expand=True)

        ctk.CTkLabel(right, text=icon,
                     font=ctk.CTkFont("Segoe UI", 24)).pack(anchor="w")
        ctk.CTkLabel(right, text=str(value),
                     font=ctk.CTkFont("Segoe UI", 28, "bold"),
                     text_color=color).pack(anchor="w")
        ctk.CTkLabel(right, text=label,
                     font=FONT_SM, text_color=TEXT_SEC).pack(anchor="w")
        return card

    # ── Recent trips table ─────────────────────────────────────────────────────
    def _recent_trips_card(self, parent):
        card = self.make_card(parent)
        card.grid(row=0, column=0, padx=(0, 8), pady=0, sticky="nsew")

        ctk.CTkLabel(card, text="🕐  Recent Trips",
                     font=FONT_H2, text_color=TEXT_PRI).pack(
            anchor="w", padx=16, pady=(14, 4))

        cols = ["trip_id", "trip_date", "departure_time",
                "route_name", "driver_name", "available_seats"]
        tree = self.make_tree(card, cols, heights=10)

        q = """
            SELECT t.trip_id, t.trip_date, t.departure_time,
                   r.route_name,
                   COALESCE(d.driver_fullname, '—') AS driver_name,
                   t.available_seats
            FROM trip t
            JOIN route r ON r.route_id = t.route_id
            LEFT JOIN driver d ON d.driver_id = t.driver_id
            ORDER BY t.trip_date DESC, t.departure_time DESC
            LIMIT 30
        """
        rows = db.fetch_all(q)
        self.populate_tree(tree, rows)

    # ── Occupancy mini-chart ───────────────────────────────────────────────────
    def _occupancy_card(self, parent):
        card = self.make_card(parent)
        card.grid(row=0, column=1, padx=(8, 0), pady=0, sticky="nsew")

        ctk.CTkLabel(card, text="📊  Routes by Region",
                     font=FONT_H2, text_color=TEXT_PRI).pack(
            anchor="w", padx=16, pady=(14, 4))

        q = """
            SELECT reg.regio_name, COUNT(r.route_id) AS cnt
            FROM region reg
            LEFT JOIN route r ON r.region_id = reg.region_id
            GROUP BY reg.regio_name
            ORDER BY cnt DESC
        """
        rows = db.fetch_all(q)

        inner = ctk.CTkScrollableFrame(card, fg_color="transparent", height=260)
        inner.pack(fill="both", expand=True, padx=14, pady=8)

        max_cnt = max((r["cnt"] for r in rows), default=1) or 1
        colors = [ACCENT, ACCENT2, WARNING, "#9b59b6", "#e67e22",
                  "#1abc9c", DANGER, "#3498db"]

        for i, row in enumerate(rows):
            color = colors[i % len(colors)]
            pct = (row["cnt"] / max_cnt)

            row_f = ctk.CTkFrame(inner, fg_color="transparent")
            row_f.pack(fill="x", pady=4)

            ctk.CTkLabel(row_f, text=row["regio_name"],
                         font=FONT_SM, text_color=TEXT_PRI,
                         width=130, anchor="w").pack(side="left")
            bar_bg = ctk.CTkFrame(row_f, height=18, fg_color=BG_ROW,
                                  corner_radius=9)
            bar_bg.pack(side="left", fill="x", expand=True, padx=6)
            bar_fill = ctk.CTkFrame(bar_bg, height=18,
                                    fg_color=color, corner_radius=9)
            bar_fill.place(relx=0, rely=0, relwidth=pct, relheight=1)
            ctk.CTkLabel(row_f, text=str(row["cnt"]),
                         font=FONT_SM, text_color=color,
                         width=24).pack(side="left")

    # ── Today bar ─────────────────────────────────────────────────────────────
    def _today_bar(self, parent):
        bar = self.make_card(parent, fg_color=BG_NAV, corner_radius=12)
        bar.pack(fill="x", padx=24, pady=(0, 20))

        inner = ctk.CTkFrame(bar, fg_color="transparent")
        inner.pack(fill="x", padx=20, pady=12)

        today_q = """
            SELECT COUNT(*) AS cnt FROM trip WHERE trip_date = CURRENT_DATE
        """
        future_q = """
            SELECT COUNT(*) AS cnt FROM trip WHERE trip_date > CURRENT_DATE
        """
        no_driver_q = """
            SELECT COUNT(*) AS cnt FROM trip
            WHERE trip_date >= CURRENT_DATE AND driver_id IS NULL
        """
        t = self._fetch_count(today_q)
        f = self._fetch_count(future_q)
        n = self._fetch_count(no_driver_q)

        for icon, label, val, color in [
            ("📅", "Today's Trips", t, ACCENT),
            ("🔮", "Future Trips",  f, ACCENT2),
            ("⚠️", "No Driver Assigned", n, DANGER),
        ]:
            blk = ctk.CTkFrame(inner, fg_color="transparent")
            blk.pack(side="left", expand=True)
            ctk.CTkLabel(blk, text=f"{icon} {label}",
                         font=FONT_SM, text_color=TEXT_SEC).pack()
            ctk.CTkLabel(blk, text=str(val),
                         font=ctk.CTkFont("Segoe UI", 22, "bold"),
                         text_color=color).pack()

    # ── Helper ────────────────────────────────────────────────────────────────
    @staticmethod
    def _fetch_count(query):
        try:
            row = db.fetch_one(query)
            return row["cnt"] if row else 0
        except Exception:
            return "—"
