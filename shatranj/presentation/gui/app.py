"""
app.py - GTK application entry point

Role: creates the GTK application and the main window.
"""

import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, Gio

from shatranj.presentation.gui.window import ShatranjWindow


class ShatranjApp(Gtk.Application):
    """Main GTK application."""

    def __init__(self) -> None:
        super().__init__(
            application_id="fr.u-bordeaux.shatranj",
            flags=Gio.ApplicationFlags.DEFAULT_FLAGS,
        )

    def do_activate(self) -> None:
        """Called on launch — creates and shows the window."""
        win = ShatranjWindow(application=self)
        win.present()


def run_gui() -> int:
    """Launch the GTK application. Returns the exit code."""
    app = ShatranjApp()
    return app.run()