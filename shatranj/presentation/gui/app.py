"""
app.py - GTK application entry point

Role: creates the GTK application and the main window.
"""

import os


def _apply_wslg_display_workaround(env: dict[str, str] | None = None) -> None:
    """Force a safer GTK backend on WSLg sessions.

    Some WSLg/Wayland setups crash GTK4 apps with a protocol error on complex
    surface updates. Prefer XWayland when DISPLAY is available, and otherwise
    keep a renderer fallback for pure Wayland sessions. Respect explicit user
    settings when they already chose a backend or renderer.
    """
    if env is None:
        env = os.environ

    if "WAYLAND_DISPLAY" not in env:
        return
    if "WSL_DISTRO_NAME" not in env and "WSL_INTEROP" not in env:
        return

    if "GDK_BACKEND" not in env and "DISPLAY" in env:
        env["GDK_BACKEND"] = "x11"
        return

    if "GSK_RENDERER" not in env:
        env["GSK_RENDERER"] = "gl"


_apply_wslg_display_workaround()

import gi

gi.require_version("Gtk", "4.0")

from gi.repository import Gio, Gtk

from shatranj.presentation.gui.window import ShatranjWindow


class ShatranjApp(Gtk.Application):
    """Main GTK application."""

    def __init__(self, blitz: bool = False, blitz_time_minutes: int = 30) -> None:
        super().__init__(
            application_id="fr.u-bordeaux.shatranj",
            flags=Gio.ApplicationFlags.DEFAULT_FLAGS,
        )
        self._blitz = blitz
        self._blitz_time_minutes = blitz_time_minutes

    def do_activate(self) -> None:
        """Called on launch — creates and shows the window."""
        win = ShatranjWindow(
            application=self,
            blitz=self._blitz,
            blitz_time_minutes=self._blitz_time_minutes,
        )
        win.present()


def run_gui(blitz: bool = False, blitz_time_minutes: int = 30) -> int:
    """Launch the GTK application. Returns the exit code."""
    app = ShatranjApp(blitz=blitz, blitz_time_minutes=blitz_time_minutes)
    return app.run()
