"""
app.py - GTK application entry point

Role: creates the GTK application and the main window.
"""

import gi
from gi.repository import Gtk, Gio
from shatranj.presentation.gui.window import ShatranjWindow

gi.require_version("Gtk", "4.0")


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
            blitz_time_minutes=self._blitz_time_minutes
        )
        win.present()


def run_gui(blitz: bool = False, blitz_time_minutes: int = 30) -> int:
    """Launch the GTK application. Returns the exit code."""
    app = ShatranjApp(blitz=blitz, blitz_time_minutes=blitz_time_minutes)
    return app.run()
