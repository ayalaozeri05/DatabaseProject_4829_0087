"""
main.py  –  TransRoute Planner  |  Phase 5 GUI
Entry point: builds the root window and top-navbar navigation.
"""

import customtkinter as ctk
from screens.dashboard_screen import DashboardScreen
from screens.routes_screen   import RoutesScreen
from screens.trips_screen    import TripsScreen
from screens.vehicles_screen import VehiclesScreen
from screens.drivers_screen  import DriversScreen
from screens.passengers_screen import PassengersScreen
from screens.stops_screen    import StopsScreen
from screens.queries_screen  import QueriesScreen
import db_connection as db

# ─── Theme ───────────────────────────────────────────────────────────────────
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

# ─── Palette ─────────────────────────────────────────────────────────────────
ACCENT      = "#5b5fcf"      # indigo
ACCENT_HOVER= "#4a4eb8"
ACCENT2     = "#22a06b"      # green
BG_MAIN     = "#f0f2f7"      # light page background
BG_NAV      = "#ffffff"      # white navbar
BG_CARD     = "#ffffff"      # white cards
TEXT_PRI    = "#1a202c"      # near-black
TEXT_SEC    = "#718096"      # medium gray
BORDER      = "#e2e8f0"      # subtle border
NAV_H       = 64             # navbar height px

FONT_LOGO   = ("Segoe UI", 17, "bold")
FONT_NAV    = ("Segoe UI", 13)
FONT_NAV_B  = ("Segoe UI", 13, "bold")
FONT_DB     = ("Segoe UI", 11)

NAV_ITEMS = [
    ("🏠  Dashboard",      DashboardScreen),
    ("🗺️  Routes",         RoutesScreen),
    ("🚌  Trips",          TripsScreen),
    ("🚗  Vehicles",       VehiclesScreen),
    ("🧑‍✈️  Drivers",        DriversScreen),
    ("👤  Passengers",     PassengersScreen),
    ("📍  Stops",          StopsScreen),
    ("📊  Queries",        QueriesScreen),
]


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("TransRoute Planner")
        self.geometry("1400x860")
        self.minsize(1100, 700)
        self.configure(fg_color=BG_MAIN)
        self._build_layout()
        self._check_db()
        self._show_screen(DashboardScreen)

    # ── Layout ────────────────────────────────────────────────────────────────
    def _build_layout(self):
        # ── Top Navbar ──────────────────────────────────────────────────────
        navbar = ctk.CTkFrame(self, height=NAV_H, corner_radius=0,
                              fg_color=BG_NAV,
                              border_width=1, border_color=BORDER)
        navbar.pack(side="top", fill="x")
        navbar.pack_propagate(False)

        # Logo block
        logo_block = ctk.CTkFrame(navbar, fg_color="transparent")
        logo_block.pack(side="left", padx=(20, 32), pady=0)

        logo_icon = ctk.CTkLabel(logo_block, text="🚌",
                                  font=("Segoe UI", 22))
        logo_icon.pack(side="left", padx=(0, 6))
        logo_text = ctk.CTkLabel(logo_block, text="TransRoute Planner",
                                  font=FONT_LOGO, text_color=ACCENT)
        logo_text.pack(side="left")

        # Separator line
        ctk.CTkFrame(navbar, width=1, fg_color=BORDER).pack(
            side="left", fill="y", pady=12)

        # Nav buttons
        self.nav_buttons = {}
        nav_tabs = ctk.CTkFrame(navbar, fg_color="transparent")
        nav_tabs.pack(side="left", fill="y", padx=8)

        for label, screen_cls in NAV_ITEMS:
            # Strip emoji for shorter labels on smaller windows
            btn = ctk.CTkButton(
                nav_tabs, text=label,
                font=FONT_NAV,
                fg_color="transparent",
                hover_color="#eef0fb",
                text_color=TEXT_SEC,
                corner_radius=8,
                height=40,
                command=lambda cls=screen_cls: self._show_screen(cls)
            )
            btn.pack(side="left", padx=2, pady=12)
            self.nav_buttons[screen_cls] = btn

        # DB status on right
        self.db_status_label = ctk.CTkLabel(
            navbar, text="● Connecting…",
            font=FONT_DB, text_color=TEXT_SEC
        )
        self.db_status_label.pack(side="right", padx=20)

        # ── Content area ─────────────────────────────────────────────────────
        self.content_frame = ctk.CTkFrame(self, corner_radius=0,
                                          fg_color=BG_MAIN)
        self.content_frame.pack(side="top", fill="both", expand=True)
        self.current_screen = None

    # ── Screen switching ──────────────────────────────────────────────────────
    def _show_screen(self, screen_cls):
        for cls, btn in self.nav_buttons.items():
            is_active = cls is screen_cls
            btn.configure(
                text_color=ACCENT if is_active else TEXT_SEC,
                font=FONT_NAV_B if is_active else FONT_NAV,
                fg_color="#eef0fb" if is_active else "transparent",
            )

        if self.current_screen:
            self.current_screen.destroy()

        self.current_screen = screen_cls(self.content_frame)
        self.current_screen.pack(fill="both", expand=True)

    # ── DB check ──────────────────────────────────────────────────────────────
    def _check_db(self):
        result = db.test_connection()
        if result is True:
            self.db_status_label.configure(
                text="● DB Connected", text_color=ACCENT2)
        else:
            self.db_status_label.configure(
                text="● DB Error", text_color="#e53e3e")


# ─── Launch ───────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = App()
    app.mainloop()
